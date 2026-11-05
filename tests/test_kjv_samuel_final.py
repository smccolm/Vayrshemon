import unittest
from tools.kjv_archive import load_register, read


class SamuelFinalTests(unittest.TestCase):
    def test_speaker_shifts_historical_senses_and_source_quantities(self):
        old, _ = load_register('0.10-kjv.47')
        lang, manifest = load_register('0.10-kjv.48')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'samuel-final-cases.json')}
        self.assertEqual(117, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {'26-6': ['kjv_ahimelech_hittite kjv_hittite', 'kjv_abishai of kjv_zeruiah son to kjv_joab brother', 'with thou i go:fu'], '26-11': ['my/hand:a i stretch:pr:should', 'we:du', 'kjv_cruse'], '26-12': ['no man', 'deep sleep from kjv_lord'], '26-22': ['behold:imp:excl'], '27-3': ['every man with his/kjv_household', 'his/two wife:pl', 'kjv_ahinoam_jezreel', 'of kjv_nabal wife'], '27-7': ['full one year and four month:pl'], '27-8': ['kjv_geshurite:pl', 'kjv_gezrite:pl', 'kjv_amalekites:pl', 'kjv_shur'], '27-10': ['kjv_raid:perf', 'of kjv_judah kjv_south', 'kjv_jerahmeelite:pl', 'kjv_kenite:pl'], '27-11': ['neither man nor woman alive kjv_david save:pa', 'lest about wesg', 'so his/manner be:fu'], '28-6': ['answer:pa not', 'dream:pl', 'kjv_urim', 'prophet:pl'], '28-8': ['disguise:pa', 'two man:pl with he', 'kjv_divine:imp'], '28-12': ['kjv_samuel:a woman see:pa', 'kjv_saul thou be:pr'], '28-13': ['god:pl:a out of earth rise:cv i see:pa'], '28-14': ['old man', 'with mantle', 'kjv_saul perceive:pa'], '28-17': ['to he kjv_lord do:perf', 'out of thy/hand kingdom:a', 'to kjv_david'], '28-24': ['fat kjv_calf', 'kjv_flour:a', 'kjv_knead:pa', 'not kjv_leaven_raise:psv'], '29-3': ['these day:pl or these year:pl', 'no fault:a'], '29-4': ['with wesg', 'to wesg kjv_adversary', 'kjv_reconcile_relation', 'head:pl'], '29-9': ['as of god angel', 'prince:pl say:perf', 'with wesg'], '30-8': ['ipl pursue:fu', 'ipl overtake:fu', 'without fail all:a recover:fu'], '30-10': ['four+hundred', 'two+hundred', 'so faint'], '30-12': ['of fig:pl cake piece:a', 'two kjv_fruit_cluster:pl of kjv_raisin:pl', 'kjv_three day:pl and kjv_three night:pl'], '30-14': ['kjv_cherethite:pl', 'kjv_caleb', 'wesg kjv_invade:pa', 'wesg burn:caus:pa'], '30-17': ['from kjv_twilight', 'of next day evening', 'four+hundred young man:pl', 'kjv_camel:pl'], '30-22': ['with wepl', 'wepl give:fu not', 'every man his/wife and his/child:pl'], '30-23': ['to wesg', 'wesg:a preserve:perf', 'ourone/hand'], '30-24': ['his/part', 'by kjv_baggage', 'equal they kjv_divide:fu'], '30-27': ['kjv_bethel', 'kjv_ramoth_south', 'kjv_jattir'], '31-2': ['kjv_jonathan', 'kjv_abinadab_saul', 'kjv_melchishua'], '31-4': ['will:pa not', 'greatly afraid', 'upon it fall:pa'], '31-6': ['his/kjv_three son:pl', 'all his/man:pl', 'same day together'], '31-8': ['on next day', 'his/kjv_three son:pl', 'fall:pp they find:pa'], '31-10': ['kjv_ashtaroth_divine', 'kjv_bethshan wall'], '31-13': ['their/bone:pl', 'under kjv_tree', 'seven day:pl kjv_fast:pa']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases["1-samuel-" + ref]["analysis"])
        self.assertEqual('data/language/archaic-kjv-47', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
