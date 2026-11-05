import unittest,re
from tools.kjv_archive import load_register,read

class EzekielPharaohUnderworldTests(unittest.TestCase):
 def test_river_self_and_underworld_lament(self):
  prior,_=load_register('0.10-kjv.162');lang,manifest=load_register('0.10-kjv.163')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('ezekiel-'):c for c in read(lang.folder/'ezekiel-river-self-and-underworld-lament-cases.json')};self.assertEqual(len(cases),97)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text']);self.assertNotIn(':du',c['analysis'])
   self.assertFalse({'one','host','bow','ghost','fold','care','plain','border','stuff','lock','divine','eminent','wax','fashion','fair','meat','worship','spy','waste','spring','shoot','flourish','point','privy','raven','pile','despite','row','wound','habit','shroud','hell','roll'}&set(r['keys']))
   for k in ('wesg','wepl','ourone'):self.assertIsNone(re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis']))
  for r,parts in {
   '29-3':['kjv_dragon_source','mypl/river of ipl own','for iplself'],
   '29-4':['thy/kjv_body_scale:pl'],
   '29-5':['for food'],
   '29-7':['by thy/hand','all their/kjv_shoulder:a rend:pa','at stand:ev be:caus:pa'],
   '29-9':['because he say:perf river of ipl'],
   '29-10':['from kjv_tower of kjv_syene'],
   '29-14':['their/dwell:ev','low kingdom'],
   '29-17':['two+twelve and three:ord year','one_num:ord month','one_num:ord day'],
   '29-18':['no kjv_wages:a'],
   '29-20':['because they for ipl work:pa'],
   '29-21':['forth bud:caus:fu'],
   '30-2':['woe:excl to day'],
   '30-5':['kjv_libya and kjv_lydia','kjv_chub','in kjv_league'],
   '30-9':['without worry kjv_ethiopian:pl'],
   '30-12':['land:a into hand of wicked sell:fu'],
   '30-13':['no more prince'],
   '30-15':['kjv_sin_egypt','kjv_no_egypt'],
   '30-16':['daily'],
   '30-17':['kjv_aven_egypt and of kjv_pibeseth'],
   '30-18':['kjv_tehaphnehes'],
   '30-21':['bind:psv:neg:fu','kjv_roller_bandage:a'],
   '30-22':['strong and that which break:psv:pa'],
   '30-25':['mypl/sword:a','he it:a upon land of egypt'],
   '31-3':['man of kjv_assyria','shade:cv canopy'],
   '31-5':['when he forth grow:pa'],
   '31-6':['their/young:a bear:pa'],
   '31-8':['hide:neg:pa:can','kjv_chestnut'],
   '31-10':['thou thyself:a','and he his/top:a'],
   '31-11':['mighty person of kjv_heathen'],
   '31-14':['neither their/kjv_tree:pl','all who water:a drink:pr'],
   '31-15':['to grave down go:pa','water:pl stop:psv:pa'],
   '31-16':['kjv_hell_depth','comfort:psv:fu'],
   '31-18':['this kjv_pharaoh'],
   '32-2':['whale in sea:pl','with thy/river:pl','with thy/foot:pl stir:pa'],
   '32-5':['valley:pl:a with thy/height'],
   '32-7':['moon her/light:a give:neg:fu'],
   '32-10':['mypl/sword:a before they kjv_brandish:fu','every man for his/own life'],
   '32-13':['neither foot of man','nor kjv_hoof:pl','stir:fu'],
   '32-14':['water:pl:a deep make:fu','like oil run:caus:fu'],
   '32-17':['twelve:ord year','twelve and three:ord day'],
   '32-19':['who:a in beauty exceed:pr?'],
   '32-22':['her/company','his/grave:pl about he'],
   '32-25':['her/grave:pl round about he','yet they their/shame:a','endure:perf'],
   '32-26':['kjv_meshech kjv_tubal','her/grave:pl round about he'],
   '32-27':['lie:neg:fu','their/sword:pl:a under their/head:pl','their/kjv_iniquity:pl upon their/bone:pl'],
   '32-30':['all kjv_zidonian:pl','endure:pr'],
   '32-31':['comfort:psv:fu'],
   '32-32':['ipl mypl/terror:a','cause:perf']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertNotIn(':ord month',cases['32-17']['analysis'])
  for r in ('29-11','29-12','29-13'):self.assertIn('three+twelve and four year:pl',cases[r]['analysis'])
  self.assertEqual({r for r,c in cases.items() if 'iplself' in c['analysis']},{'29-3'})
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),10)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
