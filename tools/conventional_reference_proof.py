"""Verify both independent publications and write an offline, page-accurate catalogue."""
import argparse
from collections import defaultdict
from html import escape
import json
import re
import shutil

from tools import shakespeare_collected as sc
from tools.compose_historical_book import texts
from tools.conventional_reference import SOURCE,edition,write_json
from tools.dictionary_corpus import page_stream,sha
from tools.dictionary_lexicon import load_gzip
from tools.dictionary_rows import collate
from tools.reciprocal_verify import stamp


def read(path):
    return json.loads(path.read_text('utf8'))


def body_proofs(state):
    proofs={}
    for i,p in enumerate(state['pages'],1):
        spec=state['printEdition']['pages'][p['pageId']]
        if spec['kind'] in ('opening','body'):
            text=sc.pe.text_of(p)
            lines=[text[l['start']:l['end']] for l in spec['lines'] if l['baseline']>77]
            assert lines
            proofs[i]=sc.pe.hash_text(json.dumps(lines,ensure_ascii=False))
    return proofs


def printed_pages(path, *, complete_bodies=None,first_entry=None):
    state=sc.unpack(sc.read(path))['state']
    numbers={p['pageId']:i+2 for i,p in enumerate(state['pages'])}
    if complete_bodies is not None:
        for local,proof in body_proofs(state).items():
            assert complete_bodies.pop(first_entry+local-3)==proof
    return {r['id']:numbers[r['fragments'][0]['pageId']] for r in state['printEdition']['verses']}


def spread_pages(native,rows):
    found={};offset=0
    for page_no,page in enumerate(page_stream(native),1):
        if page_no%2==0:continue
        written=texts(min(page['frames'],key=lambda f:int(f['x'])))
        expected=rows[offset:offset+len(written)]
        assert [r['text'] for r in expected]==written
        for r in expected:found[r['id']]=page_no
        offset+=len(written)
    assert offset==len(rows)
    return found


