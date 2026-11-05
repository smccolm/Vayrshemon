import unittest
from tools.kjv_archive import load_register,read

class ChroniclesBodyServiceTests(unittest.TestCase):
    def test_speakers_inventory_and_parallel_account_details(self):
        prior,_=load_register('0.10-kjv.80')
        lang,manifest=load_register('0.10-kjv.81')
        self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs','suffix','prefix','possessors','roman'):
            self.assertEqual(getattr(prior,field),getattr(lang,field))
        cases={c['id']:c for c in read(lang.folder/'chronicles-body-service-cases.json')}
        self.assertEqual(105,len(cases))
        for c in cases.values():
            result=lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'],result['text'])
            self.assertEqual(c['expectedGloss'],result['gloss'])
            self.assertNotIn('!',result['text'])
        for ref,parts in {
            '9-11':['kjv_meshullam_sanctuary son of kjv_zadok_sanctuary son of kjv_meraioth_sanctuary'],
            '9-22':['two+hundred and twelve'],
            '9-23':['by kjv_duty_watch:pl'],
            '9-28':['in and out by kjv_number:ev'],
            '9-31':['one_num','kjv_pan_cooking'],
            '9-33':['exempt:psv','day and night'],
            '9-35':['kjv_jehiel_gibeon'],
            '9-41':['kjv_tahrea'],
            '9-42':['kjv_jarah'],
            '9-43':['kjv_rephaiah_binea'],
            '10-4':['i:a','will:neg:pa'],
            '10-6':['all his/house'],
            '10-10':['his/head:a in temple of kjv_dagon'],
            '10-12':['their/bone:pl:a under oak','seven day:pl kjv_fast:pa'],
            '10-13':['person who kjv_familiar_spirit'],
            '11-1':['thy/bone and thy/flesh wesg'],
            '11-2':['mypl/people'],
            '11-11':['kjv_jashobeam','kjv_three+hundred','one_num time'],
            '11-13':['kjv_barley'],
            '11-14':['they in middle'],
            '11-17':['that one to i','give:opt:excl'],
            '11-19':['my/god','i blood:a'],
            '11-21':['more honourable than two','first kjv_three'],
            '11-22':['two man:pl as lion','lion:a in kjv_pit'],
            '11-23':['five kjv_cubit:pl'],
            '11-38':['brother of kjv_nathan_joel'],
            '11-42':['thirty with he'],
        }.items():
            for part in parts:self.assertIn(part,cases['1-chronicles-'+ref]['analysis'])
        self.assertEqual(2,cases['1-chronicles-11-2']['analysis'].count('mypl/people'))
        self.assertNotIn('mypl',cases['1-chronicles-11-19']['analysis'])
        self.assertNotIn('burn:caus',cases['1-chronicles-10-12']['analysis'])
        self.assertNotIn('tale',lang.compile(cases['1-chronicles-9-28']['analysis'])['keys'])
        self.assertEqual('data/language/archaic-kjv-80',manifest['basePackage'])

if __name__=='__main__':unittest.main()
