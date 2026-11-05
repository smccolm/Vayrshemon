import unittest,re
from tools.kjv_archive import load_register,read

class EzekielVisionarySelfTests(unittest.TestCase):
 def test_visionary_and_divine_self_with_exact_signs(self):
  prior,_=load_register('0.10-kjv.156');lang,manifest=load_register('0.10-kjv.157')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('ezekiel-'):c for c in read(lang.folder/'ezekiel-visionary-and-divine-plural-self-cases.json')};self.assertEqual(len(cases),140)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text']);self.assertNotIn(':du',c['analysis'])
   self.assertFalse({'one','host','bow','ghost','roll','fold','care','plain','right','tear'}&set(r['keys']))
   for k in ('wesg','wepl','ourone','iplself'):self.assertIsNone(re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis']))
  for r,parts in {
   '1-1':['thirty:ord year','four:ord month','five:ord day','i vision:pl:a'],
   '1-2':['five:ord year','kjv_jehoiachin'],
   '1-3':['kjv_ezekiel priest son of kjv_buzi'],
   '1-5':['four living creature:pl','likeness:a of man'],
   '1-6':['each four face:pl:a','each four wing:pl:a'],
   '1-7':['kjv_sole','kjv_polish_surface:psv:adj kjv_brass'],
   '1-10':['kjv_right_side','ox on left side','kjv_eagle'],
   '1-11':['two wing:pl of each','two their/body:pl:a'],
   '1-15':['one_num wheel','his/four face:pl'],
   '1-16':['four one_num likeness:a','wheel in middle of wheel'],
   '1-20':['their/spirit','spirit of living creature in wheel:pl'],
   '1-24':['noise of army'],
   '1-26':['likeness of throne','likeness as appear:ev of man'],
   '1-28':['kjv_bow which in cloud','voice:a of person'],
   '2-1':['he to i say:pa','ipl to thee speak:fu'],
   '2-9':['scroll of book'],
   '2-10':['within and without write:psv:pa'],
   '3-2':['he i:a that scroll:a eat:caus:pa'],
   '3-3':['thy/belly:a eat:caus:imp','honey for sweet:ev'],
   '3-6':['if ipl thee:a to they send:pp','listen:pp:should'],
   '3-9':['kjv_adamant more hard than flint'],
   '3-14':['heat of my/spirit','hand of kjv_lord upon i'],
   '3-15':['kjv_telabib','seven day:pl'],
   '3-16':['end of seven day:pl'],
   '3-18':['his/blood:a ipl at thine/hand require:fu'],
   '3-20':['ipl kjv_stumblingblock:a','remember:psv:neg:fu'],
   '3-21':['sin:neg:pr and he sin:neg:pr'],
   '3-24':['spirit into i enter:pa','within thine/house shut:imp'],
   '3-26':['ipl cause:fu that thy/tongue','rebuke:ag be:neg:fu'],
   '4-2':['kjv_battering_ram:pl:a'],
   '4-3':['iron kjv_pan:a','between thee and city'],
   '4-5':['three+hundred and seven+twelve and six day:pl'],
   '4-6':['thy/kjv_right_side','forty day:pl','each day:a for one_num year'],
   '4-9':['kjv_millet:a and kjv_fitches:a','one_num vessel'],
   '4-10':['twenty kjv_shekel:pl each day'],
   '4-11':['kjv_sixth_share of kjv_hin'],
   '4-14':['i say:pa','my/soul kjv_pollute_sacred:psv:neg:perf'],
   '4-15':['ipl kjv_cow kjv_dung:a for man kjv_dung'],
   '4-16':['with worry'],
   '4-17':['lack:may'],
   '5-1':['kjv_razor:a of barber'],
   '5-8':['ipl even ipl'],
   '5-11':['as ipl live:pr','mypl/eye'],
   '5-13':['ipl comfort:psv:fu'],
   '6-3':['ipl even ipl'],
   '6-9':['ipl with their/whore:adj heart','break:psv:pr'],
   '6-14':['kjv_diblath'],
   '7-7':['morning to thee','not sound:ev again of mountain:pl'],
   '7-9':['ipl kjv_lord who strike:pr'],
   '7-20':['his/kjv_ornament','therefore ipl it:a'],
   '7-26':['kjv_calamity upon kjv_calamity'],
   '7-27':['their/desert:pl']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  for r in ('5-2','5-12'):self.assertEqual(cases[r]['analysis'].count('kjv_third_share'),3)
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),12)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
