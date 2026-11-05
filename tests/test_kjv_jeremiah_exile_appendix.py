import unittest,re
from tools.kjv_archive import load_register,read

class JeremiahExileAppendixTests(unittest.TestCase):
 def test_civic_self_and_exact_unharmonized_appendix(self):
  prior,_=load_register('0.10-kjv.154');lang,manifest=load_register('0.10-kjv.155')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-borrowed-voices-and-exile-appendix-cases.json')};self.assertEqual(len(cases),144)
  for r,c in cases.items():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text']);self.assertNotIn(':du',c['analysis'])
   self.assertFalse({'one','host','bow','dragon','snuff','ghost','desert','court','bond','count','administer','light','tear','right','leaf','page','commit','plead','former','handle','cleft_lip','dote','fast','grave','reserve','tend','passage'}&set(result['keys']))
  for k,refs in {'i':'','wesg':'50-5 50-7 51-9 51-10 51-51','ourone':'50-28 51-10 51-51','mypl':'50-6 50-11 51-20 51-25 51-34 51-35 51-45','wepl':'','iplself':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in {
   '50-2':['kjv_bel','kjv_merodach','conceal:neg:imp'],
   '50-5':['wesg ourselves:a','forget:psv:neg:fu'],
   '50-7':['kjv_adversary:pl say:pa wesg offend:neg:pr'],
   '50-11':['bull:pl kjv_low_cattle:pr'],
   '50-12':['she who you:a bear:pa'],
   '50-16':['kjv_sickle:a','each to his/own land'],
   '50-20':['find:psv:neg:fu','ipl those:a whom ipl keep:pr pardon:fu'],
   '50-26':['nothing of she leave:psv:opt'],
   '50-33':['kjv_firmly hold:pa'],
   '50-34':['kjv_litigate:fu','disturb:may'],
   '50-36':['foolish become:fu'],
   '50-42':['kjv_lance:a','mercy:a show:neg:fu'],
   '50-44':['ipl they:a suddenly away from she run:caus:fu'],
   '51-1':['middle of those who against ipl up rise:pr'],
   '51-2':['kjv_winnow:ag:pl:a','she:a kjv_winnow:fu'],
   '51-9':['wesg kjv_babylon:a heal:pp:should','wesg each into his/own country'],
   '51-14':['by himself swear:perf','ipl thee:a'],
   '51-17':['by his/knowledge kjv_brutish','kjv_founder_metal','no breath'],
   '51-19':['form:ag of all thing:pl'],
   '51-25':['down from rock:pl roll:fu'],
   '51-27':['kjv_ararat kjv_minni and kjv_ashchenaz'],
   '51-31':['one_num end'],
   '51-32':['kjv_passage_route:pl'],
   '51-34':['ipl:a devour:perf','ipl:a empty vessel','mypl/delicate food:pl'],
   '51-35':['mypl/flesh','kjv_zion say:fu','mypl/blood','kjv_jerusalem say:fu'],
   '51-36':['ipl thy/cause:a kjv_litigate:fu'],
   '51-39':['wake:neg:may'],
   '51-46':['one_num year','other year','rule:ag against rule:ag'],
   '51-48':['for kjv_babylon sing:fu'],
   '51-51':['ourone/face:pl:a'],
   '51-52':['kjv_wound_inflict:psv:adj:pl groan:fu'],
   '51-57':['wake:neg:fu'],
   '51-59':['four:ord year','quiet prince'],
   '51-63':['stone:a to it bind:fu','kjv_euphrates'],
   '51-64':['ipl upon she bring:fu rise:neg:fu','thus far word:pl'],
   '52-1':['twenty and one_num year:pl','eleven year:pl','kjv_jeremiah_hamutal'],
   '52-4':['nine:ord year','ten:ord month','ten:ord day'],
   '52-7':['between two wall:pl'],
   '52-12':['ten:ord day','twelve and seven:ord year'],
   '52-15':['some:a of poor'],
   '52-16':['some:a of poor','kjv_vinedresser:pl'],
   '52-20':['two kjv_pillar:pl one_num kjv_sea_basin and twelve kjv_brass bull:pl','under base:pl'],
   '52-21':['twelve and six kjv_cubit:pl','twelve kjv_cubit:pl','four finger:pl','within empty'],
   '52-22':['five kjv_cubit:pl'],
   '52-23':['eight+twelve pomegranate:pl','hundred round about'],
   '52-24':['kjv_seraiah_priest','kjv_zephaniah_priest second priest:a','three door keep:ag:pl:a'],
   '52-25':['seven man:pl','five+twelve man:pl'],
   '52-28':['three+thousand and twenty and three'],
   '52-29':['eight+hundred and thirty and two'],
   '52-30':['seven+hundred and forty and five','four+thousand and six+hundred'],
   '52-31':['thirty and seven:ord','twenty and five:ord day','first year'],
   '52-34':['kjv_allowance','every day kjv_foodportion','until day of his/death']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),9)
  self.assertEqual(lang.lexicon['kjv_lance']['form'],lang.lexicon['kjv_spear']['form'])
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
