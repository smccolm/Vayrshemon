import unittest
from tools.kjv_archive import load_register,read
class ChroniclesCouncilHostTests(unittest.TestCase):
    def test_speaker_roles_and_contextual_host_repairs(self):
        prior,_=load_register('0.10-kjv.89');lang,manifest=load_register('0.10-kjv.90')
        self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
        for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
        cases={c['id']:c for c in read(lang.folder/'chronicles-council-host-cases.json')};self.assertEqual(len(cases),108)
        for c in cases.values():
            out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss'])
        def a(r):return cases['2-chronicles-'+r]['analysis']
        for r,parts in {
            '17-8':['kjv_tobijah_teacher and kjv_tobadonijah','kjv_jehoram_priest'],
            '17-11':['seven+thousand and seven+hundred he kjv_goat:pl'],
            '18-3':['with i','ipl as thou','mypl/people','wesg with thee'],
            '18-5':['four+hundred','or ipl kjv_forbear:fu'],
            '18-6':['we:du'], '18-7':['i he:a hate:pr','kjv_imla'],
            '18-12':['one_num agree:ev'], '18-15':['ipl thee:a kjv_adjure:fu'],
            '18-18':['army of heaven','kjv_right_side'],
            '18-19':['one_num of army'], '18-20':['i he:a entice:fu'],
            '18-21':['kjv_lie_false:cv spirit'], '18-26':['until ipl'],
            '18-29':['i myself:a disguise:fu'], '18-33':['kjv_armour_joint','i wound:psv:pr'],
            '19-7':['kjv_favour_partiality:ev'], '19-10':['lest they'],
            '20-3':['kjv_fast'], '20-5':['kjv_court_enclosure'],
            '20-11':['i say:pr','wesg:a'], '20-12':['ourone/eye:pl'],
            '20-15':['but of god'], '20-17':['need:neg:fu'],
            '20-25':['wealth with dead body:pl','kjv_three day:pl'],
            '20-31':['thirty and five','twenty and five'],
            '20-33':['take:psv:neg:pa'], '20-37':['kjv_tarshish'],
        }.items():
            for part in parts:self.assertIn(part,a(r))
        repairs=read(lang.folder/'contextual-host-corrections.json');self.assertEqual(len(repairs),7)
        for c in repairs:
            old=prior.compile(c['beforeAnalysis']);new=lang.compile(c['afterAnalysis'])
            self.assertIn('host',old['keys']);self.assertNotIn('host',new['keys'])
            self.assertIn('kjv_multitude' if c['book']=='genesis' else 'army',new['keys'])
        self.assertNotIn('ipl',lang.compile(a('18-20'))['keys'])
        self.assertNotIn('matter',lang.compile(a('19-11'))['keys'])
        self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-89')
if __name__=='__main__':unittest.main()
