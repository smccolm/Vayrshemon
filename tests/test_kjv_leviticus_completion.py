import unittest

from tools.kjv_archive import load_register, read


class LeviticusCompletionRegisterTests(unittest.TestCase):
    def test_identity_calendar_property_and_irrevocable_categories(self):
        parent, _ = load_register('0.10-kjv.18')
        lang, manifest = load_register('0.10-kjv.19')
        self.assertEqual(parent.lexicon, {k: lang.lexicon[k] for k in parent.lexicon})
        for field in ('pairs', 'suffix', 'possessors', 'roman'):
            self.assertEqual(getattr(parent, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'leviticus-completion-cases.json')}
        self.assertEqual(259, len(cases))
        for case in cases.values():
            with self.subTest(verse=case['id']):
                result = lang.compile(case['analysis'])
                self.assertEqual(case['expectedText'], result['text'])
                self.assertEqual(case['expectedGloss'], result['gloss'])
        checks = {
            '21-22': ['he eat:fu', 'both of most holy and of holy'],
            '22-13': ['widow or kjv_divorced', 'no child:a', 'return:perf'],
            '22-23': ['offer:pr:may', 'for vow it accept:psv:fu not'],
            '23-5': ['fourteen:ord day at evening'],
            '23-16': ['seven:ord kjv_sabbath fifty day:pl:a you:pl kjv_number:fu'],
            '23-17': ['with kjv_leaven they bake:psv:fu'],
            '23-27': ['seven:ord month ten:ord day'],
            '23-32': ['nine:ord day at evening', 'from evening until evening'],
            '23-36': ['seven day:pl', 'eight:ord day'],
            '24-6': ['two row:pl', 'six on row', 'kjv_table_furniture'],
            '24-22': ['one_num manner of law', 'for one of your/own country'],
            '25-20': ['wesg eat:fu', 'ourone/increase'],
            '25-21': ['mypl/bless:ev', 'ipl command:fu', 'kjv_three year:pl'],
            '25-23': ['land of ipl'],
            '25-30': ['in kjv_jubile it go:fu out not'],
            '25-31': ['in kjv_jubile go:fu out'],
            '25-32': ['at any time'],
            '25-34': ['sell:psv:pr:may not'],
            '25-46': ['for ever your/slave:pl', 'but over your/brother:pl'],
            '25-54': ['his/child:pl'],
            '26-11': ['mypl/soul:n you:pl:a loathe:fu not'],
            '26-28': ['ipl, even ipl'],
            '26-30': ['mypl/soul:n you:pl:a loathe:fu'],
            '26-34': ['land:n her/kjv_sabbath:pl:a kjv_enjoy_rest:fu'],
            '26-44': ['loathe:fu to they:a entirely destroy:inf'],
            '27-2': ['special vow'],
            '27-6': ['from month old', 'five year:pl old', 'kjv_three of silver'],
            '27-7': ['six+ten year:pl', 'fifteen kjv_shekel:pl', 'female ten'],
            '27-16': ['kjv_homer at fifty'],
            '27-21': ['its/kjv_possession of priest'],
            '27-24': ['to he to whom of land kjv_possession belong:pa'],
            '27-29': ['kjv_devote_irrevocable', 'surely to death put:psv:fu'],
            '27-31': ['five:ord part of it to it'],
            '27-33': ['both it and its/change:ev holy', 'redeem:psv:fu not']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['leviticus-' + ref]['analysis'])
        for first, second in [('kjv_homer', 'kjv_omer'),
                              ('kjv_scurvy_skin', 'scurvy'),
                              ('kjv_dwarf_body', 'dwarf'),
                              ('kjv_devote_irrevocable', 'devoted'),
                              ('kjv_number', 'count'),
                              ('kjv_table_furniture', 'table')]:
            self.assertNotEqual(lang.word(first)[1], lang.word(second)[1])
        self.assertEqual('data/language/archaic-kjv-18', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
