import unittest
from tools.kjv_archive import load_register,read

class PsalmLawLifePetitionTests(unittest.TestCase):
 def test_law_vocabulary_life_identity_and_historical_senses(self):
  prior,_=load_register('0.10-kjv.117');lang,manifest=load_register('0.10-kjv.118')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id']:c for c in read(lang.folder/'psalms-law-life-embodied-petition-cases.json')};self.assertEqual(len(cases),226)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'ipl','mypl','wepl','right','sound','quick','count','consume','prevent','render','subject','please'}&set(out['keys']))
  for ref,parts in {
   '116-3':['pain:pl of kjv_hell'],'116-5':['ourone/god'],'116-16':['son of thine kjv_handmaid','kjv_binding_band:pl:a'],
   '117-2':['kjv_kindness great to wesg'],'118-13':['thou hard','but kjv_lord'],
   '118-15':['tent:pl of kjv_righteous'],'118-22':['head stone of corner'],
   '118-23':['our/eye:pl'],'118-24':['wesg in it rejoice:fu'],'118-26':['wesg you:pl:a'],
   '118-27':['wesg light:a','kjv_cord:pl','horn:pl of altar'],
   '119-4':['wesg:a','kjv_precept:pl:a'],'119-7':['learn:fp'],
   '119-25':['dust kjv_cleave_adhere:pr','quicken:imp'],'119-28':['heaviness melt:pr'],
   '119-31':['kjv_cleave_adhere:perf'],'119-32':['heart:a large:caus:fu'],
   '119-36':['bend:imp','not to kjv_covetousness'],'119-50':['quicken:perf'],
   '119-57':['my/part'],'119-60':['haste:a','delay:neg:pa'],'119-61':['band:pl of wicked'],
   '119-69':['kjv_lie_false:a forge:perf'],'119-70':['fat as kjv_grease'],
   '119-72':['thousand:pl of gold and silver'],'119-75':['kjv_just_fair','faithful:ev'],
   '119-80':['heart whole'],'119-83':['kjv_bottle in smoke'],'119-87':['almost','devour:pp'],
   '119-92':['unless','be:pp','perish:perf:should'],'119-97':['love:pr:excl'],
   '119-103':['taste:ev','honey','be:pr:excl'],'119-108':['free willing kjv_offering:pl:a of my/mouth'],
   '119-109':['soul always in my/hand'],'119-119':['like kjv_dross'],
   '119-128':['all thing:pl kjv_just_fair'],'119-132':['by habit'],
   '119-136':['river:pl of water:pl'],'119-147':['before kjv_dawn of morning come:pa'],
   '119-148':['before night kjv_watch_period:pl'],'119-149':['thy/judge:ev quicken:imp'],
   '119-152':['kjv_found_base:perf'],'119-156':['thy/judge:ev:pl quicken:imp'],
   '119-164':['seven time:pl day'],'119-165':['kjv_stumble:caus:fu'],
   '119-175':['my/soul live:opt'],'119-176':['astray like lost sheep','seek:imp','forget:neg:pr'],
  }.items():
   for part in parts:self.assertIn(part,cases['psalms-'+ref]['analysis'],(ref,part))
  for a,b in [('116-14','116-18'),('118-1','118-29')]:self.assertEqual(cases['psalms-'+a]['expectedText'],cases['psalms-'+b]['expectedText'])
  legal=['law','testimony','kjv_precept','kjv_statute','command','judge']
  self.assertEqual(len({lang.lexicon[k]['form'] for k in legal}),len(legal))
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_grease','kjv_dross'})
  for key in ('kjv_grease','kjv_dross'):
   e=lang.lexicon[key];self.assertEqual(e['form'],''.join(lang.lexicon[k]['form'] for k in e['derivationKeys']))
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
