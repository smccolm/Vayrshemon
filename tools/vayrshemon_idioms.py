"""Build the native four-column idiom inventory from its editable manuscript."""
from functools import lru_cache
from itertools import groupby
import json

from tools.compose_historical_book import texts
from tools.dictionary_corpus import ROOT, sha
from tools.dictionary_layout import DictionaryLayout, FIELDS
from tools.dictionary_lexicon import language_set
from tools.unta_language import quantity
from tools.vayrshemon_thesaurus import COLUMNS, locations, row
from vayrshemon import pages, reading
from vayrshemon.file_api import FileSession
from vayrshemon.json_stream import write_atomic


TITLE = 'Vayrshemon Idiom Inventory - Four-Column Progressive Edition'
FOLDER = ROOT / 'Saves' / TITLE
WORK = FOLDER / 'Working'
MANUSCRIPT = WORK / 'idioms.txt'
STAGE = ROOT / '.local' / 'idiom-inventory'
# Thimfora minima slots for sōlä, tōmä, ēsis and veks in the author's order.
GRIEF = 'st\u00d7v'


def manuscript():
    groups = []
    for line in MANUSCRIPT.read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():
            continue
        if line.startswith('# '):
            label, head, *identifier = line[2:].split(' | ')
            groups.append(dict(label=label, head=head, id=identifier[0] if identifier else None, entries=[]))
        elif line.startswith('## '):
            label, head, *identifier = line[3:].split(' | ')
            entry = dict(label=label, head=head, id=identifier[0] if identifier else None, examples=[])
            groups[-1]['entries'].append(entry)
        else:
            tag, *data = line.split(' | ')
            if tag == 'W':
                path, key, phrase, reference = data
                entry['witness'] = dict(path=path, key=key, phrase=phrase, reference=reference)
            elif tag in ('D', 'E'):
                analysis, english = data
                if tag == 'D':
                    if 'definition' in entry:
                        raise ValueError('Duplicate definition for ' + entry['label'])
                    entry['definition'] = dict(analysis=analysis, english=english)
                else:
                    entry['examples'].append(dict(analysis=analysis, english=english))
            else:
                raise ValueError('Unknown manuscript line ' + line)
    # Issued identifiers travel with their text when an entry or subject moves.
    # New manuscript headings may still be written with just a name and analysis.
    for prefix, items, width in [('section', groups, 1),
                                 ('idiom', [e for g in groups for e in g['entries']], 2)]:
        numbers = set()
        for item in items:
            key = item['id']
            if key is None:
                continue
            stem, _, suffix = key.partition('-')
            if stem != prefix or not suffix.isdecimal() or int(suffix) in numbers:
                raise ValueError('Invalid or duplicate manuscript identifier: ' + key)
            numbers.add(int(suffix))
        serial = max(numbers, default=0)
        for item in items:
            if item['id'] is None:
                serial += 1
                item['id'] = f'{prefix}-{serial:0{width}d}'
    return groups


@lru_cache(maxsize=None)
def witness_units(relative_path):
    source = json.loads((ROOT / 'Saves' / relative_path).read_bytes())
    return {u['id']: u for u in source['units']}


