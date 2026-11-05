import unittest
from tools.kjv_archive import load_register, read


class KingsDedicationTests(unittest.TestCase):
    def test_quoted_self_collective_hearts_and_precise_material_senses(self):
        old, _ = load_register('0.10-kjv.56')
        lang, manifest = load_register('0.10-kjv.57')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings1-dedication-cases.json')}
        self.assertEqual(117, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        anchors = {
            '7-3': ['four+ten and five kjv_pillar:pl', 'fifteen in row'],
            '7-26': ['two+thousand kjv_bath_measure:pl'],
            '7-31': ['one_num and half kjv_cubit', 'kjv_square not round'],
            '7-33': ['kjv_wheel_hub:pl', 'kjv_wheel_felly:pl', 'kjv_wheel_spoke:pl'],
            '8-9': ['nothing be:pa except two of stone table:pl'],
            '8-16': ['no city:a ipl choose:pa', 'mypl/name'],
            '8-25': ['mypl/sight', 'if thy/child:pl', 'before ipl'],
            '8-26': ['verify:psv:opt i pray:pr'],
            '8-27': ['contain:pr:can not', 'ipl build:perf ?'],
            '8-32': ['kjv_justify_judicial:cv'],
            '8-47': ['wesg sin:perf', 'wesg wickedness:a commit:perf'],
            '8-58': ['ourone/heart:pl'],
            '8-59': ['my/word:pl', 'i kjv_supplication:a make:perf', 'ourone/god'],
            '8-63': ['two+ten+thousand and two+thousand ox:pl', 'hundred+thousand and two+ten+thousand sheep:pl'],
            '8-65': ['seven day:pl and seven day:pl even fourteen'],
            '8-66': ['eight:ord day']}
        for ref, parts in anchors.items():
            for part in parts:
                self.assertIn(part, cases['1-kings-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-56', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
