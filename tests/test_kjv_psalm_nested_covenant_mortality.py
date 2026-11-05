import unittest
from tools.kjv_archive import load_register,read
class PsalmNestedCovenantMortalityTests(unittest.TestCase):
 def test_nested_speakers_unresolved_covenant_darkness_and_numbers(self):
  prior,_=load_register('0.10-kjv.114');lang,manifest=load_register('0.10-kjv.115')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'psalms-nested-covenant-mortality-cases.json')};self.assertEqual(len(cases),198)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','right','host','consume','render','kjv_selah','quick','prevent','kjv_rahab','kjv_swallow','kjv_stripe','exact'}&set(out['keys']))
  for ref,parts in {
   '82-1':['among god:pl'], '82-6':['ipl say:perf you:pl god:pl'],
   '83-4':['wesg:a','name of kjv_israel no more'], '83-5':['one_num consent'],
   '83-9':['kjv_kison'], '83-12':['house:pl:a of god'], '83-13':['like wheel'], '83-18':['kjv_jehovah'],
   '84-3':['kjv_swallow_bird','thine altar:pl'], '84-5':['way:pl of they'], '84-6':['kjv_baca','kjv_well'],
   '84-10':['one_num day','better than thousand','i rather door keeper'],
   '85-8':['i what god kjv_lord'], '85-10':['each other:a kiss:perf'], '85-11':['truth from earth grow:fu'],
   '86-1':['ear:a down bow:imp'], '86-8':['among god:pl'], '86-10':['thou god alone'],
   '86-11':['my/heart:a together join:imp'], '86-13':['lowest kjv_hell'],
   '87-4':['ipl kjv_rahab_psalm:a'], '87-5':['this and that man in she born:psv:pa'],
   '87-6':['kjv_number:fu'], '87-7':['all my/spring:pl'],
   '88-4':['kjv_number:psv:pr'], '88-5':['free among dead','in grave lie:pr'],
   '88-7':['in heavy manner lie:pr'], '88-10':['dead rise:fu and thee:a praise:fu'],
   '88-13':['my/prayer before thee come:fu'], '88-18':['my/acquaintance:a into darkness'],
   '89-3':['ipl kjv_covenant:a','mypl/servant'], '89-10':['kjv_rahab_broken:a'],
   '89-14':['judgment dwelling of thy/throne'], '89-19':['to thy/holy one','say:pa ipl'],
   '89-22':['kjv_exact_debt:fu:neg'], '89-26':['he to ipl cry:fu','thou my/father my/god'],
   '89-27':['mypl/first born:psv:adj'], '89-32':['kjv_stripe_blow:pl'],
   '89-34':['mypl/kjv_covenant:a ipl break:fu:neg'], '89-35':['once ipl','kjv_lie_false:fu:neg'],
   '89-39':['kjv_covenant:a of thy/servant void make:perf'], '89-50':['i in my/bosom'],
   '90-4':['thousand year:pl','kjv_watch_period'],
   '90-10':['three+twenty and ten year:pl','four+twenty year:pl','wepl away fly:pr'],
   '90-12':['wepl our/heart:pl:a'], '90-13':['relent:opt'],
   '90-15':['wesg:a glad','thou wepl:a kjv_afflict:perf'], '90-17':['ourone/god upon wesg','our/hand:pl'],
   '91-3':['harm:adj kjv_pestilence'], '91-7':['thousand at thy/side','ten+thousand'],
   '91-9':['who my/kjv_refuge be:pr'], '91-11':['in all thy/way:pl'],
   '91-14':['upon ipl','mypl/name:a'], '91-15':['ipl with he in kjv_trouble'],
   '92-3':['instrument of ten string:pl'], '92-7':['grass grow:pr','kjv_iniquity thrive:pr'],
   '92-10':['kjv_unicorn'], '92-11':['my/desire:a'], '92-12':['kjv_palm_tree'],
   '93-1':['move:psv:can:neg'], '93-3':['flood:pl their/voice:a up lift:perf','flood:pl their/kjv_wave:pl:a up lift:pr'],
   '93-5':['holy:ev thy/house:a fit:pr'],
  }.items():
   for p in parts:self.assertIn(p,cases['psalms-'+ref]['analysis'])
  self.assertNotIn('mypl/',cases['psalms-89-26']['analysis'])
  for k,c in cases.items():
   if k.startswith(('psalms-86-','psalms-88-','psalms-92-')):self.assertNotIn('ipl',lang.compile(c['analysis'])['keys'])
  self.assertNotEqual(lang.lexicon['kjv_rahab']['meaning'],lang.lexicon['kjv_rahab_psalm']['meaning'])
  self.assertNotEqual(lang.lexicon['kjv_rahab_psalm']['meaning'],lang.lexicon['kjv_rahab_broken']['meaning'])
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),7)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-114')
if __name__=='__main__':unittest.main()
