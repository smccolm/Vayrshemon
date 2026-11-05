import unittest,re
from tools.kjv_archive import load_register,read
class JeremiahCivicSelfTests(unittest.TestCase):
 def test_quoted_speaker_boundaries_and_concrete_senses(self):
  prior,_=load_register('0.10-kjv.141');lang,manifest=load_register('0.10-kjv.142')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-personal-messenger-and-civic-self-cases.json')};self.assertEqual(len(cases),112)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertNotIn(':du',c['analysis'])
   self.assertFalse({'one','host','stocks','snuff','fan','bow','right','administer','kjv_flood_ark','kjv_fallow_deer','kjv_hilkiah_priest'}&set(result['keys']))
  for k,refs in {'i':'1-4 1-6 1-7 1-9 1-11 1-12 1-13 1-14 2-1 3-6 3-11 4-10 4-19 4-21 4-23 4-24 4-25 4-26 4-31','wesg':'2-6 2-27 2-31 3-22 3-25 4-5 4-8 4-13','ourone':'3-22 3-23 3-24 3-25','wepl':'','iplself':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in {
   '1-1':['kjv_hilkiah_jeremiah'],'1-2':['twelve and one_num:ord'],'1-3':['eleven:ord','five:ord'],
   '1-5':['before ipl thee:a in belly form:pa'],'1-6':['i speak:neg:can','god:excl'],
   '1-7':['i child be:pr say:neg:imp','ipl thee:a send:fu'],'1-9':['my/mouth','mypl/word:pl'],
   '1-13':['its/face towards kjv_north'],'1-14':['out of kjv_north evil'],
   '1-17':['lest ipl thee:a before they confound:pr'],'2-3':['kjv_firstfruits'],
   '2-8':['law:a in hand hold:pr','shepherd:pl'],'2-13':['two evil:pl','no water:a hold:can'],
   '2-16':['top:a of thy/head'],'2-20':['ipl thy/yoke:a break:perf','ipl transgress:neg:fu'],
   '2-21':['true seed'],'2-22':['kjv_nitre','kjv_soap'],'2-24':['up smell:pr','in her/month'],
   '2-27':['kjv_tree_stock','mypl/father','wesg:a save:imp'],'2-31':['wesg lord:pl be:pr'],
   '2-34':['by secret search find:neg:perf','upon all these'],'2-35':['ipl innocent be:pr','ipl with thee plead:fu','ipl sin:neg:perf'],
   '3-1':['yet again to ipl return:imp'],'3-8':['kjv_divorce_document'],'3-9':['lightweight:ev'],
   '3-14':['one_num of city and two of kjv_family'],'3-16':['kjv_ark_chest','neither that any more do:psv:fu'],
   '3-22':['ipl your/kjv_backslide:ev:pl:a heal:fu','wesg to thee come:pr'],
   '3-25':['wesg and ourone/father:pl'],'4-3':['kjv_fallow_ground'],'4-4':['kjv_foreskin:pl:a of your/heart'],
   '4-10':['thou this people:a and kjv_jerusalem:a greatly deceive:perf'],
   '4-11':['not to kjv_winnow:inf nor to clean:caus:inf'],'4-19':['i my/peace:a hold:neg:can','my/kjv_bowels:pl'],
   '4-23':['without form and void'],'4-27':['full end:a make:neg:fu'],
   '4-29':['kjv_bow+shoot:ag:pl'],'4-30':['thy/face:a with paint:ev rend:pr'],
   '4-31':['i voice:a','woe to ipl now:excl','mypl/soul']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_hilkiah_jeremiah','kjv_tahapanes','kjv_backslide','kjv_soap','kjv_fallow_ground','kjv_firstfruits'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
