"""Compose the single-column native dictionary using the approved Letter specimen."""
from itertools import groupby
from dataclasses import dataclass
from pathlib import Path
import re
import os
import hashlib
import json
import gc
from statistics import median
from tempfile import TemporaryDirectory
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QApplication
from tools import shakespeare_collected as sc
from tools.dictionary_rows import CHART,filing_initial,native_letter_names
from tools.dictionary_corpus import WORK, ROOT, normalize, sha
from tools.dictionary_lexicon import load_gzip
from tools.shakespeare_collected_pdf import render_duplex
from vayrshemon import language

STAGE=ROOT/'.local/dictionary-layout/print'
DEST=ROOT/'Saves/Vayrshemon Dictionary - Letter Print Edition'
NATIVE='Vayrshemon Dictionary.vay'
PDF='Vayrshemon Dictionary - Duplex Print.pdf'
BODY_TOP=103
BODY_BOTTOM=720
ENTRY_GAP=6

def typeset_article(head, senses, proof, digits, width, head_size, body_size):
    text = ''
    refs = []
    output = []
    bottom = 0
    def part(segment):
        nonlocal text
        if text:
            text += ' '
        start = len(text)
        text += segment
        return start,len(text)

    def paragraph(prefix, span, size, left, hanging, gap):
        nonlocal bottom
        start, stop = span
        words = list(re.finditer(r'\S+',text[start:stop]))
        x = left
        blocks = []
        for a,b,pt in prefix:
            ink = proof.ink(text[a:b],pt)
            blocks.append((a,b,pt,x-ink.left(),ink))
            x += ink.width()+4.5
        i = 0
        while i < len(words):
            a = start+words[i].start()
            j = i
            while j+1 < len(words) and x+proof.ink(text[a:start+words[j+1].end()],size).width() <= width:
                j += 1
            b = start+words[j].end()
            ink = proof.ink(text[a:b],size)
            if x+ink.width()>width and blocks:
                baseline=bottom+gap-min(run[-1].top() for run in blocks)
                output.extend((aa,bb,pt,dx,baseline,box) for aa,bb,pt,dx,box in blocks)
                bottom=baseline+max(run[-1].bottom() for run in blocks)
                x=hanging
                blocks=[]
                gap=2.7
                continue
            draw_size=size
            while x+ink.width()>width:
                draw_size-=1
                if draw_size<8:raise ValueError(('Word exceeds the measure',text[a:b]))
                ink=proof.ink(text[a:b],draw_size)
            blocks.append((a,b,draw_size,x-ink.left(),ink))
            baseline = bottom+gap-min(run[-1].top() for run in blocks)
            output.extend((a,b,pt,dx,baseline,box) for a,b,pt,dx,box in blocks)
            bottom = baseline+max(run[-1].bottom() for run in blocks)
            blocks = []
            i = j+1
            x = hanging
            gap = 2.7

    for pos,sense in enumerate(senses):
        prefix = []
        start = len(text) + int(bool(text))
        if pos==0:
            a,b = part(head+':')
            pt=head_size
            while proof.ink(text[a:b],pt).width()>width-35:pt-=1
            prefix.append((a,b,pt))
        if len(senses)>1:
            a,b = part(digits(pos+1))
            prefix.append((a,b,21))
        paragraph(prefix,part(sense['definition']),body_size,
                  0 if pos==0 else 12,12,0 if pos==0 else 5)
        examples = sense['examples'] if 'examples' in sense else [sense['example']]
        for example in examples:
            paragraph([],part(example),23,24,24,3.2)
        refs.append((sense['id'],start,len(text)))
    return text,refs,output,bottom

def initial_placement(proof,cap):
    for size in range(68,39,-1):
        bounds=proof.ink(cap,size)
        baseline=min(78,85-bounds.bottom())
        if baseline+bounds.top()>=sc.TOP:return size,baseline
    raise ValueError('Initial does not fit above header rule: '+cap)

@dataclass
class PagePiece:
    head: str
    letter: str
    text: str
    senses: list
    runs: list
    start: int
    end: int
    shift: float

