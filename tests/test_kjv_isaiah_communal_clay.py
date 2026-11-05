import unittest,re
from tools.kjv_archive import load_register,read
class IsaiahCommunalClayTests(unittest.TestCase):
 def test_exclusive_agency_and_communal_identity(self):
  prior,_=load_register('0.10-kjv.140');lang,manifest=load_register('0.10-kjv.141')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('isaiah-'):c for c in read(lang.folder/'isaiah-exclusive-agency-and-communal-clay-cases.json')};self.assertEqual(len(cases),92)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertNotIn(':du',c['analysis'])
   self.assertFalse({'one','table','kjv_hephzibah','kjv_pul'}&set(result['keys']))
  for k,refs in {'i':'63-7 63-15 65-5','wesg':'63-7 63-16 63-17 63-19 64-3 64-5 64-6 64-7 64-8 64-9 64-12','ourone':'63-16 63-17 63-18 64-6 64-7 64-8 64-11','wepl':'','iplself':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in {
   '62-4':['kjv_hephzibah_city','kjv_beulah'],'62-5':['thy/son:pl thee:a marry:fu'],
   '63-1':['ipl who in kjv_righteousness speak:pr'],'63-3':['ipl kjv_winepress:a alone','none with ipl'],
   '63-5':['mypl/own arm salvation:a to ipl'],'63-7':['i kjv_lovingkindness:pl:a','upon wesg bestow:perf'],
   '63-9':['he kjv_afflict:psv:pa','angel of his/presence','they:a carry:pa and they:a carry:pa'],
   '63-10':['his/holy spirit:a vex:pa','their/enemy be:inf'],'63-11':['his/holy spirit:a within he'],
   '63-14':['spirit of kjv_lord he:a rest:caus:pa'],'63-15':['towards i'],
   '63-16':['ourone/father'],'63-17':['wesg:a from thy/way:pl err:caus:perf','ourone/heart:a from thy/fear hard:caus:perf'],
   '64-5':['wesg save:psv:fu'],'64-6':['all ourone/kjv_righteousness:pl'],
   '64-8':['wesg kjv_clay_material','thou ourone/kjv_potter'],
   '65-5':['i more holy than thou','mypl/nose'],'65-11':['kjv_meal_table:a for that troop','that kjv_number_recipient'],
   '65-20':['child at hundred year:pl old die:fu','sin:ag at hundred year:pl old curse:psv:fu'],
   '65-22':['they build:fu but other inhabit:neg:fu','they plant:fu but other eat:neg:fu'],
   '66-3':['as if he human:a kill:pa','dog/neck:a off cut:pa','pig/blood:a offer:pa','idol:a bless:pa'],
   '66-4':['their/kjv_delusion:pl:a choose:fu'],'66-7':['before she kjv_travail:pa she forth bring:pa'],
   '66-8':['one_num day','nation at same time bear:psv:fu'],'66-12':['upon her/side:pl carry:psv:fu','kjv_dandle:psv:fu'],
   '66-13':['as human whom his/mother comfort:pr','ipl you:a comfort:fu'],
   '66-17':['behind one_num kjv_tree'],'66-19':['kjv_pul_people'],'66-20':['kjv_litter_vehicle:pl'],
   '66-23':['from new moon to other and from kjv_sabbath to other'],
   '66-24':['kjv_corpse:pl of human:pl','worm die:neg:fu','fire extinguish:psv:neg:fu']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_wine_vat','kjv_number_recipient','kjv_delusion','kjv_dandle','kjv_litter_vehicle','kjv_hephzibah_city','kjv_beulah','kjv_pul_people'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
