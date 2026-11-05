import unittest
from tools.kjv_archive import load_register,read
class PsalmVoicesPetitionsTests(unittest.TestCase):
 def test_poetic_voices_negative_scope_and_source_senses(self):
  prior,_=load_register('0.10-kjv.107');lang,manifest=load_register('0.10-kjv.108')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for f in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,f),getattr(lang,f))
  cases={c['id']:c for c in read(lang.folder/'psalms-voices-petitions-cases.json')};self.assertEqual(len(cases),135)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'count','one','just','band','act'}&set(out['keys']))
  for ref,parts in {
   '1-1':['walk:neg:pr','stand:neg:pr','sit:neg:pr'], '1-3':['his/leaf','plant:psv:pr'],
   '2-3':['wesg','kjv_binding_band','kjv_cord'], '2-6':['ipl mypl/king'],
   '2-7':['kjv_lord to ipl say:perf','this day ipl thee:a beget'], '2-9':['kjv_potter','kjv_dash_break'],
   '3-6':['ten+thousand:pl','afraid be:neg:fu'], '4-2':['kjv_lie_false:ev'],
   '4-4':['kjv_awe','kjv_commune'], '4-6':['to wepl','upon wesg'],
   '5-6':['kjv_lie_false:ev','kjv_abhor'], '6-1':['rebuke:neg:imp','kjv_chasten:neg:imp'],
   '6-5':['in death no remembrance','in grave who'], '6-6':['swim:caus','kjv_couch_job'],
   '7-3':['if i this:a do:perf'], '7-4':['without cause my/enemy','deliver:perf'],
   '7-5':['take:opt','my/honour:a in dust'], '7-9':['kjv_just_fair','kjv_kidney'],
   '7-16':['top of his/own head'], '8-1':['ourone/lord'], '8-3':['when i'],
   '8-5':['little lower than angel:pl'], '9-4':['my/right','kjv_just_fair'],
   '9-16':['kjv_higgaion_marker','kjv_selah_marker'], '9-18':['always forget:psv:neg:fu'],
   '10-3':['kjv_covet:ag:a bless'], '10-6':['i move:psv:neg:fu'],
   '10-9':['in wait lie:pr','kjv_den'], '10-17':['thy/ear:a hear:caus'],
   '11-4':['his/eyelid:pl'], '11-6':['snare:pl','fear:a cause'],
   '12-2':['two heart'], '12-4':['ourone/tongue wesg','over wesg'],
   '12-5':['now ipl rise','kjv_lord say','kjv_puff_at'], '12-6':['seven time:pl'],
   '12-7':['they:a keep','they:a from this generation'],
  }.items():
   for p in parts:self.assertIn(p,cases['psalms-'+ref]['analysis'])
  self.assertEqual(len(lang.lexicon)-len(prior.lexicon),16)
  self.assertEqual(manifest['basePackage'],'data/language/archaic-kjv-107')
if __name__=='__main__':unittest.main()
