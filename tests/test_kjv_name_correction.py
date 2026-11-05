"""Historical names: readable glosses without merging identities or grammar."""
import unittest
from copy import deepcopy
from tools.kjv_archive import load_register, read
from tools.kjv_name_correction import PARENT, PACKAGE, NAME_FORMS


class HistoricalNameCorrection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old, _ = load_register('0.10-kjv.281')
        cls.new, _ = load_register('0.10-kjv.282')

    def test_yeshua_reading_and_maxima_in_inflected_names(self):
        for key in NAME_FORMS:
            form, gloss, keys = self.new.word(key + ':g')
            stem = 'Baryeshūa' if key == 'kjv_barjesus_acts' else 'Yeshūa'
            self.assertTrue(self.new.reading(form).startswith(stem))
            self.assertTrue(gloss.startswith(stem + '('))
            self.assertEqual(keys, [key])
            self.assertEqual(form[0], self.new.pairs[NAME_FORMS[key][0]])

    def test_only_five_native_entries_change(self):
        self.assertEqual(self.old.lexicon.keys(), self.new.lexicon.keys())
        changed = {k for k in self.old.lexicon if self.old.lexicon[k]['form'] != self.new.lexicon[k]['form']}
        self.assertEqual(changed, set(NAME_FORMS))
        for key in self.old.lexicon:
            self.assertEqual(self.old.lexicon[key]['meaning'], self.new.lexicon[key]['meaning'])
            self.assertEqual(self.old.lexicon[key].get('semanticId'), self.new.lexicon[key].get('semanticId'))

    def test_namesake_ids_are_not_merged(self):
        identities = {self.new.lexicon[k]['semanticId'] for k in NAME_FORMS}
        self.assertEqual(len(identities), 5)
        for key in ('kjv_jesus_joshua_acts', 'kjv_jesus_justus_colossians', 'kjv_jesus_rest_hebrews'):
            self.assertNotEqual(self.new.lexicon[key]['meaning'], self.new.lexicon['kjv_jesus_matthew']['meaning'])

    def test_other_elam_keeps_the_separate_modifier_once(self):
        analysis = 'other kjv_elam_other'
        before = self.old.compile(analysis)
        after = self.new.compile(analysis)
        self.assertEqual(before['text'], after['text'])
        self.assertEqual(after['keys'], ['other', 'kjv_elam_other'])
        self.assertEqual(after['gloss'].lower().count('other'), 1)
        self.assertIn('Elam', after['gloss'])

    def test_context_qualifiers_do_not_leak_through_possessors(self):
        _, gloss, keys = self.new.word('kjv_jesus_matthew/word:g')
        self.assertIn('Yeshūa-', gloss)
        self.assertNotIn('matthew', gloss.lower())
        self.assertIn('kjv_jesus_matthew', keys)
        self.assertEqual(self.new.word('kjv_john_revelation')[1], 'John')

    def test_compounds_and_meaningful_titles_survive(self):
        for key in ('kjv_ashteroth_karnaim', 'kjv_shaveh_kiriathaim', 'kjv_lord', 'kjv_i_am', 'kjv_red_sea', 'kjv_christ_title', 'kjv_holy_spirit_title'):
            self.assertEqual(self.old.word(key), self.new.word(key))
        self.assertEqual(self.new.word('kjv_three_taverns_acts')[1], 'Three-taverns')
        self.assertEqual(self.new.word('kjv_claudius_lysias_acts')[1], 'Claudius-Lysias')

    def test_only_reviewed_glosses_change_and_grammar_is_identical(self):
        before = read(PARENT / 'morphology.json'); after = read(PACKAGE / 'morphology.json')
        labels = read(PACKAGE / 'display-labels.json')
        expected = deepcopy(before)
        for key, row in labels.items():
            self.assertEqual(before['glosses'][key], row['before'])
            self.assertTrue(row['evidence'])
            expected['glosses'][key] = row['after']
        self.assertEqual(expected, after)
        self.assertEqual((PARENT/'compiler.py').read_bytes(), (PACKAGE/'compiler.py').read_bytes())
        self.assertEqual((PARENT/'orthography.json').read_bytes(), (PACKAGE/'orthography.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
