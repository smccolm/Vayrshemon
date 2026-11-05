import unittest
from tools.kjv_archive import load_register, read


class JudgesJephthahTests(unittest.TestCase):
    def test_collective_passage_vow_and_sound_contrast(self):
        old, _ = load_register('0.10-kjv.37')
        lang, manifest = load_register('0.10-kjv.38')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'judges-jephthah-cases.json')}
        self.assertEqual(73, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {
            '10-10': ['wesg sin:perf'],
            '10-13': ['no more ipl deliver:fu'],
            '10-16': ['his/soul', 'sorrow:pa'],
            '11-2': ['of wepl father house'],
            '11-10': ['between wepl', 'so wesg do:pr not'],
            '11-17': ['ipl:a please'],
            '11-19': ['wesg:a please', 'into mypl/kjv_place_site'],
            '11-24': ['kjv_chemosh thy/god', 'wesg possess:fu'],
            '11-26': ['kjv_three+hundred year:pl'],
            '11-31': ['whatever', 'surely of kjv_lord be:fu and', 'burn:psv kjv_offering i offer:fu'],
            '11-34': ['his/only child', 'neither son nor daughter'],
            '11-37': ['my/virginity:a', 'i and my/fellow:pl'],
            '11-39': ['kjv_according to his/vow', 'no man:a she know:pa'],
            '12-6': ['kjv_shibboleth say:imp', 'kjv_sibboleth he say:pa', 'forty+thousand and two+thousand'],
            '12-14': ['thirty kjv_nephew_descendant', 'seven+ten kjv_asscolt:pl'],
        }
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['judges-' + ref]['analysis'])
        a, b = (lang.lexicon[k]['form'] for k in ('kjv_shibboleth', 'kjv_sibboleth'))
        self.assertNotEqual(a, b)
        self.assertNotEqual(lang.reading(a), lang.reading(b))
        self.assertEqual('data/language/archaic-kjv-37', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
