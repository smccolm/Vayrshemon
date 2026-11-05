import unittest
from tools.kjv_archive import load_register, read


class NumbersDisputeRegisterTests(unittest.TestCase):
    def test_voice_roles_and_uncomfortable_source_distinctions(self):
        parent, _ = load_register('0.10-kjv.21')
        lang, manifest = load_register('0.10-kjv.22')
        self.assertEqual(parent.lexicon, {k: lang.lexicon[k] for k in parent.lexicon})
        for field in ('pairs', 'suffix', 'possessors', 'roman'):
            self.assertEqual(getattr(parent, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'numbers-disputes-cases.json')}
        self.assertEqual(220, len(cases))
        for case in cases.values():
            with self.subTest(verse=case['id']):
                result = lang.compile(case['analysis'])
                self.assertEqual(case['expectedText'], result['text'])
                self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {
            '11-6': ['ourone/soul', 'ourone/eye:pl'],
            '11-12': ['i conceive:perf', 'i beget:perf', 'kjv_nurse:pr father'],
            '11-14': ['i carry:pr:can not'],
            '11-21': ['i be:pr', 'ipl give:fu'],
            '11-25': ['cease:pa not'], '11-26': ['of those who write:psv:pa'],
            '11-29': ['be:opt:excl'], '11-32': ['ten kjv_homer:pl'],
            '12-2': ['we:du'], '12-6': ['iplself', 'mypl/word'],
            '12-11': ['i thee:a beseech:pr', 'we:du sin:perf'],
            '12-15': ['journey:pa not until'],
            '13-16': ['kjv_oshea', 'kjv_jehoshua'],
            '13-27': ['wepl'], '13-30': ['wesg'],
            '14-7': ['we:du'], '14-8': ['wesg'],
            '14-20': ['ipl pardon:perf'], '14-27': ['ipl endure:fu'],
            '14-34': ['each day for year', 'mypl/kjv_promise_breach'],
            '15-6': ['two ten:ord part:pl', 'kjv_three:ord part'],
            '15-9': ['kjv_three ten:ord part:pl', 'half kjv_hin'],
            '15-34': ['kjv_custody', 'declare:psv:pa not'],
            '15-36': ['he die:pa'], '15-38': ['kjv_fringe', 'blue ribbon'],
            '16-12': ['we:du come:fu not'],
            '16-22': ['one_num man', 'all kjv_congregation'],
            '16-27': ['wife:pl', 'little child:pl'],
            '16-30': ['into kjv_pit alive'], '16-34': ['wesg'],
            '16-48': ['between dead and living', 'plague stop:psv:pa'],
            '16-49': ['fourteen+thousand and seven+hundred', 'besides']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['numbers-' + ref]['analysis'])
        self.assertEqual(2, cases['numbers-14-2']['analysis'].count('die:pp:opt:excl'))
        self.assertEqual(2, cases['numbers-15-41']['analysis'].count('ipl kjv_lord'))
        self.assertNotIn('kjv_omer', cases['numbers-11-32']['analysis'])
        self.assertNotIn('kjv_aaron kjv_leprous', cases['numbers-12-10']['analysis'])
        for first, second in [('kjv_mortar_grind', 'kjv_mortar'),
                              ('kjv_stick_wood', 'stick'),
                              ('kjv_lean_land', 'thin')]:
            self.assertNotEqual(lang.word(first)[1], lang.word(second)[1])
        self.assertEqual('data/language/archaic-kjv-21', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
