"""Collate attested lexical identities, grammatical analyses and cited contexts."""
from collections import Counter, defaultdict
from functools import lru_cache
import gzip
import json
import re

from tools.corpus_clause_revision import textpaths
from tools.dampier_working import number_gloss, source_language
from tools.dictionary_corpus import BOOK, ROOT, WORK, archived_files, normalize, read, sha, witness_name, written
from tools.editorial_language import EditorialLanguage, TOKEN, WORD
from tools.kjv_historical_flow import compiler
from tools.shakespeare_collected import sources
from tools.unta_language import quantity


def save_gzip(path, obj):
    part = path.with_suffix('.writing')
    with gzip.open(part, 'wt', encoding='utf8', compresslevel=4) as file:
        json.dump(obj,file,ensure_ascii=False,separators=(',',':'))
    part.replace(path)


def load_gzip(path):
    with gzip.open(path,'rt',encoding='utf8') as file:
        return json.load(file)


def ledger_sources():
    titles = {w['slug']:w['title'] for w in sources()}
    current = {path:titles.get(slug,'King James Bible') for slug,path in textpaths()}
    for path in sorted((ROOT/'Saves').glob('*/Working/ledger.json')):
        if not path.is_relative_to(BOOK):
            current[path] = path.parent.parent.name.split(' - Four-Column')[0]
    for path,title in current.items():
        yield path,title,True
    archives = ROOT/'Saves/Archive'
    other = set(archives.rglob('*ledger.json')) | {p for p in archived_files() if p.name.endswith('ledger.json')}
    other.update((archives/'Shakespeare Project 0.13/Ledgers').glob('*.json'))
    for path in sorted(other-current.keys()):
        if path.name != 'correction-ledger.json':
            yield path,path.parent.name,False


NUM = re.compile(r'unta_(cardinal|ordinal|times|fold|fraction)_([a-j]+)_over_([a-j]+)(_digits)?$')


def numeric(key):
    m = NUM.fullmatch(key)
    if not m:
        return None
    value,den = (int(''.join(str(ord(c)-97) for c in s)) for s in m.group(2,3))
    kind = m[1]
    q = quantity(value,kind,den,notation='digits' if m[4] else 'words')
    if kind in ('cardinal','ordinal'):
        label = number_gloss(value,kind=='ordinal','words')
    else:
        label = f'{value}/{den}' if den!=1 else str(value)
        label += {'fold':'-fold','times':' times','fraction':' of a whole'}[kind]
    return dict(form=q['form'],meaning=label,pos='numeral',number=q,label=label)


def language_set():
    common,_,_ = source_language()
    for path in sorted((ROOT/'Saves').glob('*/Working/dictionary-additions.json')):
        if path.is_relative_to(BOOK):continue
        entries=read(path).get('entries',{})
        if not isinstance(entries,dict):continue
        for key,entry in entries.items():
            if key not in common.lexicon and isinstance(entry,dict) and all(k in entry for k in ('form','meaning')):
                common.lexicon[key]=entry
                common.glosses[key]=entry.get('label') or key.replace('_','-')
    historic = compiler(ROOT/'data/language/archaic-kjv-285')
    return common, historic


