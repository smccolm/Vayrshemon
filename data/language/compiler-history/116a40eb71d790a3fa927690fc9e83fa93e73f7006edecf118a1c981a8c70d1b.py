"""Compile authored analyses against the pinned current language, never English.

The versioned package is self-contained: no Inputs, old Forge draft, TSV load
order, or private working directory participates in lexical resolution.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'\{\{[^}]+\}\}|[A-Za-z_][A-Za-z_+/:\-]*|[0-9]+|[^\w\s]')
WORD = re.compile(r'[A-Za-z_][A-Za-z_+/:\-]*')
FINITE = {'pr', 'pa', 'fu', 'perf', 'pp', 'fp', 'prog', 'pprog', 'gn'}
CASE = {'n', 'a', 'd', 'g', 'abl', 'loc', 'all', 'ins'}
PHRASE = {'relpair', 'reltriple', 'relquad', 'dep', 'add', 'cont', 'subend'}


def load_current(root=ROOT):
    pointer = json.loads((Path(root) / 'data/language/current.json').read_text(encoding='utf8'))
    folder = Path(root) / pointer['package']
    manifest_path = folder / 'manifest.json'
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != pointer['manifestSha256']:
        raise ValueError('CURRENT_LANGUAGE_MANIFEST_MISMATCH')
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    compiler = Path(root) / manifest['compilerPath']
    archived = False
    if hashlib.sha256(compiler.read_bytes()).hexdigest() != manifest['compilerSha256']:
        # Older immutable manifests retain their original compiler digest. Keep
        # the exact implementation available when a later language extends it.
        compiler = Path(root) / 'data/language/compiler-history' / (manifest['compilerSha256'] + '.py')
        if not compiler.is_file() or hashlib.sha256(compiler.read_bytes()).hexdigest() != manifest['compilerSha256']:
            raise ValueError('CURRENT_LANGUAGE_COMPILER_MISMATCH: review the compiler change and publish a matching language package')
        archived = True
    for name, expected in manifest['files'].items():
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != expected:
            raise ValueError('LANGUAGE_PACKAGE_HASH_MISMATCH: ' + name)
    if manifest['version'] != pointer['version'] or manifest['forgeHead'] != pointer['forgeHead']:
        raise ValueError('CURRENT_LANGUAGE_VERSION_MISMATCH')
    if archived:
        import importlib.util
        spec = importlib.util.spec_from_file_location('archived_editorial_compiler', compiler)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.EditorialLanguage(folder), pointer
    return EditorialLanguage(folder), pointer


class EditorialLanguage:
    def __init__(self, folder):
        self.folder = Path(folder)
        read = lambda name: json.loads((self.folder / name).read_text(encoding='utf8'))
        self.lexicon = read('lexicon.json')['entries']
        orth = read('orthography.json')
        self.pairs = orth['maximaPairs']
        self.roman = orth['romanBySlot']
        self.letters = set(self.pairs) | set(self.pairs.values())
        morph = read('morphology.json')
        self.suffix = morph['suffixes']
        self.prefix = morph['prefixes']
        self.possessors = morph['possessors']
        self.glosses = morph['glosses']

    def maxima(self, text):
        return self.pairs.get(text[0], text[0]) + text[1:] if text else text

    def reading(self, text):
        return ''.join(self.roman.get(c, c) for c in text)

    def validate_features(self, features):
        fs = set(features)
        if fs - (self.suffix.keys() | self.prefix.keys()):
            raise ValueError('UNKNOWN_FEATURE: ' + ','.join(sorted(fs - (self.suffix.keys() | self.prefix.keys()))))
        if len(fs) != len(features):
            raise ValueError('DUPLICATE_FEATURE')
        if len(fs & {'relpair', 'reltriple', 'relquad'}) > 1 or len(fs & {'add', 'cont'}) > 1:
            raise ValueError('CONFLICTING_PHRASE_CLITIC')
        if 'subend' in fs and not fs & FINITE:
            raise ValueError('DEPENDENT_CLAUSE_NEEDS_FINITE_PREDICATE')
        # Phrase clitics follow the host's complete word, including its force.
        first_phrase = next((i for i, f in enumerate(features) if f in PHRASE), len(features))
        if any(f not in PHRASE for f in features[first_phrase:]):
            raise ValueError('INFLECTION_AFTER_PHRASE_CLITIC')
        if len(fs & CASE) > 1:
            raise ValueError('CONFLICTING_CASE')
        if len(fs & FINITE) > 1:
            raise ValueError('CONFLICTING_TENSE_ASPECT')
        if len(fs & {'pl', 'du'}) > 1:
            raise ValueError('CONFLICTING_NUMBER')
        if len(fs & {'cv', 'cvds', 'inf', 'imp'}) > 1:
            raise ValueError('CONFLICTING_CLAUSE_FORM')
        if fs & {'cv', 'cvds', 'imp'} and fs & FINITE:
            raise ValueError('FINITE_NONFINITE_CONFLICT')
        if 'inf' in fs and fs & FINITE and fs & FINITE != {'perf'}:
            raise ValueError('INFINITIVE_TENSE_CONFLICT')
        if len(fs & {'rep', 'app'}) > 1:
            raise ValueError('UNLICENSED_EVIDENTIAL_STACK')
        if fs & {'rep', 'app', 'juss'} and not fs & FINITE:
            raise ValueError('FINITE_ANCHOR_REQUIRED')
        if len(fs & {'may', 'can', 'must', 'should'}) > 1:
            raise ValueError('UNLICENSED_MODAL_STACK')
        if len(fs & {'opt', 'juss', 'imp'}) > 1:
            raise ValueError('CONFLICTING_FORCE')
        # Prefixes have no surface suffix position. Voice ordering is meaningful:
        # passive+causative and causative+passive must not be sorted alike.
        suffix_order = [f for f in features if f in self.suffix and f not in PHRASE]
        anchor = next((i for i, f in enumerate(suffix_order) if f in FINITE | {'cv', 'cvds', 'inf', 'imp'}), None)
        if anchor is not None and any(f in {'psv', 'caus', 'refl', 'rec'} for f in suffix_order[anchor + 1:]):
            raise ValueError('VOICE_AFTER_CLAUSE_ENDING')
        if 'excl' in fs and suffix_order[-1] != 'excl':
            raise ValueError('EXCLAMATIVE_NOT_FINAL')
        clause_order = [f for f in suffix_order if f != 'excl']
        if any(f in {'rep', 'app', 'juss'} and i != len(clause_order) - 1 for i, f in enumerate(clause_order)):
            raise ValueError('CLAUSE_PARTICLE_NOT_FINAL')
        if 'inf' in fs and 'perf' in fs and suffix_order.index('perf') > suffix_order.index('inf'):
            raise ValueError('PERFECT_INFINITIVE_ORDER')

    def word(self, token):
        chain = token.split('/')
        stem, *features = chain[-1].split(':')
        self.validate_features(features)
        if 'dep' in features and (len(chain) != 1 or stem not in {'he', 'she', 'they', 'it', 'i', 'ipl', 'wesg', 'we', 'wepl', 'you', 'thou', 'thee'}):
            raise ValueError('DEPENDENT_FORM_REQUIRES_PRONOUN')
        keys = stem.split('+')
        try:
            entries = [self.lexicon[k] for k in keys]
        except KeyError as err:
            raise ValueError('UNKNOWN_LEXICAL_KEY: ' + str(err)) from err
        form = ''.join(e['form'] for e in entries)
        gloss = '-'.join(self.glosses.get(k, k.replace('_', '-')) for k in keys)
        used = list(keys)
        for poss in reversed(chain[:-1]):
            pf, pg, pkeys = self.word(self.possessors.get(poss, poss))
            form = pf + '’' + form
            gloss = poss.replace('+', '-') + '-' + gloss
            used += pkeys
        if entries[0]['pos'] == 'proper':
            form = self.maxima(form)
        labels = []
        for feat in features:
            if feat in self.prefix:
                p, g = self.prefix[feat]
                form = p + form
            else:
                p, g = self.suffix[feat]
                form += p
            labels.append(g)
        if labels:
            gloss += '(' + ','.join(labels) + ')'
        return form, gloss, used

    def compile(self, analysis, initial=True):
        if '!' in analysis:
            raise ValueError('EXCLAMATION_REQUIRES_EXCL_FORM: use the expressive :excl construction and a sentence boundary')
        output, gloss, used = [], [], []
        for t in TOKEN.findall(analysis):
            if t.startswith('{{'):
                form = t[2:-2]
                if not set(form) <= self.letters | set(' ,.!?’-'):
                    raise ValueError('INVALID_FEIGNED_SPEECH_SLOTS')
                output.append(self.maxima(form) if initial else form)
                gloss.append('[feigned speech]')
                initial = form.endswith(('.', '!', '?'))
            elif WORD.fullmatch(t):
                colon = t.endswith(':')
                form, g, keys = self.word(t.rstrip(':'))
                if initial:
                    form, initial = self.maxima(form), False
                output.append(form)
                gloss.append(g)
                used += keys
                if colon:
                    output[-1] += ':'
                    gloss[-1] += ':'
                    initial = True
            elif t.isdigit():
                output.append(t)
                gloss.append(t)
            elif t in '.!?;,:':
                if output:
                    output[-1] += t
                    gloss[-1] += t
                else:
                    output.append(t)
                    gloss.append(t)
                if t in '.!?':
                    initial = True
            else:
                output.append(t)
                gloss.append(t)
        return dict(text=' '.join(output), gloss=' · '.join(gloss), keys=used)

    def compile_units(self, units):
        result, previous = [], ''
        for u in units:
            continued = u.get('continuesParagraph', u.get('part', 0) > 0)
            initial = not continued or bool(re.search(r'[.!?]\s*\]?[ ]*$', previous))
            result.append(dict(deepcopy(u), **self.compile(u['analysis'], initial=initial)))
            previous = u['analysis']
        return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Check the current package and print its identity.')
    parser.add_argument('--analysis', help='Compile an authored target-order analysis (not English).')
    args = parser.parse_args()
    lang, pin = load_current()
    print(json.dumps(dict(version=pin['version'], head=pin['forgeHead'], semanticKeys=len(lang.lexicon)), ensure_ascii=True))
    if args.analysis:
        print(json.dumps(lang.compile(args.analysis), ensure_ascii=True, indent=2))
