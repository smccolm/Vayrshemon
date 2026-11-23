"""Publish the four-column Vayrshemon thesaurus from authored usage contrasts."""
from collections import Counter, defaultdict
import json
import re

from tools.compose_historical_book import texts
from tools.dictionary_corpus import ROOT, WORK as DICTIONARY, normalize, sha
from tools.dictionary_definitions import Definer
from tools.dictionary_layout import DictionaryLayout, FIELDS
from tools.dictionary_lexicon import load_gzip, save_gzip
from tools.dictionary_rows import collate
from tools.editorial_language import TOKEN, WORD
from tools.unta_language import quantity
from vayrshemon import pages
from vayrshemon.file_api import FileSession
from vayrshemon.json_stream import write_atomic

TITLE = 'Vayrshemon Thesaurus - Four-Column Progressive Edition'
FOLDER = ROOT/'Saves'/TITLE
WORK = FOLDER/'Working'
SOURCE = WORK/'synonym-families.txt'
ADDITIONS = WORK/'dictionary-additions.json'
IDIOMS = ROOT/'Saves/Vayrshemon Idiom Inventory - Four-Column Progressive Edition/Working'
STAGE = ROOT/'.local/thesaurus'
COLUMNS = ('Vayrshemon', 'Transliteration 7', 'Construction gloss', 'English')


class ThesaurusLayout(DictionaryLayout):
    # Short alphabetic pointers can fit more rows than full dictionary articles.
    spread_window = 32

    def measured(self, group):
        count, state, error = super().measured(group)
        if count > 1 and group[count-1]['kind'] == 'family':
            # A heading travels with at least its first example on the facing spread.
            return super().measured(group[:count-1])
        return count, state, error


def row(key, kind, ref, native, gloss, english, section='body'):
    return dict(id=key, kind=kind, section=section, reference=ref,
                text=native, gloss=gloss, source=english)


def family_sources():
    return [SOURCE, *sorted(WORK.glob('review-*.txt'))]


def authoring_sources():
    return [*family_sources(), ADDITIONS]


def read_families():
    families = {}
    for path in family_sources():
        family = None
        for n, raw in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
            if not raw.strip():
                continue
            if raw.startswith('# '):
                title, analysis = raw[2:].split(' | ')
                family = families.setdefault(title, dict(title=title, analysis=analysis, entries=[]))
                if family['analysis'] != analysis:
                    raise ValueError(f'Conflicting heading for {title}')
                continue
            key, distinction, note, usage, english = raw.split(' | ')
            label, nuance = distinction.split(' — ')
            if family is None or usage.count('@') != 1 or not re.search(r'[.!?][”’]?$', english):
                raise ValueError(f'Incomplete example at {path.name}:{n}')
            family['entries'].append(dict(key=key, label=label, nuance=nuance,
                                          note=note, usage=usage, english=english))
    additions = defaultdict(list)
    for key, entry in json.loads(ADDITIONS.read_bytes())['entries'].items():
        title = entry['family']
        if title not in families:
            raise ValueError(f'No established comparison family for {key}: {title}')
        additions[title, entry['nearKey']].append(dict(key=key, label=entry['label'], nuance=entry['meaning'],
                                             note=entry['nativeAnalysis'], usage=entry['exampleAnalysis'],
                                             english=entry['exampleEnglish'], coinage=entry))
    for family in families.values():
        adjacent = []
        for entry in family['entries']:
            adjacent.append(entry)
            adjacent.extend(additions.pop((family['title'],entry['key']), ()))
        family['entries'] = adjacent
    if additions:
        raise ValueError(f'Missing established comparison words: {list(additions)}')
    return list(families.values())


def end(text):
    return text.rstrip('. ') + '.'


