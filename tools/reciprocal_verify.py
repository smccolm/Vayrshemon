"""Verify lexical coverage, reciprocal discoverability and the issued native/duplex volumes."""
import argparse
from collections import Counter
from hashlib import sha256
from html import escape
from itertools import combinations
from pathlib import Path
import json
import os
import re
import shutil
from tempfile import NamedTemporaryFile
from urllib.parse import quote

from tools.dictionary_corpus import sha
from tools.dictionary_lexicon import load_gzip
from tools.reciprocal_publication import BLOCK,FOLDER,STAGE
from tools.semantic_expansion import DEST,ROOT,WORK
from tools.semantic_neighbours import collate,dictionary,normalize

def verify_words():
    groups,att=dictionary()
    d=load_gzip(WORK/'reciprocal-lexicon.json.gz');nodes=d['nodes']; stats=d['counts']
    authoring=json.loads((WORK/'dictionary-additions.json').read_text('utf8'))['entries']
    ids={normalize(n['form']):n['id'] for n in nodes}
    assert len(ids)==len(nodes) and list(ids)==sorted(ids,key=collate)
    assert {normalize(n['form']) for n in nodes if n.get('old')}==groups.keys()
    assert all(normalize(n['form']) not in att['forms'] for n in nodes if not n.get('old'))
    edges=[dict(n['links']) for n in nodes];examples=Counter(); original=0; new=0; largest=0
    for i,n in enumerate(nodes):
        assert i==n['id'] and len(edges[i])==len(n['links']) and i not in edges[i]
        for j,t in edges[i].items():assert t and edges[j][i]==t
        if n.get('old'):
            records={r['id']:r for r in groups[normalize(n['form'])]}
            assert {r['id'] for r in n['reads']}==records.keys()
            for r in n['reads']:
                a=records[r['id']]['article']
                assert all(r[x]==a[x] for x in ('definition','example','exampleEnglish','references'))
                original+=1
            children=n['children'];assert len(set(children))==len(children)>=2
            assert all(nodes[c]['anchor']==i for c in children)
            for a,b in combinations([i]+children,2):assert b in edges[a] and a in edges[b]
            for field in ('definition','example','meaning','exampleEnglish'):
                readings=[]
                for child in (nodes[c] for c in children):
                    wording=child['reads'][0][field]
                    if field in ('definition','example'):
                        wording=normalize(wording).replace(normalize(child['form']),'@')
                    else:
                        wording=wording.casefold().replace(child['roman'].casefold(),'@')
                    readings.append(' '.join(wording.split()))
                assert len(set(readings))==len(readings),(n['roman'],field)
        else:
            for r in n['reads']:
                a=authoring[r['id']]
                assert a['form']==n['form'] and a['meaning']==r['meaning'] and a['label']==n['label']
                assert all(r.get(k,'').strip() for k in ('definition','meaning','gloss','example','exampleEnglish','exampleGloss'))
                assert normalize(n['form']) in normalize(r['example']), (n['roman'],'example lacks the native headword')
                assert not re.search(r'\{[bt]\}|\b(?:vendortarget|allusiveterm|reviewbase)\b',r['meaning']+r['definition']+r['exampleEnglish'])
                assert not re.search(r'leroy jenkins|streisand',n['label']+' '+r['meaning'],re.I)
                new+=1;examples[n['method']]+=1
            if n.get('method')=='allusive transfer':
                assert n['ordinaryField'] and n['usageCondition'] and n['basis'] and n['sourceUse']
            if 'sourceSense' in n:assert n['sourceSense'] in {r['id'] for r in nodes[n['anchor']]['reads']}
        largest=max(largest,len(n['links']))
    assert new==len(authoring)==stats['addedHeads'] and original==stats['startingSenses']
    assert sum(map(len,edges))==stats['directedLinks']==2*stats['edges']
    seen={0};todo=[0]
    while todo:
        for j in edges[todo.pop()]:
            if j not in seen:seen.add(j);todo.append(j)
    assert len(seen)==len(nodes)
    examples_index={n['roman']:n['id'] for n in nodes if n['roman'] in {'jōrek','klēmun','shalōrin','shalōvek','drākem','drārun'}}
    for x,y in [('jōrek','klēmun'),('shalōrin','shalōvek'),('drākem','drārun')]:assert examples_index[y] in edges[examples_index[x]]
    hook=next(n for n in nodes if n['label']=='A fish on the hook')
    assert all(examples_index[k] in edges[hook['id']] for k in ['jōrek','klēmun'])
    from tools.dictionary_lexicon import language_set
    registry,_=language_set()
    assert all(registry.lexicon[k]['form']==a['form'] and registry.lexicon[k]['meaning']==a['meaning'] for k,a in authoring.items())
    proper=[n for n in nodes if n.get('old') and n['pos']=='proper']
    assert all(len(n['children'])>=2 and all('allusi' in nodes[i]['method'] for i in n['children']) for n in proper)
    classes=Counter(nodes[i]['pos'] for n in proper for i in n['children'])
    return dict(**stats,archivedNativeSenseExamplesMatched=original,newSensesWithExamples=new,lookupFromAnyHeadReachesAll=len(seen),
        actualNewFormsInNativeExamples=new,distinctSiblingDefinitionsAndExamplesAfterMaskingHeadword=len(groups),
        properNameAnchors=len(proper),nameDerivedReadings=sum(classes.values()),nameDerivedClasses=dict(classes),
        largestNumberOfNeighbours=largest,exampleIds=examples_index,hookId=hook['id'],methodCounts=dict(examples),
        newEntriesResolvedInLanguageRegistry=len(authoring),lexicalLedgerSha256=sha(WORK/'reciprocal-lexicon.json.gz'),wordNetArchiveSha256=sha(STAGE/'WNdb-3.0.tar.gz'))

