import unittest,re
from tools.kjv_archive import load_register,read
class IsaiahSentSpeakerTests(unittest.TestCase):
 def test_named_speakers_comparative_dual_and_source_tensions(self):
  prior,_=load_register('0.10-kjv.137');lang,manifest=load_register('0.10-kjv.138')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id'].removeprefix('isaiah-'):c for c in read(lang.folder/'isaiah-self-oath-and-sent-speaker-cases.json')};self.assertEqual(len(cases),101)
  for c in cases.values():
   result=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],result['text']);self.assertEqual(c['expectedGloss'],result['gloss']);self.assertNotIn('!',result['text'])
   self.assertFalse({'one','plain','hell','substance','rose','dumb','count','host','fan','profit','meal','quarter','kjv_nebo','kjv_sabeans_job'}&set(result['keys']))
  expected={'i':'45-24 49-20','iplself':'45-23','wesg':'','wepl':'','ourone':'47-4','we:du':'46-5'}
  for k,refs in expected.items():self.assertEqual({r for r,c in cases.items() if re.search(r'(?<![a-z_])'+re.escape(k)+r'(?![a-z_])',c['analysis'])},set(refs.split()))
  for r,parts in{
   '45-1':['two kjv_door_leaf:pl','kjv_cyrus'],
   '45-4':['kjv_surname:perf','thou ipl:a know:neg:perf'],
   '45-7':['light:a form:pr','darkness:a create:pr','peace:a make:pr','evil:a create:pr'],
   '45-9':['kjv_potsherd'],'45-11':['you ipl:a command:imp'],
   '45-12':['ipl even mypl/hand:pl'],'45-14':['they of thee be:fu','in chain:pl'],
   '45-15':['thyself:a hide:pr'],'45-19':['speak:neg:perf','kjv_right_conduct'],
   '45-23':['by iplself swear:perf','every knee','every tongue'],
   '45-24':['human say:fu','i kjv_righteousness:a'],
   '46-1':['kjv_bel','kjv_nebo_god','your/kjv_baggage'],
   '46-3':['by ipl from belly carry:psv:pr'],
   '46-5':['we:du like be:may'],'46-7':['human to he cry:fu'],
   '46-9':['former thing:pl:a of old remember:imp'],
   '46-11':['ravenous bird:a from east','human:a who mypl/counsel:a perform:pr'],
   '47-2':['kjv_flour:a kjv_grind:imp','kjv_hair_lock:pl'],
   '47-3':['as human meet:neg:fu'],'47-6':['mypl/inheritance:a kjv_pollute_sacred:perf'],
   '47-7':['thou say:pa ipl lady forever'],
   '47-8':['ipl be:pr and none else apart from ipl'],
   '47-9':['two thing:pl','one_num day'],
   '47-10':['none ipl:a see:pr'],
   '47-13':['kjv_astrologer:pl','star:pl:a watch:pr','each month foretell:pr'],
   '47-15':['thy/kjv_merchant:pl','each to his/region'],
   '48-1':['water:pl of kjv_judah'],'48-4':['iron sinew','brow kjv_brass'],
   '48-5':['lest thou say:should mypl/idol'],
   '48-7':['now create:psv:pr','ipl they:a know:pa'],
   '48-10':['not with silver'],'48-12':['ipl he be:pr'],
   '48-16':['ipl in secret from beginning speak:neg:perf','lord god and his/spirit ipl:a send:perf'],
   '48-18':['listen:pp:opt:excl'],'48-19':['his/name','destroy:psv:neg:should'],
   '49-1':['mypl/mother'],'49-2':['smooth:psv:adj arrow'],
   '49-3':['to ipl say:pa','kjv_israel:excl','ipl glorify:psv:fu'],
   '49-4':['ipl in vain labour:perf'],
   '49-5':['though kjv_israel gather:psv:neg:pr'],
   '49-6':['it small thing','for light to kjv_gentile:pl'],
   '49-10':['they:a strike:neg:fu'],'49-12':['kjv_sinim'],
   '49-14':['kjv_zion say:pa','mypl/lord ipl:a forget:perf'],
   '49-15':['yes they forget:may'],'49-16':['kjv_palm_hand:pl'],
   '49-17':['thy/child:pl'],'49-19':['kjv_swallow:pa'],
   '49-20':['place too narrow for i'],
   '49-21':['ipl alone leave:psv:pa'],
   '49-23':['kjv_nurse father:pl','dust:a of thy/foot:pl up kjv_lick:fu'],
   '49-24':['lawful captive'],'49-25':['prey of terrible'],
   '49-26':['their/own flesh','their/own blood','mighty of kjv_jacob']}.items():
   for part in parts:self.assertIn(part,cases[r]['analysis'])
  self.assertEqual(cases['48-11']['analysis'].count('for mypl/own sake'),2)
  self.assertEqual(cases['46-4']['analysis'].count('carry:fu'),3)
  self.assertTrue(cases['48-15']['analysis'].startswith('ipl even ipl'))
  self.assertEqual([r for r,c in cases.items() if 'kjv_cyrus' in c['analysis']],['45-1'])
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_potsherd','kjv_sorcery','kjv_astrologer','kjv_bel','kjv_nebo_god','kjv_sabeans_isaiah','kjv_sinim'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
