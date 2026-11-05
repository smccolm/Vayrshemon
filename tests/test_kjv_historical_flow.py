"""Grammatical contrast tests for the explicitly authorized historical correction."""
import unittest
from tools.kjv_historical_flow import PACKAGE, PARENT, compiler, revise, read


class HistoricalFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lang = compiler(PACKAGE)
        cls.old = compiler(PARENT)

    def unit(self, text, reference='Genesis 1:3', identity='01.001.003'):
        return dict(analysis=text, source='', reference=reference, id=identity)

    def test_roles_and_plural_self_are_preserved(self):
        unit = self.unit('to ipl ipl speak:pa.')
        revised, changes = revise(unit)
        self.assertEqual(revised, 'to ipl:dep ipl speak:pa.')
        self.assertEqual(self.lang.compile(revised)['keys'], self.old.compile(unit['analysis'])['keys'])
        self.assertIn('ráun’em', self.lang.compile(revised)['text'])
        for text in ('ipl be:pr', 'wesg be:pr', 'mypl/god', 'ourone/lord', 'holy holy holy'):
            self.assertEqual(self.lang.compile(text), self.old.compile(text))
        with self.assertRaisesRegex(ValueError, 'REQUIRES_PRONOUN'):
            self.lang.compile('army:dep')

    def test_construct_chain_does_not_drop_a_head_or_number(self):
        unit = self.unit('of of of kjv_issachar/child:pl kjv_tribe army', 'Numbers 10:15')
        revised, _ = revise(unit)
        self.assertEqual(revised, 'kjv_issachar/child:pl:g kjv_tribe:g army')
        result = self.lang.compile(revised)
        for key in ('kjv_issachar', 'child', 'kjv_tribe', 'army'):
            self.assertIn(key, result['keys'])
        self.assertEqual(revised.count(':g'), 2)
        self.assertIn(':pl', revised)

    def test_relational_depth_and_maxima_are_distinct(self):
        forms = []
        for depth in (2, 3, 4):
            revised, _ = revise(self.unit('of ' * depth + 'king house army'))
            forms.append(self.lang.compile(revised)['text'])
        self.assertEqual(len(set(forms)), 3)
        for text in forms:
            self.assertEqual(text[0], self.lang.maxima(text)[0])
        with self.assertRaisesRegex(ValueError, 'CONFLICTING_PHRASE'):
            self.lang.compile('king:relpair:reltriple')

    def test_continuation_is_not_a_list_or_temporal_then(self):
        previous = self.unit('he speak:pa.', identity='01.001.002')
        revised, _ = revise(self.unit('and he to she speak:pa.'), previous)
        self.assertEqual(revised, 'he:cont to she speak:pa.')
        self.assertNotIn('then', revised)
        list_unit = self.unit('and gold and silver,')
        self.assertEqual(revise(list_unit, previous)[0], list_unit['analysis'])
        chapter = self.unit('and he speak:pa.', identity='01.002.001')
        self.assertEqual(revise(chapter, previous)[0], chapter['analysis'])
        refrain = self.unit('and he speak:pa.', identity='19.136.002')
        prev = self.unit('he speak:pa.', identity='19.136.001')
        self.assertEqual(revise(refrain, prev)[0], refrain['analysis'])
        self.assertEqual(revise(self.unit('truly truly he speak:pr.'), previous)[0], 'truly truly he speak:pr.')

    def test_clause_boundary_retains_both_predicates(self):
        text = 'i they:a who i:a love:pr love:pr.'
        revised, _ = revise(self.unit(text))
        self.assertIn('love:pr:subend love:pr', revised)
        self.assertEqual(self.lang.compile(revised)['keys'].count('love'), 2)
        with self.assertRaisesRegex(ValueError, 'FINITE_PREDICATE'):
            self.lang.compile('king:subend')
        self.assertEqual(revise(self.unit('holy holy holy'))[0], 'holy holy holy')

    def test_cases_compile_and_original_lexical_forms_do_not_migrate(self):
        for case in read(PACKAGE / 'flow-cases.json'):
            self.assertEqual(self.lang.compile(case['analysis'])['text'], case['text'], case['reference'])
        for key, entry in self.old.lexicon.items():
            self.assertEqual(self.lang.lexicon[key], entry, key)
        self.assertEqual(self.lang.pairs, self.old.pairs)
        self.assertEqual(self.lang.roman, self.old.roman)
        self.assertEqual(self.lang.prefix, self.old.prefix)
        for key, value in self.old.suffix.items():
            self.assertEqual(self.lang.suffix[key], value)


if __name__ == '__main__':
    unittest.main()
