import unittest
from tools.kjv_archive import load_register, read

class KingsElijahTests(unittest.TestCase):
    def test_dynastic_quantities_speaker_identity_and_widow_pair(self):
        old, _ = load_register('0.10-kjv.59')
        lang, manifest = load_register('0.10-kjv.60')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings1-elijah-cases.json')}
        self.assertEqual(92, len(cases))
        for c in cases.values():
            result = lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'], result['text'])
            self.assertEqual(c['expectedGloss'], result['gloss'])
        anchors = {
            '15-2': ['his/mother name kjv_maachah_abijam'],
            '15-6': ['kjv_rehoboam and kjv_jeroboam'],
            '15-10': ['four+ten and one_num', 'his/mother name kjv_maachah_abijam'],
            '15-14': ['remove:psv:pa not', 'perfect be:pa'],
            '15-19': ['between ipl and thou', 'kjv_league', 'my/father'],
            '16-4': ['he:a who in city die:pr dog:pl eat:fu', 'he:a who in field:pl die:pr of air bird:pl eat:fu'],
            '16-7': ['and because he:a he kill:pa'],
            '16-11': ['one:a who against wall'],
            '16-15': ['seven day:pl'],
            '16-23': ['kjv_three+ten and one_num:ord', 'twelve year:pl', 'six year:pl'],
            '16-34': ['in kjv_abiram_hiel his/first+born', 'his/kjv_youngest son kjv_segub_hiel'],
            '17-1': ['before whom i stand:pr', 'my/word'],
            '17-4': ['raven:pl:a ipl command:perf'],
            '17-12': ['for i and my/son', 'we:du eat:pr:may and die:pr:may'],
            '17-13': ['for i little cake:a first', 'after for thou'],
            '17-20': ['evil:a thou bring:perf', 'her/son:a slay:ev ?'],
            '17-21': ['kjv_three time:pl', 'soul into he again come:opt'],
            '17-22': ['he revive:pa']}
        for ref, parts in anchors.items():
            for part in parts:
                self.assertIn(part, cases['1-kings-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-59', manifest['basePackage'])

if __name__ == '__main__':
    unittest.main()
