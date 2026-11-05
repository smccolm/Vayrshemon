import unittest,re
from tools.kjv_archive import load_register,read

class LamentationsUnansweredPrayerTests(unittest.TestCase):
 def test_shifting_selves_and_unresolved_ending(self):
  prior,_=load_register('0.10-kjv.155');lang,manifest=load_register('0.10-kjv.156')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('lamentations-'):c for c in read(lang.folder/'lamentations-civic-self-and-unanswered-prayer-cases.json')};self.assertEqual(len(cases),154)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text']);self.assertNotIn(':du',c['analysis'])
   self.assertFalse({'one','ghost','bow','just','ravish','refuse'}&set(r['keys']))
  for k,refs in {'ipl':'1-11 1-12 1-13 1-14 1-15 1-16 1-18 1-19 1-20 1-21 1-22 2-22','mypl':'1-9 1-12 1-13 1-14 1-15 1-16 1-18 1-19 1-20 1-21 1-22 2-21 2-22','wesg':'2-16 3-22 3-40 3-41 3-42 3-43 3-45 3-46 3-47 4-17 4-18 4-19 4-20 5-1 5-3 5-4 5-5 5-6 5-7 5-8 5-9 5-16 5-20 5-21 5-22','wepl':'','iplself':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in {
   '1-1':['alone sit:pr:excl','kjv_tribute give:ag'],
   '1-7':['her/kjv_sabbath:pl mock:pa'],
   '1-16':['ipl weep:pr mypl/eye mypl/eye'],
   '1-17':['kjv_menstrual_flow'],
   '1-19':['spirit:a up give:pa'],
   '2-6':['cause:perf that solemn feast:pl','forget:psv:pp'],
   '2-8':['kjv_rampart:a and wall:a lament:caus:pa'],
   '2-11':['my/kjv_liver upon earth'],
   '2-13':['i with thee compare:fu'],
   '2-16':['wesg she:a up kjv_swallow:perf'],
   '2-22':['ipl in cloth wrap:perf'],
   '3-1':['i man who'],
   '3-10':['bear_animal'],
   '3-13':['my/kjv_kidney:pl'],
   '3-22':['wesg consume:psv:neg:pr'],
   '3-24':['my/soul say:pr therefore i'],
   '3-31':['forever off cast:neg:fu'],
   '3-33':['willingly kjv_afflict:neg:pr'],
   '3-35':['right:a of man'],
   '3-38':['evil and good proceed:neg:pr?'],
   '3-42':['thou pardon:neg:perf'],
   '3-44':['thyself:a with cloud','ourone/prayer through pass:neg:should'],
   '3-45':['kjv_offscouring and kjv_refuse_matter'],
   '3-48':['my/eye with river:pl'],
   '3-51':['my/eye my/heart:a touch:pr'],
   '3-58':['kjv_litigate:perf'],
   '3-63':['their/sit:ev:a down','their/rise:ev:a up'],
   '3-66':['persecute:imp and destroy:imp'],
   '4-3':['kjv_sea_monster:pl','suck:caus:pr'],
   '4-7':['her/kjv_nazarite:pl','kjv_sapphire'],
   '4-10':['compassionate woman:pl','their/own child:pl:a boil:perf'],
   '4-20':['anoint:psv:adj of kjv_lord','wesg say:pa'],
   '4-22':['kjv_zion','carry:neg:fu','kjv_edom'],
   '5-3':['wesg kjv_orphan:pl and kjv_fatherless','as widow:pl'],
   '5-7':['ourone/father:pl sin:perf and be:neg:pr','wesg their/kjv_iniquity:pl:a carry:perf'],
   '5-11':['rape:pa'],
   '5-16':['wesg sin:perf:excl'],
   '5-21':['wesg:a to thee turn:imp','wesg turn:psv:fu'],
   '5-22':['but thou wesg:a completely reject:perf','against wesg very angry']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),5)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
