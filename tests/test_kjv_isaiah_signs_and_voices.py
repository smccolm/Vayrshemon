import unittest,re
from tools.kjv_archive import load_register,read
class IsaiahSignsVoicesTests(unittest.TestCase):
 def test_king_divinity_corporate_song_and_difficult_readings(self):
  prior,_=load_register('0.10-kjv.130');lang,manifest=load_register('0.10-kjv.131')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('isaiah-'):c for c in read(lang.folder/'isaiah-signs-imperial-boast-and-corporate-song-cases.json')};self.assertEqual(len(cases),124)
  voices={k:set() for k in ['ipl','wesg','mypl']}
  for ref,c in cases.items():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'one','fair','sound','substance','want','please','count','host','peep','league'}&set(out['keys']))
   self.assertNotRegex(c['analysis'],r'(?<![a-z_])(?:wepl|they:du|you:du|we:du|ourone|iplself)(?![a-z_])')
   for k in voices:
    if re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis']):voices[k].add(ref)
  self.assertEqual(voices['ipl'],set('10-4 10-6 10-12 12-1 12-2'.split()))
  self.assertEqual(voices['wesg'],set('7-6 8-10 9-6 9-10'.split()))
  self.assertEqual(voices['mypl'],set('10-5 10-6 10-24 10-25 11-9 12-2'.split()))
  for ref,parts in {
   '7-2':['in kjv_league'],'7-4':['two tail:pl'],'7-6':['wesg against kjv_judah','kjv_tabeal'],
   '7-8':['three+twenty and five'],'7-12':['i ask:neg:fu'],
   '7-14':['virgin conceive:fu','kjv_immanuel'],'7-18':['kjv_fly_insect','kjv_bee','whistle:fu'],
   '7-20':['hair:a of foot:pl'],'7-21':['two sheep:a'],
   '7-23':['thousand kjv_vine:pl at thousand silver piece:pl'],
   '7-25':['fear of briar:pl and thorn:pl there come:neg:fu'],
   '8-1':['great scroll:a','kjv_mahershalalhashbaz'],'8-2':['kjv_uriah_isaiah_witness','kjv_zechariah_jeberechiah'],
   '8-3':['woman prophet'],'8-4':['my/father and my/mother'],'8-7':['his/kjv_water_channel:pl'],
   '8-10':['god with wesg'],'8-14':['kjv_sanctuary','for trap and for snare'],
   '8-16':['my/disciple:pl'],'8-17':['i upon kjv_lord'],'8-18':['i and child:pl'],
   '8-19':['kjv_peep_chirp:pr and kjv_mutter:pr','for living to dead'],
   '9-1':['lightly kjv_afflict:pa','more kjv_grievous:adv kjv_afflict:pa'],
   '9-3':['joy:a increase:neg:perf'],
   '9-6':['to wesg child bear:psv:pr to wesg son give:psv:pr','mighty god eternal father prince of peace'],
   '9-8':['settle:perf'],'9-10':['wesg with kjv_hew:psv:adj stone:pl'],
   '9-14':['one_num day'],'9-15':['false:ev:pl:a teach:pr'],
   '9-17':['kjv_fatherless and widow:pl mercy:a have:fu'],'9-20':['his/own arm'],
   '10-4':['without ipl'],'10-6':['ipl he:a'],'10-7':['he thus mean:neg:pr'],
   '10-11':['i as i to kjv_samaria'],'10-12':['ipl fruit:a'],
   '10-13':['i it:a do:perf','i kjv_discreet'],'10-14':['i all earth:a','kjv_peep_chirp:pa'],
   '10-18':['kjv_standard_bearer'],'10-20':['no more again rely:fu'],
   '10-24':['mypl/people'],'10-25':['mypl/anger'],'10-27':['because of anoint:ev'],
   '10-28':['his/kjv_baggage:a'],'10-34':['by mighty fall:fu'],
   '11-3':['quick understand:ev'],'11-5':['his/kjv_kidney:pl'],
   '11-6':['wolf also with kjv_lamb','leopard with kjv_kid'],
   '11-7':['bear_animal','lion straw:a'],'11-8':['kjv_cockatrice'],
   '11-9':['mypl/holy mountain'],'11-11':['second:ord time'],
   '11-12':['four corner:pl'],'11-14':['kjv_edom and kjv_moab'],
   '11-15':['seven stream:pl','dry shoe:pl'],
   '12-1':['ipl thee:a praise:fu'],'12-2':['ipl trust:fu','kjv_lord kjv_jehovah','he also mypl/salvation'],
  }.items():
   for part in parts:self.assertIn(part,cases[ref]['analysis'],(ref,part))
  self.assertEqual(cases['8-9']['analysis'].count('you to piece:pl break:psv:fu'),3)
  self.assertEqual(cases['8-9']['analysis'].count('yourselves:a kjv_gird:imp'),2)
  refrain='for all this his/anger away turn:psv:neg:pr but his/hand still out stretch:psv:pr'
  for ref in('9-12','9-17','9-21','10-4'):self.assertIn(refrain,cases[ref]['analysis'])
  additions=set(lang.lexicon)-set(prior.lexicon);self.assertEqual(len(additions),19)
  self.assertEqual(sum(lang.lexicon[k]['pos']=='proper' for k in additions),14)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
