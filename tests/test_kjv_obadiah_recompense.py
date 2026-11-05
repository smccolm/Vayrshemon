import unittest,re
from tools.kjv_archive import load_register,read
class ObadiahRecompenseTests(unittest.TestCase):
 def test_brotherhood_recompense_and_nested_self(self):
  prior,_=load_register('0.10-kjv.177');lang,manifest=load_register('0.10-kjv.178')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('obadiah-'):c for c in read(lang.folder/'obadiah-brotherhood-and-recompense-cases.json')};self.assertEqual(len(cases),21)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text'])
   self.assertFalse({'one','matter','worship','care'}&set(r['keys']))
  anchors={'1:1': ['kjv_obadiah_prophet', 'wesg rumour from kjv_lord', 'kjv_ambassador', 'wesg against she in battle'], '1:2': ['ipl thou:a among kjv_heathen small', 'greatly despise:psv'], '1:3': ['split:ev:pl of rock', 'in his/heart', 'who ipl:a down to ground'], '1:4': ['thyself as kjv_eagle', 'thy/nest among star:pl', 'ipl thou:a down'], '1:5': ['rob:ag:pl by night', 'be:excl', 'steal:pp:neg:should', 'some grape:pl leave:neg:should'], '1:6': ['how thing:pl of kjv_esau', 'be:excl how', 'hidden thing:pl'], '1:7': ['thy/kjv_league', 'boundary', 'thy/bread eat:pr', 'under thou wound lay:perf', 'understand:cv in he'], '1:8': ['wise man:pl out of kjv_edom destroy:neg:fu', 'understand:ev'], '1:9': ['kjv_teman', 'every person', 'kjv_slaughter'], '1:10': ['thy/brother kjv_jacob', 'for ever off cut:psv:fu'], '1:11': ['on other side', 'his/force:pl captive', 'kjv_lot:pl upon kjv_jerusalem', 'as person of they'], '1:12': ['stranger become:pa', 'look:pp:neg:should', 'their/destroy:ev', 'proud:adv'], '1:13': ['mypl/people', 'their/kjv_calamity', 'their/kjv_substance_estate'], '1:14': ['crossroad', 'escape:pa off cut:inf', 'remain:pa', 'up deliver:pp:should'], '1:15': ['all kjv_heathen', 'as thou do:perf to thou do:psv:fu', 'thy/own head'], '1:16': ['you upon mypl/holy mountain', 'always drink:fu', 'kjv_swallow:fu', 'though they be:neg:pp'], '1:17': ['kjv_deliverance', 'holy:ev', 'their/kjv_possession:pl possess:fu'], '1:18': ['kjv_jacob fire', 'kjv_joseph flame', 'kjv_esau for kjv_stubble', 'any remain:cv of house of kjv_esau be:neg:fu'], '1:19': ['kjv_south', 'kjv_plain_land kjv_philistine:pl', 'kjv_ephraim', 'kjv_samaria', 'kjv_benjamin kjv_gilead'], '1:20': ['kjv_captivity of this army', 'kjv_zarephath', 'kjv_sepharad', 'city:pl of kjv_south'], '1:21': ['save:ag:pl', 'kjv_zion', 'kjv_esau judge:inf', 'kingdom of kjv_lord']}
  for ref,parts in anchors.items():
   for part in parts:self.assertIn(part,cases[ref.replace(':','-')]['analysis'])
  self.assertIn('wesg rumour',cases['1-1']['analysis'])
  self.assertIn('who ipl:a down',cases['1-3']['analysis'])
  self.assertIn('under thou wound lay:perf',cases['1-7']['analysis'])
  self.assertIn('save:ag:pl',cases['1-21']['analysis'])
  self.assertFalse(any(':du' in c['analysis'] for c in cases.values()))
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),2)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
