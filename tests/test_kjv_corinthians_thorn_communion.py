import unittest,re
from tools.kjv_archive import load_register,read
class CorinthiansThornCommunionTests(unittest.TestCase):
 def test_thorn_testing_and_communion(self):
  prior,_=load_register('0.10-kjv.245');lang,manifest=load_register('0.10-kjv.246')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('2-corinthians-'):c for c in read(lang.folder/'corinthians-thorn-testing-and-communion-cases.json')};self.assertEqual(len(cases),35)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text'])
   self.assertFalse({'one','matter','worship'}&set(r['keys']))
  anchors={'12:1': ['certainly glory:inf profitable be:neg:pr', 'vision:pl and reveal:ev:pl'], '12:2': ['above twelve and two year:pl ago', 'whether in body i tell:neg:can', 'whether out of body i tell:neg:can', 'third heaven'], '12:3': ['whether in body or out of body', 'i tell:neg:can god know:pr'], '12:4': ['into paradise', 'speak:neg:can:adj word:pl', 'utter:inf lawful be:neg:pr'], '12:5': ['of such person', 'of myself glory:neg:fu', 'my/infirmity:pl'], '12:6': ['i truth say:fu', 'now i kjv_forbear:pr', 'above what he i:a be:inf see:pr', 'what of i hear:pr'], '12:7': ['reveal:ev:pl abundance', 'thorn in flesh', 'kjv_satan_temptation messenger', 'kjv_buffet_corinthians:inf'], '12:8': ['three time:pl', 'it from i depart:may'], '12:9': ['mypl/grace for thee enough', 'mypl/strength in weak:ev', 'i rather in my/infirmity:pl', 'kjv_christ_title power upon i dwell:may'], '12:10': ['infirmity:pl', 'kjv_reproach:pl', 'necessity:pl', 'persecute:ev:pl', 'distress:pl', 'when i weak be:pr then i strong'], '12:11': ['in glory:ev fool become:perf', 'you i:a compel:perf', 'though i nothing'], '12:12': ['in all patience', 'sign:pl and wonder:pl and strong deed:pl'], '12:13': ['inferior be:pa:q', 'burden be:neg:pa', 'this wrong to i forgive:imp'], '12:14': ['third time', 'what you possess:pr seek:neg:pr but you:a', 'child:pl for parent:pl lay up:neg:should', 'parent:pl for child:pl'], '12:15': ['spend:fu and spend:psv:fu', 'more abundance:adv i you:a love:pr less i love:psv:pr'], '12:16': ['i you:a burden:neg:pa', 'with kjv_guile catch:pa'], '12:17': ['any of they whom i to you send:pa', 'gain make:pa:q'], '12:18': ['with he brother send:pa', 'kjv_titus_second_corinthians from you gain', 'we:du in same spirit', 'we:du in same step:pl'], '12:19': ['again you', 'wesg to you ourselves kjv_defend_argument_corinthians:pr', 'before god in kjv_christ_title', 'all thing:pl for your/kjv_edify_romans:ev'], '12:20': ['such as i wish:pr find:neg:fu', 'such as you wish:neg:pr find:psv:fu', 'quarrel:ev:pl', 'kjv_envy:ev:pl', 'wrath:pl', 'strife:pl', 'kjv_backbite:ev:pl', 'kjv_whispering_gossip_corinthians:pl', 'kjv_swell_pride_corinthians:pl', 'kjv_tumult:pl'], '12:21': ['my/god among you i:a humble:caus:fu', 'already sin:perf', 'unclean:ev and kjv_fornication and lascivious:ev', 'repent:neg:perf'], '13:1': ['third time', 'two or three witness:pl', 'each word kjv_establish:psv:fu'], '13:2': ['before to you tell:pa and before tell:pr', 'second time present', 'if i again come:pr i spare:neg:fu'], '13:3': ['kjv_christ_title in i speak:cv', 'towards you weak be:neg:pr', 'in you strong'], '13:4': ['through weak:ev kjv_crucify:psv:pa', 'wesg also in he weak', 'wesg with he by god power towards you live:fu'], '13:5': ['yourselves whether in faith', 'yourselves test:imp', 'kjv_jesus_matthew kjv_christ_title in you', 'except you kjv_reprobate_test_corinthians'], '13:6': ['i trust:pr', 'wesg kjv_reprobate_test_corinthians be:neg:pr'], '13:7': ['i to god pray:pr', 'not that wesg approve:psv:adj appear:should but that you honest thing', 'as kjv_reprobate_test_corinthians'], '13:8': ['against truth nothing do:can but for truth'], '13:9': ['when wesg weak and you strong', 'your/perfection'], '13:10': ['absence be:cv write:pr', 'sharpness use:should', 'for kjv_edify_romans:ev and not for destroy:ev'], '13:11': ['farewell', 'perfect be:imp', 'good comfort:ev have:imp', 'one_num mind', 'in peace live:imp', 'god of love and peace'], '13:12': ['each other with holy kiss'], '13:13': ['all saint:pl'], '13:14': ['kjv_christ_title grace and god love', 'holy spirit kjv_communion_spirit_corinthians', 'with you all be:opt amen']}
  for ref,parts in anchors.items():
   for part in parts:self.assertIn(part,cases[ref.replace(':','-')]['analysis'])
  self.assertEqual(cases['12-2']['analysis'].count('i tell:neg:can'),2)
  self.assertIn('above twelve and two',cases['12-2']['analysis'])
  self.assertEqual(cases['12-7']['analysis'].count('above measure'),2)
  self.assertIn('mypl/grace',cases['12-9']['analysis'])
  self.assertIn('mypl/strength',cases['12-9']['analysis'])
  self.assertIn('my/infirmity:pl',cases['12-9']['analysis'])
  self.assertIn('spend:fu and spend:psv:fu',cases['12-15']['analysis'])
  self.assertEqual(cases['12-18']['analysis'].count('we:du'),2)
  self.assertIn('two or three witness:pl',cases['13-1']['analysis'])
  self.assertIn('not that wesg approve:psv:adj appear:should but that you',cases['13-7']['analysis'])
  self.assertIn('one_num mind',cases['13-11']['analysis'])
  self.assertIn('kjv_christ_title grace and god love and holy spirit kjv_communion_spirit_corinthians',cases['13-14']['analysis'])
  self.assertNotIn('father',cases['13-14']['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),5)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
