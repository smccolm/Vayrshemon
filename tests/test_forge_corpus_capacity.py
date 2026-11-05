"""Growing historical corpora keep page examples versioned and bounded."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from vayrshemon.forge import ForgeProject, empty_snapshot, validate, MAX_PAGE_TESTS, MAX_WIKI_ARTICLES


def corpus(count):
    snapshot=empty_snapshot()
    snapshot['tests']=[dict(id=f'corpus.verse.{i}',title=f'Historical example {i}',ruleIds=[],
        paragraphs=[dict(text='Rá r×ow.',translation='I am.',analysis='I(sg.) · be(prs.).')]) for i in range(count)]
    return snapshot


class ForgeCorpusCapacityTests(unittest.TestCase):
    def test_snapshot_size_remains_bounded(self):
        snapshot=corpus(1)
        snapshot['research']['largeNote']='x'*4096
        with patch('vayrshemon.forge.MAX_SNAPSHOT_BYTES',1024):
            with self.assertRaisesRegex(ValueError,'FORGE_SNAPSHOT_LIMIT'):
                validate(snapshot)

    def test_large_page_library_preserves_commit_and_portable_history(self):
        snapshot=corpus(MAX_PAGE_TESTS)
        work_root=Path(__file__).resolve().parents[1]/'.local/test-forge-corpus'
        work_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work_root) as work:
            root=Path(work)
            project=ForgeProject.create(root/'corpus.vayforge','Historical corpus',snapshot)
            head=project.status()['head']
            changed=deepcopy(snapshot)
            changed['tests'][-1]['paragraphs'][0]['translation']='I exist.'
            project.replace_draft(changed,project.status()['generation'])
            project.commit('Refine last example',project.status()['generation'])
            bundle=root/'corpus.json';project.export(bundle)
            restored=ForgeProject.restore(bundle,root/'restored.vayforge')
            self.assertEqual(snapshot,restored.read(head)['snapshot'])
            self.assertEqual(changed,restored.read()['snapshot'])
            self.assertEqual(MAX_PAGE_TESTS,len(restored.read()['snapshot']['tests']))

    def test_larger_page_capacity_keeps_bounds_ids_and_reference_validation(self):
        with self.assertRaisesRegex(ValueError,'FORGE_COLLECTION_LIMIT'):
            validate(corpus(MAX_PAGE_TESTS+1))
        snapshot=corpus(2001)
        snapshot['tests'][-1]['id']=snapshot['tests'][0]['id']
        with self.assertRaisesRegex(ValueError,'FORGE_RECORD_ID'):validate(snapshot)
        snapshot=corpus(2001);snapshot['tests'][-1]['ruleIds']=['missing.rule']
        with self.assertRaisesRegex(ValueError,'FORGE_RULE_REFERENCE_MISSING'):validate(snapshot)
        snapshot=empty_snapshot()
        snapshot['wiki']=[dict(id=f'wiki.{i}',title='Article',body='Text',ruleIds=[]) for i in range(MAX_WIKI_ARTICLES+1)]
        with self.assertRaisesRegex(ValueError,'FORGE_COLLECTION_LIMIT'):validate(snapshot)


if __name__=='__main__':unittest.main()