def article_pages(rows,proof):
    """Fill the measure one ink line at a time, preserving original character offsets."""
    pieces=[]
    bottom=BODY_TOP
    for _,group in groupby(rows,key=lambda r:normalize(r['text'].partition('. ')[0])):
        group=list(group)
        head=group[0]['text'].partition('. ')[0]
        letter=filing_initial(head)
        senses=[dict(id=r['id'],**r['article']) for r in group]
        raw,spans,runs,_=typeset_article(head,senses,proof,sc.digits,sc.MEASURE,32,26)
        baselines=[]
        for baseline,at_baseline in groupby(runs,key=lambda run:run[4]):
            line=list(at_baseline)
            baselines.append((line,baseline+min(r[5].top() for r in line),
                              baseline+max(r[5].bottom() for r in line)))
        i=0
        while i<len(baselines):
            shift=bottom+(ENTRY_GAP if pieces else 0)-baselines[i][1]
            j=i
            while j<len(baselines) and shift+baselines[j][2]<=BODY_BOTTOM:
                j+=1
            if j>i:
                start=baselines[i][0][0][0]
                # Keep the inter-word space when a definition or example crosses pages.
                end=baselines[j][0][0][0] if j<len(baselines) else len(raw)
                placed=[r for line,_,_ in baselines[i:j] for r in line]
                pieces.append(PagePiece(head,letter,raw,spans,placed,start,end,shift))
                bottom=shift+baselines[j-1][2]
            if j<len(baselines):
                if not pieces:raise ValueError(('Line exceeds the height of a page',head))
                yield pieces
                pieces=[]
                bottom=BODY_TOP
            i=j
    if pieces:yield pieces

def verify_flow(state,rows,*,legacy=False):
    edition=state['printEdition']
    pages={p['pageId']:sc.pe.text_of(p) for p in state['pages']}
    records={r['id']:r['fragments'] for r in edition['verses']}
    def contents(fragments):
        return ''.join(pages[f['pageId']][f['start']:f['end']] for f in fragments)
    ids=[r['id'] for r in rows]
    assert [k for k in records if k!='title' and not k.startswith('nav/')]==ids
    assert all('[' not in t and ']' not in t for t in pages.values())
    names=native_letter_names()
    expected_sections=[]
    section_tops={}
    ranges={}
    split_entries=split_senses=heads=0
    previous_letter=None
    for _,group in groupby(rows,key=lambda r:normalize(r['text'].partition('. ')[0])):
        group=list(group)
        head=group[0]['text'].partition('. ')[0]
        letter=filing_initial(head)
        heads+=1
        prev=None
        for i,r in enumerate(group,1):
            fragments=records[r['id']]
            first=fragments[0]
            pid=first['pageId']
            if letter!=previous_letter:
                name=names[letter][0]
                expected_sections.append((name,pid))
                first_run=next(run for run in edition['pages'][pid]['lines'] if run['start']==first['start'])
                section_tops[name]=first_run['bounds'][1]
                previous_letter=letter
            parts=[head+':'] if i==1 or (legacy and pid!=prev) else []
            if len(group)>1:parts.append(sc.digits(i))
            parts.extend((r['article']['definition'],r['article']['example']))
            assert contents(fragments)==' '.join(parts),r['id']
            prev=pid
            split_senses+=int(pid!=fragments[-1]['pageId'])
            for f in fragments:
                bounds=ranges.setdefault(f['pageId'],[head,head])
                bounds[1]=head
        split_entries+=int(records[group[0]['id']][0]['pageId']!=fragments[-1]['pageId'])
    assert expected_sections==[(s['name'],s['pageId']) for s in edition['sections']]
    gaps=[]
    prev_gap=None
    for pid,source in list(pages.items())[2:]:
        first,last=ranges[pid]
        assert contents(records['nav/'+pid+'/range'])==(first+' – '+last if first!=last else first)
        body=edition['pages'][pid]['lines'][3:]
        assert body
        first_baseline=body[0]['baseline']
        ink=[r['bounds'] for r in body if r['baseline']==first_baseline]
        top=min(b[1] for b in ink)
        first_height=max(b[1]+b[3] for b in ink)-top
        if not legacy:
            assert abs(top-BODY_TOP)<.01,pid
            if prev_gap is not None:
                assert prev_gap < first_height+ENTRY_GAP+.01,('A line fits on the preceding page',pid,prev_gap,first_height)
        prev_gap=BODY_BOTTOM-max(r['bounds'][1]+r['bounds'][3] for r in body)
        assert prev_gap>=-.01,pid
        gaps.append(prev_gap)
    stats=dict(headwords=heads,entriesCrossingPages=split_entries,sensesCrossingPages=split_senses,
               nonfinalBodyPages=len(gaps)-1,medianUnusedBodyPt=round(median(gaps[:-1]),2),
               maximumUnusedBodyPt=round(max(gaps[:-1]),2))
    return stats,section_tops

