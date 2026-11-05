import unittest
from tools.kjv_archive import load_register, read


class JudgesSamsonTests(unittest.TestCase):
    def test_pair_messenger_and_different_collective_speakers(self):
        old, _ = load_register('0.10-kjv.38')
        lang, manifest = load_register('0.10-kjv.39')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'judges-samson-cases.json')}
        self.assertEqual(97, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {
            '12-14': ['thirty kjv_nephew_descendant:pl'],
            '13-5': ['deliver:inf he begin:fu'],
            '13-8': ['to we:du', 'we:du do:fu'],
            '13-11': ['i be:pr'],
            '13-16': ['i eat:fu not', 'to kjv_lord'],
            '13-22': ['god:a we:du see:perf'],
            '13-23': ['of we:du hand:pl', 'receive:cond:pp not', 'show:cond:pp'],
            '14-4': ['know:pa not', 'occasion:a'],
            '14-8': ['carcass'],
            '14-15': ['seven:ord day', 'wepl burn:caus:pr'],
            '15-11': ['kjv_three+thousand', 'over wesg ruler:pl'],
            '15-13': ['wepl kill:fu not', 'two new kjv_cord:pl'],
            '15-19': ['which in jaw be:pa'],
            '16-5': ['every one_num of wepl', 'eleven+hundred'],
            '16-7': ['seven green kjv_with:pl'],
            '16-13': ['seven kjv_hairlock:pl', 'with web thou weave:pr.'],
            '16-19': ['for man she call:pa', 'he:a she cause:pa'],
            '16-20': ['kjv_lord from he depart:pp he know:pa not'],
            '16-24': ['ourone/country', 'many of wepl:a'],
            '16-27': ['upon roof about kjv_three+thousand'],
            '16-28': ['my/two eye:pl'],
            '16-31': ['twenty year:pl'],
        }
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['judges-' + ref]['analysis'])
        for ref in ('13-11', '13-13', '13-14', '13-16', '13-18'):
            self.assertNotIn('ipl', cases['judges-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-38', manifest['basePackage'])
        self.assertEqual(1, len(read(lang.folder / 'semantic-corrections.json')))


if __name__ == '__main__':
    unittest.main()
