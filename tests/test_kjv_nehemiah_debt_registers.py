import unittest
from tools.kjv_archive import load_register,read
class NehemiahDebtRegistersTests(unittest.TestCase):
 def test_internal_coercion_personal_governor_and_conflicting_lists(self):
  prior,_=load_register('0.10-kjv.97');lang,manifest=load_register('0.10-kjv.98')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'nehemiah-debt-registers-cases.json')};self.assertEqual(len(cases),111)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertNotIn('ipl',out['keys'])
  def a(r):return cases['nehemiah-'+r]['analysis']
  for r,parts in {
   '5-1':['their/wife:pl against their/brother:pl'],
   '5-2':['wepl our/son:pl and our/daughter:pl'],
   '5-3':['kjv_mortgage:perf'],
   '5-5':['our/flesh as flesh of our/brother:pl','already into kjv_bondservice'],
   '5-7':['kjv_usury:a demand:pr'],
   '5-8':['wesg after ourone/ability'],
   '5-10':['i likewise and my/brother:pl and my/servant:pl','wesg this kjv_usury:a'],
   '5-11':['hundred:ord part'],
   '5-13':['my/kjv_garment_lap:a shake:pa'],
   '5-14':['twenty:ord','thirty and two:ord','twelve year:pl'],
   '5-18':['one_num ox and six choice sheep','once in ten day:pl'],
   '6-1':['up set:neg:pp'],
   '6-6':['kjv_gashmu'],
   '6-7':['wesg together counsel:a take:opt'],
   '6-9':['wesg:a afraid','my/hand:pl:a strengthen:imp'],
   '6-14':['kjv_prophetess kjv_noadiah_prophetess'],
   '6-15':['twenty and five:ord','fifty and two day:pl'],
   '6-19':['his/good deed:pl','to i:a in fear put:inf'],
   '7-3':['until sun hot','with bar:pl lock:opt'],
   '7-7':['kjv_azariah_return_roster kjv_raamiah kjv_nahamani','kjv_mispereth kjv_bigvai kjv_nehum'],
   '7-15':['kjv_binnui_return_family'],
   '7-43':['kjv_hodevah'],
   '7-44':['hundred and forty and eight'],
   '7-45':['hundred and thirty and eight'],
   '7-62':['six+hundred and forty and two'],
   '7-67':['two+hundred and forty and five'],
   '7-70':['five+hundred and thirty priest:pl:poss garment:pl'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(a('7-73').count('in their/city:pl'),2)
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),34)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-97')
if __name__=='__main__':unittest.main()
