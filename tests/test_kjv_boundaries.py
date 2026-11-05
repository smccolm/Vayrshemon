import unittest

from tools.kjv_archive import load_register, read


class BoundariesRegisterTests(unittest.TestCase):
    def test_historical_categories_roles_and_conditions(self):
        parent, _ = load_register('0.10-kjv.16')
        lang, manifest = load_register('0.10-kjv.17')
        self.assertEqual(parent.lexicon, {k: lang.lexicon[k] for k in parent.lexicon})
        for field in ('pairs', 'suffix', 'possessors', 'roman'):
            self.assertEqual(getattr(parent, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'boundaries-cases.json')}
        self.assertEqual(204, len(cases))
        for case in cases.values():
            with self.subTest(verse=case['id']):
                result = lang.compile(case['analysis'])
                self.assertEqual(case['expectedText'], result['text'])
                self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {
            'leviticus-11-3': ['kjv_hoof:a kjv_divide:pr', 'kjv_cud:a kjv_chew:pr'],
            'leviticus-11-6': ['kjv_hare', 'kjv_cud:a he kjv_chew:pr'],
            'leviticus-11-19': ['bat'],
            'leviticus-11-20': ['all four'],
            'leviticus-11-26': ['split:pp foot have:pr not'],
            'leviticus-11-36': ['fountain or kjv_pit', 'kjv_clean_ritual', 'but'],
            'leviticus-11-37': ['kjv_clean_ritual'],
            'leviticus-11-38': ['water', 'carcass', 'kjv_unclean_ritual'],
            'leviticus-11-44': ['ipl kjv_lord', 'holy ipl be:pr'],
            'leviticus-12-4': ['kjv_three and kjv_three+ten'],
            'leviticus-12-5': ['two week:pl', 'kjv_three+twenty and six'],
            'leviticus-13-13': ['all his/flesh', 'kjv_clean_ritual'],
            'leviticus-13-14': ['kjv_raw_lesion', 'kjv_unclean_ritual'],
            'leviticus-13-31': ['no black hair'],
            'leviticus-13-32': ['no yellow hair'],
            'leviticus-13-33': ['kjv_scall:a he shave:fu not'],
            'leviticus-13-36': ['yellow hair:a priest:n seek:fu not'],
            'leviticus-13-40': ['kjv_bald', 'kjv_clean_ritual'],
            'leviticus-13-55': ['colour:a change:perf not', 'spread:perf not', 'kjv_unclean_ritual'],
            'leviticus-14-3': ['out of camp priest:n go:fu', 'heal:psv:perf'],
            'leviticus-14-8': ['into camp', 'outside his/tent seven day:pl'],
            'leviticus-14-10': ['kjv_three ten:ord part:pl', 'one_num kjv_log_measure'],
            'leviticus-14-15': ['his/own left hand kjv_palm_hand'],
            'leviticus-14-16': ['his/kjv_right_side:m finger', 'his/left hand'],
            'leviticus-14-17': ['upon of kjv_trespass/kjv_offering blood'],
            'leviticus-14-28': ['upon of of kjv_trespass/kjv_offering blood place'],
            'leviticus-14-34': ['ipl give:pr', 'ipl put:pr'],
            'leviticus-14-35': ['to i it seem:pr'],
            'leviticus-14-48': ['house kjv_clean_ritual', 'plague heal:psv:perf'],
            'leviticus-14-53': ['for house kjv_atonement'],
            'leviticus-15-3': ['flow:pr', 'stop:psv:pr'],
            'leviticus-15-13': ['flow:pr water', 'seven day:pl'],
            'leviticus-15-18': ['both themselves:a', 'they wash:fu'],
            'leviticus-15-24': ['kjv_menstrual_flow', 'seven day:pl'],
            'leviticus-15-31': ['mypl/kjv_tabernacle', 'die:pr:may not']}
        for key, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases[key]['analysis'])
        self.assertNotIn('seven', cases['leviticus-15-16']['analysis'])
        for first, second in [('kjv_fish_scale', 'scale'),
                              ('kjv_mole_animal', 'mole'),
                              ('kjv_raw_lesion', 'kjv_raw'),
                              ('kjv_boil_skin', 'boil'),
                              ('kjv_warp_thread', 'warp'),
                              ('kjv_saddle_noun', 'kjv_saddle'),
                              ('one_num', 'one')]:
            self.assertNotEqual(lang.word(first)[1], lang.word(second)[1])
        self.assertEqual('data/language/archaic-kjv-16', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
