import unittest
from tools.kjv_archive import load_register, read


class KingsSubjectionTests(unittest.TestCase):
    def test_royal_submission_personal_inquiry_and_contextual_senses(self):
        prior, _ = load_register('0.10-kjv.69')
        lang, manifest = load_register('0.10-kjv.70')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings2-subjection-cases.json')}
        self.assertEqual(58, len(cases))
        for c in cases.values():
            result = lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'], result['text'])
            self.assertEqual(c['expectedGloss'], result['gloss'])
        for ref, parts in {
            '15-5': ['of kjv_leprosy man', 'separate:psv house'],
            '15-8': ['six month:pl'],
            '15-13': ['kjv_uzziah_amaziah', 'full month'],
            '15-16': ['with child be:pa he kjv_rend:pa up'],
            '15-19': ['thousand kjv_talent_weight:pl of silver'],
            '15-20': ['demand:pa', 'of each man fifty kjv_shekel:pl'],
            '15-25': ['kjv_argob_person and kjv_arieh'],
            '15-30': ['twenty:ord year of kjv_jotham_azariah'],
            '15-33': ['sixteen year:pl'],
            '16-3': ['his/son:a through fire pass:caus:pa'],
            '16-6': ['kjv_jew:pl:a', 'kjv_syrian:pl'],
            '16-7': ['ipl thy/servant and thy/son', 'ipl:a save:imp'],
            '16-8': ['as gift'],
            '16-10': ['of altar form and its/pattern:a'],
            '16-11': ['by time king kjv_ahaz_jotham'],
            '16-15': ['for i by it kjv_consult:inf'],
            '16-17': ['of base:pl kjv_border:pl:a', 'of kjv_brass ox:pl'],
            '16-18': ['kjv_sabbath_covert', 'for king of kjv_assyria'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['2-kings-' + ref]['analysis'])
        self.assertNotIn('ipl', cases['2-kings-16-15']['analysis'])
        self.assertEqual('data/language/archaic-kjv-69', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
