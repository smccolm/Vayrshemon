import unittest,re
from tools.kjv_archive import load_register,read
class JohnLadyTruthTests(unittest.TestCase):
 def test_lady_truth_and_shared_reward(self):
  prior,_=load_register('0.10-kjv.267');lang,manifest=load_register('0.10-kjv.268')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('2-john-'):c for c in read(lang.folder/'john-lady-and-truth-cases.json')};self.assertEqual(len(cases),13)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text'])
   self.assertFalse({'one','matter','worship'}-{'worship'}&set(r['keys']))
  anchors={'1:1': ['kjv_elder', 'choose:psv:pp lady', 'her/child:pl', 'i in truth love', 'not i only'], '1:2': ['truth sake', 'in wesg dwell', 'with wesg forever'], '1:3': ['grace with you', 'mercy and peace', 'from god father', 'from lord kjv_jesus_matthew kjv_christ_title', 'father son'], '1:4': ['i greatly rejoice', 'of thy/child:pl', 'wesg from father command'], '1:5': ['i thee:a beseech', 'lady', 'new command', 'wesg from beginning', 'wesg each other love'], '1:6': ['wesg after his/command:pl', 'this command', 'you from beginning', 'walk:should'], '1:7': ['many deceive:ag:pl', 'kjv_jesus_matthew kjv_christ_title in flesh come:perf confess:neg', 'kjv_antichrist_john_epistle'], '1:8': ['to yourselves look', 'wesg those thing:pl', 'wesg work:perf', 'wesg full reward'], '1:9': ['transgress:pr', 'kjv_christ_title doctrine remain:neg', 'god have:neg', 'both father and son'], '1:10': ['if any', 'doctrine bring:neg', 'your/house receive:neg', 'neither to he godspeed'], '1:11': ['godspeed say', 'his/evil deed:pl share:ag'], '1:12': ['paper and kjv_ink', 'face to face', 'ourone/joy full'], '1:13': ['thy/choose:psv:pp sister child:pl', 'thee:a greet', 'amen']}
  for ref,parts in anchors.items():
   for part in parts:self.assertIn(part,cases[ref.replace(':','-')]['analysis'])
  self.assertIn('choose:psv:pp lady',cases['1-1']['analysis'])
  self.assertIn('grace with you',cases['1-3']['analysis'])
  self.assertIn('of thy/child:pl',cases['1-4']['analysis'])
  self.assertEqual(cases['1-8']['analysis'].count('wesg'),3)
  self.assertIn('both father and son',cases['1-9']['analysis'])
  self.assertIn('godspeed',cases['1-10']['analysis'])
  self.assertIn('paper and kjv_ink',cases['1-12']['analysis'])
  self.assertIn('ourone/joy',cases['1-12']['analysis'])
  self.assertEqual(set(lang.lexicon),set(prior.lexicon))
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
