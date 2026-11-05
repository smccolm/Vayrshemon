import unittest
from tools.kjv_archive import load_register, read


class KingsDivisionTests(unittest.TestCase):
    def test_personal_royal_voice_conditions_and_cardinal_repairs(self):
        old, _ = load_register('0.10-kjv.57')
        lang, manifest = load_register('0.10-kjv.58')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings1-division-cases.json')}
        self.assertEqual(115, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        repairs = read(lang.folder / 'kings1-cardinal-repairs.json')
        self.assertEqual(15, len(repairs))
        for repair in repairs:
            key = '1-kings-' + repair['ref'].replace(':', '-')
            self.assertEqual(repair['after'], cases[key]['analysis'])
            self.assertNotEqual(lang.compile(repair['before'])['text'], cases[key]['expectedText'])
        self.assertIn('one woman', cases['1-kings-3-17']['analysis'])
        self.assertIn('one_num house', cases['1-kings-3-17']['analysis'])
        self.assertIn('each proportion', cases['1-kings-7-36']['analysis'])
        anchors = {
            '9-6': ['you or your/child:pl', 'ipl set:perf'],
            '9-13': ['to ipl thou give:perf my/brother'],
            '9-14': ['six+two+ten kjv_talent_weight:pl'],
            '10-7': ['i believe:pa not', 'my/eye:pl'],
            '10-16': ['kjv_target_inventory', 'six+hundred kjv_shekel:pl'],
            '10-17': ['kjv_three kjv_pound_weight:pl'],
            '10-28': ['linen yarn'],
            '11-3': ['seven+hundred wife:pl', 'kjv_three+hundred kjv_concubine:pl'],
            '11-29': ['they:du two alone'],
            '11-31': ['ten part:pl', 'ipl kjv_rend:fu', 'ten kjv_tribe:pl'],
            '11-32': ['one_num kjv_tribe'],
            '11-33': ['ipl:a they forsake:perf'],
            '11-38': ['if to all', 'then with thou ipl be:fu'],
            '11-39': ['but forever not']}
        for ref, parts in anchors.items():
            for part in parts:
                self.assertIn(part, cases['1-kings-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-57', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
