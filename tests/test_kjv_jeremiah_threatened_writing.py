import unittest,re
from tools.kjv_archive import load_register,read

class JeremiahThreatenedWritingTests(unittest.TestCase):
 def test_household_voice_scroll_objects_and_named_pairs(self):
  prior,_=load_register('0.10-kjv.150');lang,manifest=load_register('0.10-kjv.151')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-household-voices-and-threatened-writing-cases.json')};self.assertEqual(len(cases),100)
  keys={}
  for r,c in cases.items():
   result=lang.compile(c['analysis']);keys[r]=set(result['keys'])
   self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','host','bow','dragon','snuff','ghost','desert','court','bond','count','administer','light','tear','right','leaf','page','roll','commit'}&keys[r])
  for k,refs in {'wesg':'35-6 35-8 35-9 35-10 35-11 36-16 36-17 37-3 37-9 38-4 38-16 38-25','ourone':'35-6 35-8 35-10 36-15 37-3','mypl':'35-13 35-15','wepl':'','iplself':'','you:du':'36-19','they:du':'36-26','we:du':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  self.assertEqual({r for r,ks in keys.items() if 'plead' in ks},{'36-25'})
  self.assertEqual({r for r,ks in keys.items() if 'former' in ks},{'36-28'})
  for r,parts in {
   '35-3':['kjv_jeremiah_habaziniah son of kjv_habaziniah'],
   '35-6':['wesg wine:a drink:neg:fu','ourone/father'],
   '35-8':['ourone/wife:pl ourone/son:pl nor ourone/daughter:pl'],
   '35-11':['army of kjv_syrian:pl','so wesg at kjv_jerusalem dwell:pr'],
   '35-19':['man:a before ipl forever stand:inf lack:neg:fu'],
   '36-2':['scroll:a of book','against all nation:pl'],
   '36-3':['perhaps','forgive:may'],'36-5':['i shut:psv:pr','go:neg:can'],
   '36-9':['five:ord year','nine:ord month'],
   '36-10':['higher kjv_court_enclosure','at enter:ev of new gate'],
   '36-16':['they each fear:pa','wesg surely king:a'],
   '36-18':['to i with his/mouth','with kjv_ink in book'],
   '36-19':['thou and kjv_jeremiah_prophet','where you:du be:pr'],
   '36-23':['three or four kjv_scroll_leaf:pl:a','with kjv_penknife','until all scroll'],
   '36-24':['fear:neg:pa','rend:neg:pa'],
   '36-26':['kjv_lord they:du:a hide:pa'],
   '36-28':['all former word:pl:a','first scroll'],
   '36-29':['say:cv why thou in it write:perf say:cv'],
   '36-32':['all word:pl:a of book','besides many like word:pl','add:psv:pa'],
   '37-3':['ourone/god for wesg pray:imp'],
   '37-9':['from wesg depart:fu','depart:neg:fu'],
   '37-10':['only kjv_wound_inflict:psv:adj man:pl','up rise:should'],
   '37-12':['himself:a from there in middle of people separate:inf'],
   '37-14':['i to kjv_chaldean:pl away fall:neg:pr'],
   '37-20':['return:caus:neg:may','lest i there die:pr'],
   '37-21':['street of bake:ag:pl','until all bread in city spend:psv:pa'],
   '38-4':['wesg thee:a beseech:pr','weak:caus:pr'],
   '38-6':['water be:neg:pa but mud'],
   '38-10':['two+twelve and six man:pl:a'],
   '38-12':['under kjv_hollow:pl of thy/arm:pl under kjv_cord:pl'],
   '38-15':['put:neg:fu?','listen:neg:fu?'],
   '38-16':['who for wesg this soul:a make:pa','i thee:a to death put:neg:fu','give:neg:fu'],
   '38-17':['burn:psv:neg:fu'],'38-18':['escape:neg:fu'],
   '38-22':['thy/friend:pl thee:a urge:perf','thy/foot:pl in mud sink:perf'],
   '38-23':['burn:psv:caus:fu'],
   '38-25':['i with thee speak:perf','from wesg hide:neg:imp'],
   '38-26':['i my/kjv_supplication:a before king set:pa'],
   '38-27':['matter perceive:psv:neg:pa']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),44)
  self.assertEqual(cases['38-28']['analysis'].count('when kjv_jerusalem take:psv:pa'),2)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
