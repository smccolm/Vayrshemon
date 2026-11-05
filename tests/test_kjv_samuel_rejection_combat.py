import unittest
from tools.kjv_archive import load_register, read


class SamuelRejectionCombatTests(unittest.TestCase):
    def test_speaker_shifts_historical_senses_and_source_quantities(self):
        old, _ = load_register('0.10-kjv.44')
        lang, manifest = load_register('0.10-kjv.45')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'samuel-rejection-combat-cases.json')}
        self.assertEqual(116, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {'15-3': ['kjv_infant and suck:cv one', 'spare:imp not'], '15-6': ['ipl destroy:pr'], '15-11': ['ipl kjv_change_mind:pr'], '15-15': ['thy/god', 'wesg completely destroy:perf'], '15-29': ['nor kjv_change_mind:fu'], '15-33': ['as sword woman:pl:a'], '15-35': ['kjv_lord kjv_change_mind:pa'], '16-2': ['say:imp i come:perf'], '16-11': ['wepl sit:fu'], '16-14': ['from kjv_lord evil spirit'], '16-16': ['of wepl lord', 'skilled play:ag'], '17-4': ['six kjv_cubit:pl and kjv_span'], '17-5': ['five+thousand'], '17-6': ['kjv_target_shield'], '17-7': ['six+hundred'], '17-9': ['wesg be:fu', 'ourone/servant:pl'], '17-10': ['ipl kjv_defy:pr', 'we:du fight:pr:may'], '17-29': ['reason there be:pr not'], '17-40': ['five smooth stone:pl'], '17-50': ['he:a slay:pa'], '17-51': ['he:a slay:pa'], '17-55': ['of whom son']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases["1-samuel-" + ref]["analysis"])
        self.assertEqual('data/language/archaic-kjv-44', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
