import unittest
from tools.kjv_archive import load_register,read
class JobHearingMortalityTests(unittest.TestCase):
 def test_disputing_pair_generation_and_unharmonized_hope(self):
  prior,_=load_register('0.10-kjv.102');lang,manifest=load_register('0.10-kjv.103')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'job-hearing-mortality-cases.json')};self.assertEqual(len(cases),174)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','matter','right','please','consume','one','hell','fashion','wear','plant','longer','spoil'} & set(out['keys']))
  def a(r):return cases['job-'+r]['analysis']
  for r,parts in {
   '8-4':['if thy/child:pl'], '8-9':['wesg','ourone/day:pl'],
   '8-11':['kjv_rush_plant','kjv_flag_plant'], '8-18':['i thee:a see:neg:perf'],
   '8-20':['blameless man:a away cast:neg:fu'],
   '9-3':['one_num of thousand'], '9-9':['kjv_arcturus kjv_orion and kjv_pleiades'],
   '9-16':['answer:pp','believe:neg:should'], '9-17':['without reason'],
   '9-22':['blameless and wicked:a destroy:pr'], '9-25':['kjv_post_runner'],
   '9-32':['we:du together in judgment'], '9-33':['kjv_daysman between we:du','upon we:du both'],
   '10-5':['thy/year:pl as person:poss day:pl'], '10-8':['shape:perf'],
   '10-10':['as milk','like cheese'], '10-14':['if i sin:pr','observe:pr'],
   '10-18':['release:pp:opt:excl'], '10-22':['light as darkness'],
   '11-4':['thou say:perf','i in thy/eye:pl'], '11-6':['double','less than thy/kjv_iniquity'],
   '11-8':['kjv_hell_depth'], '11-9':['in length','in broad:ev'],
   '11-18':['about thee kjv_dig:fu'], '12-2':['wisdom with you:pl die:fu'],
   '12-6':['tent:pl of rob:ag:pl prosper:pr'], '12-10':['breath of all person:pl'],
   '12-16':['deceive:psv:pp person and kjv_deceiver'], '12-19':['strip:psv:cv'],
   '12-23':['large make:pr','narrow make:pr'], '13-5':['silent be:opt:excl'],
   '13-7':['for god wicked:adv'], '13-8':['his/face:a accept:fu'],
   '13-10':['face:pl:a accept:pr'], '13-12':['your/remember:ev:pl','your/body:pl'],
   '13-15':['i in he trust:fu','my/own way:pl:a before he support:fu'],
   '13-18':['kjv_case_plea:a arrange:perf'], '13-20':['two thing:pl'],
   '13-22':['or i speak:opt'], '13-27':['kjv_stocks_feet','mark:a upon heel:pl'],
   '13-28':['and he as rotten thing'], '14-4':['not one_num'],
   '14-9':['kjv_plant_growth'], '14-12':['until heaven:pl no more'],
   '14-13':['hide:opt:excl'], '14-14':['he again live:fu?','my/change:ev'],
   '14-17':['in bag up seal:psv:pr','kjv_sew:pr'], '14-19':['kjv_erode:pr'],
   '14-21':['know:neg:pr','perceive:neg:pr'], '14-22':['pain:a have:fu','mourn:fu'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),14)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-102')
if __name__=='__main__':unittest.main()
