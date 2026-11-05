import unittest,re
from tools.kjv_archive import load_register,read
class JeremiahClayProtestTests(unittest.TestCase):
 def test_material_contrast_personal_protest_and_hostile_we(self):
  prior,_=load_register('0.10-kjv.145');lang,manifest=load_register('0.10-kjv.146')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-clay-agency-and-personal-protest-cases.json')};self.assertEqual(len(cases),83)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertNotIn(':du',c['analysis']);self.assertFalse({'one','host','bow','former','dragon','snuff','ghost','desert'}&set(result['keys']))
  for k,refs in {'i':'17-14 17-15 17-16 17-17 17-18 17-19 18-3 18-5 18-19 18-20 18-22 18-23 20-7 20-8 20-9 20-10 20-11 20-12 20-14 20-17 20-18','wesg':'18-12 18-18 20-10','ourone':'17-12 18-12 20-10','wepl':'','iplself':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in {
   '17-1':['table of their/heart','horn:pl of your/altar:pl'],'17-2':['kjv_grove_cult'],
   '17-4':['thyself from thy/heritage cease:fu','you fire:a in mypl/anger'],
   '17-6':['kjv_heath_shrub in dry land','see:neg:fu'],'17-8':['her/root:pl','heat come:pr see:neg:fu','worry:neg:fu','cease:neg:fu'],
   '17-10':['ipl kjv_lord','kjv_kidney:pl:a'],'17-11':['kjv_partridge','kjv_hatch:neg:pr','not by right'],
   '17-13':['who from ipl depart:pr','in earth write:psv:fu'],'17-16':['hasten:neg:perf','straight before thee'],
   '17-18':['double destroy:ev'],'17-21':['no burden:a','carry:imp'],'17-22':['kjv_hallow:imp','ipl your/father:pl:a'],
   '17-24':['if you','no burden:a','no work:a'],'17-27':['if you to ipl listen:neg:fu','extinguish:psv:neg:fu'],
   '18-2':['mypl/word:pl:a hear:caus:fu'],'18-3':['wheel:pl'],'18-4':['kjv_clay_material','again other vessel'],
   '18-6':['mypl/hand'],'18-8':['ipl of evil repent:fu'],'18-10':['ipl of good repent:fu'],
   '18-11':['ipl evil:a against you prepare:pr'],'18-12':['wesg after ourone/own device:pl','wesg each'],
   '18-14':['rock of field','other place'],'18-15':['they they:a','up cast:psv:neg:adj'],
   '18-17':['back:a and not face:a'],'18-18':['wesg he:a with tongue strike:opt','give:neg:opt'],
   '18-20':['i before thee stand:pa','thy/wrath:a from they away turn:inf'],
   '18-23':['forgive:neg:imp','out blot:neg:imp'],
   '19-1':['kjv_potter/kjv_bottle:a of kjv_clay_material'],'19-2':['east gate'],
   '19-4':['know:neg:perf','blood of innocent human:pl'],'19-5':['command:neg:pa','speak:neg:pa','mypl/mind come:neg:pa'],
   '19-9':['eat:caus:fu','flesh:a of his/friend'],'19-11':['again whole make:psv:neg:can'],
   '19-13':['all army of heaven'],'20-1':['kjv_pashur_immer son of kjv_immer_pashur'],
   '20-2':['stocks'],'20-3':['kjv_magormissabib'],'20-4':['terror to thyself'],
   '20-7':['thou i:a deceive:perf','i deceive:psv:pa'],'20-9':['my/bone:pl','i hold:neg:can'],
   '20-10':['wesg it:a report:fu','my/familiar human:pl','ourone/revenge:a'],
   '20-12':['kjv_kidney:pl:a'],'20-14':['i bear:psv:pa','bless:psv:neg:opt'],
   '20-15':['kjv_male child'],'20-16':['repent:neg:pa'],
   '20-17':['from womb slay:neg:pa','my/mother my/grave','her/womb always great with i'],
   '20-18':['my/day:pl with shame']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual({r for r,c in cases.items() if 'bear' in lang.compile(c['analysis'])['keys']},{'20-14','20-15'})
  self.assertEqual({r for r,c in cases.items() if 'right' in lang.compile(c['analysis'])['keys']},{'17-11'})
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_heath_shrub','kjv_pashur_immer','kjv_immer_pashur','kjv_magormissabib'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
