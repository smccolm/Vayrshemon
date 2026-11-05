import unittest
from tools.kjv_archive import load_register, read


class NumbersCensusRegisterTests(unittest.TestCase):
    def test_census_populations_and_guarded_contact(self):
        parent, _ = load_register('0.10-kjv.19')
        lang, manifest = load_register('0.10-kjv.20')
        self.assertEqual(parent.lexicon, {k: lang.lexicon[k] for k in parent.lexicon})
        for field in ('pairs', 'suffix', 'possessors', 'roman'):
            self.assertEqual(getattr(parent, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'numbers-census-cases.json')}
        self.assertEqual(188, len(cases))
        for case in cases.values():
            with self.subTest(verse=case['id']):
                result = lang.compile(case['analysis'])
                self.assertEqual(case['expectedText'], result['text'])
                self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {
            '1-14': ['kjv_deuel'], '2-14': ['kjv_reuel_gad'],
            '3-12': ['ipl, behold', 'place ipl take:perf'],
            '3-13': ['both man and beast', 'ipl strike:pa'],
            '3-24': ['kjv_eliasaph_gershon', 'kjv_lael'],
            '3-28': ['eight+thousand and six+hundred'],
            '3-39': ['twenty+thousand and two+thousand'],
            '3-48': ['remain:pr amount'],
            '4-3': ['thirty year:pl', 'fifty year:pl'],
            '4-5': ['kjv_vail_partition', 'kjv_ark_chest'],
            '4-7': ['kjv_table_furniture', 'always bread on it'],
            '4-8': ['kjv_scarlet'], '4-13': ['purple cloth'],
            '4-15': ['after that', 'carry:inf', 'touch:fu:neg'],
            '4-18': ['cut:imp:neg off'],
            '4-19': ['each one to his/service and to his/burden'],
            '4-20': ['to see:inf when holy thing:pl cover:psv:pr'],
            '4-32': ['by name'], '4-44': ['kjv_three+thousand and two+hundred']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['numbers-' + ref]['analysis'])
        for first, second in [('kjv_standard_banner', 'standard'),
                              ('kjv_custody_care', 'kjv_custody'),
                              ('kjv_oversight', 'oversight'),
                              ('kjv_number', 'count'),
                              ('kjv_table_furniture', 'table')]:
            if second in lang.lexicon:
                self.assertNotEqual(lang.word(first)[1], lang.word(second)[1])
        self.assertNotEqual(lang.lexicon['kjv_eliasaph']['meaning'],
                            lang.lexicon['kjv_eliasaph_gershon']['meaning'])
        self.assertEqual('data/language/archaic-kjv-19', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
