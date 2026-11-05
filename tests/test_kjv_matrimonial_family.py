import unittest
from tools.kjv_archive import load_register,read
class MatrimonialFamilyTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.lang,cls.manifest=load_register('0.10-kjv.280')
 def test_matrimonial_constructions_are_not_oaths(self):
  for key,analysis in [('married','wed:psv:adj'),('wedding','wed:ev')]:
   self.assertEqual(self.lang.lexicon[key]['form'],self.lang.compile(analysis,initial=False)['text'])
   self.assertNotEqual(self.lang.lexicon[key]['form'],self.lang.lexicon['marry']['form'])
   self.assertEqual(self.lang.lexicon[key]['derivationKeys'],['wed'])
 def test_eight_matrimonial_verses_and_inherited_cases(self):
  cases=read(self.lang.folder/'native-correction-cases.json');related=[]
  for case in cases:
   actual=self.lang.compile(case['analysis']);self.assertEqual(actual['text'],case['text']);self.assertEqual(actual['gloss'],case['gloss'])
   if {'married','wedding'}&set(actual['keys']):related.append(case['reference'])
  self.assertEqual(len(related),8);self.assertIn('Exodus 21:3',related);self.assertIn('Matthew 22:12',related)
 def test_inherited_grammar_and_maxima_unchanged(self):
  old,_=load_register('0.10-kjv.278')
  for attr in ['suffix','prefix','possessors','pairs','roman']:self.assertEqual(getattr(self.lang,attr),getattr(old,attr))
if __name__=='__main__':unittest.main()
