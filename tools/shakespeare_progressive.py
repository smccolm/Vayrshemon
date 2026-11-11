"""Collect the issued four-column manuscripts in the sealed Letter edition's order."""
import argparse
from copy import deepcopy

from tools.compose_historical_book import texts
from tools.shakespeare_collected import DEST as LETTER, PROJECT, ROOT, TITLE, digest, read, saved_source, sources
from vayrshemon import saved_preview
from vayrshemon.json_stream import write_atomic
from vayrshemon.native_storage import MAX_FILE_BYTES, pack, unpack


EDITION = TITLE + ' - Four-Column Progressive Edition'
OUTPUT = ROOT / 'Saves' / (EDITION + ' v0.14') / (EDITION + '.vay')
MANIFEST = OUTPUT.parent / 'edition-manifest.json'
STAGE = ROOT / '.local' / 'shakespeare-progressive'
STAGED = STAGE / OUTPUT.name
DOCUMENT_ID = 'document.shakespeare.collected.progressive'


def ordered_sources():
    seal = read(LETTER.parent / 'FROZEN.json')
    assert digest(LETTER) == seal['nativeSha256']
    state = unpack(read(LETTER))['state']
    names = [s['name'] for s in state['printEdition']['sections']]
    book_paths = {w['title']: w for w in sources()}
    receipt = read(LETTER.parent / 'edition-manifest.json')
    assert receipt['nativeSha256'] == seal['nativeSha256']
    assert names == [s['title'] for s in receipt['sources']]
    assert len(names) == len(set(names)) == len(book_paths) == 42
    works = [book_paths[name] for name in names]
    for work, source in zip(works, receipt['sources'], strict=True):
        assert (work['output'], work['sha256']) == (source['file'], source['sha256'])
    return works, seal['nativeSha256']


def opened(work):
    path = saved_source(work['output'])
    if digest(path) != work['sha256']:
        raise ValueError(f'Issued manuscript differs from its receipt: {path}')
    return unpack(read(path))


def collect():
    works, letter_sha = ordered_sources()
    head = read(PROJECT / 'project.json')['forgeHead']
    report = []
    active = None
    pages, frames, objects, revisions = [], {}, {}, {}
    page_ids, frame_ids = set(), set()
    for work in works:
        payload = opened(work)
        source = payload['state']
        if not pages:
            common = {k:deepcopy(source[k]) for k in ('fontSources','recipe','features','styles','paint','pageNumbering')}
            typesetting = deepcopy({k:v for k,v in source['typesetting'].items() if k!='frames'})
            assert not typesetting['flows']
            book = dict(common, documentId=DOCUMENT_ID, title=EDITION, revision=0,
                        activeFrameId=source['activeFrameId'], view=deepcopy(source['view']))
            preview = deepcopy(payload['shellPreview'])
            assert preview['pageMode']=='two' and preview['pageIds']==[p['pageId'] for p in source['pages'][:2]]
            engine = payload['engine']
        assert all(source[k]==value for k,value in common.items())
        assert all(source['typesetting'][k]==value for k,value in typesetting.items())
        assert len(source['pages'])==work['pages'] and work['pages']%2==0
        language=source['language']
        assert not language['links']
        objects.update(language['objects'])
        for revision in language['revisions']:
            assert revisions.setdefault(revision['id'], revision)==revision
        if work.get('languageHead')==head:
            active=language['activeRevisionId']
        start=len(pages)+1
        units=0
        for i,page in enumerate(source['pages']):
            if page['pageId'] in page_ids:
                raise ValueError('Duplicate source page identity')
            page_ids.add(page['pageId'])
            if i==0:
                page['name']='Work opening · '+work['title']
            ordered=sorted(page['frames'],key=lambda f:int(f['x']))
            assert len(ordered)==2
            if i%2==0:
                units+=len(texts(ordered[0]))
            for frame in ordered:
                fid=frame['frameId']
                if fid in frame_ids:
                    raise ValueError('Duplicate source frame identity')
                frame_ids.add(fid)
                frame['content']['document']['documentId']=DOCUMENT_ID
            pages.append(page)
        frames.update(source['typesetting']['frames'])
        report.append(dict(title=work['title'],file=work['output'],sha256=work['sha256'],
                           firstPage=start,lastPage=len(pages),units=units,languageRevision=language['activeRevisionId']))
        print(f'{start}–{len(pages)}  {work["title"]}',flush=True)
    assert active is not None
    book.update(pages=pages,typesetting=dict(typesetting,frames=frames),
                language=dict(version='1.0.0',objects=objects,revisions=list(revisions.values()),links=[],activeRevisionId=active))
    # The thumbnail depicts exactly the same first spread, with the same
    # rendering globals, frame identities, and folios 1 and 2.
    preview.update(revision=book['revision'],stateSha256=saved_preview.state_hash(book))
    wire=pack(dict(format='vayrshemon.document',formatVersion='0.6.0',shellPreview=preview,
                   state=book,history=[],engine=engine))
    write_atomic(STAGED,wire,limit=MAX_FILE_BYTES)
    write_atomic(STAGE/'edition-manifest.json',dict(title=EDITION,nativeSha256=digest(STAGED),
                 sealedOrderReference=str(LETTER.relative_to(ROOT).as_posix()),sealedNativeSha256=letter_sha,
                 plays=38,poetryWorks=4,pages=len(pages),spreads=len(pages)//2,
                 columns=['Vayrshemon','Transliteration 7','Construction gloss','English source'],
                 units=sum(w['units'] for w in report),works=report))
    print('Staged complete collection',flush=True)


