import unittest,re
from tools.kjv_archive import load_register,read
class ProverbWisdomOriginsTests(unittest.TestCase):
 def test_personified_origin_speech_maxims_and_negative_scope(self):
  prior,_=load_register('0.10-kjv.121');lang,manifest=load_register('0.10-kjv.122')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id']:c for c in read(lang.folder/'proverbs-wisdom-origins-maxims-cases.json')};self.assertEqual(len(cases),145)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'just','fast','want','fair','sound','hell','simple','right','witty','invention','plain','render','meet'}&set(out['keys']))
   self.assertNotRegex(c['analysis'],r'(?<![a-z_])(?:ipl|mypl|iplself|wesg|wepl)(?![a-z_])')
  for ref,parts in {
   '8-4':['i call:pr','son:pl of human'],'8-9':['all clear','kjv_upright'],
   '8-12':['i wisdom','wise plan:pl'],'8-14':['sure wisdom','i understanding'],
   '8-22':['kjv_lord i:a','possess:pa','before his/work:pl of old'],
   '8-23':['from ever','before ever earth'],'8-24':['i forth bring:psv:pa'],
   '8-26':['most high part of dust'],'8-27':['circle:a upon face of kjv_depth'],
   '8-30':['as one with he rear:psv:pa','daily his/delight'],
   '8-31':['suitable for dwell:inf','son:pl of human'],'8-35':['favour of kjv_lord'],
   '9-1':['her/seven kjv_pillar:pl'],'9-2':['beast:pl:a kill:perf','kjv_meal_table'],
   '9-4':['kjv_naive','understanding:a lack:pr'],'9-10':['knowledge of holy'],
   '9-13':['foolish woman clamorous'],'9-16':['kjv_naive','understanding:a lack:pr'],
   '9-17':['steal:psv:adj water:pl'],'9-18':['kjv_hell'],
   '10-3':['starve:inf allow:neg:fu','substance of wicked'],'10-4':['kjv_slack','kjv_diligent'],
   '10-15':['poor their/poor:ev'],'10-19':['sin lack:neg:pr'],'10-22':['no sorrow'],
   '10-26':['vinegar','smoke','lazy:ag'],'11-1':['true weight'],'11-15':['pain:a suffer:fu'],
   '11-21':['punish:psv:neg:adj remain:neg:fu'],'11-22':['pig/nose','beautiful woman'],
   '11-24':['more than suitable'],'11-25':['generous soul fat:caus:psv:fu'],
   '11-30':['soul:pl:a gain:pr'],'12-9':['servant:a have:pr'],
   '12-10':['tender mercy:pl of wicked cruel'],'12-14':['give:psv:fu'],
   '12-15':['in his/own eye:pl'],'12-16':['immediately'],'12-21':['no kjv_calamity'],
   '12-23':['knowledge:a conceal:pr'],'12-24':['kjv_tribute'],
   '12-26':['than his/neighbour more excellent'],'12-27':['roast:neg:pr'],'12-28':['no death'],
  }.items():
   for p in parts:self.assertIn(p,cases['proverbs-'+ref]['analysis'],(ref,p))
  for a,b in [('10-6','10-11'),('10-8','10-10')]:self.assertEqual(cases['proverbs-'+a]['analysis'].split('but ')[1],cases['proverbs-'+b]['analysis'].split('but ')[1])
  with self.assertRaisesRegex(ValueError,'DUPLICATE_FEATURE'):lang.compile('wicked punish:psv:neg:neg:fu.')
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_meal_table','kjv_diligent'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
