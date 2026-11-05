"""Keep a whole corpus's grammar and its references through native/Forge storage."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from jsonschema import Draft202012Validator, ValidationError
from vayrshemon import language
from vayrshemon.language_contracts import DATA, REVISION, COLLECTION_LIMITS
from vayrshemon.forge import ForgeProject, empty_snapshot, validate


def corpus():
    snapshot = empty_snapshot()
    snapshot['language']['grammar'] = [dict(
        id=f'grammar.{i:04d}', label=f'Historical rule {i}', status='draft',
        citations=[], notes='', topic='construction', statement=f'Rule evidence {i}',
        morphologyIds=[], exampleIds=[], alternatives=[]
    ) for i in range(2001)]
    snapshot['wiki'] = [dict(id='corpus.notes', title='Corpus grammar',
                            body='Historical documentation', ruleIds=['grammar.2000'])]
    return snapshot


class GrammarCapacityTests(unittest.TestCase):
    def test_over_2000_rules_preserve_revision_wiki_and_forge_history(self):
        snapshot = corpus()
        state = language.initial()
        language.append_revision(state, snapshot['language'], 'Whole corpus')
        state = json.loads(json.dumps(state))
        language.validate_state(state)
        self.assertEqual(language.dataset(state), snapshot['language'])
        base = Path(__file__).resolve().parents[1] / '.local/test-grammar-capacity'
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as folder:
            root = Path(folder)
            project = ForgeProject.create(root / 'source.vayforge', 'Grammar capacity', snapshot)
            original_head = project.status()['head']
            changed = deepcopy(snapshot)
            changed['language']['grammar'][-1]['statement'] = 'Refined final rule evidence'
            project.replace_draft(changed, project.status()['generation'])
            project.commit('Refine a rule beyond the former limit', project.status()['generation'])
            project.export(root / 'history.json')
            restored = ForgeProject.restore(root / 'history.json', root / 'restored.vayforge')
            self.assertEqual(restored.read(original_head)['snapshot'], snapshot)
            self.assertEqual(restored.read()['snapshot'], changed)
            self.assertEqual(restored.status()['head'], project.status()['head'])

    def test_expanded_grammar_still_rejects_duplicates_missing_refs_and_excess(self):
        snapshot = corpus()
        snapshot['language']['grammar'][-1]['id'] = snapshot['language']['grammar'][0]['id']
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_LANGUAGE_RECORD: grammar'):
            validate(snapshot)
        snapshot = corpus()
        snapshot['wiki'][0]['ruleIds'] = ['grammar.missing']
        with self.assertRaisesRegex(ValueError, 'FORGE_RULE_REFERENCE_MISSING'):
            validate(snapshot)
        limit = COLLECTION_LIMITS['grammar']
        self.assertEqual(limit, 10000)
        schema = DATA['properties']['grammar']
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate([corpus()['language']['grammar'][0]] * (limit + 1))
        refs = REVISION['properties']['collections']['properties']['grammar']
        self.assertEqual(refs['maxItems'], limit)
        with self.assertRaises(ValidationError):
            Draft202012Validator(refs).validate(['0' * 64] * (limit + 1))


if __name__ == '__main__':
    unittest.main()
