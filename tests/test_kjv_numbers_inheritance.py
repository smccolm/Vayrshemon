import unittest
from tools.kjv_archive import load_register,read

class NumbersInheritanceTests(unittest.TestCase):
    def test_claims_vows_and_quantity_distinctions_survive(self):
        parent,_=load_register('0.10-kjv.23');lang,m=load_register('0.10-kjv.24')
        self.assertEqual(parent.lexicon,{k:lang.lexicon[k] for k in parent.lexicon})
        for f in ('pairs','suffix','possessors','roman'):self.assertEqual(getattr(parent,f),getattr(lang,f))
        cases={c['id']:c for c in read(lang.folder/'numbers-inheritance-cases.json')}
        self.assertEqual(175,len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                result=lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss'])
        checks={'26-11':['child:pl die:pa not'],'26-33':['no son:pl but daughter:pl','kjv_noah_daughter','kjv_milcah_daughter'],'26-46':['kjv_sarah_asher'],'26-51':['six+hundred+thousand and thousand and seven+hundred and thirty'],'26-58':['kjv_korathites'],'26-62':['month old and above'],'27-3':['ourone/father','in his/own sin'],'27-4':['to wesg'],'27-5':['kjv_case_plea'],'27-7':['right speak:pr'],'27-8':['no son','his/daughter'],'27-9':['no daughter','his/brother:pl'],'27-10':['his/father/brother:pl'],'27-11':['nearest'],'27-14':['you:pl rebel:pa','mypl/command'],'27-20':['of thy/honour some'],'27-21':['kjv_urim'],'28-5':['kjv_ephah_measure'],'28-14':['half kjv_hin','kjv_three:ord part','four:ord part'],'29-7':['any work'],'29-13':['ten and kjv_three'],'29-36':['one_num kjv_bullock one_num kjv_ram seven'],'30-4':['her/father at she silent'],'30-9':['widow','kjv_divorced'],'30-14':['from day to day','confirm:pr'],'30-15':['after that they:a he hear:perf','her/kjv_iniquity:a he carry:fu']}
        for ref,parts in checks.items():
            for part in parts:self.assertIn(part,cases['numbers-'+ref]['analysis'])
        self.assertNotEqual(lang.lexicon['kjv_noah']['semanticId'],lang.lexicon['kjv_noah_daughter']['semanticId'])
        self.assertEqual(lang.lexicon['kjv_noah']['form'],lang.lexicon['kjv_noah_daughter']['form'])
        self.assertEqual('data/language/archaic-kjv-23',m['basePackage'])

if __name__=='__main__':unittest.main()
