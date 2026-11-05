import unittest
from tools.kjv_archive import load_register,read
class PsalmParallelsVoicesTests(unittest.TestCase):
 def test_parallel_readings_and_contextual_voice(self):
  prior,_=load_register('0.10-kjv.108');lang,manifest=load_register('0.10-kjv.109')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'psalms-parallels-voices-cases.json')};self.assertEqual(len(cases),177)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','one','just','host','raven','band','act','consume'}&set(out['keys']))
  for ref,parts in {
   '13-4':['my/enemy say','i against he prevail'], '14-3':['no not one_num'],
   '14-4':['my/people:a up eat'], '15-3':['kjv_backbite:neg','do:neg','take:neg'],
   '16-2':['my/goodness to thee extend:neg'], '16-5':['kjv_lot_portion'],
   '16-7':['my/kjv_kidney:pl'], '16-10':['thy/kjv_holy_one','kjv_corrupt_decay:ev'],
   '17-1':['right:a hear'], '17-2':['my/sentence','kjv_just_fair'],
   '17-11':['wepl:a in our/step'], '17-13':['before meet','who thy/sword'],
   '17-14':['who thy/hand','remainder:a'], '18-4':['sorrow:pl of death'],
   '18-7':['kjv_foundation:pl also of hill:pl'], '18-10':['he upon wing:pl of wind fly'],
   '18-11':['his/secret kjv_place_site','his/kjv_pavilion'],
   '18-12':['cloud:pl pass','hail stone:pl'], '18-13':['hail stone:pl'],
   '18-15':['kjv_water_channel','thy/rebuke'], '18-18':['before i','my/support:ev'],
   '18-22':['his/kjv_statute:pl:a from i away put:neg'],
   '18-24':['kjv_cleanness of my/hand:pl'], '18-26':['thyself:a kjv_froward'],
   '18-27':['high look:pl:a down bring'], '18-28':['my/candle:a kjv_kindle_fire'],
   '18-31':['ourone/god'], '18-35':['thy/kjv_right_side hand'],
   '18-37':['ipl mypl/enemy','overtake','destroy:psv'], '18-41':['they cry:pa'],
   '18-42':['dust before wind','earth in street'],
   '18-43':['head of kjv_heathen make','whom i know:neg','ipl:a serve'],
   '18-44':['as soon as','they ipl:a obey'], '18-48':['lift:pr'],
   '18-50':['great deliver:ev','kjv_david'],
   '19-3':['no speech nor language','hear:psv:neg'], '19-4':['their/line'],
   '19-7':['kjv_simple_inexperienced'], '20-5':['wesg','ourone/banner'],
   '20-6':['now i know'], '20-8':['wepl rise','straight stand'],
   '20-9':['king wepl:a hear','wesg call'], '21-13':['wesg thy/power'],
   '22-1':['my/god my/god','forsake:perf'], '22-4':['ourone/father:pl'],
   '22-13':['ravenous and roar:cv lion'], '22-15':['kjv_cleave_adhere'],
   '22-16':['my/hand:pl and my/foot:pl:a pierce'], '22-17':['kjv_number:can'],
   '22-18':['kjv_lot:pl'], '22-20':['my/darling'],
   '22-21':['kjv_unicorn:pl','hear:perf'], '22-31':['born:psv:fu','he this:a do:perf'],
   '23-1':['i lack:neg:fu'], '23-2':['lie:caus'], '23-4':['thou with i'],
   '24-2':['kjv_found_base','upon flood:pl'], '24-6':['kjv_jacob:excl'],
   '24-7':['lift:psv:imp'], '24-9':['they:a up lift:imp'], '24-10':['army:pl'],
  }.items():
   for p in parts:self.assertIn(p,cases['psalms-'+ref]['analysis'])
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),10)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-108')
if __name__=='__main__':unittest.main()
