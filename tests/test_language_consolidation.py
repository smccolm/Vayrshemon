"""Cross-play semantic distinctions and the durable next-translation baseline."""
import json
import unittest
from tools.editorial_language import ROOT, EditorialLanguage


class ConsolidatedLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep the 0.10 historical regression intact when a later package is pinned.
        cls.language = EditorialLanguage(ROOT / 'data/language/consolidated-0.10')
        cls.pin = json.loads((cls.language.folder / 'manifest.json').read_text(encoding='utf8'))

    def test_current_package_is_complete_and_pinned(self):
        self.assertEqual('0.10', self.pin['version'])
        self.assertEqual(3809, len(self.language.lexicon))
        self.assertTrue(self.pin['forgeHead'])
        for key, entry in self.language.lexicon.items():
            self.assertEqual('lex.' + key, entry['semanticId'])
            self.assertTrue(set(entry['form']) <= self.language.letters | set('’ -'))
            if entry['derivationKeys']:
                self.assertEqual(entry['form'], ''.join(self.language.lexicon[k]['form'] for k in entry['derivationKeys']))

    def test_explicit_positive_and_negative_contrasts(self):
        cases = json.loads((self.language.folder / 'regression-cases.json').read_text(encoding='utf8'))
        self.assertEqual(64, len(cases))
        for case in cases:
            with self.subTest(case=case['id']):
                if case['expected'] == 'reject':
                    with self.assertRaisesRegex(ValueError, case['error']):
                        self.language.compile(case['analysis'])
                else:
                    result = self.language.compile(case['analysis'])
                    self.assertEqual(case['expectedText'], result['text'])
                    self.assertEqual(case['expectedGloss'], result['gloss'])
                    if 'expectedReading' in case:
                        self.assertEqual(case['expectedReading'], self.language.reading(result['text']))

    def test_archive_cardinal_readings_independently(self):
        # Literal readings checked against the supplied chart, not produced by
        # the compiler. In particular four has a macron, seven a diaeresis.
        expected = {'zero':'fōlem','one_num':'neksus','two':'thātus','three':'venik',
                    'four':'bārum','five':'jensis','six':'ōdēum','seven':'pärsus',
                    'eight':'krizum','nine':'deksin','ten':'eshnä','eleven':'yamen','twelve':'ämēnō'}
        for key, reading in expected.items():
            self.assertEqual(reading, self.language.reading(self.language.word(key)[0]))
        self.assertEqual('thātus’t', self.language.reading(self.language.word('second')[0]))
        self.assertEqual('venik’t', self.language.reading(self.language.word('third')[0]))

    def test_meaningful_distinctions_survive(self):
        for a, b in [('one','one_num'),('two','second'),('dead','mortal'),('bar','bar_obstruct'),
                     ('we','wepl'),('thou','you'),('sleep:cv','sleep:cvds'),
                     ('sleep:imp','sleep:pr:opt'),('sleep:pr:opt','sleep:pr:juss'),
                     ('be:pa:rep','be:pr:app'),('fool:psv:caus:pr','fool:caus:psv:pr')]:
            with self.subTest(a=a,b=b):
                self.assertNotEqual(self.language.word(a)[0], self.language.word(b)[0])
        self.assertNotEqual(self.language.compile('slumber:neg:pr:must.')['text'],
                            self.language.compile('slumber:inf i need:pr not.')['text'])
        self.assertIn('collective', (self.language.folder/'grammar.md').read_text(encoding='utf8'))

    def test_sentence_continuation_preserves_real_maxima(self):
        units = [{'analysis':'i speak:pr,','part':0},
                 {'analysis':'and i go:pr.','part':1},
                 {'analysis':'i return:pr.','part':2}]
        result = self.language.compile_units(units)
        self.assertEqual(self.language.word('and')[0][0], result[1]['text'][0])
        self.assertEqual(self.language.maxima(self.language.word('i')[0])[0], result[0]['text'][0])
        self.assertEqual(self.language.maxima(self.language.word('i')[0])[0], result[2]['text'][0])
        # A proper name stays Maxima even inside a continued sentence.
        named = self.language.compile('titania sleep:pr.', initial=False)['text']
        self.assertEqual(self.language.maxima(self.language.lexicon['titania']['form'])[0], named[0])

    def test_historical_forms_do_not_override_current_dictionary(self):
        self.assertEqual('tren', self.language.lexicon['three']['historicalForms'][0]['form'])
        self.assertEqual('venik', self.language.word('three')[0])
        self.assertEqual('nēnna', self.language.reading(self.language.word('mortal_legacy')[0]))
        self.assertNotEqual(self.language.word('mortal_legacy')[0], self.language.word('mortal')[0])
        self.assertEqual(self.language.word('bone')[0], self.language.word('noise')[0])
        self.assertNotEqual(self.language.lexicon['bone']['semanticId'], self.language.lexicon['noise']['semanticId'])

    def test_expressive_form_preserves_other_force_without_borrowed_glyph(self):
        plain=self.language.compile('go:imp.')
        marked=self.language.compile('go:imp:excl.')
        self.assertNotEqual(plain['text'], marked['text'])
        self.assertTrue(self.language.reading(marked['text']).endswith('’hā.'))
        self.assertIn('imp.',marked['gloss'])
        self.assertIn('excl.',marked['gloss'])
        self.assertNotIn('!',marked['text'])
        with self.assertRaisesRegex(ValueError,'EXCLAMATION_REQUIRES_EXCL_FORM'):
            self.language.compile('go:imp!')


if __name__ == '__main__':
    unittest.main()