def stamp(obj):return sha256(json.dumps(obj,ensure_ascii=False).encode('utf8')).hexdigest()

def print_locations(native,start,count):
    from tools import shakespeare_collected as sc
    state=sc.unpack(sc.read(native))['state']
    physical={p['pageId']:i+2 for i,p in enumerate(state['pages'])}
    found={int(z['id'][1:-2]):physical[z['fragments'][0]['pageId']] for z in state['printEdition']['verses'] if re.fullmatch(r'w\d+\.0',z['id'])}
    assert sorted(found)==list(range(start,start+count))
    assert min(found.values())>=4 and max(found.values())<=len(state['pages'])+1
    return [found[i] for i in sorted(found)]

def print_index():
    cat=json.loads((WORK/'volumes.json').read_text('utf8'));index=[];total=0
    for m in cat:
        v=load_gzip(STAGE/'volumes'/f"{m['number']:02d}.json.gz");r=json.loads((WORK/'Publication'/f"print-{m['number']:02d}.json").read_text('utf8'))
        native=FOLDER['print']/(m['name']+'.vay')
        assert sha(native)==r['sha256'] and r['ledger']==stamp(v['print']) and r['allPDFTextAndBoundsVerified']
        assert sha(FOLDER['print']/(m['name']+' - Duplex Print.pdf'))==r['pdfSha256']
        index.extend(print_locations(native,len(index),m['heads']));total+=r['physicalPages']
    (DEST/'Index data/locations.js').write_text('window.printLocations='+json.dumps(index,separators=(',',':'))+';',encoding='utf8')
    print(len(index),'page destinations;',total,'PDF pages')

def spread_locations(native,ledger,start,num,signature):
    from tools.compose_historical_book import texts
    from tools.dictionary_corpus import page_stream
    path=WORK/'Publication'/f'folios-{num:02d}.json'
    if path.exists():
        current=json.loads(path.read_text('utf8'))
        if current['ledger']==signature:return current['pages']
    pos=0;found={}
    for page_no,page in enumerate(page_stream(native),1):
        if not page_no%2:continue
        first=min(page['frames'],key=lambda f:int(f['x']));native_rows=texts(first)
        rows=ledger['rows'][pos:pos+len(native_rows)]
        assert [r['text'] for r in rows]==native_rows
        for r in rows:
            if re.fullmatch(r'w\d+\.0',r['id']):found[int(r['id'][1:-2])]=page_no
        pos+=len(rows)
    assert pos==len(ledger['rows']) and sorted(found)==list(range(start,start+ledger['meta']['heads']))
    out=[found[j] for j in sorted(found)]
    path.write_text(json.dumps(dict(ledger=signature,pages=out),separators=(',',':')),encoding='utf8')
    return out

