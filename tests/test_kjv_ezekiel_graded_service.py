import unittest,re
from tools.kjv_archive import load_register,read

class EzekielGradedServiceTests(unittest.TestCase):
 def test_voices_ritual_tensions_and_unit_ratios(self):
  prior,_=load_register('0.10-kjv.166');lang,manifest=load_register('0.10-kjv.167')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('ezekiel-'):c for c in read(lang.folder/'ezekiel-returning-glory-and-graded-service-cases.json')}
  self.assertEqual(set(cases),{f'{ch}-{v}' for ch,n in [(43,27),(44,31),(45,25)] for v in range(1,n+1)})
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text'])
   self.assertFalse({'one','post','story','leaf','court','count','fashion','meat','fold','right','light','bear','settle','just','suffer','mark'}&set(r['keys']))
  for r,parts in {
   '43-3':['when i to city:a destroy:inf come:pa','my/face'],
   '43-6':['out of house to i speak:cv','man by i stand:pa'],
   '43-7':['mypl/throne','mypl/foot:pl','ipl in middle','kjv_corpse:pl','their/high place:pl'],
   '43-8':['their/kjv_threshold:a by mypl/kjv_threshold:pl','wall between ipl and they'],
   '43-9':['away put:opt','forever dwell:fu'],
   '43-10':['house:a to house of kjv_israel','ashamed be:may'],
   '43-11':['if they','form:a of house and form:a of it','in come:ev:pl'],
   '43-13':['kjv_cubit kjv_cubit and kjv_handbreadth','one_num kjv_span'],
   '43-14':['lower kjv_ledge two','greater kjv_ledge four'],
   '43-17':['half kjv_cubit','his/kjv_stair:pl towards east'],
   '43-19':['seed of kjv_zadok','to ipl serve:ev'],
   '43-21':['thou also','he it:a','outside kjv_sanctuary'],
   '43-24':['salt:a upon they'],
   '43-26':['they themselves:a consecrate:fu'],
   '43-27':['eight:ord day','ipl you:a accept:fu'],
   '44-2':['open:psv:neg:fu','no man','kjv_lord god of kjv_israel'],
   '44-3':['prince he in it','kjv_porch'],
   '44-5':['well heed:imp','ipl to thee'],
   '44-7':['in heart kjv_circumcise:psv:neg:adj','in flesh kjv_circumcise:psv:neg:adj','they mypl/kjv_covenant:a'],
   '44-10':['their/kjv_iniquity:a endure:fu'],
   '44-11':['yet they','slay:fu'],
   '44-12':['fall:caus:pa'],
   '44-13':['near come:neg:fu','their/shame:a'],
   '44-15':['son:pl of kjv_zadok','kjv_fat:a and blood:a'],
   '44-17':['linen garment:pl','no kjv_wool'],
   '44-18':['sweat:a cause:pr','kjv_gird:neg:fu'],
   '44-19':['people:a with their/garment:pl sanctify:neg:fu'],
   '44-20':['only their/head:pl:a kjv_poll_hair:fu'],
   '44-22':['widow:a','she that away put:psv:pr','or widow:a that priest before have:pa'],
   '44-23':['holy and kjv_unholy_profane','kjv_unclean_ritual and clean'],
   '44-25':['sister that no husband','defile:may'],
   '44-26':['after he clean:psv:pr','they to he seven day:pl:a'],
   '44-28':['ipl their/inheritance','ipl their/kjv_possession'],
   '44-30':['first:a of your/dough','in thine/house rest:caus:may'],
   '45-1':['two+twelve+thousand and thousand kjv_measuring_reed:pl'],
   '45-5':['twelve and eight chamber:pl'],
   '45-8':['mypl/prince:pl mypl/people:a no more oppress:fu'],
   '45-9':['your/extort:ev:pl:a'],
   '45-10':['honest balance:pl','honest kjv_ephah_measure','honest kjv_bath_measure'],
   '45-11':['one_num measure','kjv_tenth_share:a of kjv_homer'],
   '45-12':['twelve and eight kjv_shekel:pl','two+twelve and one_num kjv_shekel:pl','twelve and three kjv_shekel:pl','your/kjv_maneh'],
   '45-13':['kjv_sixth_share of kjv_ephah_measure of kjv_homer of wheat','kjv_sixth_share of kjv_ephah_measure of kjv_homer of kjv_barley'],
   '45-14':['kjv_cor_measure','ten kjv_bath_measure:pl'],
   '45-15':['one_num kjv_lamb','two+hundred'],
   '45-17':['kjv_drinkoffer:pl:a','sin kjv_offering:a'],
   '45-20':['seven:ord day','kjv_simple_unwitting'],
   '45-22':['prince for himself','sin kjv_offering'],
   '45-24':['one_num kjv_hin of oil for one_num kjv_ephah_measure'],
   '45-25':['seven:ord month','twelve and three:ord day']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(cases['43-11']['analysis'].count('all form:pl:a'),2)
  self.assertEqual(cases['44-2']['analysis'].count('shut:psv:fu'),2)
  self.assertEqual(cases['45-23']['analysis'].split().count('seven'),4)
  self.assertFalse(any(re.search(r'\b(iplself|wesg|wepl|ourone)\b|:du',c['analysis']) for c in cases.values()))
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_maneh','kjv_cor_measure','kjv_simple_unwitting'})
  self.assertEqual(lang.lexicon['simple']['form'],lang.lexicon['kjv_simple_unwitting']['form'])
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
