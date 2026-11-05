import unittest
from tools.kjv_archive import load_register, read


class KingsSuccessionTests(unittest.TestCase):
    def test_speakers_actual_pairs_quantities_and_narrative_scope(self):
        prior, _ = load_register('0.10-kjv.63')
        lang, manifest = load_register('0.10-kjv.64')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings2-succession-cases.json')}
        self.assertEqual(70, len(cases))
        for c in cases.values():
            result = lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'], result['text'])
            self.assertEqual(c['expectedGloss'], result['gloss'])
        for ref, parts in {
            '1-2': ['sickness i recover:fu'],
            '1-6': ['to wesg meet:inf'],
            '1-10': ['if of god man i be:pr'],
            '1-17': ['kjv_jehoram_ahab', 'kjv_jehoram_jehoshaphat'],
            '2-9': ['of thy/spirit double part'],
            '2-11': ['they:du:a apart separate:pa', 'by kjv_whirlwind'],
            '2-12': ['my/father:excl my/father:excl', 'two piece:pl'],
            '2-16': ['wesg pray:pr', 'lest perhaps'],
            '2-21': ['these water:pl:a ipl heal:perf'],
            '2-24': ['two female bear_animal:pl', 'forty and two child:pl:a kjv_rend:pa'],
            '3-4': ['hundred+thousand kjv_ram:pl:a with kjv_wool give:pa'],
            '3-7': ['ipl go:fu up', 'mypl/people'],
            '3-11': ['wepl ask:pr:may'],
            '3-19': ['kjv_tree:a fall:caus:fu'],
            '3-23': ['they say:pa', 'one another:a they strike:perf'],
            '3-27': ['his/eldest son:a', 'against kjv_israel great indignation be:pa'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['2-kings-' + ref]['analysis'])
        bear_keys = lang.compile(cases['2-kings-2-24']['analysis'])['keys']
        self.assertNotIn('kill', bear_keys)
        self.assertNotIn('die', bear_keys)
        self.assertEqual('data/language/archaic-kjv-63', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
