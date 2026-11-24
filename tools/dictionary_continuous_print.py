"""Bind a reference work as one book with continuous folios."""
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtWidgets import QApplication

from tools import shakespeare_collected as sc
from tools.conventional_reference import write_json
from tools.dictionary_corpus import ROOT, sha
from tools.dictionary_lexicon import load_gzip
from tools.shakespeare_collected_pdf import render_duplex
from tools.semantic_expansion import WORK as LEXICON
from tools.thesaurus_print import ThesaurusVolume
from vayrshemon.file_api import FileSession
from vayrshemon.page_numbering import digits


def reposition(page, spec, side):
    if spec['side'] == side:
        return
    margins = page['margins']
    margins['left'], margins['right'] = margins['right'], margins['left']
    frame = page['frames'][0]
    shift = (int(margins['left']) - int(frame['x'])) / 1_000_000
    frame['x'] = margins['left']
    spec['side'] = side
    for line in spec['lines']:
        line['x'] += shift
        line['bounds'][0] += shift
    for rule in spec['paths']:
        assert rule['role'] == 'dictionary-running-head-rule'
        rule['bounds'][0] += shift
        for element in rule['elements']:
            element[1] += shift


def remove_volume_marker(page, spec, volume):
    # A page occupied by a single headword formerly printed the volume number
    # as its second running head. Keep the headword alone in the complete book.
    line = spec['lines'][1]
    text = sc.pe.text_of(page)
    start, end = line['start'], line['end']
    if text[start:end] != digits(volume):
        return 0
    assert line['baseline'] == 66
    amount = end-start
    text = text[:start]+text[end:]
    story = page['frames'][0]['content']['document']['stories'][0]
    story['blocks'][0]['runs'][0]['text'] = text
    spec['sourceSha256'] = sc.pe.hash_text(text)
    del spec['lines'][1]
    for following in spec['lines'][1:]:
        assert following['start'] >= end
        following['start'] -= amount
        following['end'] -= amount
    return amount


def assemble(book):
    catalogue = json.loads((book.work/'volumes.json').read_text('utf8'))
    source_ledger = sha(book.work/'volumes.json')
    ranges, expected_records = [], set()
    for meta in catalogue:
        number = meta['number']
        filename = meta['name']
        path = book.folders['print']/(filename+'.vay')
        receipt = json.loads((book.work/'Publication'/f'print-{number:02d}.json').read_text('utf8'))
        assert sha(path) == receipt['sha256'] and receipt['allPDFTextAndBoundsVerified']
        incoming = sc.unpack(sc.read(path))['state']
        original = incoming['printEdition']
        if number == 1:
            volume = ThesaurusVolume(incoming['language'], dict(sha256=source_ledger),
                                     title=book.title, document_id='document.'+book.key+'.complete.letter',
                                     ledger_sha=sha(LEXICON/'reciprocal-lexicon.json.gz'))
            volume.new_page('title','Title page')
            volume.label('title',meta['title'],42,300)
            guide = meta['guide']
            guide_size = next(size for size in range(26,0,-1) if volume.proof.ink(guide,size).width()<=sc.MEASURE)
            volume.label('guide',guide,guide_size,363-volume.proof.ink(guide,guide_size).top())
            volume.finish_page()
            state, edition = volume.state, volume.edition
        assert original['typography']==edition['typography'] and not original['assets']
        assert incoming['fontSources']==state['fontSources']
        assert [original['pages'][p['pageId']]['kind'] for p in incoming['pages'][:2]] == ['title','blank']
        first = len(state['pages'])+1
        mapping = {}
        for p in incoming['pages'][2:]:
            old = p['pageId']
            spec = original['pages'][old]
            assert spec['kind'] in ('opening','body') and len(spec['lines'])>2
            physical = len(state['pages'])+1
            pid = f'page.{book.key}.complete.{physical}'
            cutoff = spec['lines'][1]['end']
            removed = remove_volume_marker(p,spec,number)
            mapping[old] = (pid,cutoff,removed)
            spec['folio'] = physical-1
            reposition(p,spec,'left' if physical%2==0 else 'right')
            p['pageId'] = pid
            frame = p['frames'][0]
            frame['frameId'] = pid.replace('page.', 'frame.', 1)
            frame['content']['document']['documentId'] = state['documentId']
            state['pages'].append(p)
            edition['pages'][pid] = spec
        label = filename+' · '+meta['first']+' – '+meta['last']
        first_id = state['pages'][first-1]['pageId']
        edition['sections'].append(dict(number=number,name=label,pageId=first_id))
        rows = load_gzip(book.stage/'volumes'/f'{number:02d}.json.gz')['print']
        expected = {r['id']:sc.pe.hash_text(' '.join(r['text'].split())) for r in rows}
        assert len(expected) == len(rows) == meta['printParagraphs']
        for record in original['verses']:
            key = record['id']
            if key in ('title','guide'):
                continue
            spans = record['fragments']
            if key.startswith('nav/running-'):
                pid, _, removed = mapping[spans[0]['pageId']]
                if removed and key.startswith('nav/running-range/'):
                    continue
                key = key.rsplit('/',1)[0]+'/'+str(edition['pages'][pid]['folio'])
            else:
                assert expected.pop(key) == record['sha256'] and key not in expected_records
                expected_records.add(key)
            for span in spans:
                pid,cutoff,removed = mapping[span['pageId']]
                span['pageId'] = pid
                if span['start'] >= cutoff:
                    span['start'] -= removed
                    span['end'] -= removed
            edition['verses'].append(dict(id=key,sha256=record['sha256'],fragments=spans))
        assert not expected
        ranges.append(dict(volume=number,firstPhysicalPage=first,lastPhysicalPage=len(state['pages']),
                           sourceFirstPhysicalPage=4,sourceSha256=receipt['pdfSha256'],bookmark=label))
    state['activeFrameId'] = state['pages'][0]['frames'][0]['frameId']
    assert len(expected_records)==sum(v['printParagraphs'] for v in catalogue)
    # Validate each source definition and example, including split fragments,
    # before packing them into the native format's page-sized text records.
    sc.pe.validate(state)
    edition['verses']=[]
    for page in state['pages']:
        pid=page['pageId']
        text=sc.pe.text_of(page)
        assert text.strip()
        edition['verses'].append(dict(id=pid,sha256=sc.pe.hash_text(text),
                                      fragments=[dict(pageId=pid,start=0,end=len(text))]))
    sc.pe.validate(state)
    return state, ranges


