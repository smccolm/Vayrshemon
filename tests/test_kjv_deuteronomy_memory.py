import unittest
from tools.kjv_archive import load_register, read


class DeuteronomyMemoryTests(unittest.TestCase):
    def test_personas_retrospective_law_and_recorded_sense_repairs(self):
        old, _ = load_register('0.10-kjv.25')
        lang, manifest = load_register('0.10-kjv.26')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'deuteronomy-memory-cases.json')}
        self.assertEqual(219, len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                actual = lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'], actual['text'])
                self.assertEqual(c['expectedGloss'], actual['gloss'])
        checks = {
            '1-23': ['kjv_please_satisfy'],
            '2-5': ['ipl give:fu not', 'foot breadth'],
            '2-27': ['ipl:a', 'kjv_right_side'],
            '2-29': ['ourone/god to wesg'],
            '2-34': ['woman:pl', 'little child:pl'],
            '3-11': ['his/kjv_bedstead', 'nine kjv_cubit:pl', 'four kjv_cubit:pl'],
            '4-12': ['no likeness', 'only voice'],
            '4-48': ['kjv_sion_hermon', 'kjv_hermon'],
            '5-3': ['with ourone/father:pl', 'make:pa not', 'but with wesg'],
            '5-4': ['face to face'],
            '5-14': ['thy/stranger', 'rest:pr:can'],
            '5-15': ['servant thou be:pa', 'therefore'],
            '5-24': ['to wesg', 'wepl hear:perf', 'wepl see:perf'],
            '5-29': ['be:opt:excl', 'mypl/command:pl'],
            '6-4': ['ourone/god one_num kjv_lord'],
            '6-21': ['slave:pl wesg be:pa'],
        }
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['deuteronomy-' + ref]['analysis'])
        corrections = read(lang.folder / 'semantic-corrections.json')['corrections']
        self.assertEqual(19, len(corrections))
        for c in corrections:
            with self.subTest(correction=c['reference']):
                self.assertEqual(c['oldText'], old.compile(c['oldAnalysis'])['text'])
                result = lang.compile(c['newAnalysis'])
                self.assertEqual(c['newText'], result['text'])
                self.assertEqual(c['newGloss'], result['gloss'])
                self.assertNotEqual(c['oldText'], c['newText'])
                self.assertTrue({'please', 'plain'} & set(old.compile(c['oldAnalysis'])['keys']))
                self.assertFalse({'please', 'plain'} & set(result['keys']))
        self.assertEqual('data/language/archaic-kjv-25', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