def compile_corpus():
    WORK.mkdir(parents=True,exist_ok=True)
    common,bible = language_set()
    lexicons = {'current':common,'285':bible}
    senses, forms, catalog = {}, defaultdict(dict), []
    contexts, identities, seen_docs = {}, {}, {}
    best_score = {}
    known_witnesses = set()
    omissions = Counter()
    for path, book, active in ledger_sources():
        digest = sha(path)
        source_name = witness_name(path)
        if digest in seen_docs:
            catalog.append(dict(path=source_name,sha256=digest,sameAs=seen_docs[digest]))
            continue
        doc = read(path)
        if not isinstance(doc,dict) or not isinstance(doc.get('units'),list):
            continue
        seen_docs[digest] = source_name
        units = doc['units']
        version = str(doc.get('languageVersion') or doc.get('version') or '')
        version_match = re.search(r'kjv[.-](\d+)',version+' '+source_name,re.I)
        version_id = version_match[1] if version_match else 'current'
        if version_id not in lexicons:
            folder = ROOT / ('data/language/archaic-kjv-'+version_id)
            lexicons[version_id] = compiler(folder) if (folder/'compiler.py').exists() else bible
        language = lexicons[version_id]
        if not active:
            book = doc.get('book') or doc.get('source') or book
            if not isinstance(book,str):
                book = path.parent.name
        work_id = len(catalog)
        catalog.append(dict(path=source_name,sha256=digest,book=book,version=version,
                            units=len(units),current=active))
        ignored_ids = set()
        overrides = path.with_name('preserved-edit-overrides.json')
        if active and overrides.exists():
            for override in read(overrides)['spreads'].values():
                ignored_ids.update(override['originalLedgerUnitIds'])
        cache = {}

        def entry(key):
            if key in cache:
                return cache[key]
            record = language.lexicon.get(key) or common.lexicon.get(key) or bible.lexicon.get(key) or numeric(key)
            if record is None:
                cache[key] = None
                return None
            form = record['form']
            identity = key+'@'+normalize(form)
            if identity not in senses:
                label = record.get('label') or language.glosses.get(key) or common.glosses.get(key) or key.replace('_','-')
                senses[identity] = dict(key=key,form=form,reading=common.reading(form),label=label,
                    pos=record.get('pos',''),meaning=record['meaning'],roots=record.get('derivationKeys',[]),
                    origin=record.get('origin',''),usageScope=record.get('usageScope',''),
                    contemporary=0,historical=0,works={},citations=[])
                if 'number' in record or NUM.fullmatch(key):
                    num = numeric(key)
                    if num:
                        senses[identity]['number'] = num['number']
                identities[identity] = len(identities)
            cache[key] = identity
            return identity

        @lru_cache(maxsize=None)
        def analyzed(token):
            clean = token.rstrip(':')
            if not clean or not WORD.fullmatch(clean):
                return None
            stem = clean.split('/')[-1].split(':')[0]
            keys = stem.split('+')
            if any(entry(k) is None for k in keys):
                return None
            for k in keys:
                if k not in language.lexicon:
                    language.lexicon[k] = common.lexicon.get(k) or bible.lexicon.get(k) or numeric(k)
            try:
                surface, gloss, used = language.word(clean)
            except (ValueError,KeyError,IndexError):
                return None
            return surface,gloss,tuple(entry(k) for k in used if entry(k))

        for u in units:
            if not isinstance(u,dict) or not u.get('text') or not u.get('analysis') or u.get('id') in ignored_ids:
                continue
            identifier = str(u.get('id',u.get('reference','')))
            context_key = (u['analysis'],u['text'])
            if not active and context_key in known_witnesses:
                continue
            known_witnesses.add(context_key)
            count = Counter(u.get('keys',[]))
            slot_words = {normalize(s) for s in written(u['text'])}
            for token in TOKEN.findall(u['analysis']):
                a = analyzed(token)
                if a is None:
                    continue
                surface,g,uses = a
                for word in written(surface):
                    n = normalize(word)
                    if n in slot_words and uses:
                        link = (g,uses)
                        forms[n].setdefault(link, [0,0])[0 if active else 1] += 1
            if not count:
                count.update(k for t in TOKEN.findall(u['analysis']) if (a:=analyzed(t)) for k in [senses[x]['key'] for x in a[2]])
            for k,n in count.items():
                ident = entry(k)
                if not ident:
                    omissions[k] += n
                    continue
                sense = senses[ident]
                sense['contemporary' if active else 'historical'] += n
                if active:
                    sense['works'][work_id] = sense['works'].get(work_id,0)+n
                citation_key = f'{work_id}/{identifier}'
                # A complete, economical attestation takes priority over a heading.
                length = len(u['text'].split())
                score = (not active, not 4 <= length <= 42, abs(length-11))
                if score < best_score.get(ident,(True,True,10**9)):
                    best_score[ident] = score
                    sense['citations'] = [citation_key]
                    contexts[citation_key] = dict(reference=u.get('reference',identifier),
                        chapter=u.get('chapter',u.get('section','')), text=u['text'],gloss=u.get('gloss',''),
                        source=u.get('source',''),analysis=u['analysis'],book=book)
        analyzed.cache_clear()
        print(f'{book}: {len(senses)} attested readings',flush=True)
    used_contexts = {c for s in senses.values() for c in s['citations']}
    output = dict(catalog=catalog,senses=senses,
                  contexts={k:v for k,v in contexts.items() if k in used_contexts},
                  forms={f:[[g,list(ids),*v] for (g,ids),v in d.items()] for f,d in forms.items()},
                  unresolvedKeys=dict(omissions))
    save_gzip(WORK/'attestations.json.gz',output)
    print(len(senses),'semantic readings;',len(forms),'analyzed written forms;',len(omissions),'unresolved keys',flush=True)


if __name__ == '__main__':
    compile_corpus()
