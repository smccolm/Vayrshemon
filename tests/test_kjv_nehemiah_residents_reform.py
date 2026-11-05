import unittest
from tools.kjv_archive import load_register,read
class NehemiahResidentsReformTests(unittest.TestCase):
 def test_counted_groups_named_relations_and_coercive_personal_voice(self):
  prior,_=load_register('0.10-kjv.99');lang,manifest=load_register('0.10-kjv.100')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'nehemiah-residents-reform-cases.json')};self.assertEqual(len(cases),114)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text']);self.assertNotIn('ipl',out['keys'])
  def a(r):return cases['nehemiah-'+r]['analysis']
  for r,parts in {
   '11-1':['one_num of ten','nine part:pl'], '11-2':['willingly themselves:a'],
   '11-6':['four+hundred and six+ten and eight'], '11-8':['nine+hundred and twenty and eight'],
   '11-9':['kjv_judah_senuah','second over city'], '11-14':['son of some of great man:pl'],
   '11-18':['two+hundred and four+twenty and four'], '11-19':['hundred and seven+ten and two'],
   '11-24':['king:poss hand','affair:pl'], '11-26':['kjv_jeshua_town'],
   '12-4':['kjv_ginnetho_return_priest'], '12-11':['kjv_jonathan_joiada'],
   '12-17':['of kjv_miniamin_priest_house; of kjv_moadiah_priest_house'],
   '12-23':['kjv_johanan_eliashib_priest'], '12-24':['kjv_jeshua_kadmiel son of kjv_kadmiel','watch:ev opposite watch:ev'],
   '12-31':['two great company:pl:a','one_num on kjv_right_side'],
   '12-32':['half of prince:pl'], '12-38':['half of people'], '12-40':['half of ruler:pl'],
   '12-43':['wife:pl also and child:pl'], '12-44':['who attend:pa'],
   '13-6':['kjv_artaxerxes king of kjv_babylon','thirty and two:ord','permission:a'],
   '13-8':['house kjv_goods','forth cast:pa'], '13-10':['give:psv:neg:pp','each to his/field'],
   '13-18':['upon wesg'], '13-20':['once or twice'], '13-21':['i hand:pl:a upon you:pl lay:fu'],
   '13-24':['half in speech of kjv_ashdod'], '13-25':['some of they:a strike:pa','their/hair:a off pluck:pa','swear:caus:pa'],
   '13-27':['wesg to you:pl','ourone/god'], '13-29':['they:a remember:imp'],
   '13-31':['i:a remember:imp my/god:excl for good'],
  }.items():
   for p in parts:self.assertIn(p,a(r))
  self.assertEqual(a('11-25').count('its/village:pl'),3)
  self.assertEqual(a('12-35').count('son of'),6)
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),203)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-99')
if __name__=='__main__':unittest.main()