def build(ledger=None):
    STAGE.mkdir(exist_ok=True,parents=True)
    app=QApplication.instance() or QApplication([])
    led=load_gzip(ledger or WORK/'dictionary-rows.json.gz')
    rows=[r for r in led['rows'] if 'article' in r]
    assert len(rows)==led['counts']['examples']
    title=led['rows'][0]['text']
    sections=native_letter_names()
    expected={r['id']:r['article'] for r in rows}
    canonical=hashlib.sha256(json.dumps([[r['id'],r['text'].partition('. ')[0],r['article']['definition'],r['article']['example']] for r in rows],ensure_ascii=False).encode()).hexdigest()
    template=ROOT/'Saves/Paradise Lost - Letter Print Edition/Paradise Lost.vay'
    state=sc.unpack(sc.read(template))['state']
    v=sc.Volume.__new__(sc.Volume)
    v.proof=proof=sc.Typesetter(next(f for f in state['fontSources'] if f['fontId']==sc.pe.DRAMA_PUNCT))
    v.state=state
    v.prototype=state['pages'][4]
    v.records={};v.page=None;v.start_body=3
    v.edition=dict(version=1,layoutVersion=sc.pe.COLLECTED,typography=dict(sc.pe.COMPACT_TYPE),
        languageVersion='Vayrshemon Dictionary',sourceSha256=canonical,ledgerSha256=canonical,
        assets={},pages={},verses=[],sections=[])
    state.update(title='Vayrshemon Dictionary',documentId='document.dictionary.letter',pages=[],revision=0,
                 printEdition=v.edition,language=language.initial())
    v.new_page('title','Vayrshemon Dictionary')
    v.label('title',title,48,323)
    v.new_page('blank','Blank')
    last_letter=None
    for pieces in article_pages(rows,proof):
        first=pieces[0]
        final=pieces[-1]
        changed=last_letter!=final.letter
        first_name,slotname=sections[first.letter]
        name=first_name
        if first.letter!=final.letter:
            last_name,last_slot=sections[final.letter]
            name+=' – '+last_name
            slotname+=' – '+last_slot
        v.new_page('opening' if changed else 'body',name)
        nav='nav/'+v.pid+'/'
        cap=next(chr(row[1]) for row in CHART if chr(row[2])==first.letter)
        cap_size,baseline=initial_placement(proof,cap)
        v.label(nav+'initial',cap,cap_size,baseline,at=0,width=60,align='left')
        start=proof.ink(cap,cap_size).width()+12
        label_width=proof.ink(slotname,27).width()
        v.label(nav+'letter',slotname,27,77,at=start,width=label_width+1,align='left')
        room=sc.MEASURE-start-label_width-16
        guide=first.head+' – '+final.head if first.head!=final.head else first.head
        size=22
        while proof.ink(guide,size).width()>room:
            size-=1
            if size<8:raise ValueError(('Running head exceeds the measure',guide))
        v.label(nav+'range',guide,size,77,align='right')
        path=QPainterPath();path.addRect(QRectF(v.left,89,sc.MEASURE,.55))
        v.page['paths']=[sc.pe.encode_path(path,'dictionary-running-head-rule')]
        for piece in pieces:
            if piece.letter!=last_letter:
                v.edition['sections'].append(dict(number=len(v.edition['sections'])+1,
                                                  name=sections[piece.letter][0],pageId=v.pid))
                last_letter=piece.letter
            v.source+='\n'
            offset=len(v.source)-piece.start
            v.source+=piece.text[piece.start:piece.end]
            for key,a,b in piece.senses:
                a=max(piece.start,a)
                b=min(piece.end,b)
                if a<b:v.fragment(key,piece.text[a:b],offset+a,offset+b)
            for a,b,pt,dx,baseline,ink in piece.runs:
                v.place(offset+a,offset+b,v.left+dx,piece.shift+baseline,pt,ink)
        if len(state['pages'])%250==0:print(len(state['pages']),'pages composed',flush=True)
    v.finish_page()
    state['activeFrameId']=state['pages'][0]['frames'][0]['frameId']
    by_page={p['pageId']:sc.pe.text_of(p) for p in state['pages']}
    for record in v.records.values():
        raw=''.join(by_page[f['pageId']][f['start']:f['end']] for f in record['fragments'])
        record['sha256']=sc.pe.hash_text(raw)
    stats,section_tops=verify_flow(state,rows)
    assert stats['headwords']==led['counts']['headwords']
    total=len(rows)
    sc.pe.validate(state)
    from tools.dictionary_forge import forge_data
    dataset=forge_data(rows)
    dataset['lexicon']=[e for e in dataset['lexicon'] if e['id'].startswith('native.dictionary.')]
    dataset['corpus']=[];dataset['morphology']=[];dataset['grammar']=[]
    for rec in dataset['lexicon']:
        for sense in rec['senses']:
            article=expected[sense['id'].removeprefix('dictionary.')]
            sense['definition']=article['definition']+'\n'+article['example']
    language.append_revision(state['language'],dataset,'Illustrated native dictionary',preserve_lexicon_order=True)
    sc.pe.validate(state)
    print('Verified print ledger on',len(state['pages']),'pages.',stats,flush=True)
    del by_page,led,rows,expected
    session=sc.FileSession(ROOT,source_fonts=False,recovery=False)
    session.remember=lambda *args:None;session.log.emit=lambda *args,**kwargs:None
    try:
        for f in state['fontSources']:session.fonts.register(session.fonts.document_path(f['path'],f['sha256']),f['sha256'])
        session._restore(state,take_ownership=True)
        session._state=state
        with TemporaryDirectory(dir=STAGE) as folder:
            candidate=Path(folder)/NATIVE
            session.save(candidate,preview_mode='two')
            before=session.capture()
            session.open(candidate,advance_revision=False)
            state=session.capture()
            assert before==state
            candidate.replace(STAGE/NATIVE)
    finally:session.finish()
    print('Verified native reopening.',flush=True)
    export_verified_pages(state,canonical,total,stats,section_tops)

