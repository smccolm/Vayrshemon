"""Native historical vocabulary: semantic contrast and inherited-form regression."""
import unittest
from tools.kjv_archive import load_register,read

class NativeVocabularyTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.lang,cls.manifest=load_register('0.10-kjv.279')
  cls.old,_=load_register('0.10-kjv.278')
  cls.cases=read(cls.lang.folder/'native-correction-cases.json')
 def test_contextual_assent_and_quoted_language(self):
  for case in self.cases:
   with self.subTest(reference=case['reference']):
    actual=self.lang.compile(case['analysis'])
    self.assertEqual(actual['text'],case['text']);self.assertEqual(actual['gloss'],case['gloss'])
  byref={c['reference']:c for c in self.cases}
  self.assertIn('native_affirmation_title',byref['Revelation 3:14']['analysis'])
  self.assertIn('native_affirmation',byref['2 Corinthians 1:20']['analysis'])
  self.assertNotIn('amen',self.lang.reading(byref['Revelation 22:21']['text']).lower())
  for ref in ['Matthew 27:46','Mark 15:34']:
   self.assertEqual(byref[ref]['analysis'].count('mypl/god'),4)
   self.assertNotIn('kjv_sabachthani_quoted',byref[ref]['analysis'])
 def test_marriage_is_not_an_oath(self):
  marriage=[c for c in self.cases if 'wed' in self.lang.compile(c['analysis'])['keys']]
  self.assertEqual(sum('Correct marriage verb:' in c['note'] for c in marriage),38)
  for case in marriage:self.assertNotIn('marry',self.lang.compile(case['analysis'])['keys'])
  self.assertNotEqual(self.lang.lexicon['marry']['form'],self.lang.lexicon['wed']['form'])
 def test_reviewed_borrowings_and_accidental_homographs(self):
  changes=read(self.lang.folder/'native-corrections.json')
  for row in changes['directChanges']:
   if row['decision']['construction'].startswith('@'):
    self.assertNotEqual(row['before']['form'],row['after']['form'],row['key'])
  for key in ['berry','asleep','bone','drop']:
   self.assertEqual(self.lang.lexicon[key]['form'],self.old.lexicon[key]['form'],key)
  for key in ['amen','christ','silver','mountain','kjv_shibboleth','kjv_sibboleth']:
   self.assertNotEqual(self.lang.lexicon[key]['form'],self.old.lexicon[key]['form'],key)
  sh=self.lang.reading(self.lang.lexicon['kjv_shibboleth']['form']);s=self.lang.reading(self.lang.lexicon['kjv_sibboleth']['form'])
  self.assertTrue(sh.startswith('sh') and s.startswith('s'));self.assertEqual(sh[2:],s[1:])
 def test_archaic_morphology_names_and_maxima_preserved(self):
  for attr in ['suffix','prefix','possessors','pairs','roman']:
   self.assertEqual(getattr(self.lang,attr),getattr(self.old,attr),attr)
  for key in ['kjv_jesus_matthew','kjv_jerusalem']:
   self.assertEqual(self.lang.lexicon[key]['form'],self.old.lexicon[key]['form'])
  for analysis in ['ipl be:pr','wesg be:pr','mypl/god','ourone/lord']:
   self.assertEqual(self.lang.compile(analysis),self.old.compile(analysis))
  self.assertEqual(self.lang.compile('amen')['text'],self.lang.maxima(self.lang.compile('amen',initial=False)['text']))

if __name__=='__main__':unittest.main()
