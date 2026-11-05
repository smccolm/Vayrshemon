import unittest
from tools.kjv_archive import load_register, read


class KingsLimitedRescueTests(unittest.TestCase):
    def test_named_kings_actual_pair_and_limited_sign(self):
        prior, _ = load_register('0.10-kjv.68')
        lang, manifest = load_register('0.10-kjv.69')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings2-limited-rescue-cases.json')}
        self.assertEqual(54, len(cases))
        for c in cases.values():
            result = lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'], result['text'])
            self.assertEqual(c['expectedGloss'], result['gloss'])
        for ref, parts in {
            '13-7': ['fifty kjv_horseman:pl', 'ten+thousand kjv_foot_soldier:pl'],
            '13-14': ['my/father:excl my/father:excl'],
            '13-15': ['kjv_bow and arrow:pl'],
            '13-18': ['kjv_three time:pl he strike:pa and cease:pa'],
            '13-19': ['five or six time:pl', 'strike:pp:should', 'but kjv_three time:pl thou strike:fu'],
            '13-21': ['bone:pl:a touch:pa', 'he revive:pa'],
            '13-23': ['destroy:inf will:pa not', 'as yet'],
            '14-6': ['of murderer:pl child:pl:a he slay:pa not', 'each man for his/own sin'],
            '14-8': ['we:du one another:a in face look:opt'],
            '14-9': ['thy/daughter:a to my/son', 'thistle:a tread:pa down'],
            '14-13': ['kjv_jehoash_jehoahaz king of kjv_israel', 'son of kjv_jehoash_judah', 'four+hundred kjv_cubit:pl'],
            '14-14': ['kjv_hostage:pl'],
            '14-23': ['forty and one_num year:pl'],
            '14-25': ['kjv_plain_land', 'kjv_jonah son of kjv_amittai'],
            '14-27': ['name:a from under heaven erase:inf'],
            '14-28': ['which to kjv_judah belong:pa for kjv_israel'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['2-kings-' + ref]['analysis'])
        self.assertNotIn('mypl/', cases['2-kings-14-9']['analysis'])
        self.assertEqual('data/language/archaic-kjv-68', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