def js_data(obj):
    return json.dumps(obj,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')


def catalogue(book,volumes,words,groups,summary):
    root=book.work.parent;assets=root/'Index data';assets.mkdir(exist_ok=True)
    (assets/'locations.js').write_text('window.referenceWords='+js_data(words)+';window.referenceGroups='+js_data(groups)+';',encoding='utf8')
    shutil.copyfile(SOURCE.parent/'Index data/Thimfora.ttf',assets/'Thimfora.ttf')
    kind=book.title.split()[-1]
    rows=[]
    for m in volumes:
        name=m['name']
        rows.append('<tr><th>'+name+'</th><td>'+escape(m['first'])+' – '+escape(m['last'])+'</td><td><a href="Four-Column Progressive Edition/'+name+'.vay">Four-column .vay</a></td><td><a href="Letter Print Edition/'+name+'.vay">Print .vay</a></td><td><a href="Letter Print Edition/'+name+' - Duplex Print.pdf">PDF</a></td></tr>')
    other='Thesaurus' if kind=='Dictionary' else 'Dictionary'
    page=PAGE.replace('BOOKTITLE',escape(book.title)).replace('OTHERBOOK',other).replace('ISDICTIONARY',str(kind=='Dictionary').lower()).replace('SUMMARY',escape(summary)).replace('VOLUMEROWS',''.join(rows))
    (root/('Open the '+kind+'.html')).write_text(page,encoding='utf8')


PAGE='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BOOKTITLE</title>
<style>@font-face{font-family:Thimfora;src:url("Index data/Thimfora.ttf")}*{box-sizing:border-box}body{max-width:66rem;margin:2.4rem auto;padding:0 1.5rem;color:#242421;background:#faf9f5;font:17px/1.5 Georgia,serif}h1,h2,h3{font-weight:normal;line-height:1.2}h1{font-size:2.5rem;margin-bottom:0}p,nav{margin:.65rem 0}a{color:#115955}nav a{display:inline-block;margin:0 1em .25em 0}header{margin-bottom:2rem}input{margin:.3em 0;width:min(100%,36rem);font:inherit;padding:.4em}label,small{display:block}article{border-left:3px solid #b8b09b;padding:0 1rem}.native{font:2.6rem Thimfora;overflow-wrap:anywhere}.note,small{color:#4c504b;font-size:.92rem}table{margin-top:1rem;width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #d1cdbf;text-align:left;padding:.45rem}.links a{display:inline-block;margin-right:1rem}button{padding:.3rem .6rem}h2{margin-top:1.7rem}ul{padding-left:1.5rem}li{margin-bottom:.25rem}@media(max-width:700px){body{margin:1.3rem auto;padding:0 .8rem}td,th{padding:.2rem;font-size:.9rem}h1{font-size:2rem}}</style>
<header><h1>BOOKTITLE</h1><p>SUMMARY</p><nav><a href="Four-Column Progressive Edition/Volume 00 - Reader%27s Guide.vay">Four-column reader’s guide</a><a href="Letter Print Edition/BOOKTITLE.vay">Complete print manuscript</a><a href="Letter Print Edition/BOOKTITLE - Duplex Print.pdf">Complete duplex PDF</a><a href="#volumes">Alphabetical volumes</a></nav></header>
<label for="query">Find a headword or English meaning</label><input id="query" type="search" autocomplete="off"><div id="hits"></div><article id="entry"></article>
<h2 id="volumes">Alphabetical volumes</h2><table><thead><tr><th>Volume</th><th>Thimfora range</th><th>Progressive</th><th>Native print</th><th>Duplex print</th></tr></thead><tbody>VOLUMEROWS</tbody></table>
<footer><h2>Companion works</h2><nav><a href="../Vayrshemon OTHERBOOK/Open the OTHERBOOK.html">Vayrshemon OTHERBOOK</a><a href="../Vayrshemon Dictionary and Thesaurus - Reciprocal Vocabulary/Open the dictionary and thesaurus.html">Combined Dictionary–Thesaurus</a></nav></footer>
<script src="Index data/locations.js"></script><script>
const q=document.querySelector('#query'),hits=document.querySelector('#hits'),entry=document.querySelector('#entry');
const words=window.referenceWords,g=window.referenceGroups,byId=new Map(words.map(w=>[w[0],w]));
function escapeHtml(t){return String(t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function fold(t){return t.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase()}
const keys=words.map(w=>fold(w.slice(1,4).join(' ')+' '+w[6])),loads=new Map();window.referenceArticles={};
function find(){let s=fold(q.value.trim());if(!s){hits.innerHTML='';return}let all=[],parts=s.split(/\\s+/);for(let i=0;i<words.length;i++){if(parts.every(x=>keys[i].includes(x))){let w=words[i];all.push([fold(w[2])===s||fold(w[1])===s?0:fold(w[2]).startsWith(s)?1:2,i])}}
 all.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);hits.innerHTML='<small>'+all.length.toLocaleString()+' matches</small><ul>'+all.slice(0,limit).map(([,i])=>'<li>'+link(words[i])+' · '+escapeHtml(words[i][3])+'</li>').join('')+'</ul>'+(all.length>limit?'<button id="more">Show more</button>':'');if(document.querySelector('#more'))document.querySelector('#more').onclick=()=>{limit+=20;find()}}
function link(w){return '<a href="#word-'+w[0]+'">'+escapeHtml(w[2])+'</a>'}
function pages(loc){let [v,p,b]=loc,vol='Volume '+String(v).padStart(2,'0');return '<nav><a href="Four-Column Progressive Edition/'+vol+'.vay">'+vol+', native pp. '+p+'–'+(p+1)+'</a><a href="Letter Print Edition/BOOKTITLE - Duplex Print.pdf#page='+b+'">Print folio '+(b-1)+' · PDF p. '+b+'</a></nav>'}
function loadVolume(v){if(!loads.has(v)){let task=new Promise((ok,fail)=>{let s=document.createElement('script');s.onload=ok;s.onerror=()=>fail(new Error('volume '+v));s.src='Index data/articles-'+String(v).padStart(2,'0')+'.js';document.head.append(s)});loads.set(v,task)}return loads.get(v)}
function articleText(s){return '<div style="font:1.8rem/1.25 Thimfora">'+escapeHtml(s[0])+'</div><blockquote style="font:1.6rem/1.25 Thimfora;margin:.3rem 1.3rem">'+escapeHtml(s[1])+'</blockquote><details><summary>English reading</summary><p>'+escapeHtml(s[2])+'</p><blockquote>'+escapeHtml(s[3])+'</blockquote></details>'}
function fill(v,id,selector){loadVolume(v).then(()=>{let elem=document.getElementById(selector);if(!elem)return;let data=window.referenceArticles[v][id];
 elem.innerHTML=ISDICTIONARY?data.map((s,i)=>(data.length>1?'<h3>Sense '+(i+1)+'</h3>':'')+articleText(s)).join(''):data.map(s=>'<h4>'+link(byId.get(s[0]))+'</h4>'+articleText(s.slice(1))).join('')}).catch(()=>{let e=document.getElementById(selector);if(e)e.textContent='Use the volume or PDF link above to read this entry.'})}
function show(){let w=byId.get(+((location.hash.match(/^#word-(\\d+)$/)||[])[1]));if(!w){entry.innerHTML='';return}
 entry.innerHTML='<div class="native">'+escapeHtml(w[1])+'</div><h2>'+escapeHtml(w[2])+'</h2><p>'+escapeHtml(w[3])+'</p>'+pages(w[4])+
 (ISDICTIONARY?'<div id="article-'+w[0]+'"></div>':(w[5]||[]).map(id=>{const f=g[id];return '<section><h3>'+escapeHtml(f[0])+'</h3><p class="links">'+f[2].map(id=>link(byId.get(id))).join(' ')+'</p>'+pages(f[1])+'<div id="group-'+id+'"></div></section>'}).join(''));
 if(ISDICTIONARY)fill(w[4][0],w[0],'article-'+w[0]);else for(const id of w[5])fill(g[id][1][0],id,'group-'+id)}
let limit=12;q.oninput=()=>{limit=12;find()};window.onhashchange=show;show();</script></html>'''


def verify(kind):
    book=edition(kind);cat=read(book.work/'volumes.json')
    nodes=load_gzip(SOURCE/'reciprocal-lexicon.json.gz')['nodes']
    combo=read(SOURCE/'verification.json')
    assert sha(SOURCE/'reciprocal-lexicon.json.gz')==combo['lexicalLedgerSha256']
    bound=read(book.work/'complete-pdf.json');master=read(book.work/'complete-print-native.json')
    assert bound['allPageContentsAndBoxesVerified'] and master['everyNativePageTextAndPrintGeometryVerified']
    assert master['nativeReopened'] and sha(book.folders['print']/master['file'])==master['sha256']!=combo['completePrintNativeSha256']
    assert sha(book.folders['print']/bound['file'])==bound['sha256']!=combo['completePrintPdfSha256']
    assert bound['physicalPDFPages']==master['pages']
    assert bound['titlePages']==1 and bound['blankPages']==0 and bound['continuousFoliosVerified']
    complete_bodies=body_proofs(sc.unpack(sc.read(book.folders['print']/master['file']))['state'])
    groups=read(book.work/'sense-groups.json') if kind=='thesaurus' else []
    sense_by_id={r['id']:r for n in nodes for r in n['reads']}
    if groups:
        from tools.semantic_neighbours import BOOK
        originals=read(BOOK/'Working/sense-register.json')
        sense_by_id.update({'authored-'+r['key']+'-'+r['family']:r for r in originals.values()})
    member_senses={(f['number'],m['word']):sense_by_id[m['sense']] for f in groups for m in f['members']}
    membership=defaultdict(list);group_index={};actual_members=defaultdict(set);seen_examples=0;actual_pointers=defaultdict(set)
    expected_groups={f['number']:f for f in groups}
    for f in groups:
        assert len(f['members'])>=2 and len({m['word'] for m in f['members']})==len(f['members'])
        for m in f['members']:membership[m['word']].append(f['number'])
    headmap={};spreads=0;total_senses=0;hashes=[]
    assets=book.work.parent/'Index data';assets.mkdir(exist_ok=True)
    for m,b in zip(cat,bound['volumes'],strict=True):
        n=m['number'];assert n==b['volume']
        ledger=load_gzip(book.stage/'volumes'/f'{n:02d}.json.gz')
        assert m==ledger['meta']
        manuscripts={}
        for fmt,k in [('progressive','rows'),('print','print')]:
            p=book.folders[fmt]/(m['name']+'.vay')
            receipt=read(book.work/'Publication'/f'{fmt}-{n:02d}.json')
            assert receipt['ledger']==stamp(ledger[k]) and receipt['nativeReopened'] and receipt['sha256']==sha(p)
            if fmt=='progressive':
                assert receipt['allFourSavedColumnsVerified'] and receipt['maxBaselineErrorPt']<.035
                spreads+=receipt['spreads']
            else:
                assert receipt['allPDFTextAndBoundsVerified'] and b['sourceSha256']==receipt['pdfSha256']==sha(p.with_name(p.stem+' - Duplex Print.pdf'))
            manuscripts[fmt]=p;hashes.append([fmt,n,receipt['sha256']])
        pp=printed_pages(manuscripts['print'],complete_bodies=complete_bodies,first_entry=b['firstPhysicalPage'])
        lp=spread_pages(manuscripts['progressive'],ledger['rows'])
        def where(rid):
            v=b['firstPhysicalPage']+pp[rid]-b.get('sourceFirstPhysicalPage',1)
            assert b['firstPhysicalPage']<=v<=b['lastPhysicalPage']
            return [n,lp[rid],v]
        for i,rid in zip(m['headIDs'],m['headRows'],strict=True):
            assert i not in headmap
            headmap[i]=where(rid)
        printrows={r['id']:r for r in ledger['print']}
        progressive_rows={r['id']:r for r in ledger['rows']}
        articles={}
        assert len(printrows)==len(ledger['print']) and set(printrows)<=pp.keys()
        if kind=='dictionary':
            for i in m['headIDs']:
                w=nodes[i]
                articles[i]=[]
                for j,s in enumerate(w['reads']):
                    k=f'w{i}.{j}'
                    assert printrows[k]['text'].endswith(s['definition'])
                    assert printrows[k+'x']['text']==s['example']
                    ex=progressive_rows[k] if s.get('construction') else progressive_rows[k+'x']
                    assert ex['text'].endswith(s['example']) and s['exampleEnglish'] in ex['source']
                    assert all(ref in progressive_rows[k]['source'] for ref in s['references'])
                    articles[i].append([s[field] for field in ('definition','example','meaning','exampleEnglish')])
                    total_senses+=1
            assert all(r['kind'] in ('definition','example') for r in printrows.values())
            assert not any('see' in key for key in printrows)
        else:
            for r in ledger['rows']:
                k=r['id']
                if match:=re.fullmatch(r'h(\d+)g(\d+)',k):
                    home,g=map(int,match.groups());f=expected_groups[g];assert home==f['home'] and g not in group_index
                    group_index[g]=[f['title'],where(k),[m['word'] for m in f['members']]]
                    articles[g]=[]
                elif match:=re.fullmatch(r'g(\d+)m(\d+)',k):
                    g,i=map(int,match.groups());actual_members[g].add(i)
                    sense=member_senses[g,i]
                    assert printrows[k+'x']['text']==sense['example'] and printrows[k]['text'].startswith(nodes[i]['form']+':')
                    ex=progressive_rows.get(k+'x',r)
                    assert ex['text'].endswith(sense['example']) and sense['exampleEnglish'] in ex['source']
                    en=r['source'].removeprefix(nodes[i]['roman']+' · ').split(' Example: ',1)[0]
                    articles[g].append([i,printrows[k]['text'].removeprefix(nodes[i]['form']+': '),sense['example'],en,sense['exampleEnglish']])
                    seen_examples+=1
                elif match:=re.fullmatch(r'h(\d+)see\d+',k):
                    i=int(match[1])
                    for vol,g in re.findall(r'\(volume (\d+), group (\d+)\)',r['source']):
                        g=int(g);assert g in membership[i] and expected_groups[g]['home']!=i
                        actual_pointers[i].add((int(vol),g))
        (assets/f'articles-{n:02}.js').write_text(f'window.referenceArticles[{n}]='+js_data(articles)+';',encoding='utf8')
    assert list(headmap)==sorted(headmap)
    assert list(headmap)==sorted(headmap,key=lambda j:collate(nodes[j]['form']))
    assert not complete_bodies
    if kind=='dictionary':
        assert list(headmap)==list(range(len(nodes))) and total_senses==sum(len(n['reads']) for n in nodes)
    else:
        assert headmap.keys()==membership.keys() and group_index.keys()==expected_groups.keys()
        for g,f in expected_groups.items():
            assert actual_members[g]=={r['word'] for r in f['members']}
        for i,ids in membership.items():
            assert actual_pointers[i]=={(headmap[expected_groups[g]['home']][0],g) for g in ids if expected_groups[g]['home']!=i}
        assert seen_examples==sum(len(f['members']) for f in groups)
    words=[]
    for i,loc in headmap.items():
        w=nodes[i]
        labels=[r['gloss'] for r in w['reads'] if r.get('construction')] or [w['label']]
        if kind=='thesaurus':labels.extend(expected_groups[g]['title'] for g in membership[i])
        meanings=(r['meaning'] for r in w['reads']) if kind=='dictionary' else (member_senses[g,i].get('meaning','') for g in membership[i])
        words.append([i,w['form'],w['roman'],' · '.join(dict.fromkeys(labels)),loc,membership[i],' '.join(dict.fromkeys(meanings))])
    summary=(f'{len(words):,} headwords and {total_senses:,} senses. Each sense has a native definition and example.' if not groups else
             f'{len(groups):,} word-choice groups with {seen_examples:,} illustrated readings. Look up any of the {len(words):,} headwords to find its groups. In a native pointer, the first number is the volume and the second is the group.')
    guide=read(book.work/'guide.json')
    assert guide['nativeReopened'] and guide['ranges']==len(cat) and sha(book.folders['progressive']/guide['file'])==guide['sha256']
    catalogue(book,cat,words,group_index,summary)
    write_json(book.work/'publication.json',dict(headwords=len(words),senses=total_senses,senseGroups=len(groups),groupExamples=seen_examples,
        progressivePages=2*spreads,progressiveVolumes=len(cat),pdfPages=bound['physicalPDFPages'],nativePrintPages=master['pages'],
        printedSha256=master['sha256'],pdfSha256=bound['sha256'],volumeHashes=hashes,
        alphabeticalOrderChecked=True,headwordPageLocationsChecked=len(words),reverseGroupPointersChecked=sum(map(len,actual_pointers.values())),
        progressiveGuidePages=guide['pages'],examplesComparedInBothFormats=total_senses or seen_examples))
    print(summary,2*spreads,'progressive pages',bound['physicalPDFPages'],'physical PDF pages',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('kind',choices=['dictionary','thesaurus'])
    verify(p.parse_args().kind)
