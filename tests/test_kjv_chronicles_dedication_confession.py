import unittest
from tools.kjv_archive import load_register,read

class ChroniclesDedicationConfessionTests(unittest.TestCase):
    def test_nested_speakers_conditional_presence_and_objects(self):
        prior,_=load_register('0.10-kjv.86');lang,manifest=load_register('0.10-kjv.87')
        self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs','suffix','prefix','possessors','roman'):
            self.assertEqual(getattr(prior,field),getattr(lang,field))
        cases={c['id']:c for c in read(lang.folder/'chronicles-dedication-confession-cases.json')}
        self.assertEqual(98,len(cases))
        for c in cases.values():
            out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss'])
        def a(ref):return cases['2-chronicles-'+ref]['analysis']
        for ref,parts in {
            '4-8':['kjv_table_furniture:pl'], '4-19':['kjv_table_furniture:pl'],
            '5-10':['two table:pl'], '5-11':['by kjv_service_order wait:neg:pa'],
            '5-12':['hundred and twenty'], '5-13':['as one_num','one_num sound'],
            '6-8':['my/father','mypl/name'], '6-13':['five kjv_cubit:pl long','kjv_three kjv_cubit:pl high'],
            '6-16':['yet if','mypl/sight','before ipl'],
            '6-18':['i build:perf','contain:neg:pr:can','can:excl'],
            '6-32':['kjv_israel be:neg:pr','if they'], '6-37':['wesg sin:perf'],
            '7-9':['eight:ord','seven day:pl'], '7-10':['twenty and kjv_three:ord'],
            '7-12':['iplself'], '7-19':['you:pl','mypl/command:pl'],
            '8-2':['kjv_huram_king to kjv_solomon restore:pp'],
            '8-10':['two+hundred and fifty'], '8-18':['four+hundred and fifty'],
        }.items():
            for part in parts:self.assertIn(part,a(ref))
        self.assertNotIn('ipl',a('6-18'))
        self.assertNotIn('kjv_table_furniture',a('5-10'))
        self.assertEqual('data/language/archaic-kjv-86',manifest['basePackage'])

if __name__=='__main__':unittest.main()
