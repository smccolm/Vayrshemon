import unittest,re
from tools.kjv_archive import load_register,read

class EzekielMourningSignTests(unittest.TestCase):
 def test_paired_cities_and_mourning_sign(self):
  prior,_=load_register('0.10-kjv.160');lang,manifest=load_register('0.10-kjv.161')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('ezekiel-'):c for c in read(lang.folder/'ezekiel-paired-cities-and-mourning-sign-cases.json')};self.assertEqual(len(cases),139)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text'])
   self.assertFalse({'one','host','bow','ghost','roll','fold','care','plain','border','stuff','lock','light','divine','eminent','wax','fashion','fair','meat','worship','spy','waste','spring','shoot','flourish','point','privy','raven','pile'}&set(r['keys']))
  for r,parts in {
   '21-3':['kjv_righteous and wicked:a'],
   '21-10':['wesg mirth:a make:should?','rod:a of mypl/son'],
   '21-14':['double:psv:opt third:ord time','their/secret chamber:pl'],
   '21-15':['kjv_sword_point:a','up wrap:psv:perf'],
   '21-19':['two way:pl:a','both two out of one_num land'],
   '21-21':['his/arrow:pl:a bright make:pa','in kjv_liver look:pa'],
   '21-22':['captain:pl:a appoint:inf','kjv_battering_ram:pl:a'],
   '21-24':['remember:psv:caus:perf'],
   '21-27':['whose right it be:pr'],
   '21-30':['ipl it:a into his/kjv_sheath return:caus:fu?'],
   '22-7':['father and mother:a little esteem:perf'],
   '22-11':['his/daughter by marriage:a','his/father daughter:a'],
   '22-16':['thine/inheritance:a in thyself'],
   '22-18':['kjv_brass and kjv_tin and kjv_iron and lead_metal'],
   '22-20':['kjv_brass and kjv_iron and lead_metal and kjv_tin:a','you:a there leave:fu'],
   '22-24':['rain fall:neg:perf'],
   '22-25':['conspiracy of her/prophet:pl'],
   '22-26':['between holy and common','between kjv_unclean_ritual and kjv_clean_ritual','ipl among they kjv_profane:psv:pr'],
   '22-27':['her/prince:pl'],
   '22-28':['when kjv_lord speak:neg:perf'],
   '22-30':['ipl none:a find:pa'],
   '23-2':['two woman:pl daughter:pl of one_num mother'],
   '23-4':['they:du of ipl','kjv_samaria kjv_aholah','kjv_jerusalem kjv_aholibah'],
   '23-13':['they:du both one_num way:a take:pa'],
   '23-14':['with kjv_vermilion'],
   '23-17':['her/mind from they stranger make:psv:pa'],
   '23-18':['mypl/mind from she stranger make:psv:pa'],
   '23-23':['kjv_pekod and kjv_shoa and kjv_koa'],
   '23-24':['according_to their/judgment:pl'],
   '23-34':['its/kjv_potsherd:pl:a break:fu'],
   '23-37':['whom they:du to ipl bear:pa'],
   '23-40':['you:du for man:pl:a','thou thyself:a wash:pa'],
   '23-42':['kjv_sabeans_ezekiel'],
   '23-45':['kjv_righteous man:pl they they:du:a'],
   '23-49':['you:du sin:pl:a','you:du know:fu'],
   '24-5':['bone:pl:a under it burn:imp'],
   '24-6':['kjv_pot_scum out of it go:neg:perf','no kjv_lot'],
   '24-7':['she it:a upon top of rock'],
   '24-8':['ipl her/blood:a upon top of rock'],
   '24-12':['herself:a with lie:ev:pl tire:perf'],
   '24-13':['ipl thee:a purge:perf','thou purge:psv:neg:pa'],
   '24-14':['neither ipl repent:fu','they thee:a judge:fu'],
   '24-17':['kjv_head_tire:a','thy/lip:pl:a cover:neg:imp'],
   '24-18':['at evening my/wife die:pa','i in morning'],
   '24-19':['thou wesg:a','to wesg'],
   '24-21':['ipl mypl/kjv_sanctuary:a kjv_profane:fu'],
   '24-22':['as i do:perf'],
   '24-23':['you mourn:neg:fu nor weep:fu','each towards another mourn:fu'],
   '24-24':['kjv_ezekiel to you sign','ipl lord god']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(cases['21-27']['analysis'].count('kjv_overthrow:fu'),3)
  self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])wesg(?![a-z_])',c['analysis'])},{'21-10','24-19'})
  self.assertEqual({r for r,c in cases.items() if 'you:du' in c['analysis']},{'23-40','23-49'})
  self.assertNotIn('ipl',cases['24-22']['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),8)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
