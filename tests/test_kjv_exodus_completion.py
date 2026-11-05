import unittest
from tools.kjv_archive import load_register, read


class ExodusCompletionTests(unittest.TestCase):
    def test_person_material_and_accounting_distinctions(self):
        parent, _ = load_register('0.10-kjv.14')
        lang, manifest = load_register('0.10-kjv.15')
        self.assertEqual(parent.lexicon, {k: lang.lexicon[k] for k in parent.lexicon})
        for field in ('pairs', 'suffix', 'possessors', 'roman'):
            self.assertEqual(getattr(parent, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'exodus-completion-cases.json')}
        self.assertEqual(307, len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                actual = lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'], actual['text'])
                self.assertEqual(c['expectedGloss'], actual['gloss'])
        checks = {
            'exodus-32-1': ['for wesg kjv_god:pl', 'wesg know:pr not'],
            'exodus-32-4': ['kjv_engrave:ev kjv_tool'],
            'exodus-32-24': ['into fire it:a i cast:pa', 'out this kjv_calf:n come:pa'],
            'exodus-32-32': ['--', 'i:a erase:imp'],
            'exodus-32-33': ['mypl/book ipl erase:fu'],
            'exodus-33-11': ['face to face', 'kjv_nun'],
            'exodus-33-15': ['with i', 'wesg:a carry:imp not'],
            'exodus-33-23': ['mypl/kjv_back_parts', 'mypl/face:n see:psv:fu not'],
            'exodus-34-7': ['by no means from kjv_guilt guilty:a release:fu'],
            'exodus-34-9': ['ourone/sin:a', 'for kjv_stiffnecked'],
            'exodus-34-21': ['plough:ev time'],
            'exodus-35-22': ['kjv_tablet_ornament'],
            'exodus-37-17': ['his/branch'],
            'exodus-38-8': ['kjv_mirror', 'woman:pl'],
            'exodus-38-26': ['half kjv_shekel', 'six+hundred+thousand and kjv_three+thousand and five+hundred and five+ten'],
            'exodus-39-3': ['thin plate:pl', 'kjv_wire:pl', 'cut:pa'],
            'exodus-40-13': ['to ipl in priest/office'],
            'exodus-40-31': ['kjv_moses and kjv_aaron and his/son:pl'],
            'exodus-40-35': ['able be:pa not']}
        for key, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases[key]['analysis'])
        self.assertNotIn('kjv_cast_metal', cases['exodus-32-19']['analysis'])
        self.assertNotIn('kjv_candlestick:pl', cases['exodus-37-20']['analysis'])
        self.assertNotEqual(lang.word('kjv_tablet_ornament')[1], lang.word('table')[1])
        self.assertNotEqual(lang.word('kjv_nun')[1], lang.word('nun')[1])
        self.assertEqual('data/language/archaic-kjv-14', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
