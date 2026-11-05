import unittest,re
from tools.kjv_archive import load_register,read
class EcclesiastesConclusionTests(unittest.TestCase):
 def test_speaker_shifts_counts_and_unharmonized_source(self):
  prior,_=load_register('0.10-kjv.127');lang,manifest=load_register('0.10-kjv.128')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id']:c for c in read(lang.folder/'ecclesiastes-unresolved-voices-and-communal-conclusion-cases.json')};self.assertEqual(len(cases),108)
  voices={k:set() for k in ['i','wesg']}
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'one','just','right','bear','kjv_travail','kjv_bereave','exercise','count'}&set(out['keys']))
   self.assertNotRegex(c['analysis'],r'(?<![a-z_])(?:ipl|mypl|iplself|wepl|ourone|we:du|they:du|you:du)(?![a-z_])')
   for k in voices:
    if re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis']):voices[k].add(c['id'])
  self.assertEqual(voices['wesg'],{'ecclesiastes-12-13'})
  self.assertEqual(voices['i'],{'ecclesiastes-'+r for r in '7-15 7-23 7-25 7-26 7-27 7-28 7-29 8-2 8-9 8-10 8-12 8-14 8-15 8-16 8-17 9-1 9-11 9-13 9-16 10-5 10-7 12-1'.split()})
  for ref,parts in {
   '7-1':['day of death than day of human birth'],'7-3':['sorrow better than laughter'],
   '7-6':['kjv_crackle of thorn:pl under kjv_pot'],'7-13':['he crooked:caus:perf straight:caus:can?'],
   '7-15':['kjv_righteous:ev perish:pr','wicked:ev long:caus:pr'],'7-16':['kjv_righteous over much be:neg:imp'],
   '7-19':['ten mighty'],'7-20':['sin:neg:pr be:neg:pr'],'7-26':['her/hand:pl as fetter:pl'],
   '7-27':['one_num by one_num'],'7-28':['one_num kjv_male human:a among thousand','woman:a among all those i find:neg:perf'],
   '8-1':['interpret:ev:a of thing'],'8-8':['spirit:a keep:inf','release:ev in that war'],
   '8-10':['forget:psv:pa'],'8-11':['judgment against evil work quickly perform:psv:neg:pr'],
   '8-12':['hundred time:pl'],'8-14':['according_to work of wicked','according_to work of kjv_righteous'],
   '8-15':['i mirth:a commend:pa'],'8-17':['find:neg:can','find:neg:fu'],
   '9-4':['living dog better than dead lion'],'9-5':['dead any thing:a know:neg:pr'],
   '9-6':['share:ev:a for ever','under sun'],'9-10':['in grave to which thou go:pr'],
   '9-11':['kjv_race to swift be:neg:pr','time and chance'],'9-15':['no human that same poor human:a remember:pa'],
   '9-18':['one_num sin:ag'],'10-2':['his/kjv_right_side','his/left'],
   '10-11':['kjv_babble:ag better be:neg:pr'],'10-12':['himself:a up kjv_swallow:fu'],
   '10-16':['land:excl','thy/king child'],'10-18':['house water:a through drop:pr'],
   '11-2':['to seven','also to eight'],'11-5':['way of spirit','bone:pl in womb'],
   '12-1':['thou say:fu i no pleasure:a'],'12-3':['keeper:pl','kjv_grind:ag:pl','window:pl'],
   '12-5':['kjv_grasshopper burden','his/long home','around street:pl'],
   '12-6':['before silver kjv_cord','gold:adj bowl','kjv_pitcher','kjv_cistern'],
   '12-7':['spirit to god who it:a give:pa return:fu'],'12-9':['he still to people knowledge:a teach:pa'],
   '12-11':['one_num shepherd'],'12-12':['make:ev end be:neg:pr'],
   '12-13':['wesg conclude:ev:a of whole matter hear:opt','whole duty of human'],
  }.items():
   for part in parts:self.assertIn(part,cases['ecclesiastes-'+ref]['analysis'],(ref,part))
  self.assertEqual(cases['ecclesiastes-9-9']['analysis'].count('all day:pl of'),2)
  self.assertEqual(cases['ecclesiastes-12-8']['analysis'].count('vanity of vanity:pl'),1)
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_crackle','kjv_race'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
