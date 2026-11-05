import unittest,re
from tools.kjv_archive import load_register,read
class ProverbAgurListsTests(unittest.TestCase):
 def test_question_speakers_lists_materials_and_maternal_agency(self):
  prior,_=load_register('0.10-kjv.125');lang,manifest=load_register('0.10-kjv.126')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id']:c for c in read(lang.folder/'proverbs-agur-lists-and-maternal-teaching-cases.json')};self.assertEqual(len(cases),119)
  personal=set()
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'just','want','sound','hell','simple','right','plain','mean','scale','train','conceit','discover','whip','kjv_mortar','charm','substance','riot','bear'}&set(out['keys']))
   self.assertNotRegex(c['analysis'],r'(?<![a-z_])(?:ipl|mypl|iplself|wesg|wepl|ourone)(?![a-z_])')
   if re.search(r'(?<![a-z_])i(?![a-z_])',c['analysis']):personal.add(c['id'])
  self.assertEqual(personal,{'proverbs-30-'+r for r in ['2','3','7','8','9','18','20']})
  for ref,parts in {
   '28-3':['poor human who poor:a oppress:pr'],'28-8':['his/wealth:a increase:pr'],
   '28-13':['confess:pr and forsake:pr'],'28-15':['wandering bear_animal'],
   '28-16':['understanding:a lack:pr'],'28-17':['no human he:a hold:imp'],'28-18':['suddenly fall:fu'],
   '28-21':['person:pl:a favour:inf'],'28-24':['it transgress:ev be:neg:pr'],
   '29-2':['wicked rule:pr'],'29-7':['cause:a of poor'],'29-10':['kjv_righteous his/soul:a seek:pr'],
   '29-18':['people perish:pr'],'29-21':['his/son become:caus:fu'],
   '29-23':['honour humble:a in spirit support:fu'],'29-24':['it:a reveal:neg:pr'],
   '30-1':['kjv_agur son of kjv_jakeh','kjv_ucal'],'30-4':['what name of his/son if thou tell:can?'],
   '30-7':['two thing:pl:a i'],'30-8':['food fitting for i'],'30-9':['name of my/god:a in vain'],
   '30-13':['be:pr:excl'],'30-15':['kjv_horseleech two daughter:pl','give:imp give:imp','three thing:pl','four thing:pl'],
   '30-18':['three thing:pl','indeed four'],'30-21':['three thing:pl','for four which it carry:neg:can'],
   '30-24':['four thing:pl'],'30-28':['spider with her/hand:pl'],'30-29':['three thing:pl','indeed four'],
   '30-31':['kjv_greyhound','kjv_male kjv_goat'],'30-33':['churn:ev of milk','kjv_wring:ev of nose'],
   '31-1':['his/mother to he teach:pa'],'31-2':['my/womb?','my/vow:pl?'],
   '31-5':['judgment:a of any of kjv_afflict:psv:adj'],'31-8':['for kjv_mute'],
   '31-12':['good:a do:fu and evil:a do:neg:fu'],'31-16':['field:a consider:pr and it:a buy:pr'],
   '31-19':['kjv_spindle','kjv_distaff'],'31-21':['kjv_scarlet'],'31-22':['kjv_tapestry','silk and purple'],
   '31-24':['fine linen:a make:pr and sell:pr'],'31-30':['pleasing appearance deceitful'],
   '31-31':['her/own work:pl she:a in gate:pl praise:imp'],
  }.items():
   for p in parts:self.assertIn(p,cases['proverbs-'+ref]['analysis'],(ref,p))
  self.assertEqual(cases['proverbs-30-4']['analysis'].count('?'),5)
  self.assertEqual(cases['proverbs-30-1']['analysis'].count('kjv_ithiel_agur'),2)
  for n in range(11,15):self.assertTrue(cases[f'proverbs-30-{n}']['analysis'].startswith('generation be:pr'))
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_agur','kjv_jakeh','kjv_ithiel_agur','kjv_ucal','kjv_lemuel','kjv_horseleech','kjv_greyhound','kjv_spindle','kjv_distaff','kjv_tapestry'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
