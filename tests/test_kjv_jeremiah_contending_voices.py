import unittest,re
from tools.kjv_archive import load_register,read
class JeremiahContendingVoicesTests(unittest.TestCase):
 def test_communities_negations_and_bird_senses(self):
  prior,_=load_register('0.10-kjv.142');lang,manifest=load_register('0.10-kjv.143')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-contending-communities-and-unheeded-word-cases.json')};self.assertEqual(len(cases),117)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertNotIn(':du',c['analysis']);self.assertFalse({'one','host','lead','bow','pitch','tear','kjv_swallow','kjv_flood_ark'}&set(result['keys']))
  for k,refs in {'i':'5-4 5-5 6-10 6-11 8-6 8-18 8-21','wesg':'5-12 5-19 5-24 6-4 6-5 6-16 6-17 6-24 6-26 7-10 8-8 8-14 8-15 8-20','ourone':'5-19 5-24 6-24 8-14','wepl':'','iplself':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in {
   '5-1':['if you human:a find:can'],'5-3':['grief:a feel:neg:perf'],
   '5-5':['i to great human:pl','all together yoke:a break:perf'],
   '5-6':['wolf of evening:pl','into piece:pl rend:psv:fu'],'5-8':['each after his/neighbour/wife neigh:pa'],
   '5-10':['kjv_battlement','full end:a make:neg:imp'],'5-12':['evil upon wesg'],
   '5-14':['mypl/word:pl:a in thy/mouth fire','this people:a wood'],
   '5-16':['kjv_quiver as open tomb'],'5-17':['which thy/son:pl and thy/daughter:pl eat:should'],
   '5-22':['sand:a for boundary of sea'],'5-24':['neither they in their/heart','wesg kjv_lord ourone/god:a fear:imp'],
   '5-27':['kjv_bird_cage'],'5-28':['right:a of kjv_needy','yet they prosper:pr'],
   '5-31':['priest:pl by their/means rule:pr'],
   '6-4':['wesg at noon up go:imp'],'6-5':['wesg her/palace:pl:a destroy:imp'],
   '6-6':['kjv_siege_mound'],'6-10':['i speak:fu','their/ear kjv_circumcise:psv:neg:adj'],
   '6-11':['i full of fury of kjv_lord','i it:a upon child:pl'],
   '6-12':['ipl mypl/hand:a'],'6-14':['peace peace when no peace'],
   '6-16':['wesg in it walk:neg:fu'],'6-17':['wesg heed:neg:fu'],
   '6-20':['kjv_sweet_cane'],'6-24':['ourone/hand:pl'],'6-26':['daughter of my/people','upon wesg'],
   '6-27':['kjv_tower and fortress'],'6-29':['bellows burn:psv:pr','lead_metal','kjv_founder_metal'],
   '7-4':['temple of kjv_lord temple of kjv_lord temple of kjv_lord'],
   '7-10':['wesg deliver:psv:pr to all these kjv_abomination:pl:a do:inf'],
   '7-16':['pray:neg:imp','neither cry nor prayer','neither to ipl for they plead:imp','hear:neg:fu'],
   '7-18':['queen of heaven'],'7-22':['speak:neg:pa nor they:a command:pa'],
   '7-25':['daily early up rise:cv'],'7-31':['command:neg:pa','neither it into mypl/heart'],
   '7-33':['kjv_corpse:pl','none they:a away frighten:fu'],
   '8-2':['gather:psv:neg:fu nor bury:psv:fu'],'8-6':['ipl heed:pa','what i do:perf'],
   '8-7':['kjv_stork','kjv_turtledove','kjv_crane_bird','kjv_swallow_bird'],
   '8-8':['wesg wise be:pr','in vain he it:a make:pa','pen of kjv_scribe:pl in vain'],
   '8-14':['kjv_gall_bitter'],'8-16':['kjv_snort:ev','neigh:ev'],
   '8-18':['i myself:a','comfort:inf wish:pr'],'8-19':['daughter of my/people','why they ipl:a'],
   '8-20':['wesg save:psv:neg:pr'],'8-21':['i black be:pr'],
   '8-22':['no kjv_balm in kjv_gilead','recover:psv:neg:pr']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_battlement','kjv_bird_cage','kjv_snort'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
