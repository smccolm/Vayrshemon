import unittest
from tools.kjv_archive import load_register,read
class PsalmCorporateSelfTests(unittest.TestCase):
 def test_composite_people_physical_members_and_divine_declaration(self):
  prior,_=load_register('0.10-kjv.110');lang,manifest=load_register('0.10-kjv.111')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'psalms-corporate-personal-cases.json')};self.assertEqual(len(cases),198)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','one','just','host','raven','band','act','consume','fast','plain','render','fashion','bay','conversation','corrupt','dumb','dragon','mark','shield'}&set(out['keys']))
  for ref,parts in {
   '37-3':['feed:psv:fu'], '37-12':['kjv_just_fair'], '37-14':['kjv_upright behaviour'],
   '37-20':['into smoke','waste:fu'], '37-25':['i young be:perf','see:neg:perf'],
   '37-35':['kjv_bay_tree'], '37-37':['observe:imp'],
   '38-2':['kjv_firmly stick'], '38-3':['no health','my/sin'],
   '38-5':['kjv_corrupt_decay'], '38-7':['kjv_loins','kjv_loathsome illness'],
   '38-13':['kjv_deaf','kjv_mute'], '38-17':['kjv_limp:inf'],
   '38-20':['evil for good repay'], '39-5':['kjv_handbreadth','age as nothing'],
   '39-10':['strike:ev of thy/hand'], '39-12':['stranger with thee','kjv_sojourn:ag'],
   '39-13':['no more be:pr'], '40-3':['ourone/god'], '40-5':['towards wesg','if i would'],
   '40-6':['my/ear:pl:a thou open','require:neg'], '40-7':['scroll of book'],
   '40-9':['i kjv_righteousness:a','proclaim:perf'], '40-12':['kjv_innumerable','hair:pl'],
   '41-3':['thou all his/bed:a'], '41-8':['they say','kjv_cleave_adhere','he lie:pr'],
   '41-9':['familiar friend','heel:a'], '41-10':['i they:a repay:may'],
   '42-1':['kjv_hart','kjv_pant'], '42-3':['my/food'],
   '42-5':['his/face'], '42-6':['kjv_hermonites','kjv_mizar'],
   '42-7':['kjv_waterspout'], '42-11':['health of my/face'], '43-5':['health of my/face'],
   '44-1':['wepl with our/ear:pl','ourone/father:pl wesg:a'],
   '44-4':['mypl/king'], '44-5':['wepl our/enemy:pl'],
   '44-6':['ipl in mypl/bow','mypl/sword ipl:a'],
   '44-8':['wesg all day long boast'], '44-9':['wesg:a to shame','our/army:pl'],
   '44-10':['wepl:a','turn:caus'], '44-11':['wepl:a like sheep','scatter:perf'],
   '44-13':['wesg:a kjv_reproach'], '44-15':['mypl/confusion','mypl/face ipl:a'],
   '44-17':['wesg thee:a forget:neg'], '44-18':['ourone/heart','our/step:pl'],
   '44-19':['wepl:a greatly','kjv_dragon_source'],
   '44-20':['if wesg','ourone/god','our/hand:pl'],
   '44-22':['wepl all day long kill','wepl as sheep'],
   '44-23':['why thou sleep','wesg:a'], '44-25':['ourone/soul','ourone/belly'],
   '45-1':['compose:prog','i of thing:pl'], '45-6':['thy/throne god:excl','kjv_just_fair sceptre'],
   '45-7':['god thy/god'], '45-8':['kjv_lign_aloes','kjv_ivory'],
   '45-11':['thy/lord','worship:imp'], '45-17':['i thy/name:a','remember:psv:caus:fu'],
   '46-2':['wesg fear:neg','though earth'], '46-5':['very early'],
   '46-10':['ipl god be:pr','ipl among kjv_heathen','ipl in earth'],
   '47-3':['under wepl','our/foot:pl'], '47-4':['ourone/inheritance:a for wesg'],
   '47-9':['kjv_shield_armour:pl'], '48-8':['wepl hear:perf','wepl in city','ourone/god'],
   '48-9':['wesg'], '48-12':['kjv_number:imp'],
   '48-13':['kjv_defensive_bulwark','observe:imp','generation tell:may'],
   '48-14':['ourone/guide even to death'],
  }.items():
   for p in parts:self.assertIn(p,cases['psalms-'+ref]['analysis'])
  self.assertEqual(cases['psalms-46-7']['analysis'],cases['psalms-46-11']['analysis'])
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),7)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-110')
if __name__=='__main__':unittest.main()
