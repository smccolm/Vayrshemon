"""Reopen the issued dictionary with the editor and independently check its lookup coverage."""
from collections import Counter
import re

from PySide6.QtWidgets import QApplication
from tools.compose_historical_book import texts
from tools.dictionary_corpus import BOOK, EDITION, ROOT, WORK, TOKENIZATION, connect, normalize, read, sha
from tools.dictionary_layout import FIELDS, STAGE
from tools.dictionary_lexicon import load_gzip
from tools.dictionary_order_audit import MINIMA, check_native_order
from tools.dictionary_place_words import place_words
from tools.dictionary_rows import collate, pointer
from tools.dictionary_scope import NUMERAL_TOKEN, citation_exclusions, lexical_form_analysis, word_senses
from vayrshemon import language, pages
from vayrshemon.file_api import FileSession
from vayrshemon.json_stream import write_atomic


def require(condition,message):
    if not condition:
        raise ValueError(message)


def verify():
    target=BOOK/(EDITION+'.vay')
    pub=read(WORK/'publication.json')
    require(sha(target)==pub['sha256'],'Native publication hash mismatch')
    require(sha(WORK/'dictionary-rows.json.gz')==pub['ledgerSha256'],'Entry ledger hash mismatch')
    rows=load_gzip(WORK/'dictionary-rows.json.gz')['rows']
    index=read(WORK/'page-index.json')
    corpus=load_gzip(WORK/'attestations.json.gz')
    require(not corpus['unresolvedKeys'],'Unresolved semantic identities')
    lexical=word_senses(corpus)
    places=place_words(corpus,lexical)
    included=lexical.keys() | places.keys()
    from tools.dictionary_reference_books import BATCH, harvest
    batch=load_gzip(BATCH) if BATCH.exists() else None
    idiom_examples=set()
    if batch:
        # Re-read the actual four-column publications and recompile the grammar
        # examples. Idioms may split or inflect several words in running speech.
        refreshed=harvest(persist=False)
        import json
        require(json.loads(json.dumps(refreshed))==batch,'Reference books differ from the editorial intake')
        published={r['id']:r for r in rows}
        for r in batch['entries']:
            saved=published[r['id']]
            require(saved['article']==r['article'] and all(saved[k]==r[k] for k in ('text','gloss','reference'))
                    and saved['source'].endswith(r['source']), 'Changed source reading '+r['id'])
            included.update(r['article']['readingIds'])
            if r['article']['exampleMethod']=='published idiom example':
                idiom_examples.add((r['text'].partition('. ')[0],r['article']['example']))
    manuscript=load_gzip(WORK/'manuscript-readings.json.gz')
    distribution=Counter(normalize(s['form']) for s in lexical.values())
    finder=[f for r in rows if r['section'].startswith('forms-') for f in r['text'].split(', ')]
    with connect() as db:
        spellings={r[0] for r in db.execute('SELECT DISTINCT form FROM written')}
        witnesses=[r[0] for r in db.execute('SELECT path FROM manuscripts')]
        require({r[0] for r in db.execute('SELECT path FROM word_boundaries WHERE version=?',(TOKENIZATION,))}==set(witnesses),
                'Some manuscripts still use earlier word-boundary rules')
    require(normalize('Korrientēs') in spellings and
            all('Corrientes' not in g for g,*_ in corpus['forms'].get('s',[])),
            'A fallback-font vowel divided a native name into separate words')
    # Reconstruct coverage from the witness records, independently of the
    # publication routine that selects and ranks the displayed analyses.
    ledger_words={f for f,analyses in corpus['forms'].items()
                  if any(lexical_form_analysis(f,ids,corpus,lexical) for _,ids,*_ in analyses)}
    manuscript_words={f for f,v in manuscript.items() if 'value' not in v and v.get('gloss')!='feigned speech' and
                      (not v.get('analyses') or any(lexical_form_analysis(f,ids,corpus,lexical) for ids in v['analyses']))}
    eligible={f for f in spellings.intersection(ledger_words|manuscript_words) if not NUMERAL_TOKEN.fullmatch(f)}
    eligible.update(s for p in places.values() for s in (p.form,*p.variants))
    if batch:eligible.update(batch['forms'])
    require(len(finder)==len(eligible) and set(finder)==eligible,'Incomplete or duplicated lexical form finder')
    require(normalize('Korrientēs') in eligible,'Missing manuscript name from the word finder')
    require(not any(NUMERAL_TOKEN.fullmatch(f) for f in finder),'Numerical notation indexed as a word')
    require(finder==sorted(finder,key=collate),'Wrong written-form collation')
    require({i for r in rows if 'article' in r for i in r['article']['readingIds']}==included,'Headwords differ from eligible lexical readings and place words')
    by_id={r['id']:r for r in rows}
    citation_ids,citation_forms=citation_exclusions(corpus,manuscript,spellings-eligible)
    require(sorted(citation_ids)==pub['excludedCitationReadings'] and
            sorted(citation_forms)==pub['excludedCitationSpellings'],'Citation exclusions differ from publication')
    require('dambk_jd@j d' in citation_ids and 'boyle_initial_j@j' in citation_ids and
            all('sense-'+pointer(i) not in by_id for i in citation_ids),'Standalone attribution entered as a word')
    require('school_source_letter_a@a' in lexical and not citation_forms & set(finder),
            'Confused a written letter with an attribution initial')
    require(all('sense-'+pointer(i) not in by_id for i,s in corpus['senses'].items() if s.get('number') and i not in places),
            'Generated quantity published as a headword')
    require(all(any(s['key']==key for s in lexical.values()) for key in
            ('word','measure','one','number_aggregate','reckon','pair','kjv_score','locke_second_kings')),
            'A lexical meaning or the proper title of 2 Kings was lost')
    require(not any(NUMERAL_TOKEN.fullmatch(r['section'].split('-')[-1])
                    for r in rows),'Number-symbol section left in dictionary')
    require(not any(r['source'].startswith('Unta numeral for ') for r in rows),'Manuscript-only numeral published')
    for ident,relationship in [('kjv_cleophas_john@kleofas','husband'),('kjv_mary_cleophas_wife_john@mari','wife')]:
        require(by_id['sense-'+pointer(ident)]['gloss'].partition('. ')[2].startswith(relationship+' · of'),
                'Reversed relationship in John 19:25')
    king_lookup=next(r for r in rows if r['section'].startswith('forms-') and 'varßn' in r['text'].split(', '))
    require('varōn' in king_lookup['source'] and 'favour' not in king_lookup['source'],
            'A companion word in a compound was promoted to the headword for king')
    row_pages={}
    bounds={}
    for i,spread in enumerate(index):
        a,b=spread['leftPage'],spread['rightPage']
        require((a,b)==(2*i+1,2*i+2),'Broken spread sequence')
        sections={by_id[uid]['section'] for uid in spread['ids']}
        require(len(sections)==1,'Letter boundary in middle of spread')
        section=sections.pop()
        bounds[section]=(bounds.get(section,(a,b))[0],b)
        row_pages.update((uid,a) for uid in spread['ids'])
    require(list(row_pages)==list(by_id) and len(rows)==len(row_pages),'Broken page index')
    sections={'Headwords':'headwords','Manuscript readings':'manuscript','Written forms':'forms'}
    actual={}
    for row in rows:
        if row['section']!='directory':continue
        initial=chr(int(row['id'].split('-')[1]))
        for name,a,b in re.findall(r'(Headwords|Manuscript readings|Written forms) pp\. (\d+)–(\d+)',row['source']):
            actual[sections[name]+'-'+initial]=(int(a),int(b))
    require(actual=={k:v for k,v in bounds.items() if k not in ('opening','directory')},
            'Letter directory differs from actual pagination')
    probes=['jar'+letter for letter in MINIMA]
    require(len(MINIMA)==47 and sorted(probes,key=collate)==probes,'Thimfora chart order mismatch')
    primary=[r for r in rows if r['section'].startswith('headwords-')]
    units='fßlem neksus ÕÅtus venik bÅrum jensis ßd×um pÉrsus krizum deksin eÛnÉ yamen'.split()
    dozens='fßlem Ém×nß sid×um salisiks Çramen riv×um vÅkus lanserß Énimés Õen×um mesidÉl onez'.split()
    expected_slots={(c,e):f for e,series in enumerate((units,dozens,[units[0]]+[u+' nßrum' for u in units[1:]]))
                    for c,f in enumerate(series)}
    place_rows=[r for r in primary if 'untaPlaces' in r]
    published_slots={tuple(slot):r['text'].partition('. ')[0] for r in place_rows for slot in r['untaPlaces']}
    require(len(place_rows)==34 and sum(len(r['untaPlaces']) for r in place_rows)==36 and
            published_slots==expected_slots,'Wrong, missing or duplicate Unta place-word entry')
    require(set(published_slots.values())<=set(finder),'Unta headword missing from spelling lookup')
    place_pages={r['reference']:row_pages[r['id']] for r in place_rows}
    require('änimu\u0307s' in place_pages,'The dotted-u spelling for eight dozen was lost in lookup text')
    require(any('Jonah.vay' in w for w in witnesses) and any('Micro-translation' in w for w in witnesses),
            'Early independent manuscripts missing')
    for r in rows:
        if r['id'].startswith(('sense-','written-','usage-')):
            require(r['text'].partition('. ')[2].strip(' .') and 'in preparation' not in r['source'],
                    'Empty native definition '+r['id'])
    from tools.dictionary_rows import citation
    from tools.dictionary_sentence_witnesses import head_present
    articles=[r for r in rows if 'article' in r]
    require(len(articles)==pub['examples'],'Example count differs from publication')
    from tools.dictionary_sense_revision import GENERIC, UP, skeleton
    from collections import defaultdict
    from tools.dictionary_corpus import WORDS
    example_shapes=defaultdict(set)
    native_shapes=defaultdict(set)
    name_forms={normalize(s['form']) for s in corpus['senses'].values() if s['pos']=='proper'}
    name_forms.difference_update(normalize(s['form']) for s in corpus['senses'].values() if s['pos']!='proper')
    for r in articles:
        article=r['article'];head=r['text'].partition('. ')[0]
        en=article['exampleEnglish']
        shape=skeleton(en);head_key=normalize(head)
        require(shape not in example_shapes[head_key], 'Sibling examples differ only by names: '+r['id'])
        example_shapes[head_key].add(shape)
        native_shape=tuple('@' if token in name_forms else token for token in
                           (normalize(m[0]) for m in WORDS.finditer(article['example'])))
        require(native_shape not in native_shapes[head_key], 'Repeated native example after masking names: '+r['id'])
        native_shapes[head_key].add(native_shape)
        require(not GENERIC.search(en),'Generic example: '+r['id'])
        initial=WORDS.search(article['example'])
        require(initial is not None and initial[0][0] not in UP,'Example begins in minima: '+r['id'])
        require((head_present(article['example'],head) or (head,article['example']) in idiom_examples)
                and r['text']==head+'. '+article['definition']+' '+article['example'],
                'Missing headword or example in native text: '+r['id'])
        require(' Example: ' in r['source'] and article['references'] and
                all(ref in r['source'] for ref in article['references']), 'Missing English example or reference: '+r['id'])
        for rid in article['readingIds']:
            rec=corpus['senses'].get(rid)
            if rec:
                for ck in rec['citations']:
                    ref=citation(rec,corpus['contexts'][ck]).strip(' .')
                    require(ref in r['source'],'Lost original attestation: '+rid)
    first_word=next(r for r in rows if r['section'].startswith('headwords-'))
    first_word_page=row_pages[first_word['id']]
    selected={1,bounds['directory'][0],first_word_page,row_pages['sense-'+pointer('draw@kloj')],
              row_pages['sense-'+pointer('adopt_practice@tavr')],len(index)*2-1}
    selected.update(place_pages[w] for w in ('fōlem','änimu\u0307s','mesidäl','jensis nōrum'))
    for prefix in ('forms-',):
        start=next(v[0] for k,v in bounds.items() if k.startswith(prefix))
        selected.add(start)
    sample_draw=[r['source'] for r in rows if r['id'].startswith('usage-') and r['text'].startswith('kloj. ')]
    require(all(any(ref in s for s in sample_draw) for ref in ('John 4:7','Exodus 20:21','Matthew 26:51')),
            'Attested senses of draw collapsed')
    out=STAGE/'proofs'
    out.mkdir(parents=True,exist_ok=True)
    # Retain the Qt application while the FileSession and all images are alive.
    app=QApplication.instance() or QApplication([])
    session=FileSession(ROOT,source_fonts=False,recovery=False)
    session.remember=lambda *args:None
    session.log.emit=lambda *args,**kwargs:None
    try:
        print('Opening complete dictionary through FileSession',flush=True)
        session.open(target,advance_revision=False)
        state=session.state
        require(session.saved_page_mode=='two','Saved preview does not reopen as a spread')
        require(len(state['pages'])==2*len(index)==pub['pages'],'Native page count mismatch')
        order=check_native_order(state['pages'],index,by_id)
        dataset=language.dataset(state['language'])
        entries=[e for e in dataset['lexicon'] if e['id'].startswith('native.dictionary.')]
        heads=[e['headword'] for e in entries]
        require(heads==sorted(heads,key=collate),'Embedded dictionary headwords out of sequence')
        embedded={s['id']:s['definition'] for e in entries for s in e['senses']}
        expected={'dictionary.'+r['id']:r['text'].partition('. ')[2]+'\n'+r['gloss']+'\n'+r['source']
                  for r in rows if r['id'].startswith(('sense-','usage-','written-'))}
        require(embedded==expected,'Language Forge differs from the pages')
        from PIL import Image
        for a in sorted(selected):
            filenames=[]
            for no in (a,a+1):
                p=state['pages'][no-1]
                for field,frame in zip(FIELDS[2*((no-1)%2):],sorted(p['frames'],key=lambda f:int(f['x']))):
                    require(texts(frame)==[by_id[u][field] for u in index[(no-1)//2]['ids']],
                            'Reopened column text differs on p. '+str(no))
                qimage,_=pages.render(session,page_id=p['pageId'],mode='mono',dpi=80,page_mode='two',reading=True)
                f=out/f'p{no}.png'
                require(qimage.save(str(f),'PNG'),'Proof raster could not be written')
                filenames.append(f)
            halves=[Image.open(f).convert('RGB') for f in filenames]
            montage=Image.new('RGB',(sum(im.width for im in halves)+10,max(im.height for im in halves)),'#d0d0d0')
            montage.paste(halves[0],(0,0));montage.paste(halves[1],(halves[0].width+10,0))
            montage.save(out/f'spread-{a}.png')
        result=dict(exampleSentencesVerified=len(articles),sentenceInitialsVerified=len(articles),
                    repeatedNameMaskedSiblingExamples=0,repeatedNameMaskedNativeExamples=0,sourceReferencesVerified=True,nativeSha256=pub['sha256'],pages=pub['pages'],openedInFileSession=True,
                    allNativeDefinitionsInForge=len(embedded),embeddedDictionaryHeadwords=len(entries),
                    headwordsWithMultipleReadings=sum(len(e['senses'])>1 for e in entries),
                    lexicalHeadwordsWithMultipleKeyedReadings=sum(v>1 for v in distribution.values()),
                    lexicalWrittenFormsVerified=len(finder),corpusWrittenForms=len(spellings),
                    excludedNumericalSpellings=len(spellings-eligible-citation_forms-set(pub['excludedNonwordSpellings'])),
                    excludedNumericalReadings=len(corpus['senses'].keys()-included-citation_ids-set(pub['excludedNonwordReadings'])),
                    excludedCitationReadings=sorted(citation_ids),excludedCitationSpellings=sorted(citation_forms),
                    thimforaChartSha256=sha(ROOT/'Inputs/Origins_2_Thimfora_2.jpg'),
                    savedAlphabeticalOrder=order,
                    untaChartSha256=sha(ROOT/'Inputs/Origins_3_Unta_2.jpg'),
                    verifiedPlaceCombinations=len(published_slots),placeWordPages=place_pages,
                    firstHeadword=first_word['reference'],firstHeadwordPage=first_word_page,
                    directoryRangesVerified=len(actual),attestedKeysVerified=len(corpus['senses'].keys() & included),renderedSpreads=sorted(selected))
        if batch:
            result['referenceBookSensesVerified']=len(batch['entries'])
            result['existingThesaurusWitnessesReconciled']=len(batch['existingThesaurusReadings'])
        write_atomic(WORK/'verification.json',result)
        print(result,flush=True)
    finally:
        session.finish()


if __name__=='__main__':
    verify()