def compile_rows():
    corpus = load_gzip(DICTIONARY/'attestations.json.gz')
    ledger = load_gzip(DICTIONARY/'dictionary-rows.json.gz')
    dictionary = defaultdict(list)
    for item in ledger['rows']:
        for identity in item.get('article', {}).get('readingIds', []):
            dictionary[identity].append(item['id'])
    editor = Definer(corpus)
    lang = editor.lang
    idioms = {r['id']:r for r in json.loads((IDIOMS/'entries.json').read_bytes())}
    occupied = defaultdict(set)
    for key, record in lang.lexicon.items():
        occupied[normalize(record['form'])].add(key)
    for sense in corpus['senses'].values():
        occupied[normalize(sense['form'])].add(sense['key'])
    idiom_forms = {normalize(r['native']) for r in idioms.values()}
    # Use the readable labels from the language ledger for historical keys too.
    for k, forms in editor.keyrefs.items():
        if '_' in k and k in lang.lexicon:
            exact = [s for s in forms if s['form'] == lang.lexicon[k]['form']]
            if exact:
                lang.glosses[k] = max(exact, key=lambda s: s['contemporary'])['label'].partition('{')[0]
    families = read_families()
    defaults = lang.glosses.copy()
    for f in families:
        for item in f['entries']:
            if '_' in item['key'] and item['key'] not in defaults:
                defaults[item['key']] = item['label'].lower()
    lang.glosses.update(defaults)
    native_examples, english_examples, title_set = set(), set(), set()
    rows, references = [], {}
    lookup = defaultdict(list)
    def bilingual(identifier, kind, native_analysis, english, section='body'):
        out = lang.compile(native_analysis)
        return row(identifier, kind, english, out['text'], out['gloss'], english, section)
    rows.append(bilingual('title', 'title', 'book of word:pl with near:m meaning:pl',
                          'Vayrshemon Thesaurus'))
    rows.append(bilingual('guide', 'guide',
                          'each group word:pl with near:m meaning:pl gather:pr. for each word one_num example its/meaning show:pr. at end of book word:pl in kjv_sequence_order stand:pr.',
                          'Each group brings together words close in meaning. One example shows the use of each word. The alphabetical word index follows the groups.'))
    rows.append(bilingual('use-guide','guide',
                          'when two word:pl near:m be:pr, ask:imp what speak:ag show:inf desire:pr. in verse, in council, and on ship different:m word:pl fit:can:pr. one_num word in several group:pl stand:can:pr.',
                          'Read the examples side by side. Ask what the speaker wants the listener to notice, and whether the words belong in a poem, a council meeting, or an ordinary exchange aboard ship. The index gives every place where a word is discussed.'))
    rows.append(bilingual('coinage-guide','guide',
                          'new:m word:pl among other word:pl stand:pr. in last part new:m word before its/meaning stand:pr. by example which word fit:pr see:imp.',
                          'New Vayrshemon words appear beside the nearest established choices. In the English column each new word is given in Transliteration 7 before its gloss.'))
    for family in families:
        family['heading'] = lang.compile(family['analysis'])
    for family in sorted(families, key=lambda f: collate(f['heading']['text'])):
        title = family['title']
        if title in title_set or len(family['entries']) < 2:
            raise ValueError(f'Invalid synonym family: {title}')
        title_set.add(title)
        gid = 'family-' + re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')
        head = family['heading']
        rows.append(row(gid, 'family', title, head['text'], head['gloss'], title))
        local_forms = set()
        for item in family['entries']:
            k = item['key']
            lang.glosses[k] = item['label'].lower()
            head_form, gloss_name, _ = lang.word(k)
            base = normalize(head_form)
            coinage = item.get('coinage')
            if coinage:
                other_keys = occupied[base] - {k}
                written = corpus['forms'].get(base, [])
                other_readings = {rid for _, ids, *_ in written for rid in ids if rid != k+'@'+base}
                if (other_keys or other_readings or base in idiom_forms or head_form!=coinage['form']
                        or set(head_form)-lang.letters or lang.reading(head_form)!=coinage['roman']
                        or ' ' in head_form or lang.maxima(head_form)==head_form):
                    raise ValueError(f'Invalid or occupied new spelling: {k}, {head_form}, {other_keys}')
                roots = coinage.get('derivationKeys', [])
                if roots and ''.join(lang.word(root)[0] for root in roots) != head_form:
                    raise ValueError('Incorrect compound analysis for '+k)
            witness = [s for s in editor.keyrefs[k] if s['form'] == head_form]
            if not witness and not coinage:
                raise ValueError(f'No matching corpus evidence for {k}')
            sense = max(witness, key=lambda s: (s['contemporary'], s['historical'])) if witness else None
            identity = k+'@'+base
            # Some citations are indexed under an alternative canonical spelling.
            if sense and identity not in corpus['senses']:
                identity = next(i for i,s in corpus['senses'].items() if s is sense)
            if base in local_forms:
                raise ValueError(f'Duplicate spelling within {title}: {k}')
            local_forms.add(base)
            if item['usage'].count('@') != 1 or not re.search(r'[.!?][”’]?$',item['english']):
                raise ValueError('Incomplete usage illustration for '+k)
            analysis = item['usage'].replace('@', k)
            chosen_token = next(t for t in TOKEN.findall(item['usage'].replace('@','TARGET'))
                                if 'TARGET' in t).replace('TARGET',k)
            actual_form = lang.word(chosen_token.rstrip(':'))[0]
            note = lang.compile(item['note'], initial=False)
            ex = lang.compile(analysis)
            if k in defaults:
                lang.glosses[k] = defaults[k]
            else:
                lang.glosses.pop(k, None)
            if k not in ex['keys'] or normalize(actual_form) not in normalize(ex['text']):
                raise ValueError(f'Lost the illustrated form of {k}')
            if ex['text'] in native_examples or item['english'] in english_examples:
                raise ValueError(f'Reused example for {k}')
            native_examples.add(ex['text'])
            english_examples.add(item['english'])
            gloss = gloss_name + ': ' + end(note['gloss']) + ' ' + ex['gloss']
            english = item['label'] + ' — ' + end(item['nuance']) + ' ' + item['english']
            english = english[:1].upper()+english[1:]
            if coinage:
                english = coinage['roman']+' · '+english
            entry_id = k if k not in references else k+'--'+gid
            rows.append(row('term-'+entry_id, 'term', lang.reading(head_form)+' · '+item['label'],
                            head_form+': '+end(note['text'])+' '+ex['text'], gloss, english))
            lookup[head_form].append((entry_id, gid, family, item['label']))
            citations = []
            for ref in sense['citations'] if sense else []:
                ctx = corpus['contexts'].get(ref)
                if ctx:
                    citations.append(dict(book=ctx['book'], reference=ctx['reference'],
                                          chapter=ctx.get('chapter','')))
            if not coinage and (not citations or not dictionary[identity]):
                raise ValueError('Missing source citation for '+k)
            references[entry_id] = dict(key=k, family=title, form=head_form, transliteration=lang.reading(head_form),
                                 sense=identity, dictionaryRows=dictionary[identity], sources=citations,
                                 example=ex['text'], exampleEnglish=item['english'])
            if coinage:
                precedent = idioms[coinage['idiomId']]
                references[entry_id].update(origin='authored in this thesaurus',
                    idiomPrecedent=dict(id=precedent['id'],title=precedent['label'],leftPage=precedent['leftPage']),
                    nearKey=coinage['nearKey'],analysis=analysis,exampleKeys=ex['keys'],exampleGloss=ex['gloss'])
                if not any(e['key']==coinage['nearKey'] and not e.get('coinage') for e in family['entries']):
                    raise ValueError(f'{k} has no established comparison in {title}')
    return rows, lookup, references, lang


