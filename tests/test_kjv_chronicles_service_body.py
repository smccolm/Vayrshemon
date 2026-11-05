import unittest
from tools.kjv_archive import load_register,read
class ChroniclesServiceBodyTests(unittest.TestCase):
 def test_service_body_plural_people_imperial_self_and_remainder(self):
  prior,_=load_register('0.10-kjv.92');lang,manifest=load_register('0.10-kjv.93')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'chronicles-service-body-remainder-cases.json')};self.assertEqual(len(cases),137)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss'])
  def a(r):return cases['2-chronicles-'+r]['analysis']
  for r,parts in {
   '29-5':['i:a hear:imp'],
   '29-10':['my/heart','away from wesg:a'],
   '29-11':['mypl/son:pl'],
   '29-17':['eight:ord day','in eight day:pl','sixteen:ord day'],
   '29-18':['wesg','kjv_table_furniture'],
   '29-19':['wesg prepare:perf'],
   '29-24':['kjv_reconcile_ritual:ev','for all kjv_israel'],
   '29-34':['more kjv_uprightness:adj','than priest:pl'],
   '29-35':['kjv_fat'],
   '30-6':['messenger:pl','remain:cv part'],
   '30-12':['one_num heart'],
   '30-15':['fourteen:ord day of second month'],
   '30-18':['each person:a pardon:opt'],
   '30-19':['though','purify:psv:neg:pr'],
   '30-23':['other seven day:pl keep:inf','other seven day:pl with glad:ev keep:pa'],
   '31-10':['wepl enough:a to eat:inf'],
   '31-16':['kjv_three year:pl old'],
   '31-17':['twenty year:pl old'],
   '32-8':['with wesg','ourone/god','rest:pa'],
   '32-11':['ourone/god wesg:a'],
   '32-12':['one_num altar'],
   '32-13':['ipl and mypl/father:pl'],
   '32-17':['mypl/hand','deliver:neg:fu'],
   '32-30':['kjv_gihon_accession'],
   '32-31':['god he:a leave:pa to he:a try:inf','all:a which in his/heart be:pa know:may'],
   '32-32':['remain:cv part of act:pl'],
  }.items():
   for part in parts:self.assertIn(part,a(r))
  self.assertNotIn('wesg',lang.compile(a('31-10'))['keys'])
  self.assertNotIn('rest',lang.compile(a('32-32'))['keys'])
  repairs=read(lang.folder/'contextual-remainder-corrections.json');self.assertEqual(len(repairs),20)
  for c in repairs:
   before=prior.compile(c['beforeAnalysis']);after=lang.compile(c['afterAnalysis'])
   self.assertEqual(before['text'],c['beforeText']);self.assertEqual(after['text'],c['afterText']);self.assertNotEqual(before['text'],after['text'])
   self.assertIn('rest',before['keys']);self.assertNotIn('rest',after['keys']);self.assertIn('remain',after['keys'])
  self.assertIn('remain:cv part:n',cases['leviticus-5-9']['analysis'])
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-92')
if __name__=='__main__':unittest.main()
