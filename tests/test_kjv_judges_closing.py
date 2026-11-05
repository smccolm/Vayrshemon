import unittest
from tools.kjv_archive import load_register, read


class JudgesClosingTests(unittest.TestCase):
    def test_corporate_voices_testimony_and_oath_distinctions(self):
        old, _ = load_register('0.10-kjv.39')
        lang, manifest = load_register('0.10-kjv.40')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'judges-closing-cases.json')}
        self.assertEqual(147, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {
            '17-3': ['to kjv_lord', 'kjv_graven image and melt:psv image'],
            '17-4': ['two+hundred', 'kjv_founder_metal'],
            '18-9': ['against they wesg go:pr:may', 'land:a wepl see:perf'],
            '18-24': ['my/god:pl whom i make:pa'],
            '18-30': ['kjv_gershom son of kjv_manasseh son'],
            '19-9': ['he and his/kjv_concubine and his/servant'],
            '19-18': ['wepl pass:pr', 'to of kjv_lord house i go:pr'],
            '19-25': ['to they she:a bring:pa forth', 'all night until morning'],
            '19-27': ['her/hand:pl upon kjv_threshold'],
            '20-5': ['i:a slay:inf intend:pa', 'rape:perf that dead she be:pr'],
            '20-8': ['wesg any one of wepl'],
            '20-23': ['mypl/brother ipl go:fu'],
            '20-28': ['mypl/brother ipl go:fu or ipl cease:fu', 'into thy/hand ipl deliver:fu'],
            '20-35': ['twenty+thousand and five+thousand and hundred'],
            '20-46': ['twenty+thousand and five+thousand man:pl'],
            '21-6': ['kjv_regret_loss:pa'],
            '21-12': ['four+hundred young virgin:pl'],
            '21-14': ['they suffice:pa not'],
            '21-21': ['every man catch:imp'],
            '21-22': ['wepl reserve:pa not', 'you:pl give:pa not'],
            '21-25': ['in his/own eye:pl kjv_right_conduct'],
        }
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['judges-' + ref]['analysis'])
        self.assertEqual(3, cases['judges-20-28']['analysis'].count('ipl'))
        self.assertNotIn('dead', cases['judges-19-26']['analysis'])
        self.assertNotIn('kjv_moses', cases['judges-18-30']['analysis'])
        for ref in ('19-11', '19-12', '19-13', '19-18', '19-19', '19-28'):
            self.assertNotIn('we:du', cases['judges-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-39', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
