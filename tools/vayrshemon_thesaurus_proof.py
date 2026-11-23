import hashlib
import json
import re
from collections import defaultdict


from tools.vayrshemon_thesaurus import FOLDER, WORK, TITLE, DICTIONARY, IDIOMS, ADDITIONS, authoring_sources
from tools.dictionary_corpus import page_stream, sha, read
from tools.dictionary_lexicon import load_gzip, language_set, ledger_sources
from tools.dictionary_rows import collate
from tools.compose_historical_book import texts
from tools.unta_language import quantity
from vayrshemon.reading import SCRIPT_SHA, ROMAN_SHA
from vayrshemon.json_stream import write_atomic

def term_columns(manuscript, spreads):
    records = {}
    stream = iter(page_stream(manuscript))
    for spread in spreads:
        pair = next(stream), next(stream)
        frames = [f for page in pair for f in sorted(page['frames'],key=lambda f:int(f['x']))]
        for key,*columns in zip(spread['ids'],*(texts(f) for f in frames),strict=True):
            if key.startswith('term-'):
                records[key[5:]] = tuple(columns)
    return records


def check_new_words(entries, current_terms):
    additions = read(ADDITIONS)['entries']
    units = {u['id']:u for u in read(WORK/'ledger.json')['units']}
    language, _ = language_set()
    idiom_book = next(IDIOMS.parent.glob('*.vay'))
    assert sha(idiom_book)==read(IDIOMS/'publication.json')['sha256']
    idioms = {v['id']:v for v in read(IDIOMS/'entries.json')}
    assert set(units)==set(additions)=={k for k,v in entries.items() if v.get('origin')}
    assert any(path==WORK/'ledger.json' and current for path,title,current in ledger_sources())
    source_spreads = defaultdict(list)
    other_spellings = {language.reading(v['form']).casefold() for k,v in language.lexicon.items() if k not in additions}
    assert len({e['roman'].casefold() for e in additions.values()})==len(units)
    for k,e in additions.items():
        term, u = entries[k], units[k]
        assert language.word(k)[0]==e['form']==term['form']
        assert language.reading(e['form'])==e['roman'] and e['roman'].casefold() not in other_spellings
        assert (language.reading(language.word(k+':pa')[0]) if e['pos']=='verb' else language.reading(language.word(k+':g')[0])) != e['roman']
        assert e['pos'] in ('verb','noun') and e['status']=='authored'
        assert not term['dictionaryRows'] and not term['sources']
        assert any(v['key']==e['nearKey'] and v['family']==e['family'] and v['dictionaryRows'] and v['form']!=term['form'] for v in entries.values())
        idiom = idioms[e['idiomId']]
        assert term['idiomPrecedent']==dict(id=idiom['id'],title=idiom['label'],leftPage=idiom['leftPage'])
        source_spreads[idiom['leftPage']].append(idiom)
        assert e['exampleAnalysis'].count('@')==1 and e['exampleAnalysis'].replace('@',k)==u['analysis']
        assert language.compile(u['analysis'])['text']==u['text']==term['example']
        assert k in u['keys']==language.compile(u['analysis'])['keys'] and term['exampleEnglish']==u['source']==e['exampleEnglish']
        assert e['meaning'] in current_terms[k][3] and u['gloss'] in current_terms[k][2]
        assert language.compile(e['nativeAnalysis'],initial=False)['text'] in current_terms[k][0]
    previous = None
    for page_no,page in enumerate(page_stream(idiom_book),1):
        if page_no in source_spreads:
            previous = texts(next(f for f in page['frames'] if f['name']=='Vayrshemon'))
        elif page_no-1 in source_spreads:
            english = texts(next(f for f in page['frames'] if f['name']=='English'))
            for idiom in source_spreads.pop(page_no-1):
                assert any(n.startswith(idiom['native']+':') and en.startswith(idiom['label']+' —') for n,en in zip(previous,english,strict=True))
            if not source_spreads: break
    assert not source_spreads
    return dict(authoredWordsVerified=len(additions),distinctIdiomPrecedentsVerified=len({v['idiomId'] for v in additions.values()}),
                newExamplesAvailableToDictionary=len(units),idiomInventorySha256=sha(idiom_book))