def review_dictionary(references):
    """Record the search space separately from the decisions made about synonymy."""
    path = DICTIONARY/'dictionary-rows.json.gz'
    edition = json.loads((DICTIONARY/'publication.json').read_bytes())
    if sha(path) != edition['ledgerSha256']:
        raise ValueError('Dictionary rows differ from the published dictionary ledger.')
    ledger = load_gzip(path)
    senses = load_gzip(DICTIONARY/'attestations.json.gz')['senses']
    field_path = WORK/'semantic-search-fields.txt'
    fields = defaultdict(set)
    for line in field_path.read_text('utf8').splitlines():
        title, vocabulary = line.split(' | ')
        for word in vocabulary.split():
            fields[word].add(title)
    decisions = defaultdict(list)
    for ref in references.values():
        decisions[ref['sense']].append(ref['family'])
    eligible = defaultdict(set)
    native_definitions = defaultdict(set)
    article_notes = {}
    articles = {}
    for row in ledger['rows']:
        if 'article' not in row:
            continue
        readings = row['article']['readingIds']
        heads, labels, prompts, included = set(), set(), set(), set()
        roles = set()
        for identity in readings:
            reading = senses.get(identity)
            if reading is None:
                continue
            heads.add(normalize(reading['form']))
            roles.add(reading['pos'])
            included.update(decisions.get(identity, ()))
            if reading['pos'] in ('numeral', 'proper'):
                continue
            label = reading['label'].partition('{')[0].strip().lower()
            key = reading['key']
            labels.add(label)
            for alias in (key, label, key.rsplit('_',1)[-1]):
                prompts.update(fields.get(alias, ()))
            eligible[label].add(normalize(reading['form']))
        if labels:
            note = normalize(row['article']['definition'].strip(' .'))
            if note and len(note.split())<=4:
                native_definitions[note].update(heads)
                article_notes[row['id']] = note
        articles[row['id']] = dict(forms=sorted(heads),labels=sorted(labels),roles=sorted(roles),
                                   searchFields=sorted(prompts),publishedFamilies=sorted(included))
    counts = Counter()
    for row_id, article in articles.items():
        collisions = [s for s in article['labels'] if len(eligible[s])>1]
        article['sharedEnglishLabels'] = collisions
        note = article_notes.get(row_id)
        matches = len(native_definitions[note]) if note else 0
        if 2<=matches<=14:
            article['sharedNativeParaphrase'] = note
        reason = ('published' if article['publishedFamilies'] else
                  'lexical candidate' if collisions or article['searchFields'] or 'sharedNativeParaphrase' in article else
                  'name or numeral' if article['roles'] and not article['labels'] else
                  'supplementary article without a lexical key' if not article['roles'] else
                  'no match in these searches')
        article['status'] = reason
        counts[reason] += 1
    if len(articles) != edition['examples']:
        raise ValueError('Dictionary review omitted articles.')
    if any(rid not in articles for v in references.values() for rid in v['dictionaryRows']):
        raise ValueError('Unresolved dictionary article in the sense register.')
    summary = dict(dictionaryHeadwords=edition['headwords'],dictionaryArticles=len(articles),
                   dictionaryLedgerSha256=edition['ledgerSha256'],dictionaryEditionSha256=edition['sha256'],
                   searchFieldsSha256=sha(field_path),searchFieldCount=len(set().union(*fields.values())),
                   englishLabelsSharedByDistinctForms=sum(len(v)>1 for v in eligible.values()),
                   shortNativeParaphrasesSharedByDistinctForms=sum(2<=len(v)<=14 for v in native_definitions.values()),
                   articleCounts=dict(counts))
    return summary, articles


