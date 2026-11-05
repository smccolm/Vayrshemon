import unittest
from tools.kjv_archive import load_register, read


class DeuteronomySongTests(unittest.TestCase):
    def test_song_identity_and_final_blessings(self):
        old, _ = load_register('0.10-kjv.30')
        lang, manifest = load_register('0.10-kjv.31')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'deuteronomy-song-cases.json')}
        self.assertEqual(123, len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                result = lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'], result['text'])
                self.assertEqual(c['expectedGloss'], result['gloss'])
        checks = {'31-2': ['hundred and two+ten', 'i be:pr', 'go:fu not'], '31-8': ['kjv_dismay:psv:imp'], '31-9': ['kjv_ark_chest:a carry:pa'], '31-10': ['every seven year:pl', 'of release year'], '31-12': ['man:pl and woman:pl and child:pl', 'thy/stranger'], '31-14': ['ipl give:pr:can', 'kjv_joshua'], '31-16': ['mypl/kjv_covenant', 'kjv_whoring'], '31-17': ['mypl/face', 'ourone/god among wesg'], '31-19': ['their/mouth:pl', 'for ipl against'], '31-20': ['ipl bring:fp', 'they eat:fp'], '31-23': ['ipl swear:pa', 'with thou ipl be:fu'], '31-26': ['kjv_ark_chest side'], '31-27': ['of thou kjv_stiffnecked:ev:a', 'my/death'], '31-28': ['testify:inf'], '32-1': ['i speak:fu', 'my/mouth'], '32-3': ['ourone/god'], '32-4': ['kjv_rock_title', 'without kjv_iniquity'], '32-5': ['their/spot', 'be:pr not'], '32-8': ['of of kjv_israel child:pl amount'], '32-10': ['of his/eye apple'], '32-11': ['her/wing:pl carry:pr'], '32-12': ['alone kjv_lord', 'strange god be:pa not'], '32-14': ['of wheat kjv_kidney:pl kjv_fat', 'of grape pure blood'], '32-15': ['kjv_jeshurun', 'of his/salvation kjv_rock_title'], '32-18': ['kjv_rock_title who thou:a beget:pa'], '32-20': ['mypl/face', 'ipl hide:fu'], '32-21': ['god be:pr not', 'people be:pr not'], '32-23': ['into kjv_heap'], '32-27': ['wrath:a ipl fear:pa', 'of wepl hand'], '32-29': ['be:opt:excl', 'understand:opt:excl', 'consider:opt:excl'], '32-30': ['one_num thousand', 'two ten+thousand', 'sell:pp'], '32-31': ['ourone/kjv_rock_title'], '32-33': ['kjv_dragon_source:pl', 'kjv_asp:pl'], '32-34': ['with ipl', 'mypl/treasure:pl'], '32-36': ['himself:a repent:fu', 'shut:psv up or leave:psv'], '32-39': ['ipl, even ipl he be:pr', 'with ipl god be:pr not', 'ipl kill:pr and alive make:pr', 'mypl/hand'], '32-40': ['forever ipl live:pr'], '32-41': ['kjv_whet:pr'], '32-43': ['merciful be:fu'], '32-44': ['kjv_hoshea of kjv_nun son'], '32-46': ['i testify:pr'], '32-50': ['die:imp', 'gather:psv:imp'], '32-51': ['kjv_meribahkadesh', 'you:pl kjv_trespass:pa'], '32-52': ['thou go:fu not'], '33-2': ['ten+thousand:pl', 'of fire law'], '33-4': ['wesg:a'], '33-5': ['king he be:pa'], '33-6': ['die:opt not', 'few be:opt not'], '33-8': ['kjv_thummim', 'kjv_urim', 'kjv_massah'], '33-9': ['he:a i see:perf not'], '33-11': ['kjv_substance_estate'], '33-12': ['between his/kjv_shoulder:pl'], '33-14': ['by moon'], '33-17': ['kjv_unicorn:pl', 'ten+thousand:pl', 'thousand:pl'], '33-19': ['sea:pl abundance', 'they suck:fu'], '33-24': ['his/foot:a in oil dip:opt'], '33-29': ['be:pr:excl?', 'their/high kjv_place_site:pl'], '34-1': ['kjv_plain_land:pl'], '34-3': ['kjv_palm_tree:pl'], '34-4': ['ipl swear:pa', 'thou go:fu not'], '34-6': ['he he:a', 'no man'], '34-7': ['hundred and two+ten', 'dim be:pa not', 'force diminish:pa'], '34-8': ['kjv_three+ten day:pl'], '34-9': ['lay:pp'], '34-10': ['face to face', 'rise:perf not']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['deuteronomy-' + ref]['analysis'])
        self.assertNotEqual(lang.compile('i be:pr')['text'], lang.compile('ipl be:pr')['text'])
        self.assertNotEqual(lang.compile('wepl be:pr')['text'], lang.compile('wesg be:pr')['text'])
        self.assertEqual('data/language/archaic-kjv-30', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
