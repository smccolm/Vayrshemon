import unittest,re
from tools.kjv_archive import load_register,read

class EzekielRefusedConsultationTests(unittest.TestCase):
 def test_inherited_guilt_and_refused_consultation(self):
  prior,_=load_register('0.10-kjv.159');lang,manifest=load_register('0.10-kjv.160')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('ezekiel-'):c for c in read(lang.folder/'ezekiel-inherited-guilt-and-refused-consultation-cases.json')};self.assertEqual(len(cases),119)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text']);self.assertNotIn(':du',c['analysis'])
   self.assertFalse({'one','host','bow','ghost','roll','fold','care','plain','right','tear','border','stuff','lock','light','divine','eminent','wax','fashion','fair','meat','worship','bear','spy','waste','spring','shoot','flourish'}&set(r['keys']))
  for r,parts in {
   '17-3':['long wing:adj','different colour:pl'],
   '17-7':['another great kjv_eagle','her/root:pl:a','kjv_water_irrigate:may'],
   '17-9':['up pull:neg:fu','her/grow:ev'],
   '17-14':['kingdom low','it itself:a up lift:neg:may'],
   '17-16':['as ipl live:pr','king who he:a king make:pa'],
   '17-18':['his/hand:a give:pp','he escape:neg:fu'],
   '17-19':['mypl/oath:a','mypl/kjv_covenant:a'],
   '17-20':['with he there','kjv_litigate:fu'],
   '17-21':['his/band:pl','all wind:pl'],
   '17-22':['tender branch:a','high and lofty mountain'],
   '17-24':['high kjv_tree:a down bring:perf','dry kjv_tree:a kjv_flourish_plant:caus:perf'],
   '18-4':['all soul:pl of ipl','soul who sin:pr it die:fu'],
   '18-6':['woman of kjv_menstrual_flow'],
   '18-7':['debt:a owe:pr his/pledge:a restore:perf'],
   '18-13':['he then live:fu?','he live:neg:fu','his/blood upon he'],
   '18-16':['pledge:a withhold:neg:perf'],
   '18-17':['his/hand:a from poor off take:perf','father die:neg:fu'],
   '18-20':['son kjv_iniquity:a of father endure:neg:fu','neither father kjv_iniquity:a of son endure:fu'],
   '18-22':['kjv_mention:psv:neg:fu'],
   '18-24':['all his/kjv_righteousness','kjv_mention:psv:neg:fu'],
   '18-25':['mypl/way equal be:neg:pr?','your/way:pl equal:neg:adj be:neg:pr?'],
   '18-29':['mypl/way:pl equal be:neg:pr?'],
   '18-31':['for you new heart:a and new spirit:a make:imp'],
   '19-4':['chain:pl to land of egypt'],
   '19-7':['their/kjv_desolate palace:pl:a know:pa'],
   '19-10':['in thy/blood'],
   '19-11':['authority:a hold:pa'],
   '19-14':['fire out of rod of her/branch:pl','this lamentation be:pr and for lamentation be:fu'],
   '20-3':['ipl by you ask:psv:neg:fu'],
   '20-5':['iplself:a'],
   '20-8':['to ipl listen:inf refuse:pa'],
   '20-9':['ipl iplself:a'],
   '20-18':['kjv_statute:pl of your/father:pl'],
   '20-19':['mypl/kjv_statute:pl'],
   '20-22':['mypl/hand:a withdraw:pa'],
   '20-25':['ipl they:a also kjv_statute:pl:a which good be:neg:pa give:pa','by which they live:neg:should'],
   '20-26':['ipl they:a in their/own gift:pl kjv_pollute_sacred:pa','all which womb:a open:pr'],
   '20-29':['kjv_bamah'],
   '20-32':['wesg as kjv_heathen as kjv_family:pl'],
   '20-35':['face to face kjv_litigate:fu'],
   '20-37':['bond of kjv_covenant'],
   '20-38':['enter:neg:fu'],
   '20-39':['go:imp each his/idol:pl:a serve:imp','if you to ipl listen:neg:fu'],
   '20-41':['ipl in you before kjv_heathen sanctify:psv:fu'],
   '20-47':['every green kjv_tree:a','every dry kjv_tree:a','burn:cv flame extinguish:psv:neg:fu'],
   '20-49':['then i say:pa ah lord god:excl','he kjv_parable_oracle:pl:a speak:neg:pr?']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(cases['20-4']['analysis'].count('thou they:a judge:fu'),2)
  self.assertEqual(cases['20-5']['analysis'].count('mypl/hand:a'),2)
  self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])wesg(?![a-z_])',c['analysis'])},{'20-32'})
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),2)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
