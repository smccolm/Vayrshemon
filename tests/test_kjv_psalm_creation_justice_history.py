import unittest
from tools.kjv_archive import load_register,read
class PsalmCreationJusticeHistoryTests(unittest.TestCase):
 def test_shared_bodies_distinct_gods_and_unharmonized_history(self):
  prior,_=load_register('0.10-kjv.115');lang,manifest=load_register('0.10-kjv.116')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'psalms-creation-justice-history-cases.json')};self.assertEqual(len(cases),220)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','right','host','consume','render','kjv_selah','prevent','fair','share','suffer'}&set(out['keys']))
  for ref,parts in {
   '94-17':['my/help be:neg:pp','dwell:perf:should'], '94-20':['throne of kjv_iniquity','by law shape:pr'],
   '95-6':['wesg worship:inf','wepl down bow:inf','kneel:inf'], '95-9':['ipl:a tempt:pa','mypl/work:a'],
   '95-10':['forty year:pl ipl','mypl/way:pl:a know:neg:perf'], '95-11':['ipl in mypl/wrath','mypl/rest enter:neg:should'],
   '96-5':['god:pl of nation:pl idol:pl'], '97-7':['all you:pl god:pl:excl'], '97-11':['light for kjv_righteous kjv_sow:psv:pr'],
   '98-9':['kjv_righteousness','kjv_equity'], '99-4':['judge:ev:a love:pr','kjv_equity:a kjv_establish:pr'],
   '99-8':['forgive:pa','revenge:a'], '100-3':['wepl:a make:perf','not wepl ourselves:a','wesg his/people'],
   '101-5':['allow:neg:fu'], '101-7':['kjv_lie_false:pl'],
   '102-6':['kjv_pelican','owl of dry land'], '102-9':['kjv_ashes:a like bread','with weep:ev mix:perf'],
   '102-24':['i say:pa my/god:excl','middle of my/day:pl'], '102-26':['old become:fu like garment'],
   '103-5':['thy/mouth:a','youth of kjv_eagle'], '103-10':['wesg','ourone/sin:pl'],
   '103-14':['our/shape:ev:a','wepl dust'], '103-20':['angel:pl:excl'], '103-21':['army:pl:excl'],
   '104-4':['angel:pl:a spirit:pl','flame:adj fire'], '104-8':['they up by mountain:pl','they down by valley:pl'],
   '104-16':['kjv_tree_sap'], '104-26':['leviathan','play:inf'], '104-29':['their/breath:a'], '104-30':['thy/spirit:a'],
   '104-35':['sin:ag:pl out of earth destroy:psv:inf'],
   '105-8':['thousand generation:pl'], '105-11':['to thee ipl','your/inheritance'], '105-15':['mypl/anoint:psv:adj:a','mypl/prophet:pl'],
   '105-18':['in iron lay:psv:pa'], '105-22':['kjv_senator:pl:a wisdom:a teach:inf'],
   '105-25':['he their/heart:a his/people:a hate:inf turn:pa'], '105-28':['rebel:neg:pa'], '105-30':['their/king:pl'],
   '105-36':['first born:psv:adj'], '105-37':['not one_num feeble person'], '105-44':['labour:a of people inherit:pa'],
  }.items():
   for part in parts:self.assertIn(part,cases['psalms-'+ref]['analysis'],(ref,part))
  added=set(lang.lexicon)-set(prior.lexicon)
  self.assertEqual(added,{'kjv_equity','kjv_tree_sap','kjv_senator'})
  for key in added:
   entry=lang.lexicon[key];self.assertEqual(entry['form'],''.join(lang.lexicon[k]['form'] for k in entry['derivationKeys']))
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
