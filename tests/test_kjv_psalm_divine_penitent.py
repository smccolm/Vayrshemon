import unittest
from tools.kjv_archive import load_register,read
class PsalmDivinePenitentTests(unittest.TestCase):
 def test_divine_self_individual_confession_dual_and_physical_members(self):
  prior,_=load_register('0.10-kjv.111');lang,manifest=load_register('0.10-kjv.112')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'psalms-divine-penitent-cases.json')};self.assertEqual(len(cases),171)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'just','host','consume','render','conversation','mark','kjv_selah','quick','prevent','hell'}&set(out['keys']))
  for ref,parts in {
   '49-4':['my/riddle:a'], '49-8':['precious','for ever cease'], '49-12':['dwell:neg'], '49-20':['understand:neg'],
   '50-3':['ourone/god'], '50-5':['mypl/saint','to ipl','with ipl'],
   '50-7':['ipl god even thy/god'], '50-8':['thy/kjv_burnt_sacrifice','be:perf:inf','rebuke:neg'],
   '50-10':['kjv_livestock upon thousand hill:pl'], '50-12':['if ipl hungry be:pa','ipl would thee:a tell:neg:pr'],
   '50-13':['ipl flesh:a','drink:fu?'], '50-16':['god say:pr','mypl/kjv_statute','mypl/kjv_covenant'],
   '50-21':['ipl fully such one as thyself'], '50-23':['his/behaviour:a fittingly','ipl salvation:a'],
   '51-4':['against thee thee only i sin:perf','kjv_justify_judicial','innocent'],
   '51-5':['my/mother i:a conceive'], '51-11':['thy/holy spirit:a from i take:neg:imp'],
   '51-12':['thy/willing spirit'], '51-14':['kjv_bloodguilt'],
   '51-16':['else i it:a would give:pr','delight:neg'], '51-19':['whole kjv_burnt_sacrifice','kjv_bullock'],
   '52-3':['kjv_lie_false'], '53-1':['kjv_abomination:adj kjv_iniquity'],
   '53-2':['god from heaven'], '53-3':['back go:perf','not one_num'],
   '53-5':['where no fear','bone:pl','against thee kjv_encamp'],
   '55-6':['have:opt:excl','fly:pr would'], '55-12':['bear:perf:inf can','hide:perf:inf would'],
   '55-14':['we:du','in company walk:pa'], '55-15':['alive into kjv_hell'],
   '55-19':['no change:pl:a'], '55-20':['his/kjv_covenant:a break:perf'],
   '55-21':['out pull:psv sword:pl'], '55-23':['half their/day:pl'],
   '56-4':['what flesh'], '56-11':['what man'], '56-8':['kjv_number:pr','thy/kjv_bottle'],
   '56-12':['thy/vow:pl upon i'], '57-1':['kjv_refuge:a for myself'],
   '57-4':['lie:pr','kjv_spear:pl'], '58-3':['born:psv:pr','kjv_lie_false'],
   '58-8':['kjv_untimely_birth'], '58-9':['both living and in his/wrath'],
   '58-10':['in blood of wicked wash:fu'], '59-7':['kjv_belch'],
   '59-9':['his/strength'], '59-10':['before i go:fu'],
   '59-11':['slay:neg:imp','ourone/kjv_shield_armour'], '59-13':['destroy:imp','that they be:neg:pr'],
   '59-14':['return:opt'], '59-17':['my/strength:excl'],
   '60-1':['wesg:a off cast:perf','wepl:a scatter:perf','to wesg again turn:imp'],
   '60-3':['wepl:a wine:a of astonish:ev'], '60-5':['i:a hear:imp'],
   '60-6':['god in his/holy:ev speak:perf','ipl rejoice:fu','ipl kjv_shechem'],
   '60-7':['of ipl','mypl/head','mypl/kjv_lawgiver'],
   '60-8':['mypl/kjv_washpot','ipl mypl/shoe:a','because of ipl triumph:imp'],
   '60-9':['who i:a'], '60-10':['wesg:a off cast:pp','our/army:pl'],
   '60-11':['to wesg'], '60-12':['wepl with courage','ourone/enemy:pl'],
  }.items():
   for p in parts:self.assertIn(p,cases['psalms-'+ref]['analysis'])
  self.assertEqual(cases['psalms-57-5']['analysis'],cases['psalms-57-11']['analysis'])
  for k,c in cases.items():
   if k.startswith('psalms-51-'):self.assertNotIn('ipl',lang.compile(c['analysis'])['keys'])
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),5)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-111')
if __name__=='__main__':unittest.main()
