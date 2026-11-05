import unittest
from tools.kjv_archive import load_register,read
class ChroniclesPaidArmiesTests(unittest.TestCase):
 def test_collective_cost_dual_opponents_and_shared_liability(self):
  prior,_=load_register('0.10-kjv.91');lang,manifest=load_register('0.10-kjv.92')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'chronicles-paid-armies-cases.json')};self.assertEqual(len(cases),87)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss'])
  def a(r):return cases['2-chronicles-'+r]['analysis']
  for r,parts in {
   '25-4':['each man for his/own sin'],
   '25-9':['wesg','ipl','hundred kjv_talent_weight:pl'],
   '25-12':['other ten+thousand alive','all in piece:pl'],
   '25-16':['i know:pr','my/counsel'],
   '25-17':['we:du each_other:a'],
   '25-21':['they:du each_other:a'],
   '25-23':['kjv_jehoahaz_jehoram','four+hundred kjv_cubit:pl'],
   '25-28':['city of kjv_judah'],
   '26-3':['kjv_jecoliah'],
   '26-10':['field+work:ev','flat land:pl'],
   '26-11':['kjv_scribe','one_num of captain:pl'],
   '26-13':['kjv_three+hundred+thousand and seven+thousand and five+hundred'],
   '26-15':['skill:adj man:pl'],
   '26-21':['separate:psv house'],
   '26-22':['rest of act:pl:a','kjv_amoz write:pa'],
   '27-1':['kjv_jerushah'],
   '27-5':['second year and third'],
   '28-3':['his/child:pl:a in fire burn:pa'],
   '28-11':['i:a hear:imp'],
   '28-13':['wesg','ourone/sin:pl','ourone/kjv_trespass'],
   '28-15':['shoe:pa','anoint:pa','kjv_palm_tree:pl'],
   '28-16':['king:pl of kjv_assyria'],
   '28-18':['kjv_shocho'],
   '28-19':['king of kjv_israel','kjv_uncoveredness'],
   '28-23':['ipl to they','ipl:a help:may'],
   '28-27':['tomb:pl of king:pl of kjv_israel'],
  }.items():
   for part in parts:self.assertIn(part,a(r))
  for c in cases.values():self.assertFalse({'host','count','matter'} & set(lang.compile(c['analysis'])['keys']))
  self.assertNotIn('ipl',lang.compile(a('25-16'))['keys'])
  self.assertNotIn('wesg',lang.compile(a('25-17'))['keys'])
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-91')
if __name__=='__main__':unittest.main()
