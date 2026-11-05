import unittest,re
from tools.kjv_archive import load_register,read
class JeremiahContestedPromisesTests(unittest.TestCase):
 def test_personal_body_claimed_divinity_and_negatives(self):
  prior,_=load_register('0.10-kjv.144');lang,manifest=load_register('0.10-kjv.145')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('jeremiah-'):c for c in read(lang.folder/'jeremiah-embodied-messenger-and-contested-promises-cases.json')};self.assertEqual(len(cases),91)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertNotIn(':du',c['analysis']);self.assertFalse({'one','host','bow','former','dragon','snuff','ghost','kjv_principal_amount'}&set(result['keys']))
  for k,refs in {'i':'13-1 13-2 13-3 13-5 13-6 13-7 13-8 14-11 14-13 14-14 14-18 15-1 15-10 15-15 15-16 15-17 15-18 16-1','wesg':'13-12 14-7 14-9 14-19 14-20 14-21 14-22 15-2 16-10','ourone':'14-7 14-20 14-22 16-10 16-19','wepl':'','iplself':''}.items():
   self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in {
   '13-1':['linen kjv_girdle:a','in water put:neg:imp'],'13-6':['kjv_lord to i','ipl thee:a there hide:inf command:pa'],
   '13-7':['kjv_dig:pa','for nothing profitable'],'13-11':['kjv_cleave_adhere:caus:perf','hear:neg:pa'],
   '13-12':['wesg surely'],'13-13':['kjv_david/throne','with drunkenness fill:fu'],
   '13-14':['each against other','pity:a have:neg:fu','spare:neg:fu','mercy:a have:neg:fu'],
   '13-17':['my/soul','my/eye','with tear:pl'],'13-18':['principal authority:pl'],
   '13-22':['upon ipl','thy/heel:pl bare'],'13-23':['kjv_ethiopian his/skin:a','leopard his/spot:pl'],
   '13-27':['kjv_lewdness','when it once be:fu'],'14-1':['kjv_dearth'],
   '14-4':['ground crack:psv:pr','plough:ag human:pl'],'14-5':['hind','child:a bear:pa'],
   '14-6':['wind:a smell:pa','kjv_dragon_creature:pl'],'14-7':['ourone/kjv_backslide:ev:pl'],
   '14-9':['save:neg:can','wesg:a leave:neg:imp'],'14-11':['pray:neg:imp'],
   '14-12':['hear:neg:fu','accept:neg:fu','kjv_pestilence consume:fu'],
   '14-13':['then i say:pa','kjv_prophet:pl to they say:pr','ipl to you assure:psv:adj peace:a give:fu'],
   '14-14':['send:neg:pa','command:neg:perf','speak:neg:pa','kjv_divine:ev:a'],
   '14-17':['my/eye:pl with tear:pl','cease:neg:opt'],'14-19':['thy/soul kjv_zion:a loathe:perf','thou wesg:a strike:perf'],
   '14-21':['kjv_abhor:neg:imp','disgrace:neg:imp','break:neg:imp'],
   '15-1':['kjv_moses and kjv_samuel before ipl','mypl/mind','be:neg:can'],
   '15-3':['four kind:pl:a','dog:pl to rend:inf'],'15-4':['kjv_manasseh_hezekiah son of kjv_hezekiah_ahaz'],
   '15-6':['ipl with repent:ev weary'],'15-7':['kjv_winnowing_fan','child:pl kjv_bereave:fu'],
   '15-8':['mother of young man:pl','upon it suddenly fall:caus:perf'],
   '15-9':['seven:a bear:perf','spirit:a up give:perf','while it still day'],
   '15-10':['my/mother','on kjv_usury lend:neg:perf'],'15-12':['iron kjv_north:adj iron:a and steel:a'],
   '15-14':['mypl/anger kjv_kindle_fire:psv:pr','upon you burn:fu'],
   '15-15':['thy/kjv_longsuffering'],'15-16':['i they:a eat:pa','god of army:pl'],
   '15-17':['nor rejoice:neg:pa','i alone sit:pa'],'15-18':['as kjv_lie_false:ag','as water:pl which fail:pr'],
   '15-19':['they to thee return:opt','thou to they return:neg:imp'],
   '16-3':['mother:pl who they:a bear:pa','father:pl who they:a beget:pa'],
   '16-4':['bury:psv:neg:fu','carcass:pl food'],'16-5':['mypl/peace:a','kjv_lovingkindness'],
   '16-6':['cut:neg:fu','kjv_bald make:neg:fu'],'16-7':['rend:neg:fu','cup:a of comfort:ev'],
   '16-11':['mypl/law:a keep:neg:perf'],'16-12':['each after imagination of his/evil heart'],
   '16-13':['other god:pl:a day and night serve:fu','favour show:neg:fu'],
   '16-14':['no more say:psv:fu','land of egypt'],'16-15':['land of kjv_north','ipl they:a again'],
   '16-18':['first ipl','double recompense:fu'],'16-19':['my/kjv_refuge','ourone/father:pl'],
   '16-21':['at this once','mypl/hand:a and mypl/might:a']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual({r for r,c in cases.items() if 'bear' in lang.compile(c['analysis'])['keys']},{'14-5','15-9','15-10','16-3'})
  self.assertEqual({r for r,c in cases.items() if 'tear' in lang.compile(c['analysis'])['keys']},{'13-17','14-17'})
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_dearth'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
