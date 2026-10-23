"""Immutable, content-addressed language revisions; no implicit text rewriting."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator
from .authoring import digest, identity, stamp
from .language_contracts import DATA, RECORDS, COLLECTIONS, PACKAGE, LANGUAGE
from .session import checked_text, scalar_offset, utf16_length


def empty_data(): return {key: [] for key in COLLECTIONS}
def text_hash(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()


def revision(state, revision_id=None):
    key = revision_id or state['activeRevisionId']
    value = next((r for r in state['revisions'] if r['id'] == key), None)
    if value is None: raise ValueError('LANGUAGE_REVISION_NOT_FOUND')
    return value


def dataset(state, revision_id=None):
    rev = revision(state, revision_id)
    return {key: [deepcopy(state['objects'][h]) for h in rev['collections'][key]] for key in COLLECTIONS}


def validate_data(data):
    Draft202012Validator(DATA).validate(data)
    ids = {}
    for key, records in data.items():
        ids[key] = {r['id'] for r in records}
        if len(ids[key]) != len(records): raise ValueError('DUPLICATE_LANGUAGE_RECORD: ' + key)
    senses = {s['id'] for r in data['lexicon'] for s in r['senses']}
    if len(senses) != sum(len(r['senses']) for r in data['lexicon']): raise ValueError('DUPLICATE_SENSE_ID')
    def reference(key, values):
        if not set(values) <= ids[key]: raise ValueError('LANGUAGE_REFERENCE_MISSING: ' + key)
    def citations(value):
        if isinstance(value, dict):
            if 'citations' in value: reference('sources', [c['sourceId'] for c in value['citations']])
            for child in value.values(): citations(child)
        elif isinstance(value, list):
            for child in value: citations(child)
        elif isinstance(value, str): checked_text(value)
    citations(data)
    for r in data['orthographies']:
        symbol_ids = [s['id'] for s in r['symbols']]
        scalars = [f['scalar'] for s in r['symbols'] for f in s['forms']]
        if len(symbol_ids) != len(set(symbol_ids)) or len(scalars) != len(set(scalars)): raise ValueError('ORTHOGRAPHY_AMBIGUOUS_SLOT')
    for key in ('inputLayouts', 'transliterations', 'lexicon', 'corpus'):
        for r in data[key]:
            if r['orthographyId']: reference('orthographies', [r['orthographyId']])
    for r in data['inputLayouts']:
        keys = [k['key'] for k in r['keys']]
        if len(keys) != len(set(keys)) or any(not k for k in keys): raise ValueError('INPUT_KEY_AMBIGUOUS')
    for r in data['transliterations']:
        sources = [m['source'] for m in r['mappings']]
        if len(sources) != len(set(sources)) or any(not m['source'] or not m['target'] for m in r['mappings']): raise ValueError('INVALID_TRANSLITERATION_MAPPING')
    for r in data['lexicon']:
        reference('corpus', r['exampleIds'])
        if any(not url.startswith(('https://', 'http://')) for url in r['audioLinks']): raise ValueError('AUDIO_LINK_MUST_BE_HTTP_URL')
    for r in data['morphology']: reference('lexicon', r['entryIds'])
    for r in data['grammar']:
        reference('morphology', r['morphologyIds']); reference('corpus', r['exampleIds'])
    for r in data['corpus']:
        end = 0
        for token in r['tokens']:
            if token['start'] < end or token['end'] <= token['start'] or token['end'] > len(r['text']): raise ValueError('CORPUS_TOKEN_RANGE')
            if r['text'][token['start']:token['end']] != token['surface']: raise ValueError('CORPUS_TOKEN_TEXT_MISMATCH')
            if len(token['morphemes']) != len(token['glosses']): raise ValueError('INTERLINEAR_SEGMENT_COUNT')
            reference('lexicon', token['entryIds']); reference('morphology', token['morphologyIds'])
            allowed_senses = {s['id'] for entry in data['lexicon'] if entry['id'] in token['entryIds'] for s in entry['senses']}
            if not set(token['senseIds']) <= allowed_senses: raise ValueError('CORPUS_SENSE_ENTRY_MISMATCH')
            end = token['end']
    for r in data['numberConventions']:
        alphabet = r['digits'] + [r[k] for k in ('radixPoint', 'minus', 'repeatOpen', 'repeatClose')]
        if len(r['digits']) != 12 or len(r['digitNames']) != 12 or any(len(c) != 1 for c in alphabet) or len(set(alphabet)) != 16:
            raise ValueError('NUMBER_ALPHABET_REQUIRES_DISTINCT_SCALARS')


def append_revision(state, data, label):
    validate_data(data)
    collections = {}
    for key in COLLECTIONS:
        collections[key] = []
        for r in sorted(data[key], key=lambda r: r['id']):
            h = digest(r); state['objects'][h] = deepcopy(r); collections[key].append(h)
    rev = dict(id=identity('language'), parentId=state.get('activeRevisionId'), label=label,
               createdAt=stamp(), sha256=digest(collections), collections=collections)
    state['revisions'].append(rev); state['activeRevisionId'] = rev['id']
    return deepcopy(rev)


def initial():
    state = dict(version='1.0.0', objects={}, revisions=[], links=[])
    append_revision(state, empty_data(), 'Unassigned language')
    return state


def validate_state(state):
    Draft202012Validator(LANGUAGE).validate(state)
    seen = set()
    for h, r in state['objects'].items():
        if digest(r) != h: raise ValueError('LANGUAGE_OBJECT_HASH_MISMATCH')
    for rev in state['revisions']:
        if rev['id'] in seen or (rev['parentId'] is not None and rev['parentId'] not in seen): raise ValueError('LANGUAGE_REVISION_GRAPH_INVALID')
        seen.add(rev['id'])
        if digest(rev['collections']) != rev['sha256']: raise ValueError('LANGUAGE_REVISION_HASH_MISMATCH')
        validate_data(dataset(state, rev['id']))
    revision(state)
    link_ids = set()
    for link in state['links']:
        if link['id'] in link_ids: raise ValueError('DUPLICATE_CORPUS_LINK')
        link_ids.add(link['id'])
        if link['corpusId'] not in {r['id'] for r in dataset(state, link['revisionId'])['corpus']}: raise ValueError('LINK_CORPUS_MISSING')
        for anchor in (link['source'], link['translation']):
            if anchor['end'] - anchor['start'] != utf16_length(anchor['text']): raise ValueError('LINK_RANGE_INVALID')


def diff(state, before, after):
    a, b = dataset(state, before), dataset(state, after)
    result = {}
    for key in COLLECTIONS:
        aa, bb = ({r['id']: r for r in records} for records in (a[key], b[key]))
        result[key] = dict(added=sorted(bb.keys()-aa.keys()), removed=sorted(aa.keys()-bb.keys()),
                           changed=[dict(id=i, before=aa[i], after=bb[i]) for i in sorted(aa.keys() & bb.keys()) if aa[i] != bb[i]])
    return dict(before=before, after=after, collections=result, rewritesDocumentText=False)


def find_record(data, collection, record_id):
    r = next((r for r in data[collection] if r['id'] == record_id), None)
    if r is None: raise ValueError('LANGUAGE_RECORD_NOT_FOUND: ' + record_id)
    return r


def tokens(text):
    # A transparent surface-token heuristic, never an asserted morpheme parser.
    return [dict(start=m.start(), end=m.end(), surface=m.group(), morphemes=[], glosses=[], entryIds=[], senseIds=[], morphologyIds=[], status='uncertain')
            for m in re.finditer(r'[^\s.,!?;:()\[\]{}]+', text)]


def transliterate(profile, text, reverse=False, trace=None):
    checked_text(text)
    if trace is not None:
        if trace.get('profileHash') != digest(profile) or trace.get('output') != text: raise ValueError('TRANSLITERATION_TRACE_MISMATCH')
        replay = transliterate(profile, trace['original'])
        if replay['trace'] != trace: raise ValueError('TRANSLITERATION_TRACE_INVALID')
        return dict(text=trace['original'], reversible=True, diagnostics=[], trace=None)
    pairs = profile['mappings']
    if reverse:
        targets = [m['target'] for m in pairs]
        # Prefix-free output is required for a provably unique untraced inverse.
        if len(targets) != len(set(targets)) or any(a != b and b.startswith(a) for a in targets for b in targets):
            raise ValueError('AMBIGUOUS_REVERSE_TRANSLITERATION: use the forward trace')
        pairs = [dict(source=m['target'], target=m['source']) for m in pairs]
    pairs = sorted(pairs, key=lambda m: -len(m['source']))
    output, diagnostics, i = [], ([dict(code='UNTRACED_REVERSE_NOT_PROVEN', note='Unknown source scalars may coincide with transliteration output. Use a forward trace for exact restoration.')] if reverse else []), 0
    while i < len(text):
        match = next((m for m in pairs if text.startswith(m['source'], i)), None)
        if match: output.append(match['target']); i += len(match['source'])
        else:
            output.append(text[i]); diagnostics.append(dict(offset=i, scalar=ord(text[i]), code='UNMAPPED_PRESERVED')); i += 1
    result = ''.join(output)
    return dict(text=result, reversible=not reverse, diagnostics=diagnostics,
                trace=dict(profileHash=digest(profile), original=text, output=result) if not reverse else None)


def number_value(numerator, denominator):
    for s in (numerator, denominator):
        if not re.fullmatch(r'-?[0-9]{1,256}', s): raise ValueError('EXACT_INTEGER_STRING_REQUIRED')
    if int(denominator) == 0: raise ValueError('ZERO_DENOMINATOR')
    return Fraction(int(numerator), int(denominator))


def number_format(convention, numerator, denominator='1', max_places=512):
    value = number_value(numerator, denominator); n, d = abs(value.numerator), value.denominator
    integer, rem = divmod(n, d); digits = convention['digits']; whole = []
    while integer: integer, digit = divmod(integer, 12); whole.append(digits[digit])
    whole = ''.join(reversed(whole)) or digits[0]
    seen, tail, repeat = {}, [], None
    while rem:
        if rem in seen: repeat = seen[rem]; break
        if len(tail) >= max_places: break
        seen[rem] = len(tail); digit, rem = divmod(rem*12, d); tail.append(digits[digit])
    fractional = ''.join(tail)
    if repeat is not None: fractional = fractional[:repeat]+convention['repeatOpen']+fractional[repeat:]+convention['repeatClose']
    display = (convention['minus'] if value < 0 else '') + whole + (convention['radixPoint']+fractional if tail else '')
    truncated = rem != 0 and repeat is None
    if truncated: display += '…'
    return dict(numerator=str(value.numerator), denominator=str(value.denominator), base=12, text=display,
                exact=not truncated, repeatingFrom=repeat, truncated=truncated, conventionId=convention['id'], conventionHash=digest(convention),
                digitReading=[convention['digitNames'][digits.index(c)] for c in whole+''.join(tail)],
                readingPolicy=convention['readingPolicy'], note='Digit names only; no unverified positional spoken grammar is inferred.')


def number_parse(convention, text):
    if len(text) > 2048: raise ValueError('NUMBER_TOO_LONG')
    chars = {c: str(i) for i, c in enumerate(convention['digits'])}
    sign = -1 if text.startswith(convention['minus']) else 1
    if sign < 0: text = text[1:]
    parts = text.split(convention['radixPoint'])
    if len(parts) > 2 or not parts[0]: raise ValueError('INVALID_BASE12_NUMBER')
    tail = parts[1] if len(parts) == 2 else ''
    repeat = ''
    if convention['repeatOpen'] in tail:
        tail, repeat = tail.split(convention['repeatOpen'], 1)
        if not repeat.endswith(convention['repeatClose']) or len(repeat) < 2: raise ValueError('INVALID_REPETEND')
        repeat = repeat[:-1]
    def integer(s):
        v = 0
        for c in s:
            if c not in chars: raise ValueError('INVALID_BASE12_DIGIT')
            v = v*12+int(chars[c])
        return v
    if len(parts) == 2 and not tail and not repeat: raise ValueError('EMPTY_FRACTION')
    value = Fraction(integer(parts[0])) + Fraction(integer(tail), 12**len(tail))
    if repeat: value += Fraction(integer(repeat), (12**len(repeat)-1)*12**len(tail))
    value *= sign
    return dict(numerator=str(value.numerator), denominator=str(value.denominator), base=12, exact=True)


def anchor(session, frame_id, start, end):
    if session.source_for(frame_id)!=frame_id: raise ValueError('FLOW_TARGET_RANGE: link the source story')
    session.locate(frame_id); frame = session.frames[frame_id]; text = frame.text()
    frame.range_cursor(start, end)  # Enforce native grapheme boundaries too.
    if end <= start: raise ValueError('EMPTY_CORPUS_LINK')
    return dict(frameId=frame_id, start=start, end=end, text=text[scalar_offset(text, start):scalar_offset(text, end)], frameSha256=text_hash(text))


def inspect_links(session):
    result = []
    for link in session.state['language']['links']:
        issues = []
        for role in ('source', 'translation'):
            a = link[role]; f = session.frames.get(a['frameId'])
            if f is None: issues.append(role.upper()+'_FRAME_MISSING')
            elif text_hash(f.text()) != a['frameSha256']: issues.append(role.upper()+'_TEXT_CHANGED')
        result.append(dict(link, valid=not issues, diagnostics=issues, usesActiveRevision=link['revisionId'] == session.state['language']['activeRevisionId']))
    return result


def search(data, query='', entry_id=None, limit=200):
    hits = []; frequencies = Counter(); total = 0
    for r in data['corpus']:
        for t in tokens(r['text']): frequencies[t['surface']] += 1
        if entry_id:
            ranges = [(t['start'], t['end']) for t in r['tokens'] if entry_id in t['entryIds']]
        elif query:
            ranges = []; start = 0
            while (start := r['text'].find(query, start)) >= 0:
                ranges.append((start, start+len(query))); start += max(1, len(query))
        else: ranges = [(0, len(r['text']))]
        for start, end in ranges:
            total += 1
            if len(hits) < limit: hits.append(dict(corpusId=r['id'], start=start, end=end, before=r['text'][max(0,start-40):start], match=r['text'][start:end], after=r['text'][end:end+40], translation=r['translation'], status=r['status']))
    return dict(hits=hits, total=total, truncated=total>limit, offsetUnit='unicode-scalar', caseSensitive=True,
                frequencies=[dict(text=t, count=n) for t,n in frequencies.most_common(limit)], tokenizer='surface-v1: whitespace and selected punctuation; no morphological inference')


def export_package(data, label):
    return dict(format='vayrshemon.language', formatVersion='1.0.0', label=label, sha256=digest(data), data=deepcopy(data))


def read_package(path):
    path = Path(path)
    if path.stat().st_size > 6*1024*1024: raise ValueError('LANGUAGE_PACKAGE_TOO_LARGE')
    payload = json.loads(path.read_text(encoding='utf-8-sig'))
    Draft202012Validator(PACKAGE).validate(payload)
    if digest(payload['data']) != payload['sha256']: raise ValueError('LANGUAGE_PACKAGE_HASH_MISMATCH')
    validate_data(payload['data'])
    return payload
