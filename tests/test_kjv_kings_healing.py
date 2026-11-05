import unittest
from tools.kjv_archive import load_register, read


class KingsHealingTests(unittest.TestCase):
    def test_private_speech_royal_letters_pairs_and_false_report(self):
        prior, _ = load_register('0.10-kjv.64')
        lang, manifest = load_register('0.10-kjv.65')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings2-healing-cases.json')}
        self.assertEqual(71, len(cases))
        for c in cases.values():
            result = lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'], result['text'])
            self.assertEqual(c['expectedGloss'], result['gloss'])
        for ref, parts in {
            '4-1': ['my/two son:pl:a', 'slave:pl be:inf'],
            '4-10': ['we:du make:opt', 'we:du set:opt'],
            '4-19': ['my/head:excl my/head:excl'],
            '4-22': ['one of young man:pl', 'one_num of ass:pl:a'],
            '4-27': ['from i it:a kjv_lord hide:perf'],
            '4-31': ['before they:du', 'child awake:perf not'],
            '4-33': ['upon they:du door:a shut:pa'],
            '4-35': ['seven time:pl sneeze:pa'],
            '4-41': ['kjv_flour:a'],
            '5-5': ['ipl send:fu', 'six+thousand'],
            '5-6': ['mypl/servant:a to thou ipl send:perf'],
            '5-7': ['god i be:pr'],
            '5-14': ['seven time:pl in kjv_jordan plunge:pa'],
            '5-18': ['kjv_rimmon_deity', 'kjv_lean_body:pr'],
            '5-22': ['my/master i:a send:perf say:cv', 'one_num kjv_talent_weight'],
            '5-23': ['in two bag:pl', 'they:du they:a carry:pa'],
            '5-25': ['thy/servant anywhere go:pa not'],
            '5-27': ['thy/descendant:pl', 'white as snow'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['2-kings-' + ref]['analysis'])
        self.assertNotIn('kjv_gourd', lang.compile(cases['2-kings-4-39']['analysis'])['keys'])
        self.assertEqual('data/language/archaic-kjv-64', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
