import unittest
from tools.kjv_archive import load_register,read
class PsalmWorshipAgeingTests(unittest.TestCase):
 def test_personal_voice_memory_members_and_unharmonized_readings(self):
  prior,_=load_register('0.10-kjv.112');lang,manifest=load_register('0.10-kjv.113')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'psalms-worship-ageing-cases.json')};self.assertEqual(len(cases),201)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'host','consume','render','conversation','mark','kjv_selah','flourish','spring','issue','light'}&set(out['keys']))
  for ref,parts in {
   '61-2':['i to thee cry:fu','more high than i'], '61-6':['king:poss life','many generation:pl'],
   '62-2':['i greatly move:psv:neg:fu'], '62-6':['i move:psv:neg:fu'],
   '62-8':['for wesg'], '62-9':['kjv_lie_false','more lightweight than vanity'],
   '62-11':['god once speak:perf','twice i this:a hear:perf'],
   '63-1':['my/flesh for thee kjv_yearn:pr'], '63-6':['night kjv_watch_period:pl'],
   '63-8':['closely after thee','kjv_right_side'], '63-9':['more low part:pl'], '63-10':['fox:pl'],
   '64-3':['kjv_whet:pr','bitter word:pl'], '64-8':['their/own tongue:a upon themselves fall:caus:fu'],
   '65-1':['kjv_sion_psalm'], '65-3':['against i','ourone/transgress'],
   '65-4':['wesg with goodness'], '65-5':['wesg:a answer','ourone/salvation'],
   '65-10':['kjv_field_ridge','kjv_furrow','its/grow:ev'], '65-11':['as crown adorn'],
   '66-6':['they through flood on foot','there wesg in he rejoice'],
   '66-9':['ourone/soul','our/foot:pl'], '66-10':['wesg:a prove','wesg:a try'],
   '66-11':['wepl:a into kjv_net','our/kjv_loins:pl'],
   '66-12':['over our/head:pl','wepl through fire','wepl:a out into rich'],
   '66-13':['i into thy/house','i to thee my/vow:pl'],
   '66-18':['if i','hear:neg:fu'], '66-19':['but truly god i:a hear:perf'],
   '67-1':['wesg:a bless','upon wesg shine'], '67-6':['ourone/own god wesg:a'],
   '68-4':['kjv_jah'], '68-12':['she who at home'], '68-13':['kjv_pot:pl lie:perf'],
   '68-14':['kjv_salmon_hill'], '68-17':['twenty+thousand','thousand:pl of angel:pl'],
   '68-18':['gift:pl:a for man:pl receive:perf'], '68-20':['escape:ev:pl from death'],
   '68-22':['lord say:pa ipl','ipl mypl/people'], '68-24':['my/god my/king'],
   '68-28':['for wesg'], '69-4':['what i away take:neg:pa restore:pa'],
   '69-5':['my/foolish:ev','my/sin:pl'], '69-9':['kjv_zeal','i:a up eat:perf'],
   '69-10':['kjv_fast:ev'], '69-21':['kjv_gall_bitter','vinegar'],
   '69-22':['kjv_welfare be:perf:inf should'], '69-25':['their/dwelling','their/tent:pl'],
   '69-27':['kjv_iniquity:a to their/kjv_iniquity add:imp'], '69-28':['book of living erase:psv:opt'],
   '70-3':['ah:excl ah:excl'], '71-6':['my/mother:poss kjv_bowels'],
   '71-9':['time of old age','my/strength fail'], '71-11':['say:cv god he:a forsake:perf'],
   '71-18':['i old','my/head grey','this generation'], '71-20':['again quicken:fu'],
   '71-22':['kjv_holy_one'], '72-1':['king:poss son'], '72-7':['thrive:fu'],
   '72-10':['kjv_sheba and kjv_seba'], '72-13':['soul:pl:a'], '72-14':['their/soul:a'],
   '72-16':['kjv_handful of corn','grow:fu like grass'], '72-20':['kjv_david son of kjv_jesse end:perf'],
  }.items():
   for p in parts:self.assertIn(p,cases['psalms-'+ref]['analysis'])
  self.assertEqual(cases['psalms-67-3']['analysis'],cases['psalms-67-5']['analysis'])
  for k,c in cases.items():
   if k.startswith('psalms-71-'):self.assertNotIn('ipl',lang.compile(c['analysis'])['keys'])
  self.assertNotEqual(lang.lexicon['kjv_salmon_hill']['meaning'],lang.lexicon['kjv_salmon']['meaning'])
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),4)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-112')
if __name__=='__main__':unittest.main()
