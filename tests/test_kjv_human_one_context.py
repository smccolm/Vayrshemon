import unittest
from tools.kjv_archive import load_register, read


class HumanOneContextTests(unittest.TestCase):
    def test_contextual_repairs_preserve_humans_and_cardinal_unity(self):
        before, _ = load_register('0.10-kjv.62')
        lang, manifest = load_register('0.10-kjv.63')
        self.assertEqual(before.lexicon, lang.lexicon)
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(before, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'human-one-context-cases.json')}
        self.assertEqual(203, len(cases))
        changed = 0
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
            changed += case['analysis'] != case['priorAnalysis']
        self.assertEqual(47, changed)
        for ref, phrase in {
            'genesis-19-20': 'city',
            'numbers-7-89': 'he',
            'numbers-36-9': 'one_num',
            '1-samuel-27-1': 'some',
            '2-samuel-14-27': 'one_num',
            '2-samuel-19-14': 'one_num',
            '2-samuel-24-12': 'one_num:a',
        }.items():
            self.assertIn(phrase, cases[ref]['analysis'])
        retained = [c for c in cases.values() if c['priorAnalysis'] == c['analysis']]
        self.assertEqual(156, len(retained))
        self.assertTrue(any(c['id'].startswith('ruth-') for c in retained))
        self.assertEqual('data/language/archaic-kjv-62', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
