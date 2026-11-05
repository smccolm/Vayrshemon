import unittest
from tools.kjv_archive import load_register, read


class KingsAccessionTests(unittest.TestCase):
    def test_identity_fractions_and_entrusted_money(self):
        prior, _ = load_register('0.10-kjv.67')
        lang, manifest = load_register('0.10-kjv.68')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings2-accession-cases.json')}
        self.assertEqual(78, len(cases))
        for c in cases.values():
            result = lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'], result['text'])
            self.assertEqual(c['expectedGloss'], result['gloss'])
        for ref, parts in {
            '10-4': ['wepl stand:fu'],
            '10-5': ['wesg thy/servant:pl'],
            '10-6': ['if you of ipl', 'mypl/voice', 'seven+ten person:pl'],
            '10-9': ['i against my/master conspire:pa'],
            '10-13': ['wepl brother:pl', 'wesg to of king child:pl'],
            '10-14': ['they:a alive take:pa', 'two and forty men'],
            '10-19': ['in cunning', 'worship:ag:pl:a he destroy:pr:may'],
            '10-24': ['four+twenty men', 'his/life for of he life'],
            '10-27': ['kjv_latrine_house'],
            '10-30': ['mypl/heart', 'four:ord generation'],
            '11-5': ['kjv_third_share'],
            '11-6': ['kjv_third_share at gate of kjv_sur_gate'],
            '11-7': ['two part:pl', 'go:pr forth'],
            '11-14': ['betray:ev:excl betray:ev:excl'],
            '11-15': ['in house of kjv_lord she slay:psv:opt not'],
            '12-9': ['as one into house', 'its/kjv_lid'],
            '12-10': ['money:a they:du put:pa and reckon:pa'],
            '12-13': ['vessel:pl make:psv:pa not'],
            '12-15': ['with men they reckon:pa not', 'faithfully'],
            '12-16': ['kjv_trespass money and sin money', 'of priest:pl'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['2-kings-' + ref]['analysis'])
        self.assertNotIn('kjv_third_share', cases['2-kings-11-7']['analysis'])
        self.assertNotIn('tell', cases['2-kings-12-10']['analysis'])
        self.assertEqual('data/language/archaic-kjv-67', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
