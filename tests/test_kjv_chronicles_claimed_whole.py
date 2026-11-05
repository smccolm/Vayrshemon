import unittest
from tools.kjv_archive import load_register,read
class ChroniclesClaimedWholeTests(unittest.TestCase):
    def test_claimed_community_and_source_tensions(self):
        prior,_=load_register('0.10-kjv.88');lang,manifest=load_register('0.10-kjv.89')
        self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
        for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
        cases={c['id']:c for c in read(lang.folder/'chronicles-claimed-whole-cases.json')};self.assertEqual(len(cases),70)
        for c in cases.values():
            out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss'])
        def a(r):return cases['2-chronicles-'+r]['analysis']
        for r,parts in {
            '13-2':['kjv_michaiah_uriel','kjv_uriel_gibeah'],
            '13-4':['i:a hear:imp'], '13-7':['young and tender in heart'],
            '13-10':['wesg','ourone/god'], '13-11':['kjv_table_furniture'],
            '13-17':['five+hundred+thousand','kjv_slaughter'],
            '13-19':['kjv_ephraim_city'], '13-21':['fourteen','twenty and two','sixteen'],
            '14-7':['wesg he:a seek:perf'], '14-9':['thousand+thousand'],
            '14-11':['wesg:a help:imp'], '15-1':['kjv_azariah_oded'],
            '15-8':['kjv_prophesy:ev of kjv_oded_prophet'],
            '15-13':['to death put:psv:pr:should','whether man or woman'],
            '15-16':['kjv_maachah_abijam mother of kjv_asa'],
            '15-17':['take:psv:neg:pa','perfect be:pa all his/day:pl'],
            '16-1':['thirty and six:ord'], '16-3':['kjv_league between i and thee'],
            '16-7':['army of king of kjv_syria out of thy/hand escape:perf'],
            '16-12':['his/foot:pl sick','physician:pl'],
            '16-14':['kjv_apothecary:pl','for he very great burn:ev'],
        }.items():
            for part in parts:self.assertIn(part,a(r))
        self.assertNotIn('ipl',lang.compile(a('16-3'))['keys'])
        self.assertNotIn('league',lang.compile(a('16-3'))['keys'])
        self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-88')
if __name__=='__main__':unittest.main()
