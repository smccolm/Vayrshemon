import unittest,re
from tools.kjv_archive import load_register,read
class SongHumanVoicesTests(unittest.TestCase):
 def test_human_chorus_pair_and_source_refrains(self):
  prior,_=load_register('0.10-kjv.128');lang,manifest=load_register('0.10-kjv.129')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('song-of-solomon-'):c for c in read(lang.folder/'song-human-voices-and-communal-refrains-cases.json')};self.assertEqual(len(cases),117)
  voices={k:set() for k in ['wesg','ourone','we:du']}
  for ref,c in cases.items():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'one','fair','right','sound','substance','want','rose','lock','temple','please','ravish','tend'}&set(out['keys']))
   self.assertNotRegex(c['analysis'],r'(?<![a-z_])(?:ipl|mypl|iplself|wepl|they:du|you:du)(?![a-z_])')
   for k in voices:
    if re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis']):voices[k].add(ref)
  self.assertEqual(voices['wesg'],set('1-4 1-11 2-15 5-9 6-1 6-13 8-8 8-9'.split()))
  self.assertEqual(voices['ourone'],set('1-16 1-17 2-9 2-12 2-15 8-8'.split()))
  self.assertEqual(voices['we:du'],{'7-11','7-12','7-13'})
  for ref,parts in {
   '1-2':['he i:a','thy/love:ev'],'1-4':['wesg after thee run:fu','king i:a'],
   '1-5':['i black but beautiful'],'1-6':['my/mother child:pl','mine/own kjv_vineyard:a'],
   '1-7':['human who aside turn:pr'],'1-9':['company of horse:pl'],
   '1-11':['kjv_stud:pl'],'1-13':['all night between my/breast:pl lie:fu'],
   '1-14':['kjv_camphire'],'2-1':['kjv_rose_flower'],'2-5':['kjv_flagon:pl'],
   '2-6':['his/left','his/kjv_right_side'],'2-7':['until he desire:pr'],
   '2-12':['kjv_turtledove'],'2-14':['kjv_stair:pl'],
   '2-16':['my/beloved of i be:pr and i of he be:pr'],
   '3-7':['three+twenty'],'3-9':['chariot:a'],'3-10':['love:ev pave:psv:adj'],
   '3-11':['his/mother he:a crown:pa'],'4-2':['equal:adv shear:psv:pr','each kjv_twin:pl:a bear:pr'],
   '4-3':['kjv_temple_head:pl','kjv_hair_lock:pl'],'4-4':['thousand kjv_buckler:pl'],
   '4-5':['two thy/breast:pl like two young kjv_roe:pl'],'4-9':['my/heart:a capture:perf','one_num of thine eye:pl','one_num chain'],
   '4-16':['my/kjv_garden','his/kjv_garden'],'5-2':['i sleep:pr but my/heart awake:pr'],
   '5-5':['kjv_handle:pl of kjv_lock_fastening'],'5-7':['they i:a strike:pa','they i:a wound:pa','my/kjv_veil:a'],
   '5-10':['ten+thousand'],'5-13':['kjv_garden_bed'],'5-14':['his/hand:pl','his/belly'],
   '6-3':['i of my/beloved be:pr and my/beloved of i be:pr'],
   '6-6':['no one_num among they barren'],'6-8':['three+twenty','four+twenty','without kjv_number'],
   '6-9':['but one_num','only human of her/mother'],'6-12':['before i know:pa','kjv_amminadib'],
   '6-13':['company of two army:pl'],'7-5':['king in kjv_gallery:pl'],
   '7-9':['they who asleep be:pr speak:caus:cv'],'7-10':['his/desire towards i'],
   '8-1':['as my/brother','i thee:a kiss:should'],'8-2':['who i:a instruct:should'],
   '8-3':['embrace:should'],'8-6':['jealousy cruel as grave','most strong flame'],
   '8-7':['all wealth:a'],'8-8':['wesg little sister:a','she no breast:pl:a'],
   '8-9':['if she wall','if she door'],'8-10':['i wall','my/breast:pl like kjv_tower:pl'],
   '8-11':['for pay:ev','thousand piece:pl'],'8-12':['thousand:a','two+hundred:a'],
  }.items():
   for part in parts:self.assertIn(part,cases[ref]['analysis'],(ref,part))
  self.assertEqual(cases['2-7']['analysis'],cases['3-5']['analysis'])
  self.assertNotIn('by kjv_roe:pl',cases['8-4']['analysis'])
  self.assertNotIn('shear',cases['6-6']['analysis']);self.assertNotIn('lily',cases['7-3']['analysis'])
  self.assertEqual(cases['6-13']['analysis'].count('return:imp'),4)
  self.assertEqual(cases['5-9']['analysis'].count('what thy/beloved more than another beloved be:pr'),2)
  additions=set(lang.lexicon)-set(prior.lexicon);self.assertEqual(len(additions),18)
  self.assertEqual(sum(lang.lexicon[k]['pos']=='proper' for k in additions),6)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
