import unittest,re
from tools.kjv_archive import load_register,read

class EzekielMeasuredVisionTests(unittest.TestCase):
 def test_measures_and_speakers_not_harmonized(self):
  prior,_=load_register('0.10-kjv.165');lang,manifest=load_register('0.10-kjv.166')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('ezekiel-'):c for c in read(lang.folder/'ezekiel-measured-vision-and-holy-boundary-cases.json')}
  self.assertEqual(set(cases),{f'{ch}-{v}' for ch,n in [(40,49),(41,26),(42,20)] for v in range(1,n+1)})
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text'])
   self.assertFalse({'one','post','story','leaf','court','count','fashion','meat','fold','right','light','bear'}&set(r['keys']))
  for r,parts in {
   '40-1':['two+twelve and one_num:ord','ourone/kjv_captivity','ten:ord','twelve and two:ord','i:a there'],
   '40-3':['appearance of kjv_brass','line of kjv_flax','kjv_measuring_reed'],
   '40-4':['man to i say:pa','i thee:a show:fu','i they:a to thee show:may'],
   '40-5':['six kjv_cubit:pl long by kjv_cubit and kjv_handbreadth'],
   '40-8':['within one_num kjv_measuring_reed'],
   '40-9':['eight kjv_cubit:pl','two kjv_cubit:pl'],
   '40-14':['five+twelve kjv_cubit:pl make:pa'],
   '40-21':['one_num:ord gate'],
   '40-30':['two+twelve and one_num kjv_cubit:pl long','five kjv_cubit:pl broad'],
   '40-34':['kjv_arch_structure:pl of it towards outside'],
   '40-37':['kjv_structural_post:pl of it towards outside'],
   '40-38':['burn:psv:adj kjv_offering:a wash:pa'],
   '40-39':['sin kjv_offering:a','kjv_trespass kjv_offering:a'],
   '40-42':['one_num and half kjv_cubit long','one_num and half kjv_cubit broad','one_num kjv_cubit high','instrument:pl:a'],
   '40-43':['kjv_hook:pl kjv_handbreadth broad','flesh of kjv_offering'],
   '40-44':['sing:ag:pl','kjv_north gate','towards kjv_south','one_num at side of east gate','towards kjv_north'],
   '40-45':['kjv_charge_custody of house'],
   '40-46':['kjv_charge_custody of altar','son:pl of kjv_zadok','son:pl of kjv_levi'],
   '40-49':['breadth eleven kjv_cubit:pl'],
   '41-1':['breadth of kjv_tabernacle'],
   '41-3':['he within go:pa','door six kjv_cubit:pl','breadth of door seven'],
   '41-6':['three each above another','two+twelve and six in order','hold:ev:a have:may','hold:ev:a in wall of house have:neg:pa'],
   '41-8':['six great kjv_cubit:pl'],
   '41-16':['three kjv_storey:pl','with wood round about cover:psv:adj','window:pl cover:psv:pa'],
   '41-18':['every kjv_cherub two face:pl'],
   '41-19':['face of man','face of young lion'],
   '41-22':['altar of wood','corner:pl of it and length of it and wall:pl','kjv_table_furniture'],
   '41-24':['two kjv_door_leaf:pl each','two turn:cv kjv_door_leaf:pl'],
   '42-4':['ten kjv_cubit:pl breadth within','way of one_num kjv_cubit'],
   '42-5':['higher chamber:pl more short','kjv_gallery:pl higher'],
   '42-6':['have:neg:pa','narrow:caus:psv:pa'],
   '42-11':['their/form:pl'],
   '42-13':['kjv_meat_offering:a','sin kjv_offering:a','kjv_trespass kjv_offering:a'],
   '42-14':['go:neg:fu','their/garment:pl:a','other garment:pl:a on put:fu'],
   '42-16':['five+hundred kjv_measuring_reed:pl'],
   '42-17':['five+hundred kjv_measuring_reed:pl'],
   '42-18':['five+hundred kjv_measuring_reed:pl'],
   '42-19':['five+hundred kjv_measuring_reed:pl'],
   '42-20':['four side:pl','five+hundred kjv_measuring_reed:pl long','five+hundred broad','kjv_unholy_profane place']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(cases['41-24']['analysis'].split().count('two'),4)
  self.assertEqual({r for r,c in cases.items() if 'ourone/' in c['analysis']},{'40-1'})
  self.assertFalse(any(re.search(r'\b(ipl|iplself|mypl|wesg|wepl)\b|:du',c['analysis']) for c in cases.values()))
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_measuring_reed','kjv_structural_post','kjv_arch_structure'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
