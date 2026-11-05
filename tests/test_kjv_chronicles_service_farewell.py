import unittest
from tools.kjv_archive import load_register,read

class ChroniclesServiceFarewellTests(unittest.TestCase):
    def test_farewell_speakers_and_irregular_inventories(self):
        prior,_=load_register('0.10-kjv.84')
        lang,manifest=load_register('0.10-kjv.85')
        self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs','suffix','prefix','possessors','roman'):
            self.assertEqual(getattr(prior,field),getattr(lang,field))
        cases={c['id']:c for c in read(lang.folder/'chronicles-service-farewell-cases.json')}
        self.assertEqual(211,len(cases))
        for c in cases.values():
            out=lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'],out['text'])
            self.assertEqual(c['expectedGloss'],out['gloss'])
        def a(ref):return cases['1-chronicles-'+ref]['analysis']
        for ref,parts in {
            '23-3':['thirty year:pl','thirty+thousand and eight+thousand'],
            '23-24':['twenty year:pl'],
            '23-11':['kjv_zizah','one_num reckon:ev'],
            '23-29':['kjv_pan_cooking','kjv_fry_food'],
            '24-6':['kjv_ahimelech_abiathar son of kjv_abiathar','one_num chief house'],
            '24-18':['kjv_delaiah_course','kjv_maaziah'],
            '25-3':['kjv_zeri','kjv_mattithiah_jeduthun six'],
            '25-7':['two+hundred and four+twenty and eight'],
            '25-20':['kjv_shubael_heman'],
            '25-22':['kjv_jeremoth_heman'],
            '26-1':['kjv_asaph_kore'],
            '26-10':['first+born be:neg:pa','his/father he:a chief make:pa'],
            '26-17':['two, and two'],
            '26-32':['two+thousand and seven+hundred','half kjv_tribe'],
            '27-18':['kjv_elihu_david'],
            '27-24':['finish:neg:pa','neither kjv_number:ev'],
            '27-34':['kjv_jehoiada_benaiah son of kjv_benaiah'],
            '28-6':['ipl he:a to mypl/son','ipl his/father'],
            '28-7':['if he','mypl/command:pl'],
            '28-18':['chariot of kjv_cherub:pl'],
            '29-7':['ten+thousand kjv_dram_treasure:pl','hundred+thousand kjv_talent_weight:pl of iron'],
            '29-13':['ourone/god wesg'],
            '29-14':['who i be:pr','wesg'],
            '29-15':['wepl stranger:pl','day:pl of wepl'],
            '29-16':['wesg','all thine own'],
            '29-17':['i also know:pr','kjv_uprightness of my/heart'],
            '29-20':['kjv_lord and king:a worship:pa'],
            '29-22':['king second time'],
            '29-27':['forty year:pl','seven year:pl','thirty and kjv_three'],
        }.items():
            for part in parts:self.assertIn(part,a(ref))
        self.assertNotIn('kjv_shimei_musician',a('25-3'))
        self.assertEqual(1,a('25-9').count('twelve'))
        self.assertEqual(5,a('26-25').count('his/son'))
        self.assertNotIn('ipl',a('29-17'))
        self.assertEqual('data/language/archaic-kjv-84',manifest['basePackage'])

if __name__=='__main__':unittest.main()
