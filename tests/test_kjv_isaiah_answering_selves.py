import unittest,re
from tools.kjv_archive import load_register,read
class IsaiahAnsweringSelvesTests(unittest.TestCase):
 def test_distinct_speakers_source_accounts_and_concrete_senses(self):
  prior,_=load_register('0.10-kjv.135');lang,manifest=load_register('0.10-kjv.136')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('isaiah-'):c for c in read(lang.folder/'isaiah-answering-selves-and-mortal-song-cases.json')};self.assertEqual(len(cases),99)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','plain','hell','substance','rose','dumb','count','host','peep','ward','issue','prevent','table','sieve','fan','profit','boil','plaster','kjv_swallow'}&set(result['keys']))
  expected={'i':'38-3 38-10 38-11 38-12 38-13 38-14 38-15 38-16 38-17 38-19 38-20 38-22 40-6','ipl':'37-6 37-7 37-21 37-24 37-25 37-26 37-28 37-29 37-35 38-5 38-6 38-8 39-3 39-4 40-25','mypl':'37-12 37-24 37-25 37-29 37-35 39-4 40-1 40-27','wesg':'37-20 38-20','ourone':'37-20 38-20 40-3 40-8','wepl':'','iplself':''}
  for k,refs in expected.items():self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  anchors={
   '37-16':['thou alone'],'37-20':['wesg:a','even thou only'],
   '37-23':['kjv_holy_one'],'37-24':['thy/servant:pl','mypl/chariot:pl','height of his/boundary'],
   '37-25':['ipl kjv_dig:perf and water:a drink:perf'],
   '37-26':['ipl it:a do:perf','ipl it:a form:perf','ipl it:a happen:caus:perf'],
   '37-29':['mypl/kjv_restraint_hook'],'37-33':['shield:pl'],
   '37-36':['then angel','hundred+thousand and eight+ten+thousand and five+thousand'],
   '38-1':['die:fu and live:neg:fu'],'38-5':['fifteen year:pl'],
   '38-8':['ipl shadow:a','sun ten kjv_shadow_degree:pl return:pa'],
   '38-10':['kjv_deprive:psv:pr'],'38-12':['i like weaver','he i:a','thou of i'],
   '38-14':['kjv_crane_bird','kjv_swallow_bird','dove'],
   '38-18':['grave thee:a praise:neg:can','death thee:a praise:neg:can','hope:neg:can'],
   '38-19':['living living'],'38-20':['wesg my/song:pl:a','ourone/life'],
   '38-21':['kjv_poultice','kjv_boil_lesion'],
   '39-2':['glad be:pa','his/kjv_dominion'],'39-3':['to ipl come:perf'],
   '39-4':['mypl/house','mypl/treasure:pl'],'39-8':['he further say:pa for peace and truth in my/day:pl be:fu'],
   '40-1':['mypl/people:a comfort:imp comfort:imp'],'40-2':['double for all her/sin:pl'],
   '40-3':['ourone/god'],'40-6':['what i cry:fu?'],
   '40-9':['kjv_zion who good news:a','kjv_jerusalem who good news:a'],
   '40-15':['dust of balance consider:psv:pr'],'40-17':['less than nothing and vanity'],
   '40-19':['kjv_graven image:a melt:pr','silver chain:pl:a kjv_cast_metal:pr'],
   '40-22':['circle of earth','kjv_grasshopper:pl'],
   '40-24':['their/kjv_plant_stock'],'40-25':['ipl:a compare:fu','kjv_holy_one'],
   '40-26':['their/army:a by kjv_number:ev','not one_num'],
   '40-27':['mypl/way','mypl/judgment','mypl/god']}
  for r,parts in anchors.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  for r,banned in {'37-4':['all word'],'37-20':['beseech'],'37-21':['hear:perf'],'37-24':['messenger:pl','kjv_lodging_place'],'37-25':['foreign'],'37-36':['that night'],'38-5':['third','three'],'38-22':['third','three'],'39-2':['listen:pa'],'39-8':['?']}.items():
   for part in banned:self.assertNotIn(part,cases[r]['analysis'])
  self.assertEqual(cases['40-21']['analysis'].count('?'),4)
  self.assertNotIn(' cast:',cases['40-19']['analysis'])
  for r in('38-12','38-13'):self.assertTrue(cases[r]['analysis'].endswith('from day even to night thou of i end:a make:fu.'))
  for r in('40-7','40-8'):self.assertTrue(cases[r]['analysis'].startswith('grass wither:pr flower fade:pr'))
  comparisons=read(lang.folder/'parallel-comparison.json');self.assertEqual(len(comparisons),68)
  self.assertEqual({x['reference'] for x in comparisons if x['exact']},{'Isaiah 37:1','Isaiah 37:5','Isaiah 37:8','Isaiah 37:19','Isaiah 37:23','Isaiah 37:28','Isaiah 37:32','Isaiah 37:34','Isaiah 37:37','Isaiah 39:7'})
  for x in comparisons:
   if x['exact'] and x['reference']!='Isaiah 37:23':self.assertEqual(cases[x['reference'].split()[-1].replace(':','-')]['analysis'],x['priorAnalysis'])
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_crane_bird','kjv_poultice','kjv_plant_stock','kjv_telassar','kjv_merodachbaladan'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
