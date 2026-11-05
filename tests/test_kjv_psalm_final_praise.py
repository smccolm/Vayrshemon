import re,unittest
from tools.kjv_archive import load_register,read
class PsalmFinalPraiseTests(unittest.TestCase):
 def test_exile_refrain_legal_verdict_and_plural_numeral_units(self):
  prior,_=load_register('0.10-kjv.119');lang,manifest=load_register('0.10-kjv.120')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id']:c for c in read(lang.folder/'psalms-final-praise-exile-judgment-cases.json')};self.assertEqual(len(cases),225)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','just','host','dragon','mark','hell','suffer','exercise','muse'}&set(out['keys']))
   self.assertNotRegex(c['analysis'],r'(?<![a-z_])(?:ipl|mypl|iplself)(?![a-z_])')
   self.assertNotRegex(c['analysis'],r':(?:can|may|must|should):(?:a|g|i|d)(?:[^a-z]|$)')
  for n in range(1,27):self.assertEqual(cases[f'psalms-136-{n}']['analysis'].count('for his/mercy for ever endure:pr'),1)
  for ref,parts in {
   '135-11':['kjv_canaan_land'], '136-23':['wesg','ourone/'], '136-24':['wesg','ourone/'],
   '137-1':['wepl','wesg'],'137-3':['wepl'],'137-4':['wesg'],'137-5':['i','kjv_right_side'],
   '137-9':['little','stone'], '138-2':['great:caus:perf'], '139-3':['lie'],
   '139-15':['skill:adv work:psv:pa'],'139-16':['my/body part:pl'], '139-21':['hate:neg:pr'],
   '140-12':['right'], '141-10':['while i escape:pr'], '143-2':['kjv_justify'],
   '144-9':['ten string:pl'],'144-12':['grow:perf','smooth:caus:psv:adj'],
   '144-13':['thousand:pl:a and ten+thousand:pl:a'],'144-14':['strong to labour:inf'],
   '145-15':['food'],'146-4':['thought:pl'],'147-4':['kjv_number'],'147-9':['raven'],
   '147-14':['boundary'],'147-16':['kjv_ashes'],'148-7':['kjv_dragon_source'],
   '148-10':['kjv_livestock'],'149-6':['two'],'149-7':['kjv_avenge:ev:a'],'150-4':['kjv_pipe'],
  }.items():
   for part in parts:self.assertIn(part,cases['psalms-'+ref]['analysis'],(ref,part))
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_canaan_land','kjv_justify'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
