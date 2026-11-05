import unittest
from tools.kjv_archive import load_register, read


class SamuelOpeningTests(unittest.TestCase):
    def test_personal_calls_divine_promises_and_unreconciled_counts(self):
        old, _ = load_register('0.10-kjv.41')
        lang, manifest = load_register('0.10-kjv.42')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'samuel-opening-cases.json')}
        self.assertEqual(119, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {'1-24': ['kjv_three kjv_bullock:pl', 'one_num kjv_ephah_measure'], '1-25': ['kjv_bullock:a they slay:pa'], '2-5': ['barren seven:a bear:perf'], '2-21': ['kjv_three son:pl and two daughter:pl'], '2-25': ['because kjv_lord they:a slay:inf will:pa'], '2-30': ['forever before ipl', 'but now kjv_lord'], '2-36': ['i:a please'], '3-4': ['here i be:pr'], '3-10': ['speak:imp for thy/servant'], '3-14': ['forever purge:psv:fu not'], '4-7': ['god into camp'], '4-8': ['god:pl'], '4-15': ['nine+ten and eight'], '4-18': ['forty year:pl'], '5-4': ['both of his/hand:pl kjv_palm_hand:pl', 'kjv_stump'], '5-10': ['wesg and ourone/people:a slay:inf']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['1-samuel-' + ref]['analysis'])
        for ref in ('1-15', '2-36', '3-4', '3-10'):
            self.assertNotIn('ipl', cases['1-samuel-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-41', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
