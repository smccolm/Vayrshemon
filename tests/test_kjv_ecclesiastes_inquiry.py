import unittest,re
from tools.kjv_archive import load_register,read
class EcclesiastesInquiryTests(unittest.TestCase):
 def test_personal_shared_dual_voices_and_unresolved_questions(self):
  prior,_=load_register('0.10-kjv.126');lang,manifest=load_register('0.10-kjv.127')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id']:c for c in read(lang.folder/'ecclesiastes-personal-inquiry-and-shared-mortality-cases.json')};self.assertEqual(len(cases),114)
  voices={k:set() for k in ['i','wesg','they:du']}
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'one','just','want','sound','hell','simple','right','plain','mean','scale','train','conceit','discover','whip','charm','substance','riot','bear','kjv_travail','exercise','kjv_bereave'}&set(out['keys']))
   self.assertNotRegex(c['analysis'],r'(?<![a-z_])(?:ipl|mypl|iplself|wepl|ourone)(?![a-z_])')
   for k in voices:
    if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis']):voices[k].add(c['id'])
  self.assertEqual(voices['wesg'],{'ecclesiastes-1-10'})
  self.assertEqual(voices['they:du'],{'ecclesiastes-4-'+n for n in ['9','10','11']})
  expected_i='1-12 1-13 1-14 1-16 1-17 2-1 2-2 2-3 2-4 2-5 2-6 2-7 2-8 2-9 2-10 2-11 2-12 2-13 2-14 2-15 2-17 2-18 2-19 2-20 2-24 2-25 3-10 3-12 3-14 3-16 3-17 3-18 3-22 4-1 4-2 4-4 4-7 4-8 4-15 5-13 5-18 6-1 6-3'.split()
  self.assertEqual(voices['i'],{'ecclesiastes-'+n for n in expected_i})
  for ref,parts in {
   '1-1':['kjv_preacher son of kjv_david'],'1-6':['kjv_south','kjv_north','his/kjv_circuit:pl'],
   '1-13':['kjv_grievous kjv_toil','busy:caus:psv:inf'],'1-15':['lack:pr kjv_number:psv:neg:can'],
   '1-16':['mine/own heart kjv_commune:pa'],'1-18':['much wisdom much grief'],
   '2-1':['with mirth test:fu'],'2-5':['kjv_orchard'],'2-7':['born:psv:adj in my/house'],
   '2-8':['kjv_male sing:ag:pl','woman sing:ag:pl','musical instrument:pl'],
   '2-13':['wisdom folly:a exceed:pr'],'2-14':['one_num event'],'2-17':['i life:a hate:pa'],
   '2-20':['despair:caus:inf turn:pa'],'2-24':['from hand of god'],'2-25':['more than i hasten:can?'],
   '3-2':['born:psv:inf'],'3-5':['kjv_forbear:inf'],'3-7':['kjv_sew:inf'],
   '3-11':['world:a in their/heart'],'3-15':['god that which past be:pr require:pr'],
   '3-18':['they themselves beast:pl'],'3-19':['one_num thing','one_num breath','no advantage above beast'],
   '3-20':['one_num place'],'3-21':['who spirit:a','up go:pr','down to earth'],
   '4-4':['skilled work:a','by his/neighbour kjv_envy:psv:pr'],'4-5':['kjv_fold_limb:pr'],
   '4-8':['good:a from my/soul withhold:pr?'],'4-12':['three kjv_fold kjv_cord'],
   '4-13':['instruction:a no more receive:fu'],'4-15':['second child'],
   '5-5':['vow:neg:should','pay:neg:should'],'5-6':['before angel','allow:neg:imp'],
   '5-8':['higher than highest','higher than they'],'5-9':['king himself by field serve:psv:pr'],
   '5-12':['sleep:inf allow:neg:fu'],'5-19':['power:a to of it eat:inf'],
   '5-20':['god he:a in joy of his/heart answer:pr'],'6-2':['give:neg:pr but stranger it:a eat:pr'],
   '6-3':['hundred child:pl','kjv_untimely_birth'],'6-6':['two+thousand year:pl','one_num place'],
   '6-10':['it human be:pr'],'6-11':['many thing:pl'],
  }.items():
   for p in parts:self.assertIn(p,cases['ecclesiastes-'+ref]['analysis'],(ref,p))
  self.assertEqual(cases['ecclesiastes-1-2']['analysis'].count('vanity of vanity:pl'),2)
  self.assertEqual(cases['ecclesiastes-4-1']['analysis'].count('no comfort:ag:a have:pa'),2)
  self.assertTrue(cases['ecclesiastes-3-21']['analysis'].endswith('?'))
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_preacher','kjv_toil','kjv_orchard'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
