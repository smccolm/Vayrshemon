import unittest
from tools.kjv_archive import load_register,read
class NehemiahWallBodyTests(unittest.TestCase):
 def test_unity_distributed_workers_and_local_identities(self):
  prior,_=load_register('0.10-kjv.96');lang,manifest=load_register('0.10-kjv.97')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'nehemiah-wall-body-cases.json')};self.assertEqual(len(cases),86)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
  def a(r):return cases['nehemiah-'+r]['analysis']
  for r,parts in {
   '1-6':['wesg against thee','both i and my/father:poss house'],
   '1-8':['remember:imp i thee:a','ipl you:pl:a'],
   '1-9':['mypl/command:pl','mypl/name:a'],
   '2-9':['captain:pl of army and kjv_horseman:pl'],
   '2-18':['they say:pa wesg'],
   '2-20':['no kjv_portion_share nor right nor kjv_memorial'],
   '3-5':['their/kjv_lord put:neg:pa'],
   '3-12':['he and his/daughter:pl'],
   '3-13':['thousand kjv_cubit:pl'],
   '3-16':['kjv_nehemiah_azbuk son of kjv_azbuk'],
   '3-26':['kjv_nethinim:pl in kjv_ophel dwell:pa'],
   '3-30':['six:ord son of kjv_zalaph'],
   '4-4':['for prey in land of kjv_captivity'],
   '4-5':['cover:neg:imp','blot:psv:neg:opt'],
   '4-10':['wepl wall:a build:neg:pr:can'],
   '4-11':['ourone/kjv_adversary:pl','until wesg in middle'],
   '4-12':['to wesg ten time:pl','to wepl return:fu'],
   '4-15':['to wesg know:psv:pa','wepl all of wepl','each to his/work'],
   '4-17':['one_num of his/hand:pl'],
   '4-19':['wepl upon wall separate:psv:pr'],
   '4-20':['ourone/god for wesg fight:fu'],
   '4-23':['none of wepl','for wash:ev'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(a('4-2').count('?'),5)
  self.assertNotIn('repair',lang.compile(a('3-26'))['keys'])
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-96')
if __name__=='__main__':unittest.main()
