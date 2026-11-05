import unittest,re
from tools.kjv_archive import load_register,read

class EzekielSharedInheritanceTests(unittest.TestCase):
 def test_healing_exceptions_and_inheritance(self):
  prior,_=load_register('0.10-kjv.167');lang,manifest=load_register('0.10-kjv.168')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('ezekiel-'):c for c in read(lang.folder/'ezekiel-healing-waters-and-shared-inheritance-cases.json')}
  self.assertEqual(set(cases),{f'{ch}-{v}' for ch,n in [(46,24),(47,23),(48,35)] for v in range(1,n+1)})
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text'])
   self.assertFalse({'one','post','story','court','count','fashion','meat','fold','right','light','settle','just','suffer','mark','desert','border'}&set(r['keys']))
  for r,parts in {
   '46-1':['six work:cv day:pl','day of new moon'],
   '46-2':['until evening shut:psv:neg:fu'],
   '46-5':['as he give:fu:can','one_num kjv_hin of oil to one_num kjv_ephah_measure'],
   '46-7':['his/hand reach:fu'],
   '46-8':['by way of it forth go:fu'],
   '46-9':['kjv_north gate','kjv_south gate','return:neg:fu','opposite it forth go:fu'],
   '46-10':['prince in middle of they'],
   '46-12':['willing:adv','person then for he','after his/forth go:ev person'],
   '46-13':['one_num:ord year'],
   '46-14':['kjv_sixth_share of kjv_ephah_measure','kjv_third_share of kjv_hin','mix:ev'],
   '46-16':['if prince gift:a','their/kjv_possession by inheritance'],
   '46-17':['year of free:ev','to prince return:fu'],
   '46-18':['oppress:ev take:neg:fu','mypl/people','scatter:psv:neg:may'],
   '46-19':['two side:pl towards west'],
   '46-20':['people:a sanctify:inf carry:neg:may'],
   '46-22':['join:psv:adj','three+twelve and four','two+twelve and six','one_num measure'],
   '46-23':['row of build:ev','under row:pl'],
   '47-1':['kjv_right_side side','kjv_south side of altar'],
   '47-3':['thousand kjv_cubit:pl:a','kjv_ankle:pl'],
   '47-4':['knee:pl','kjv_loins'],
   '47-5':['i across pass:neg:pa:can','swim:inf','pass:psv:neg:pa:can'],
   '47-8':['kjv_wilderness','water:pl heal:psv:fu'],
   '47-9':['wherever river:pl','where river come:pr'],
   '47-10':['kjv_engedi even to kjv_eneglaim','their/kjv_fish'],
   '47-11':['heal:psv:neg:fu','to salt give:psv:fu'],
   '47-12':['leaf fade:neg:fu','neither fruit of it consume:psv:fu','his/month:pl','leaf of it for medicine'],
   '47-13':['twelve kjv_tribe:pl','kjv_joseph two kjv_portion_share:pl'],
   '47-14':['ipl mypl/hand:a'],
   '47-16':['kjv_berothah','kjv_hazarhatticon','kjv_hauran'],
   '47-17':['kjv_hazarenan','kjv_north towards kjv_north'],
   '47-19':['kjv_tamar_boundary','strife in kjv_kadesh','river to great sea'],
   '47-22':['to stranger:pl','beget:fu','bear:psv:adj','inheritance:a with you'],
   '47-23':['in what kjv_tribe stranger kjv_sojourn:pr'],
   '48-8':['two+twelve+thousand and thousand kjv_measuring_reed:pl'],
   '48-11':['mypl/kjv_charge_custody:a','astray go:neg:pa'],
   '48-14':['sell:neg:fu','neither exchange:fu','to another give:fu'],
   '48-15':['kjv_unholy_profane place for city'],
   '48-19':['out of all kjv_tribe:pl of kjv_israel'],
   '48-31':['one_num gate of kjv_levi'],
   '48-32':['five+hundred; and three gate:pl','one_num gate of kjv_joseph'],
   '48-35':['twelve+thousand and six+thousand measure:pl','name of city from that day','kjv_lord there be:pr']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(cases['47-4']['analysis'].count('thousand:a'),2)
  self.assertEqual(cases['48-16']['analysis'].count('four+thousand and five+hundred'),4)
  self.assertEqual(cases['48-17']['analysis'].count('two+hundred and four+twelve and two'),4)
  for r in ['48-31','48-32','48-33','48-34']:self.assertEqual(cases[r]['analysis'].count('one_num gate'),3)
  self.assertEqual({r for r,c in cases.items() if re.search(r'\bipl\b',c['analysis'])},{'47-14'})
  self.assertFalse(any(re.search(r'\b(iplself|wesg|wepl|ourone)\b|:du',c['analysis']) for c in cases.values()))
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_ankle','kjv_marsh','kjv_eneglaim','kjv_hethlon','kjv_berothah','kjv_sibraim','kjv_hazarhatticon','kjv_hauran','kjv_tamar_boundary'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
