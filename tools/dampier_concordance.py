"""Publish the source and page concordance accompanying Dampier's passage restoration."""
import base64
from collections import defaultdict
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import quote

from tools.dampier_concordance_inventory import original_sentence_inventory, sentences
from tools.dampier_concordance_pages import load_locations
from tools.dampier_working import BOOK, EDITION, ROOT, SOURCE, SOURCE_HASH, TITLE, WORK, source_language
from tools.editorial_language import TOKEN, WORD
from tools.unta_language import quantity


PRINT = BOOK.parent / (TITLE + ' - Letter Print Edition')
PDF = PRINT / (TITLE + ' - Duplex Print.pdf')
REPORT = BOOK / 'Passage concordance.html'
OLD = BOOK.parent / 'Archive/Previous editions/Before Dampier passage restoration' / EDITION / 'Working'
HEADINGS = {
    'L275.S8': 'Could they reach the people in question?',
    'L275.S10': 'The lookouts the Spaniards kept',
    'L275.S11': 'A question about the guard',
    'L275.S14': 'Comparing prisoners’ accounts and looking for a guide',
    'L299.S8': 'The size of the harpoon staff',
    'L299.S9': 'The bobwood float and its line',
    'L299.S10': 'The line held in the hand',
    'L305.S2': 'What happens when the tortoise is struck',
    'L319.S6': 'Dampier’s account of the blowpipes',
    'L319.S7': 'The darts and the difficulty of removing them',
    'L447.S4': 'The islander’s ironwork',
    'L461.S10': 'The fatal blow to a seal',
    'L745.S1': 'A suspected attempt to burn the ship',
    'L749.S4': 'Dampier’s criticism of the gun platforms',
    'L959.S3': 'Captain Swan’s order and the search for provisions',
    'L1359.S2': 'The heat, the insects and the threatened killing',
    'L1391.S2': 'The servant’s repeated submersion',
    'L1837.S6': 'The shape and hardening of the lance',
    'L2067.S10': 'What the French ships might have done',
    'L2161.S4': 'Captain Monday’s arrival near the fort',
}


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def overlap(a, b, c, d):
    return a < d and c < b


def table(headers, rows, cls=''):
    head = ''.join(f'<th scope="col">{escape(s)}</th>' for s in headers)
    return (f'<div class="scroll"><table class="{cls}"><thead><tr>{head}</tr></thead>'
            '<tbody>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>' for row in rows)
            + '</tbody></table></div>')


def page_list(numbers, pdf=False):
    pages = sorted(set(n for n in numbers if n is not None))
    href = '../' + quote(PRINT.name) + '/' + quote(PDF.name)
    return ', '.join(f'<a href="{href}#page={n}">{n}</a>' if pdf else str(n) for n in pages)


def native_forms(notes, published_units, lang, numerals):
    """Match authoring keys in a note to words actually used in the enclosing native text."""
    emitted = {}
    for u in published_units:
        for t in TOKEN.findall(u['analysis']):
            if not WORD.fullmatch(t):
                continue
            key = t.rstrip(':')
            if key in numerals:
                label, reading = numerals[key]
                emitted[label] = emitted[key] = reading
                continue
            try:
                form, _, _ = lang.word(key)
            except ValueError:
                continue
            for version in {key, key.replace('drama_native_', '')}:
                emitted[version] = lang.reading(form)
            if '/' in key:
                owner = key.split('/')[0]
                if owner in lang.possessors:
                    emitted[owner+'/'] = lang.reading(lang.word(lang.possessors[owner])[0]) + '’'
            for feature in key.split('/')[-1].split(':')[1:]:
                if feature in lang.suffix:
                    emitted[':'+feature] = '–' + lang.reading(lang.suffix[feature][0])
                elif feature in lang.prefix:
                    emitted[':'+feature] = lang.reading(lang.prefix[feature][0]) + '–'
    out = []
    for note in notes:
        # Prose after an em dash, semicolon or full stop often describes a grammatical choice.
        # Only a named form attested in these actual pages counts as a match.
        bracket = re.search(r'\[([^\[\]]+)\]', note)
        lead = bracket[1] if bracket is not None else re.split(
            r'[—;.,]|\s+(?:(?:on|in|at|within) the\b|(?:and|plus) the following\b|expresses\b)',
            note, maxsplit=1)[0]
        if lead.startswith('∅') or len(lead.split()) > 10:
            out.append('')
            continue
        candidates = re.findall(r'[#@][0-9]+o?|:[A-Za-z_]+|[A-Za-z_]+(?:[/:+][A-Za-z_]+)*/?', lead)
        matched = []
        for t in candidates:
            if t not in emitted:
                break
            matched.append(emitted[t])
        out.append(' · '.join(matched))
    return out


