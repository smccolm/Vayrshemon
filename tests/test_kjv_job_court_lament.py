import unittest
from tools.kjv_archive import load_register,read
class JobCourtLamentTests(unittest.TestCase):
 def test_distinct_voices_hard_images_and_bodily_senses(self):
  prior,_=load_register('0.10-kjv.101');lang,manifest=load_register('0.10-kjv.102')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'job-court-lament-cases.json')};self.assertEqual(len(cases),160)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','matter','right','please','consume','one'} & set(out['keys']))
  def a(r):return cases['job-'+r]['analysis']
  for r,parts in {
   '1-2':['seven son:pl and kjv_three daughter:pl'],
   '1-3':['seven+thousand sheep:pl','kjv_three+thousand kjv_camel:pl','five+hundred yoke:pl','five+hundred female ass:pl'],
   '1-8':['mypl/servant','blameless'], '1-12':['only upon himself','put:neg:imp'],
   '1-15':['i only alone escape:perf'], '1-16':['fire of god','i only alone escape:perf'],
   '1-17':['kjv_three band:pl','i only alone escape:perf'], '1-19':['four corner:pl','i only alone escape:perf'],
   '1-21':['kjv_nakedness:adj i','to there return:fu'],
   '2-3':['thou ipl:a against he','without reason destroy:inf'],
   '2-7':['kjv_boil_lesion:pl','kjv_sole','top of his/head'],
   '2-9':['god:a curse:imp and die:imp'], '2-10':['wesg good:a','wesg evil:a','with his/lip:pl'],
   '2-13':['seven day:pl and seven night:pl','none word:a'],
   '3-3':['day perish:opt'], '3-8':['their/mourn:ev:a'], '3-11':['breath:a release:neg:pa'],
   '3-12':['knee:pl i:a meet:pa'], '3-16':['kjv_untimely_birth'],
   '3-24':['before i eat:pr'], '3-26':['in safety be:neg:pa','neither i rest:a','neither i quiet'],
   '4-2':['if wesg','who himself:a'], '4-12':['my/ear little of it:a'],
   '4-15':['spirit before my/face'], '4-16':['perceive:neg:pa:can'],
   '4-17':['more kjv_righteous than god'], '4-19':['before kjv_moth_job'],
   '5-3':['i his/dwell:ev:a curse:pa'], '5-8':['my/kjv_case_plea:a'],
   '5-19':['six distress:pl','in seven no evil'], '5-23':['kjv_covenant with stone:pl'],
   '5-24':['sin:neg:fu'], '5-26':['kjv_grain_shock'], '5-27':['wesg it:a search:perf'],
   '6-2':['lay:psv:opt:excl'], '6-3':['word:pl kjv_swallow:psv:pr'],
   '6-5':['kjv_bray:pr','kjv_low_cattle:pr'], '6-10':['kjv_holy_one'],
   '6-14':['but he fear of kjv_almighty:a forsake:pr'],
   '6-25':['kjv_right_speech'], '6-27':['kjv_fatherless'], '6-28':['kjv_lie_false:pr'],
   '7-1':['kjv_hireling_job'], '7-4':['down lie:pr'], '7-6':['kjv_shuttle_weaving'],
   '7-9':['no more up come:fu'], '7-12':['i sea or whale'],
   '7-15':['kjv_strangling_lament'], '7-20':['i sin:perf','preserve:ag:excl'],
   '7-21':['pardon:neg:pr','take:neg:pr','i be:neg:fu'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),21)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-101')
if __name__=='__main__':unittest.main()
