"""Author-directed historical name correction 282; never edits sealed books.

Display labels are explicit package data. They never replace lexical identities,
authored analyses, English source text, or the historical grammar.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
import argparse
import hashlib
import html
import json
import re
import shutil

from tools.kjv_archive import read, digest, verify_register
from tools.kjv_historical_flow import compiler

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.10-kjv.282'
PARENT = ROOT / 'data/language/archaic-kjv-281'
PACKAGE = ROOT / 'data/language/archaic-kjv-282'
SOURCE = ROOT / 'Saves/KJV Bible v0.10-kjv.281'
OUT = ROOT / 'Saves/KJV Bible v0.10-kjv.282'
COMPACT = ROOT / 'Saves/KJV Bible - Compact Letter Edition v0.10-kjv.282'
SOURCE_SHA = 'e210054b0a01f34cd5582590c0c30e3118e4fc33d2f3b74d701da59330fc979e'
NAME_FORMS = {
    'kjv_jesus_matthew': 'yeÛça',
    'kjv_jesus_joshua_acts': 'yeÛça',
    'kjv_jesus_justus_colossians': 'yeÛça',
    'kjv_jesus_rest_hebrews': 'yeÛça',
    'kjv_barjesus_acts': 'baryeÛça',
}
NOTE = '''# Historical correction 282: names and construction glosses

This is an explicit author-requested correction to historical 281, not a
modernization. The author selected **Yeshūa**. Its legacy minima slots are
`yeÛça`; the ordinary proper-name Maxima yields `YeÛça`, read **Yeshūa** by
Transliteration 7. The inherited affixes and phrase clitics still attach normally.
The spelling is an authored Vayrshemon adaptation, not a claim that the historical
Hebrew vowel quantity was ū.

The four distinct Jesus entries use that spelling. The Jesus called Justus,
the Acts 7:45 namesake and the Hebrews 4:8 rest-giver retain separate semantic
identities and their existing contextual definitions. The name Barjesus adopts
the same stem as **Baryeshūa**, retaining its inherited bar- prefix without a
new grammatical or theological analysis. Joshua and Jeshua entries otherwise
remain unchanged; no people are merged merely because names are related.

“Jesus-Matthew” was an internal lookup qualifier printed as if part of a name.
Construction glosses now use the name itself. The same repair removes book,
parent, role and location qualifiers accidentally printed from other proper-name
keys. Exact reviewed replacements and dictionary/source evidence are in
`display-labels.json`. Full definitions and stable lexical keys retain all
distinctions. Genuine compound names and semantic title translations remain.
The English KJV column remains byte-for-byte unchanged, including its Jesus.

No grammar, ordinary lexical roots, source verses, Maxima rules, typography or
paint recipes change. All 31,102 analyses are recompiled and compared with the
281 outputs; every changed verse has a before/after correction record.

The small 282 Forge project imports the exact sealed 281 snapshot as its local
root. The original 281 head and full older ancestry remain in the verified
`KJV before 281.7z` archive; the import record distinguishes the local root from
that original head. This avoids copying 17 GB of cumulative history again.
'''


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def normalized(value):
    return re.sub('[^a-z]', '', value.lower())


def display_labels(lexicon, glosses, units):
    sources = defaultdict(list)
    for unit in units:
        for key in set(unit['keys']):
            sources[key].append(unit)
    result = {}
    # A leading dictionary name must also occur in a verse using this exact ID.
    # This is a proposal filter, not a runtime name-stripping heuristic.
    for key, entry in lexicon.items():
        old = glosses.get(key, key.replace('_', '-'))
        if entry['pos'] != 'proper' or key not in sources or not ('-' in old or '{' in old):
            continue
        match = re.match(r'([A-Z][A-Za-z]*(?:[- ][A-Z][A-Za-z]*)*)', entry['meaning'])
        name = match[1].replace(' ', '-') if match else None
        if name and old.lower().startswith(name.lower()) and old.lower() != name.lower():
            evidence = next((u['reference'] for u in sources[key] if normalized(name) in normalized(u['source'])), None)
            if not evidence:
                raise ValueError('NAME_NEEDS_SOURCE_REVIEW: ' + key)
            result[key] = dict(before=old, after=name, evidence=evidence, reason='Leading dictionary name attested in the source; internal context qualifier removed.')
    # Reviewed cases whose definition starts with a description instead of a name.
    for key, entry in lexicon.items():
        old = glosses.get(key, '')
        if entry['pos'] == 'proper' and key in sources and re.fullmatch(r'[A-Z][a-z]+\{[^}]+\}', old):
            name = old.split('{')[0]
            if name in {'Rock', 'Belial'}:
                continue  # Already handled by the leading dictionary-name rule.
            evidence = next((u['reference'] for u in sources[key] if normalized(name) in normalized(u['source'])), None)
            if evidence:
                result[key] = dict(before=old, after=name, evidence=evidence, reason='Reviewed referent qualifier; identity retained in dictionary.')
    manual = {
        'kjv_avite_ava': 'Avite', 'kjv_shilonite_resident': 'Shilonite',
        'kjv_bands_staff': 'Band', 'kjv_pavement_john': 'Pavement',
        'kjv_fair_havens_acts': 'Fair-havens', 'kjv_three_taverns_acts': 'Three-taverns',
        'kjv_elam_other': 'Elam',  # Ezra 2:31 / Nehemiah 7:34 already have separate “other”.
    }
    for key, name in manual.items():
        result[key] = dict(before=glosses[key], after=name, evidence=sources[key][0]['reference'], reason='Reviewed name/number stem; genuine multiword place label retained.')
    for key in NAME_FORMS:
        result[key] = dict(before=glosses[key], after='Baryeshūa' if key == 'kjv_barjesus_acts' else 'Yeshūa', evidence=sources[key][0]['reference'], reason='Author-selected native name; separate identities retained.')
    return result


def prepare():
    verify_register('0.10-kjv.281')
    assert digest(SOURCE / 'KJV Bible.vay') == SOURCE_SHA
    assert not PACKAGE.exists() and not OUT.exists() and not COMPACT.exists(), 'Use a new edition; never overwrite working or sealed files'
    PACKAGE.mkdir(); OUT.mkdir(); COMPACT.mkdir()
    for name in ('compiler.py', 'lexicon.json', 'morphology.json', 'orthography.json', 'grammar.md', 'flow-cases.json'):
        shutil.copyfile(PARENT / name, PACKAGE / name)
    original = read(SOURCE / 'complete-translation-ledger.json')
    lex = read(PACKAGE / 'lexicon.json'); morph = read(PACKAGE / 'morphology.json')
    labels = display_labels(lex['entries'], morph['glosses'], original['units'])
    prior = compiler(PARENT)
    changes = {}
    for key, form in NAME_FORMS.items():
        entry = lex['entries'][key]
        changes[key] = dict(before=entry['form'], after=form, beforeRoman=entry['roman'], afterRoman=prior.reading(form), semanticId=entry['semanticId'])
        entry['historicalForms'] = entry.get('historicalForms', []) + [dict(version='0.10-kjv.281', form=entry['form'], roman=entry['roman'], status='superseded by explicit author correction')]
        entry.update(form=form, roman=prior.reading(form), register=VERSION)
        entry['origin'] += ' Author-selected Yeshūa adaptation, 2026-11-05; original referent retained.'
    for key, change in labels.items():
        morph['glosses'][key] = change['after']
    lex['version'] = VERSION
    write(PACKAGE / 'lexicon.json', lex); write(PACKAGE / 'morphology.json', morph)
    write(PACKAGE / 'display-labels.json', labels); write(PACKAGE / 'name-forms.json', changes)
    (PACKAGE / 'names.md').write_text(NOTE, encoding='utf8')
    lang = compiler(PACKAGE)
    assert lang.reading(lang.word('kjv_jesus_matthew')[0]) == 'Yeshūa'
    units, corrections, counts = [], [], Counter()
    for old in original['units']:
        expected = prior.compile(old['analysis'])
        assert expected['text'] == old['text'] and expected['gloss'] == old['gloss'], ('PARENT_COMPILATION_DIFFERS', old['reference'])
        compiled = lang.compile(old['analysis'])
        assert compiled['keys'] == old['keys']
        new = dict(deepcopy(old), **compiled)
        if new['text'] != old['text'] or new['gloss'] != old['gloss']:
            affected = sorted(set(old['keys']) & (set(labels) | set(NAME_FORMS)))
            assert affected
            if new['text'] != old['text']:
                assert set(affected) & set(NAME_FORMS)
                counts['nativeNameVerses'] += 1
            if new['gloss'] != old['gloss']: counts['glossVerses'] += 1
            corrections.append(dict(id=old['id'], reference=old['reference'], keys=affected, beforeText=old['text'], afterText=new['text'], beforeGloss=old['gloss'], afterGloss=new['gloss']))
        units.append(new)
    ledger = dict(original, version=VERSION, correctionOf='0.10-kjv.281', units=units)
    summary = dict(version=VERSION, parent='0.10-kjv.281', verses=len(units), sections=len({u['id'].split('.')[0] for u in units}), revisedVerses=len(corrections), **counts,
        properDisplayLabelsCorrected=len(labels), nameEntriesAdapted=len(NAME_FORMS), newLexicalRoots=0, grammarChanges=0,
        exactSourceAndAnalysesPreserved=True, identitiesPreserved=True, maximaRulesUnchanged=True,
        parentNativeSha256=SOURCE_SHA, parentLedgerSha256=digest(SOURCE / 'complete-translation-ledger.json'),
        currentModernLanguageSha256=digest(ROOT / 'data/language/current.json'))
    write(OUT / 'complete-translation-ledger.json', ledger)
    write(OUT / 'correction-ledger.json', corrections); write(OUT / 'language-delta.json', summary)
    write(PACKAGE / 'coverage-summary.json', summary)
    for name in ('complete-translation-ledger.json', 'correction-ledger.json', 'language-delta.json'):
        shutil.copyfile(OUT / name, COMPACT / name)
    print(json.dumps(summary, indent=2), flush=True)


def publish():
    from vayrshemon.forge import ForgeProject, validate, digest as snapshot_digest
    assert not (PACKAGE / 'manifest.json').exists(), 'Already published'
    prior = read(SOURCE / 'current-snapshot.json')
    project = ForgeProject.create(OUT / 'KJV 282.vayforge', 'KJV 282 · Yeshūa and proper-name gloss correction', snapshot=prior['snapshot'])
    root = project.status()['head']
    provenance = dict(originalHead=prior['head'], importedSnapshotSha256=snapshot_digest(prior['snapshot']), localImportHead=root,
        externalAncestryArchive='Saves/Archive/Previous editions/KJV before 281.7z',
        archiveMember='KJV Bible v0.10-kjv.280/KJV Bible 0.10-kjv.280.vayforge',
        archiveSha256='380eba43c8dda71145ef99eb58206e87150a79572ffa54f9efc94c77ec2ed427',
        explanation='Exact 281 snapshot imported into a small project; older complete ancestry archived, not falsely represented as this local root.')
    snapshot = deepcopy(prior['snapshot']); lex = read(PACKAGE / 'lexicon.json')['entries']
    found = set()
    for entry in snapshot['language']['lexicon']:
        if entry['label'] in NAME_FORMS:
            new = lex[entry['label']]; entry.update(headword=new['form'], pronunciation=new['roman'])
            found.add(entry['label'])
    assert found == set(NAME_FORMS), found
    snapshot['wiki'].insert(0, dict(id='kjv282-names', title='KJV 282 · Yeshūa and readable name glosses', body=NOTE, ruleIds=[]))
    snapshot['decisions'].append(dict(id='kjv282-names', status='draft', choice=NOTE, evidence='Explicit author choice Yeshūa and direction to correct both editions; source-checked display label ledger.'))
    units = read(OUT / 'complete-translation-ledger.json')['units']
    snapshot['tests'] = [t for t in snapshot['tests'] if not t['id'].startswith('kjv')]
    for u in units:
        snapshot['tests'].append(dict(id='kjv282.verse.'+u['id'], title='KJV 282 · '+u['reference'], ruleIds=[], paragraphs=[dict(text=u['text'], translation=u['source'], analysis=u['gloss']+'\nAuthored analysis: '+u['analysis']+'\nBack-reading: '+u['backReading']+'\nNote: '+u['note'])]))
    snapshot['research']['kjv282Names'] = read(OUT / 'language-delta.json')
    snapshot['research']['kjv282Import'] = provenance
    validate(snapshot)
    status = project.replace_draft(snapshot, project.status()['generation'])
    status = project.commit('KJV 282 · Yeshūa, source-checked proper-name labels; all 31,102 verses', status['generation'])
    write(OUT / 'current-snapshot.json', dict(head=status['head'], snapshot=snapshot))
    write(OUT / 'forge-import.json', provenance)
    ref = dict(project=str(project.path), branch='main', head=status['head'], original281Head=prior['head'], localImportHead=root)
    write(OUT / 'forge-reference.json', ref); write(COMPACT / 'forge-reference.json', ref)
    manifest = dict(version=VERSION, policy='never-modernize', status='Author-directed name correction; publication validation recorded separately.',
        basePackage='data/language/archaic-kjv-281', baseManifestSha256=digest(PARENT / 'manifest.json'), baseForgeHead=prior['head'],
        forgeHead=status['head'], localImportHead=root, compilerPath='data/language/archaic-kjv-282/compiler.py', compilerSha256=digest(PACKAGE / 'compiler.py'),
        files={p.name:digest(p) for p in PACKAGE.iterdir() if p.is_file() and p.name!='manifest.json'})
    write(PACKAGE / 'manifest.json', manifest)
    registry = read(ROOT / 'data/language/historical.json')
    registry['registers'].append(dict(version=VERSION, package='data/language/archaic-kjv-282', manifestSha256=digest(PACKAGE / 'manifest.json'), forgeHead=status['head'], policy='never-modernize', status='Author-directed names correction; complete 31,102 verse targets', guide='docs/KJV_ARCHIVE.md'))
    write(ROOT / 'data/language/historical.json', registry); verify_register(VERSION)
    style='<meta charset="utf-8"><style>body{max-width:1100px;margin:3em auto;font:18px/1.6 Georgia}td,th{padding:8px;text-align:left;border-bottom:1px solid #ddd}pre{white-space:pre-wrap}</style>'
    language = compiler(PACKAGE); labels=read(PACKAGE / 'morphology.json')['glosses']
    rows=''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in (k, language.reading(v['form']), labels.get(k,''), v['meaning']))+'</tr>' for k,v in sorted(lex.items()))
    (OUT/'Dictionary.html').write_text(style+'<h1>KJV 282 · Historical dictionary</h1><p>Stable identifiers distinguish referents; glosses display names without internal context labels.</p><table><tr><th>ID</th><th>Roman form</th><th>Gloss</th><th>Meaning</th></tr>'+rows+'</table>',encoding='utf8')
    grammar=NOTE+'\n\n'+(PACKAGE/'grammar.md').read_text(encoding='utf8')
    (OUT/'Wiki.md').write_text(grammar,encoding='utf8'); (OUT/'Wiki.html').write_text(style+'<h1>KJV 282 · Historical grammar and names</h1><pre>'+html.escape(grammar)+'</pre>',encoding='utf8')
    for name in ('Wiki.md','Wiki.html','Dictionary.html'): shutil.copyfile(OUT/name, COMPACT/name)
    print('Published',status['head'],flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--publish',action='store_true');args=parser.parse_args()
    if args.prepare:prepare()
    if args.publish:publish()
