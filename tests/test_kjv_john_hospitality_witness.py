import unittest,re
from tools.kjv_archive import load_register,read
class JohnHospitalityWitnessTests(unittest.TestCase):
 def test_hospitality_and_personal_elder(self):
  prior,_=load_register('0.10-kjv.268');lang,manifest=load_register('0.10-kjv.269')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('3-john-'):c for c in read(lang.folder/'john-hospitality-witness-cases.json')};self.assertEqual(len(cases),14)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text'])
   self.assertFalse({'one','matter','worship'}-{'worship'}&set(r['keys']))
  anchors={'1:1': ['kjv_elder', 'kjv_gaius_john_epistle', 'i in truth love'], '1:2': ['i above all', 'thou prosper:may', 'in health', 'thy/kjv_soul prosper'], '1:3': ['i greatly rejoice', 'brother:pl come', 'truth which in thee', 'thou in truth walk'], '1:4': ['i greater joy', 'my/child:pl', 'truth walk'], '1:5': ['brother:pl and to stranger:pl', 'faithful:adv'], '1:6': ['thy/kjv_charity_love_corinthians', 'before kjv_church_assembly', 'if thou', 'journey', 'god:adj manner'], '1:7': ['his/name sake', 'from kjv_gentile:pl nothing'], '1:8': ['wesg', 'receive:should', 'to truth together help:ag:pl'], '1:9': ['i to kjv_church_assembly write', 'kjv_diotrephes_john_epistle', 'kjv_preeminence_colossians', 'wesg:a receive:neg'], '1:10': ['if i come', 'remember:fu', 'against wesg with malicious', 'brother:pl receive:pr', 'forbid:pr', 'out of kjv_church_assembly'], '1:11': ['evil thing follow:neg', 'good do:pr of god', 'evil do:pr god see:neg'], '1:12': ['kjv_demetrius_john_epistle', 'truth itself', 'wesg also witness', 'you that ourone/testimony true'], '1:13': ['i many thing:pl', 'kjv_ink and pen', 'write:neg:fu'], '1:14': ['soon thee:a see', 'wesg face to face', 'peace to thee', 'ourone/friend:pl', 'by name greet']}
  for ref,parts in anchors.items():
   for part in parts:self.assertIn(part,cases[ref.replace(':','-')]['analysis'])
  self.assertIn('kjv_gaius_john_epistle',cases['1-1']['analysis'])
  self.assertIn('thy/kjv_soul prosper:pr',cases['1-2']['analysis'])
  self.assertIn('his/name sake',cases['1-7']['analysis'])
  self.assertIn('wesg to truth together help:ag:pl',cases['1-8']['analysis'])
  self.assertIn('kjv_diotrephes_john_epistle',cases['1-9']['analysis'])
  self.assertIn('remember:fu',cases['1-10']['analysis'])
  self.assertIn('kjv_demetrius_john_epistle',cases['1-12']['analysis'])
  self.assertIn('you that ourone/testimony true',cases['1-12']['analysis'])
  self.assertIn('friend:pl by name greet:imp',cases['1-14']['analysis'])
  self.assertNotIn('amen',cases['1-14']['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),3)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
