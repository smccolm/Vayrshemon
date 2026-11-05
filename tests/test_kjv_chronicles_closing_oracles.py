import unittest
from tools.kjv_archive import load_register,read
class ChroniclesClosingOraclesTests(unittest.TestCase):
 def test_personal_wound_collective_crowns_and_unharmonized_source(self):
  prior,_=load_register('0.10-kjv.93');lang,manifest=load_register('0.10-kjv.94')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'chronicles-closing-oracles-cases.json')};self.assertEqual(len(cases),108)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss'])
  def a(r):return cases['2-chronicles-'+r]['analysis']
  for r,parts in {
   '33-3':['kjv_multitude of heaven'],
   '33-4':['mypl/name'],
   '33-6':['his/child:pl','kjv_observe_times','kjv_familiar_spirit'],
   '33-8':['foot of kjv_israel','your/father:pl','so that'],
   '33-11':['captain:pl of army','among thorn:pl'],
   '33-17':['their/god only'],
   '34-2':['kjv_right_conduct','kjv_right_side'],
   '34-6':['their/kjv_mattock:pl'],
   '34-8':['kjv_record_keeper'],
   '34-15':['i book of law'],
   '34-18':['to i book:a'],
   '34-20':['kjv_abdon_micah','kjv_asaiah_josiah'],
   '34-21':['for ipl','upon wesg','ourone/father:pl'],
   '34-22':['kjv_tikvath son of kjv_hasrah','kjv_college_locality'],
   '34-23':['to i send:pa'],
   '34-24':['ipl evil:a','all curse:pl'],
   '34-28':['thy/grave in peace'],
   '35-3':['kjv_ark_chest','your/kjv_shoulder:pl'],
   '35-7':['thirty+thousand, and kjv_three+thousand'],
   '35-13':['roast:pa','boil:pa','kjv_pan_cooking'],
   '35-21':['ipl against thee this day come:neg:pr','god ipl:a'],
   '35-22':['word:pl of kjv_necho from mouth of god'],
   '35-23':['i:a away take:imp','i kjv_grievous:adv wound:psv:pr'],
   '35-24':['kjv_jerusalem bring:pa and he die:pa'],
   '36-3':['at kjv_jerusalem'],
   '36-9':['eight year:pl','kjv_three month:pl and ten day:pl'],
   '36-10':['kjv_zedekiah_king his/brother'],
   '36-15':['early rise:cv'],
   '36-21':['kjv_three+twenty and ten year:pl'],
   '36-23':['to ipl give:perf','he ipl:a charge:perf'],
  }.items():
   for part in parts:self.assertIn(part,a(r))
  self.assertNotIn('ipl',lang.compile(a('35-23'))['keys'])
  for c in cases.values():self.assertFalse({'host','recorder','right','rest','commit','one'} & set(lang.compile(c['analysis'])['keys']))
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-93')
if __name__=='__main__':unittest.main()
