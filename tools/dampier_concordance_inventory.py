"""Index complete source sentences and their enclosing Dampier edition passages."""
from collections import defaultdict
from collections.abc import Mapping
from html import escape
import re


ABBREVIATIONS = {
    'mr', 'mrs', 'dr', 'sr', 's', 'st', 'capt', 'cap', 'lat', 'long',
    'chap', 'gen', 'col', 'viz', 'i.e', 'e.g', 'n', 'e', 'w', 'b',
    's.e', 's.w', 'n.e', 'n.w', '&c', 'l',
}


def _sentences(line_number, line_text, inventory=False):
    matches = list(re.finditer(r'\S+', line_text))
    start, sequence = 0, 1
    for j, match in enumerate(matches):
        word = match[0].rstrip('”’"\')]}')
        terminates = word.endswith(('.', '!', '?'))
        if word.endswith('.') and word[:-1].lower() in ABBREVIATIONS:
            terminates = False
        if inventory and j + 1 < len(matches):
            # Two boundaries outside the detailed concordance need the following
            # word to distinguish abbreviation from sentence punctuation.
            following = matches[j + 1][0]
            if line_number == 647 and (word, following) == ('C.', 'Davis'):
                terminates = False
            if line_number == 723 and (word, following) == ('&c.', 'So'):
                terminates = True
        if not terminates and j + 1 < len(matches):
            continue
        parts = matches[start:j + 1]
        yield dict(id=f'L{line_number}.S{sequence}', line=line_number,
                   start=parts[0].start(), end=parts[-1].end(),
                   words=[dict(n=i, word=w[0], start=w.start(), end=w.end())
                          for i, w in enumerate(parts, 1)])
        start, sequence = j + 1, sequence + 1


def sentences(line_number, line_text, *, inventory=False):
    """Yield the stable sentence IDs and word offsets used by the grammatical notes."""
    yield from _sentences(line_number, line_text, inventory=inventory)


def _pages(numbers):
    """Format actual one-based pages without implying that a skipped page is covered."""
    pages = sorted({n for n in numbers if n is not None})
    runs = []
    for n in pages:
        if runs and n == runs[-1][-1] + 1:
            runs[-1].append(n)
        else:
            runs.append([n])
    return ', '.join(str(r[0]) if len(r) == 1 else f'{r[0]}–{r[-1]}' for r in runs) or '—'


def original_sentence_inventory(lines, old_units, finals, live_by_line, locations, decisions=None):
    """Return safe HTML and a count of unique original sentences intersecting old units.

    Unit and span offsets are zero-based and half-open. Replacements are clipped
    against every intersecting sentence before escaping any surviving source text.
    Source offsets and original redacted wording are never embedded in the HTML.
    """
    old_by_line, notes_by_line = defaultdict(list), defaultdict(list)
    for uid, spans in finals.items():
        unit = old_units[uid]
        line = unit['sourceLine']
        a, b = unit['sourceOffsets']
        old_by_line[line].append((a, b))
        for span in spans:
            i, j, reading = span['start'], span['end'], span['replacement']
            if not 0 <= i < j <= b - a or not (reading.startswith('[') and reading.endswith(']')):
                raise ValueError(f'Invalid source substitution in {uid}')
            notes_by_line[line].append((a + i, a + j, reading))

    out = ['<div class="scroll"><table><thead><tr><th scope="col">Source sentence</th>'
           '<th scope="col">English and individual editorial assessment</th>'
           '<th scope="col">Enclosing passages and pages</th></tr></thead><tbody>']
    count = 0
    for line in sorted(old_by_line):
        text = lines[line] if isinstance(lines, Mapping) else lines[line - 1]
        notes = sorted(notes_by_line[line])
        if any(left[1] > right[0] for left, right in zip(notes, notes[1:])):
            raise ValueError(f'Overlapping source substitutions on line {line}')
        whole = list(_sentences(line, text, inventory=True))
        for sentence in whole:
            a, b, sid = sentence['start'], sentence['end'], sentence['id']
            if not any(i < b and a < j for i, j in old_by_line[line]):
                continue
            pieces, bridges, cursor, detailed = [], [], a, False
            for i, j, reading in notes:
                if j <= a or b <= i:
                    continue
                detailed = True
                pieces.extend((escape(text[cursor:max(a, i)]), escape(reading)))
                cursor = min(j, b)
                if i < a or j > b:
                    others = [s['id'] for s in whole if s['id'] != sid and s['start'] < j and i < s['end']]
                    bridges.append('The same bracketed substitution also covers ' + ', '.join(others) + '.')
            pieces.append(escape(text[cursor:b]))
            for message in dict.fromkeys(bridges):
                pieces.append('<br><small>' + escape(message) + '</small>')
            enclosing = []
            for u in live_by_line[line]:
                i, j = u['sourceOffsets']
                if j <= a or b <= i:
                    continue
                uid = u['id']
                p = locations[uid]
                label = (f"{uid} · progressive {_pages(p['progressive'])} · "
                         f"print native {_pages(p['printNative'])} · print folio {_pages(p['printFolios'])} · "
                         f"duplex PDF {_pages(p['pdfPhysical'])}")
                enclosing.append('<div>' + escape(label) + '</div>')
            if not enclosing:
                raise ValueError(f'No enclosing live passage for {sid}')
            reference = escape(sid, quote=True)
            link = f'<a href="#{reference}">Word analysis</a>' if detailed else 'Fully restored'
            if decisions is not None:
                pieces.append('<p class="assessment">'+escape(decisions[sid])+'</p>')
            out.append(f'<tr id="inventory-{reference}"><th scope="row">{reference}<br>{link}</th>'
                       f'<td>{"".join(pieces)}</td><td>{"".join(enclosing)}</td></tr>')
            count += 1
    out.append('</tbody></table></div>')
    return '\n'.join(out), count
