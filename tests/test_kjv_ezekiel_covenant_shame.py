import unittest,re
from tools.kjv_archive import load_register,read

class EzekielCovenantShameTests(unittest.TestCase):
 def test_rival_revelation_and_covenant_shame(self):
  prior,_=load_register('0.10-kjv.158');lang,manifest=load_register('0.10-kjv.159')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('ezekiel-'):c for c in read(lang.folder/'ezekiel-rival-revelation-and-covenant-shame-cases.json')};self.assertEqual(len(cases),117)
  for c in cases.values():
   r=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],r['text']);self.assertEqual(c['expectedGloss'],r['gloss']);self.assertNotIn('!',r['text']);self.assertNotIn(':du',c['analysis'])
   self.assertFalse({'one','host','bow','ghost','roll','fold','care','plain','right','tear','border','stuff','lock','light','divine','eminent','wax','fashion','fair','meat','worship'}&set(r['keys']))
   for k in ('wesg','wepl','ourone'):self.assertIsNone(re.search(r'(?<![a-z_])'+k+r'(?![a-z_])',c['analysis']))
  for r,parts in {
   '13-2':['out of their/own heart:pl'],
   '13-3':['their/own spirit:a','nothing:a see:perf','woe:excl'],
   '13-4':['fox:pl in dry land:pl'],
   '13-6':['kjv_lord they:a send:neg:perf','other:pl:a hope:caus:perf'],
   '13-7':['ipl speak:neg:perf?'],
   '13-9':['mypl/hand','kjv_assembly of mypl/people be:neg:fu','neither they in write:ev','neither they into land'],
   '13-10':['because even because','peace there be:neg:pa','person wall:a','kjv_untempered_mortar'],
   '13-11':['you oh great hail stone:pl','storm:adj wind it:a rend:fu'],
   '13-14':['its/kjv_foundation kjv_uncover:psv:fu'],
   '13-18':['pillow:pl:a to all kjv_hollow:pl of arm','head of every stature'],
   '13-19':['handful:pl of kjv_barley','piece:pl of bread','die:neg:should','live:neg:should'],
   '13-20':['from your/arm:pl rend:fu','soul:pl:a go:caus:fu'],
   '13-22':['whom ipl sad:caus:neg:perf','return:neg:should'],
   '14-3':['ipl by they at all ask:psv:should?'],
   '14-7':['ipl kjv_lord he:a by iplself answer:fu'],
   '14-9':['ipl kjv_lord that prophet:a deceive:perf'],
   '14-10':['kjv_punishment:a of their/kjv_iniquity endure:fu'],
   '14-14':['three man:pl','kjv_daniel_ezekiel_exemplar','only their/own soul:pl:a'],
   '14-16':['neither son:pl nor daughter:pl:a'],
   '14-18':['they only themselves deliver:psv:fu'],
   '14-20':['neither son nor daughter:a'],
   '14-21':['mypl/four kjv_grievous judgment:pl:a'],
   '14-22':['both son:pl and daughter:pl','about evil which ipl','comfort:psv:fu'],
   '14-23':['without cause all which ipl in it do:perf do:neg:perf'],
   '15-3':['kjv_pin:a of it'],
   '15-4':['both end:pl:a','fitting be:pr?'],
   '15-7':['one_num fire','another fire'],
   '16-3':['thy/birth and thy/kjv_nativity','kjv_canaan_land','kjv_hittite'],
   '16-4':['thy/kjv_navel cut:psv:neg:pa','kjv_supple_wash:inf','salt:psv:neg:pa','nor at all in kjv_swaddlingband:pl'],
   '16-6':['thine/own blood defile:psv:adj','live:imp yes ipl'],
   '16-7':['thy/breast:pl form:psv:pr','clothe:neg:psv:adj and bare'],
   '16-8':['mypl/kjv_skirt_garment:a','thou of ipl become:pa'],
   '16-10':['shoe:pl:a of kjv_badger:pl skin','fine linen kjv_gird:pa','with silk cover:pa'],
   '16-12':['jewel:a on thy/forehead'],
   '16-15':['of he it be:pa'],
   '16-16':['like thing:pl come:neg:fu','neither it so be:fu'],
   '16-17':['image:pl:a of man:pl'],
   '16-19':['mypl/food:a','fine kjv_flour:a and oil:a and honey:a'],
   '16-20':['to devour:psv:inf kjv_sacrifice:perf'],
   '16-21':['mypl/child:pl:a slay:perf'],
   '16-25':['thy/foot:pl:a'],
   '16-26':['kjv_egyptian:pl thy/neighbour:pl great of flesh'],
   '16-27':['thine/ordinary food:a diminish:perf'],
   '16-28':['satisfy:psv:pa:neg:can'],
   '16-30':['kjv_imperious kjv_whoredom:adj woman'],
   '16-31':['as whore be:neg:perf','kjv_wages:a scorn:pr'],
   '16-33':['thy/gift:pl:a to all thy/lover:pl','they:a kjv_hire:pr'],
   '16-34':['thou reward:a give:pr','no reward to thee give:psv:pr'],
   '16-36':['thy/filthy:ev'],
   '16-37':['whom thou love:perf','whom thou hate:perf'],
   '16-40':['with stone:pl kjv_stone_attack:fu'],
   '16-41':['any more no kjv_wages:a give:fu'],
   '16-42':['mypl/fury:a towards thee rest:caus:fu','no more angry be:fu'],
   '16-43':['kjv_lewdness:a above all thine/kjv_abomination:pl do:neg:fu'],
   '16-45':['your/mother kjv_hittite','your/father kjv_amorite'],
   '16-46':['thy/left hand','thy/kjv_right_side hand'],
   '16-49':['pride full:ev of bread','abundance of idle:ev','neither she hand:a of poor and kjv_needy'],
   '16-51':['half:a of thy/sin:pl','kjv_justify:perf'],
   '16-52':['they more kjv_righteous than thou'],
   '16-53':['kjv_captivity:a of kjv_sodom','kjv_captivity:a of kjv_samaria'],
   '16-55':['their/former estate','your/former estate'],
   '16-57':['daughter:pl of kjv_syria'],
   '16-60':['nevertheless ipl','eternal kjv_covenant:a kjv_establish:fu'],
   '16-61':['for daughter:pl give:fu but not by thy/kjv_covenant'],
   '16-63':['never thy/mouth:a','kjv_appease:psv:pr']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(cases['13-20']['analysis'].count('fly:caus:inf'),2)
  self.assertEqual(cases['16-6']['analysis'].count('live:imp'),2)
  self.assertEqual(cases['16-23']['analysis'].count('woe:excl'),2)
  self.assertNotIn('three',cases['14-20']['analysis'])
  self.assertEqual(len(set(lang.lexicon)-set(prior.lexicon)),8)
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
