import unittest,re
from tools.kjv_archive import load_register,read
class JudeContestedHolinessTests(unittest.TestCase):
 def test_contested_holiness_and_exclamation(self):
  prior,_=load_register('0.10-kjv.269');lang,manifest=load_register('0.10-kjv.270')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jude-'):c for c in read(lang.folder/'jude-contested-holiness-cases.json')};self.assertEqual(len(cases),25)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text'])
   self.assertFalse({'one','matter','worship'}-{'worship'}&set(r['keys']))
  anchors={'1:1': ['kjv_jude_epistle', 'kjv_james_jude_brother brother', 'by god father sanctify', 'in kjv_jesus_matthew kjv_christ_title keep', 'call:psv'], '1:2': ['mercy', 'peace and love', 'increase:caus:psv'], '1:3': ['i all kjv_diligent:ev', 'common salvation', 'once to holy person:pl deliver', 'earnest:adv contend'], '1:4': ['without notice in creep', 'before of old', 'ourone/god grace', 'lascivious:ev', 'only lord god', 'ourone/lord kjv_jesus_matthew kjv_christ_title'], '1:5': ['i therefore', 'once this know', 'lord people out of egypt', 'afterward', 'believe:neg:pa person:pl destroy'], '1:6': ['their/first kjv_angel_estate_jude', 'their/own dwell:ev', 'eternal chain:pl', 'under darkness', 'great day judgment'], '1:7': ['kjv_sodom and kjv_gomorrha_matthew', 'city:pl around', 'kjv_fornication', 'strange flesh', 'eternal fire revenge'], '1:8': ['filthy dream:ag:pl', 'flesh defile', 'kjv_dominion despise', 'dignity:pl evil speak'], '1:9': ['kjv_michael_jude_archangel kjv_archangel_thessalonians', 'devil', 'kjv_moses body', 'dare:neg', 'lord thee:a rebuke:opt'], '1:10': ['know:neg:pr evil speak', 'natural:adv', 'reason:neg:adj beast:pl', 'themselves corrupt'], '1:11': ['to they woe:excl', 'kjv_cain way', 'kjv_balaam error for reward', 'kjv_core_jude kjv_gainsay_romans:ev'], '1:12': ['spot:pl', 'kjv_charity_love_corinthians feast:pl', 'themselves without fear feed', 'cloud:pl without water', 'fruit wither', 'twice dead', 'root:pl up pluck'], '1:13': ['sea rage:cv kjv_wave:pl', 'own shame', 'wander:cv star:pl', 'darkness black:ev forever'], '1:14': ['kjv_enoch', 'kjv_adam seven:ord', 'his/holy person:pl ten+thousand:pl'], '1:15': ['upon all judgment', 'all god:neg:adj person:pl', 'all their/god:neg:adj deed:pl', 'god:neg:adj:adv do', 'all their/hard speech:pl', 'kjv_convince_reprove'], '1:16': ['kjv_murmur:pr and complaint:ag:pl', 'their/own lust:pl', 'swell:cv word:pl', 'because advantage', 'admire:ev'], '1:17': ['ourone/lord kjv_jesus_matthew kjv_christ_title kjv_apostle:pl', 'before', 'remember:imp'], '1:18': ['last time mock:ag:pl', 'their/own god:neg:adj lust:pl'], '1:19': ['themselves separate', 'kjv_sensual_james', 'spirit have:neg'], '1:20': ['your/most holy faith', 'yourselves up build', 'in holy spirit pray'], '1:21': ['yourselves in god love', 'ourone/lord kjv_jesus_matthew kjv_christ_title mercy', 'eternal life'], '1:22': ['to some kjv_compassion', 'difference make'], '1:23': ['other person:pl with fear save', 'out of fire pull', 'garment by flesh spot', 'hate'], '1:24': ['you:a from fall:ev keep', 'his/glory presence', 'very great joy', 'fault:neg:adj present'], '1:25': ['only wise god ourone/save:ag', 'glory and majesty', 'kjv_dominion and power', 'both now and forever', 'amen']}
  for ref,parts in anchors.items():
   for part in parts:self.assertIn(part,cases[ref.replace(':','-')]['analysis'])
  self.assertIn('by god father sanctify:psv',cases['1-1']['analysis'])
  self.assertIn('only lord god',cases['1-4']['analysis'])
  self.assertIn('their/first kjv_angel_estate_jude',cases['1-6']['analysis'])
  self.assertIn('lord thee:a rebuke:opt',cases['1-9']['analysis'])
  self.assertIn('woe:excl .',cases['1-11']['analysis'])
  self.assertIn('twice dead',cases['1-12']['analysis'])
  self.assertIn('ten+thousand:pl',cases['1-14']['analysis'])
  self.assertIn('themselves separate:pr',cases['1-19']['analysis'])
  self.assertIn('difference make:cv',cases['1-22']['analysis'])
  self.assertIn('only wise god ourone/save:ag',cases['1-25']['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),5)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
