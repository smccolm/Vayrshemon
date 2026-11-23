"""Resolve editorial sense distinctions to passages in the current manuscripts."""
from collections import defaultdict
from tools.dictionary_lexicon import WORK,read,ledger_sources
from tools.dictionary_corpus import normalize

def sense_divisions(corpus,definer):
    pending=defaultdict(list)
    for line in (WORK/'sense-divisions.txt').read_text(encoding='utf8').splitlines():
        if not line or line.startswith('#'):continue
        key,ref,analysis,english=line.split(' | ')
        native,gloss=definer.phrase(analysis)
        pending[ref].append((key,native,gloss,english))
    found=defaultdict(list)
    for path,title,current in ledger_sources():
        if not current:continue
        for unit in read(path).get('units',[]):
            ref=unit.get('reference',unit.get('id'))
            if ref not in pending:continue
            for key,n,g,en in pending[ref][:]:
                if key not in unit.get('keys',[]):continue
                candidates=[s for s in definer.keyrefs[key] if s['contemporary'] and normalize(s['form']) in normalize(unit['text'])]
                if len(candidates)!=1:raise ValueError(f'Ambiguous native sense at {ref}: {key}')
                s=candidates[0];identity=key+'@'+normalize(s['form'])
                cite=ref if title=='King James Bible' or ref.startswith(title) else f'{title}, {ref}'
                found[identity].append((n,g,en,cite))
                pending[ref].remove((key,n,g,en))
            if not pending[ref]:del pending[ref]
    if pending:raise ValueError(f'Unmatched sense citations: {list(pending)}')
    return found
