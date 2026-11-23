"""Recover readings from the saved parallel columns, including manuscript-only edits."""
from collections import Counter, defaultdict
from difflib import SequenceMatcher
import re

from tools.compose_historical_book import texts
from tools.dictionary_corpus import connect, normalize, page_stream, publications, witness_name, written
from tools.dictionary_lexicon import WORK, load_gzip, save_gzip


def form_readings():
    corpus = load_gzip(WORK/'attestations.json.gz')
    forms = corpus['forms']
    reverse = defaultdict(set)
    for form, rows in forms.items():
        for gloss, keys, *_ in rows:
            reverse[gloss].add(tuple(keys))
    sources = {witness_name(p):p for p in publications()}
    with connect() as db:
        surface = {f for f, in db.execute('SELECT DISTINCT form FROM written')}
        missing = surface - forms.keys()
        result = {}
        for word in sorted(missing):
            if re.fullmatch(r'[0-9ÀÁ]+',word):
                result[word] = dict(value=int(word.replace('À','A').replace('Á','B'),12))
        for name in sorted(sources,key=lambda n:('Archive/' in n,'Letter' in n or 'Print' in n,n)):
            locations = {w for w, in db.execute('SELECT form FROM written WHERE manuscript=?',(name,)) if w in missing and w not in result}
            if not locations:
                continue
            left = None
            for page_no,page in enumerate(page_stream(sources[name]),1):
                fs=sorted(page['frames'],key=lambda f:int(f['x']))
                if len(fs)<2:
                    left=None
                    continue
                native = next((f for f in fs if 'Vayrshemon' in f['name'] and 'ransliter' not in f['name']),None)
                construction = next((f for f in fs if 'gloss' in f['name'].lower()),None)
                if native:
                    left=texts(native)
                elif left and construction:
                    right=texts(construction)
                    if len(left)!=len(right):
                        left=None
                        continue
                    for text,gloss in zip(left,right):
                        words=[normalize(w) for w in written(text)]
                        if not locations.intersection(words):
                            continue
                        # Keep grammatical parentheses, strip only sentence marks.
                        gs=[v.strip(' .,;:?![]“”‘’') for v in gloss.split(' · ') if re.search(r'\w',v)]
                        if len(words)==len(gs):
                            pairs=zip(words,gs)
                        else:
                            # Match exact bilingual anchors before admitting a 1:1 gap.
                            equivalents=[next((next(iter(d)) for g,d,*_ in forms.get(w,[]) if d),'') for w in words]
                            labels=[next(iter(next(iter(reverse.get(g,{()})))), '') if len(reverse.get(g,()))==1 else '' for g in gs]
                            gaps=SequenceMatcher(None,equivalents,labels,autojunk=False).get_opcodes()
                            pairs=[(words[i],gs[j+i-lo]) for tag,lo,hi,j,k in gaps
                                   if (tag=='equal' and any(equivalents[lo:hi]) or tag=='replace' and hi-lo==k-j==1)
                                   for i in range(lo,hi) if equivalents[i] or tag=='replace']
                        for w,g in pairs:
                            if w in locations:
                                result[w]=dict(gloss=g,analyses=[list(v) for v in sorted(reverse.get(g,()))],
                                               manuscript=name,page=page_no-1)
                                locations.discard(w)
                    left=None
                else:
                    left=None
                if not locations:
                    break
        for w in missing-result.keys():
            path,page,example=db.execute('SELECT manuscript,first_page,example FROM written WHERE form=? ORDER BY manuscript LIKE ?, manuscript LIMIT 1',(w,'%Archive%')).fetchone()
            result[w]=dict(manuscript=path,page=page,example=example)
    save_gzip(WORK/'manuscript-readings.json.gz',result)
    review_saved_readings()
    print(Counter('number' if 'value' in v else 'gloss' if 'gloss' in v else 'witness' for v in result.values()))


def review_saved_readings():
    """Check the *authored token boundaries* against the native page, even when
    a multiword entry receives just one gloss or the scribe changes a spelling."""
    from tools.dictionary_lexicon import ledger_sources,language_set,numeric
    from tools.dictionary_corpus import read
    from tools.editorial_language import TOKEN,WORD
    from functools import lru_cache
    corpus=load_gzip(WORK/'attestations.json.gz')
    raw=load_gzip(WORK/'manuscript-readings.json.gz')
    by_page=defaultdict(lambda:defaultdict(set))
    for f,v in raw.items():
        if v.get('manuscript'):by_page[v['manuscript']][v['page']].add(f)
    pages={witness_name(p):p for p in publications()}
    passages=defaultdict(list)
    normalize_source=lambda x:' '.join(x.split()).casefold()
    for name,wanted in by_page.items():
        left=None
        for no,p in enumerate(page_stream(pages[name]),1):
            if no>max(wanted)+1:break
            fs=sorted(p['frames'],key=lambda f:int(f['x']))
            if no in wanted:
                left=texts(fs[0]) if len(fs)==2 else None
            if left and no-1 in wanted and len(fs)==2:
                for n,en in zip(left,texts(fs[1])):
                    native=[normalize(w) for w in written(n)]
                    look=wanted[no-1].intersection(native)
                    if look:passages[normalize_source(en)].append((native,look))
                left=None
    modern,older=language_set()
    modern.lexicon={**older.lexicon,**modern.lexicon}
    def resolve(key):
        if key not in modern.lexicon:
            rec=numeric(key)
            if rec:modern.lexicon[key]=rec
    @lru_cache(maxsize=75000)
    def piece(token):
        if token.startswith('{{'):
            return [(normalize(w),'feigned speech',[]) for w in written(token[2:-2])]
        if not WORD.fullmatch(token):return []
        try:
            clean=token.rstrip(':')
            for k in re.split(r'[+/]',clean.split(':')[0]):resolve(k)
            text,gloss,keys=modern.word(clean)
        except (ValueError,KeyError):return []
        ids=[k+'@'+normalize(modern.lexicon[k]['form']) for k in keys]
        return [(normalize(w),gloss,ids if all(k in corpus['senses'] for k in ids) else []) for w in written(text)]
    best={};seen=set()
    for path,book,current in ledger_sources():
        doc=read(path)
        for u in doc.get('units',[]) if isinstance(doc,dict) else []:
            en=normalize_source(u.get('source',''))
            analysis=u.get('analysis')
            if not analysis or en not in passages or (en,analysis) in seen:continue
            seen.add((en,analysis))
            seq=[data for t in TOKEN.findall(analysis) for data in piece(t)]
            expected=[r[0] for r in seq]
            for words,look in passages[en]:
                match=SequenceMatcher(None,expected,words,autojunk=False)
                if match.ratio()<.58:continue
                for tag,a,b,x,y in match.get_opcodes():
                    if tag!='equal' and (tag!='replace' or b-a!=y-x):continue
                    for ix in range(x,y):
                        word=words[ix]
                        if word not in look:continue
                        _,g,ids=seq[a+ix-x]
                        score=(tag=='equal',match.ratio(),current)
                        if score>best.get(word,((False,0,False),))[0]:best[word]=(score,g,ids)
    corrected=0
    for f,(_,g,ids) in best.items():
        corrected+=g!=raw[f].get('gloss')
        raw[f].update(gloss=g,analyses=[ids] if ids else [],tokenBoundaryVerified=True)
    save_gzip(WORK/'manuscript-readings.json.gz',raw)
    print(f'Checked authored token boundaries for {len(best)} manuscript spellings; {corrected} readings corrected.',flush=True)


if __name__=='__main__':
    form_readings()
