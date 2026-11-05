import unittest
from tools.kjv_archive import load_register, read


class JudgesGideonTests(unittest.TestCase):
    def test_quoted_selves_and_preserved_difficult_readings(self):
        old, _ = load_register('0.10-kjv.36')
        lang, manifest = load_register('0.10-kjv.37')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'judges-gideon-cases.json')}
        self.assertEqual(157, len(cases))
        for case in cases.values():
            with self.subTest(verse=case['id']):
                result = lang.compile(case['analysis'])
                self.assertEqual(case['expectedText'], result['text'])
                self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {
            '6-13': ['with wesg', 'wesg:a forsake:perf'],
            '6-14': ['kjv_lord upon he look:pa', 'ipl send:perf not?'],
            '6-15': ['i save:fu'],
            '6-39': ['dry only upon kjv_fleece', 'upon all ground dew'],
            '7-2': ['against ipl boast:pr', 'mypl/own hand ipl:a save:perf'],
            '7-3': ['twenty+thousand and two+thousand', 'ten+thousand remain'],
            '7-5': ['as dog kjv_lap_drink:pr'],
            '7-19': ['middle kjv_watch_period', 'watch:ev:a but newly'],
            '8-7': ['kjv_rend:fu'],
            '8-21': ['upon we:du'],
            '8-22': ['over wesg'],
            '8-25': ['wepl give:fu'],
            '9-5': ['seven+ten person:pl', 'one_num stone', 'kjv_jotham'],
            '9-8': ['over wesg'],
            '9-13': ['god and man:a cheer:pr'],
            '9-23': ['god evil spirit:a'],
            '9-28': ['wesg serve:pr:should?'],
            '9-29': ['i remove:cond'],
            '9-34': ['four company:pl'],
            '9-43': ['kjv_three company:pl'],
            '9-49': ['about thousand man:pl and woman:pl'],
            '9-52': ['near to of kjv_tower door'],
            '9-53': ['kjv_millstone piece:a'],
        }
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['judges-' + ref]['analysis'])
        self.assertEqual(2, cases['judges-6-39']['analysis'].count('once'))
        self.assertNotIn('tear:fu', cases['judges-8-7']['analysis'])
        self.assertNotIn('close', cases['judges-9-52']['analysis'])
        self.assertEqual('data/language/archaic-kjv-36', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
