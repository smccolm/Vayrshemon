import unittest,re
from tools.kjv_archive import load_register,read

class JeremiahDeedsLibertyTests(unittest.TestCase):
 def test_deeds_conditional_promises_and_revoked_liberty(self):
  prior,_=load_register('0.10-kjv.149');lang,manifest=load_register('0.10-kjv.150')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-deeds-and-revoked-liberty-cases.json')};self.assertEqual(len(cases),92)
  keys={}
  for r,c in cases.items():
   result=lang.compile(c['analysis']);keys[r]=set(result['keys'])
   self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','host','bow','dragon','snuff','ghost','desert','court','bond','plead','count','administer','light','tear'}&keys[r]);self.assertNotIn(':du',c['analysis'])
  for k,refs in {'i':'32-6 32-8 32-9 32-10 32-11 32-12 32-13 32-16 32-25','wesg':'','ourone':'33-16','wepl':'','iplself':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  self.assertEqual({r for r,ks in keys.items() if 'right' in ks},{'32-7','32-8'})
  self.assertEqual({r for r,ks in keys.items() if 'former' in ks},{'34-5'})
  for r,parts in {
   '32-1':['ten:ord year','twelve and six:ord year'],
   '32-7':['right of redeem:ev'],'32-9':['twelve and five kjv_shekel:pl of silver'],
   '32-10':['my/name:a on kjv_purchase_deed write:pa','seal:pa','in balance:pl weigh:pa'],
   '32-12':['kjv_baruch_neriah son of kjv_neriah_baruch son of kjv_maaseiah_neriah'],
   '32-14':['which seal:psv:pr','which open be:pr','earth:adj vessel'],
   '32-18':['thousand:pl','into bosom of their/child:pl'],
   '32-23':['obey:neg:pa','walk:neg:pa','nothing:a'],
   '32-35':['command:neg:pa','mypl/mind come:neg:pa'],
   '32-39':['one_num heart:a and one_num way:a'],
   '32-41':['mypl/whole heart','mypl/whole soul'],
   '33-12':['their/flock:pl:a down lie:caus:pr'],
   '33-13':['under hand:pl of he who they:a kjv_number:pr'],
   '33-15':['judgment:a and kjv_righteousness:a in land do:fu'],
   '33-16':['she call:psv:fu','kjv_lord ourone/kjv_righteousness'],
   '33-18':['man:a lack:neg:fu','kjv_meat_offering:pl:a kjv_kindle_fire:inf'],
   '33-20':['if you mypl/kjv_covenant:a of day','mypl/kjv_covenant:a of night'],
   '33-22':['army of heaven kjv_number:psv:neg:can'],
   '33-24':['two kjv_family:pl'],'33-25':['if ipl','appoint:neg:perf'],
   '34-4':['by sword die:neg:fu'],'34-5':['in peace die:fu','odour:pl:a for thee burn:fu'],
   '34-9':['kjv_hebrew man or kjv_hebrew woman','none they:a for himself serve:caus:should'],
   '34-11':['whom they free go:inf allow:pp return:caus:pa','into kjv_bondservice'],
   '34-14':['end of seven year:pl','six year:pl serve:perf'],
   '34-16':['at their/pleasure free set:pp','into kjv_bondservice'],
   '34-17':['ipl for you free:ev:a proclaim:pr','to sword to kjv_pestilence and to kjv_famine'],
   '34-18':['kjv_calf:a in two cut:pa'],'34-20':['dead body:pl food for bird:pl'],
   '34-22':['they:a to this city return:caus:fu']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),6)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
