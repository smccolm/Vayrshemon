import unittest
from tools.kjv_archive import load_register, read

class KingsFallTests(unittest.TestCase):
    def test_royal_self_quoted_accusation_and_distinct_council_voices(self):
        old, _ = load_register('0.10-kjv.61')
        lang, manifest = load_register('0.10-kjv.62')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings1-fall-cases.json')}
        self.assertEqual(125, len(cases))
        for c in cases.values():
            result = lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'], result['text'])
            self.assertEqual(c['expectedGloss'], result['gloss'])
        anchors = {
            '20-3': ['thy/child:pl even best of ipl'],
            '20-7': ['i pray:pr you', 'my/wife:pl'],
            '20-10': ['to i thus god:pl do:opt', 'who ipl:a follow:pr'],
            '20-15': ['two+hundred and kjv_three+ten and two', 'seven+thousand'],
            '20-23': ['in kjv_plain_land wesg fight:opt'],
            '20-28': ['into thy/hand ipl deliver:fu and you know:fu'],
            '20-29': ['hundred+thousand kjv_foot_soldier:pl:a in one_num day'],
            '20-30': ['two+ten+thousand and seven+thousand'],
            '20-31': ['of wepl kjv_loins', 'of wepl head:pl'],
            '20-32': ['i pray:pr thou i live:opt'],
            '20-33': ['kjv_ahab he:a into chariot come:caus:pa up'],
            '20-38': ['kjv_ashes upon his/face'],
            '21-7': ['to thou ipl give:fu'],
            '21-8': ['letter:pl:a she write:pa', 'with his/seal'],
            '21-13': ['before people testify:pa', 'he die:pa'],
            '21-24': ['he:a who in city die:pr dog:pl eat:fu'],
            '21-29': ['in his/day:pl evil:a ipl bring:fu not', 'in his/son day:pl'],
            '22-3': ['ourone/kjv_possession', 'wesg do:pr nothing'],
            '22-7': ['we:du ask:pr:may'],
            '22-8': ['he:a i hate:pr'],
            '22-13': ['with one_num mouth', 'one of they'],
            '22-20': ['one_num of army'],
            '22-21': ['he:a i persuade:fu'],
            '22-22': ['kjv_lie_false:cv spirit i be:fu', 'so do:imp'],
            '22-23': ['spirit:a kjv_lord put:perf'],
            '22-31': ['captain:pl kjv_three+ten and two'],
            '22-34': ['kjv_armour_joint:pl', 'i kjv_wound_inflict:psv:perf'],
            '22-38': ['one chariot:a', 'his/kjv_armour:a they wash:pa'],
            '22-47': ['no king in kjv_edom', 'kjv_deputy king be:pa'],
            '22-49': ['kjv_jehoshaphat will:pa not']}
        for ref, parts in anchors.items():
            for part in parts:
                self.assertIn(part, cases['1-kings-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-61', manifest['basePackage'])

if __name__ == '__main__':
    unittest.main()
