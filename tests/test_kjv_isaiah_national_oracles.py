import unittest,re
from tools.kjv_archive import load_register,read
class IsaiahNationalOraclesTests(unittest.TestCase):
 def test_voices_inclusion_quantities_and_bird_correction(self):
  prior,_=load_register('0.10-kjv.131');lang,manifest=load_register('0.10-kjv.132')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id']:c for c in read(lang.folder/'isaiah-national-oracles-and-contextual-bird-cases.json')};self.assertEqual(len(cases),124)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
  isaiah={k.removeprefix('isaiah-'):c for k,c in cases.items() if k.startswith('isaiah-')};self.assertEqual(len(isaiah),123)
  voices={k:{r for r,c in isaiah.items() if re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis'])} for k in ['i','ipl','wesg','mypl']}
  self.assertEqual(voices['i'],set('14-13 14-14 16-9 18-4 19-11'.split()))
  self.assertEqual(voices['ipl'],set('13-3 13-11 13-12 13-13 13-17 14-22 14-23 14-24 14-25 14-30 15-9 16-10 18-4 19-2 19-3 19-4'.split()))
  self.assertEqual(voices['wesg'],set('14-8 14-10 16-6 17-14'.split()))
  self.assertEqual(voices['mypl'],set('13-3 14-25 18-4 19-25'.split()))
  for ref,parts in {
   '13-3':['mypl/sanctify:psv:adj'],'13-9':['cruel'],'13-10':['kjv_constellation:pl','shine:caus:neg:fu'],
   '13-16':['rape:psv:fu'],'13-20':['sheepfold:a'],'13-21':['kjv_satyr:pl'],'13-22':['kjv_dragon_creature:pl'],
   '14-4':['king of kjv_babylon'],'14-6':['persecute:psv:pr'],'14-9':['kjv_hell_depth'],
   '14-12':['kjv_lucifer'],'14-13':['i into heaven'],'14-16':['this human'],
   '14-22':['kjv_nephew_descendant:a'],'14-23':['kjv_bittern','broom'],
   '14-30':['kjv_firstborn_human'],'14-31':['appoint:psv:adj time:pl'],
   '14-32':['kjv_zion:a kjv_establish:perf'],
   '15-5':['three year:pl'],'15-8':['around boundary:pl'],
   '16-3':['he:a who wander:pr betray:neg:imp'],'16-4':['my/human:pl who out cast:psv:pr'],
   '16-7':['kjv_foundation:pl'],'16-9':['my/tear:pl'],'16-11':['my/kjv_bowels','sound:fu'],
   '16-14':['within three year:pl'],
   '17-5':['kjv_grain_ear:pl:a'],'17-6':['two or three','four or five'],
   '17-10':['kjv_plant_cutting:pl'],'17-11':['kjv_heap'],
   '18-2':['scatter:psv:adj and kjv_peel:psv:adj'],
   '18-4':['kjv_lord to i say:pa ipl mypl/rest:a'],
   '18-6':['summer:a spend:fu','winter:a spend:fu'],
   '19-3':['charm:ag:pl'],'19-6':['kjv_flag_plant:pl'],'19-8':['kjv_fishing_hook:a'],
   '19-9':['kjv_net:pl:a weave:pr'],'19-10':['kjv_sluice:pl:a'],
   '19-13':['support:ev'],'19-18':['five city:pl','one_num city of destroy:ev'],
   '19-20':['save:ag:a and great:a'],'19-23':['with human:pl of kjv_assyria serve:fu'],
   '19-24':['third:ord'],'19-25':['egypt mypl/people','kjv_assyria work of mypl/hand:pl','kjv_israel mypl/inheritance']
  }.items():
   for p in parts:self.assertIn(p,isaiah[ref]['analysis'])
  self.assertEqual(isaiah['15-1']['analysis'].count('to silence bring:psv:pr'),2)
  self.assertEqual(isaiah['19-22']['analysis'].count('strike:fu'),2)
  self.assertEqual(isaiah['19-22']['analysis'].count('heal:fu'),2)
  correction=cases['proverbs-26-2'];self.assertIn('kjv_swallow_bird by fly:ev',correction['analysis']);self.assertIn('swallow-bird',correction['expectedGloss']);self.assertNotIn('inside-eat',correction['expectedGloss'])
  self.assertNotEqual(lang.compile('kjv_swallow')['text'],lang.compile('kjv_swallow_bird')['text'])
  self.assertIn('inside-eat',lang.compile('kjv_swallow:pr')['gloss'])
  self.assertIn('enchantment',lang.lexicon['charm']['meaning'])
  self.assertEqual(len(read(lang.folder/'contextual-repairs.json')),1)
  added=set(lang.lexicon)-set(prior.lexicon);self.assertEqual(len(added),20);self.assertEqual(sum(lang.lexicon[k]['pos']=='proper' for k in added),12)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
