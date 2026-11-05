import unittest
from tools.kjv_archive import load_register, read


class DeuteronomyPossessionTests(unittest.TestCase):
    def test_inner_speakers_and_ordinary_meat_are_not_flattened(self):
        old, _ = load_register('0.10-kjv.26')
        lang, manifest = load_register('0.10-kjv.27')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'deuteronomy-possession-cases.json')}
        self.assertEqual(161, len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                actual = lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'], actual['text'])
                self.assertEqual(c['expectedGloss'], actual['gloss'])
        checks = {
            '7-4': ['from ipl:a follow:ev'],
            '7-9': ['thousand generation:pl'],
            '7-17': ['more than ipl'],
            '7-22': ['by little and little', 'beast:pl'],
            '8-17': ['mypl/power', 'for ipl'],
            '9-4': ['mypl/kjv_righteousness', 'ipl:a'],
            '9-12': ['thy/people'],
            '9-26': ['thy/people and thine/inheritance'],
            '9-28': ['wesg:a', 'because they:a he hate:pa'],
            '10-6': ['kjv_mosera', 'there kjv_aaron die:pa'],
            '10-16': ['of your/heart kjv_foreskin', 'kjv_circumcise:imp'],
            '10-17': ['kjv_favour_partiality:pr not', 'kjv_bribe'],
            '10-19': ['stranger:a love:imp'],
            '11-14': ['first rain and later rain', 'ipl give:fu'],
            '12-8': ['wepl do:pr', 'every man'],
            '12-15': ['kjv_unclean_ritual and kjv_clean_ritual'],
            '12-17': ['eat:pr:may not'],
            '12-18': ['eat:pr:must'],
            '12-20': ['flesh:a i eat:fu'],
            '12-23': ['blood life be:pr'],
            '12-30': ['likewise i do:fu'],
        }
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['deuteronomy-' + ref]['analysis'])
        self.assertEqual(lang.lexicon['kjv_ebal']['form'], lang.lexicon['kjv_ebal_mountain']['form'])
        self.assertNotEqual(lang.lexicon['kjv_ebal']['semanticId'], lang.lexicon['kjv_ebal_mountain']['semanticId'])
        self.assertEqual('data/language/archaic-kjv-26', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
