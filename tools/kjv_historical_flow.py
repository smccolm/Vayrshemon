"""Author-directed historical correction 281; never modify a sealed edition.

Rules operate on authored grammatical analyses, never on glyph strings. Every
application retains its input, output and rule in the private correction ledger.
The modern dramatic language is neither imported nor promoted.
"""
from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.10-kjv.281'
PARENT = ROOT / 'data/language/archaic-kjv-280'
PACKAGE = ROOT / 'data/language/archaic-kjv-281'
SOURCE = ROOT / 'Saves/KJV Bible v0.10-kjv.280'
OUT = ROOT / 'Saves/KJV Bible - Compact Letter Edition v0.10-kjv.281'
TOKEN = r'[A-Za-z_][A-Za-z_+/:\-]*'
STACK = re.compile(r'\bof(?: of)+(?![A-Za-z_]) (' + TOKEN + r')')
PRONOUN = r'(?:he|she|they|it|i|ipl|wesg|we|you|thou|thee)(?::(?:pl|du))?'
DEPENDENT_PAIR = re.compile(r'\b(to|with|from|before|after|upon|against|among|for|unto|by|in|of|near|behind|beside|besides|over|on|under|into|through|without|between|within|around|until) (' + PRONOUN + r') \2\b(?![/+:])')
FINITE = re.compile(r':(?:pr|pa|fu|perf|pp|fp|prog|pprog|gn|imp)(?=[:\s.,;?!]|$)')
NARRATIVE_BOOKS = set(range(1, 18)) | {27, 32, 40, 41, 42, 43, 44}
# Deliberate liturgical, alphabetic and quoted cumulative refrains are retained.
REFRAIN_CHAPTERS = {(19, 119), (19, 136), (19, 148), (19, 150)}
MORPHEMES = {
    'relpair': ['’yë', 'rel.chain.2'],
    'reltriple': ['’yër', 'rel.chain.3'],
    'relquad': ['’yël', 'rel.chain.4'],
    'dep': ['’em', 'dependent.pron.'],
    'add': ['’ã', 'additive.clause'],
    'cont': ['', 'unmarked.continuation'],
    'subend': ['’eth', 'dependent.clause.end'],
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compiler(folder):
    spec = importlib.util.spec_from_file_location('kjv_flow_compiler', folder / 'compiler.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.EditorialLanguage(folder)


def revise(unit, previous=None):
    analysis = unit['analysis']
    changes = []

    def record(rule, before, after):
        changes.append(dict(rule=rule, before=before, after=after))
        return after

    # Authored census construction: the bound name/child already expresses the
    # innermost relation. The two outer heads receive inherited genitive case.
    # This is not a general inference that every repeated 'of' is redundant.
    pattern = r'\bof of of (kjv_[a-z_]+/child:pl) kjv_tribe army\b'
    analysis = re.sub(pattern, lambda m: record('construct-census-host', m[0], m[1] + ':g kjv_tribe:g army'), analysis)
    # The corresponding captain-of-children census formula, with its explicitly
    # bound ancestor, has one remaining relational level, not two.
    pattern = r'\bof of (kjv_[a-z_]+/child:pl) (captain|chief)(?=[:\s.,;]|$)'
    analysis = re.sub(pattern, lambda m: record('construct-census-captain', m[0], m[1] + ':g ' + m[2]), analysis)
    if unit['reference'] == 'Numbers 3:30':
        old = 'of of of of kjv_kohath people kjv_family:pl father kjv_household chief'
        new = 'kjv_kohath people:g kjv_family:pl:g father:g kjv_household:g chief'
        if old not in analysis:
            raise ValueError('REVIEWED_CONSTRUCTION_CHANGED: Numbers 3:30')
        analysis = analysis.replace(old, record('construct-household-chief', old, new))

    def relational(m):
        depth = m[0].split().count('of')
        feature = {2: 'relpair', 3: 'reltriple', 4: 'relquad'}[depth]
        host = m[1]
        if host.endswith(':') or host in {'and', 'or', 'but'}:
            raise ValueError('RELATION_HOST_REVIEW: ' + unit['reference'] + ' ' + m[0])
        return record('relational-clitic-' + str(depth), m[0], host + ':' + feature)

    analysis = STACK.sub(relational, analysis)
    # The preposition keeps its meaning. An oblique allomorph distinguishes its
    # dependent pronoun without assuming coreference or dropping either person.
    analysis = DEPENDENT_PAIR.sub(lambda m: record('dependent-pronoun', m[0], m[1] + ' ' + m[2] + ':dep ' + m[2]), analysis)
    # The first 'to' introduces purpose, the second a recipient. Keep both roles.
    analysis = re.sub(r'\bto to (' + TOKEN + r') (?=[^.,;?!]*:inf\b)',
                      lambda m: record('purpose-recipient', m[0], 'for to ' + m[1] + ' '), analysis)
    # Causal 'for' and benefactive 'for' are different constructions. Use the
    # inherited causal conjunction before the retained beneficiary expression.
    analysis = re.sub(r'\bfor for\b', lambda m: record('cause-beneficiary', m[0], 'because for'), analysis)
    # Head-final dependent and matrix predicates may coincide. A clause-ending
    # clitic makes that boundary audible; neither predicate is elided.
    def close_clause(m):
        prefix = analysis[:m.start()]
        clause = re.split(r'[.!?;]', prefix)[-1]
        if re.search(r'\b(who|which|whom|where|that)\b', clause):
            return record('dependent-clause-boundary', m[0], m[1] + ':subend ' + m[1])
        return m[0]
    analysis = re.sub(r'\b(' + TOKEN + r':(?:pr|pa|fu|perf|pp|fp)) \1(?=[\s.,;?!]|$)', close_clause, analysis)

    book, chapter, _ = map(int, unit['id'].split('.'))
    same_context = previous is not None and previous['id'].split('.')[:2] == unit['id'].split('.')[:2]
    # Verse boundaries are not always clause boundaries. Do not remove a list
    # coordinator or the opening of a deliberately preserved refrain.
    if analysis.startswith('and ') and same_context and FINITE.search(analysis) and (book, chapter) not in REFRAIN_CHAPTERS:
        match = re.match(r'and (' + TOKEN + r')', analysis)
        if match and not match[1].endswith(':') and match[1] not in {'and', 'or', 'but'}:
            host = match[1]
            # At a completed narrative sentence, juxtaposition carries additive
            # continuation. At other boundaries the additive clitic is audible.
            complete = bool(re.search(r'[.?!]\s*$', previous['analysis']))
            feature = 'cont' if book in NARRATIVE_BOOKS and complete else 'add'
            replacement = host + ':' + feature
            analysis = record('clause-' + feature, match[0], replacement) + analysis[len(match[0]):]
    return analysis, changes


def prepare(resume=False):
    if ((OUT / 'complete-translation-ledger.json').exists() and not resume) or (PACKAGE / 'manifest.json').exists():
        raise FileExistsError('281 already exists; inspect the working edition before rebuilding')
    from tools.editorial_language import load_current
    from tools.kjv_archive import verify_register
    _, modern = load_current()
    verify_register('0.10-kjv.280')
    PACKAGE.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
    for name in ('compiler.py', 'lexicon.json', 'morphology.json', 'orthography.json'):
        if not (PACKAGE / name).exists():
            shutil.copyfile(PARENT / name, PACKAGE / name)
    morphology = read(PACKAGE / 'morphology.json')
    morphology['suffixes'].update(MORPHEMES)
    write(PACKAGE / 'morphology.json', morphology)
    lang = compiler(PACKAGE)
    old_lang = compiler(PARENT)
    original = read(SOURCE / 'complete-translation-ledger.json')
    units, corrections, counts, previous = [], [], Counter(), None
    # Exact equality against the old compiler catches unrecorded/manual surface
    # spellings. Only revised verses are recompiled; unaffected bytes stay exact.
    for old in original['units']:
        analysis, edits = revise(old, previous)
        new = deepcopy(old)
        if edits:
            expected = old_lang.compile(old['analysis'])
            if expected['text'] != old['text']:
                raise ValueError('PARENT_COMPILATION_DIFFERS: ' + old['reference'])
            new.update(lang.compile(analysis), analysis=analysis)
            new['note'] += ' Historical correction 281: ' + ', '.join(dict.fromkeys(e['rule'] for e in edits)) + '. Participant identities, polarity and quantities retained.'
            corrections.append(dict(id=old['id'], reference=old['reference'], source=old['source'],
                                    beforeAnalysis=old['analysis'], afterAnalysis=analysis,
                                    beforeText=old['text'], afterText=new['text'], rules=edits))
            counts.update(e['rule'] for e in edits)
        units.append(new); previous = old
    ledger = dict(original, version=VERSION, units=units, correctionOf='0.10-kjv.280')
    write(OUT / 'complete-translation-ledger.json', ledger)
    write(OUT / 'correction-ledger.json', corrections)
    summary = dict(version=VERSION, parent='0.10-kjv.280', currentModernVersionReviewed=modern['version'],
                   currentModernHeadUnchanged=modern['forgeHead'], verses=31102, sections=66,
                   revisedVerses=len(corrections), rules=dict(counts), newLexicalRoots=0,
                   newGrammaticalForms=MORPHEMES, originalLedgerSha256=digest(SOURCE / 'complete-translation-ledger.json'),
                   parentNativeSha256=digest(SOURCE / 'KJV Bible.vay'),
                   sourceVerseOrderUnchanged=[(u['id'],u['source']) for u in units] == [(u['id'],u['source']) for u in original['units']],
                   remainingAdjacentOfAnalyses=sum(bool(re.search(r'\bof of\b', u['analysis'])) for u in units),
                   initialAndBefore=sum(u['analysis'].startswith('and ') for u in original['units']),
                   initialAndAfter=sum(u['analysis'].startswith('and ') for u in units))
    write(OUT / 'language-delta.json', summary)
    refs = {'Numbers 3:30', 'Numbers 10:15', 'Numbers 10:16', 'Numbers 7:89', 'Numbers 14:24',
            'Genesis 1:2', 'Genesis 1:3', 'Genesis 30:41', 'Psalms 136:11', 'John 1:1', 'Revelation 22:21'}
    write(PACKAGE / 'flow-cases.json', [u for u in units if u['reference'] in refs])
    write(PACKAGE / 'coverage-summary.json', {k:v for k,v in summary.items() if k != 'newGrammaticalForms'})
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


def publish():
    """Add a branch to the canonical Forge; do not clone its growing history."""
    from vayrshemon.forge import ForgeProject, validate
    from vayrshemon.archive_language import base
    from tools.kjv_archive import verify_register
    if (PACKAGE / 'manifest.json').exists():
        raise FileExistsError('281 package already published')
    language = compiler(PACKAGE)
    lexicon = read(PACKAGE / 'lexicon.json')
    meanings = {
        'relpair': 'Bound relational chain of depth two; expands to two left-edge analytical relations.',
        'reltriple': 'Bound relational chain of depth three; expands to three left-edge analytical relations.',
        'relquad': 'Bound relational chain of depth four; expands to four left-edge analytical relations.',
        'dep': 'Dependent personal-pronoun allomorph after a preposition, contrasting with an adjacent free pronoun.',
        'add': 'Second-position additive clause clitic; preserves addition without asserting temporal sequence or cause.',
        'subend': 'Marks the end of a dependent finite predicate before a matching matrix predicate.',
    }
    for feature, meaning in meanings.items():
        form = MORPHEMES[feature][0]
        lexicon['entries']['kjv_flow_' + feature] = dict(form=form, meaning=meaning, pos='particle',
            semanticId='lex.kjv_flow_' + feature, status='authored', derivationKeys=[],
            roman=language.reading(form), historicalForms=[], register=VERSION,
            origin='Author-directed historical grammar correction, 2026-11-05; bound grammatical form.',
            evidence='Explicitly authored construction; not independent historical attestation.')
    write(PACKAGE / 'lexicon.json', lexicon)
    snapshot = read(SOURCE / 'current-snapshot.json')['snapshot']
    grammar = (PACKAGE / 'grammar.md').read_text(encoding='utf-8')
    rules = []
    for i, part in enumerate(re.split(r'\n## ', grammar)[1:], 1):
        rid = f'kjv281.rule.{i}'; rules.append(rid)
        snapshot['language']['grammar'].append(dict(base(rid, part.splitlines()[0], 'kjv.source', 'Historical correction 281', status='draft'),
            topic='construction', statement=part, morphologyIds=[], exampleIds=[], alternatives=[]))
    for feature, meaning in meanings.items():
        key = 'kjv_flow_' + feature; entry = lexicon['entries'][key]
        snapshot['language']['lexicon'].append(dict(base('kjv281.lex.' + feature, key, 'kjv.source', 'Grammar correction 281', status='draft'),
            headword=entry['form'], orthographyId='thimfora-79', pronunciation=entry['roman'], ipa='', partOfSpeech='particle',
            senses=[dict(id='kjv281.sense.' + feature, definition=meaning, status='draft', citations=[dict(sourceId='kjv.source', locator='Grammar correction 281')])],
            variants=[], etymology=entry['origin'], exampleIds=[], audioLinks=[]))
    snapshot['wiki'].insert(0, dict(id='kjv281-historical-flow', title='KJV 281 · Construct phrases and clause flow', body=grammar, ruleIds=rules))
    units = read(OUT / 'complete-translation-ledger.json')['units']
    snapshot['tests'] = [t for t in snapshot['tests'] if not t['id'].startswith('kjv')]
    for unit in units:
        snapshot['tests'].append(dict(id='kjv281.verse.' + unit['id'], title='KJV 281 · ' + unit['reference'], ruleIds=rules,
            paragraphs=[dict(text=unit['text'], translation=unit['source'], analysis=unit['gloss'] + '\nAuthored analysis: ' + unit['analysis'] + '\nBack-reading: ' + unit['backReading'] + '\nNote: ' + unit['note'])]))
    snapshot['decisions'].append(dict(id='kjv281-historical-flow', status='draft', choice=grammar,
        evidence='Explicit author request 2026-11-05; complete 31,102-verse correction ledger; no modernization.'))
    summary = read(OUT / 'language-delta.json')
    snapshot['research']['kjvHistoricalFlow'] = summary
    validate(snapshot)
    parent_head = read(PARENT / 'manifest.json')['forgeHead']
    project = ForgeProject(SOURCE / 'KJV Bible 0.10-kjv.280.vayforge')
    status = project.status(); previous_branch = status['branch']
    branch = 'kjv-historical-flow-281'
    if any(b['name'] == branch for b in status['branches']):
        raise ValueError('FORGE_BRANCH_ALREADY_EXISTS: inspect before resuming')
    print('Committing historical correction to canonical Forge branch', flush=True)
    status = project.branch(branch, status['generation'], version=parent_head)
    status = project.replace_draft(snapshot, status['generation'])
    status = project.commit('KJV 281 · construct chains, dependent roles and varied clause continuation; complete compact correction', status['generation'])
    head = status['head']
    # Leave the previously selected branch intact, including its unsaved draft.
    project.checkout(previous_branch, status['generation'])
    summary.update(forgeHead=head, forgeBranch=branch, forgeProject=str(project.path), forgeVerseTests=31102,
                   dictionaryGrammaticalEntriesAdded=6, wikiArticlesAdded=1, grammarSectionsAdded=len(rules))
    write(OUT / 'language-delta.json', summary)
    manifest = dict(version=VERSION, policy='never-modernize', status='Author-requested historical grammar correction; publication verification recorded separately.',
        basePackage='data/language/archaic-kjv-280', baseManifestSha256=digest(PARENT / 'manifest.json'),
        baseForgeHead=parent_head, forgeHead=head, compilerPath='data/language/archaic-kjv-281/compiler.py', compilerSha256=digest(PACKAGE / 'compiler.py'),
        files={p.name:digest(p) for p in PACKAGE.iterdir() if p.is_file() and p.name!='manifest.json'})
    write(PACKAGE / 'manifest.json', manifest)
    registry = read(ROOT / 'data/language/historical.json')
    registry['registers'].append(dict(version=VERSION, package='data/language/archaic-kjv-281', manifestSha256=digest(PACKAGE / 'manifest.json'),
        forgeHead=head, policy='never-modernize', status='Historical grammar correction; complete 31,102 verse targets', guide='docs/KJV_ARCHIVE.md'))
    write(ROOT / 'data/language/historical.json', registry); verify_register(VERSION)
    shutil.copyfile(PACKAGE / 'grammar.md', OUT / 'Wiki.md')
    # Browsable complete dictionary, plus the grammar in ordinary local HTML.
    style='<meta charset="utf-8"><style>body{max-width:1000px;margin:3em auto;font:18px/1.6 Georgia}td,th{padding:8px;text-align:left;border-bottom:1px solid #ddd}pre{white-space:pre-wrap}a{color:#145c88}</style>'
    rows=''.join('<tr><td>'+html.escape(k)+'</td><td>'+html.escape(v.get('roman',language.reading(v['form'])))+'</td><td>'+html.escape(v['meaning'])+'</td></tr>' for k,v in sorted(lexicon['entries'].items()))
    (OUT / 'Dictionary.html').write_text(style+'<h1>KJV 281 · Historical dictionary</h1><p>Complete inherited vocabulary plus six bound grammatical forms. No modernization.</p><table><tr><th>Key</th><th>Roman form</th><th>Meaning</th></tr>'+rows+'</table>',encoding='utf-8')
    (OUT / 'Wiki.html').write_text(style+'<h1>KJV 281 · Grammar</h1><pre>'+html.escape(grammar)+'</pre>',encoding='utf-8')
    write(OUT / 'forge-reference.json', dict(project=str(project.path), branch=branch, head=head, parentHead=parent_head))
    print('Published', head, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--prepare', action='store_true'); parser.add_argument('--resume-working', action='store_true'); parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        prepare(args.resume_working)
    if args.publish:
        publish()