def verify():
    book = FOLDER/(TITLE+'.vay')
    receipt = read(WORK/'publication.json')
    entries = read(WORK/'sense-register.json')
    index = read(WORK/'page-index.json')
    before = FOLDER.parent/'Archive/Previous editions/Before thesaurus native coinages'/TITLE/'Working'
    old = read(before/'sense-register.json')
    current_examples = {(v['example'],v['exampleEnglish']) for v in entries.values()}
    assert len(current_examples)==len(entries)
    assert all((v['example'],v['exampleEnglish']) in current_examples for v in old.values())
    digests = {p.name:sha(p) for p in authoring_sources()}
    assert digests==receipt['sourceHashes']
    assert hashlib.sha256(json.dumps(digests,sort_keys=True).encode()).hexdigest()==receipt['ledgerSha256']
    assert sha(book)==receipt['sha256']
    pages = list(page_stream(book))
    assert len(pages)==len(index)*2==receipt['pages']
    occurrences = defaultdict(list)
    ordered = []
    pointers = 0
    for spread in index:
        frames = [f for p in pages[spread['leftPage']-1:spread['rightPage']] for f in sorted(p['frames'],key=lambda f:int(f['x']))]
        assert [f['name'] for f in frames]==receipt['columns']
        for f,font in zip(frames[:2],(SCRIPT_SHA,ROMAN_SHA),strict=True):
            for block in f['content']['document']['stories'][0]['blocks']:
                assert {u['sourceFontSha256'] for u in block['runs'] if u['type']=='legacy'}=={font}
        for key,native,roman,gloss,english in zip(spread['ids'],*(texts(f) for f in frames),strict=True):
            assert native==roman and gloss and english
            if key.startswith('term-'):
                term=entries[key[5:]]
                assert term['leftPage']==spread['leftPage']
                assert native.startswith(term['form']+': ') and native.endswith(term['example']) and english.endswith(term['exampleEnglish'])
                occurrences[term['form']].append(spread['leftPage'])
            if key.startswith('index-'):
                form,_,body=native.partition(': ')
                ordered.append(form)
                refs=[(int(a),int(b)) for a,b in re.findall(r'pp\. (\d+)–(\d+)',english)]
                assert [a for a,b in refs]==occurrences[form]
                for a,b in refs:
                    assert a+1==b
                    assert ', '.join(quantity(n,notation='digits')['form'] for n in (a,b)) in body
                    pointers+=1
    assert ordered==sorted(occurrences,key=collate) and len(ordered)==receipt['indexedSpellings'] and pointers==len(entries)
    # Compare the dictionary evidence directly to the pages in its published manuscript.
    dictionary = next(DICTIONARY.parent.glob('*.vay'))
    assert sha(dictionary)==receipt['dictionaryReview']['dictionaryEditionSha256']
    wanted = {rid for v in entries.values() for rid in v['dictionaryRows']}
    raw = load_gzip(DICTIONARY/'dictionary-rows.json.gz')
    rows = {r['id']:r for r in raw['rows'] if r['id'] in wanted}
    spreads = read(DICTIONARY/'page-index.json')
    spots = {}
    for s in spreads:
        for j,k in enumerate(s['ids']):
            if k in wanted:
                spots[k] = s['leftPage'],j
    def pages_needed():
        needs=defaultdict(list)
        for rid,(a,j) in spots.items():
            for offset,flds in enumerate((('text','text'),('gloss','source'))):
                needs[a+offset].append((rid,j,flds))
        return needs
    needs=pages_needed()
    for no,page in enumerate(page_stream(dictionary),1):
        if no not in needs:
            continue
        cols=[texts(f) for f in sorted(page['frames'],key=lambda f:int(f['x']))]
        for rid,j,fields in needs.pop(no):
            assert [c[j] for c in cols]==[rows[rid][f] for f in fields]
        if not needs:break
    assert not needs and wanted==set(spots)
    for entry in entries.values():
        assert entry['dictionaryLeftPages']==sorted({spots[rid][0] for rid in entry['dictionaryRows']})
        assert all(entry['sense'] in rows[rid]['article']['readingIds'] for rid in entry['dictionaryRows'])
    old_columns = term_columns(before.parent/(TITLE+'.vay'),read(before/'page-index.json'))
    current_columns = term_columns(book,index)
    assert len(old_columns)==len(old) and all(current_columns[k]==v for k,v in old_columns.items())
    new_checks = check_new_words(entries,current_columns)
    assert len(entries)==len(old)+new_checks['authoredWordsVerified']
    result=dict(**new_checks,previousFourColumnEntriesPreserved=len(old_columns),publicationSha256=sha(book),previousPublicationSha256=read(before/'publication.json')['sha256'],
                priorNativeAndEnglishExamplesPreserved=len(old),uniqueIllustrations=len(entries),
                verifiedThimforaIndexForms=len(ordered),verifiedBilingualPageDestinations=pointers,
                comparedPublishedDictionaryArticles=len(wanted),checkedScriptAndTransliterationFonts=True)
    print(result,flush=True)
    write_atomic(WORK/'revision-verification.json',result)

if __name__=='__main__':verify()
