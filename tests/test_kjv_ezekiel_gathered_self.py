import unittest,re
from tools.kjv_archive import load_register,read

class EzekielGatheredSelfTests(unittest.TestCase):
 def test_gathered_self_and_invading_host(self):
  prior,_=load_register('0.10-kjv.164');lang,manifest=load_register('0.10-kjv.165')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('ezekiel-'):c for c in read(lang.folder/'ezekiel-gathered-self-and-invading-host-cases.json')};self.assertEqual(len(cases),80)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text'])
   self.assertFalse({'one','host','bow','ghost','fold','care','plain','border','stuff','lock','divine','eminent','wax','fashion','fair','meat','worship','spy','waste','spring','shoot','flourish','point','privy','raven','pile','despite','row','wound','habit','shroud','hell','roll','bear','light','right','stick','observe','steep'}&set(r['keys']))
  for r,parts in {
   '37-1':['in spirit of kjv_lord'],
   '37-3':['these bone:pl live:can?','i answer:pa','thou know:pr'],
   '37-5':['ipl breath:a into you enter:caus:fu'],
   '37-7':['bone to his/bone'],
   '37-8':['no breath in they'],
   '37-9':['to wind','four wind:pl','oh breath','breathe:imp'],
   '37-11':['ourone/bone:pl','ourone/hope','wesg off cut:psv:pr for ourone/part:pl'],
   '37-12':['your/grave:pl:a open:fu'],
   '37-14':['mypl/spirit:a'],
   '37-16':['one_num kjv_stick_wood:a','for kjv_judah','for kjv_joseph','kjv_ephraim'],
   '37-17':['they:du:a each to another','one_num kjv_stick_wood','they:du one_num'],
   '37-18':['to wesg','show:neg:fu?'],
   '37-19':['kjv_tribe:pl:a of kjv_israel','they:a with he','one_num in mypl/hand'],
   '37-20':['kjv_stick_wood:pl'],
   '37-22':['one_num nation','one_num king','no more two nation:pl','two kingdom:pl'],
   '37-23':['their/dwell:ev place:pl'],
   '37-24':['kjv_david mypl/servant','one_num shepherd:a'],
   '37-25':['your/father:pl','their/child:pl child:pl','kjv_david their/prince forever'],
   '37-26':['eternal kjv_covenant'],
   '37-27':['mypl/kjv_tabernacle'],
   '38-2':['kjv_gog_oracle','kjv_magog_land','chief prince of kjv_meshech and kjv_tubal'],
   '38-4':['kjv_hook:pl:a into thy/jaw:pl','sword:pl:a hold:cv'],
   '38-8':['later year:pl','always ruin:psv:adj'],
   '38-11':['thou say:fu ipl','neither bar:pl nor gate:pl'],
   '38-12':['middle of land'],
   '38-13':['young lion:pl'],
   '38-14':['know:neg:fu?'],
   '38-16':['ipl thee:a against mypl/land bring:fu','ipl in thee','sanctify:psv:fu'],
   '38-18':['mypl/fury in mypl/face'],
   '38-20':['cliff:pl'],
   '38-21':['every man sword against his/brother'],
   '38-22':['kjv_litigate:fu','hail stone:pl fire and kjv_brimstone'],
   '38-23':['ipl iplself:a great make:fu','iplself:a sanctify:fu'],
   '39-2':['only kjv_sixth_share of thee'],
   '39-3':['thy/left hand','thy/kjv_right_side hand'],
   '39-6':['without worry in kjv_isle:pl'],
   '39-7':['allow:neg:fu','kjv_holy_one'],
   '39-8':['it come:perf','it do:psv:pr'],
   '39-9':['hand staff:pl and kjv_spear:pl','seven year:pl'],
   '39-11':['nose:pl:a of pass:ag:pl stop:fu','kjv_hamongog'],
   '39-12':['seven month:pl','bury:cv be:fu'],
   '39-14':['with pass:ag:pl','after end of seven month:pl'],
   '39-15':['sign:a by it'],
   '39-16':['kjv_hamonah'],
   '39-17':['ipl for you kjv_sacrifice:a offer:pr','blood:a drink:may'],
   '39-18':['kjv_fatling:pl of kjv_bashan'],
   '39-19':['until you drunk'],
   '39-20':['mypl/kjv_meal_table','horse:pl and chariot:pl'],
   '39-23':['they all by sword'],
   '39-26':['endure:perf'],
   '39-28':['lead:psv:caus:pa','none of they any more there leave:perf'],
   '39-29':['mypl/spirit:a','out pour:perf']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual({r for r,c in cases.items() if ':du' in c['analysis']},{'37-17'})
  self.assertEqual({r for r,c in cases.items() if 'iplself' in c['analysis']},{'38-23'})
  self.assertEqual(cases['38-23']['analysis'].count('iplself'),2)
  self.assertEqual({r for r,c in cases.items() if re.search(r'\bwesg\b',c['analysis'])},{'37-11','37-18'})
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),4)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
