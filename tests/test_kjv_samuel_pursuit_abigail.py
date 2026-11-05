import unittest
from tools.kjv_archive import load_register, read


class SamuelPursuitAbigailTests(unittest.TestCase):
    def test_speaker_shifts_historical_senses_and_source_quantities(self):
        old, _ = load_register('0.10-kjv.46')
        lang, manifest = load_register('0.10-kjv.47')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'samuel-pursuit-abigail-cases.json')}
        self.assertEqual(118, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {'22-13': ['you:du conspire:perf', 'thou and of kjv_jesse son'], '22-18': ['eight+ten and five', 'linen kjv_ephod'], '22-21': ['kjv_saul slay:pp'], '22-22': ['i know:pa', 'death:a i cause:perf'], '23-2': ['ipl go:fu', 'kjv_keilah:a save:imp'], '23-3': ['afraid wepl be:pr', 'wepl come:pr'], '23-4': ['kjv_lord he:a answer:pa', 'ipl deliver:fu'], '23-11': ['he come:fu down'], '23-12': ['i and my/man:pl:a', 'thou:a they deliver:fu up'], '23-14': ['every day', 'god deliver:pa not'], '23-19': ['with wesg', 'kjv_hachilah', 'kjv_south of kjv_jeshimon'], '23-23': ['with you:pl i go:fu', 'kjv_judah thousand:pl', 'ipl search:fu'], '24-3': ['sheepfold:pl', 'his/foot:pl:a cover:inf', 'kjv_cave side:pl'], '24-4': ['man:pl to he say:pa', 'ipl deliver:fu', 'kjv_skirt_garment:a secretly cut:pa off'], '25-7': ['i hear:perf', 'with wesg', 'wesg harm:pa not'], '25-8': ['wepl come:pr', 'thy/son kjv_david'], '25-18': ['two+hundred kjv_loaf:pl', 'two of wine kjv_bottle:pl', 'five sheep prepare:psv', 'five kjv_measure_portion:pl', 'hundred of kjv_raisin kjv_fruit_cluster:pl', 'two+hundred of fig cake:pl'], '25-21': ['ipl keep:perf', 'to ipl he repay:perf'], '25-22': ['to of kjv_david enemy:pl god do:opt', 'piss:pr', 'ipl leave:pr'], '25-33': ['my/own hand myself:a'], '25-37': ['his/heart die:pa', 'like stone'], '25-38': ['about ten day:pl', 'kjv_lord strike:pa', 'he die:pa'], '25-43': ['kjv_ahinoam_jezreel', 'both of they his/wife:pl'], '25-44': ['kjv_laish_person', 'kjv_gallim', 'of kjv_david wife:a']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases["1-samuel-" + ref]["analysis"])
        self.assertEqual('data/language/archaic-kjv-46', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
