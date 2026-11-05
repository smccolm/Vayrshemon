import unittest
from tools.kjv_archive import load_register,read

class ChroniclesSongCovenantTests(unittest.TestCase):
    def test_speakers_inventory_and_parallel_account_details(self):
        prior,_=load_register('0.10-kjv.82')
        lang,manifest=load_register('0.10-kjv.83')
        self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs','suffix','prefix','possessors','roman'):
            self.assertEqual(getattr(prior,field),getattr(lang,field))
        cases={c['id']:c for c in read(lang.folder/'chronicles-song-covenant-cases.json')}
        self.assertEqual(87,len(cases))
        for c in cases.values():
            result=lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'],result['text'])
            self.assertEqual(c['expectedGloss'],result['gloss'])
            self.assertNotIn('!',result['text'])
        for ref,parts in {
            '16-3':['both man and woman','kjv_flagon of wine'],
            '16-6':['kjv_jahaziel_priest'],
            '16-10':['kjv_exult:imp'],
            '16-13':['kjv_seedline'],
            '16-14':['ourone/god'],
            '16-15':['thousand generation:pl'],
            '16-18':['to thou ipl','your/inherit:ev'],
            '16-20':['one_num kingdom'],
            '16-21':['permit:pa'],
            '16-22':['mypl/anoint:psv','mypl/prophet:pl'],
            '16-30':['kjv_establish:psv:fu'],
            '16-33':['kjv_tree:pl of forest'],
            '16-34':['give:imp:excl'],
            '16-35':['wesg:a','ourone/salvation'],
            '16-38':['kjv_three+twenty and eight','kjv_obededom_jeduthun','kjv_hosah_porter'],
            '16-39':['at kjv_gibeon'],
            '16-41':['by name call:psv:pa'],
            '17-4':['to ipl house:a','build:neg:fu'],
            '17-6':['judge:ag:pl','mypl/people:a feed:inf'],
            '17-10':['ipl to thou tell:pr that kjv_lord'],
            '17-13':['ipl his/father be:fu','he mypl/son be:fu','take:neg:fu'],
            '17-16':['who i be:pr','my/house'],
            '17-18':['what kjv_david'],
            '17-20':['wepl with ear:pl of wepl'],
            '17-21':['one_num nation'],
            '17-25':['my/god'],
            '18-4':['seven+thousand kjv_horseman:pl','twenty+thousand kjv_foot_soldier:pl','hundred chariot:pl'],
            '18-8':['kjv_tibhath','kjv_chun','kjv_sea_basin of kjv_brass'],
            '18-10':['kjv_congratulate:inf','kjv_hadoram_tou'],
            '18-12':['kjv_abishai','ten+thousand and eight+thousand'],
            '18-15':['kjv_record_keeper'],
            '18-16':['kjv_abimelech_abiathar son of kjv_abiathar','kjv_shavsha'],
        }.items():
            for part in parts:self.assertIn(part,cases['1-chronicles-'+ref]['analysis'])
        self.assertEqual(2,cases['1-chronicles-16-5']['analysis'].count('kjv_jeiel_musician'))
        for ref,key in [('16-30','stable'),('16-33','wood'),('16-21','suffer'),('16-41','express'),('18-4','footman'),('18-15','recorder')]:
            self.assertNotIn(key,lang.compile(cases['1-chronicles-'+ref]['analysis'])['keys'])
        self.assertEqual('data/language/archaic-kjv-82',manifest['basePackage'])

if __name__=='__main__':unittest.main()
