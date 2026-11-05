import unittest,re
from tools.kjv_archive import load_register,read
class IsaiahCivicSelvesTests(unittest.TestCase):
 def test_civic_divine_personal_and_failed_birth(self):
  prior,_=load_register('0.10-kjv.132');lang,manifest=load_register('0.10-kjv.133')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('isaiah-'):c for c in read(lang.folder/'isaiah-civic-selves-and-failed-birth-cases.json')};self.assertEqual(len(cases),122)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','ward','issue','prevent','host','count'}&set(result['keys']))
  expected={
   'i':'21-2 21-3 21-4 21-6 21-8 21-10 21-11 21-16 22-4 24-16 26-9',
   'ipl':'21-2 22-19 22-20 22-21 22-22 22-23 23-4 25-1',
   'mypl':'20-3 22-20 25-1',
   'wesg':'20-6 22-13 24-16 25-9 26-1 26-8 26-12 26-13 26-17 26-18',
   'ourone':'20-6 25-9 26-8 26-12 26-13'}
  for k,refs in expected.items():self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  self.assertEqual({r for r,c in cases.items() if ':du' in c['analysis']},{'21-7','21-9'})
  for r in('21-7','21-9'):self.assertIn('kjv_horseman:du',cases[r]['analysis'])
  for r,parts in {
   '20-2':['bare and with bare foot:pl'],'20-3':['mypl/servant','three year:pl'],
   '20-4':['young and old','buttock:pl kjv_uncover:psv:adj'],
   '21-2':['to i declare:psv:pr','ipl cease:caus:perf'],'21-8':['lion:excl','my/watch:ev place'],
   '21-14':['beforehand meet:pa'],'21-16':['one_num year'],
   '22-2':['slay:psv:pr not','nor in battle dead'],'22-4':['my/people','labour:neg:imp'],
   '22-8':['kjv_uncover:pa'],'22-10':['kjv_number:perf'],'22-11':['two wall:pl'],
   '22-13':['wesg eat:opt and drink:opt','tomorrow wesg die:fu'],
   '22-14':['purge:psv:neg:fu until you die:pr'],
   '22-17':['surely thee:a cover:fu'],'22-19':['ipl','thy/office','thy/rank he'],
   '22-22':['none shut:fu','none open:fu'],'22-24':['offspring:a and descendant:pl:a'],
   '22-25':['sure place','remove:psv:fu'],
   '23-3':['market of nation:pl'],'23-4':['sea speak:perf','ipl kjv_travail:neg:pr'],
   '23-8':['trade:ag:pl'],'23-13':['be:pa not until','kjv_establish:pa'],
   '23-15':['seven+ten year:pl','one_num king'],'23-17':['kjv_whoredom:a do:fu'],
   '23-18':['holy:ev to kjv_lord','endure:adj clothing'],
   '24-2':['maid','mistress','buy:ag','sell:ag','lend:ag','borrow:ag','kjv_usury'],
   '24-15':['in fire:pl'],'24-16':['wesg song:pl:a','but i say:pa'],
   '24-19':['completely dissolve:psv:pr'],'24-20':['again rise:neg:fu'],
   '24-21':['army:a of high:pl'],'24-22':['visit:psv:fu'],
   '25-1':['thou mypl/god','ipl thee:a'],'25-5':['branch of terrible:pl'],
   '25-6':['all people','kjv_wine_lees','marrow'],
   '25-8':['kjv_swallow:fu','all face:pl','kjv_reproach:a'],
   '25-10':['kjv_moab','kjv_dung'],
   '26-3':['mind upon thee support:psv:pr'],'26-9':['my/soul i','my/spirit'],
   '26-12':['ourone/work:pl:a in wesg'],'26-14':['live:neg:fu','rise:neg:fu'],
   '26-18':['wind:a forth bring:perf','neither inhabit:ag:pl of world fall:perf'],
   '26-19':['thy/dead human:pl live:fu','my/kjv_corpse'],
   '26-20':['my/people:excl'],'26-21':['her/blood:a disclose:fu']
  }.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  for r,phrase in {'21-9':'fall:perf','21-11':'watch:ag:excl what of night?','24-16':'my/thin:ev','25-9':'wesg for he wait:perf','26-5':'low lay:pr','26-15':'thou nation:a increase:perf'}.items():self.assertEqual(cases[r]['analysis'].count(phrase),2)
  added=set(lang.lexicon)-set(prior.lexicon);self.assertEqual(added,{'kjv_wine_lees','kjv_sargon','kjv_dedanim'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
