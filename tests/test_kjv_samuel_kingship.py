import unittest
from tools.kjv_archive import load_register, read


class SamuelKingshipTests(unittest.TestCase):
    def test_speaker_shifts_historical_senses_and_source_quantities(self):
        old, _ = load_register('0.10-kjv.42')
        lang, manifest = load_register('0.10-kjv.43')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'samuel-kingship-cases.json')}
        self.assertEqual(114, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {'6-4': ['five gold kjv_emerods:pl and five gold mouse:pl', 'one_num plague'], '6-9': ['but if not', 'chance which to wesg happen:pa'], '6-19': ['five+ten+thousand and seven+ten'], '7-3': ['kjv_ashtaroth_divine'], '7-5': ['i pray:fu'], '7-13': ['no more', 'all of kjv_samuel day:pl'], '8-7': ['ipl:a they reject:perf'], '8-13': ['kjv_perfumer:pl', 'cook:ag:pl', 'bake:ag:pl'], '8-16': ['young man:pl and your/ass:pl'], '8-18': ['kjv_lord hear:fu not'], '9-8': ['kjv_shekel fourth part:a i have:pr', 'of we:du way'], '9-9': ['to kjv_seer wepl go:inf'], '9-16': ['to ipl their/cry:ev come:perf'], '9-19': ['kjv_seer i be:pr', 'you:du eat:fu'], '9-27': ['before we:du pass:inf servant:a'], '10-3': ['kjv_three of bread kjv_loaf:pl'], '10-4': ['two of bread kjv_loaf:pl'], '10-19': ['over wesg king:a'], '10-22': ['kjv_baggage'], '10-24': ['save:opt:excl']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['1-samuel-' + ref]['analysis'])
        for ref in ('7-5', '9-8', '9-19', '9-27', '10-8'):
            self.assertNotIn('ipl', cases['1-samuel-' + ref]['analysis'])
        self.assertNotEqual(lang.lexicon['kjv_ashtaroth']['semanticId'],lang.lexicon['kjv_ashtaroth_divine']['semanticId'])
        self.assertNotEqual(lang.lexicon['kjv_abel']['semanticId'],lang.lexicon['kjv_abel_stone']['semanticId'])
        self.assertEqual('data/language/archaic-kjv-42', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
