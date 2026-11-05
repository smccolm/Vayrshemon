import unittest
from tools.kjv_archive import load_register,read
class ChroniclesRoyalChildTests(unittest.TestCase):
 def test_source_variants_fractions_and_exclamatory_cry(self):
  prior,_=load_register('0.10-kjv.90');lang,manifest=load_register('0.10-kjv.91')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'chronicles-royal-child-cases.json')};self.assertEqual(len(cases),80)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss'])
  def a(r):return cases['2-chronicles-'+r]['analysis']
  for r,parts in {
   '21-2':['kjv_azariah_jehoshaphat_first','kjv_azariah_jehoshaphat_second','king of kjv_israel'],
   '21-7':['destroy:inf will:neg:pa','light:a'],
   '21-12':['write:ev from kjv_elijah'],
   '21-17':['kjv_goods','kjv_jehoahaz_jehoram'],
   '21-19':['two year:pl','no burn:ev'],
   '22-2':['forty and two','one_num year','daughter of kjv_omri'],
   '22-6':['kjv_ramah','kjv_azariah_jehoram'],
   '22-8':['son:pl of brother:pl'],
   '22-11':['kjv_jehoshabeath','his/kjv_nurse','wife of kjv_jehoiada_priest'],
   '23-4':['kjv_third_share'], '23-5':['kjv_court_enclosure'],
   '23-8':['kjv_service_order:pl:a dismiss:neg:pa'],
   '23-13':['treason:excl treason:excl'],
   '23-14':['over army'], '23-16':['between he'],
   '24-6':['kjv_tabernacle of testimony'],
   '24-11':['kjv_scribe of king and officer of high priest'],
   '24-15':['hundred and thirty'],
   '24-20':['kjv_zechariah_jehoiada','he also you:pl:a forsake:perf'],
   '24-21':['kjv_court_enclosure'],
   '24-25':['son:pl of kjv_jehoiada_priest','not in tomb:pl'],
   '24-26':['kjv_zabad_shimeath','kjv_shimrith_moabitess'],
  }.items():
   for part in parts:self.assertIn(part,a(r))
  self.assertEqual(a('23-5').count('kjv_third_share'),2)
  self.assertEqual(lang.compile(a('23-13'))['text'].count('’hÅ'),2)
  for c in cases.values():
   self.assertNotIn('!',c['expectedText']);self.assertFalse({'ipl','wesg','host'} & set(lang.compile(c['analysis'])['keys']))
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-90')
if __name__=='__main__':unittest.main()
