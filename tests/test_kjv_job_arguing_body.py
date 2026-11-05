import unittest
from tools.kjv_archive import load_register,read
class JobArguingBodyTests(unittest.TestCase):
 def test_collective_claims_mortal_pair_and_kjv_bodily_readings(self):
  prior,_=load_register('0.10-kjv.103');lang,manifest=load_register('0.10-kjv.104')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'job-arguing-body-cases.json')};self.assertEqual(len(cases),186)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','matter','right','please','consume','one','tabernacle','kjv_lean_body'} & set(out['keys']))
  def a(r):return cases['job-'+r]['analysis']
  for r,parts in {
   '15-7':['first man'], '15-9':['wesg know:neg:pr'], '15-10':['with wepl'],
   '15-20':['kjv_number:ev of year:pl'], '15-26':['kjv_shield_boss:pl'],
   '15-27':['kjv_fat_collop:pl'], '15-34':['kjv_congregation_general'],
   '16-4':['if your/soul','gather:pa:can'], '16-7':['he i:a weary','thou all my/company'],
   '16-8':['my/thin:ev'], '16-9':['kjv_gnash'], '16-13':['my/kjv_kidney:pl','my/kjv_gall_bitter'],
   '16-19':['my/kjv_record_witness'], '16-21':['plead:may:excl'], '16-22':['return:neg:fu'],
   '17-1':['kjv_corrupt_decay'], '17-5':['kjv_flatter'], '17-6':['in former time','as kjv_tabret'],
   '17-10':['one_num wise man'], '17-14':['my/mother and my/sister'], '17-16':['ourone/rest'],
   '18-2':['wesg speak'], '18-3':['wepl as beast:pl'], '18-9':['rob:ag'],
   '18-13':['first bear:psv:pp of death'], '18-19':['kjv_nephew_posterity'], '18-20':['after he come','before go:pa'],
   '19-3':['ten time:pl'], '19-11':['one_num of his/enemy:pl regard'],
   '19-17':['child:pl of my/own body'], '19-20':['skin of my/tooth:pl'],
   '19-23':['write:psv:opt:excl'], '19-24':['lead_metal'],
   '19-25':['my/redeem:ag live'], '19-26':['worm:pl this body:a','in my/flesh i god:a see'],
   '19-27':['not another','my/kjv_kidney:pl'], '19-28':['wesg he:a persecute','in i find'],
   '20-10':['kjv_please_satisfy'], '20-11':['sin of his/youth'], '20-16':['kjv_viper:g tongue'],
   '20-18':['his/kjv_goods kjv_restitution'], '20-22':['every hand of wicked'],
   '20-24':['bow of steel'], '20-25':['glitter:pp sword'], '20-26':['blow:neg:psv:pp'],
   '21-10':['beget:pr','kjv_miscarry:neg:pr'], '21-12':['kjv_pipe'],
   '21-14':['from wesg depart'], '21-15':['wesg he:a serve','wepl have','wesg to he pray'],
   '21-16':['far from i'], '21-17':['come:pr:excl'], '21-18':['kjv_chaff'],
   '21-24':['his/breast:pl full of milk'], '21-26':['they:du same:adv','they:du:a'],
   '21-30':['to day of destroy:ev'], '21-32':['in tomb remain'], '21-33':['kjv_clod:pl'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),13)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-103')
if __name__=='__main__':unittest.main()
