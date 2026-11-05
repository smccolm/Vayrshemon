import unittest
from tools.kjv_archive import load_register, read


class OfferingsRegisterTests(unittest.TestCase):
    def test_status_axes_roles_and_pronoun_attribution(self):
        parent, _ = load_register('0.10-kjv.15')
        lang, manifest = load_register('0.10-kjv.16')
        self.assertEqual(parent.lexicon, {k: lang.lexicon[k] for k in parent.lexicon})
        for field in ('pairs', 'suffix', 'possessors', 'roman'):
            self.assertEqual(getattr(parent, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'offerings-cases.json')}
        self.assertEqual(252, len(cases))
        for case in cases.values():
            with self.subTest(verse=case['id']):
                result = lang.compile(case['analysis'])
                self.assertEqual(case['expectedText'], result['text'])
                self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {
            'leviticus-1-3': ['kjv_male without kjv_blemish'],
            'leviticus-1-5': ['he kill:fu', 'priest:pl', 'kjv_sprinkle:fu'],
            'leviticus-1-16': ['kjv_crop_bird', 'feather:pl'],
            'leviticus-3-1': ['kjv_male or female'],
            'leviticus-3-11': ['food it be:pr'],
            'leviticus-4-7': ['sweet kjv_incense', 'burn:pp kjv_offering altar bottom'],
            'leviticus-4-23': ['kjv_male'],
            'leviticus-4-28': ['female'],
            'leviticus-5-2': ['kjv_unclean_ritual and guilty'],
            'leviticus-5-11': ['kjv_ephah ten:ord part', 'no oil', 'neither any kjv_frankincense'],
            'leviticus-6-5': ['kjv_principal_amount', 'five:ord part more:a', 'to he to who it belong:pr'],
            'leviticus-6-17': ['mypl/kjv_offering:pl', 'ipl give:perf'],
            'leviticus-6-20': ['ten:ord part', 'half of it in morning and half of it at night'],
            'leviticus-6-30': ['kjv_reconcile_ritual', 'eat:psv:fu'],
            'leviticus-7-13': ['with kjv_leaven bread'],
            'leviticus-7-34': ['ipl take:perf'],
            'leviticus-8-29': ['of kjv_moses part'],
            'leviticus-8-31': ['as i command:pa'],
            'leviticus-8-35': ['i command:psv:pr'],
            'leviticus-10-3': ['ipl sanctify:psv:fu', 'ipl glorify:psv:fu'],
            'leviticus-10-10': ['holy and kjv_unholy_profane', 'kjv_unclean_ritual and kjv_clean_ritual'],
            'leviticus-10-14': ['thy/daughter:pl', 'kjv_clean_ritual place'],
            'leviticus-10-18': ['bring:psv:pa not', 'eat:pp:should', 'as i command:pa'],
            'leviticus-10-19': ['to i happen:perf', 'i eat:pp:cond', 'accept:psv:pp:cond?']}
        for key, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases[key]['analysis'])
        self.assertNotIn('kjv_rump', cases['leviticus-3-14']['analysis'])
        self.assertNotIn('drink', cases['leviticus-10-1']['analysis'])
        for left, right in [('kjv_unclean_ritual', 'unclean'),
                            ('kjv_unholy_profane', 'kjv_unclean_ritual'),
                            ('kjv_fry_food', 'fry'), ('kjv_crop_bird', 'crop'),
                            ('kjv_memorial_portion', 'kjv_memorial')]:
            self.assertNotEqual(lang.word(left)[1], lang.word(right)[1])
        self.assertEqual('data/language/archaic-kjv-15', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
