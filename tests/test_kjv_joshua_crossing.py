import unittest
from tools.kjv_archive import load_register, read


class JoshuaCrossingTests(unittest.TestCase):
    def test_crossing_dual_oath_and_city_ban(self):
        old, _ = load_register('0.10-kjv.31')
        lang, manifest = load_register('0.10-kjv.32')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'joshua-crossing-cases.json')}
        self.assertEqual(125, len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                result = lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'], result['text'])
                self.assertEqual(c['expectedGloss'], result['gloss'])
        checks = {'1-2': ['mypl/servant', 'ipl give:pr'], '1-3': ['kjv_sole', 'ipl give:perf'], '1-4': ['kjv_euphrates', 'your/boundary'], '1-5': ['ipl be:pa', 'ipl be:fu'], '1-7': ['kjv_right_side', 'to left'], '1-8': ['thy/mouth', 'day and night'], '1-9': ['ipl command:perf not?'], '1-11': ['within kjv_three day:pl', 'through army'], '1-12': ['half of kjv_manasseh kjv_tribe'], '1-14': ['your/wife:pl', 'remain:fu', 'armed pass:fu'], '1-16': ['wesg do:fu', 'wesg go:fu'], '1-17': ['wesg listen:fu', 'be:opt'], '1-18': ['to death put:psv:fu'], '2-1': ['two man:pl', 'kjv_harlot', 'kjv_rahab'], '2-4': ['they:a hide:pa', 'i know:pa not'], '2-5': ['i know:pr not', 'pursue:imp'], '2-6': ['kjv_flax stem:pl', 'she lay:pp'], '2-9': ['i know:pr', 'upon wesg'], '2-10': ['wepl hear:perf', 'two of kjv_amorite:pl king:pl'], '2-11': ['of wepl heart:pl', 'earth beneath'], '2-12': ['of my/father house'], '2-13': ['of wepl life:pl'], '2-14': ['of we:du life', 'to wesg give:perf', 'we:du deal:fu'], '2-18': ['wesg come:pr', 'kjv_scarlet thread kjv_cord', 'we:du:a thou lower:pa'], '2-19': ['his/blood upon his/head', 'of we:du head'], '2-20': ['free we:du be:fu'], '2-24': ['ourone/hand:pl', 'because of wesg'], '3-3': ['kjv_ark_chest', 'carry:pr'], '3-4': ['about two+thousand kjv_cubit:pl', 'near to it come:imp not'], '3-7': ['ipl begin:fu', 'with thou ipl be:fu'], '3-10': ['kjv_canaanite:pl', 'kjv_girgashites:pl', 'kjv_jebusite:pl'], '3-13': ['upon kjv_heap'], '3-15': ['all of harvest time overflow:pr'], '3-16': ['kjv_adam_city', 'kjv_zaretan', 'salt sea'], '3-17': ['on dry ground', 'completely over'], '4-3': ['twelve stone:pl', 'they:a carry:fu over'], '4-8': ['they:a carry:pa over', 'there they:a lay:pa down'], '4-9': ['in of kjv_jordan middle', 'twelve stone:pl', 'to this day'], '4-11': ['kjv_ark_chest and priest:pl', 'people presence'], '4-13': ['about forty+thousand'], '4-18': ['water:pl to their/kjv_place_site return:pa'], '4-19': ['ten:ord day of first month', 'kjv_gilgal'], '4-20': ['twelve stone:pl'], '4-23': ['before wesg', 'wesg go:pp'], '5-1': ['until wesg pass:pp over'], '5-2': ['kjv_second time', 'sharp kjv_knife:pl'], '5-4': ['kjv_male:pl', 'of war man:pl'], '5-5': ['born:psv:pa', 'kjv_circumcise:pp not'], '5-6': ['forty year:pl', 'to wesg he give:fu'], '5-9': ['ipl roll:perf away', 'kjv_gilgal'], '5-10': ['fourteen:ord day'], '5-11': ['old corn', 'without kjv_leaven'], '5-12': ['kjv_manna', 'any more have:pa'], '5-13': ['for wesg or for ourone/kjv_adversary:pl'], '5-14': ['captain i now come:perf', 'kjv_worship:pa'], '5-15': ['thy/shoe', 'holy be:pr'], '6-2': ['ipl give:perf'], '6-3': ['one_num time', 'six day:pl'], '6-4': ['seven priest:pl', 'seven:ord day', 'seven time:pl'], '6-10': ['i you:pl:a shout:inf bid:pr'], '6-13': ['kjv_rearguard'], '6-15': ['seven:ord day', 'seven time:pl'], '6-16': ['shout:imp:excl'], '6-17': ['kjv_accursed_devoted', 'only kjv_rahab', 'whom wesg send:pa'], '6-18': ['kjv_accursed_devoted thing', 'camp:a curse:ev'], '6-19': ['silver and gold', 'consecrate:psv:pr', 'kjv_treasury'], '6-21': ['both man and woman young and old', 'ass:a', 'completely they destroy:pa'], '6-22': ['two man:pl', 'you:pl swear:pa'], '6-23': ['outside of kjv_israel camp'], '6-24': ['burn:caus:pa', 'only silver'], '6-25': ['alive save:pa', 'to this day'], '6-26': ['curse:psv:opt:excl', 'in his/first+born', 'in his/kjv_youngest son']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['joshua-' + ref]['analysis'])
        self.assertNotEqual(lang.compile('i be:pr')['text'], lang.compile('ipl be:pr')['text'])
        self.assertNotEqual(lang.compile('wepl be:pr')['text'], lang.compile('wesg be:pr')['text'])
        self.assertEqual('data/language/archaic-kjv-31', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
