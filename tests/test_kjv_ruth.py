import unittest
from tools.kjv_archive import load_register, read


class RuthTests(unittest.TestCase):
    def test_household_personal_dual_and_witness_voices(self):
        old, _ = load_register('0.10-kjv.40')
        lang, manifest = load_register('0.10-kjv.41')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'ruth-cases.json')}
        self.assertEqual(85, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {
            '1-10': ['we:du return:fu'],
            '1-11': ['my/womb'],
            '1-16': ['i go:fu', 'thy/people my/people', 'thy/god my/god'],
            '1-17': ['if anything but death'],
            '1-20': ['i:a kjv_mara'],
            '1-21': ['ipl full go:pa out', 'ipl:a home again empty'],
            '2-3': ['her/chance'],
            '2-9': ['thou:a they touch:fu not'],
            '2-12': ['under whose wing:pl'],
            '2-14': ['some:a leave:pa'],
            '2-17': ['about kjv_ephah_measure'],
            '2-20': ['to we:du', 'of we:du nearest kinsman:pl'],
            '2-21': ['near my/young man:pl'],
            '2-22': ['with his/maiden:pl'],
            '3-9': ['thy/kjv_skirt_garment:a'],
            '3-12': ['kinsman nearer than i'],
            '3-15': ['six kjv_measure_portion:pl', 'into city she go:pa'],
            '3-16': ['who thou be:pr my/daughter'],
            '4-3': ['of we:du brother kjv_elimelech'],
            '4-6': ['my/right:a'],
            '4-10': ['to my/wife be:inf i buy:perf'],
            '4-11': ['witness:pl wepl be:pr'],
            '4-15': ['better than seven son:pl'],
            '4-17': ['to kjv_naomi son bear:psv:perf', 'kjv_jesse of kjv_david father'],
            '4-19': ['kjv_ram_person'],
        }
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['ruth-' + ref]['analysis'])
        for ref in ('1-11', '1-12', '1-16', '1-17', '1-20', '3-5', '4-9', '4-10'):
            self.assertNotIn('ipl', cases['ruth-' + ref]['analysis'])
        for ref in ('3-15', '3-17'):
            self.assertNotIn('kjv_ephah', cases['ruth-' + ref]['analysis'])
        self.assertNotEqual(lang.lexicon['kjv_ram']['semanticId'], lang.lexicon['kjv_ram_person']['semanticId'])
        self.assertEqual('data/language/archaic-kjv-40', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