def locations(rows, renderer):
    start = 0
    result = {}
    left = 1
    while start < len(rows):
        count, _, _ = renderer.measured(rows[start:start+renderer.spread_window])
        for r in rows[start:start+count]:
            result[r['id']] = left
        start += count
        left += 2
    return result


def append_index(rows, lookup, loc, lang):
    heading = lang.compile('list of word:pl in kjv_sequence_order')
    rows.append(row('index','index-title','Word index',heading['text'],heading['gloss'],
                    'Alphabetical word index','index'))
    ordered = sorted(lookup, key=collate)
    for idx, form in enumerate(ordered, 1):
        ns, gs, es = [], [], []
        for key, _, family, label in lookup[form]:
            page = loc['term-'+key]
            leaf = ', '.join(quantity(p, notation='digits')['form'] for p in (page, page+1))
            ns.append(f"{lang.compile(family['analysis'], initial=False)['text']} {leaf}")
            gs.append(f"{label.lower()} · {page}–{page+1}")
            es.append(f"{label} · {family['title']}, pp. {page}–{page+1}")
        rows.append(row('index-'+str(idx), 'index-word', lang.reading(form),
                        form+': '+'. '.join(ns)+'.', '. '.join(gs)+'.', '. '.join(es)+'.','index'))
    return ordered


def reopen(path, rows, index, proofs):
    session = FileSession(ROOT, source_fonts=False, recovery=False)
    session.remember = lambda *a: None
    session.log.emit = lambda *a, **kw: None
    try:
        session.open(path, advance_revision=False)
        if session.state['title'] != TITLE or session.saved_page_mode != 'two':
            raise ValueError('Incorrect native title or page mode')
        native_pages = session.state['pages']
        if len(native_pages) != 2*len(index):
            raise ValueError('Unexpected reopened page count')
        lookup = {r['id']:r for r in rows}
        for spread in index:
            pair = native_pages[spread['leftPage']-1:spread['rightPage']]
            frames = [f for page in pair for f in sorted(page['frames'],key=lambda f:int(f['x']))]
            if [f['name'] for f in frames] != list(COLUMNS):
                raise ValueError('Reopened column order differs')
            if lookup[spread['ids'][-1]]['kind']=='family':
                raise ValueError('Stranded family heading')
            for field, frame in zip(FIELDS,frames,strict=True):
                if texts(frame) != [lookup[i][field] for i in spread['ids']]:
                    raise ValueError('Reopened text differs on '+str(spread['leftPage']))
        for n in sorted(set(proofs)):
            image,_ = pages.render(session,page_id=native_pages[n-1]['pageId'],
                                   mode='mono',dpi=100,reading=True)
            if not image.save(str(STAGE/f'proof-{n}.png')):
                raise OSError('Failed to save print proof')
    finally:
        session.finish()


