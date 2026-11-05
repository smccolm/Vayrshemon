import unittest
from tools.kjv_archive import load_register,read
class PsalmChorusIdentityTests(unittest.TestCase):
 def test_personal_shared_and_requested_divine_voices(self):
  prior,_=load_register('0.10-kjv.109');lang,manifest=load_register('0.10-kjv.110')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'psalms-chorus-identity-cases.json')};self.assertEqual(len(cases),199)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','just','host','raven','band','act','consume','fast','plain','render','fashion'}&set(out['keys']))
  for ref,parts in {
   '25-7':['remember:neg:imp','thy/goodness:poss sake'],
   '25-11':['pardon:imp for it great'], '25-16':['kjv_desolate_person','kjv_afflict:psv'],
   '25-17':['heart grow:pr'], '25-22':['kjv_israel:a redeem'],
   '26-2':['my/kjv_kidney:pl'], '26-7':['publish:may','tell:may'],
   '26-10':['kjv_right_side hand','kjv_bribe:pl'], '26-12':['in level kjv_place_site'],
   '27-3':['army','kjv_encamp:should','rise:should'], '27-4':['one_num thing'],
   '27-8':['you:pl mypl/face:a seek:imp','my/heart','i seek:fu'],
   '27-9':['hide:neg','put:neg','leave:neg','forsake:neg'],
   '27-11':['level path'], '27-13':['i would faint be:pp unless'],
   '28-2':['kjv_oracle_chamber'], '28-4':['their/desert:a repay'],
   '28-5':['destroy:fu','build:neg:fu'], '28-8':['their/strength'],
   '29-6':['kjv_sirion','young kjv_unicorn'],
   '29-9':['hind:pl:a born:caus','forest:pl:a kjv_uncover','everyone'],
   '30-1':['rejoice:caus:neg:perf'], '30-5':['but moment','weep:ev for night'],
   '30-7':['my/mountain:a strong stand:caus'], '30-12':['my/glory','silent be:neg:may'],
   '31-5':['i my/spirit:a commit'], '31-6':['kjv_lie_false:ev vanity:pl'],
   '31-9':['eye with grief waste:psv','my/belly'], '31-11':['outside see'],
   '31-17':['ashamed be:neg','wicked ashamed','in grave silent'],
   '31-22':['in my/haste say','nevertheless'],
   '32-2':['kjv_impute:neg','no kjv_guile'], '32-3':['silence:a keep','my/roar:ev'],
   '32-5':['acknowledge:pr','hide:neg:perf','confess:fu','forgive:pa'],
   '32-8':['i thee:a instruct','with my/eye'],
   '32-9':['kjv_horse_bit','lest they near to thee come'],
   '33-2':['ten string:pl'], '33-6':['their/army','breath of his/mouth'],
   '33-9':['kjv_firmly stand'], '33-15':['equally shape'],
   '33-20':['ourone/soul','ourone/help'], '33-21':['ourone/heart','wesg'],
   '33-22':['upon wesg','as wesg'], '34-3':['with i','wesg his/name'],
   '34-5':['light:caus:psv:pa'], '34-9':['no lack'],
   '34-18':['kjv_contrite spirit'], '34-20':['not one_num'],
   '35-3':['say:imp ipl thy/salvation'], '35-6':['kjv_slippery'],
   '35-13':['with kjv_fast:ev','own bosom return'],
   '35-14':['as though','friend or brother'], '35-15':['kjv_abject:pl'],
   '35-17':['my/darling'], '35-18':['i to thee thanks'],
   '35-21':['ah:excl ah:excl','ourone/eye'],
   '35-25':['wesg it:a would have','wesg he:a up kjv_swallow'],
   '36-1':['within my/heart','before his/eye:pl'], '36-8':['fat:ev','drink:caus'],
   '36-9':['wesg light:a see'], '36-11':['against i','i:a remove:neg'],
   '36-12':['fall:perf','cast:psv:pr','rise:neg:can:fu'],
  }.items():
   for p in parts:self.assertIn(p,cases['psalms-'+ref]['analysis'])
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),4)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-109')
if __name__=='__main__':unittest.main()
