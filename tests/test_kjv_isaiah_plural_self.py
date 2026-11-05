import unittest,re
from tools.kjv_archive import load_register,read
class IsaiahPluralSelfTests(unittest.TestCase):
 def test_plural_self_and_account_specific_language(self):
  prior,_=load_register('0.10-kjv.134');lang,manifest=load_register('0.10-kjv.135')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('isaiah-'):c for c in read(lang.folder/'isaiah-plural-self-and-royal-voices-cases.json')};self.assertEqual(len(cases),93)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','rose','dumb','count','host','table','sieve','fan','profit'}&set(result['keys']))
  expected={'i':'33-24 36-5 36-8 36-10 36-12','ipl':'33-10 33-13 36-5 36-7 36-16 36-17','mypl':'32-18 33-13 34-5 34-16 36-19 36-20','wesg':'32-15 33-2 33-14 33-21 33-22 36-7 36-15 36-18','wepl':'36-11','ourone':'33-2 33-20 33-22 35-2 36-7','iplself':'33-10'}
  for k,refs in expected.items():self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in{
   '32-4':['clearly speak:inf','they who kjv_stammer:pr'],'32-5':['kjv_churl_niggardly','generous'],
   '32-12':['kjv_teat:pl'],'32-13':['my/people'],'32-18':['mypl/people'],
   '33-2':['their/arm','ourone/salvation'],'33-10':['ipl iplself:a up lift:fu'],
   '33-11':['kjv_chaff:a conceive:fu','kjv_stubble:a forth bring:fu'],
   '33-12':['burn:ev:pl of lime'],'33-18':['kjv_tower:pl:a kjv_number:pa'],
   '33-20':['not one_num of its/kjv_pin:pl'],'33-21':['kjv_galley with kjv_oar:pl'],
   '33-23':['kjv_rigging','kjv_mast','sail','kjv_lame'],
   '34-5':['mypl/sword','kjv_idumea'],'34-7':['kjv_unicorn:pl'],
   '34-9':['stream:pl into pitch'],'34-14':['kjv_satyr','screech:adj owl'],
   '34-15':['kjv_hatch:fu','each with her/companion'],
   '34-16':['not one_num','mypl/mouth','his/spirit'],
   '35-1':['kjv_rose_flower'],'35-6':['kjv_mute'],'35-7':['dry ground'],
   '35-8':['for those','though fool:pl'],
   '36-1':['fourteen:ord year'],'36-2':['he by kjv_conduit'],
   '36-5':['i say:pr thou say:pr','i counsel:a','against ipl'],
   '36-7':['thou to ipl','wesg in kjv_lord ourone/god'],
   '36-8':['please','i two+thousand horse:pl:a'],
   '36-9':['one_num captain'],'36-10':['against this land'],
   '36-11':['wepl it:a understand:pr','to wepl'],
   '36-12':['kjv_dung:a','kjv_urine:a'],'36-14':['deliver:neg:can:fu'],
   '36-16':['with ipl','his/own kjv_cistern'],
   '36-19':['kjv_arphad','mypl/hand'],'36-21':['they silent remain:pa']
  }.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  for r,phrase,n in[('32-8','generous',3),('33-10','now ipl',3),('33-14','who among wesg',2),('33-22','kjv_lord ourone/',3),('36-20','mypl/hand',2)]:self.assertEqual(cases[r]['analysis'].count(phrase),n)
  for r,banned in{'36-2':['kjv_tartan','kjv_rabsaris'],'36-14':['out of his/hand'],'36-17':['oil','honey','die:pr'],'36-19':['kjv_hena','kjv_ivah']}.items():
   for part in banned:self.assertNotIn(part,cases[r]['analysis'])
  comparisons=read(lang.folder/'isaiah36-comparison.json');self.assertEqual(len(comparisons),22)
  self.assertEqual([x['reference'] for x in comparisons if x['exact']],['Isaiah 36:9'])
  self.assertEqual(cases['36-9']['analysis'],next(x for x in comparisons if x['exact'])['priorAnalysis'])
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_churl_niggardly','kjv_teat','kjv_oar','kjv_galley','kjv_rigging','kjv_hatch','kjv_idumea','kjv_arphad'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
