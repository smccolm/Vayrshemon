import unittest
from tools.kjv_archive import load_register,read
class JobHiddenWisdomTests(unittest.TestCase):
 def test_hidden_hearing_social_senses_and_personified_pair(self):
  prior,_=load_register('0.10-kjv.104');lang,manifest=load_register('0.10-kjv.105')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'job-hidden-wisdom-cases.json')};self.assertEqual(len(cases),143)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','matter','right','consume','one','fine'} & set(out['keys']))
  def a(r):return cases['job-'+r]['analysis']
  for r,parts in {
   '22-4':['for fear of thee'], '22-9':['widow:pl:a empty','kjv_fatherless'],
   '22-13':['thou say:pr'], '22-17':['from wesg depart','for they do'],
   '22-18':['far from i'], '22-20':['ourone/substance'], '22-22':['receive:imp please'],
   '22-24':['gold:a as dust'], '22-25':['thy/defence','abundance of silver'],
   '22-30':['kjv_isle of innocent'], '23-2':['my/strike:ev'], '23-4':['kjv_case_plea:a before he arrange'],
   '23-6':['no but','strength:a in i'], '23-9':['kjv_right_side'], '23-10':['test:perf'],
   '23-12':['my/necessary food'], '23-13':['one_num mind'], '23-17':['off cut:psv:neg','neither he darkness'],
   '24-1':['hide:psv:neg','see:neg:pr'], '24-2':['kjv_landmark'], '24-6':['every person his/corn'],
   '24-9':['from breast'], '24-12':['god folly:a to they lay:neg'],
   '24-15':['no eye i:a see'], '24-16':['in day mark:pa'], '24-19':['snow water:pl'],
   '24-24':['kjv_grain_ear'], '25-4':['of woman bear'],
   '26-5':['dead thing:pl','form:psv:pr'], '26-6':['kjv_hell_depth'],
   '26-9':['face of his/throne'], '26-10':['until day and night to end'],
   '26-12':['proud:a through strike'], '26-13':['crooked serpent'],
   '27-1':['kjv_parable_oracle'], '27-2':['my/judgment:a away take'],
   '27-3':['my/breath in i','spirit of god in my/kjv_nostril:pl'],
   '27-5':['my/integrity'], '27-15':['in death bury','his/widow:pl'],
   '27-19':['gather:psv:neg'], '27-22':['willingly'],
   '28-1':['kjv_mineral_vein','kjv_fine_metal'], '28-4':['flood from inhabit:ag','by foot forget','up dry:psv:pr'],
   '28-13':['its/price'], '28-14':['it in i','it with i'],
   '28-18':['kjv_coral'], '28-22':['destroy:ev and death','we:du','ear:pl of we:du'],
   '28-27':['see:pa','declare:pa','prepare:pa','search:pa'], '28-28':['fear of kjv_lord'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),3)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-104')
if __name__=='__main__':unittest.main()
