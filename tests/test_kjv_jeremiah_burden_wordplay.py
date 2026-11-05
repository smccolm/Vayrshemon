import unittest,re
from tools.kjv_archive import load_register,read
class JeremiahBurdenWordplayTests(unittest.TestCase):
 def test_reflexive_wordplay_and_real_human_dual(self):
  prior,_=load_register('0.10-kjv.146');lang,manifest=load_register('0.10-kjv.147')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-plural-self-oaths-and-burden-wordplay-cases.json')};self.assertEqual(len(cases),94)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','host','bow','former','dragon','snuff','ghost','desert','right','light'}&set(result['keys']))
  for k,refs in {'i':'21-2 22-14 23-9 23-25 24-1 24-3 24-4','wesg':'21-2 21-13','ourone':'21-13 23-6 23-36','wepl':'','iplself':'21-5 22-5','you:du':'22-26'}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  self.assertEqual({r for r,c in cases.items() if ':du' in c['analysis']},{'22-26'})
  for r,parts in {
   '21-1':['kjv_pashur_melchiah:a son of kjv_melchiah_pashur','kjv_zephaniah_maaseiah'],
   '21-2':['for wesg','i thee:a pray:pr'],'21-5':['ipl iplself against you fight:fu'],
   '21-7':['spare:neg:fu','pity:a have:neg:fu','mercy:a have:neg:fu'],
   '21-9':['his/life to he for prey'],'21-10':['for evil and not for good'],
   '21-13':['ourone/dwell:ev place:pl'],'22-3':['kjv_fatherless','shed:neg:imp'],
   '22-4':['king:pl enter:fu','he and his/servant:pl'],'22-5':['ipl by iplself swear:pr'],
   '22-10':['country:a see:neg:fu'],'22-11':['kjv_shallum_josiah'],'22-13':['without kjv_wages'],
   '22-14':['i for i wide house:a','kjv_vermilion'],'22-15':['thyself in kjv_cedar close:pr'],
   '22-16':['this ipl:a know:inf'],'22-18':['ah my/brother:excl','ah his/glory:excl'],
   '22-20':['from passage:pl'],'22-21':['thou say:pa ipl hear:neg:fu'],
   '22-23':['how gracious'],'22-24':['mypl/kjv_right_side hand'],
   '22-26':['thy/mother:a who thee:a bear:pa','you:du bear:psv:neg:pa','you:du die:fu'],
   '22-28':['he and his/seed'],'22-29':['earth earth earth'],
   '22-30':['without child write:imp','no human of his/seed prosper:fu'],
   '23-2':['visit:neg:perf','upon you visit:fu'],'23-3':['ipl they:a drive:perf','sheepfold:pl'],
   '23-4':['kjv_dismay:psv:neg:fu','lack:adj be:neg:fu'],'23-5':['kjv_righteous branch:a'],
   '23-6':['kjv_lord ourone/kjv_righteousness'],'23-9':['my/heart within i','my/bone:pl'],
   '23-10':['their/force fitting be:neg:pr'],'23-13':['mypl/people:a kjv_israel err:caus:pa'],
   '23-15':['kjv_gall_bitter drink:caus:fu'],'23-16':['not out of mouth of kjv_lord'],
   '23-21':['send:neg:perf','speak:neg:perf'],'23-22':['stand:pp','hear:caus:pp','turn:pp:should'],
   '23-23':['ipl god at hand','not god far off'],'23-24':['heaven:a and earth:a fill:neg:pr'],
   '23-25':['i dream:perf i dream:perf'],'23-28':['he dream:a tell:opt','kjv_chaff to wheat'],
   '23-32':['their/lightweight:ev','benefit:neg:fu'],'23-33':['what kjv_burden_oracle'],
   '23-36':['kjv_burden_oracle:a','every human/word his/burden','ourone/god'],
   '23-38':['you kjv_burden_oracle of kjv_lord say:neg:fu'],
   '23-39':['ipl even ipl','to full forget:fu'],'23-40':['forget:psv:neg:fu'],
   '24-1':['two kjv_basket:pl','kjv_jeconiah:a son of kjv_jehoiakim'],
   '24-2':['one_num kjv_basket','first ripe','other kjv_basket'],
   '24-5':['for their/good send:perf'],'24-6':['pull:neg:fu','pluck:neg:fu'],
   '24-7':['they mypl/people be:fu','ipl their/god be:fu'],
   '24-8':['land of egypt dwell:pr'],'24-9':['kjv_reproach and proverb and taunt and curse']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(lang.lexicon['burden']['form'],lang.lexicon['kjv_burden_oracle']['form'])
  self.assertEqual(lang.word('burden:a')[0],lang.word('kjv_burden_oracle:a')[0])
  self.assertNotEqual(lang.word('burden:a')[1],lang.word('kjv_burden_oracle:a')[1])
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_vermilion','kjv_burden_oracle','kjv_pashur_melchiah','kjv_melchiah_pashur','kjv_zephaniah_maaseiah','kjv_maaseiah_zephaniah','kjv_nebuchadrezzar','kjv_coniah_jehoiakim'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