def bind(book, *, pdf_name=None, native_name=None):
    app = QApplication.instance() or QApplication([])
    state,ranges = assemble(book)
    print('Assembled',len(state['pages']),'pages, including one title.',flush=True)
    with TemporaryDirectory(dir=book.stage,ignore_cleanup_errors=True) as tmp:
        pdf = Path(tmp)/(pdf_name or book.title+' - Duplex Print.pdf')
        count = render_duplex(state,pdf,book.title,use_printed_folios=True,binding_blank=False,
                              bookmark_letter_openings=True)
        assert count == len(state['pages'])
        publish(book,state,ranges,pdf,native_name=native_name)


def publish(book,state,ranges,pdf, *, native_name=None):
    target = book.folders['print']
    native = pdf.with_name(native_name or book.title+'.vay')
    count = len(state['pages'])
    fingerprint = sha(pdf)
    edition = state['printEdition']
    edition['sourceSha256'] = fingerprint
    assert [edition['pages'][p['pageId']]['folio'] for p in state['pages']] == [None,*range(1,count)]
    session = FileSession(ROOT,source_fonts=False,recovery=False)
    session.remember=lambda *a,**k:None
    session.log.emit=lambda *a,**k:None
    try:
        for font in state['fontSources']:
            session.fonts.register(session.fonts.document_path(font['path'],font['sha256']),font['sha256'])
        session._restore(state,take_ownership=True)
        session._state=state
        session.save(native,preview_mode='one')
        session.open(native,advance_revision=False)
        reopened=session.state
        # Qt encodes the active title's two paragraphs as separate story
        # blocks on save. Its text, measured lines, and all folios must agree.
        assert reopened['printEdition']==edition and reopened['pages'][1:]==state['pages'][1:]
        assert sc.pe.text_of(reopened['pages'][0])==sc.pe.text_of(state['pages'][0])
        assert all(reopened[k]==state[k] for k in state if k not in ('pages','printEdition'))
    finally:
        session.finish()
    report = dict(file=pdf.name,physicalPDFPages=count,duplexSheets=(count+1)//2,
                  titlePages=1,blankPages=0,interVolumeBlanks=[],volumes=ranges,
                  openingPhysicalPage=1,pageLayout='TwoPageRight',sha256=fingerprint,
                  allPageContentsAndBoxesVerified=True,volumeBookmarksVerified=True,
                  letterBookmarks=sum(spec['kind']=='opening' for spec in edition['pages'].values()),
                  outsideFolioParityVerified=True,continuousFoliosVerified=True)
    manuscript = dict(file=native.name,sha256=sha(native),pages=count,physicalPDFPages=count,
                      nativeReopened=True,everyNativePageTextAndPrintGeometryVerified=True)
    staged_reports=[(pdf.parent/name,book.work/name) for name in ('complete-pdf.json','complete-print-native.json')]
    write_json(staged_reports[0][0],report)
    write_json(staged_reports[1][0],manuscript)
    replacements=[(pdf,target/pdf.name),(native,target/native.name),*staged_reports]
    with TemporaryDirectory(dir=book.stage) as backup:
        restored=[]
        for staged,dest in replacements:
            if dest.exists():
                shutil.copyfile(dest,Path(backup)/dest.name)
        for path,receipt in zip((pdf,native),staged_reports,strict=True):
            if receipt[1].exists():
                old=json.loads(receipt[1].read_text('utf8'))
                assert sha(Path(backup)/path.name)==old['sha256'], f'Print master edited independently: {path.name}'
        try:
            for staged,dest in replacements:
                staged.replace(dest)
                restored.append(dest)
        except OSError:
            for dest in reversed(restored):
                previous=Path(backup)/dest.name
                if previous.exists():
                    previous.replace(dest)
                else:
                    dest.unlink()
            raise
    print(count,'pages,',len(ranges),'alphabetical ranges',flush=True)
