import unittest,re
from tools.kjv_archive import load_register,read

class JeremiahDisputedGuidanceTests(unittest.TestCase):
 def test_reflexive_plural_self_and_attributed_communal_refusal(self):
  prior,_=load_register('0.10-kjv.151');lang,manifest=load_register('0.10-kjv.152')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-fallen-city-and-disputed-guidance-cases.json')};self.assertEqual(len(cases),87)
  for r,c in cases.items():
   result=lang.compile(c['analysis'])
   self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','host','bow','dragon','snuff','ghost','desert','court','bond','count','administer','light','tear','right','leaf','page','roll','commit','plead','former'}&set(result['keys']));self.assertNotIn(':du',c['analysis'])
  for k,refs in {'i':'40-4 40-10 40-15 42-4 42-9 42-19 42-20 42-21','wesg':'40-10 41-8 42-2 42-3 42-5 42-6 42-13 42-14 42-20 43-3','ourone':'42-2 42-6 42-20 43-2','mypl':'39-16 42-18 43-10','wepl':'','iplself':'42-10'}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in {
   '39-1':['nine:ord year','ten:ord month'],
   '39-2':['eleven:ord year','four:ord month nine:ord day'],
   '39-4':['between two wall:pl'],
   '39-6':['before his/eye:pl'],'39-7':['eye:pl:a out put:pa'],
   '39-10':['who nothing:a have:pa','kjv_vineyard:pl:a and field:pl:a'],
   '39-14':['entrust:pa'],'39-16':['for evil and not for good'],
   '39-18':['fall:neg:fu','thy/life for prey'],
   '40-1':['from kjv_ramah','chain:pl bind:psv:cv'],
   '40-2':['captain of guard','kjv_lord thy/god'],
   '40-4':['i thee:a this day','kjv_forbear:imp'],
   '40-8':['kjv_johanan_kareah and kjv_jonathan_kareah','kjv_jezaniah_maachathite'],
   '40-10':['as for i','to wesg come:fu'],
   '40-14':['kjv_baalis','believe:neg:pa'],
   '40-15':['i go:opt','no human it:a know:fu'],
   '41-1':['seven:ord month','ten man:pl'],
   '41-5':['six+twelve and eight man:pl','themselves:a cut:perf'],
   '41-8':['ten man:pl','wesg:a slay:neg:imp'],
   '41-9':['because of kjv_gedaliah_ahikam','kjv_asa king for fear of kjv_baasha'],
   '41-14':['around turn:pa and return:pa'],
   '41-15':['with eight man:pl escape:pa'],
   '42-1':['kjv_jezaniah_hoshaiah son of kjv_hoshaiah_jezaniah'],
   '42-2':['kjv_lord thy/god','wesg of many only few'],
   '42-4':['kjv_lord your/god','i nothing:a from you back keep:fu'],
   '42-6':['whether good','whether evil','ourone/god'],
   '42-7':['after ten day:pl'],
   '42-10':['down pull:neg:fu','up pluck:neg:fu','ipl iplself:a of evil','repent:pr'],
   '42-12':['that he upon you mercy:a have:may','return:caus:may'],
   '42-14':['see:neg:fu','hear:neg:fu','have:neg:fu'],
   '42-18':['curse:ev and astonish:ev and curse:psv:adj thing','no more see:fu'],
   '42-20':['kjv_dissemble:pa','wesg it:a do:fu'],
   '43-2':['kjv_azariah_hoshaiah son of kjv_hoshaiah_jezaniah','send:neg:perf'],
   '43-3':['against wesg urge:pr'],
   '43-6':['kjv_jeremiah_prophet kjv_prophet:a','kjv_baruch_neriah'],
   '43-9':['kjv_clay_material in kjv_brickkiln','in sight of man:pl'],
   '43-10':['mypl/servant:a','which ipl hide:perf'],
   '43-12':['ipl fire:a','he they:a burn:fu','himself:a with land of egypt clothe:fu','in peace forth go:fu'],
   '43-13':['kjv_bethshemesh_egypt','image:pl:a']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(cases['39-3']['analysis'].count('kjv_nergalsharezer'),2)
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),18)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
