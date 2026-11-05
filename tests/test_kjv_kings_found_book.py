import unittest
from tools.kjv_archive import load_register, read


class KingsFoundBookTests(unittest.TestCase):
    def test_human_intermediaries_collective_peril_and_unaverted_judgment(self):
        prior, _ = load_register('0.10-kjv.73')
        lang, manifest = load_register('0.10-kjv.74')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings2-found-book-cases.json')}
        self.assertEqual(57, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        for ref, parts in {
            '22-2': ['kjv_right_conduct', 'kjv_right_side'],
            '22-4': ['silver:a he reckon:pr:may'],
            '22-7': ['no reckon:ev make:psv:pa'],
            '22-8': ['book of law:a i find:perf'],
            '22-13': ['for i and for people', 'against wesg', 'ourone/father:pl'],
            '22-14': ['kjv_huldah woman prophet', 'kjv_college_locality'],
            '22-15': ['who you:a to i send:pa'],
            '22-16': ['ipl bring:fu'],
            '22-20': ['into thy/tomb in peace'],
            '23-4': ['two:ord order'],
            '23-7': ['kjv_sodomite_source_label:pl', 'women hang:psv cloth:pl'],
            '23-11': ['horse:pl:a he take:pa away', 'chariot:pl of sun:a with fire burn:caus:pa'],
            '23-13': ['kjv_right_side hand'],
            '23-17': ['kjv_inscription_mark', 'that i see:pr'],
            '23-20': ['upon altar:pl he slay:pa'],
            '23-26': ['kjv_lord turn:pa not'],
            '23-27': ['mypl/sight ipl remove:fu', 'ipl choose:perf'],
            '23-29': ['against king of kjv_assyria'],
            '23-30': ['he:a dead in chariot'],
            '23-33': ['hundred kjv_talent_weight:pl of silver', 'one_num kjv_talent_weight of gold'],
            '23-35': ['of each kjv_according to his/kjv_tax_assessment', 'demand:pa'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['2-kings-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-73', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
