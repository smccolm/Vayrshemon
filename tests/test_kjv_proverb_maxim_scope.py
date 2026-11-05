import unittest
from tools.kjv_archive import load_register,read
class ProverbMaximScopeTests(unittest.TestCase):
 def test_source_repetition_scope_and_contextual_senses(self):
  prior,_=load_register('0.10-kjv.122');lang,manifest=load_register('0.10-kjv.123')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id']:c for c in read(lang.folder/'proverbs-maxims-scope-and-historical-senses-cases.json')};self.assertEqual(len(cases),126)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'just','want','sound','hell','simple','right','plain','disposition','late','revenue'}&set(out['keys']))
   self.assertNotRegex(c['analysis'],r'(?<![a-z_])(?:i|ipl|mypl|iplself|wesg|wepl)(?![a-z_])')
  for ref,parts in {
   '13-4':['desire:pr and nothing:a have:pr','fat:caus:psv:fu'],
   '13-7':['rich:caus:pr yet nothing','poor:caus:pr yet great rich:ev'],
   '13-8':['poor rebuke:ev:a hear:neg:pr'],'13-22':['his/child:pl/child:pl'],
   '13-23':['lack of judgment'],'13-24':['early kjv_chastise:pr'],'13-25':['belly of wicked lack:fu'],
   '14-4':['kjv_crib clean'],'14-9':['fool:pl at sin mock:pr'],'14-10':['stranger in his/joy join:neg:pr'],
   '14-14':['in heart back turn:pr','from himself satisfy:psv:fu'],
   '14-20':['poor even by his/own neighbour hate:psv:pr'],'14-21':['neighbour:a despise:pr sin:pr'],
   '14-22':['err:neg:pr?'],'14-24':['foolish:ev of fool:pl folly'],
   '14-26':['his/child:pl place of kjv_refuge'],'14-30':['health:adj heart','kjv_envy'],
   '14-32':['hope:a in his/death'],'15-1':['pain:caus:adj word:pl'],
   '15-3':['eye:pl of kjv_lord in every place'],'15-6':['kjv_income of wicked'],
   '15-11':['kjv_hell and destroy:ev'],'15-17':['stall:psv:adj ox and hate:ev'],
   '15-19':['clear:caus:psv:pr'],'15-22':['purpose:pl fail:pr'],
   '15-23':['be:pr:excl'],'15-25':['boundary of widow'],
   '15-27':['gift:pl:a hate:pr'],'15-29':['kjv_lord far from wicked'],
   '15-30':['bone:pl:a fat:caus:pr'],'16-1':['heart in human and answer of tongue from kjv_lord'],
   '16-3':['entrust:imp'],'16-4':['even wicked for day of evil'],
   '16-5':['punish:psv:neg:adj remain:neg:fu'],'16-8':['kjv_income without kjv_uprightness'],
   '16-10':['divine sentence','judgment transgress:neg:pr'],'16-11':['true weight'],
   '16-15':['kjv_latter_rain'],'16-16':['gold be:pr:excl','silver be:pr:excl'],
   '16-19':['spoil:a with proud kjv_divide:inf'],'16-20':['matter:a wise:adv deal:pr'],
   '16-26':['mouth it:a from he demand:pr'],'16-31':['grey head','if it in way of kjv_righteousness'],
   '16-33':['kjv_lot into lap','whole decide:ev of it'],
  }.items():
   for p in parts:self.assertIn(p,cases['proverbs-'+ref]['analysis'],(ref,p))
  self.assertEqual(cases['proverbs-14-12']['analysis'],cases['proverbs-16-25']['analysis'])
  with self.assertRaisesRegex(ValueError,'DUPLICATE_FEATURE'):lang.compile('wicked punish:psv:neg:neg:fu.')
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_income'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
