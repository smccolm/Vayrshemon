"""The Valentino title must retain its whole action and all named victims."""
from copy import deepcopy
import unittest

from tools.prince_working import compile_opening, join_alignment_groups, lexical_distinctions, PARENT
from tools.editorial_language import EditorialLanguage


class PrinceHeadingTests(unittest.TestCase):
    def test_complete_source_heading_and_distinct_verbs(self):
        ledger, additions = compile_opening()
        headings = [u for u in ledger['units'] if 'mergedUnitIds' in u]
        self.assertEqual(len(headings), 2)
        self.assertEqual(headings[0]['source'], headings[1]['source'])
        self.assertEqual(headings[0]['text'], headings[1]['text'])
        self.assertEqual(headings[0]['gloss'], headings[1]['gloss'])
        expected = ('DESCRIPTION OF THE METHODS ADOPTED BY THE DUKE VALENTINO WHEN MURDERING '
                    'VITELLOZZO VITELLI, OLIVEROTTO DA FERMO, THE SIGNOR PAGOLO, '
                    'AND THE DUKE DI GRAVINA ORSINI')
        for h in headings:
            self.assertEqual(h['source'], expected)
            for token in ('description', 'method_practice:pl', 'adopt_practice:psv:m',
                          'murder_targeted:pa', 'vitellotso_vitelli', 'oliveroto_fermo',
                          'pagolo_orsini', 'gravina_orsini'):
                self.assertIn(token, h['analysis'])
            self.assertIn('murder(pst.)', h['gloss'])
            self.assertIn('adopt(pass.,mod.)', h['gloss'])
        language = EditorialLanguage(PARENT/'Language')
        original = deepcopy(language.lexicon)
        words, glosses = lexical_distinctions(language)
        self.assertEqual(language.lexicon, original)
        self.assertNotEqual(words['adopt_practice']['form'], original['use']['form'])
        self.assertNotEqual(words['murder_targeted']['form'], original['murder']['form'])
        self.assertNotEqual(words['murder_targeted']['form'], original['kill']['form'])
        self.assertTrue(all(words[k]['denotation'] and words[k]['connotation']
                            and words[k]['contrasts'] for k in words))

    def test_alignment_groups_fail_closed_on_missing_or_discontinuous_source(self):
        rows = [dict(id=str(i), chapter='one', source=str(i), sourceOffsets=[i*2, i*2+1],
                     analysis='word', lineStart=i+1, lineEnd=i+1) for i in range(3)]
        for ids in (['0','2'], ['0','missing'], ['0','0']):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                join_alignment_groups(rows, [dict(unitIds=ids, reason='test')])
        for change in (dict(chapter='two'), dict(editorialTreatment='Omission'),
                       dict(sourceOffsets=[4,5])):
            broken = deepcopy(rows)
            broken[1].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                join_alignment_groups(broken, [dict(unitIds=['0','1'],reason='test')])
        merged = join_alignment_groups(rows, [dict(unitIds=['0','1'],reason='test')])
        self.assertEqual(rows[2], merged[1])
        self.assertEqual(merged[0]['source'], '0 1')
        self.assertEqual(merged[0]['sourceOffsets'], [0,3])


if __name__ == '__main__':
    unittest.main()
