import unittest
from tools.kjv_archive import load_register, read


class SamuelEarlyWarsTests(unittest.TestCase):
    def test_speaker_shifts_historical_senses_and_source_quantities(self):
        old, _ = load_register('0.10-kjv.43')
        lang, manifest = load_register('0.10-kjv.44')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'samuel-early-wars-cases.json')}
        self.assertEqual(115, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {'11-2': ['kjv_covenant:a ipl make:fu', 'all your/kjv_right_side eye:pl'], '12-4': ['wepl:a thou kjv_defraud:perf not'], '12-11': ['kjv_bedan'], '13-1': ['one_num year:a rule:pa', 'two year:pl:a he rule:pp'], '13-5': ['thirty+thousand chariot:pl and six+thousand horse+man:pl'], '13-21': ['kjv_file_tool'], '14-9': ['we:du', 'wepl'], '14-10': ['we:du', 'wepl'], '14-18': ['kjv_ark'], '14-27': ['hear:pa not', 'kjv_honeycomb'], '14-37': ['ipl go:fu down', 'answer:pa not'], '14-43': ['only little honey:a i taste:pa', 'i die:inf must:pr'], '14-45': ['people rescue:pa'], '14-52': ['all of kjv_saul day:pl']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases["1-samuel-" + ref]["analysis"])
        self.assertEqual('data/language/archaic-kjv-43', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