def available_volumes():
    cat=json.loads((WORK/'volumes.json').read_text('utf8'))
    ready=[];rows=[];spread_index={}
    for m in cat:
        number=m['number'];entry=WORK/'Publication'/f'progressive-{number:02d}.json'
        if entry.is_file():
            receipt=json.loads(entry.read_text('utf8'))
            v=load_gzip(STAGE/'volumes'/f'{number:02d}.json.gz')
            if receipt['ledger']==stamp(v['rows']):
                ready.append(number)
                start=(number-1)*BLOCK
                native=FOLDER['progressive']/(m['name']+'.vay')
                pages=spread_locations(native,v,start,number,receipt['ledger'])
                spread_index.update(enumerate(pages,start))
        p=FOLDER['print']/(m['name']+'.vay')
        pdf=p.with_name(m['name']+' - Duplex Print.pdf')
        prog=FOLDER['progressive']/p.name
        def link(path,label):return '<a href="'+quote(path.relative_to(DEST).as_posix())+'">'+label+'</a>'
        rows.append('<tr><th>'+str(number)+'</th><td>'+escape(m['first'])+' – '+escape(m['last'])+'</td><td>'+(link(prog,'Four columns') if number in ready else 'Typesetting')+'</td><td>'+link(p,'Print .vay')+'</td><td>'+link(pdf,'Duplex PDF')+'</td></tr>')
    (DEST/'Index data/volume-status.js').write_text('window.progressiveVolumes='+json.dumps(ready)+';window.progressiveLocations='+json.dumps(spread_index,separators=(',',':'))+';',encoding='utf8')
    guide=json.loads((WORK/'guide.json').read_text('utf8'))['file']
    native=json.loads((WORK/'complete-print-native.json').read_text('utf8'))['file']
    pdf=json.loads((WORK/'complete-pdf.json').read_text('utf8'))['file']
    navigation=' · '.join([link(FOLDER['progressive']/guide,'Four-column guide'),link(FOLDER['print']/native,'Complete print manuscript'),link(FOLDER['print']/pdf,'Complete duplex PDF')])
    (DEST/'Volumes.html').write_text('<!doctype html><meta charset="utf-8"><title>Alphabetical volumes</title><style>body{max-width:58em;margin:3em auto;padding:0 1em;font:17px/1.5 Georgia}th,td{padding:.4em;text-align:left;border-bottom:1px solid #ccc}a{color:#165653}</style><h1>Vayrshemon dictionary and thesaurus</h1><a href="Open the dictionary and thesaurus.html">Search all headwords</a><p>'+navigation+'</p><table><tr><th>Volume</th><th>Headword range</th><th>Progressive</th><th>Print</th><th>PDF</th></tr>'+''.join(rows)+'</table>',encoding='utf8')
    print('Reopened four-column volumes:',ready,flush=True)

