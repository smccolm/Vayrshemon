"""Embed the dictionary's native lookup entries in the book's Language Forge."""
from collections import defaultdict

from tools.dictionary_corpus import ROOT, WORK, normalize, read, sha
from tools.dictionary_lexicon import load_gzip
from tools.dictionary_rows import collate, pointer
from vayrshemon.archive_language import base


def forge_data(rows):
    corpus=load_gzip(WORK/'attestations.json.gz')
    pin=next((ROOT/'Saves').glob('A New Voyage*/Working/snapshot.json'))
    data=read(pin)['snapshot']['language']
    required={k for s in data['corpus'] for t in s['tokens'] for k in t['entryIds']}
    required.update(k for rule in data['morphology'] for k in rule['entryIds'])
    data['lexicon']=[e for e in data['lexicon'] if e['id'] in required]
    ledger=WORK/'dictionary-rows.json.gz'
    source='dictionary.native.readings'
    data['sources'].append(dict(base(source,'Vayrshemon Dictionary',None,''),kind='other',
        path=ledger.relative_to(ROOT).as_posix(),sha256=sha(ledger)))
    by_row={'sense-'+pointer(key):s for key,s in corpus['senses'].items()}
    entries={}
    for r in rows:
        section=r['section']
        if not section.startswith(('headwords-','manuscript-')):continue
        head,sep,native=r['text'].partition('. ')
        if not sep:raise ValueError(r['id'])
        normalized=normalize(head)
        rec=by_row.get(r['id'],{})
        citation=dict(sourceId=source,locator=r['id'])
        if normalized not in entries:
            eid='native.dictionary.'+pointer(normalized)
            entry=dict(base(eid,r['reference'],source,r['id'],status=r.get('evidenceStatus','attested')),headword=head,
                       orthographyId='thimfora-79',pronunciation=r['reference'],ipa='',
                       partOfSpeech=r.get('partOfSpeech',rec.get('pos','')),senses=[],variants=[],etymology='',
                       exampleIds=[],audioLinks=[])
            entries[normalized]=entry
        entries[normalized]['senses'].append(dict(id='dictionary.'+r['id'],
            definition=native+'\n'+r['gloss']+'\n'+r['source'],status=r.get('evidenceStatus','attested'),citations=[citation]))
    data['lexicon'].extend(entries[head] for head in sorted(entries,key=collate))
    return data