def export_verified_pages(state,canonical,total,stats,section_tops):
    count=render_duplex(state,STAGE/PDF,'Vayrshemon Dictionary',use_printed_folios=True,section_tops=section_tops)
    sc.write(STAGE/'edition-manifest.json',dict(nativeSha256=sha(STAGE/NATIVE),pdfSha256=sha(STAGE/PDF),
        pages=len(state['pages']),physicalPages=count,sections=len(state['printEdition']['sections']),
        headwords=stats['headwords'],definitions=total,articleSha256=canonical,bindingBlank=1,
        pagination=stats,nativeReopenVerified=True,allDefinitionAndExampleFragmentsVerified=True,
        allPDFTextAndBoundsVerified=True))
    print('Verified duplex PDF',count,stats,flush=True)

def verify_and_export(ledger):
    app=QApplication.instance() or QApplication([])
    rows=[r for r in load_gzip(ledger)['rows'] if 'article' in r]
    snapshot=sc.unpack(sc.read(STAGE/NATIVE))['state']
    session=sc.FileSession(ROOT,source_fonts=False,recovery=False)
    session.remember=lambda *args:None;session.log.emit=lambda *args,**kwargs:None
    try:
        session.open(STAGE/NATIVE,advance_revision=False)
        state=session.capture()
        assert state['printEdition']==snapshot['printEdition']
        for saved,opened in zip(snapshot['pages'],state['pages'],strict=True):
            assert saved['pageId']==opened['pageId'] and sc.pe.text_of(saved)==sc.pe.text_of(opened)
        sc.pe.validate(state)
        ed=state['printEdition']
        legacy=not any(len(r['fragments'])>1 for r in ed['verses'])
        stats,section_tops=verify_flow(state,rows,legacy=legacy)
        total=len(rows)
        canonical=hashlib.sha256(json.dumps([[r['id'],r['text'].partition('. ')[0],r['article']['definition'],r['article']['example']] for r in rows],ensure_ascii=False).encode()).hexdigest()
        assert ed['ledgerSha256']==canonical
        print('Verified all',total,'definition/example pairs in the reopened book',flush=True)
    finally:session.finish()
    del snapshot,rows
    gc.collect()
    export_verified_pages(state,canonical,total,stats,section_tops)