def compile_rows():
    lang, historical = language_set()
    lang.lexicon = {**historical.lexicon, **lang.lexicon}
    for k, g in {'kjv_bucket':'bucket', 'kjv_ferryboat':'ferryboat', 'kjv_scribe':'scribe',
                 'kjv_dawn':'dawn', 'kjv_mill':'mill', 'kjv_pot':'pot', 'kjv_gnat':'gnat',
                 'kjv_camel':'camel', 'kjv_swallow':'swallow', 'kjv_strain_filter':'strain',
                 'kjv_message':'message', 'plank_board':'plank', 'wrist_joint':'wrist',
                 'sheet_paper_and_bed':'sheet-of-paper', 'yesterday_day':'yesterday',
                 'kjv_ceiling':'ceiling','leak_vessel':'leak','service_wages':'wages',
                 'author_person':'author','appeal_request':'appeal',
                 'kjv_fish_scale':'fish-scale','kjv_sequence_order':'sequence',
                 'kjv_ship_stern':'stern-of-a-ship'}.items():
        lang.glosses[k] = g
    if lang.word('ultimate_grief')[:2] != (GRIEF, 'ultimate-grief') or len(GRIEF) != 4 or lang.reading(GRIEF) != 'stēv':
        raise ValueError('The four native letters must read stēv in Transliteration 7')
    rows, records, seen = [], [], set()

    def add(key, kind, ref, analysis, english, initial=True):
        try:
            result = lang.compile(analysis, initial=initial)
        except (KeyError, ValueError) as exc:
            raise ValueError(f'{ref} ({key}): {analysis}') from exc
        rows.append(row(key, kind, ref, result['text'], result['gloss'], english))
        return result

    add('title','title','Idiom inventory','book of way:pl of speak:inf',
        'Vayrshemon Idiom Inventory')
    add('guide','guide','Reading the inventory',
        'way:pl of speak:inf about same:m thing together stand:pr. each example meaning in use show:pr. list first book_leaf of each group show:pr.',
        'Expressions about the same subject appear together. Each example shows how an expression is used. The subject guide gives the opening page of each group.')
    example_texts = set()
    for group in manuscript():
        start = len(rows)
        add(group['id'],'section',group['label'],group['head'],group['label'])
        for entry in group['entries']:
            label = entry['label']
            if label in seen or 'definition' not in entry or not entry['examples']:
                raise ValueError('Duplicate or incomplete idiom: ' + label)
            seen.add(label)
            eid = entry['id']
            head = lang.compile(entry['head'], initial=False)
            if any(record['native'] == head['text'] for record in records):
                raise ValueError('Two idioms share a heading: ' + label)
            record = dict(id=eid, label=label, section=group['label'], native=head['text'],
                          transliteration=lang.reading(head['text']), examples=[])
            definition = entry['definition']
            d = lang.compile(definition['analysis'])
            record['definition'] = dict(native=d['text'], transliteration=lang.reading(d['text']),
                                        gloss=d['gloss'], english=definition['english'])
            english = label + ' — ' + definition['english']
            if 'witness' in entry:
                w = entry['witness']
                unit = witness_units(w['path'])[w['key']]
                if w['phrase'] not in unit['analysis']:
                    raise ValueError('Witness wording differs for ' + label)
                record['witness'] = dict(**w, nativePassage=unit['text'], sourcePassage=unit['source'])
                english += ' (' + w['reference'] + ')'
            rows.append(row(eid,'entry',label,head['text']+': '+d['text'],
                            head['gloss']+': '+d['gloss'],english))
            for idx, example in enumerate(entry['examples'], 1):
                rendered = add(f'{eid}-ex{idx}','example',label,example['analysis'],example['english'])
                if rendered['text'] in example_texts or example['english'] in example_texts:
                    raise ValueError('Repeated illustration for ' + label)
                example_texts.update((rendered['text'],example['english']))
                record['examples'].append(dict(native=rendered['text'], english=example['english']))
            records.append(record)
        for r in rows[start:]:
            r['section'] = group['id']
    return rows, records


class InventoryLayout(DictionaryLayout):
    def measured(self, group):
        count, state, error = super().measured(group)
        end = count
        while end > 1 and group[end-1]['kind'] in {'section', 'entry'}:
            end -= 1
        if end != count:
            return super().measured(group[:end])
        return count, state, error


def subject_guide(rows, layout):
    opening, body = rows[:2], rows[2:]
    headings = []
    body_pages = 0
    for _, group in groupby(body, key=lambda r: r['section']):
        group = list(group)
        headings.append((group[0], body_pages + 1))
        body_pages += max(locations(group, layout).values()) + 1
    for r in opening:
        r['section'] = 'directory'
    offset = 0
    for _ in range(8):
        front = opening.copy()
        targets = {}
        for r, relative_page in headings:
            page = relative_page + offset
            number = quantity(page, notation='digits')['form']
            front.append(row('guide-'+r['id'], 'pointer', r['reference'],
                             f"{r['text']} · {number}", f"{r['gloss']} · {page}",
                             f"{r['source']} · {page}", 'directory'))
            targets[r['id']] = page
        size = max(locations(front, layout).values())+1
        if size == offset:
            return front + body, targets
        offset = size
    raise ValueError('Subject guide pagination did not converge')


