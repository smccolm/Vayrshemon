import unittest
from tools.kjv_archive import load_register, read


class DeuteronomyLawTests(unittest.TestCase):
    def test_authority_debt_and_witness_scope(self):
        old, _ = load_register('0.10-kjv.27')
        lang, manifest = load_register('0.10-kjv.28')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'deuteronomy-law-cases.json')}
        self.assertEqual(134, len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                result = lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'], result['text'])
                self.assertEqual(c['expectedGloss'], result['gloss'])
        checks = {
            '13-2': ['happen:pr', 'wepl'],
            '13-6': ['we:du'],
            '13-14': ['truth', 'certain'],
            '14-26': ['strong drink'],
            '15-2': ['kjv_exact_debt:fu not'],
            '15-3': ['kjv_foreigner', 'kjv_exact_debt:pr:may'],
            '15-16': ['i go:fu not'],
            '15-17': ['female servant', 'his/ear'],
            '16-19': ['kjv_bribe', 'blind make:pr'],
            '17-6': ['two witness:pl', 'kjv_three witness:pl', 'one_num witness', 'put:psv:fu not'],
            '17-14': ['over ipl ipl set:fu'],
            '18-15': ['like to i'],
            '18-16': ['mypl/god', 'ipl hear:opt not'],
            '18-18': ['mypl/word:pl', 'ipl raise:fu'],
            '18-21': ['wesg know:fu'],
            '18-22': ['nor happen:pr', 'afraid thou be:fu not'],
        }
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['deuteronomy-' + ref]['analysis'])
        self.assertNotEqual(lang.compile('i be:pr')['text'], lang.compile('ipl be:pr')['text'])
        self.assertNotEqual(lang.compile('wepl be:pr')['text'], lang.compile('wesg be:pr')['text'])
        self.assertEqual('data/language/archaic-kjv-27', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
