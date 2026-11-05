import unittest,re
from tools.kjv_archive import load_register,read

class JeremiahInwardCovenantTests(unittest.TestCase):
 def test_shared_self_distinct_voices_and_inward_law(self):
  prior,_=load_register('0.10-kjv.148');lang,manifest=load_register('0.10-kjv.149')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-communal-return-and-inward-covenant-cases.json')};self.assertEqual(len(cases),96)
  keys={}
  for r,c in cases.items():
   result=lang.compile(c['analysis']);keys[r]=set(result['keys'])
   self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','host','bow','dragon','snuff','ghost','desert','right','court','bond','plead'}&keys[r]);self.assertNotIn(':du',c['analysis'])
  for k,refs in {'i':'31-26','wesg':'29-15 29-28 30-5 31-6','ourone':'31-6','wepl':'','iplself':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for k,refs in {'light':{'31-35'},'former':{'30-20'},'tear':{'31-16'}}.items():self.assertEqual({r for r,ks in keys.items() if k in ks},refs)
  for r,parts in {
   '29-3':['kjv_elasah_shaphan son of kjv_shaphan','kjv_gemariah_hilkiah son of kjv_hilkiah_gemariah'],
   '29-4':['carry:caus:perf'],'29-6':['beget:imp','bear:may','diminish:psv:neg:may'],
   '29-7':['peace:a of city seek:imp','in its/peace you peace:a have:fu'],
   '29-8':['hear:neg:imp','dream:psv:caus:pr'],'29-10':['five+twelve and ten year:pl'],
   '29-11':['expect:psv:adj end:a'],'29-14':['captive:ev:a away turn:fu'],
   '29-15':['for wesg'],'29-19':['they to mypl/word:pl','but you hear:neg:pa'],
   '29-21':['kjv_ahab_kolaiah','kjv_zedekiah_maaseiah','kjv_nebuchadrezzar'],
   '29-23':['their/neighbour:pl/wife:pl','command:neg:perf','witness be:pr'],
   '29-26':['kjv_jehoiada_letter','mad be:pr','himself:a kjv_prophet make:pr','in prison and in stocks'],
   '29-28':['to wesg','captive:ev long be:pr'],'29-31':['send:neg:pa','trust:caus:perf'],
   '29-32':['his/seed:a punish:fu','good:a behold:neg:fu'],
   '30-5':['wesg voice:a','fear and not of peace'],
   '30-6':['whether man with child kjv_travail:pr?','ipl every man:a'],
   '30-7':['alas:excl'],'30-8':['his/yoke:a from off thy/neck','no more he:a for themselves serve:caus:fu'],
   '30-9':['kjv_david their/king:a'],'30-10':['kjv_dismay:psv:neg:imp'],
   '30-11':['full end:a of thee make:neg:fu','in measure kjv_chasten:fu','without punish:ev leave:neg:fu'],
   '30-12':['incurable'],'30-14':['with wound of enemy kjv_wound_inflict:perf'],
   '30-17':['health:a restore:fu'],'30-19':['kjv_multiply:caus:fu','few be:neg:fu','small be:neg:fu'],
   '30-21':['his/heart:a as pledge give:pa'],'30-22':['you mypl/people','ipl your/god'],
   '31-3':['to ipl appear:perf','ipl thee:a with eternal love love:perf'],
   '31-6':['wesg to kjv_zion to kjv_lord ourone/god up go:opt'],
   '31-9':['ipl father to kjv_israel','mypl/kjv_firstborn_human'],
   '31-12':['kjv_goodness_bounty','kjv_water_irrigate:psv:adj kjv_garden'],
   '31-15':['kjv_rahel','because they be:neg:pa'],
   '31-18':['ipl surely kjv_ephraim:a','thou ipl:a kjv_chasten:perf','mypl/god'],
   '31-19':['ipl turn:psv:pa ipl repent:pa','mypl/youth endure:pa'],
   '31-20':['mypl/kjv_bowels for he in kjv_trouble be:pr'],
   '31-21':['kjv_waymark:pl:a'],'31-22':['woman man:a surround:fu'],
   '31-26':['i awake:pa','my/sleep to i sweet be:pa'],
   '31-27':['seed of human and with seed of beast'],
   '31-29':['child:pl/tooth:pl kjv_teeth_on_edge:pr'],
   '31-30':['each for his/own kjv_iniquity','his/tooth:pl kjv_teeth_on_edge:fu'],
   '31-31':['with house of kjv_israel and with house of kjv_judah'],
   '31-32':['although ipl husband to they be:pa'],
   '31-33':['mypl/law:a in their/inside part:pl','in their/heart:pl write:fu'],
   '31-34':['no more each human','all ipl:a know:fu','no more remember:fu'],
   '31-35':['sea:a kjv_divide:pr'],'31-36':['if those kjv_ordinance:pl'],
   '31-37':['if heaven above measure:psv:can'],'31-39':['kjv_gareb_hill','kjv_goath'],
   '31-40':['dead body:pl','holy to kjv_lord','up pluck:psv:neg:fu','down throw:psv:neg:fu']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),17)
  self.assertEqual(lang.lexicon['kjv_rahel']['form'],lang.lexicon['kjv_rachel']['form'])
  self.assertEqual(lang.lexicon['kjv_goodness_bounty']['form'],lang.lexicon['goodness']['form'])
  self.assertNotEqual(lang.word('kjv_goodness_bounty')[1],lang.word('goodness')[1])
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