def install():
    import shutil
    from tools.dictionary_corpus import BOOK,EDITION,read
    pub=read(WORK/'publication.json')
    proof=read(WORK/'verification.json')
    manifest=read(STAGE/'edition-manifest.json')
    assert manifest['nativeSha256']==sha(STAGE/NATIVE) and manifest['pdfSha256']==sha(STAGE/PDF)
    assert pub['sha256']==sha(BOOK/(EDITION+'.vay'))==proof['nativeSha256']
    assert pub['ledgerSha256']==sha(WORK/'dictionary-rows.json.gz')
    led=load_gzip(WORK/'dictionary-rows.json.gz')
    rows=[r for r in led['rows'] if 'article' in r]
    canonical=hashlib.sha256(json.dumps([[r['id'],r['text'].partition('. ')[0],r['article']['definition'],r['article']['example']] for r in rows],ensure_ascii=False).encode()).hexdigest()
    assert canonical==manifest['articleSha256'] and manifest['definitions']==pub['examples']==proof['exampleSentencesVerified']
    # Connect the embedded print lexicon to the final, paginated source ledger.
    app=QApplication.instance() or QApplication([])
    session=sc.FileSession(ROOT,source_fonts=False,recovery=False)
    session.remember=lambda *args:None;session.log.emit=lambda *a,**kw:None
    try:
        session.open(STAGE/NATIVE,advance_revision=False)
        state=session.capture()
        dataset=language.dataset(state['language'])
        source,=[v for v in dataset['sources'] if v['id']=='dictionary.native.readings']
        if source['sha256']!=pub['ledgerSha256']:
            source['sha256']=pub['ledgerSha256']
            state['language']=language.initial()
            language.append_revision(state['language'],dataset,'Illustrated native dictionary',preserve_lexicon_order=True)
            session._restore(state,take_ownership=True)
            session._state=session.capture()
            with TemporaryDirectory(dir=STAGE) as folder:
                new=Path(folder)/NATIVE
                session.save(new,preview_mode='two');before=session.capture()
                session.open(new,advance_revision=False)
                assert session.capture()==before and before['printEdition']==state['printEdition']
                new.replace(STAGE/NATIVE)
            manifest['nativeSha256']=sha(STAGE/NATIVE)
    finally:session.finish()
    manifest['sourceProgressiveSha256']=pub['sha256']
    manifest['sourceLedgerSha256']=pub['ledgerSha256']
    sc.write(STAGE/'edition-manifest.json',manifest)
    names=[NATIVE,PDF,'edition-manifest.json']
    if DEST.exists():
        old=read(DEST/'edition-manifest.json')
        for f,k in [(NATIVE,'nativeSha256'),(PDF,'pdfSha256')]:
            if sha(DEST/f)!=old[k]:raise ValueError('Independent edits in published '+f)
        backup=STAGE/'editions'/old['nativeSha256']
        backup.mkdir(parents=True,exist_ok=True)
        for f in names:
            if not (backup/f).exists():shutil.copy2(DEST/f,backup/f)
    with TemporaryDirectory(dir=DEST.parent) as tmp:
        staged=Path(tmp)/DEST.name;staged.mkdir()
        for f in names:shutil.copy2(STAGE/f,staged/f)
        if not DEST.exists():staged.rename(DEST)
        else:
            try:
                for f in names:(staged/f).replace(DEST/f)
            except BaseException:
                for f in names:shutil.copy2(backup/f,DEST/f)
                raise
    print('Published',DEST,flush=True)

if __name__=='__main__':
    import sys
    try:
        if sys.argv[1:]==['--install']:install()
        elif sys.argv[1:2]==['--export']:verify_and_export(Path(sys.argv[2]) if len(sys.argv)>2 else WORK/'dictionary-rows.json.gz')
        else:build(Path(sys.argv[1]) if len(sys.argv)>1 else None)
    except Exception as exc:
        if hasattr(exc,'absolute_path'):
            raise RuntimeError((list(exc.absolute_path),exc.validator,exc.validator_value)) from None
        raise
