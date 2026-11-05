"""Semantic contrasts for the later dramatic language; no Inputs/Saves required."""
import json
import unittest
from tools.editorial_language import ROOT, EditorialLanguage, load_current


class LaterDramaticLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.language = EditorialLanguage(ROOT / 'data/language/later-dramatic-0.11')

    def test_versioned_parent_remains_explicit(self):
        # Keep 0.11 as a permanent regression when a later language is pinned.
        manifest = json.loads((self.language.folder / 'manifest.json').read_text(encoding='utf8'))
        self.assertEqual('0.11', manifest['version'])
        self.assertEqual('c5fa1161b15094f3b57b4042963e5ba82ea7dfbf3142f88ad557d524573b5fef', manifest['parentHead'])
        self.assertEqual('0.10-kjv.280', manifest['historicalReference']['version'])

    def test_four_first_person_perspectives(self):
        lang = self.language
        forms = [lang.word(k)[0] for k in ('i', 'ipl', 'wesg', 'wepl')]
        self.assertEqual(4, len(set(forms)))
        self.assertEqual(['rô', 'rôun', 'ly', 'lym'], [lang.reading(x) for x in forms])
        self.assertEqual('lym’sevarun', lang.reading(lang.word('ourpl/heart:pl')[0]))
        self.assertEqual('ly’älm', lang.reading(lang.word('ourone/will')[0]))
        self.assertNotEqual(lang.word('ourselvespl')[0], lang.word('ourselves')[0])

    def test_inherited_contrasts_with_documented_native_migrations(self):
        cases=json.loads((self.language.folder/'regression-cases.json').read_text(encoding='utf8'))
        self.assertEqual(64,len(cases))
        for case in cases:
            with self.subTest(case=case['id']):
                if case['expected']=='reject':
                    with self.assertRaisesRegex(ValueError,case['error']):
                        self.language.compile(case['analysis'])
                else:
                    result=self.language.compile(case['analysis'])
                    self.assertEqual(case['expectedText'],result['text'])
                    self.assertEqual(case['expectedGloss'],result['gloss'])
                    if 'expectedReading' in case:
                        self.assertEqual(case['expectedReading'],self.language.reading(result['text']))

    def test_oath_marriage_and_native_ratification(self):
        lang = self.language
        self.assertEqual('lamüw’hā', lang.reading(lang.word('marry')[0]))
        self.assertEqual('zerilatya', lang.reading(lang.word('wed:fu')[0]))
        self.assertEqual('kom rē’ne', lang.reading(lang.word('amen')[0]))
        self.assertEqual('zerilarimizya', lang.reading(lang.word('wed:caus:psv:pa')[0]))
        self.assertEqual('zerilimarizya', lang.reading(lang.word('wed:psv:caus:pa')[0]))
        self.assertNotEqual(lang.word('wed')[0], lang.word('marry')[0])

    def test_comic_correction_keeps_two_distinct_meanings(self):
        lang = self.language
        self.assertEqual('yalangz', lang.reading(lang.word('paramour_colloquial')[0]))
        self.assertEqual('farangz', lang.reading(lang.word('paragon_epithet')[0]))
        self.assertNotEqual(lang.word('paramour_colloquial')[0], lang.word('paragon_epithet')[0])
        self.assertEqual('later-literary', lang.lexicon['paragon_epithet']['usageScope'])

    def test_lexicalization_is_bounded_and_history_is_retained(self):
        lang = self.language
        self.assertEqual('hefakgurget', lang.reading(lang.word('war:a')[0]))
        self.assertEqual('pomsōlumunläy', lang.reading(lang.word('scholar:pl:n')[0]))
        self.assertIn('hefak gur', [x['form'] for x in lang.lexicon['war']['historicalForms']])
        self.assertEqual('editorial-exception', lang.lexicon['mortal_legacy']['usageScope'])
        self.assertGreater(sum(v['usageScope']=='historical-reference' for v in lang.lexicon.values()), 6000)
        self.assertNotEqual(lang.word('groat')[0], lang.word('penny')[0])

    def test_inherited_grammatical_safeguards_and_maxima(self):
        lang = self.language
        for bad in ('wed:pa:psv', 'i:n:a', 'sleep:pr:cv', 'go:excl:imp', 'go:imp!'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                lang.compile(bad)
        result=lang.compile_units([{'analysis':'i speak:pr,','part':0},
                                   {'analysis':'and i go:pr.','part':1},
                                   {'analysis':'i return:pr.','part':2}])
        self.assertEqual(lang.word('and')[0][0], result[1]['text'][0])
        self.assertEqual(lang.maxima(lang.word('i')[0])[0], result[2]['text'][0])
        self.assertTrue(lang.reading(lang.compile('go:imp:excl.')['text']).endswith('’hā.'))
        for key, value in lang.lexicon.items():
            self.assertTrue(set(value['form']) <= lang.letters | set(' ’-'), key)

    def test_source_linked_marriage_and_identity_repairs(self):
        decisions=json.loads((self.language.folder/'decisions.json').read_text(encoding='utf8'))
        changes={(x['play'],x['unitId']):x for x in decisions['editorialRevisions']}
        for ident in ('0296','0369','0386','0408'):
            row=changes['allswell',ident]
            self.assertRegex(row['before'], r'\bwe\b')
            self.assertNotRegex(row['after'], r'\b(?:we|wesg|wepl)\b')
        self.assertIn('wed:fu',changes['midsummer','0006']['after'])
        self.assertIn('wed:psv:cv',changes['allswell','0461']['after'])
        self.assertIn('paramour_colloquial',changes['midsummer','0592']['after'])
        self.assertIn('paragon_epithet',changes['midsummer','0593']['after'])


if __name__ == '__main__':
    unittest.main()
