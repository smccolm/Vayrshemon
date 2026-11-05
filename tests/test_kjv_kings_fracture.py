import unittest
from tools.kjv_archive import load_register, read

class KingsFractureTests(unittest.TestCase):
    def test_quote_centres_bodies_deception_and_unchanged_ancestry(self):
        old, _ = load_register('0.10-kjv.58')
        lang, manifest = load_register('0.10-kjv.59')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings1-fracture-cases.json')}
        self.assertEqual(98, len(cases))
        for c in cases.values():
            actual = lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'], actual['text'])
            self.assertEqual(c['expectedGloss'], actual['gloss'])
        anchors = {
            '12-4': ['ourone/yoke', 'kjv_lighten:imp', 'wesg serve:fu'],
            '12-9': ['wesg answer:pr:may', 'to i speak:perf', 'upon wesg'],
            '12-11': ['kjv_scourge_lash:pl', 'ipl kjv_chastise:fu'],
            '12-21': ['hundred+thousand and eight+ten+thousand'],
            '12-24': ['from ipl', 'your/brother:pl'],
            '12-27': ['i:a they kill:fu'],
            '12-29': ['one_num:a'],
            '13-7': ['with i home', 'to thou ipl give:fu'],
            '13-18': ['angel to i', 'but to he he kjv_lie_false:pa'],
            '13-20': ['they:du'],
            '13-28': ['carcass:a eat:pp not nor ass:a kjv_rend:pp'],
            '13-30': ['my/brother:excl'],
            '13-33': ['one of'],
            '14-7': ['thou:a prince make:pa'],
            '14-11': ['he:a who in city die:pr dog:pl eat:fu', 'he:a who in field die:pr of air bird:pl eat:fu'],
            '14-15': ['kjv_uproot:fu'],
            '14-21': ['four+ten and one_num', 'seventeen'],
            '14-24': ['kjv_sodomite_source_label:pl'],
            '14-27': ['they:a entrust:pa']}
        for ref, parts in anchors.items():
            for part in parts:
                self.assertIn(part, cases['1-kings-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-58', manifest['basePackage'])

if __name__ == '__main__':
    unittest.main()
