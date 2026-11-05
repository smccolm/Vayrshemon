import unittest
from tools.kjv_archive import load_register,read
class JobOathNewSpeakerTests(unittest.TestCase):
 def test_oath_conditions_voices_and_archaic_senses(self):
  prior,_=load_register('0.10-kjv.105');lang,manifest=load_register('0.10-kjv.106')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'job-oath-new-speaker-cases.json')};self.assertEqual(len(cases),204)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','matter','consume','one','fine','just','render','mark'}&set(out['keys']))
  def a(r):return cases['job-'+r]['analysis']
  for r,parts in {
   '29-4':['my/youth','secret of god'], '29-6':['step:pl:a with butter'],
   '29-10':['kjv_mouth_roof'], '29-17':['thing:a which plunder:psv:pp'],
   '29-18':['as sand'], '29-23':['kjv_latter_rain'],
   '30-2':['old age perish'], '30-4':['kjv_mallows','kjv_juniper root:pl:a for their/food'],
   '30-7':['kjv_nettle'], '30-12':['kjv_right_side'], '30-18':['kjv_garment_collar'],
   '30-22':['substance:a dissolve'], '30-24':['grave stretch:neg'],
   '30-27':['before meet:pa'], '30-28':['without sun'], '30-29':['kjv_dragon_source'],
   '30-31':['kjv_pipe'], '31-10':['my/wife to another kjv_grind:opt'],
   '31-13':['my/kjv_male servant','my/female servant'], '31-15':['one_num we:du:a in womb'],
   '31-18':['he with i','i she:a from my/mother:poss womb'], '31-22':['kjv_shoulder_blade'],
   '31-24':['pure gold'], '31-31':['wesg of his/flesh','wepl satisfy:psv:neg'],
   '31-35':['person i:a hear','write:perf:opt'], '31-40':['kjv_cockle','word:pl of kjv_job_sufferer end'],
   '32-2':['kjv_elihu_job','kjv_barachel','kjv_buzite','kjv_ram_job'],
   '32-8':['kjv_inspiration_breath'], '32-12':['kjv_convince_reprove'],
   '32-13':['wesg wisdom'], '32-18':['full of word:pl'], '32-19':['new kjv_bottle:pl'],
   '33-6':['i according_to thy/wish in kjv_place_site of god'],
   '33-10':['as his/enemy regard'], '33-11':['path:pl:a observe'],
   '33-12':['kjv_just_fair'], '33-14':['one_num time','two time:pl'],
   '33-23':['one_num among thousand'], '33-24':['ipl ransom:a find'],
   '33-27':['kjv_just_fair','gain:ev:a bring:neg'], '33-29':['often'],
   '34-4':['wesg judgment:a','wepl among ourselves'], '34-6':['my/right'],
   '34-17':['justice:a hate','most kjv_just_fair'], '34-19':['face:pl:a of prince:pl accept:neg'],
   '34-23':['more than kjv_just_fair'], '34-31':['i kjv_chastise:ev:a bear'],
   '34-36':['my/desire','until end test'], '34-37':['among wepl'],
   '35-2':['my/kjv_righteousness more than god:poss'],
   '35-3':['advantage to thee','gain:a i have','from my/sin clean'],
   '35-11':['wesg:a more than beast:pl','wesg:a more wise than bird:pl'],
   '35-15':['because it so be:neg','anger visit:perf','know:neg:pr'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),16)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-105')
if __name__=='__main__':unittest.main()
