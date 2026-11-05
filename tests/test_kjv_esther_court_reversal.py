import unittest
from tools.kjv_archive import load_register,read
class EstherCourtReversalTests(unittest.TestCase):
 def test_court_number_source_variants_and_unsoftened_reversal(self):
  prior,_=load_register('0.10-kjv.100');lang,manifest=load_register('0.10-kjv.101')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'esther-court-reversal-cases.json')};self.assertEqual(len(cases),167)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','matter','right','please','force','consume','god','yahweh'} & set(out['keys']))
  def a(r):return cases['esther-'+r]['analysis']
  for r,parts in {
   '1-4':['hundred and four+twenty'], '1-8':['none compel:pa'],
   '1-10':['kjv_harbona','seven kjv_chamberlain'], '1-15':['wesg'],
   '1-19':['change:psv:neg:pr'], '2-3':['kjv_hege'], '2-8':['kjv_hegai'],
   '2-12':['twelve month:pl','six month:pl with oil of kjv_myrrh','six month:pl with sweet smell:pl'],
   '2-21':['kjv_bigthan and kjv_teresh'], '2-23':['they:du both'],
   '3-7':['kjv_pur that be:pr kjv_lot'], '3-9':['i ten+thousand'],
   '3-12':['kjv_lieutenant_province:pl','kjv_governor:pl'],
   '3-13':['little child:pl and woman:pl','their/spoil:a'],
   '4-14':['from another kjv_place_site','who know:pr whether'],
   '4-16':['if i perish:pr i perish:pr'], '5-4':['i for he prepare:perf'],
   '5-8':['i for they prepare:fu'], '5-14':['fifty kjv_cubit:pl'],
   '6-2':['kjv_bigthana'], '6-9':['one_num of king:poss most noble prince:pl'],
   '7-4':['wesg sell:psv:perf i and my/people','wepl for slave:pl and female slave:pl'],
   '7-8':['before i','kjv_force_assault:fu?'], '7-9':['kjv_harbonah'],
   '8-5':['letter:pl:a reverse:inf'], '8-7':['ipl house of kjv_haman'],
   '8-8':['you:du','no man reverse:may'], '8-9':['twenty and kjv_three:ord','hundred and twenty and seven'],
   '8-10':['young kjv_dromedary:pl'], '8-11':['both little one:pl and woman:pl','spoil:a for prey'],
   '8-17':['kjv_jew:pl become:pa','fear of kjv_jew:pl'],
   '9-9':['kjv_arisai and kjv_aridai'], '9-10':['slay:pa','lay:neg:pa'],
   '9-12':['remain:cv part'], '9-13':['tomorrow also','hang:psv:opt'],
   '9-16':['seven+ten+thousand and five+thousand','lay:neg:pa'],
   '9-18':['ten and five:ord'], '9-22':['kjv_foodportion:pl','gift:pl to poor'],
   '9-29':['second letter'], '9-30':['and he letter:pl'],
   '10-3':['his/people:poss good:a seek:cv'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),57)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-100')
if __name__=='__main__':unittest.main()
