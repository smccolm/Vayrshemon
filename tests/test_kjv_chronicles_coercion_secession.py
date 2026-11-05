import unittest
from tools.kjv_archive import load_register,read
class ChroniclesCoercionSecessionTests(unittest.TestCase):
    def test_royal_self_collective_refusal_and_distinct_inventory(self):
        prior,_=load_register('0.10-kjv.87');lang,manifest=load_register('0.10-kjv.88')
        self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,field),getattr(lang,field))
        cases={c['id']:c for c in read(lang.folder/'chronicles-coercion-secession-cases.json')};self.assertEqual(89,len(cases))
        for c in cases.values():
            out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss'])
        def a(r):return cases['2-chronicles-'+r]['analysis']
        for r,parts in {
            '9-4':['kjv_table_furniture'], '9-6':['one_num+half','i their/word:pl'],
            '9-11':['kjv_terrace'], '9-16':['kjv_three+hundred kjv_shekel:pl'],
            '9-25':['four+thousand kjv_horse_stall:pl'],
            '10-4':['ourone/yoke','wesg thee:a serve:fu'],
            '10-9':['wesg to this people','upon wesg:a'],
            '10-10':['less heavy','my/father kjv_loins kjv_thicker'],
            '10-11':['ipl','you:pl'], '10-16':['wesg no inheritance','each man'],
            '10-18':['kjv_hadoram_tribute'], '11-4':['by ipl','each man'],
            '11-18':['kjv_abihail_eliab'], '11-21':['ten and eight wife:pl','twenty and eight son:pl'],
            '12-7':['some kjv_deliverance','mypl/wrath'],
            '12-8':['mypl/service and service of kingdom:pl'],
            '12-10':['shield:pl of kjv_brass'], '12-13':['one_num and forty','seventeen'],
        }.items():
            for part in parts:self.assertIn(part,a(r))
        self.assertNotIn('ipl',a('9-6'))
        self.assertNotIn('light',lang.compile(a('10-10'))['keys'])
        self.assertEqual('data/language/archaic-kjv-87',manifest['basePackage'])
if __name__=='__main__':unittest.main()