def verify():
    works, letter_sha = ordered_sources()
    receipt=read(STAGE/'edition-manifest.json')
    assert digest(STAGED)==receipt['nativeSha256'] and letter_sha==receipt['sealedNativeSha256']
    saved=unpack(read(STAGED))
    state=saved['state']
    saved_preview.validate(saved['shellPreview'],state)
    merged_revisions={r['id']:r for r in state['language']['revisions']}
    position=0
    for work, entry in zip(works,receipt['works'],strict=True):
        source=opened(work)['state']
        assert work['title']==entry['title'] and position+1==entry['firstPage']
        for k in ('paint','features','recipe','styles','fontSources','pageNumbering'):
            assert source[k]==state[k],(work['title'],k)
        assert all(merged_revisions[r['id']]==r for r in source['language']['revisions'])
        assert all(state['language']['objects'][k]==v for k,v in source['language']['objects'].items())
        assert all(state['typesetting']['frames'][k]==v for k,v in source['typesetting']['frames'].items())
        for i,original in enumerate(source['pages']):
            bound=state['pages'][position]
            if i==0:
                assert bound['name']=='Work opening · '+work['title']
                original['name']=bound['name']
            for frame in original['frames']:
                frame['content']['document']['documentId']=DOCUMENT_ID
            # This covers every run, glyph/font assignment, paragraph style,
            # measured spacing, coordinate and column on both facing pages.
            assert original==bound,(work['title'],i+1)
            position+=1
        assert position==entry['lastPage']
    assert position==receipt['pages']==len(state['pages'])
    assert receipt['units']==read(LETTER.parent/'edition-manifest.json')['sourceUnits']
    print(f'Verified all {position} saved pages against the 42 issued manuscripts.',flush=True)
    if OUTPUT.exists() and digest(OUTPUT)!=receipt['nativeSha256']:
        raise FileExistsError(OUTPUT)
    OUTPUT.parent.mkdir(exist_ok=True)
    STAGED.replace(OUTPUT)
    write_atomic(MANIFEST,dict(receipt,verifiedAgainstIssuedPages=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['build','verify'])
    args=parser.parse_args()
    (collect if args.operation=='build' else verify)()
