import unittest

from tools.kjv_archive import load_register, read


class AtonementRegisterTests(unittest.TestCase):
    def test_source_roles_conditions_and_measure_senses(self):
        parent, _ = load_register('0.10-kjv.17')
        lang, manifest = load_register('0.10-kjv.18')
        self.assertEqual(parent.lexicon, {k: lang.lexicon[k] for k in parent.lexicon})
        for field in ('pairs', 'suffix', 'possessors', 'roman'):
            self.assertEqual(getattr(parent, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'atonement-cases.json')}
        self.assertEqual(146, len(cases))
        for case in cases.values():
            with self.subTest(verse=case['id']):
                result = lang.compile(case['analysis'])
                self.assertEqual(case['expectedText'], result['text'])
                self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {
            '5-11': ['kjv_ephah_measure ten:ord part'],
            '6-20': ['kjv_ephah_measure ten:ord part', 'half of it in morning'],
            '16-8': ['one_num kjv_lot for kjv_lord', 'other kjv_lot for kjv_scapegoat'],
            '16-10': ['alive present:psv:fu', 'with he kjv_atonement'],
            '16-21': ['both his/hand:pl', 'head they:a put:cv', 'fit man'],
            '16-22': ['all their/kjv_iniquity:pl', 'land not inhabit:psv:pp', 'let:fu go'],
            '16-29': ['seven:ord month', 'ten:ord day', 'your/soul:pl:a you:pl kjv_afflict:fu'],
            '16-34': ['once each year'],
            '17-11': ['of flesh life in blood', 'ipl give:perf'],
            '17-14': ['of all flesh life of it blood'],
            '18-9': ['of thy/father daughter or of thy/mother daughter'],
            '18-21': ['thy/kjv_seedline', 'through fire to kjv_molech'],
            '19-4': ['kjv_cast_metal:pp kjv_god:pl'],
            '19-20': ['she whip:psv:fu', 'they to death put:psv:fu not', 'because free she be:pa not'],
            '19-23': ['kjv_three year:pl'],
            '19-24': ['four:ord year'],
            '19-25': ['five:ord year'],
            '19-36': ['kjv_righteous balance:pl', 'kjv_righteous kjv_ephah_measure'],
            '20-2': ['kjv_stone_person:fu'],
            '20-18': ['woman who her/sickness:a have:pr'],
            '20-20': ['without child:pl they die:fu'],
            '20-21': ['without child:pl they be:fu'],
            '20-26': ['to ipl holy', 'of ipl you:pl be:pr:should']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['leviticus-' + ref]['analysis'])
        for ref in ['5-11', '6-20', '19-36']:
            self.assertNotIn('kjv_ephah ', cases['leviticus-' + ref]['analysis'])
        self.assertNotEqual(lang.word('kjv_ephah')[1], lang.word('kjv_ephah_measure')[1])
        self.assertNotIn('stone:caus', cases['leviticus-20-2']['analysis'])
        self.assertEqual('data/language/archaic-kjv-17', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
