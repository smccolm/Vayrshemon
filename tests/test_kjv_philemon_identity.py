import unittest,re
from tools.kjv_archive import load_register,read
class PhilemonIdentityTests(unittest.TestCase):
 def test_person_and_obligation(self):
  prior,_=load_register('0.10-kjv.257');lang,manifest=load_register('0.10-kjv.258')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('philemon-'):c for c in read(lang.folder/'philemon-person-and-obligation-cases.json')};self.assertEqual(len(cases),25)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text'])
   self.assertFalse({'one','matter','worship'}&set(r['keys']))
  anchors={'1:1': ['kjv_paul_acts kjv_jesus_matthew kjv_christ_title kjv_prisoner', 'kjv_timothy_second_corinthians ourone/brother', 'kjv_philemon_letter'], '1:2': ['ourone/beloved kjv_apphia_philemon', 'ourone/kjv_fellowsoldier_philemon', 'kjv_church_assembly in thy/house'], '1:3': ['grace to you and peace', 'god ourone/father', 'kjv_lord kjv_jesus_matthew kjv_christ_title'], '1:4': ['i my/god thank:pr', 'in my/prayer:pl thou:a always'], '1:5': ['thy/love and faith', 'towards kjv_lord kjv_jesus_matthew', 'towards all saint:pl'], '1:6': ['thy/faith share:ev', 'every good thing acknowledge:ev', 'in you in kjv_christ_title kjv_jesus_matthew'], '1:7': ['wesg in thy/love great joy and comfort:ev have:pr', 'kjv_bowels_affection_philemon:pl by thou kjv_refresh:psv:perf'], '1:8': ['i in kjv_christ_title much bold be:may', 'that which fitting be:pr command:inf'], '1:9': ['for love sake i rather thou:a beseech:pr', 'kjv_paul_acts old', 'now also'], '1:10': ['my/son kjv_onesimus_colossians', 'i in my/chain:pl beget:perf'], '1:11': ['in past time to thou benefit:neg:adj', 'now to thou and to i benefit:adj'], '1:12': ['i again send:perf', 'he:a receive:imp', 'my/own kjv_bowels_affection_philemon:pl'], '1:13': ['i with i keep:inf desire:pa', 'in thy/place he to i', 'kjv_gospel chain:pl serve:may'], '1:14': ['without thy/consent', 'i nothing do:inf will:pa', 'necessity be:neg:should but willingly'], '1:15': ['perhaps therefore', 'for season depart:pa', 'forever receive:should'], '1:16': ['not as servant but above servant', 'beloved brother', 'in flesh and in kjv_lord'], '1:17': ['i:a kjv_partner_philemon reckon:pr', 'he:a as myself receive:imp'], '1:18': ['if he thou:a wrong:perf', 'anything owe:pr', 'that to i kjv_impute:imp'], '1:19': ['i kjv_paul_acts with my/own hand it write:perf', 'i it repay:fu', 'thy/own self besides owe:pr'], '1:20': ['i of thou in kjv_lord joy have:opt', 'my/kjv_bowels_affection_philemon:pl in kjv_lord'], '1:21': ['in thy/obey:ev confidence', 'more than i say:pr do:fu'], '1:22': ['to i kjv_lodging_place prepare:imp', 'through your/prayer:pl i to you give:psv:fu'], '1:23': ['kjv_epaphras_colossians my/kjv_fellowprisoner_philemon', 'thou:a greet:pr'], '1:24': ['kjv_marcus_colossians kjv_aristarchus_acts kjv_demas_colossians kjv_lucas_philemon', 'my/kjv_fellowlabourer_philemon:pl'], '1:25': ['ourone/kjv_lord', 'with your/spirit be:opt amen']}
  for ref,parts in anchors.items():
   for part in parts:self.assertIn(part,cases[ref.replace(':','-')]['analysis'])
  self.assertIn('ourone/beloved kjv_apphia_philemon',cases['1-2']['analysis'])
  self.assertIn('in you in kjv_christ_title kjv_jesus_matthew',cases['1-6']['analysis'])
  self.assertIn('wesg in thy/love great joy',cases['1-7']['analysis'])
  self.assertIn('kjv_paul_acts old',cases['1-9']['analysis'])
  self.assertIn('my/own kjv_bowels_affection_philemon:pl',cases['1-12']['analysis'])
  self.assertIn('without thy/consent',cases['1-14']['analysis'])
  self.assertIn('perhaps therefore',cases['1-15']['analysis'])
  self.assertIn('he:a as myself receive:imp',cases['1-17']['analysis'])
  self.assertIn('that to i kjv_impute:imp',cases['1-18']['analysis'])
  self.assertEqual(cases['1-20']['analysis'].count('in kjv_lord'),2)
  self.assertIn('through your/prayer:pl i to you',cases['1-22']['analysis'])
  self.assertIn('with your/spirit',cases['1-25']['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),8)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
