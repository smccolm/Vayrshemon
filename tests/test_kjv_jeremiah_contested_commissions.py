import unittest,re
from tools.kjv_archive import load_register,read

class JeremiahContestedCommissionsTests(unittest.TestCase):
 def test_claimed_divine_voice_optative_and_material_senses(self):
  prior,_=load_register('0.10-kjv.147');lang,manifest=load_register('0.10-kjv.148')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-contested-commissions-and-embodied-yokes-cases.json')};self.assertEqual(len(cases),101)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','host','bow','former','dragon','snuff','ghost','desert','right','court','bond','plead'}&set(result['keys']))
   self.assertNotIn(':du',c['analysis'])
  for k,refs in {'i':'25-3 25-15 25-17 26-12 26-14 26-15 27-2 27-12 27-16 28-1 28-7 28-8','wesg':'26-16 26-19','ourone':'26-16 26-19','wepl':'','iplself':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in {
   '25-1':['four:ord year','first year','kjv_nebuchadrezzar'],
   '25-3':['twelve and one_num:ord','twelve and eleven:ord','i to you speak:perf'],
   '25-6':['kjv_provoke:neg:imp','no hurt'],
   '25-9':['mypl/servant'],'25-10':['light:a of candle'],
   '25-11':['five+twelve and ten year:pl'],'25-12':['five+twelve and ten year:pl'],
   '25-14':['they:a also for themselves serve:caus:fu'],
   '25-15':['to i say:pr','mypl/hand','drink:caus:imp'],
   '25-23':['kjv_dedan_people','kjv_tema_people','kjv_buz_people'],
   '25-25':['kjv_zimri_region'],'25-26':['kjv_sheshach after they'],
   '25-29':['punish:psv:neg:should?','without punish:ev be:neg:fu'],
   '25-31':['kjv_litigate:ev:a','with all flesh kjv_litigate:fu'],
   '25-33':['lament:psv:neg:fu','gather:psv:neg:fu','bury:psv:neg:fu'],
   '25-34':['principal human:pl'],'25-38':['his/kjv_den_shelter:a'],
   '26-2':['kjv_court_enclosure','diminish:neg:imp'],
   '26-3':['ipl of evil repent:may'],'26-13':['kjv_lord of evil repent:fu'],
   '26-16':['worthy be:neg:pr','to wesg','ourone/god'],
   '26-18':['kjv_micah_morasthite kjv_morasthite','kjv_heap:pl'],
   '26-19':['wesg great evil:a against ourone/soul:pl'],
   '26-23':['with sword slay:pa'],'26-24':['give:neg:should'],
   '27-1':['kjv_jehoiakim'],'27-3':['kjv_zedekiah_king'],
   '27-2':['kjv_binding_restraint:pl:a','upon thy/neck'],
   '27-5':['mypl/great power','mypl/out stretch:psv:adj arm'],
   '27-6':['nebuchadnezzar','mypl/servant','beast:pl:a'],
   '27-7':['his/son/son:a','he:a for themselves serve:caus:fu'],
   '27-9':['your/kjv_divine:ag:pl:a','your/enchant:ag:pl:a'],
   '27-11':['it:a kjv_till_land:fu'],'27-15':['send:neg:perf','mypl/name'],
   '27-18':['go:neg:opt'],'27-19':['kjv_sea_basin'],
   '27-20':['take:neg:pa','kjv_jeconiah:a'],'27-22':['to this place restore:fu'],
   '28-1':['four:ord year','five:ord month','kjv_hananiah_azur son of kjv_azur_hananiah'],
   '28-2':['ipl yoke:a','break:perf'],'28-3':['two full year:pl'],
   '28-6':['amen','so do:opt','thy/word:pl:a perform:opt'],
   '28-9':['when word of kjv_prophet come:fu to be','truly he:a send:perf'],
   '28-11':['ipl yoke:a','two full year:pl','kjv_jeremiah_prophet his/way go:pa'],
   '28-13':['thou yoke:pl:a of wood break:perf','thou for they yoke:pl:a of iron make:fu'],
   '28-14':['ipl yoke:a of iron','they he:a serve:fu'],
   '28-15':['send:neg:perf','trust:caus:pr'],'28-16':['this year thou die:fu'],
   '28-17':['seven:ord month die:pa']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),17)
  self.assertEqual(lang.lexicon['kjv_sea_basin']['form'],lang.lexicon['sea']['form'])
  self.assertNotEqual(lang.word('kjv_litigate:fu')[0],lang.word('plead:fu')[0])
  self.assertNotEqual(lang.word('kjv_binding_restraint:pl')[0],lang.word('bond:pl')[0])
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
