import unittest
from tools.kjv_archive import load_register,read
class JobWhirlwindRestorationTests(unittest.TestCase):
 def test_divine_voices_creature_senses_and_restoration(self):
  prior,_=load_register('0.10-kjv.106');lang,manifest=load_register('0.10-kjv.107')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'job-whirlwind-restoration-cases.json')};self.assertEqual(len(cases),204)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','matter','consume','one','fine','just','render','mark','point','discover','stay','scale'}&set(out['keys']))
  def a(r):return cases['job-'+r]['analysis']
  for r,parts in {
   '34-6':['my/right kjv_lie_false:should'],
   '36-2':['i:a little permit','on behalf of god'], '36-6':['right:a to poor'],
   '36-26':['wesg he:a know:neg'], '36-27':['drop:pl of water:a small','kjv_vapour'],
   '36-32':['with cloud:pl','shine:neg:inf'], '36-33':['kjv_livestock also about kjv_vapour'],
   '37-4':['restrain:neg'], '37-9':['kjv_south','kjv_north'], '37-18':['melt:psv:pp kjv_mirror'],
   '37-19':['wepl:a what wesg','wesg ourone/speech:a'], '37-20':['i speak:pr'],
   '37-22':['fair weather out of kjv_north'], '37-23':['wesg','kjv_afflict:neg'],
   '38-3':['ipl of thee demand','thou ipl:a answer'], '38-4':['ipl kjv_foundation'],
   '38-9':['ipl cloud:a','kjv_swaddlingband'], '38-10':['mypl/kjv_place_site'],
   '38-12':['kjv_dawn'], '38-14':['clay_material to seal','they as garment'],
   '38-16':['spring:pl of sea'], '38-23':['ipl against time'], '38-27':['forth grow:caus'],
   '38-31':['sweet influence:pl','kjv_pleiades','kjv_orion'],
   '38-32':['kjv_mazzaroth','kjv_arcturus:a with his/son:pl'], '38-35':['wesg here'],
   '38-36':['part:pl within','understanding:a to heart'], '38-37':['bottle:pl of heaven:a restrain'],
   '39-4':['with corn'], '39-6':['ipl kjv_wilderness'], '39-9':['kjv_unicorn','kjv_crib'],
   '39-13':['kjv_peacock:pl','kjv_ostrich'], '39-19':['neck:a with thunder'],
   '39-20':['afraid as kjv_grasshopper'], '39-24':['neither he','believe:pr'], '39-25':['kjv_ha kjv_ha'],
   '40-4':['i vile'], '40-5':['one_num time','two time:pl'], '40-8':['mypl/judgment:a kjv_annul','ipl:a condemn'],
   '40-14':['ipl','kjv_right_side'], '40-15':['kjv_behemoth','ipl with thee'],
   '40-17':['kjv_testicle:pl'], '40-21':['shady kjv_tree:pl','kjv_fen:pl'],
   '40-23':['kjv_jordan:a up into his/mouth'], '40-24':['eye:pl take:pr','nose through snare:pl pierce'],
   '41-10':['before ipl'], '41-11':['ipl:a before give','mypl/thing'], '41-12':['ipl his/part:pl'],
   '41-13':['kjv_uncover','double bridle'], '41-15':['kjv_body_scale'], '41-18':['sneeze:ev:pl'],
   '41-22':['sorrow into joy'], '41-23':['kjv_flesh_flake'], '41-25':['break:ev:pl','pure:caus'],
   '41-26':['kjv_habergeon'], '41-29':['regard:psv'], '41-30':['sharp stone:pl','kjv_sharp_point:adj'],
   '42-2':['no thought'], '42-4':['i of thee demand'], '42-6':['i myself:a kjv_abhor'],
   '42-7':['mypl/wrath','two friend:pl','thing:a which true','mypl/servant'],
   '42-8':['seven kjv_bullock','seven kjv_ram','he:a ipl accept'],
   '42-9':['kjv_bildad','kjv_zophar'], '42-10':['double:a'],
   '42-11':['all evil which kjv_lord upon he bring'],
   '42-12':['ten+thousand and four+thousand','six+thousand','thousand yoke:pl'],
   '42-13':['seven son:pl','three daughter:pl'], '42-14':['kjv_jemima','kjv_kezia','kjv_kerenhappuch'],
   '42-15':['inheritance:a among their/brother:pl'], '42-16':['hundred and forty','four generation:pl'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),21)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-106')
if __name__=='__main__':unittest.main()
