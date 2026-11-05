import unittest
from tools.kjv_archive import load_register, read


class KingsSiegeTests(unittest.TestCase):
    def test_collective_purpose_individual_risk_and_nested_strategy(self):
        prior, _ = load_register('0.10-kjv.65')
        lang, manifest = load_register('0.10-kjv.66')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings2-siege-cases.json')}
        self.assertEqual(53, len(cases))
        for c in cases.values():
            result = lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'], result['text'])
            self.assertEqual(c['expectedGloss'], result['gloss'])
        for ref, parts in {
            '6-2': ['wesg pray:pr thou', 'each man beam:a'],
            '6-5': ['beam:a fall:caus:pa', 'kjv_axe head into water fall:pa'],
            '6-11': ['which of wepl'],
            '6-15': ['we:du do:fu'],
            '6-21': ['they:a ipl strike:fu ? they:a ipl strike:fu'],
            '6-25': ['four+twenty', 'kjv_fourth_share of kjv_cab_measure', 'of dove kjv_dung'],
            '6-28': ['this woman to i say:pa', 'we:du eat:pr:may'],
            '6-29': ['my/son:a we:du boil:pa', 'her/son:a she hide:perf'],
            '6-33': ['messenger to he come:pa down and he say:pa'],
            '7-4': ['wesg fall:opt', 'wepl:a they kill:pr'],
            '7-9': ['wesg do:pr not well', 'ourone/peace:a'],
            '7-12': ['ipl show:fu', 'say:cv when', 'wesg catch:fu'],
            '7-13': ['five of horse:pl:a', 'who consume:psv:perf'],
            '7-14': ['two chariot horse:pl:a'],
            '7-17': ['lord:a on whose hand he kjv_lean_body:pa', 'he die:pa'],
            '7-18': ['two kjv_measure_portion:pl of kjv_barley for one_num kjv_shekel and of fine kjv_flour'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['2-kings-' + ref]['analysis'])
        self.assertNotIn('two chariot:pl', cases['2-kings-7-14']['analysis'])
        self.assertEqual('data/language/archaic-kjv-65', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