def safe_excerpt(line, sentence, marks):
    a, b = sentence['start'], sentence['end']
    out = []
    cursor = a
    for m in marks:
        left, right = max(a, m['start']), min(b, m['end'])
        out.extend((escape(line[cursor:left]), f'<mark>{escape(m["replacement"])}</mark>'))
        cursor = right
    out.append(escape(line[cursor:b]))
    return ''.join(out)


def page_row(chapter, sid, marks, locations):
    ids = sorted({m['live'] for m in marks})
    return [f'<a href="#{sid}">{escape(chapter)} · {sid}</a>', escape(HEADINGS[sid]),
            page_list(x for uid in ids for x in locations[uid]['progressive']),
            page_list(x for m in marks for x in m['locator']['printNative']),
            page_list(x for m in marks for x in m['locator']['printFolios']),
            page_list((x for m in marks for x in m['locator']['pdfPhysical']), True)]


def report():
    ledger = read(WORK / 'ledger.json')
    notes = read(WORK / 'passage-concordance-notes.json')
    original = {u['id']: u for u in read(OLD / 'ledger.json')['units']}
    former = {uid: original[uid] for uid in notes['final']}
    assert set(former) == {uid for uid, u in original.items() if u.get('sourceTreatment')}
    assert SOURCE_HASH == digest(SOURCE) == notes['sourceSha256'] == ledger['sourceSha256']
    withheld = notes['withheldPositions']
    assert ledger['sourceWords'] == ledger['translatedSourceWords'] + ledger['sourceWordsInSummaryPassages']
    lines = SOURCE.read_text(encoding='utf-8-sig').splitlines()
    treatments = read(WORK / 'source-treatments.json')
    loc = load_locations(ledger, WORK / 'page-index.json', PRINT / (TITLE + '.vay'))
    lang, _, _ = source_language()
    numerals = {}
    for r in read(WORK / 'unta-readings.json'):
        if r['key'] not in numerals:
            q = quantity(r['value'], r['kind'], notation=r['notation'])
            label = ('#' if r['notation']=='digits' else '@')+str(r['value'])+('o' if r['kind']=='ordinal' else '')
            numerals[r['key']] = (label,lang.reading(q['spokenForm']))
    by_line = defaultdict(list)
    for unit in ledger['units']:
        by_line[unit['sourceLine']].append(unit)
    replacements = defaultdict(list)
    for uid, u in former.items():
        line = u['sourceLine']
        offset = u['sourceOffsets'][0]
        for m in notes['final'][uid]:
            a, b = offset + m['start'], offset + m['end']
            live, = [x for x in by_line[line] if x['sourceOffsets'][0] <= a and b <= x['sourceOffsets'][1]]
            lid = live['id']
            j, = [i for i, t in enumerate(treatments[lid]['spans'])
                  if t['start'] + live['sourceOffsets'][0] == a and t['end'] + live['sourceOffsets'][0] == b
                  and t['replacement'] == m['replacement']]
            seen, = [r for r in notes['spanReviews'][uid] if (r['start'],r['end']) == (m['start'],m['end'])]
            assert len(treatments[lid]['spans']) == len(loc[lid]['brackets'])
            locator = loc[lid]['brackets'][j]
            start_native, end_native = locator['range']
            roman = lang.reading(live['text'][start_native + 1:end_native - 1].strip())
            replacements[line].append(dict(start=a, end=b, live=lid, old=uid, replacement=m['replacement'],
                                            review=seen, locator=locator, roman=roman))
    for group in replacements.values():
        group.sort(key=lambda x: x['start'])
    detailed = []
    quick = []
    detailed_ids = set()
    row_count = word_count = substituted_count = hidden_count = 0
    bracket_keys = set()
    pdf_pages = set()
    for n, group in sorted(replacements.items()):
        line = lines[n-1]
        for s in sentences(n, line):
            marks = [m for m in group if overlap(m['start'], m['end'], s['start'], s['end'])]
            if not marks:
                continue
            sid = s['id']
            detailed_ids.add(sid)
            rows = notes['grammar'][sid]
            assert len(rows) == len(s['words'])
            related = [u for u in by_line[n] if overlap(*u['sourceOffsets'], s['start'], s['end'])]
            chapter = related[0]['chapter']
            scan = page_row(chapter, sid, marks, loc)
            quick.append(scan)
            explanations = []
            for m in marks:
                bracket_keys.add((m['live'], m['start']))
                pdf_pages.update(m['locator']['pdfPhysical'])
                positions = [w['n'] for w in s['words'] if overlap(w['start'], w['end'], m['start'], m['end'])]
                label = str(positions[0]) if len(positions) == 1 else f'{positions[0]}–{positions[-1]}'
                across = ' This one printed bracket spans a sentence boundary and appears in both entries here.' if (
                         m['start'] < s['start'] or m['end'] > s['end']) else ''
                loss = m['review']['loss']
                reason = m['review']['reason']
                word_label = 'Word' if len(positions) == 1 else 'Words'
                explanations.append(f'<li><b>{word_label} {label}</b> <mark>{escape(m["replacement"])}</mark> '
                                    + escape(reason) + ' ' + escape(loss) + escape(across)
                                    + f'<small class="reading">Printed Vayrshemon · {escape(m["roman"])}</small></li>')
            shown = []
            forms = native_forms([row[2] for row in rows], related, lang, numerals)
            for w, (pos, sense, target), roman in zip(s['words'], rows, forms, strict=True):
                masked = any(overlap(w['start'], w['end'], m['start'], m['end']) for m in marks)
                substituted_count += int(masked)
                surface = w['word']
                if w['n'] in withheld[sid]:
                    assert masked
                    hidden_count += 1
                    surface = '<span class="omitted">[in bracket]</span>'
                else:
                    surface = escape(surface)
                word_count += 1
                shown.append([str(w['n']),surface,escape(pos),escape(sense),escape(target)
                              + (f'<small class="reading">{escape(roman)}</small>' if roman else '')])
            containing = []
            for u in related:
                p = loc[u['id']]
                containing.append(f'<div class="unit"><p><b>{escape(u["reference"])}</b> · Four-column pp. '
                                  + page_list(p['progressive']) + ' · PDF pp. ' + page_list(p['pdfPhysical'], True)
                                  + f'</p><p class="native">{escape(u["text"])}</p><p class="roman">{escape(lang.reading(u["text"]))}</p>'
                                  + f'<p class="gloss">{escape(u["gloss"])}</p></div>')
            detailed.append(f'<section class="entry" id="{sid}"><div class="locator">{escape(chapter)} · Source line {n} · Sentence {sid.split(".S")[1]}</div>'
                            + f'<h2>{escape(HEADINGS[sid])}</h2><p>Brackets on four-column pp. {scan[2]}, print native pp. {scan[3]}, '
                            + f'printed folios {scan[4]}, PDF pp. {scan[5]}.</p><blockquote>{safe_excerpt(line,s,marks)}</blockquote>'
                            + '<ul class="explain">' + ''.join(explanations) + '</ul><details><summary>Native paragraphs containing this sentence</summary>'
                            + ''.join(containing) + '</details><details><summary>Word-by-word grammar · ' + str(len(rows))
                            + ' source words</summary>' + table(['No.','Source word','Part of speech','Sense and function',
                            'Native construction and reading'], shown, 'words') + '</details><a href="#affected">Back to page index</a></section>')
            row_count += 1
    assert detailed_ids == notes['grammar'].keys() == withheld.keys()
    assert word_count == sum(map(len,notes['grammar'].values()))
    assert substituted_count == ledger['sourceWordsInSummaryPassages']
    assert len(bracket_keys) == sum(len(r['spans']) for r in treatments.values())
    assert hidden_count == sum(map(len,withheld.values()))
    prev = []
    for uid, old in sorted(former.items()):
        for r in notes['review'].get(uid, []):
            a = old['sourceOffsets'][0] + r['start']
            b = old['sourceOffsets'][0] + r['end']
            n = old['sourceLine']
            chosen = [s['id'] for s in sentences(n,lines[n-1],inventory=True) if overlap(a,b,s['start'],s['end'])]
            prev.append([escape(old['chapter']),', '.join(f'<a href="#{s}">{s}</a>' if s in notes['grammar']
                         else f'<a href="#inventory-{s}">{s}</a>' for s in chosen),
                         escape(r['decision']),escape(r['reason']),escape(r['loss'])])
    assert len(prev) == sum(map(len,notes['previous'].values()))
    passages = []
    for uid, old in sorted(former.items()):
        n = old['sourceLine']
        a,b = old['sourceOffsets']
        original_words = len(lines[n-1][a:b].split())
        loss = sum(len(lines[n-1][a+r['start']:a+r['end']].split()) for r in notes['final'][uid])
        units = [u for u in by_line[n] if overlap(a,b,*u['sourceOffsets'])]
        pages = [loc[u['id']] for u in units]
        passages.append([escape(old['reference']),str(original_words),str(original_words-loss),str(loss),
                         page_list(n for p in pages for n in p['progressive']),page_list(n for p in pages for n in p['printNative']),
                         page_list((n for p in pages for n in p['pdfPhysical']), True)])
    decisions = read(WORK / 'passage-concordance-assessments.json')
    all_sentences, sentence_count = original_sentence_inventory(lines, former, notes['final'], by_line, loc, decisions)
    assert sentence_count == len(decisions)
    assert len(passages) == len(former)
    historical_words = sum(int(row[1]) for row in passages)
    historical_direct = sum(int(row[2]) for row in passages)
    assert historical_words - historical_direct == substituted_count
    remaining = sum(bool(v) for v in notes['final'].values())
    intermediate_words = sum(len(lines[original[k]['sourceLine']-1][original[k]['sourceOffsets'][0]+sp['start']:
                         original[k]['sourceOffsets'][0]+sp['end']].split())
                         for k,previous in notes['previous'].items() for sp in previous)
    compact = lambda pages: ', '.join(str(p) for p in sorted(set(pages)))
    families = [('native','Thimfora_79.ttf')]
    fonts = ''.join('@font-face{font-family:'+name+';src:url(data:font/ttf;base64,'
                    + base64.b64encode((ROOT/'data/runtime-fonts'/filename).read_bytes()).decode()
                    + ') format("truetype")}' for name,filename in families)
    parts = ['<!DOCTYPE html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>Dampier · Passage concordance</title><style>',fonts,STYLE,'</style><main><header><p class="locator">William Dampier · A New Voyage Round the World</p>',
             f'<h1>Passage concordance</h1><p class="lead">Of the {len(former)} passages previously summarized, {len(former)-remaining} are now translated in full. Across the other {remaining} passages, {len(bracket_keys)} brackets replace {substituted_count} words of Dampier’s English.</p></header>',
             f'<nav><a href="#affected">Affected pages</a><a href="#all">{len(former)} passages</a><a href="#sentences">All reviewed sentences</a><a href="#reviews">Earlier decisions</a></nav>',
             '<section id="affected"><h2>Pages with substitutions</h2><p>Both the English and the Vayrshemon mark each replacement with square brackets. Each row locates the replacement itself. Odd and even four-column pages form the facing spread. The print native count includes the front matter. The PDF has one additional binding blank at the front.</p>',
             table(['Sentence','Subject','Four-column pages','Print native pages','Printed folios','PDF pages'],quick),
             f'<p>The entries below give the published English reading and the reason for each change. Expand the grammar to see every original word position in order. The tables transcribe {word_count-hidden_count} of the {word_count} words individually, including {substituted_count-hidden_count} words inside replacements. The other {hidden_count} positions show <i>[in bracket]</i> with a grammatical analysis and an explanation of the loss. Counts follow whitespace in the supplied file, including the printed form <i>kill d</i>. A shared construction can account for several words. The symbol ∅ marks a word expressed through grammar or context.</p>',
             '<p>Native paragraphs give the script, roman reading and construction gloss from the edition. Word numbers follow the English. Vayrshemon word order can put a directly translated noun before its bracketed verb. The grammar table shows where each meaning appears. Italic readings identify forms attested in the enclosing paragraphs.</p></section>',
             *detailed,f'<section id="all"><h2>The {len(former)} earlier passage summaries</h2><p>Direct translation now covers {historical_direct:,} of the {historical_words:,} source words in these passages. The remaining column counts original words inside brackets. The page columns cover the entire reviewed passage.</p>',
             table(['Original passage','Source words','Direct','Remaining','Four-column pages','Print native pages','PDF pages'],passages),
             '</section><section id="sentences"><h2>All reviewed sentences</h2><p>Each of the ',str(sentence_count),
             ' source sentences that touches an earlier summary appears once here, including those restored in full. Page numbers cover the enclosing aligned paragraphs.</p>',all_sentences,
             f'</section><section id="reviews"><h2>Reassessment of the earlier {len(prev)} brackets</h2><p>The intermediate edition put {intermediate_words:,} words inside those brackets. The table records what each earlier decision means for the current text.</p>',
             table(['Chapter','Source sentence','Decision','Reason','Effect on the reading'],prev),
             '</section><footer><p>Verified editions</p>']
    for path in (BOOK/(EDITION+'.vay'), PRINT/(TITLE+'.vay'), PDF, SOURCE):
        parts.append(f'<p>{escape(path.name)}<br><code>{digest(path)}</code></p>')
    parts.append('</footer></main></html>')
    temporary = REPORT.with_suffix('.html.tmp')
    temporary.write_text(''.join(parts),encoding='utf8')
    temporary.replace(REPORT)
    print(f'{REPORT}: {sentence_count} reviewed sentences, {row_count} detailed sentences, {word_count} words, {len(bracket_keys)} brackets.')
    print(f'{word_count-hidden_count} source forms individually displayed; {hidden_count} described by grammatical function.')
    print('PDF pages',compact(pdf_pages))


