"""Typeset the reciprocal dictionary/thesaurus in alphabetic native volumes and verify both formats."""
import argparse
import gc
import gzip
import hashlib
import json
import os
import re
import sys
import time
from tempfile import TemporaryDirectory
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path

from tools.semantic_expansion import DEST,ROOT,STAGE,WORK,prepare_lang
from tools.dictionary_lexicon import load_gzip,save_gzip
from tools.dictionary_rows import collate,filing_initial,native_letter_names
from tools.dictionary_corpus import sha
from tools.unta_language import quantity

BLOCK=1600
FOLDER={'progressive':DEST/'Four-Column Progressive Edition','print':DEST/'Letter Print Edition'}
LABELS={'sense':('near:m meaning','Related sense'),'narrower sense':('small:m part of meaning','Narrower sense'),'sibling distinction':('compare:imp','Compare'),
        'allusion':('name and example','Allusion'),'figurative bridge':('image and meaning','Figurative connection'),
        'connected idea':('near:m thought','Related idea'),'associated sense':('near:m meaning','Associated sense'),
        'application':('use','Field of use'),'earlier thesaurus':('other word:pl','Earlier thesaurus'),
        'same lexical sense':('same:m meaning','Shared sense'),'distinguish':('difference','Distinguish')}
TITLE='Vayrshemon Dictionary and Thesaurus'
@lru_cache(maxsize=None)
def digit(n):return quantity(n,notation='digits')['form']

def brief(s,limit=70):
    return s if len(s)<=limit else s[:limit].rsplit(' ',1)[0]+'…'

