import unittest
from tools.kjv_archive import load_register, read


class SamuelCovenantFlightTests(unittest.TestCase):
    def test_speaker_shifts_historical_senses_and_source_quantities(self):
        old, _ = load_register('0.10-kjv.45')
        lang, manifest = load_register('0.10-kjv.46')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'samuel-covenant-flight-cases.json')}
        self.assertEqual(111, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {'18-4': ['his/kjv_bow'], '18-7': ['thousand:pl', 'ten+thousand:pl'], '18-10': ['from god evil spirit', 'kjv_prophesy:pa'], '18-17': ['my/daughter more old'], '18-25': ['hundred'], '18-27': ['two+hundred', 'full kjv_number:ev'], '19-6': ['he slay:psv:fu not'], '19-13': ['kjv_bolster'], '19-17': ['to i he say:pa', 'why thou:a i kill:pr:should'], '20-11': ['we:du'], '20-20': ['kjv_three arrow:pl'], '20-25': ['kjv_jonathan rise:pa'], '20-29': ['ourone/kjv_family'], '20-36': ['arrow:a he shoot:pa'], '20-39': ['boy know:pa not'], '20-40': ['his/weapon:pl:a'], '20-42': ['both of we:du'], '21-2': ['ipl send:pr', 'my/servant:pl:a i appoint:perf'], '21-5': ['from wepl woman:pl', 'about these kjv_three day:pl'], '21-13': ['mad feign:pa', 'kjv_scrabble:pa', 'kjv_saliva']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases["1-samuel-" + ref]["analysis"])
        self.assertEqual('data/language/archaic-kjv-45', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
