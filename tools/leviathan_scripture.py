"""Link Hobbes's explicit chapter-and-verse citations to the sealed four-column KJV."""
from hashlib import sha256
from collections import defaultdict
import json
import re

from tools.leviathan_source import WORK, ROOT


LEDGER = ROOT / 'Saves/KJV Bible v0.10-kjv.285/complete-translation-ledger.json'
SHA = '31d014091323420b444eaad3a15384917ad5bffc5f33e697d4330168f7126844'
SHORT = {
    'Genesis':'Gen Genes', 'Exodus':'Exod Exo', 'Leviticus':'Levit Lev', 'Numbers':'Numb Num',
    'Deuteronomy':'Deut', 'Joshua':'Josh', 'Judges':'Judg', 'Nehemiah':'Neh',
    'Psalms':'Psal Psalm Ps', 'Proverbs':'Prov', 'Ecclesiastes':'Eccles', 'Isaiah':'Isa Esay',
    'Jeremiah':'Jer Jerem', 'Ezekiel':'Ezek', 'Daniel':'Dan', 'Zechariah':'Zach Zech',
    'Matthew':'Mat Matth Math Matt', 'Mark':'Marke Mar', 'Luke':'Luk', 'John':'Joh',
    'Acts':'Act', 'Romans':'Rom', 'Galatians':'Gal', 'Ephesians':'Ephes Eph',
    'Philippians':'Philipp', 'Colossians':'Coll Col', 'Titus':'Tit', 'Hebrews':'Heb',
    'Revelation':'Rev Apocalypse',
    'Samuel':'Sam', 'Kings':'King', 'Chronicles':'Chron Chro', 'Corinthians':'Cor Corinth',
    'Thessalonians':'Thess Thessal', 'Timothy':'Tim', 'Peter':'Pet',
}

WORD = re.compile(r"[^\W_]+(?:[’'][^\W_]+)*", re.UNICODE)


def shared_wording(rows, bible):
    """Find verbatim runs, preserving spelling and distinguishing parallel verses."""
    length = 9
    index = defaultdict(list)
    passages = {}
    for row in rows:
        if row['kind'] != 'prose':
            continue
        tokens = list(WORD.finditer(row['text']))
        words = [m[0].casefold().replace('’', "'") for m in tokens]
        passages[row['id']] = (row['text'], tokens, words)
        for i in range(len(words)-length+1):
            index[tuple(words[i:i+length])].append((row['id'], i))
    matches = defaultdict(list)
    for ref, verse in bible.items():
        tokens = list(WORD.finditer(verse['source']))
        words = [m[0].casefold().replace('’', "'") for m in tokens]
        for j in range(len(words)-length+1):
            for block, i in index.get(tuple(words[j:j+length]), ()):
                _, ht, hw = passages[block]
                if i and j and hw[i-1] == words[j-1]:
                    continue  # One maximal match per pair of locations.
                size = length
                while i+size < len(hw) and j+size < len(words) and hw[i+size] == words[j+size]:
                    size += 1
                matches[block, ht[i].start(), ht[i+size-1].end()].append(dict(
                    reference=ref, verseStart=tokens[j].start(), verseEnd=tokens[j+size-1].end()))
    result = []
    for (block, start, end), references in matches.items():
        original = passages[block][0]
        result.append(dict(block=block, start=start, end=end, printed=original[start:end],
                           parallelReadings=references))
    order = {r['id']: i for i,r in enumerate(rows)}
    return sorted(result,key=lambda entry:(order[entry['block']],entry['start'],-entry['end']))


def citations():
    raw = LEDGER.read_bytes()
    assert sha256(raw).hexdigest() == SHA
    bible = {u['reference']:u for u in json.loads(raw)['units']}
    books = sorted({v.rsplit(' ',1)[0] for v in bible})
    variants = {}
    for book in books:
        n, _, name = book.rpartition(' ')
        if not n.isdigit():
            name, n = book, ''
        for label in [name, *SHORT.get(name,'').split()]:
            variants[(n,label.lower())] = book
    labels = sorted({v[1] for v in variants}, key=len, reverse=True)
    names = '|'.join(re.escape(l) for l in labels)
    pattern = re.compile(rf'(?<!\w)(?:([123]|III|II|I)\s*\.?\s*(?:Epist\.?\s+to\s+)?)?({names})[.,]?\s*(\d+)\s*[.,:]\s*(?:v\.\s*)?(\d+)\b',re.I)
    rows = json.loads((WORK/'english-blocks.json').read_bytes())['rows']
    matches, unresolved, sources = [], [], {}
    for row in rows:
        if row['kind'] not in ('prose', 'marginal heading'):
            continue
        for m in pattern.finditer(row['text']):
            n = (m[1] or '').upper()
            book = variants.get(({'I':'1','II':'2','III':'3'}.get(n,n),m[2].lower()))
            if m[1] and not book:
                # The preceding number can be the end of a different citation.
                book = variants.get(('',m[2].lower()))
                start = m.start(2)
            else:
                start = m.start()
            locator = dict(block=row['id'], section=row['section'], start=start, end=m.end(),
                           printed=row['text'][start:m.end()])
            ref = f'{book} {int(m[3])}:{int(m[4])}' if book else None
            if ref not in bible:
                unresolved.append(locator)
                continue
            matches.append(dict(locator, reference=ref))
            if ref not in sources:
                verse=bible[ref]
                sources[ref]={k:verse[k] for k in ('source','analysis','text','gloss')}
    verbal_matches = shared_wording(rows, bible)
    for match in verbal_matches:
        for parallel in match['parallelReadings']:
            ref = parallel['reference']
            verse = bible[ref]
            sources.setdefault(ref, {k:verse[k] for k in ('source','analysis','text','gloss')})
    data=dict(kjvLedgerSha256=SHA,
              scope='Explicit book, chapter and first verse printed together in prose or marginal headings. Following verses, chapter-only references and allusions require editorial lookup.',
              wordingScope='Shared runs of at least nine consecutive words. Case, punctuation, and apostrophe style are normalized. Parallel references are retained for comparison.',
              matches=matches, sharedWording=verbal_matches, ambiguousOrUnmatched=unresolved, verses=sources)
    (WORK/'scripture-concordance.json').write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
    return len(matches), len({m['reference'] for m in matches}), len(unresolved), len(verbal_matches)


if __name__ == '__main__':
    print('Explicit citations, distinct cited verses, unmatched citations, shared word sequences:', *citations())
