import unittest
from tools.kjv_archive import load_register,read

class ChroniclesKinshipTests(unittest.TestCase):
    def test_names_counts_and_household_relations(self):
        prior,_=load_register('0.10-kjv.79')
        lang,manifest=load_register('0.10-kjv.80')
        self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs','suffix','prefix','possessors','roman'):
            self.assertEqual(getattr(prior,field),getattr(lang,field))
        cases={c['id']:c for c in read(lang.folder/'chronicles-kinship-cases.json')}
        self.assertEqual(80,len(cases))
        for c in cases.values():
            result=lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'],result['text'])
            self.assertEqual(c['expectedGloss'],result['gloss'])
            self.assertFalse({'i','ipl','wesg','wepl','one'} & set(result['keys']))
        for ref,parts in {
            '7-3':['kjv_ishiah five'],
            '7-5':['four+twenty+thousand and seven+thousand'],
            '7-7':['twenty+thousand and two+thousand and thirty and four'],
            '7-15':['name of their/sister','two:ord kjv_zelophehad','daughter:pl'],
            '7-20':['kjv_tahath_bered','kjv_tahath_eladah'],
            '7-23':['with his/house evil go:pa'],
            '7-24':['his/daughter kjv_sherah','kjv_uzzensherah:a build:pa'],
            '7-27':['kjv_non his/son kjv_jehoshuah'],
            '7-28':['to east kjv_naaran','to west kjv_gezer','until kjv_gaza'],
            '7-32':['kjv_shua_woman their/sister'],
            '8-8':['after he they:a send:pp away','kjv_hushim_wife'],
            '8-26':['kjv_athaliah_jeroham'],
            '8-29':['father of kjv_gibeon','name of his/wife'],
            '8-33':['kjv_ner kjv_kish:a beget:pa','kjv_eshbaal'],
            '8-34':['kjv_meribbaal','kjv_micah_meribbaal'],
            '8-38':['six son:pl','kjv_bocheru'],
            '8-40':['kjv_bow shoot:ag:pl','son:pl and son:pl of son:pl hundred and fifty'],
        }.items():
            for part in parts:self.assertIn(part,cases['1-chronicles-'+ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-79',manifest['basePackage'])

if __name__=='__main__':unittest.main()
