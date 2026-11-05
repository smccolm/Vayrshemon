import unittest,re
from tools.kjv_archive import load_register,read
class IsaiahCommissionTests(unittest.TestCase):
 def test_divine_self_human_response_and_source_difficulties(self):
  prior,_=load_register('0.10-kjv.129');lang,manifest=load_register('0.10-kjv.130')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('isaiah-'):c for c in read(lang.folder/'isaiah-divine-plural-self-and-commission-cases.json')};self.assertEqual(len(cases),128)
  voices={k:set() for k in ['ipl','wesg','ourone']}
  for ref,c in cases.items():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'one','fair','right','sound','substance','want','please','count','host'}&set(out['keys']))
   self.assertNotRegex(c['analysis'],r'(?<![a-z_])(?:wepl|they:du|you:du|we:du)(?![a-z_])')
   for k in voices:
    if re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis']):voices[k].add(ref)
  self.assertEqual(voices['ipl'],set('1-2 1-11 1-12 1-13 1-14 1-15 1-24 1-25 1-26 3-4 5-3 5-4 5-5 5-6 6-8'.split()))
  self.assertEqual(voices['wesg'],set('1-9 1-18 2-3 2-5 4-1 5-19 6-8'.split()))
  self.assertEqual(voices['ourone'],{'1-10','3-6','4-1'})
  for ref,parts in {
   '1-6':['no healthy:ev','kjv_ointment'],'1-9':['wesg would as kjv_sodom'],
   '1-13':['ipl endure:neg:can'],'1-14':['mypl/soul hate:pr','carry:inf weary'],
   '1-18':['wesg together reason:opt','kjv_scarlet','crimson','kjv_wool'],
   '1-24':['ipl iplself:a'],'1-25':['thy/kjv_tin:a'],'1-27':['kjv_convert:ag:pl'],
   '1-31':['its/make:ag as spark'],'2-4':['kjv_ploughshare:pl','kjv_pruninghook:pl'],
   '2-6':['kjv_please_satisfy:pr'],'2-9':['they:a forgive:neg:imp'],
   '2-16':['pleasing image:pl'],'2-20':['kjv_mole_animal:pl'],'2-22':['esteem:psv:inf'],
   '3-3':['five+ten'],'3-4':['ipl child:pl:a'],'3-7':['i heal:ag be:neg:fu'],
   '3-12':['my/people'],'3-15':['mypl/people:a'],'3-16':['small delicate step:pl'],
   '3-17':['scalp:a','secret part:pl:a expose:fu'],'3-18':['kjv_head_caul:pl','kjv_crescent_tire:pl'],
   '3-20':['kjv_tablet_ornament:pl:a'],'3-22':['kjv_crisping_pin:pl:a'],
   '3-23':['kjv_mirror:pl:a'],'3-24':['kjv_stomacher'],
   '4-1':['seven woman:pl one_num','wesg ourone/own bread:a'],
   '4-4':['spirit of judgment and by spirit of burn:ev'],
   '5-1':['i to my/well beloved'],'5-3':['between ipl and mypl/kjv_vineyard'],
   '5-10':['ten kjv_acre:pl','one_num kjv_homer one_num kjv_ephah_measure:a'],
   '5-12':['kjv_viol'],'5-13':['my/people'],'5-14':['kjv_hell_depth herself:a'],
   '5-17':['fat human:pl stranger:pl eat:fu'],'5-19':['wesg it:a see:may'],
   '5-25':['kjv_corpse:pl in middle of street:pl rend:psv:pa'],
   '5-26':['whistle:fu'],'5-28':['kjv_hoof:pl like flint esteem:psv:fu'],
   '6-1':['kjv_robe_train'],'6-2':['each six wing:pl:a'],
   '6-5':['i human of unclean lip:pl'],'6-6':['one_num of kjv_seraph:pl','burn:adj kjv_charcoal:a'],
   '6-8':['i voice:a of lord hear:pa','whom:a ipl send:fu and who for wesg go:fu','then i say:pa here i be:pr i:a send:imp'],
   '6-9':['understand:neg:imp','perceive:neg:imp'],'6-10':['lest they','kjv_convert:pr and heal:psv:pr'],
   '6-13':['kjv_tenth_share','kjv_teil_tree','their/leaf:pl:a cast:pr','holy seed its/kjv_tree_stock'],
  }.items():
   for part in parts:self.assertIn(part,cases[ref]['analysis'],(ref,part))
  self.assertEqual(cases['6-2']['analysis'].count('with two'),3)
  self.assertEqual(cases['6-3']['analysis'].count('holy'),3)
  self.assertEqual(cases['3-24']['analysis'].count('in place of'),5)
  additions=set(lang.lexicon)-set(prior.lexicon);self.assertEqual(len(additions),16)
  self.assertEqual(sum(lang.lexicon[k]['pos']=='proper' for k in additions),0)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