def publication():
    report=verify_words()
    cat=json.loads((WORK/'volumes.json').read_text('utf8'))
    receipt_dir=WORK/'Publication'; pages=[];spreads=[];physical=[];sheets=0; index=[];progressive_index=[];rows_html=[]
    libs=[(ROOT/'Saves'/('Vayrshemon '+typ+' - '+name),kind)
         for typ in ('Dictionary','Thesaurus') for kind,name in [('progressive','Four-Column Progressive Edition'),('print','Letter Print Edition')]]
    files={}; checks=[]
    for m in cat:
        n=m['number'];stub=m['name'];v=load_gzip(STAGE/'volumes'/f'{n:02d}.json.gz')
        assert m==v['meta'];names={}
        for kind in ('print','progressive'):
            native=FOLDER[kind]/(stub+'.vay');names[kind]=native
            r=json.loads((receipt_dir/f'{kind}-{n:02d}.json').read_text('utf8'))
            assert r['nativeReopened'] and r['sha256']==sha(native) and r['headwords']==m['heads']
            assert r['ledger']==stamp(v['print' if kind=='print' else 'rows']),(kind,n,'outdated ledger')
            files.setdefault(kind,[]).append(native)
            if kind=='print':
                pdf=FOLDER['print']/(stub+' - Duplex Print.pdf');names['pdf']=pdf
                assert r['allPDFTextAndBoundsVerified'] and r['pdfSha256']==sha(pdf) and r['physicalPages']==r['pages']+1
                index.extend(print_locations(native,len(index),m['heads']))
                physical.append(r['physicalPages']);pages.append(r['pages']);sheets+=(r['physicalPages']+1)//2
                files[kind].append(pdf)
            else:
                assert r['allFourSavedColumnsVerified'] and r['rows']==len(v['rows']) and r['maxBaselineErrorPt']<.035
                spreads.append(r['spreads'])
                locations=spread_locations(native,v,len(progressive_index),n,r['ledger'])
                assert len(locations)==m['heads'] and all(0<k<r['pages'] and k%2 for k in locations)
                progressive_index.extend(locations)
            checks.append(dict(volume=n,format=kind,sha256=r['sha256'],pages=r['pages'],ledger=r['ledger']))
        def a(path,t):return '<a href="'+quote(path.relative_to(DEST).as_posix())+'">'+t+'</a>'
        rows_html.append('<tr><th>'+f'{n:02d}'+'</th><td>'+escape(m['first'])+' – '+escape(m['last'])+'</td><td>'+a(names['progressive'],'Four columns')+'</td><td>'+a(names['print'],'Print .vay')+'</td><td>'+a(names['pdf'],'Duplex PDF')+'</td><td>'+str(physical[-1])+'</td></tr>')
    assert len(index)==report['heads']==sum(m['heads'] for m in cat)
    (DEST/'Index data/locations.js').write_text('window.printLocations='+json.dumps(index,separators=(',',':'))+';',encoding='utf8')
    catalogue='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Vayrshemon dictionary and thesaurus volumes</title><style>body{max-width:64em;margin:3em auto;padding:0 1em;color:#242525;background:#fbfaf6;font:17px/1.5 Georgia,serif}table{width:100%;border-collapse:collapse}th,td{text-align:left;border-bottom:1px solid #c8c5be;padding:.45em}a{color:#165653}h1{line-height:1.15}thead th{vertical-align:bottom}</style><h1>Vayrshemon dictionary and thesaurus</h1><p><a href="Open the dictionary and thesaurus.html">Search the entries and follow related words</a></p><p>The volumes follow Thimfora alphabetical order. Each volume has a four-column manuscript, a native print manuscript, and a Letter duplex PDF. PDF page counts include the leading binding blank.</p><table><thead><tr><th>Volume</th><th>First and last headwords</th><th>Progressive</th><th>Native print</th><th>PDF</th><th>PDF pages</th></tr></thead><tbody>'''+''.join(rows_html)+'</tbody></table></html>'
    omnibus=json.loads((WORK/'complete-pdf.json').read_text('utf8'))
    bound=FOLDER['print']/omnibus['file']
    assert sha(bound)==omnibus['sha256'] and omnibus['allPageContentsAndBoxesVerified'] and omnibus['volumeBookmarksVerified']
    assert omnibus['physicalPDFPages']==sum(physical)+len(omnibus['interVolumeBlanks'])
    complete=json.loads((WORK/'complete-print-native.json').read_text('utf8'))
    manuscript=FOLDER['print']/complete['file']
    assert sha(manuscript)==complete['sha256'] and complete['nativeReopened'] and complete['everyNativePageTextAndPrintGeometryVerified']
    assert complete['pages']+1==omnibus['physicalPDFPages']
    guide=json.loads((WORK/'guide.json').read_text('utf8'));guide_file=FOLDER['progressive']/guide['file']
    assert guide['nativeReopened'] and guide['ranges']==len(cat) and sha(guide_file)==guide['sha256']
    om_link='<p><a href="'+quote(guide_file.relative_to(DEST).as_posix())+'">Native four-column guide and alphabetical index</a> · <a href="'+quote(manuscript.relative_to(DEST).as_posix())+'">Complete print manuscript</a> · <a href="'+quote(bound.relative_to(DEST).as_posix())+'">Complete duplex PDF</a> · '+f"{omnibus['physicalPDFPages']:,} PDF pages"+'</p><p>Native volume numbers use Unta base twelve. English volume numbers and filenames use decimal. Historical references beside a coinage identify its source headword.</p>'
    (DEST/'Volumes.html').write_text(catalogue.replace('<table>',om_link+'<table>'),encoding='utf8')
    files['print'].extend([bound,manuscript])
    files['progressive'].append(guide_file)
    (DEST/'Index data/volume-status.js').write_text('window.progressiveVolumes='+json.dumps([v['number'] for v in cat])+';window.progressiveLocations='+json.dumps(progressive_index,separators=(',',':'))+';',encoding='utf8')
    previous=WORK/'library-links.json'
    known=json.loads(previous.read_text('utf8')) if previous.exists() else {}
    linked={};filehashes={f:sha(f) for sourcefiles in files.values() for f in sourcefiles}
    def library_link(f,local):
        if local.exists():
            if os.path.samefile(local,f) or sha(local)==filehashes[f]:
                linked[str(local)]=f
                return
            if known.get(str(local))!=sha(local):raise ValueError('Independent local copy: '+str(local))
        else:
            try:
                os.link(f,local)
            except PermissionError:
                pass
            else:
                linked[str(local)]=f
                return
        with NamedTemporaryFile(dir=local.parent,delete=False) as draft:
            staged=Path(draft.name)
        try:
            shutil.copyfile(f,staged)
            assert sha(staged)==filehashes[f]
            staged.replace(local)
        finally:
            staged.unlink(missing_ok=True)
        linked[str(local)]=f
    for book,kind in libs:
        assert book.is_dir()
        branch=book/'Reciprocal vocabulary';branch.mkdir(exist_ok=True)
        for f in files[kind]:
            local=branch/f.name
            library_link(f,local)
        if kind=='print':
            title=book.name.removesuffix(' - Letter Print Edition')
            library_link(manuscript,book/(title+' - Expanded Print Edition.vay'))
            library_link(bound,book/(title+' - Expanded Duplex Print.pdf'))
        else:
            title=book.name.removesuffix(' - Four-Column Progressive Edition')
            library_link(guide_file,book/(title+' - Expanded Four-Column Edition Index.vay'))
        dest='../'+quote(DEST.name)+'/'
        (book/'Expanded vocabulary.html').write_text('<!doctype html><meta charset="utf-8"><title>Expanded Vayrshemon vocabulary</title><h1>Expanded Vayrshemon vocabulary</h1><p><a href="'+dest+'Open%20the%20dictionary%20and%20thesaurus.html">Search the complete dictionary and follow the thesaurus links</a></p><p><a href="'+dest+'Volumes.html">Alphabetical volumes and print PDFs</a></p>',encoding='utf8')
    linkids={local:filehashes[f] for local,f in linked.items()}
    (WORK/'library-links.json').write_text(json.dumps(linkids,indent=1),encoding='utf8')
    report.update(volumes=len(cat),progressivePages=2*sum(spreads),printNativePages=sum(pages),physicalPDFPages=sum(physical),duplexSheetsAcrossSeparateVolumes=sheets,
      completePrintPdfPages=omnibus['physicalPDFPages'],completePrintPdfSha256=omnibus['sha256'],
      completePrintNativePages=complete['pages'],completePrintNativeSha256=complete['sha256'],
      progressiveGuidePages=guide['pages'],
      printPageLinks=len(index),progressiveHeadwordSpreads=len(progressive_index),nativePublicationsValidated=len(checks),volumeHashes=checks)
    (WORK/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf8')
    print({k:v for k,v in report.items() if k not in ('volumeHashes','partsOfSpeech','methodCounts')})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--words',action='store_true');parser.add_argument('--print-index',action='store_true')
    args=parser.parse_args()
    if args.words:
        report=verify_words();(WORK/'lexical-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf8');print(report)
    elif args.print_index:print_index()
    else:publication()
