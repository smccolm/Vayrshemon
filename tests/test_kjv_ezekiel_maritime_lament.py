import unittest,re
from tools.kjv_archive import load_register,read

class EzekielMaritimeLamentTests(unittest.TestCase):
 def test_civic_boasts_and_maritime_lament(self):
  prior,_=load_register('0.10-kjv.161');lang,manifest=load_register('0.10-kjv.162')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('ezekiel-'):c for c in read(lang.folder/'ezekiel-civic-boasts-and-maritime-lament-cases.json')};self.assertEqual(len(cases),100)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text']);self.assertNotIn(':du',c['analysis'])
   self.assertFalse({'one','host','bow','ghost','fold','care','plain','border','stuff','lock','light','divine','eminent','wax','fashion','fair','meat','worship','spy','waste','spring','shoot','flourish','point','privy','raven','pile','despite','row','wound'}&set(r['keys']))
   for k in ('wesg','wepl','ourone','iplself'):self.assertIsNone(re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis']))
  for r,parts in {
   '25-3':['kjv_gloat_aha:excl','mypl/kjv_sanctuary'],
   '25-4':['their/palace:pl:a'],
   '25-6':['thine/hand:pl:a together strike:perf','thy/contempt'],
   '25-9':['kjv_bethjeshimoth kjv_baalmeon and kjv_kiriathaim'],
   '25-14':['by hand of mypl/people kjv_israel'],
   '25-16':['kjv_cherethims:a'],
   '26-2':['she to ipl turn:psv:pr','ipl fill:psv:fu'],
   '26-7':['kjv_nebuchadrezzar','king of king:pl'],
   '26-9':['war engine:pl:a','his/kjv_axe:pl'],
   '26-11':['thy/strong kjv_garrison:pl'],
   '26-12':['thy/stone:pl:a and thy/wood:a and thy/dust:a'],
   '26-14':['thou no more build:psv:fu'],
   '26-17':['often visit:pr'],
   '26-20':['ipl glory:a in land of live:cv set:fu'],
   '27-3':['thou say:perf ipl of perfect beauty'],
   '27-6':['company of kjv_ashurite:pl','kjv_bench:pl:a of kjv_ivory'],
   '27-8':['thy/kjv_sailor:pl','thy/kjv_ship_pilot:pl'],
   '27-9':['kjv_elder:pl of kjv_gebal','thy/kjv_caulk:ag:pl'],
   '27-11':['kjv_gammadims'],
   '27-12':['silver kjv_iron kjv_tin and lead_metal'],
   '27-13':['person:pl:a of man:pl'],
   '27-14':['horse:pl and kjv_horseman:pl and mule:pl'],
   '27-15':['horn:pl:a of kjv_ivory and kjv_ebony'],
   '27-16':['kjv_syria'],
   '27-17':['kjv_minnith and kjv_pannag'],
   '27-18':['wine of kjv_helbon and white kjv_wool'],
   '27-19':['kjv_dan also and kjv_javan back and forth'],
   '27-20':['precious clothes for chariot:pl'],
   '27-23':['kjv_eden_trade'],
   '27-24':['chest:pl of rich clothing','kjv_cedar make:psv:adj'],
   '27-25':['ship:pl of kjv_tarshish of thee in thy/market sing:pa'],
   '27-27':['thy/kjv_sailor:pl and thy/kjv_ship_pilot:pl thy/kjv_caulk:ag:pl','trade:ag:pl'],
   '27-30':['in kjv_ashes roll:fu'],
   '28-2':['ipl god be:pr','yet thou man be:pr and not god'],
   '28-3':['kjv_daniel_ezekiel_exemplar'],
   '28-8':['death:pl:a'],
   '28-9':['ipl god be:pr?','man and no god'],
   '28-12':['king of kjv_tyrus','thou sum:a up seal:pr'],
   '28-13':['kjv_eden kjv_garden of god','kjv_sardius kjv_topaz and kjv_diamond','kjv_carbuncle and gold','thy/kjv_tabret:pl and of thy/pipe:pl'],
   '28-14':['anoint:psv:adj kjv_cherub who cover:pr'],
   '28-16':['they thy/middle:a with kjv_violence','as common','oh cover:cv kjv_cherub'],
   '28-18':['thy/kjv_sanctuary:pl:a','fire:a from thy/middle'],
   '28-22':['glorify:psv:fu','sanctify:psv:fp'],
   '28-23':['kjv_wound_inflict:psv:adj','judge:psv:fu'],
   '28-25':['sanctify:psv:fp','mypl/servant kjv_jacob']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertNotIn('kjv_eden_trade',cases['28-13']['analysis'])
  self.assertEqual(lang.lexicon['kjv_gloat_aha']['form'],prior.lexicon['ah']['form'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),13)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
