from fractions import Fraction
import unittest
from tools.unta_language import cardinal,quantity,digits,candidates,semantic_key
from tools.editorial_language import load_current

class UntaLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lang,_=load_current()
    def reading(self,n):return self.lang.reading(cardinal(n))
    def test_score_is_twenty_not_two_dozens(self):
        self.assertEqual('18',digits(20));self.assertEqual('ämēnō krizum',self.reading(20))
        self.assertEqual('sidēum',self.reading(24));self.assertNotEqual(cardinal(20),cardinal(24))
        self.assertEqual('50',digits(60));self.assertEqual('rivēum',self.reading(60))
    def test_chart_place_values_and_exact_source_hundreds(self):
        self.assertEqual('änimus bārum',self.reading(100))
        self.assertEqual('neksus nōrum',self.reading(144))
        self.assertEqual('ōdēum nōrum onez bārum',self.reading(1000))
        self.assertEqual('neksus therid',self.reading(1728))
        self.assertEqual('neksus nekra',self.reading(20736))
    def test_order_frequency_and_fraction_are_distinct(self):
        self.assertEqual('venik’t',self.lang.reading(quantity(3,'ordinal')['form']))
        self.assertEqual('thātus venor',self.lang.reading(quantity(2,'times')['form']))
        self.assertEqual('venik mem',self.lang.reading(quantity(3,'fold')['form']))
        self.assertEqual('fōlemchoi bārum',self.lang.reading(quantity(1,'fraction',3)['form']))
        self.assertEqual('fōlemchoi ōdēum',self.lang.reading(quantity(1,'fraction',2)['form']))
        self.assertEqual('fōlemchoi venik',self.lang.reading(quantity(1,'fraction',4)['form']))
    def test_exact_fraction_never_silently_rounds(self):
        q=quantity(1,'fraction',7);self.assertEqual(Fraction(1,7),Fraction(q['value']))
        self.assertEqual('1/7',q['base12']);self.assertIn('parts-out-of',q['evidence'])
        self.assertEqual('yamenchoi yamen',self.lang.reading(quantity(143,'fraction',12)['form']))
    def test_numeric_review_flags_ambiguous_words_without_translating(self):
        self.assertEqual(['score','third','score'],[r['text'] for r in candidates('a score of men; the third man; pay the score')])
        self.assertTrue(semantic_key(20).replace('_','').isalpha())
        for n in [-1,True,1.5]:
            with self.assertRaises(ValueError):cardinal(n)
        with self.assertRaises(ValueError):quantity(0,'ordinal')
        with self.assertRaises(ValueError):quantity(1,'ordinal',3)
    def test_numeric_review_catches_ordinal_and_compound_forms(self):
        source='Thirteenth, thirtieth, a hundredth; threefold and two-fold; fourscore, scores and dozens; doubled interest.'
        self.assertEqual(['Thirteenth','thirtieth','hundredth','threefold','two','fourscore','scores','dozens','doubled'],
                         [r['text'] for r in candidates(source)])
        self.assertEqual([],candidates('someone alongside a milestone'))
        self.assertEqual(['thousand','doubles'],[r['text'] for r in candidates('a thousand doubles to evade the hounds')])
        self.assertEqual(['millioned'],[r['text'] for r in candidates('whose millioned accidents')])
        self.assertEqual(['seconds','seconds'],[r['text'] for r in candidates('mixed with seconds; he seconds the motion')])
        self.assertEqual([],candidates('a secondary concern'))
        self.assertEqual([],candidates('a millionaire beside a millstone'))
        self.assertEqual(['fiftyfold','sixteenfold','ninetyfold','millionfold','50fold'],
                         [r['text'] for r in candidates('fiftyfold, sixteenfold, ninetyfold, millionfold, 50fold')])
        self.assertEqual([],candidates('a blindfold beside a folder'))
        self.assertEqual(['demi'],[r['text'] for r in candidates('the demi-Atlas of this Earth')])
        self.assertEqual([],candidates('Demetrius admires the demigod'))
        fiftyfold=quantity(50,'fold')
        self.assertEqual('50',fiftyfold['value'])
        self.assertEqual('42',fiftyfold['base12'])
        self.assertEqual('ãramēn thātus mem',self.lang.reading(fiftyfold['form']))

    def test_source_notation_preserves_words_or_glyphs_with_same_value(self):
        from vayrshemon.page_numbering import digits as folio_digits
        for n in (0,3,10,11,12,20,100,1000,20000):
            words=quantity(n);written=quantity(n,notation='digits')
            self.assertEqual(cardinal(n),words['form'])
            self.assertEqual(folio_digits(n),written['form'])
            self.assertEqual(words['value'],written['value'])
            self.assertEqual(words['form'],written['spokenForm'])
            self.assertNotEqual(semantic_key(n),semantic_key(n,notation='digits'))
        self.assertEqual('3’t',quantity(3,'ordinal',notation='digits')['form'])
        self.assertEqual('venik’t',quantity(3,'ordinal')['form'])
        self.assertEqual('18 venor',quantity(20,'times',notation='digits')['form'])
        self.assertEqual('0:6',quantity(1,'fraction',2,notation='digits')['form'])
        self.assertEqual('Á:Á',quantity(143,'fraction',12,notation='digits')['form'])
        self.assertEqual('1 threnin tha 7 ilmem threnin',quantity(1,'fraction',7,notation='digits')['form'])
        with self.assertRaises(ValueError):quantity(3,notation='guess')

    def test_numeral_morphology_and_radix_survive_sentence_compilation(self):
        lang,_=load_current();lang.lexicon=dict(lang.lexicon);lang.glosses=dict(lang.glosses)
        for key,q in [('written_third',quantity(3,'ordinal',notation='digits')),
                      ('written_half',quantity(1,'fraction',2,notation='digits'))]:
            lang.lexicon[key]=dict(form=q['form'],pos='numeral');lang.glosses[key]=q['value']
        self.assertEqual('3’t. 0:6.',lang.compile('written_third. written_half.')['text'])

if __name__=='__main__':unittest.main()
