import unittest
from tools.kjv_archive import load_register,read

class EzraCrownConfessionTests(unittest.TestCase):
 def test_personal_corporate_imperial_and_exposed_bodies(self):
  prior,_=load_register('0.10-kjv.95');lang,manifest=load_register('0.10-kjv.96')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'ezra-crown-and-confession-cases.json')};self.assertEqual(len(cases),162)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss'])
   self.assertNotIn('three',result['keys']);self.assertNotIn('!',result['text'])
  def a(r):return cases['ezra-'+r]['analysis']
  for r,parts in {
   '5-4':['wesg to they'],
   '5-11':['to wesg return:pa','wesg servant:pl'],
   '6-2':['kjv_achmetha'],
   '6-11':['ipl decree:a','hang:psv:opt','kjv_dunghill'],
   '6-12':['his/name:a there dwell:caus:perf','ipl kjv_darius'],
   '6-22':['king of kjv_assyria'],
   '7-13':['mypl/kingdom'],
   '7-21':['ipl even ipl kjv_artaxerxes'],
   '7-22':['salt without how much:a set:ev'],
   '7-24':['wesg you:pl:a','be:neg:fu'],
   '7-26':['death','kjv_banish:ev','kjv_confiscate:ev','imprison:ev'],
   '7-28':['i strengthen:psv:pa','my/god upon i'],
   '8-5':['son of kjv_jahaziel_return_father'],
   '8-10':['son of kjv_josiphiah'],
   '8-15':['wepl in tent:pl','i people and priest:pl:a view:pa'],
   '8-21':['i kjv_fast:ev:a','wesg ourselves:a','straight way:a'],
   '8-22':['i ashamed be:pa','because wesg to king speak:pp'],
   '8-23':['wesg kjv_fast:pa'],
   '8-27':['twenty kjv_basin:pl','thousand kjv_dram_treasure:pl','two vessel:pl of fine kjv_copper'],
   '8-31':['wepl from river','ourone/god upon wepl'],
   '9-6':['my/god:excl i ashamed','ourone/kjv_iniquity:pl'],
   '9-8':['nail:a','little revive:ev:a in ourone/bondage'],
   '9-9':['wepl person:pl in kjv_bondservice','ourone/god wesg:a'],
   '9-15':['wesg escape:perf and yet remain:pr','stand:neg:pr:can'],
   '10-3':['all wife:pl:a and such:a as of they bear:psv:pr','counsel of my/lord'],
   '10-8':['his/kjv_goods forfeit:psv:should'],
   '10-12':['wesg do:must'],
   '10-13':['wepl outside stand:neg:pr:can','wepl many be:pr'],
   '10-15':['employ:psv:pa'],
   '10-23':['kjv_kelaiah same kjv_kelita be:pr'],
   '10-25':['kjv_malchiah_ezra_list','kjv_malchijah_ezra_list'],
   '10-44':['some of they','child:pl:a have:pa'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(a('8-16').count('kjv_elnathan_return'),3)
  self.assertNotIn('kjv_brass',lang.compile(a('8-27'))['keys'])
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),158)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-95')

if __name__=='__main__':unittest.main()
