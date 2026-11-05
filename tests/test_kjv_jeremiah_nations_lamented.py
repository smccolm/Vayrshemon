import unittest,re
from tools.kjv_archive import load_register,read

class JeremiahNationsLamentedTests(unittest.TestCase):
 def test_plural_self_lament_and_unharmonized_return_promises(self):
  prior,_=load_register('0.10-kjv.153');lang,manifest=load_register('0.10-kjv.154')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-nations-lamented-and-judged-cases.json')};self.assertEqual(len(cases),86)
  for r,c in cases.items():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text']);self.assertNotIn(':du',c['analysis'])
   self.assertFalse({'one','host','bow','dragon','snuff','ghost','desert','court','bond','count','administer','light','tear','right','leaf','page','commit','plead','former','handle','cleft_lip'}&set(result['keys']))
  for k,refs in {'i':'49-14','wesg':'48-2 48-14 48-29','ourone':'','mypl':'48-31 48-36 49-37 49-38','wepl':'','iplself':'49-13'}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in {
   '48-2':['kjv_madmen','wesg it:a from nation be:ev'],
   '48-10':['deceitful:adv do:pr','his/sword:a from blood back keep:pr'],
   '48-11':['his/kjv_wine_lees','empty:caus:psv:neg:perf','his/odour change:psv:neg:pr'],
   '48-12':['wander:ag:pl:a','wander:caus:fu','his/vessel:pl:a','their/kjv_bottle:pl:a'],
   '48-14':['wesg mighty and strong man:pl'],
   '48-19':['he:a who flee:pr and she:a who escape:pr'],
   '48-26':['his/kjv_vomit:ev roll:fu'],
   '48-29':['(he very proud be:pr)'],
   '48-31':['ipl for kjv_moab howl:fu','mypl/heart'],
   '48-32':['sea of kjv_jazer'],
   '48-33':['their/shout:ev no shout:ev be:fu'],
   '48-34':['kjv_heifer of three year:pl'],
   '48-36':['mypl/heart for kjv_moab like pipe:pl','mypl/heart like pipe:pl'],
   '48-37':['upon all hand:pl cut:ev:pl'],
   '48-41':['kjv_stronghold:pl suddenly take:psv:pr'],
   '48-45':['because of force','head top:a'],
   '48-47':['yet ipl captive:ev:a of kjv_moab again bring:fu'],
   '49-1':['their/king kjv_gad:a inherit:pr'],
   '49-2':['heir to they who his/heir:pl'],
   '49-4':['who to ipl come:fu?'],
   '49-5':['straight forth'],
   '49-9':['leave:neg:should?','until they enough:a have:pr'],
   '49-10':['he be:neg:pr'],
   '49-11':['ipl they:a alive preserve:fu'],
   '49-12':['without punish:ev go:neg:fu'],
   '49-13':['ipl by iplself swear:perf'],
   '49-14':['i rumour:a from kjv_lord'],
   '49-16':['split:ev:pl of rock'],
   '49-19':['ipl suddenly he:a away from she run:caus:fu','who to ipl time:a appoint:fu'],
   '49-20':['least of flock they:a out draw:fu'],
   '49-23':['sorrow on sea'],
   '49-25':['city of my/joy:excl'],
   '49-31':['without worry','neither gate:pl nor bar:pl:a'],
   '49-33':['kjv_dragon_creature:pl'],
   '49-35':['kjv_bow:a of kjv_elam'],
   '49-36':['four wind:pl:a from four quarter:pl','come:neg:fu be:fu'],
   '49-38':['mypl/throne:a in kjv_elam'],
   '49-39':['ipl captive:ev:a of kjv_elam again bring:fu']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(cases['48-36']['analysis'].count('mypl/heart'),2)
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),7)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
