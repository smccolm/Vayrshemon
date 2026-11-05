import unittest
from tools.kjv_archive import load_register,read

class ChroniclesArkOrderTests(unittest.TestCase):
    def test_speakers_inventory_and_parallel_account_details(self):
        prior,_=load_register('0.10-kjv.81')
        lang,manifest=load_register('0.10-kjv.82')
        self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs','suffix','prefix','possessors','roman'):
            self.assertEqual(getattr(prior,field),getattr(lang,field))
        cases={c['id']:c for c in read(lang.folder/'chronicles-ark-order-cases.json')}
        self.assertEqual(100,len(cases))
        for c in cases.values():
            result=lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'],result['text'])
            self.assertEqual(c['expectedGloss'],result['gloss'])
            self.assertNotIn('!',result['text'])
        for ref,parts in {
            '12-2':['kjv_right_side hand and left:a'],
            '12-8':['kjv_buckler','as face:pl of lion:pl'],
            '12-17':['if you:pl to i','my/heart','ourone/father:pl'],
            '12-18':['of thou wesg','peace peace'],
            '12-19':['head:pl of wepl'],
            '12-20':['kjv_jozabad_first','kjv_jozabad_later'],
            '12-31':['half kjv_tribe','ten+thousand and eight+thousand','by name call:psv:pa'],
            '12-33':['of double heart be:neg:pa'],
            '12-34':['thousand captain:pl','thirty+thousand and seven+thousand'],
            '12-38':['whole heart','one_num heart'],
            '12-40':['food and kjv_flour'],
            '13-2':['if it of kjv_lord ourone/god','wesg'],
            '13-3':['ask:neg:pa'],
            '13-4':['kjv_right_conduct'],
            '13-7':['new wagon','kjv_abinadab','kjv_uzza_ark'],
            '13-9':['kjv_chidon','kjv_stumble'],
            '13-10':['he he:a strike:pa because'],
            '13-12':['how i'],
            '13-14':['kjv_three month:pl'],
            '14-5':['kjv_elpalet'],
            '14-7':['kjv_beeliada and kjv_eliphalet'],
            '14-10':['i against','ipl they:a'],
            '14-11':['my/enemy:pl by my/hand'],
            '14-12':['their/god:pl:a','burn:psv:pa'],
            '14-16':['kjv_gibeon even to kjv_gazer'],
            '15-1':['tent:a set:pa up'],
            '15-12':['you:pl chief','i for it prepare:perf'],
            '15-13':['ourone/god breach:a upon wesg','kjv_due_order'],
            '15-15':['their/kjv_shoulder:pl with staff:pl'],
            '15-18':['kjv_ben_singer'],
            '15-20':['kjv_alamoth'],
            '15-21':['kjv_sheminith'],
            '15-26':['seven kjv_bullock:pl and seven kjv_ram:pl'],
            '15-29':['in her/heart despise:pa'],
        }.items():
            for part in parts:self.assertIn(part,cases['1-chronicles-'+ref]['analysis'])
        self.assertEqual(2,cases['1-chronicles-12-40']['analysis'].count('ox:pl'))
        self.assertNotIn('pitch',lang.compile(cases['1-chronicles-15-1']['analysis'])['keys'])
        self.assertNotIn('mypl',cases['1-chronicles-14-11']['analysis'])
        self.assertEqual('data/language/archaic-kjv-81',manifest['basePackage'])

if __name__=='__main__':unittest.main()
