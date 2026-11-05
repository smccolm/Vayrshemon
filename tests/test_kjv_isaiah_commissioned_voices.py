import unittest,re
from tools.kjv_archive import load_register,read
class IsaiahCommissionedVoicesTests(unittest.TestCase):
 def test_voices_reflexives_and_material_senses(self):
  prior,_=load_register('0.10-kjv.139');lang,manifest=load_register('0.10-kjv.140')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('isaiah-'):c for c in read(lang.folder/'isaiah-communal-confessions-and-commissioned-voices-cases.json')};self.assertEqual(len(cases),101)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','dumb','count','host','quarter','kjv_breastplate','kjv_ephah_measure','kjv_ephah','kjv_nebaioth'}&set(result['keys']))
   self.assertNotIn(':du',c['analysis'])
  expected={'i':'56-3 56-12','iplself':'57-17','wesg':'56-12 58-3 59-9 59-10 59-11 59-12','wepl':'','ourone':'56-12 58-3 59-12 59-13 61-2 61-6'}
  for k,refs in expected.items():self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in{
   '56-3':['i dry kjv_tree be:pr'],'56-5':['name:a better than of son:pl and of daughter:pl'],
   '56-7':['for all people'],'56-10':['kjv_mute dog:pl','bark:neg:can'],
   '56-11':['each for his/gain from his/region'],
   '56-12':['i wine:a fetch:fu','wesg ourone/self:a','kjv_strong_drink'],
   '57-5':['under split:ev:pl of rock:pl kill:cv'],
   '57-6':['they they thy/kjv_lot','corn kjv_offering'],
   '57-8':['other than ipl kjv_uncover:perf'],
   '57-9':['to king with kjv_ointment','kjv_hell_depth'],
   '57-10':['life:a of thy/hand'],
   '57-11':['thou kjv_lie_false:perf'],
   '57-17':['ipl iplself:a hide:pa','he in way of his/heart'],
   '57-19':['peace peace'],'57-21':['my/god'],
   '58-3':['wesg ourone/soul:a','all your/labour:pl:a exact:pr'],
   '58-6':['every yoke:a break:pr'],'58-8':['health quickly forth rise:fu'],
   '58-9':['here ipl be:pr'],'58-11':['spring of water'],
   '59-1':['his/ear heavy be:neg:pr'],'59-5':['kjv_cockatrice','kjv_viper'],
   '59-10':['wesg no eye:pl:a have:pa'],'59-11':['wesg all like bear_animal:pl'],
   '59-13':['against kjv_lord kjv_lie_false:cv'],
   '59-17':['kjv_breastplate_armour','kjv_cloak'],
   '59-19':['spirit of kjv_lord kjv_standard_banner:a against he'],
   '59-21':['mypl/spirit which upon thee','thy/kjv_seedline/kjv_seedline'],
   '60-6':['kjv_ephah_people'],'60-7':['kjv_nebaioth_people'],
   '60-9':['kjv_tarshish first'],'60-12':['serve:neg:fu perish:fu'],
   '60-13':['kjv_box_tree'],'60-16':['breast:a of king:pl suck:fu'],
   '60-19':['sun no more thy/light'],'60-20':['thy/sun no more down go:fu'],
   '60-22':['little human thousand become:fu','in his/time'],
   '61-1':['spirit of lord god upon ipl','he ipl:a send:perf'],
   '61-2':['day:a of kjv_avenge:ev of ourone/god'],
   '61-5':['your/kjv_vinedresser:pl'],
   '61-7':['you double:a have:fu','they double:a possess:fu'],
   '61-8':['ipl kjv_lord judgment:a love:pr','rob:ev:a for burn:psv:adj kjv_offering hate:pr'],
   '61-10':['ipl greatly in kjv_lord rejoice:fu','mypl/god','bride herself:a'],
   '61-11':['forth sprout:caus:pr']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_breastplate_armour','kjv_cloak','kjv_ephah_people','kjv_nebaioth_people'})
  self.assertNotIn('mypl/',cases['57-21']['analysis'])
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