def publish():
    rows, records = compile_rows()
    STAGE.mkdir(parents=True,exist_ok=True)
    dest = FOLDER / (TITLE + '.vay')
    receipt = WORK / 'publication.json'
    if dest.exists() and (not receipt.exists() or json.loads(receipt.read_bytes())['sha256'] != sha(dest)):
        raise ValueError('The existing edition has independent edits.')
    layout = InventoryLayout(title=TITLE, document_id='document.native-idioms',
                             id_prefix='idioms', column_names=COLUMNS, cache_root=STAGE)
    stage = STAGE / 'publication.vay'
    try:
        rows, targets = subject_guide(rows, layout)
        report, spreads = layout.build(rows,stage,sha(MANUSCRIPT))
    finally:
        layout.session.finish()
    by_id = {r['id']:r for r in rows}
    on_page = {key:spread['leftPage'] for spread in spreads for key in spread['ids']}
    if any(on_page[k] != p for k,p in targets.items()):
        raise ValueError('A subject guide reference leads to the wrong page')
    native_grief_uses = sum(r['text'].count(GRIEF) for r in rows)
    grief_runs = [0, 0]
    session = FileSession(ROOT,source_fonts=False,recovery=False)
    session.remember = lambda *a:None
    session.log.emit = lambda *a,**kw:None
    try:
        session.open(stage,advance_revision=False)
        state = session.state
        if state['title'] != TITLE or session.saved_page_mode != 'two' or len(state['pages']) != 2*len(spreads):
            raise ValueError('Unexpected reopened edition')
        for spread in spreads:
            pair = state['pages'][spread['leftPage']-1:spread['rightPage']]
            frames = [f for page in pair for f in sorted(page['frames'],key=lambda x:int(x['x']))]
            if [f['name'] for f in frames] != list(COLUMNS):
                raise ValueError('Reopened column order differs')
            for field, frame in zip(FIELDS,frames,strict=True):
                if texts(frame) != [by_id[key][field] for key in spread['ids']]:
                    raise ValueError('Reopened content differs')
            for index, (frame, digest) in enumerate(zip(frames[:2], (reading.SCRIPT_SHA,reading.ROMAN_SHA),strict=True)):
                doc = frame['content']['document']
                font_ids = {style['styleId']:style.get('fontId') for style in doc['styles']}
                for block in doc['stories'][0]['blocks']:
                    for run in block['runs']:
                        value = run.get('sourceText',run.get('text',''))
                        if any(c.isalpha() for c in value) and font_ids[run['styleId']] != f'font:{digest}:0':
                            raise ValueError('Unexpected font for native letters in ' + frame['name'])
                        if 'sola-toma-esis-veks' in value:
                            raise ValueError('Letter names printed in place of the word for ultimate grief')
                        if GRIEF in value and run.get('type') == 'legacy':
                            grief_runs[index] += value.count(GRIEF)
        if native_grief_uses < 3 or grief_runs != [native_grief_uses, native_grief_uses]:
            raise ValueError('Lost or split four-letter spelling for ultimate grief')
        for page in state['pages']:
            picture,_ = pages.render(session,page_id=page['pageId'],mode='mono',dpi=80,reading=True)
            if not picture.save(str(STAGE/(page['pageId']+'.png'))):
                raise OSError('Could not render ' + page['pageId'])
    finally:
        session.finish()
    for r in records:
        r['leftPage'] = on_page[r['id']]
    write_atomic(WORK/'entries.json',records)
    report.update(idioms=len(records),examples=sum(len(r['examples']) for r in records),
                  sourceLinkedIdioms=sum('witness' in r for r in records),
                  subjects=[dict(label=by_id[k]['reference'], leftPage=p) for k,p in targets.items()],
                  ultimateGrief=dict(transliteration='stēv', nativeLetters=4,
                                     verifiedOccurrencesPerReadingColumn=native_grief_uses),
                  columns=list(COLUMNS),nativeReopenVerified=True)
    stage.replace(dest)
    write_atomic(receipt,report)
    print(json.dumps(report,ensure_ascii=True))


if __name__ == '__main__':
    publish()
