"""Reconstruct the two native editions and check the source and editorial decisions."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.compose_historical_book import texts
from tools.kjv_archive import load_register,parse_source,read,verify_seal
from tools.kjv_native_vocabulary import COMPACT,CONTEXT,OUT,PACKAGE,RECORD,VERSION,prior
from tools.m0.common import file_hash,write_json
from vayrshemon.native_storage import unpack
from vayrshemon.print_edition import text_of

def verse_hash(rows):
    h=sha256()
    for row in rows:h.update((json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf8'))
    return h.hexdigest()

def main():
    for folder in (prior.OUT,prior.COMPACT):verify_seal(folder)
    lang,manifest=load_register(VERSION);old,_=load_register(prior.VERSION)
    source=parse_source(ROOT/'Inputs/Sources/The King James Bible.txt')
    assert source==read(ROOT/'Saves/KJV Archive v0.10-kjv.1/source-index.json')
    units=read(OUT/'complete-translation-ledger.json')['units']
    parents=read(prior.OUT/'complete-translation-ledger.json')['units']
    records={r['id']:r for r in read(OUT/'correction-ledger.json')}
    review=read(PACKAGE/'vocabulary-review.json')['entries']
    quantities=read(PACKAGE/'quantities.json')
    approved_names=read(PACKAGE/'name-forms.json')
    assert quantities==read(prior.PACKAGE/'quantities.json')
    for k,e in old.lexicon.items():
        assert lang.lexicon[k]['semanticId']==e['semanticId'],k
        if k in quantities or k in approved_names:assert lang.lexicon[k]==e,k
        if k in review:
            assert review[k]['before']==e['form'] and review[k]['after']==lang.lexicon[k]['form']
        else:assert lang.lexicon[k]==e,k
    changed=set();contexts=set();refs={};quantity_count=0
    for original,base,unit in zip((v for b in source['books'] for v in b['verses']),parents,units,strict=True):
        assert all(unit[k]==value for k,value in original.items()),unit['reference']
        assert base['id']==unit['id'] and base['backReading']==unit['backReading']
        new=lang.compile(unit['analysis'])
        assert all(new[k]==unit[k] for k in ('text','keys','gloss')),unit['reference']
        if unit['analysis']!=base['analysis']:
            contexts.add(unit['reference']);before,after=CONTEXT[unit['reference']]
            assert base['analysis'].replace(before,after)==unit['analysis']
        if unit['text']!=base['text'] or unit['gloss']!=base['gloss'] or unit['analysis']!=base['analysis']:
            changed.add(unit['id']);rec=records[unit['id']]
            assert (rec['parentText'],rec['text'])==(base['text'],unit['text'])
        assert [k for k in unit['keys'] if k in quantities]==[k for k in base['keys'] if k in quantities]
        quantity_count+=sum(k in quantities for k in unit['keys'])
        refs[unit['reference']]=unit
        assert 'endin' not in unit['text'].casefold()
    assert changed==set(records) and contexts==set(CONTEXT)
    omega=[u for u in units if 'kjv_omega_letter_revelation' in u['keys']]
    assert [r['reference'] for r in omega]==['Revelation 1:8','Revelation 1:11','Revelation 21:6','Revelation 22:13']
    for u in omega:
        roman=lang.reading(u['text'])
        assert 'neksus’t īvden' in roman and 'hüŧh’na īvden' in roman
    assert 'venik’t' in lang.reading(refs['Genesis 1:13']['text'])
    assert 'former' in refs['Genesis 31:29']['keys'] and 'continue' in refs['Judges 14:17']['keys']
    assert 'cut' in refs['Isaiah 14:8']['keys'] and 'kjv_church_assembly' in refs['Revelation 22:16']['keys']
    assert all('yeshūa' in lang.reading(u['text']).casefold() for u in units if 'kjv_jesus_matthew' in u['keys'])
    snap=read(OUT/'current-snapshot.json')
    fixtures={t['id'].removeprefix('kjv285.verse.'):t['paragraphs'][0] for t in snap['snapshot']['tests'] if t['id'].startswith('kjv285.verse.')}
    assert len(fixtures)==len(units)==31102 and manifest['forgeHead']==snap['head']
    assert all(fixtures[u['id']]['text']==u['text'] and fixtures[u['id']]['translation']==u['source'] for u in units)
    assert not any('endin' in e['headword'].casefold() for e in snap['snapshot']['language']['lexicon'])
    del snap,fixtures
    compact_path=next(COMPACT.glob('*.vay'))
    compact=unpack(read(compact_path))['state'];previous=unpack(read(next(prior.COMPACT.glob('*.vay'))))['state']
    for k in ('assets','typography','layoutVersion'):assert compact['printEdition'][k]==previous['printEdition'][k],k
    for k in ('paint','recipe','pageNumbering'):assert compact[k]==previous[k],k
    assert compact['printEdition']['ledgerSha256']==file_hash(OUT/'complete-translation-ledger.json')
    pages={p['pageId']:text_of(p) for p in compact['pages']}
    for i,p in enumerate(compact['pages']):
        model=0 if i==0 else (1 if i%2 else 2)
        assert p['margins']==previous['pages'][model]['margins']
    compact_rows=[(row['id'],''.join(pages[f['pageId']][f['start']:f['end']] for f in row['fragments'])) for row in compact['printEdition']['verses']]
    assert compact_rows==[(u['id'],u['text']) for u in units]
    compact_count=len(compact['pages']);del compact,previous,pages
    study_path=OUT/'KJV Bible.vay';state=unpack(read(study_path))['state']
    by_id={u['id']:u for u in units};study_rows=[]
    idx=read(OUT/'page-index.json')['spreads']
    assert len(idx)*2==len(state['pages'])
    for i,spread in enumerate(idx):
        assert (spread['leftPage'],spread['rightPage'])==(2*i+1,2*i+2)
        columns=[texts(f) for p in state['pages'][2*i:2*i+2] for f in sorted(p['frames'],key=lambda f:int(f['x'])) if f['name']!='Book title']
        assert columns==[[by_id[k][field] for k in spread['unitIds']] for field in ('text','text','gloss','source')]
        study_rows.extend(zip(spread['unitIds'],columns[0],strict=True))
    assert study_rows==compact_rows
    folios=read(OUT/'numbering-validation.json')
    assert [(r['pageNumber'],r['pageId'],r['pageMode'],r['status']) for r in folios]==[(i,p['pageId'],m,'placed') for i,p in enumerate(state['pages'],1) for m in ('one','two')]
    report=read(OUT/'combined-validation.json');pr=read(COMPACT/'edition-manifest.json')
    assert report['sha256']==file_hash(study_path) and pr['sha256']==file_hash(compact_path)
    assert pr['saveReopenIdentical'] and report['saveReopenIdentical'] and report['geometryAndPaintPreserved']
    receipt=dict(version=VERSION,head=manifest['forgeHead'],verses=31102,books=66,compactStudyVersePairsCompared=len(study_rows),mismatchedVerseTexts=0,
        studyNativeVerseTextSha256=verse_hash(study_rows),compactNativeVerseTextSha256=verse_hash(compact_rows),
        progressiveSha256=report['sha256'],compactSha256=pr['sha256'],progressivePages=len(state['pages']),compactPages=compact_count,duplexSheets=compact_count//2,
        progressiveFolioPlacements=len(folios),revisedVerses=len(changed),reviewedDictionaryChanges=len(review),contextCorrections=sorted(contexts),
        quantityOccurrences=quantity_count,distinctQuantities=len(quantities),sourceSha256=source['sourceSha256'],readingAndScriptExact=True,
        allFourColumnsMatchLedger=True,studyReopenedIdentically=True,compactReopenedIdentically=True,parentSealsVerified=True,
        checkedOmegaVerses=[dict(reference=u['reference'],source=u['source'],roman=lang.reading(u['text'])) for u in omega])
    write_json(RECORD/'delivery-validation.json',receipt)
    print({k:v for k,v in receipt.items() if k!='checkedOmegaVerses'},flush=True)

if __name__=='__main__':main()
