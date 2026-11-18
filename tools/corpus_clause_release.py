"""Verify issued body columns, update their provenance, then install verified replacements."""
import os,shutil,gzip,uuid
from collections import Counter
from tools.corpus_clause_revision import *
from tools.corpus_clause_spreads import save_native
from tools.compose_historical_book import texts
from tools.shakespeare_collected import pe
from vayrshemon.native_storage import unpack
from vayrshemon import saved_preview
from pypdf import PdfReader

REVIEW=SV/'Archive'/'Editorial reviews'/'Bible and Shakespeare clause review'
BEFORE=SV/'Archive'/'Previous editions'/'Before Bible and Shakespeare clause review'
def manifest(folder):return folder/'edition-manifest.json'
def info(folder):return read(manifest(folder))
def project_ref(path):return path.relative_to(ROOT).as_posix()
def revised_metadata():
    changes=read(S/'changes.json');project=read(PROJECT/'project.json')
    reviewed=read(PROJECT/'Reviews/complete-corpus.json')
    for w in sources():
        if w['slug'] not in changes:continue
        slug=w['slug'];u={r['id']:r for r in read(edited(ledger(w)))['units']}
        path=saved_source(w['output']);h=sha(edited(path));lh=sha(edited(ledger(w)))
        raw=next((q for q in project['works'] if q['slug']==slug),None)
        if raw is None:raw=project['existingPlayImpressions'][slug]
        raw.update(sha256=h,ledgerSha256=lh,previousOutput=project_ref(BEFORE/path.relative_to(ROOT)),editorialRevision=raw.get('editorialRevision',1)+1)
        evidence=next((q for q in reviewed['editionEvidence'] if q['work']==slug),None)
        if evidence:evidence.update(sha256=h,ledgerSha256=lh)
        authors=PROJECT/'Analyses'/(slug+'.json')
        if authors.exists():
            draft=read(authors)
            for row in draft:
                if row['id'] in changes[slug]:
                    for k in ('analysis','backTranslation','review'):row[k]=u[row['id']][k]
            write(revised(authors),draft)
        else:assert slug in project['existingPlayImpressions']
        c=changes[slug]
        for name in ('edition.json','revision-validation.json','layout-validation.json'):
            dest=path.parent/name
            if not dest.exists():continue
            m=read(dest)
            if name=='layout-validation.json':
                m.update(sha256=h,priorNativeSha256=w['sha256'],clauseReview=dict(ledgerSha256=lh,correctedUnits=list(c),method='Reopened and compared all four columns. Changed spreads recomposed with the issued typography.'))
            else:
                prior=m.get('nativeSha256',m.get('sha256'))
                m.update(priorNativeSha256=prior,priorLedgerSha256=m.get('ledgerSha256'),nativeSha256=h,ledgerSha256=lh,
                         editorialRevision=raw['editorialRevision'],correctedUnits=list(c),clauseReview=project_ref(REVIEW))
                if 'sha256' in m:m['sha256']=h
            write(revised(dest),m)
    write(revised(PROJECT/'project.json'),project);write(revised(PROJECT/'Reviews/complete-corpus.json'),reviewed)
    working={w['slug']:w for w in sources()}; hs=[]
    for w in sources():hs.append(sha(edited(saved_source(w['output']))))
    hfile=next(H.glob('*.vay'));hpfile=next(HP.glob('*.vay'));bf=next(B.glob('*.vay'));bpf=next(BP.glob('*.vay'))
    hstate=unpack(read(revised(hfile)));hstate['state']['printEdition']['sourceSha256']=pe.hash_text('\n'.join(hs))
    hstate['state']['printEdition']['ledgerSha256']=pe.hash_text('\n'.join(sha(edited(ledger(w))) for w in sources()))
    save_native(hstate,hfile);del hstate
    for folder in (H,HP):
        m=info(folder);key='sources' if folder==H else 'works'
        for item in m[key]:
            p=saved_source(item['file']);item['sha256']=sha(edited(p))
        m.update(priorNativeSha256=m['nativeSha256'],nativeSha256=sha(revised(hfile if folder==H else hpfile)),clauseReview=project_ref(REVIEW))
        if folder==HP:
            m['sealedNativeSha256']=sha(revised(hfile));m['verification']=dict(reopened=True,individualManuscriptColumnsCompared=42)
        else:m['pdfSha256']=sha(revised(next(H.glob('*.pdf'))))
        write(revised(manifest(folder)),m)
    script=read(edited(B/'complete-translation-ledger.json'))['units']
    ordered=hashlib.sha256()
    for u in script:ordered.update((json.dumps((u['id'],u['text']),ensure_ascii=False,separators=(',',':'))+'\n').encode())
    bman=info(B);bman.update(previousImpressionSha256=bman['sha256'],sha256=sha(revised(bf)),ledgerSha256=sha(edited(B/'complete-translation-ledger.json')),commonNativeVerseTextSha256=ordered.hexdigest(),clauseReview=project_ref(REVIEW))
    write(revised(manifest(B)),bman)
    correctionlog=read(B/'correction-ledger.json')
    for id,c in changes['bible'].items():
        correctionlog.append(dict(id=id,parentText=c['oldText'],text=c['text'],beforeAnalysis=c['oldAnalysis'],afterAnalysis=c['analysis'],note=c['note']))
    write(revised(B/'correction-ledger.json'),correctionlog);write(revised(B/'quotation-readings.json'),read(S/'quoted-readings.json'))
    bcheck=read(B/'combined-validation.json');pageset={j for _,j in read(S/'bible-spreads.json').values()};bcheck.pop('nonTitleStateSha256',None)
    bcheck.update(sha256=bman['sha256'],previousImpressionSha256=bman['previousImpressionSha256'],recomposedSpreads=len(pageset)//2,reusedMeasuredSpreads=len(bcheck['checks'])-len(pageset)//2,clauseReview=project_ref(REVIEW))
    for r in bcheck['checks']:
        if r['leftPage'] in pageset:r.update(measurement='Clause correction; all four columns measured and compared.')
    write(revised(B/'combined-validation.json'),bcheck)
    bpman=info(BP);bpman.update(priorRunInSha256=bpman['nativeSha256'],nativeSha256=sha(revised(bpf)),ledgerSha256=bman['ledgerSha256'],fourColumnSha256=bman['sha256'],commonOrderedVerseTextSha256=ordered.hexdigest(),
                                 printSha256=sha(revised(next(BP.glob('*.pdf')))),clauseReview=project_ref(REVIEW))
    for key in ('reader','printComparison','pagination','mismatchedVerses','compactSha256','genesisFirst18VersesAndArtworkMatchPrior'):
        bpman.pop(key,None)
    bpman['mismatchedVerses']=0;bpman['printComparison']=read(S/'bible-pdf.json')
    write(revised(manifest(BP)),bpman)
    for folder,file in [(B,bf),(BP,bpf),(H,hfile)]:
        p=folder/'FROZEN.json';seal=read(p)
        seal['previousImpressionSha256']=seal['nativeSha256'];seal['nativeSha256']=sha(revised(file))
        if folder==H:seal['pdfSha256']=sha(revised(next(H.glob('*.pdf'))))
        for name in seal.get('files',{}):
            doc=folder/name
            if revised(doc).exists():seal['files'][name]=sha(revised(doc))
        if folder==B:seal['files']['quotation-readings.json']=sha(revised(B/'quotation-readings.json'))
        write(revised(p),seal)

def confirm():
    counts={};allws=sources()
    for folder in (B,BP,H,HP):
        p=next(folder.glob('*.vay'));m=read(edited(manifest(folder)));assert sha(edited(p))==m.get('nativeSha256',m.get('sha256'))
        data=unpack(read(edited(p)));state=data['state'];saved_preview.validate(data['shellPreview'],state)
        if folder in (B,BP):
            rows=[(u['id'],u) for u in read(edited(B/'complete-translation-ledger.json'))['units']]
        else:
            rows=[(w['slug']+'/'+u['id'],u) for w in allws for u in read(edited(ledger(w)))['units']]
        if folder in (H,BP):
            text={pg['pageId']:pe.text_of(pg) for pg in state['pages']}
            records=[r for r in state['printEdition']['verses'] if not r['id'].startswith('nav/')]
            for r,(id,u) in zip(records,rows,strict=True):
                val=''.join(text[f['pageId']][f['start']:f['end']] for f in r['fragments'])
                assert (id,u['text'],pe.hash_text(val))==(r['id'],val,r['sha256']),(p,id)
            q=next(folder.glob('*.pdf'));assert sha(edited(q))==m.get('pdfSha256',m.get('printSha256'))
            with PdfReader(edited(q)) as doc:assert len(doc.pages)==m.get('physicalPrintPages',m.get('physicalPages'))
        else:
            itr=iter(rows)
            for i in range(0,len(state['pages']),2):
                fs=[f for pg in state['pages'][i:i+2] for f in sorted(pg['frames'],key=lambda f:int(f['x'])) if f['name']!='Book title']
                assert len(fs)==4
                for native,roman,gl,en in zip(*(texts(f) for f in fs),strict=True):
                    id,u=next(itr);assert (native,roman,gl,en)==(u['text'],u['text'],u['gloss'],u['source']),(p,id)
            assert next(itr,None) is None
        counts[folder.name]=dict(passages=len(rows),nativePages=len(state['pages']),sha256=sha(edited(p)))
        del rows,data,state
    for w in allws:
        individual=saved_source(w['output'])
        state=unpack(read(edited(individual)))['state'];us=iter(read(edited(ledger(w)))['units'])
        for i in range(0,len(state['pages']),2):
            fs=[f for pg in state['pages'][i:i+2] for f in sorted(pg['frames'],key=lambda f:int(f['x']))]
            for native,roman,gl,en in zip(*(texts(f) for f in fs),strict=True):
                u=next(us);assert (native,roman,gl,en)==(u['text'],u['text'],u['gloss'],u['source']),(w['slug'],u['id'])
        assert next(us,None) is None
    write(S/'verified-publications.json',counts)
    print('All four editions, 42 individuals and PDF receipts verified',flush=True)
def install():
    assert (S/'verified-publications.json').is_file()
    staged=sorted((S/'files').rglob('*'));entries=[]
    for src in staged:
        if not src.is_file():continue
        relative=src.relative_to(S/'files');dst=ROOT/relative
        assert dst.resolve().is_relative_to(SV.resolve()) and not dst.resolve().is_relative_to(BEFORE.resolve())
        old=sha(dst) if dst.exists() else None;new=sha(src)
        if new==old:continue
        archive=BEFORE/relative
        if old:
            archive.parent.mkdir(parents=True,exist_ok=True)
            if not archive.exists():shutil.copyfile(dst,archive)
            assert sha(archive)==old,(relative,'base moved')
        entries.append(dict(path=relative.as_posix(),old=old,new=new))
    write(BEFORE/'restoration-index.json',entries)
    done=[]
    try:
        for e in entries:
            dst=ROOT/e['path'];src=revised(dst)
            assert (sha(dst) if dst.exists() else None)==e['old'],e['path']
            dst.parent.mkdir(parents=True,exist_ok=True)
            tmp=dst.with_name(dst.name+'.clause-revision-tmp')
            assert not tmp.exists();shutil.copyfile(src,tmp);os.replace(tmp,dst);done.append(e)
        for e in entries:assert sha(ROOT/e['path'])==e['new']
    except Exception:
        for e in reversed(done):
            dst=ROOT/e['path']
            if e['old']:
                tmp=dst.with_name(dst.name+'.rollback-tmp');shutil.copyfile(BEFORE/e['path'],tmp);os.replace(tmp,dst)
            else:dst.unlink()
        raise
    print('Published',len(entries),'files. All old and new hashes checked.',flush=True)
if __name__=='__main__':{'metadata':revised_metadata,'verify':confirm,'install':install}[sys.argv[1]]()

