import unittest
from tools.kjv_archive import load_register, read

class KingsCarmelTests(unittest.TestCase):
    def test_dual_plural_collective_lone_and_divine_speakers(self):
        old, _ = load_register('0.10-kjv.60')
        lang, manifest = load_register('0.10-kjv.61')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings1-carmel-cases.json')}
        self.assertEqual(67, len(cases))
        for c in cases.values():
            result = lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'], result['text'])
            self.assertEqual(c['expectedGloss'], result['gloss'])
        anchors = {
            '18-5': ['we:du find:pr:may'],
            '18-6': ['they:du', 'one_num way'],
            '18-19': ['four+hundred and five+ten', 'four+hundred'],
            '18-22': ['i even i only'],
            '18-23': ['to wepl two kjv_bullock:pl'],
            '18-26': ['kjv_baal:excl wesg:a hear:imp'],
            '18-34': ['two:ord time it:a do:imp', 'kjv_three:ord time it:a do:imp'],
            '18-39': ['kjv_lord he god be:pr kjv_lord he god be:pr'],
            '18-40': ['of they one escape:opt not', 'they:a slay:pa'],
            '19-2': ['to i god:pl do:opt', 'ipl make:fu not'],
            '19-5': ['he lie:pa and sleep:pa'],
            '19-10': ['i even i only remain:pr'],
            '19-11': ['in wind kjv_lord be:pa not', 'in earthquake kjv_lord be:pa not'],
            '19-12': ['in fire kjv_lord be:pa not', 'quiet small voice'],
            '19-14': ['i even i only remain:pr'],
            '19-17': ['kjv_jehu_nimshi slay:fu', 'kjv_elisha slay:fu'],
            '19-18': ['for ipl seven+thousand:a in kjv_israel ipl keep:perf'],
            '19-19': ['twelve of ox:pl yoke:pl', 'twelve:ord']}
        for ref, parts in anchors.items():
            for part in parts:
                self.assertIn(part, cases['1-kings-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-60', manifest['basePackage'])

if __name__ == '__main__':
    unittest.main()