def publish():
    STAGE.mkdir(parents=True,exist_ok=True)
    dest = FOLDER/(TITLE+'.vay')
    receipt = WORK/'publication.json'
    if dest.exists() and (not receipt.exists() or json.loads(receipt.read_bytes())['sha256'] != sha(dest)):
        raise ValueError('Reconcile independent edits in the published thesaurus before a rebuild.')
    rows, lookup, references, lang = compile_rows()
    renderer = ThesaurusLayout(title=TITLE, document_id='document.native-thesaurus',
                               id_prefix='thesaurus', column_names=COLUMNS,cache_root=STAGE)
    stage = STAGE/'publication.vay'
    try:
        loc = locations(rows, renderer)
        ordered = append_index(rows, lookup, loc, lang)
        from hashlib import sha256
        source_hashes = {p.name:sha(p) for p in authoring_sources()}
        source_digest = sha256(json.dumps(source_hashes,sort_keys=True).encode()).hexdigest()
        report, index = renderer.build(rows,stage,source_digest)
    finally:
        renderer.session.finish()
    final_locations = {i:s['leftPage'] for s in index for i in s['ids']}
    if any(final_locations[i]!=p for i,p in loc.items()):
        raise ValueError('Index page references became stale')
    for key, ref in references.items():
        ref['leftPage'] = final_locations['term-'+key]
    new_entries = {k:v for k,v in references.items() if v.get('origin')}
    units = [dict(id=k,reference=f"{ref['transliteration']} (pp. {ref['leftPage']}–{ref['leftPage']+1})",
                  chapter=ref['family'], text=ref['example'], source=ref['exampleEnglish'], gloss=ref['exampleGloss'],
                  keys=ref['exampleKeys'], analysis=ref['analysis']) for k,ref in new_entries.items()]
    dictionary_pages = {key:spread['leftPage'] for spread in json.loads((DICTIONARY/'page-index.json').read_bytes())
                        for key in spread['ids']}
    for ref in references.values():
        ref['dictionaryLeftPages'] = sorted({dictionary_pages[rid] for rid in ref['dictionaryRows']})
    scope, articles = review_dictionary(references)
    index_page = final_locations['index']
    left_proofs = [1,loc['term-apply'],loc['term-damat_roadstead'],loc['term-boyle_infusion'],
                   loc['term-milton_ambiguous'],index_page,report['pages']-1]
    new_pages = sorted({r['leftPage'] for r in new_entries.values()})
    left_proofs.extend(new_pages[::max(1,len(new_pages)//5)])
    proofs = [n+i for n in left_proofs for i in (0,1)]
    reopen(stage,rows,index,proofs)
    report.update(families=sum(r['kind']=='family' for r in rows),senseExamples=len(references),
                  sourceHashes=source_hashes,dictionaryReview=scope,
                  distinctDictionaryReadings=len({r['sense'] for r in references.values() if r['dictionaryRows']}),
                  authoredWords=len(new_entries),familiesWithAuthoredWords=len({r['family'] for r in new_entries.values()}),
                  indexedSpellings=len(ordered),indexStartsOn=index_page,
                  exampleProvenance='Original usage illustrations composed for this edition.',
                  wordIndexOrder='Full-word Thimfora collation used by the native dictionary.',
                  nativeReopenVerified=True,allIndexDestinationsVerified=True,
                  proofPages=sorted(set(proofs)),columns=list(COLUMNS))
    # Keep the book and its working files reconstructible from the authored readings.
    write_atomic(WORK/'sense-register.json',references)
    write_atomic(WORK/'ledger.json',dict(book='Vayrshemon Thesaurus',units=units))
    save_gzip(WORK/'dictionary-review.json.gz',dict(scope=scope,articles=articles))
    write_atomic(WORK/'page-index.json',index)
    stage.replace(dest)
    write_atomic(receipt,report)
    print(json.dumps(report,ensure_ascii=True,indent=2),flush=True)


if __name__ == '__main__':
    publish()

