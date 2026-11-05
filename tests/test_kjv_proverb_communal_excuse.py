import unittest,re
from tools.kjv_archive import load_register,read
class ProverbCommunalExcuseTests(unittest.TestCase):
 def test_speaker_scope_opposed_counsel_and_material_senses(self):
  prior,_=load_register('0.10-kjv.124');lang,manifest=load_register('0.10-kjv.125')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id']:c for c in read(lang.folder/'proverbs-communal-excuses-and-opposed-counsel-cases.json')};self.assertEqual(len(cases),152)
  refs={k:set() for k in ['i','wesg','ipl','wepl','mypl','ourone','iplself']}
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'just','want','sound','hell','simple','right','plain','mean','scale','train','conceit','discover','whip','kjv_mortar'}&set(out['keys']))
   for kind in refs:
    if re.search(r'(?<![a-z_])'+kind+r'(?![a-z_])',c['analysis']):refs[kind].add(c['id'])
  self.assertEqual(refs['wesg'],{'proverbs-24-12'})
  self.assertEqual(refs['i'],{'proverbs-'+r for r in ['23-26','23-35','24-29','24-30','24-32','26-19','27-11']})
  for k in ['ipl','wepl','mypl','ourone','iplself']:self.assertFalse(refs[k])
  for ref,parts in {
   '23-4':['thy/own wisdom'],'23-16':['my/kjv_kidney:pl'],'23-21':['kjv_drowse','kjv_rag:pl'],
   '23-27':['kjv_ditch'],'23-29':['kjv_babble'],'23-33':['strange woman:pl'],'23-34':['kjv_mast'],
   '24-11':['kjv_forbear'],'24-12':['wesg'],'24-16':['seven'],
   '24-26':['every human lip:pl:a of he who kjv_upright answer:a give:pr kiss:fu'],
   '25-1':['kjv_hezekiah_ahaz'],'25-11':['apple:pl','image:pl'],'25-18':['false witness:a against his/neighbour give:pr'],
   '25-20':['kjv_nitre'],'25-23':['kjv_north wind','away'],'25-26':['spoil:psv:adj spring'],
   '26-3':['kjv_whip_tool'],'26-4':['answer:neg:imp','lest thou also like he'],
   '26-5':['answer:imp','lest he wise in his/own thought'],'26-8':['kjv_sling_tool'],
   '26-10':['god','reward:pr'],'26-15':['his/bosom'],'26-16':['seven'],
   '26-19':['i in sport be:neg:pr?'],'26-23':['kjv_potsherd_scraper'],'26-25':['seven'],
   '27-16':['hand of his/kjv_right_side'],'27-21':['kjv_crucible'],
   '27-22':['kjv_mortar_grind','kjv_pestle','kjv_grind:should'],'27-25':['appear:pr'],
  }.items():
   for p in parts:self.assertIn(p,cases['proverbs-'+ref]['analysis'],(ref,p))
  self.assertTrue(cases['proverbs-26-18']['analysis'].endswith(','))
  old={}
  for version,filename in [('0.10-kjv.124','proverbs-quoted-claims-and-source-readings-cases.json')]:
   prev,_=load_register(version);old.update({c['id']:c for c in read(prev.folder/filename)})
  for a,b in [('18-8','26-22'),('22-3','27-12'),('20-16','27-13')]:self.assertEqual(old['proverbs-'+a]['analysis'],cases['proverbs-'+b]['analysis'])
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_drowse','kjv_rag','kjv_ditch','kjv_babble','kjv_mast','kjv_nitre','kjv_whip_tool','kjv_pestle'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
