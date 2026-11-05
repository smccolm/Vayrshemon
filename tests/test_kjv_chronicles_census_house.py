import unittest
from tools.kjv_archive import load_register,read

class ChroniclesCensusHouseTests(unittest.TestCase):
    def test_speakers_responsibility_numbers_and_source_contrasts(self):
        prior,_=load_register('0.10-kjv.83')
        lang,manifest=load_register('0.10-kjv.84')
        self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs','suffix','prefix','possessors','roman'):
            self.assertEqual(getattr(prior,field),getattr(lang,field))
        cases={c['id']:c for c in read(lang.folder/'chronicles-census-house-cases.json')}
        self.assertEqual(76,len(cases))
        for c in cases.values():
            result=lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'],result['text'])
            self.assertEqual(c['expectedGloss'],result['gloss'])
            self.assertNotIn('!',result['text'])
        for ref,parts in {
            '19-12':['ipl'], '19-13':['wesg','ourone/people'],
            '19-18':['seven+thousand','forty+thousand','kjv_shophach'],
            '20-5':['kjv_lahmi','kjv_jair_elhanan'],
            '20-6':['twenty and four','six'],
            '21-1':['kjv_satan_chronicles','urge:pa'],
            '21-5':['thousand+thousand and hundred+thousand','four+hundred+thousand and seven+ten+thousand'],
            '21-8':['i','kjv_iniquity'],
            '21-10':['ipl','kjv_three','one_num'],
            '21-12':['kjv_famine','i'],
            '21-15':['kjv_relent','stop:imp'],
            '21-17':['i','house of my/father'],
            '21-25':['six+hundred','gold'],
            '22-8':['mypl/name','blood'],
            '22-10':['ipl his/father','mypl/son'],
            '22-14':['hundred+thousand','thousand+thousand','kjv_talent_weight'],
        }.items():
            for part in parts:self.assertIn(part,cases['1-chronicles-'+ref]['analysis'])
        self.assertEqual(3,cases['1-chronicles-19-12']['analysis'].count('ipl'))
        self.assertEqual('data/language/archaic-kjv-83',manifest['basePackage'])

if __name__=='__main__':unittest.main()
