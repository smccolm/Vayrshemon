import unittest,re
from tools.kjv_archive import load_register,read
class JeremiahLamentingSelvesTests(unittest.TestCase):
 def test_lament_possessors_and_material_senses(self):
  prior,_=load_register('0.10-kjv.143');lang,manifest=load_register('0.10-kjv.144')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-lamenting-selves-and-contested-judgment-cases.json')};self.assertEqual(len(cases),91)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertNotIn(':du',c['analysis']);self.assertFalse({'one','host','bear','bow','former','dragon','kjv_upright','kjv_tabernacle'}&set(result['keys']))
  for k,refs in {'i':'9-1 9-2 9-10 10-23 10-24 11-5 11-6 11-9 11-18 11-19 11-20 12-1 12-3','wesg':'9-18 9-19 11-19','ourone':'9-18 9-19 9-21 11-21 12-4','wepl':'','iplself':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in {
   '9-1':['my/head water:pl','my/eye:pl fountain of tear:pl','weep:may:excl'],
   '9-2':['my/people:a leave:may'],'9-3':['their/kjv_bow','they ipl:a know:neg:pr'],
   '9-7':['ipl they:a melt:fu'],'9-10':['mountain:pl i','voice:a of kjv_livestock'],
   '9-11':['kjv_dragon_creature'],'9-15':['kjv_wormwood','kjv_gall_bitter'],
   '9-17':['skill:adj woman:pl'],'9-18':['ourone/eye:pl','ourone/eyelid:pl'],
   '9-19':['ourone/dwell:ev place:pl wesg:a out cast:perf'],'9-21':['ourone/window:pl'],
   '9-25':['kjv_circumcise:psv:pr with kjv_circumcise:psv:neg:adj people'],
   '9-26':['most far corner:pl','in heart kjv_circumcise:psv:neg:adj'],
   '10-5':['straight as kjv_palm_tree','carry:psv:must','go:neg:can'],
   '10-8':['kjv_tree_stock teaching'],'10-9':['kjv_uphaz','kjv_founder_metal','blue and purple'],
   '10-13':['kjv_vapour:pl:a','up rise:caus:pr'],'10-16':['form:ag of all thing:pl','rod of his/inheritance'],
   '10-18':['at this once out kjv_sling:fu'],'10-19':['ipl it:a endure:must'],
   '10-20':['mypl/tent','mypl/child:pl forth from ipl','they be:neg:pr'],
   '10-23':['way of human in himself be:neg:pr'],'10-24':['i:a kjv_chasten:imp','not in thy/anger'],
   '11-4':['iron kjv_furnace'],'11-5':['ipl oath:a','then i answer:pa','so it be:imp'],
   '11-7':['with kjv_zeal testify:pa'],'11-11':['escape:neg:can','heed:neg:fu'],
   '11-15':['kjv_lewdness:a','holy flesh from thee pass:perf'],
   '11-17':['against themselves','ipl:a to anger kjv_provoke:inf'],
   '11-19':['i like kjv_lamb or ox','wesg kjv_tree:a with its/fruit'],
   '11-20':['kjv_kidney:pl:a and heart:a'],'11-21':['ourone/hand'],
   '12-1':['wicked human:pl prosper:pr','happy be:pr'],'12-2':['thou they:a plant:perf','far from their/kjv_kidney:pl'],
   '12-4':['ourone/last end:a see:neg:fu'],'12-5':['swell:ev of kjv_jordan'],
   '12-7':['dearly beloved:a of mypl/soul'],'12-8':['ipl it:a hate:perf'],
   '12-9':['kjv_speckled bird'],'12-12':['from end of land even to other end'],
   '12-13':['they of your/revenue:pl'],'12-15':['kjv_compassion:a have:fu','each human to his/heritage'],
   '12-16':['if they','build:psv:fu'],'12-17':['if they obey:neg:fu','destroy:fu']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_lewdness','kjv_wail','kjv_uphaz'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
