import unittest
from tools.kjv_archive import load_register,read
class ProverbQuotedClaimsTests(unittest.TestCase):
 def test_quoted_persons_historical_senses_and_supplied_readings(self):
  prior,_=load_register('0.10-kjv.123');lang,manifest=load_register('0.10-kjv.124')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id']:c for c in read(lang.folder/'proverbs-quoted-claims-and-source-readings-cases.json')};self.assertEqual(len(cases),171)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'just','want','sound','hell','simple','right','plain','mean','scale','train','conceit','discover','kjv_stripe'}&set(out['keys']))
   self.assertNotRegex(c['analysis'],r'(?<![a-z_])(?:ipl|mypl|iplself|wesg|wepl)(?![a-z_])')
  for ref,parts in {
   '17-1':['house full of kjv_sacrifice:pl'],'17-2':['wise servant over son','inheritance among brother:pl'],
   '17-3':['kjv_crucible','heart:pl:a test:pr'],'17-7':['speech fool:a suit:neg:pr'],
   '17-9':['near friend:pl'],'17-10':['hundred blow:pl'],'17-12':['bear_animal','her/kjv_whelp:pl'],
   '17-15':['kjv_justify:pr','kjv_righteous:a condemn:pr'],'17-18':['hand:pl:a strike:pr','surety'],
   '17-22':['spirit bone:pl:a dry:caus:pr'],'17-23':['gift:a out of bosom','judgment:a crooked:caus:inf'],
   '17-25':['she who he:a bear:pa'],'17-26':['prince:pl:a for kjv_equity'],
   '17-27':['excellent spirit'],'17-28':['wise reckon:psv:pr'],
   '18-1':['himself:a separate:cv','with all wisdom deal:pr'],'18-2':['itself:a reveal:may'],
   '18-8':['kjv_talebearer like wound:pl'],'18-11':['in his/own thought'],
   '18-14':['spirit:a who carry:can?'],'18-17':['first in his/own cause'],
   '18-18':['kjv_lot'],'18-24':['himself:a friendly show:must'],
   '19-7':['they to he lack:pr'],'19-10':['servant over prince:pl rule:inf'],
   '19-13':['cease:neg:adj drop:ev'],'19-18':['for his/cry:ev spare:inf allow:neg:imp'],
   '19-22':['desire of human his/kjv_kindness'],'19-24':['hand:a in his/bosom'],
   '19-27':['instruction:a hear:inf which','knowledge err:caus:pr'],
   '20-2':['fear of king'],'20-9':['i my/heart:a clean:caus:perf','i pure from my/sin'],
   '20-16':['for strange woman'],'20-17':['kjv_gravel'],'20-21':['get:psv:may'],
   '20-22':['say:neg:imp i evil:a repay:fu'],'20-25':['holy:a devour:pr','after vow:pl'],
   '20-26':['wheel:a over they'],'20-27':['candle of kjv_lord'],
   '20-30':['blue:ev of wound','blow:pl inside part:pl'],
   '21-4':['plough:ev of wicked'],'21-12':['but god wicked:a'],
   '21-16':['kjv_assembly of dead'],'21-18':['wicked ransom for kjv_righteous'],
   '21-22':['city of mighty:a climb:pr'],'21-28':['kjv_steadfast:adv speak:pr'],
   '22-6':['go:should teach:imp'],'22-7':['borrow:ag servant to lend:ag'],
   '22-13':['lazy:ag say:pr','i in street:pl kill:psv:fu'],
   '22-19':['i to thee this day know:caus:perf even to thee'],
   '22-20':['excellent thing:pl','write:neg:perf,'],'22-21':['i thee:a','answer:may?'],
   '22-23':['soul:a of they who they:a spoil:pa spoil:fu'],
   '22-28':['ancient kjv_landmark'],'22-29':['before lowly human:pl stand:neg:fu'],
  }.items():
   for p in parts:self.assertIn(p,cases['proverbs-'+ref]['analysis'],(ref,p))
  self.assertEqual(cases['proverbs-19-5']['analysis'].split(' and ')[0],cases['proverbs-19-9']['analysis'].split(' and ')[0])
  for r in ['17-5','19-5','19-9']:self.assertIn('punish:psv:neg:adj remain:neg:fu',cases['proverbs-'+r]['analysis'])
  self.assertTrue(cases['proverbs-20-14']['analysis'].startswith('it worthless be:pr it worthless be:pr'))
  self.assertNotIn('thirty',cases['proverbs-22-20']['analysis'])
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_crucible','kjv_gravel'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
