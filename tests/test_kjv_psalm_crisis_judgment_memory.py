import unittest
from tools.kjv_archive import load_register,read
class PsalmCrisisJudgmentMemoryTests(unittest.TestCase):
 def test_crisis_corporate_self_judge_counterfactual_and_source_readings(self):
  prior,_=load_register('0.10-kjv.113');lang,manifest=load_register('0.10-kjv.114')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'psalms-crisis-judgment-memory-cases.json')};self.assertEqual(len(cases),213)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'bow','lie','desert','right','host','consume','render','conversation','kjv_selah','quick','prevent'}&set(out['keys']))
  for ref,parts in {
   '73-2':['my/step:pl almost kjv_slide:pp'], '73-4':['kjv_binding_band:pl'],
   '73-10':['his/people here','kjv_wring:psv:pr'], '73-13':['i my/heart:a in vain'],
   '73-15':['offend:should'], '73-21':['my/kjv_kidney:pl prick:psv:pa'],
   '73-23':['my/kjv_right_side hand'], '73-27':['kjv_whoring:pr'],
   '74-1':['wesg:a'], '74-8':['wesg:a they:a together destroy:inf','kjv_synagogue:pl:a'],
   '74-9':['wepl ourone/sign:pl:a','among wesg'], '74-12':['mypl/king'],
   '74-14':['head:pl:a of leviathan','as food to people'],
   '75-2':['ipl kjv_congregation:a'], '75-3':['ipl its/kjv_pillar:pl:a'],
   '75-6':['from east','from west nor from kjv_south'],
   '75-8':['wine red','kjv_wine_dregs:a'], '75-9':['i praise:pl:a'], '75-10':['ipl cut:fu off'],
   '76-3':['kjv_bow','battle:a break:pa'], '76-6':['chariot and horse','death:adj sleep:ev'],
   '76-7':['when thou angry become:pr'], '76-10':['wrath of human thee:a praise:fu','remainder:a of wrath'],
   '77-2':['my/wound in night flow:pa'], '77-4':['i speak:can:neg'],
   '77-6':['my/own heart kjv_commune:pr'], '77-8':['mercy entirely'],
   '77-10':['year:pl:a of kjv_right_side hand'], '77-13':['ourone/god'],
   '77-19':['footstep:pl know:psv:pr:neg'],
   '78-2':['i my/mouth:a'], '78-3':['wesg hear:perf','ourone/father:pl'],
   '78-4':['wesg they:a from their/child:pl hide:fu:neg'],
   '78-9':['kjv_bow:pl:a'], '78-18':['test:pa','food:a for their/lust'],
   '78-25':['human food:a of angel:pl eat:pa'], '78-31':['most fat','choose:psv:adj man:pl:a'],
   '78-36':['kjv_lie_false:pa'], '78-37':['kjv_steadfast'], '78-41':['boundary:caus:pa'],
   '78-45':['kjv_fly_insect:a','kjv_frog:pl:a'], '78-47':['kjv_sycomore:pl:a with frost'],
   '78-49':['evil angel:pl:a'], '78-51':['first born:psv:adj:a'],
   '78-55':['by kjv_cord'], '78-63':['maiden:pl to marriage give:psv:pa:neg'],
   '78-65':['because of wine shout:pr'], '78-66':['in back part:pl'],
   '78-69':['like high palace:pl'], '78-71':['pregnant female sheep:a'],
   '79-8':['quickly before wesg come:inf'], '79-12':['seven kjv_fold'],
   '80-1':['between kjv_cherub:pl'], '80-11':['she her/branch:pl:a'],
   '80-16':['it down cut:psv:pr','they at rebuke'], '80-17':['son of man'],
   '80-18':['wesg:a alive make:imp'], '81-3':['new moon'],
   '81-5':['where i language:a hear:pa','i understand:pa:neg'],
   '81-6':['ipl his/kjv_shoulder:a','kjv_pot:pl'], '81-7':['ipl thee:a','kjv_meribah'],
   '81-10':['ipl kjv_lord thy/god'], '81-11':['mypl/voice listen:pa:neg'],
   '81-13':['if only mypl/people to ipl listen:pp','walk:pp:excl'],
   '81-14':['subdue:perf:should','mypl/hand:a'],
   '81-15':['their/time for ever endure:perf:should'],
   '81-16':['he they:a','honey from rock ipl thee:a satisfy:perf:should'],
  }.items():
   for p in parts:self.assertIn(p,cases['psalms-'+ref]['analysis'])
  for k,c in cases.items():
   if k.startswith(('psalms-73-','psalms-77-')):self.assertNotIn('ipl',lang.compile(c['analysis'])['keys'])
  self.assertNotIn('north',lang.compile(cases['psalms-75-6']['analysis'])['keys'])
  for ref,address in [('3','god:excl'),('7','god of army:pl:excl'),('19','kjv_lord god of army:pl:excl')]:
   a=cases['psalms-80-'+ref]['analysis'];self.assertIn('turn:imp '+address,a);self.assertIn('wesg save:psv:fu',a)
  self.assertIn('interpret',cases['psalms-75-2']['note'].lower())
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),3)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-113')
if __name__=='__main__':unittest.main()
