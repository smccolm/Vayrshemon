import unittest,re
from tools.kjv_archive import load_register,read
class ProverbTeachingTests(unittest.TestCase):
 def test_personified_and_quoted_voices_historical_senses(self):
  prior,_=load_register('0.10-kjv.120');lang,manifest=load_register('0.10-kjv.121')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id']:c for c in read(lang.folder/'proverbs-teaching-personification-cases.json')};self.assertEqual(len(cases),202)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'just','fast','want','consume','ravish','fair','sound','hell','simple','subtle','please','right','goodman'}&set(out['keys']))
   self.assertNotRegex(c['analysis'],r'(?<![a-z_])(?:ipl|mypl|iplself)(?![a-z_])')
   self.assertNotRegex(c['analysis'],r':(?:can|may|must|should):(?:a|g|i|d)(?:[^a-z]|$)')
  for ref,parts in {
   '1-4':['kjv_naive kjv_prudence:a','kjv_discretion:a'], '1-6':['riddle:pl'],
   '1-11':['if they say:pr','wepl'], '1-14':['kjv_lot_portion','wepl','wesg all one_num purse:a'],
   '1-18':['their/own blood','their/own life:pl'], '1-20':['wisdom outside','she her/voice'],
   '1-23':['i my/spirit:a to you:pl'], '1-26':['i also at your/kjv_calamity laugh:fu'],
   '1-28':['they upon i','early seek:fu'], '1-29':['fear of kjv_lord'],
   '2-7':['sure wisdom','kjv_uprightness:adv'], '2-18':['her/house to death bend:pr'],
   '3-5':['thine own understanding rely:neg:imp'], '3-8':['kjv_navel','marrow'],
   '3-16':['kjv_right_side','left hand'], '3-19':['kjv_foundation of earth:a lay:perf'],
   '3-28':['say:neg:imp','tomorrow i give:fu','when thou it:a by thee have:pr'],
   '4-3':['only beloved','my/mother'], '4-4':['he i:a also teach:pa','to i say:pa'],
   '4-11':['kjv_upright path:pl'], '4-12':['narrow:caus:psv:neg:fu'],
   '4-13':['strongly hold:imp'], '4-23':['life issue:pr'], '4-25':['straight on'],
   '5-4':['two edge:pl'], '5-5':['kjv_hell'], '5-6':['lest thou','know:neg:can'],
   '5-12':['i instruction:a hate:perf'], '5-16':['disperse:psv:opt'],
   '5-17':['only thine own','not of stranger:pl'], '5-19':['breast:pl','delight:psv:imp'],
   '6-3':['thy/friend:a urge:imp'], '6-6':['kjv_ant','lazy:ag'],
   '6-7':['no guide kjv_overseer or ruler'], '6-8':['her/food:a in summer'],
   '6-10':['kjv_fold_limb:ev'], '6-11':['thy/lack as armed man'],
   '6-16':['six thing:pl:a','seven kjv_abomination'], '6-26':['kjv_harlot','kjv_adulteress'],
   '6-30':['despise:neg:pr','hungry'], '6-31':['seven kjv_fold','all substance'],
   '7-2':['apple of thine eye'], '7-4':['my/sister','kjv_kinswoman'],
   '7-14':['i peace kjv_offering:pl:a'], '7-17':['kjv_myrrh kjv_lign_aloes and kjv_cinnamon'],
   '7-18':['we:du our/fill:a','we:du ourselves:a'], '7-19':['husband at home be:neg:pr'],
   '7-22':['fool to kjv_chastise:ev of stocks'], '7-24':['i:a','child:pl:excl'],
  }.items():
   for p in parts:self.assertIn(p,cases['proverbs-'+ref]['analysis'],(ref,p))
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_naive','kjv_discretion','kjv_ant','kjv_fold_limb'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
