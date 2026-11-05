import unittest,re
from tools.kjv_archive import load_register,read

class EzekielNestedSpeakersTests(unittest.TestCase):
 def test_nested_claims_and_unharmonized_vision(self):
  prior,_=load_register('0.10-kjv.157');lang,manifest=load_register('0.10-kjv.158')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('ezekiel-'):c for c in read(lang.folder/'ezekiel-nested-speakers-and-disputed-delay-cases.json')};self.assertEqual(len(cases),104)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text']);self.assertNotIn(':du',c['analysis'])
   self.assertFalse({'one','host','bow','ghost','roll','fold','care','plain','right','tear','border','stuff','lock','light','divine'}&set(r['keys']))
   for k in ('wepl','ourone','iplself'):self.assertIsNone(re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis']))
  for r,parts in {
   '8-1':['six:ord year','six:ord month','five:ord day'],
   '8-2':['likeness as appear:ev of fire'],
   '8-3':['kjv_hair_lock','in vision:pl of god'],
   '8-6':['ipl far off from mypl/kjv_sanctuary go:should?'],
   '8-11':['five+twelve and ten man:pl','kjv_jaazaniah_shaphan'],
   '8-12':['kjv_lord wesg:a see:neg:pr'],
   '8-14':['woman:pl for kjv_tammuz weep:cv'],
   '8-16':['about twenty and five man:pl','their/back:pl towards temple','sun:a towards east kjv_worship:pa'],
   '8-17':['lightweight thing','branch:a to their/nose'],
   '8-18':['mypl/eye spare:neg:fu','hear:neg:fu'],
   '9-2':['six man:pl','one_num man among they','kjv_inkhorn'],
   '9-3':['from kjv_cherub','kjv_threshold'],
   '9-4':['mark:a upon forehead:pl','who sigh:pr'],
   '9-6':['little child:pl and woman:pl:a','come:neg:imp','mypl/kjv_sanctuary begin:imp'],
   '9-7':['house:a defile:imp'],
   '9-8':['i leave:psv:pa','ah lord god:excl'],
   '9-9':['kjv_lord see:neg:pr'],
   '9-10':['as for ipl'],
   '9-11':['i as thou i:a command:perf do:perf'],
   '10-7':['one_num kjv_cherub'],
   '10-9':['four wheel:pl','one_num wheel by one_num kjv_cherub'],
   '10-12':['their/whole body','their/back:pl','their/hand:pl','their/wing:pl','full of eye:pl'],
   '10-14':['first face face of kjv_cherub','second face face of man','third face of lion','fourth face of kjv_eagle'],
   '10-15':['this living creature'],
   '10-17':['these themselves:a','spirit of living creature'],
   '10-22':['same face:pl'],
   '11-1':['twenty and five man:pl','kjv_jaazaniah_azur','kjv_pelatiah_benaiah'],
   '11-3':['wesg house:pl:a build:opt','wesg flesh'],
   '11-7':['your/slay:psv:adj:pl','they flesh be:pr'],
   '11-11':['your/kjv_caldron be:neg:fu','neither you flesh','boundary'],
   '11-12':['mypl/kjv_statute:pl walk:neg:perf'],
   '11-13':['when i kjv_prophesy:pa','kjv_pelatiah_benaiah'],
   '11-15':['thy/brother:pl even thy/brother:pl','to wesg this land'],
   '11-16':['as little kjv_sanctuary'],
   '11-19':['they:a one_num heart:a','new spirit:a within you','stone:adj heart:a','heart:a of flesh'],
   '11-20':['they mypl/people','ipl their/god'],
   '11-23':['mountain which on east side'],
   '11-24':['in vision by spirit of god','kjv_chaldea'],
   '12-3':['kjv_baggage:a for move:ev','it be:may they consider:fu'],
   '12-6':['thy/kjv_shoulder:pl'],
   '12-7':['with my/hand kjv_dig:pa','my/kjv_shoulder in their/sight'],
   '12-10':['kjv_burden_oracle','prince:a in kjv_jerusalem'],
   '12-11':['say:imp i your/sign be:pr','as i do:perf'],
   '12-13':['it:a see:neg:fu though he there die:fu'],
   '12-14':['his/band:pl:a'],
   '12-16':['few man:pl:a'],
   '12-18':['with tremble:ev and with worry'],
   '12-22':['day:pl delay:psv:pr','every vision fail:pr?'],
   '12-25':['in your/day:pl','more delay:psv:neg:fu'],
   '12-27':['many day:pl','far off'],
   '12-28':['none of mypl/word:pl','delay:psv:fu']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertNotIn('wesg',cases['9-9']['analysis'])
  self.assertNotIn('about',cases['11-1']['analysis'])
  self.assertNotIn('kjv_jaazaniah_shaphan',cases['11-1']['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),8)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
