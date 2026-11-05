import unittest
from tools.kjv_archive import load_register,read
class PsalmRefrainCurseRoyalTests(unittest.TestCase):
 def test_refrain_variations_curse_ambiguity_and_divine_quote(self):
  prior,_=load_register('0.10-kjv.116');lang,manifest=load_register('0.10-kjv.117')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'psalms-refrain-curse-royal-cases.json')};self.assertEqual(len(cases),197)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','right','host','consume','render','kjv_selah','prevent','fair','share','suffer','subject','please'}&set(out['keys']))
  for ref,parts in {
   '106-6':['wesg','ourone/father:pl'], '106-11':['not one_num'], '106-15':['thin:ev:a into their/soul'],
   '106-23':['stand:neg:pp','destroy:should'], '106-30':['plague stop:psv:pa'], '106-31':['reckon:psv:pa'],
   '106-37':['son:pl:a and their/daughter:pl:a'], '106-42':['subdue:psv:pa'],
   '106-46':['pity:psv:inf make:pa'], '106-47':['wesg:a save:imp','wepl:a from among kjv_heathen gather:imp'],
   '107-6':['cry:pa','deliver:pa'], '107-13':['cry:pa','save:pa'], '107-19':['cry:pr','save:pr'],
   '107-20':['send:pa','heal:pa'], '107-28':['cry:pr','bring:pr'], '107-14':['kjv_binding_band:pl'],
   '107-27':['kjv_reel_unsteady:pr','like drunk man'], '107-30':['kjv_haven'],
   '107-38':['allow:neg:pr'], '107-42':['kjv_iniquity her/mouth:a'],
   '108-4':['above heaven:pl'], '108-7':['ipl rejoice:fu'], '108-9':['over kjv_philistia ipl triumph:fu'],
   '108-11':['our/army:pl go:fu'], '108-13':['wepl','ourone/enemy:pl'],
   '109-6':['over he','satan','kjv_right_side'], '109-9':['child:pl kjv_fatherless','wife widow'],
   '109-14':['his/father:pl','his/mother','blot:psv:neg:inf'], '109-18':['kjv_bowels like water','oil into his/bone:pl'],
   '109-20':['mine kjv_adversary:pl'], '109-24':['kjv_fast:ev'], '109-31':['kjv_right_side hand of poor'],
   '110-1':['kjv_lord to my/lord say:pa','mypl/kjv_right_side','until ipl','thy/kjv_footstool'],
   '110-3':['womb of morning','dew:a of thy/youth'], '110-4':['relent:neg:fu','rank of kjv_melchizedek'],
   '110-5':['lord at thy/kjv_right_side','his/wrath'], '111-9':['kjv_revere:psv:adj'],
   '112-4':['he gracious','kjv_compassion'], '113-7':['kjv_dunghill'], '114-1':['strange language'],
   '115-3':['whatever he desire:perf'], '115-12':['wesg:a remember:perf','wesg:a bless:fu'],
   '115-17':['dead kjv_lord:a praise:neg:pr'], '115-18':['wesg kjv_lord:a bless:fu'],
  }.items():
   for part in parts:self.assertIn(part,cases['psalms-'+ref]['analysis'],(ref,part))
  self.assertEqual(len({cases['psalms-107-'+str(v)]['expectedText'] for v in (8,15,21,31)}),1)
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_reel_unsteady'})
  entry=lang.lexicon['kjv_reel_unsteady'];self.assertEqual(entry['form'],''.join(lang.lexicon[k]['form'] for k in entry['derivationKeys']))
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
