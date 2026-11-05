import unittest,re
from tools.kjv_archive import load_register,read
class IsaiahVineyardsSiegesTests(unittest.TestCase):
 def test_voice_repetitions_and_concrete_senses(self):
  prior,_=load_register('0.10-kjv.133');lang,manifest=load_register('0.10-kjv.134')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('isaiah-'):c for c in read(lang.folder/'isaiah-vineyards-refused-rest-and-sieges-cases.json')};self.assertEqual(len(cases),108)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','sieve','fan','plain','issue','host','count','profit'}&set(result['keys']))
  expected={'i':'28-22 29-11 29-12 29-16 30-7 31-4','ipl':'27-3 27-4 27-5 28-16 28-17 29-2 29-3 29-13 29-14 30-1','mypl':'27-5 29-23 30-1 30-2','wesg':'28-15 29-15 30-10 30-11 30-16','ourone':'28-15'}
  for k,refs in expected.items():self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in{
   '27-1':['leviathan pierce:adj','kjv_dragon_creature'],
   '27-3':['ipl kjv_lord','every moment'],'27-4':['fury in ipl be:neg:pr','burn:pr would'],
   '27-5':['peace:a with ipl make:may','peace:a with ipl make:fu'],
   '27-8':['forth sprout:pr','wind restrain:pr'],'27-9':['kjv_chalkstone:pl'],
   '27-11':['mercy:a have:neg:fu','no favour'],'27-12':['each by each'],
   '28-4':['early fruit before summer','up eat:pr'],'28-7':['kjv_swallow:psv:pr'],
   '28-8':['kjv_meal_table:pl','kjv_vomit:ev'],'28-11':['kjv_stammer:adj','another tongue'],
   '28-12':['hear:inf will:neg:pa'],'28-15':['wesg','ourone/kjv_refuge','kjv_hell_depth'],
   '28-16':['haste:a make:neg:fu'],'28-21':['his/strange work:a','his/strange act:a'],
   '28-25':['kjv_fitches','kjv_cummin','wheat','kjv_barley','kjv_rie'],
   '28-28':['his/kjv_horseman:pl'],
   '29-2':['to ipl as kjv_ariel_city'],'29-7':['her/fortify:ev'],
   '29-11':['seal:psv:adj book','i read:neg:can'],'29-12':['i learned be:neg:pr'],
   '29-15':['who wesg:a see:pr?','who wesg:a know:pr?'],
   '29-16':['he i:a make:neg:pa'],'29-23':['mypl/hand:pl','mypl/name'],
   '30-6':['kjv_camel_hump:pl','fire:adj fly:adj serpent'],
   '30-8':['in table write:imp'],'30-10':['kjv_right_conduct:adj'],
   '30-14':['kjv_potsherd_scraper','kjv_hearth fire','kjv_pit water'],
   '30-15':['return:ev and rest','will:neg:pa'],
   '30-17':['one_num+thousand','rebuke of one_num','rebuke of five','kjv_beacon'],
   '30-21':['kjv_right_side','left'],'30-22':['cloth of kjv_menstrual_flow'],
   '30-24':['ground:a plough:pr','kjv_winnowing_fan'],
   '30-26':['seven kjv_fold','seven day:pl'],
   '30-28':['kjv_dry_sieve','err:caus:cv'],'30-30':['descend:ev:a of his/arm'],
   '30-32':['ground:psv:adj staff','battle:pl of shake:ev'],
   '30-33':['kjv_tophet','kjv_brimstone'],
   '31-2':['evil:a bring:fu'],'31-3':['human:pl be:pr and not god','flesh be:pr and not spirit'],
   '31-5':['shield:fu','deliver:fu','over pass:cv','preserve:fu'],
   '31-8':['not of mighty human','not of low rank human']
  }.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  for r in('28-10','28-13'):
   self.assertEqual(cases[r]['analysis'].count('kjv_precept upon kjv_precept'),2);self.assertEqual(cases[r]['analysis'].count('line upon line'),2)
  self.assertEqual(cases['29-14']['analysis'].count('wonder:adj work'),2)
  self.assertEqual(cases['30-16']['analysis'].count('wesg upon'),2)
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_chalkstone','kjv_stammer','kjv_fitches','kjv_cummin','kjv_camel_hump','kjv_beacon','kjv_winnowing_fan','kjv_dry_sieve','kjv_perazim','kjv_ariel_city','kjv_hanes','kjv_tophet'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
