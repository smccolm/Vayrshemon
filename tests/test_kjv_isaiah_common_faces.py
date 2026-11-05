import unittest,re
from tools.kjv_archive import load_register,read
class IsaiahCommonFacesTests(unittest.TestCase):
 def test_communal_faces_divergent_ways_and_unsoftened_source(self):
  prior,_=load_register('0.10-kjv.138');lang,manifest=load_register('0.10-kjv.139')
  self.assertEqual(prior.lexicon,lang.lexicon)
  for attr in('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('isaiah-'):c for c in read(lang.folder/'isaiah-common-faces-and-divergent-ways-cases.json')};self.assertEqual(len(cases),91)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','dumb','count','host','kjv_rahab','kjv_rahab_psalm','kjv_slaughter'}&set(result['keys']))
   self.assertNotIn(':du',c['analysis'])
  expected={'i':'','iplself':'','wesg':'50-8 53-2 53-3 53-4 53-5 53-6','wepl':'51-23','ourone':'52-10 53-1 53-3 53-4 53-5 55-7'}
  for k,refs in expected.items():self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in{
   '50-1':['mypl/kjv_creditor:pl','you yourselves:a sell:perf'],
   '50-4':['lord god to ipl tongue:a','morning by morning'],
   '50-6':['hair:a off pluck:pa','kjv_spit:ev hide:neg:pa'],
   '50-8':['wesg together stand:opt'],
   '51-9':['kjv_rahab_broken:a cut:perf','dragon:a wound:perf'],
   '51-12':['ipl even ipl he'],
   '51-14':['die:neg:should','bread fail:neg:should'],
   '51-15':['kjv_lord of army:pl his/name'],
   '51-16':['heaven:pl:a plant:may'],
   '51-19':['two thing:pl','kjv_desolate:ev and destroy:ev and kjv_famine and sword'],
   '51-21':['drunken but not with wine'],
   '51-23':['wepl over go:may','thy/body:a as ground and as street'],
   '52-1':['kjv_circumcise:psv:neg:adj'],
   '52-2':['rise:imp and down sit:imp'],
   '52-7':['thy/god rule:pr:excl'],
   '52-11':['vessel:pl:a of kjv_lord carry:pr'],
   '52-12':['your/kjv_rearguard'],
   '52-15':['kjv_sprinkle:fu'],
   '53-3':['ourone/face:pl:a'],
   '53-5':['kjv_chastise:ev of ourone/peace','kjv_stripe_blow:pl wesg heal:psv:pr'],
   '53-6':['all wesg like sheep','wesg each to his/own way','kjv_iniquity:a of all wesg'],
   '53-7':['kjv_lamb to kill:ev','kjv_mute','mouth:a open:neg:pa','mouth:a open:neg:pr'],
   '53-8':['my/people'],
   '53-9':['with rich in his/death because','no kjv_violence','mouth be:neg:pa'],
   '53-10':['kjv_lord:a kjv_please_satisfy:pa to he:a kjv_bruise:inf','kjv_seedline:a','day:pl:a long:caus:fu'],
   '53-11':['kjv_toil of his/soul','mypl/kjv_righteous servant'],
   '53-12':['ipl to he part:a with great kjv_divide:fu','for transgress:ag:pl pray:pa'],
   '54-1':['kjv_travail:neg:pa','kjv_desolate_person'],
   '54-2':['kjv_pin:pl:a strengthen:imp'],
   '54-3':['right side and on left','kjv_seedline'],
   '54-5':['thy/make:ag thy/husband'],
   '54-15':['not by ipl'],
   '54-16':['waste:ag:a to destroy:inf create:perf'],
   '55-1':['without money and without price'],
   '55-8':['mypl/thought:pl your/thought:pl be:neg:pr'],
   '55-10':['seed:a to kjv_sow:ag'],
   '55-11':['mypl/word','to ipl empty return:neg:fu'],
   '55-12':['all kjv_tree:pl of field their/hand:pl:a kjv_clap_hands:fu']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertNotIn('mypl/',cases['53-8']['analysis'])
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
