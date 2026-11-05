import unittest
from tools.kjv_archive import load_register, read


class NumbersVowRegisterTests(unittest.TestCase):
    def test_conditional_bodies_vows_and_nested_speakers(self):
        parent, _ = load_register('0.10-kjv.20')
        lang, manifest = load_register('0.10-kjv.21')
        self.assertEqual(parent.lexicon, {k: lang.lexicon[k] for k in parent.lexicon})
        for field in ('pairs', 'suffix', 'possessors', 'roman'):
            self.assertEqual(getattr(parent, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'numbers-vows-cases.json')}
        self.assertEqual(232, len(cases))
        for case in cases.values():
            with self.subTest(verse=case['id']):
                result = lang.compile(case['analysis'])
                self.assertEqual(case['expectedText'], result['text'])
                self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {
            '5-14': ['she defile:psv:pr, or if', 'she defile:psv:pr not'],
            '5-15': ['kjv_ephah_measure ten:ord part', 'no oil', 'nor kjv_frankincense'],
            '5-21': ['thy/thigh:a rot:inf', 'thy/belly:a swell:inf'],
            '5-22': ['amen, amen'], '5-28': ['conceive:fu'],
            '5-31': ['man free be:fu', 'woman her/kjv_iniquity:a carry:fu'],
            '6-2': ['either man or woman'],
            '6-10': ['two kjv_turtledove:pl or two young kjv_pigeon:pl'],
            '6-12': ['day:pl that before be:pa lose:psv:fu'],
            '6-20': ['after that wine:a kjv_nazarite drink:pr:may'],
            '6-24': ['thee:a kjv_lord:n bless:imp'],
            '6-27': ['mypl/name', 'ipl bless:fu'],
            '7-9': ['none:a', 'their/kjv_shoulder:pl'],
            '7-85': ['two+thousand and four+hundred'],
            '8-17': ['for iplself'], '8-24': ['twenty and five year:pl'],
            '8-26': ['with their/brother:pl', 'no service:a do:fu'],
            '9-7': ['wesg defile:psv:pr'], '9-8': ['i hear:fu'],
            '9-11': ['fourteen:ord day of kjv_second month'],
            '9-13': ['in journey be:pr not', 'keep:pr not'],
            '10-7': ['alarm:a sound:fu not'],
            '10-29': ['ipl give:fu', 'wesg journey:pr'],
            '10-30': ['i go:fu not'],
            '10-31': ['wesg:a leave:imp:neg', 'i thee:a pray:pr'],
            '10-32': ['wesg do:fu']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['numbers-' + ref]['analysis'])
        for ref in ['5-21', '5-22', '5-27']:
            self.assertNotIn('miscarriage', cases['numbers-' + ref]['analysis'])
        self.assertNotEqual(lang.word('kjv_hair_lock')[1], lang.word('lock')[1])
        self.assertEqual('data/language/archaic-kjv-20', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