def prep():
    data=load_gzip(WORK/'reciprocal-lexicon.json.gz');nodes=data['nodes'];lang=prepare_lang()
    stage=STAGE/'volumes';stage.mkdir(exist_ok=True)
    native={k:lang.compile(v[0])['text'].strip('.') for k,v in LABELS.items()}
    title=lang.compile('book of word:pl and near:m meaning:pl')['text']
    guide=lang.compile('each word seek:imp. after example near:m word:pl see:imp. mark before word book show:pr.')['text']
    count=(len(nodes)+BLOCK-1)//BLOCK
    catalogue=[]
    for vol in range(1,count+1):
        group=nodes[(vol-1)*BLOCK:vol*BLOCK];meta=dict(number=vol,title=title,guide=guide,first=group[0]['roman'],last=group[-1]['roman'],
             rangeNative=[group[0]['form'],group[-1]['form']],name=f'Volume {vol:02d}',heads=len(group))
        rows=[];printed=[]; guideen='Use the volume number before a cross-reference to find the term in its alphabetical volume.'
        rows.append(dict(id='title',section='opening',reference=TITLE,text=title+' '+digit(vol)+'. '+guide,gloss='Book of words and related meanings. '+str(vol)+'. Seek each word. After the example read the other entries. The number identifies the volume.',source=TITLE+f', volume {vol}. '+meta['first']+' – '+meta['last']+'. '+guideen))
        for n in group:
            h=n['form'];ix=n['id'];section='letter-'+str(ord(filing_initial(h)));roman=n['roman']
            for s_no,r in enumerate(n['reads']):
                sk=f'w{ix}.{s_no}';header=h+': ' if s_no==0 else ''
                d=r['definition'];e=r['example'];english=r['meaning']; engex=r['exampleEnglish'];ref=' '.join(r['references'])
                if len(ref)>350:ref=' '.join(r['references'][:3])
                constr=r.get('construction')
                if constr:
                    whole=header+d+' '+e
                    rows.append(dict(id=sk,section=section,reference=roman,text=whole,gloss=constr,source=english+' Example: '+engex+' '+ref))
                else:
                    pre=n['label']+'. '
                    rows.extend([dict(id=sk,section=section,reference=roman,text=header+d,gloss=pre+r['gloss'],source=n['label']+'. '+english+' '+ref),
                          dict(id=sk+'x',section=section,reference=roman,text=e,gloss=r.get('exampleGloss',pre),source=engex)])
                printed.append(dict(id=sk,head=h,kind='definition',text=(h+': ' if s_no==0 else '')+(digit(s_no+1)+' ' if len(n['reads'])>1 else '')+d))
                printed.append(dict(id=sk+'-ex',head=h,kind='example',text=e))
            bytype=defaultdict(list)
            for neighbor,types in n['links']:
                # A pair can have several motives. The analytical index retains all of them.
                tag=next(t for t in ('sibling distinction','allusion','figurative bridge','distinguish','narrower sense','sense','earlier thesaurus','same lexical sense','application','associated sense','connected idea') if t in types)
                bytype[tag].append(neighbor)
            refs_print=[];refs_src=[];refs_gl=[];seq=0
            def flush():
                nonlocal seq
                if not refs_print:return
                key=f'w{ix}-see{seq}';seq+=1
                z=' '.join(refs_print)
                rows.append(dict(id=key,section=section,reference=roman,text=z,gloss=' '.join(refs_gl),source=' '.join(refs_src)))
                printed.append(dict(id=key,head=h,kind='references',text=z))
                refs_print.clear();refs_src.clear();refs_gl.clear()
            for tag,groupids in bytype.items():
                for start in range(0,len(groupids),5):
                    ids=groupids[start:start+5]
                    terms=[nodes[j] for j in ids]
                    s=native[tag]+': '+', '.join(digit(t['id']//BLOCK+1)+' '+t['form'] for t in terms)+'.'
                    trans=LABELS[tag][1]+': '+', '.join(str(t['id']//BLOCK+1)+' '+t['roman'] for t in terms)+'.'
                    eng=LABELS[tag][1]+': '+', '.join(str(t['id']//BLOCK+1)+' '+t['roman']+' ('+brief(t['label'],45)+')' for t in terms)+'.'
                    if refs_src and len(' '.join(refs_src))+len(eng)>245:flush()
                    refs_print.append(s);refs_src.append(eng);refs_gl.append(trans)
            flush()
        meta.update(rows=len(rows),printParagraphs=len(printed))
        save_gzip(stage/f'{vol:02d}.json.gz',dict(meta=meta,rows=rows,print=printed))
        catalogue.append(meta)
    (WORK/'volumes.json').write_text(json.dumps(catalogue,ensure_ascii=False,indent=1),encoding='utf8')
    print(len(catalogue),'volumes prepared',flush=True)

def volume(kind,num):
    from PySide6.QtCore import QLockFile

    stage=STAGE/(kind+f'-{num:02d}')
    stage.mkdir(exist_ok=True,parents=True)
    lock=QLockFile(str(stage/'publication.lock'))
    lock.setStaleLockTime(0)
    if not lock.lock():
        raise OSError(f'Could not lock {stage}')
    try:
        return render_volume(kind,num)
    finally:
        lock.unlock()

def render_volume(kind,num):
    from PySide6.QtWidgets import QApplication
    from tools.dictionary_layout import DictionaryLayout
    from tools import shakespeare_collected as sc
    from tools.comprehensive_grammar_print import lines_for
    from tools.thesaurus_print import ThesaurusVolume
    from tools.shakespeare_collected_pdf import render_duplex
    from vayrshemon import language
    from vayrshemon.file_api import FileSession
    source=STAGE/'volumes'/f'{num:02d}.json.gz';ledger=load_gzip(source);meta=ledger['meta']
    folder=FOLDER[kind];folder.mkdir(exist_ok=True,parents=True)
    stub=meta['name'];label=TITLE+' · '+stub
    stamp=hashlib.sha256(json.dumps(ledger[kind=='print' and 'print' or 'rows'],ensure_ascii=False).encode('utf8')).hexdigest()
    receipts=WORK/'Publication';receipts.mkdir(exist_ok=True);receipt=receipts/f'{kind}-{num:02d}.json'
    native=folder/(stub+'.vay');pdf=folder/(stub+' - Duplex Print.pdf')
    if receipt.exists():
        old=json.loads(receipt.read_text('utf8'))
        if old['ledger']==stamp and native.exists() and old['sha256']==sha(native) and (kind!='print' or pdf.exists() and sha(pdf)==old['pdfSha256']):return (kind,num,'already checked')
    stage=STAGE/(kind+f'-{num:02d}');stage.mkdir(exist_ok=True)
    app=QApplication.instance() or QApplication([])
    if kind=='progressive':
        from PySide6.QtCore import QCoreApplication,QEvent
        class LexicalLayout(DictionaryLayout):
            """Measure the usual spread first; extend the window whenever all candidates fit."""
            def measured(self,group):
                QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
                end=min(len(group),getattr(self,'previous_count',7)+2)
                while True:
                    count,state,error=super().measured(group[:end])
                    if count<end or end==len(group):
                        self.previous_count=count
                        return count,state,error
                    end=min(len(group),end+4)
        v=LexicalLayout(title=label,document_id=f'document.reciprocal.{num}',id_prefix=f'reciprocal{num}',
          column_names=('Vayrshemon','Transliteration 7','Construction gloss','English definition, use and sources'),cache_root=stage)
        # The fonts used by this typesetting job are immutable, hash-verified buffers.
        # Recheck changed on-disk locators immediately, and all locators before issuing the volume.
        resolve_face=v.session.fonts.resolve
        verified={}
        def resolve_for_composition(identity):
            face=v.session.fonts.faces.get(identity)
            if face is None:return resolve_face(identity)
            status=face.path.stat()
            fingerprint=(face.path,status.st_size,status.st_mtime_ns,status.st_ctime_ns)
            if verified.get(identity)!=fingerprint:
                face=resolve_face(identity)
                verified[identity]=fingerprint
            return face
        v.session.fonts.resolve=resolve_for_composition
        try:
            report,idx=v.build(ledger['rows'],stage/native.name,stamp)
            for identity in verified:resolve_face(identity)
        finally:v.session.finish()
        file=FileSession(ROOT,source_fonts=False,recovery=False)
        try:
            file.open(stage/native.name,advance_revision=False)
            assert len(file.state['pages'])==report['pages'] and file.saved_page_mode=='two'
        finally:file.finish()
        report['nativeReopened']=True
        folios=[g['leftPage'] for g in idx for ident in g['ids'] if re.fullmatch(r'w\d+\.0',ident)]
        assert len(folios)==meta['heads']
        (receipts/f'folios-{num:02d}.json').write_text(json.dumps(dict(ledger=stamp,pages=folios),separators=(',',':')),encoding='utf8')
    else:
        v=ThesaurusVolume(language.initial(),dict(sha256=stamp),title=label,document_id=f'document.reciprocal.letter.{num}',ledger_sha=stamp)
        v.start_body=3;v.new_page('title',label);v.label('title',meta['title']+' '+digit(num),42,300)
        v.guide_paragraph(meta['guide'],363);v.new_page('blank','Blank')
        expected={};tops={};report={};rows=ledger['print'];current=None;sheet=[];bottom=88
        def draw(sheet):
            nonlocal current
            first,last=sheet[0][0].row['head'],sheet[-1][0].row['head']
            name=native_letter_names()[filing_initial(first)][0];v.new_page('opening' if current!=name else 'body',name)
            if name!=current:
                v.edition['sections'].append(dict(name=name,number=len(v.edition['sections'])+1,pageId=v.pid));tops[name]=88;current=name
            # Independently sized ranges handle long compound headwords.
            left=first;right=last if last!=first else digit(num)
            if max(len(left),len(right))>28:
                left=left[:22];right=right[:22]
            v.running_head(left,right)
            for ln,y in sheet:v.plain_line(ln,y)
        for row in rows:
            row=dict(row,text=' '.join(row['text'].split()))
            expected[row['id']]=row['text']
            size,inset,gap={'definition':(27,0,6),'example':(24,16,3.1),'references':(21,12,2.1)}[row['kind']]
            lines=list(lines_for(v.proof,row,size,inset,gap=gap))
            for ln in lines:
                y=bottom+(ln.gap if sheet else 0)
                if y+ln.ink.height()>720:
                    draw(sheet);sheet=[];y=88
                sheet.append((ln,y));bottom=y+ln.ink.height()
        if sheet:draw(sheet)
        v.finish_page();v.state['activeFrameId']=v.state['pages'][0]['frames'][0]['frameId']
        by_page={p['pageId']:sc.pe.text_of(p) for p in v.state['pages']}
        for k,r in v.records.items():
            s=''.join(by_page[z['pageId']][z['start']:z['end']] for z in r['fragments'])
            if k in expected:assert s==expected.pop(k),(k,s)
            r['sha256']=sc.pe.hash_text(s)
        assert not expected;sc.pe.validate(v.state)
        session=FileSession(ROOT,source_fonts=False,recovery=False)
        session.remember=lambda *a,**kw:None;session.log.emit=lambda *a,**kw:None
        try:
            for f in v.state['fontSources']:session.fonts.register(session.fonts.document_path(f['path'],f['sha256']),f['sha256'])
            session._restore(v.state,take_ownership=True);session._state=v.state
            with TemporaryDirectory(dir=stage) as sub:
                candidate=Path(sub)/native.name
                session.save(candidate,preview_mode='two');before=session.capture()
                session.open(candidate,advance_revision=False);saved=session.capture()
                assert before==saved
                candidate.replace(stage/native.name)
        finally:session.finish()
        physical=render_duplex(saved,stage/pdf.name,label,use_printed_folios=True,section_tops=tops)
        report.update(pages=len(saved['pages']),physicalPages=physical,pdfSha256=sha(stage/pdf.name),nativeReopened=True,allPDFTextAndBoundsVerified=True)
        (stage/pdf.name).replace(pdf)
    (stage/native.name).replace(native)
    report.update(ledger=stamp,sha256=sha(native),headwords=meta['heads'])
    receipt.write_text(json.dumps(report,indent=1),encoding='utf8')
    return kind,num,report['pages']

def build_all(kinds,workers,nums):
    catalogue=json.loads((WORK/'volumes.json').read_text('utf8'))
    jobs=[(k,n) for n in (nums or range(1,len(catalogue)+1)) for k in kinds]
    with ProcessPoolExecutor(max_workers=workers,max_tasks_per_child=1) as pool:
        tasks={pool.submit(volume,*job):job for job in jobs}
        errors=[]
        for t in as_completed(tasks):
            try:print(t.result(),flush=True)
            except Exception as e:
                import traceback
                traceback.print_exception(e);errors.append((tasks[t],str(e)))
        if errors:raise ValueError(errors)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['prep','print','progressive','both']);parser.add_argument('--volumes',nargs='*',type=int);parser.add_argument('--workers',default=6,type=int)
    args=parser.parse_args()
    if args.kind=='prep':prep()
    else:build_all(['print','progressive'] if args.kind=='both' else [args.kind],args.workers,args.volumes)
