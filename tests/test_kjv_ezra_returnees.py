import unittest
from tools.kjv_archive import load_register,read

class EzraReturneeTests(unittest.TestCase):
 def test_opposed_communities_court_and_returnee_distinctions(self):
  prior,_=load_register('0.10-kjv.94');lang,manifest=load_register('0.10-kjv.95')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'ezra-returnees-cases.json')};self.assertEqual(len(cases),118)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss'])
   self.assertNotIn('three',result['keys'])
  def a(r):return cases['ezra-'+r]['analysis']
  for r,parts in {
   '1-2':['to ipl all kingdom:pl','he ipl:a charge:perf'],
   '1-7':['house of his/god:pl'],
   '1-8':['kjv_mithredath_treasurer','kjv_sheshbazzar','kjv_number:pa'],
   '1-11':['five+thousand and four+hundred'],
   '2-16':['kjv_ater_hezekiah of kjv_hezekiah_ater'],
   '2-31':['other kjv_elam_other'],
   '2-40':['kjv_hodaviah_return'],
   '2-42':['kjv_ater_porter','kjv_akkub_porter_return'],
   '2-45':['kjv_akkub_nethinim'],
   '2-59':['show:neg:pa:can','whether they of kjv_israel'],
   '2-61':['kjv_barzillai_claimant','after their/name'],
   '2-62':['their/record:ev:a','kjv_pollute_sacred:psv'],
   '2-63':['kjv_tirshatha','until priest with kjv_urim and with kjv_thummim'],
   '2-64':['forty+thousand and two+thousand and kjv_three+hundred and six+ten'],
   '2-69':['six+ten+thousand and one_num+thousand','kjv_dram_treasure','kjv_pound_weight'],
   '3-1':['as one_num man'],
   '3-3':['its/kjv_foundation:pl'],
   '3-4':['custom'],
   '3-9':['son:pl of kjv_judah'],
   '3-13':['distinguish:neg:pa:can'],
   '4-2':['wesg with you:pl build:opt','wesg your/god:a'],
   '4-3':['with wesg','ourone/god','wesg ourselves together'],
   '4-13':['toll kjv_tribute and kjv_custom_duty'],
   '4-14':['wepl support:ev:a','therefore wesg send:perf'],
   '4-18':['to wesg','before ipl'],
   '4-19':['ipl command:pa'],
   '4-21':['until another command from ipl'],
   '4-23':['by force and power'],
   '4-24':['until second year','kjv_darius'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(a('4-7').count('kjv_syrian speech'),2)
  self.assertEqual(a('2-70').count('in their/city:pl'),2)
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),140)
  self.assertEqual(lang.lexicon['kjv_tirshatha']['pos'],'noun')
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-94')

if __name__=='__main__':unittest.main()
