import unittest
from tools.kjv_archive import load_register, read


class DeuteronomyRefugeTests(unittest.TestCase):
    def test_witnesses_protection_and_social_boundaries(self):
        old, _ = load_register('0.10-kjv.28')
        lang, manifest = load_register('0.10-kjv.29')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'deuteronomy-refuge-cases.json')}
        self.assertEqual(141, len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                result = lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'], result['text'])
                self.assertEqual(c['expectedGloss'], result['gloss'])
        checks = {'19-5': ['head from kjv_helve'], '19-6': ['of death worthy he be:pa not'], '19-9': ['kjv_three city:pl more', 'these kjv_three'], '19-15': ['one_num witness', 'two witness:pl', 'kjv_three witness:pl'], '20-15': ['very far'], '20-16': ['nothing that breathe:pr'], '21-7': ['of wepl hand:pl', 'of wepl eye:pl'], '21-20': ['of we:du', 'kjv_glutton'], '22-19': ['hundred kjv_shekel:pl'], '22-25': ['force:pr', 'man only'], '22-26': ['nothing thou do:fu', 'no sin of death worthy'], '22-29': ['five+ten kjv_shekel:pl'], '23-15': ['deliver:fu not'], '23-16': ['he choose:fu'], '23-20': ['stranger', 'kjv_usury thou lend:pr:may'], '24-1': ['kjv_uncleanness_charge'], '24-16': ['for his/own sin']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['deuteronomy-' + ref]['analysis'])
        self.assertNotEqual(lang.compile('i be:pr')['text'], lang.compile('ipl be:pr')['text'])
        self.assertNotEqual(lang.compile('wepl be:pr')['text'], lang.compile('wesg be:pr')['text'])
        self.assertEqual('data/language/archaic-kjv-28', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
