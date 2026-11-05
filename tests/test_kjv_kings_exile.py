import unittest
from tools.kjv_archive import load_register, read


class KingsExileTests(unittest.TestCase):
    def test_exile_quantities_senses_and_contextual_repairs(self):
        prior, _ = load_register('0.10-kjv.74')
        lang, manifest = load_register('0.10-kjv.75')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings2-exile-cases.json')}
        self.assertEqual(66, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        for ref, parts in {
            '2-kings-24-4': ['pardon:inf refuse:pa'],
            '2-kings-24-8': ['ten and eight year:pl', 'kjv_three month:pl'],
            '2-kings-24-14': ['ten+thousand captive:pl'],
            '2-kings-24-16': ['seven+thousand', 'kjv_smith:pl thousand'],
            '2-kings-24-17': ['brother of his/father', 'his/name:a to kjv_zedekiah_king'],
            '2-kings-25-1': ['nine:ord year', 'ten:ord month', 'ten:ord day'],
            '2-kings-25-7': ['before his/eye:pl', 'eye:pl of kjv_zedekiah_king:a put:pa out'],
            '2-kings-25-8': ['five:ord month', 'seven:ord day', 'ten and nine:ord year'],
            '2-kings-25-11': ['kjv_defect_allegiance'],
            '2-kings-25-12': ['kjv_vinedresser', 'kjv_husbandman'],
            '2-kings-25-16': ['one_num sea', 'without weigh:ev'],
            '2-kings-25-17': ['ten and eight kjv_cubit:pl', 'kjv_chapiter kjv_three kjv_cubit:pl'],
            '2-kings-25-18': ['kjv_seraiah_priest', 'two:ord priest', 'kjv_three keep:ag:pl'],
            '2-kings-25-19': ['five men', 'kjv_three+twenty men'],
            '2-kings-25-23': ['kjv_seraiah_tanhumeth', 'kjv_jaazaniah_maachathite'],
            '2-kings-25-27': ['kjv_three+ten and seven:ord year', 'twelve:ord month', 'twenty and seven:ord day'],
            '2-kings-25-30': ['kjv_allowance', 'daily amount for every day'],
            'genesis-18-25': ['kjv_right_conduct:a'],
            'numbers-18-18': ['kjv_right_side'],
            'numbers-27-7': ['kjv_right_conduct:adv'],
            '2-kings-10-15': ['sincere'],
            '2-kings-12-9': ['kjv_right_side'],
            '2-kings-18-3': ['kjv_right_conduct'],
        }.items():
            for part in parts:
                self.assertIn(part, cases[ref]['analysis'])
        for ident, case in cases.items():
            if ident.startswith(('2-kings-24-', '2-kings-25-')):
                self.assertFalse({'i','ipl','wesg','wepl'} & set(lang.compile(case['analysis'])['keys']))
        self.assertEqual('data/language/archaic-kjv-74', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
