import unittest
from tools.kjv_archive import load_register, read


class NumbersRefugeTests(unittest.TestCase):
    def test_refuge_limits_personas_and_human_tribute_remain_explicit(self):
        parent, _ = load_register('0.10-kjv.24')
        lang, manifest = load_register('0.10-kjv.25')
        self.assertEqual(parent.lexicon, {k: lang.lexicon[k] for k in parent.lexicon})
        for field in ('pairs', 'suffix', 'possessors', 'roman'):
            self.assertEqual(getattr(parent, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'numbers-refuge-cases.json')}
        self.assertEqual(228, len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                result = lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'], result['text'])
                self.assertEqual(c['expectedGloss'], result['gloss'])
        checks = {
            '31-18': ['know:perf not', 'for yourselves'],
            '31-40': ['sixteen+thousand', 'thirty and two person:pl'],
            '31-49': ['ourone/kjv_charge_custody', 'of wesg not one_num man'],
            '32-30': ['in of kjv_canaan land kjv_possession:pl they have:fu'],
            '33-56': ['to you:pl as to they', 'ipl do:fu'],
            '35-15': ['stranger', 'kjv_sojourn:pr person'],
            '35-22': ['without enmity', 'without ambush'],
            '35-25': ['until of high priest death'],
            '35-30': ['one_num witness', 'testify:fu not'],
            '35-31': ['no ransom'],
            '35-32': ['no ransom', 'until of priest death'],
            '36-11': ['their/father/brother:pl/son:pl'],
        }
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['numbers-' + ref]['analysis'])
        self.assertNotEqual(lang.lexicon['kjv_hur']['semanticId'],
                            lang.lexicon['kjv_hur_midian']['semanticId'])
        self.assertEqual('data/language/archaic-kjv-24', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
