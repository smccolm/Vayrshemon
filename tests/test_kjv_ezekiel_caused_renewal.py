import unittest,re
from tools.kjv_archive import load_register,read

class EzekielCausedRenewalTests(unittest.TestCase):
 def test_communal_claims_and_caused_renewal(self):
  prior,_=load_register('0.10-kjv.163');lang,manifest=load_register('0.10-kjv.164')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('ezekiel-'):c for c in read(lang.folder/'ezekiel-communal-claims-and-caused-renewal-cases.json')};self.assertEqual(len(cases),117)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text'])
   self.assertFalse({'one','host','bow','ghost','fold','care','plain','border','stuff','lock','divine','eminent','wax','fashion','fair','meat','worship','spy','waste','spring','shoot','flourish','point','privy','raven','pile','despite','row','wound','habit','shroud','hell','roll','bear','light','grave','right'}&set(r['keys']))
  for r,parts in {
   '33-2':['their/kjv_coast_region:pl','their/watch:ag'],
   '33-6':['blow:neg:pr','kjv_warn_solemn:psv:neg:pr','in his/kjv_iniquity','ipl at watch:ag hand'],
   '33-7':['mypl/mouth'],
   '33-10':['ourone/transgress:ev:pl','ourone/sin:pl upon wesg','how wesg then live:should?'],
   '33-11':['ipl no pleasure:a','you turn:imp you'],
   '33-12':['deliver:neg:fu','fall:neg:fu','neither kjv_righteous'],
   '33-13':['his/kjv_righteousness:pl remember:psv:neg:fu'],
   '33-15':['pledge:a restore:pr','rob:pp again give:pr','die:neg:fu'],
   '33-16':['none of his/sin:pl','kjv_mention:psv:fu'],
   '33-17':['way of lord equal be:neg:pr','their/way equal be:neg:pr'],
   '33-20':['ipl you:a each after his/way:pl'],
   '33-21':['twelve:ord year of ourone/kjv_captivity','ten:ord month','five:ord day','person who'],
   '33-22':['in evening before','to i in morning','i no more dumb'],
   '33-24':['kjv_abraham one_num','wesg many be:pr','to wesg for inheritance'],
   '33-25':['with blood eat:pr','possess:fu?'],
   '33-26':['each his/neighbour wife:a'],
   '33-30':['against thee by wall:pl','i you:a pray:pr'],
   '33-31':['as mypl/people','much love:a show:pr','their/kjv_covet:ev'],
   '33-32':['lovely song of person','do:neg:pr'],
   '34-2':['kjv_prophesy:imp kjv_prophesy:imp','woe:excl','feed:neg:should?'],
   '34-3':['kjv_fat:a','feed:psv:pr kill:pr'],
   '34-4':['strong make:neg:perf','with force and with cruelty'],
   '34-8':['no shepherd','mypl/shepherd:pl','mypl/flock:a feed:neg:pa'],
   '34-10':['from their/mouth','food for they be:neg:may'],
   '34-11':['ipl even ipl'],
   '34-14':['good sheepfold','fat kjv_pasture'],
   '34-16':['fat and strong:a destroy:fu','with judgment feed:fu'],
   '34-17':['kjv_ram:pl and kjv_male kjv_goat:pl'],
   '34-20':['ipl even ipl','thin kjv_livestock'],
   '34-23':['one_num shepherd:a','mypl/servant kjv_david'],
   '34-24':['ipl kjv_lord their/god','mypl/servant kjv_david prince'],
   '34-27':['kjv_yoke_band:pl:a','themselves:a of they serve:pa'],
   '34-29':['plant:a of renown','shame:a of kjv_heathen any more endure:fu'],
   '34-31':['flock of mypl/kjv_pasture man:pl'],
   '35-5':['their/kjv_iniquity end:a have:pa'],
   '35-6':['blood:a hate:neg:perf'],
   '35-10':['two nation:pl','two country:pl of ipl','wesg it:a possess:fu'],
   '35-11':['against they:du','ipl iplself:a among they:du'],
   '35-12':['they to wesg to consume:inf'],
   '36-2':['kjv_gloat_aha:excl','of wesg in kjv_possession'],
   '36-3':['kjv_infamy'],
   '36-5':['contempt:adj mind:pl'],
   '36-8':['your/branch:pl:a forth grow:caus:fu'],
   '36-11':['your/old state:pl','better than at your/begin:ev:pl'],
   '36-15':['hear:caus:fu','fall:caus:fu'],
   '36-17':['kjv_unclean_ritual:ev of kjv_menstrual_flow woman'],
   '36-20':['they to they say:pa','out of his/land'],
   '36-21':['pity:a for mypl/holy name'],
   '36-22':['for your/sake:pl do:neg:pr','but for mypl/holy name sake'],
   '36-23':['ipl in you before their/eye:pl sanctify:psv:fu'],
   '36-25':['kjv_clean_ritual water:a','kjv_sprinkle:fu'],
   '36-26':['new spirit:a','stone:adj heart:a','heart of flesh'],
   '36-27':['mypl/spirit:a within you','mypl/kjv_statute:pl walk:caus:fu'],
   '36-29':['for corn','no kjv_famine:a'],
   '36-31':['yourselves:a in your/own sight','loathe:fu'],
   '36-32':['not for your/sake:pl'],
   '36-35':['like kjv_garden of kjv_eden','fortify:psv:perf'],
   '36-37':['kjv_consult:psv:fu'],
   '36-38':['flock:pl of man:pl']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual({r for r,c in cases.items() if ':du' in c['analysis']},{'35-11'})
  self.assertEqual({r for r,c in cases.items() if 'iplself' in c['analysis']},{'35-11'})
  self.assertEqual({r for r,c in cases.items() if re.search(r'\bwesg\b',c['analysis'])},{'33-10','33-24','35-10','35-12','36-2'})
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),1)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