STYLE = """
*{box-sizing:border-box}body{margin:0;color:#202321;background:#faf9f5;font:16px/1.55 Georgia,serif}
main{max-width:1130px;margin:auto;padding:45px clamp(16px,4vw,58px) 80px}header{padding-bottom:14px;border-bottom:2px solid #273c38}
h1,h2{line-height:1.15;font-weight:normal;color:#1b3530}h1{font-size:clamp(42px,6vw,77px);margin:12px 0 18px}h2{font-size:clamp(26px,3vw,39px);margin:8px 0 21px}
.lead{font-size:23px;max-width:780px}.locator,th,summary,nav{font-family:Arial,sans-serif}.locator{text-transform:uppercase;letter-spacing:.07em;color:#455955;font-size:12px;font-weight:bold}
nav{display:flex;flex-wrap:wrap;gap:12px 23px;padding:18px 0;border-bottom:1px solid #a7b5af}a{color:#225b50;text-underline-offset:3px}
section{padding:33px 0;border-bottom:1px solid #bbc5bc}p{max-width:88ch}blockquote{background:#f0f1e9;border-left:3px solid #5a7767;margin:18px 0;padding:16px 22px;font-size:19px}
mark{background:#f2dfae;color:#261d12;padding:0 2px}.explain li{margin:10px 0}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.4;margin:8px 0 15px}
th,td{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid #d8dcd5}th{color:#273d35}thead{background:#e6ebe4}.words td:nth-child(2){font-weight:bold}
.reading,.roman{font-style:italic}.reading{display:block;color:#315a4b;font-size:.95em}.omitted{color:#785636;font-size:.88em}
.assessment{color:#334e43;border-left:2px solid #a4b6ab;padding-left:9px;margin:8px 0 2px}
details{margin:10px 0;border:1px solid #c3cfc5;background:#fff;padding:8px 12px}summary{cursor:pointer;color:#294b3f;font-size:15px;font-weight:600}
.unit+.unit{border-top:1px solid #d1d6cc}.native{font:38px/1.2 native,serif;max-width:none}.gloss{font-size:14px}.unit p{overflow-wrap:anywhere}
footer{padding-top:20px;font-size:13px;color:#5d655d}code{overflow-wrap:anywhere}a:focus,summary:focus{outline:2px solid #315d4e}
@media print{body{background:white;font-size:10pt}nav,.entry>a{display:none}main{padding:0}h2,summary{break-after:avoid}.scroll{overflow:visible}tr{break-inside:avoid}}
"""


if __name__ == '__main__':
    report()
