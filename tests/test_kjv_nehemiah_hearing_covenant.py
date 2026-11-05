import unittest
from tools.kjv_archive import load_register,read
class NehemiahHearingCovenantTests(unittest.TestCase):
 def test_corporate_body_source_senses_and_binding_obligations(self):
  prior,_=load_register('0.10-kjv.98');lang,manifest=load_register('0.10-kjv.99')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'nehemiah-hearing-covenant-cases.json')};self.assertEqual(len(cases),95)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text']);self.assertNotIn('ipl',result['keys'])
  def a(r):return cases['nehemiah-'+r]['analysis']
  for r,parts in {
   '8-1':['as one_num man'], '8-2':['man:pl and woman:pl','with understanding'],
   '8-4':['his/kjv_right_side hand','his/left hand'], '8-6':['amen amen','their/face:pl'],
   '8-8':['meaning:a give:pa'], '8-10':['kjv_fat:a','for whom nothing prepare:psv:pr'],
   '8-15':['kjv_pine_tree','kjv_myrtle_tree'], '8-17':['kjv_jeshua_nun son of kjv_nun','do:neg:pp'],
   '9-3':['one_num fourth part','another fourth part'], '9-6':['thou even thou kjv_lord alone'],
   '9-8':['i say:pr'], '9-18':['kjv_cast_metal:psv:pp kjv_calf','this thy/god'],
   '9-25':['kjv_well:pl kjv_dig:psv:pr'], '9-28':['rest:a have:pa'],
   '9-30':['patient:adv endure:pa'], '9-33':['kjv_right_conduct:a','wesg wicked:adv'],
   '9-37':['our/body:pl','ourone/sin:pl','at their/pleasure'],
   '10-1':['kjv_zidkijah'], '10-6':['kjv_ginnethon_signer_priest'],
   '10-8':['kjv_bilgai_signer_priest'], '10-13':['kjv_beninu_signer_levite'],
   '10-14':['kjv_zatthu_signer_chief'], '10-17':['kjv_hizkijah_signer_chief'],
   '10-28':['their/wife:pl their/son:pl and their/daughter:pl'],
   '10-29':['into curse and into oath'], '10-32':['kjv_third_share of kjv_shekel'],
   '10-33':['kjv_continual_rite kjv_meat_offering'], '10-38':['tithe of tithe:pl'],
   '10-39':['wesg house of ourone/god:a forsake:neg:fu'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(a('9-4').count('kjv_bani_teacher'),2)
  self.assertEqual(a('9-6').count('kjv_multitude'),2)
  self.assertEqual(a('9-36').count('wesg servant:pl'),2)
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),112)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-98')
if __name__=='__main__':unittest.main()
