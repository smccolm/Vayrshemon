import unittest,re
from tools.kjv_archive import load_register,read
class IsaiahSelfAloneTests(unittest.TestCase):
 def test_selfhood_negation_and_material_language(self):
  prior,_=load_register('0.10-kjv.136');lang,manifest=load_register('0.10-kjv.137')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('isaiah-'):c for c in read(lang.folder/'isaiah-plural-self-alone-and-common-court-cases.json')};self.assertEqual(len(cases),110)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','one_num','plain','hell','substance','rose','dumb','count','host','fan','profit','boil','plaster','kjv_swallow','fashion','divine','base'}&set(result['keys']))
  self.assertNotIn('rule',lang.compile(cases['44-13']['analysis'])['keys'])
  self.assertIn('rule',lang.compile(cases['41-2']['analysis'])['keys'])
  expected={'i':'44-5 44-16 44-17 44-19','iplself':'42-14 43-21 44-24','wesg':'41-1 41-22 41-23 41-26 42-24 43-9 43-26','wepl':'','ourone':'42-17'}
  for k,refs in expected.items():self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in{
   '41-4':['ipl kjv_lord first and with last ipl he be:pr'],
   '41-7':['kjv_anvil','kjv_solder:ev','with nail:pl kjv_fasten:pa'],
   '41-10':['kjv_right_side hand of mypl/kjv_righteousness'],
   '41-14':['thou worm kjv_jacob'],'41-16':['kjv_winnow:fu'],
   '41-19':['kjv_shittim kjv_tree','oil kjv_tree','kjv_box_tree'],
   '41-21':['your/kjv_legal_case:a'],'41-23':['good:a do:imp or evil:a do:imp'],
   '41-25':['human:a from kjv_north','kjv_mortar'],
   '42-1':['mypl/servant','mypl/soul','mypl/spirit:a upon he'],
   '42-2':['cry:neg:fu','lift:neg:fu','hear:psv:caus:neg:fu'],
   '42-4':['courage:a lose:neg:fu'],'42-6':['for kjv_covenant of people'],
   '42-13':['jealousy:a'],'42-14':['iplself:a restrain:perf','woman who kjv_travail:pr'],
   '42-15':['river:pl:a kjv_isle:pl'],'42-19':['he who perfect be:pr'],
   '42-20':['thou observe:neg:pr','he hear:neg:pr'],
   '42-24':['wesg sin:perf','they in his/way:pl walk:inf wish:neg:pa'],
   '43-1':['thou of ipl be:pr'],'43-2':['kjv_kindle_fire:neg:fu'],
   '43-3':['egypt:a for thy/ransom','kjv_ethiopia:a and kjv_seba:a'],
   '43-10':['ipl he be:pr','before ipl no god','after ipl god be:neg:fu'],
   '43-13':['before day be:pa ipl he be:pr','who it:a hinder:fu?'],
   '43-20':['dragon:pl and owl:pl'],'43-21':['for iplself form:perf'],
   '43-23':['serve:caus:neg:perf'],'43-24':['kjv_sweet_cane','fill:neg:perf','ipl:a with thy/sin:pl serve:caus:perf'],
   '43-25':['for mypl/own sake'],'44-5':['i of kjv_lord','kjv_surname:fu'],
   '44-8':['ipl any:a know:neg:pr'],'44-10':['kjv_cast_metal:perf'],
   '44-13':['kjv_measuring_rule','kjv_plane_tool','kjv_drawing_compass'],
   '44-14':['kjv_cypress','kjv_ash_tree'],'44-18':['he their/eye:pl:a shut:perf'],
   '44-20':['kjv_ashes:pl','false:ev in my/kjv_right_side hand'],
   '44-24':['alone forth stretch:pr','by iplself out spread:pr'],
   '44-25':['kjv_divine:ag:pl:a'],'44-28':['kjv_cyrus','mypl/shepherd']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(cases['44-21']['analysis'].count('thou mypl/servant be:pr'),2)
  self.assertEqual(cases['41-26']['analysis'].count('none who'),3)
  for r in('43-11','43-25'):self.assertTrue(cases[r]['analysis'].startswith('ipl even ipl'))
  self.assertEqual([r for r,c in cases.items() if 'kjv_cyrus' in c['analysis']],['44-28'])
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_anvil','kjv_solder','kjv_box_tree','kjv_sweet_cane','kjv_measuring_rule','kjv_plane_tool','kjv_drawing_compass','kjv_cypress','kjv_ash_tree','kjv_surname','kjv_jesurun'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
