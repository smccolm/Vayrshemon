import unittest
from tools.kjv_archive import load_register
from tools.kjv_unta_correction import Correction


class BibleUntaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.language, _ = load_register('0.10-kjv.283')

    def render(self, source, analysis, ref='test'):
        correction = Correction()
        revised = correction.revise(dict(reference=ref,source=source,analysis=analysis))
        compiled = self.language.compile(revised)
        return self.language.reading(compiled['text']), [correction.forms[k] for k in compiled['keys'] if k in correction.forms]

    def test_third_and_possessed_ordinal(self):
        text, forms = self.render('the third day','kjv_three:ord day')
        self.assertIn('Venik’t',text)
        self.assertEqual(forms[0]['notation'],'words')
        _,forms=self.render('the seven and twentieth day of the month','month/twenty and seven:ord day')
        self.assertEqual([(q['value'],q['kind']) for q in forms],[('27','ordinal')])

    def test_census_and_distributive(self):
        _,forms=self.render('forty and six thousand and five hundred','forty+thousand and six+thousand and five+hundred')
        self.assertEqual([q['value'] for q in forms],['46500'])
        _,forms=self.render('two and two','two and two')
        self.assertEqual([q['value'] for q in forms],['2','2'])

    def test_score_fraction_factor_and_temporal_reading(self):
        _,forms=self.render('more than sixscore thousand persons','more than six kjv_score thousand person')
        self.assertEqual([q['value'] for q in forms],['120000'])
        _,forms=self.render('the third part of an hin','kjv_three:ord part of kjv_hin')
        self.assertEqual(forms[0]['value'],'1/3')
        _,forms=self.render('seventy times seven','five+twelve and ten kjv_fold seven')
        self.assertEqual([(q['value'],q['kind']) for q in forms],[('70','fold'),('7','cardinal')])
        _,forms=self.render('at once','at once','Deuteronomy 7:22')
        self.assertEqual(forms,[])
