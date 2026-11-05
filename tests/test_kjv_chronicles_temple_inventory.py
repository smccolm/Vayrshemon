import unittest
from tools.kjv_archive import load_register,read

class ChroniclesTempleInventoryTests(unittest.TestCase):
    def test_chronicles_numbers_and_speakers_not_harmonized(self):
        prior,_=load_register('0.10-kjv.85')
        lang,manifest=load_register('0.10-kjv.86')
        self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs','suffix','prefix','possessors','roman'):
            self.assertEqual(getattr(prior,field),getattr(lang,field))
        cases={c['id']:c for c in read(lang.folder/'chronicles-temple-inventory-cases.json')}
        self.assertEqual(74,len(cases))
        for c in cases.values():
            out=lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'],out['text'])
            self.assertEqual(c['expectedGloss'],out['gloss'])
        def a(ref):return cases['2-chronicles-'+ref]['analysis']
        for ref,parts in {
            '1-7':['ipl'], '1-8':['i'], '1-11':['mypl/people'],
            '1-14':['thousand and four+hundred','twelve+thousand'],
            '2-2':['seven+ten+thousand','four+twenty+thousand','kjv_three+thousand and six+hundred'],
            '2-6':['heaven of heaven:pl','contain:neg'],
            '2-13':['i','kjv_huram_craftsman'],
            '2-14':['kjv_dan','kjv_tyre'], '2-16':['wesg'],
            '3-4':['hundred and twenty'], '3-15':['thirty and five'],
            '3-17':['kjv_right_side','kjv_jachin_pillar','kjv_boaz_pillar'],
            '4-3':['ox:pl'], '4-5':['kjv_three+thousand','kjv_thickness'],
            '4-13':['four+hundred','kjv_pommel'],
            '4-17':['kjv_zeredathah'],
        }.items():
            for part in parts:self.assertIn(part,a(ref))
        self.assertNotIn('kjv_naphtali',a('2-14'))
        self.assertNotIn('kjv_knop',a('4-3'))
        self.assertEqual('data/language/archaic-kjv-85',manifest['basePackage'])

if __name__=='__main__':unittest.main()
