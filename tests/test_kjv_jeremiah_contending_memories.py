import unittest,re
from tools.kjv_archive import load_register,read

class JeremiahContendingMemoriesTests(unittest.TestCase):
 def test_opposed_causal_memories_and_different_plural_selves(self):
  prior,_=load_register('0.10-kjv.152');lang,manifest=load_register('0.10-kjv.153')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-contending-memories-and-civic-boast-cases.json')};self.assertEqual(len(cases),70)
  for r,c in cases.items():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','host','bow','dragon','snuff','ghost','desert','court','bond','count','administer','light','tear','right','leaf','page','roll','commit','plead','former','handle'}&set(result['keys']))
  for k,refs in {'i':'45-3','wesg':'44-16 44-17 44-18 44-19 44-25 46-16','ourone':'44-17 44-19 44-25 46-16','mypl':'44-4 44-6 44-10 44-11 44-26 44-28 44-29 46-27 46-28','they:du':'46-12','wepl':'','iplself':'','we:du':'','you:du':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in {
   '44-17':['queen of heaven','ourone/'],
   '44-18':['since','wesg'],
   '44-19':['ourone/man:pl'],
   '44-22':['endure'],
   '44-25':['wesg'],
   '44-28':['mypl/word:pl','their/word:pl'],
   '45-1':['four:ord year'],
   '45-3':['i',':excl'],
   '46-2':['kjv_pharaohnecho','four:ord year'],
   '46-4':['kjv_furbish:imp','kjv_brigandine:pl:a'],
   '46-8':['egypt','he say:pr ipl up go:fu'],
   '46-9':['kjv_shield_armour:a hold:pr','kjv_bow:a hold:pr and bend:pr'],
   '46-10':['with their/blood drunk make:psv:fu'],
   '46-12':['they:du together fall:perf'],
   '46-16':['each upon other','wesg again to ourone/own people'],
   '46-20':['destroy:ev come:pr'],
   '46-22':['its/voice like serpent'],
   '46-25':['kjv_multitude:a of kjv_no_egypt'],
   '46-26':['afterward it inhabit:psv:fu'],
   '46-28':['full end:a of thee make:neg:fu','without punish:ev leave:neg:fu'],
   '47-6':['sword','thou'],
   '47-7':['it']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),7)
  self.assertEqual(lang.lexicon['kjv_brigandine']['form'],lang.lexicon['kjv_mail_coat']['form'])
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
