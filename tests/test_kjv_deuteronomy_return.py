import unittest
from tools.kjv_archive import load_register, read


class DeuteronomyReturnTests(unittest.TestCase):
    def test_household_self_curses_and_return(self):
        old, _ = load_register('0.10-kjv.29')
        lang, manifest = load_register('0.10-kjv.30')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'deuteronomy-return-cases.json')}
        self.assertEqual(181, len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                result = lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'], result['text'])
                self.assertEqual(c['expectedGloss'], result['gloss'])
        checks = {'25-3': ['forty strike:ev:pl', 'exceed:pr:may not'], '25-8': ['i like:pr not'], '26-3': ['ipl profess:pr', 'ourone/father:pl', 'to wesg'], '26-5': ['mypl/father', 'nation great mighty'], '26-7': ['ourone/voice'], '26-13': ['mypl/house', 'ipl transgress:perf not'], '27-15': ['curse:psv:opt:excl', 'amen'], '28-7': ['one_num way', 'seven way:pl'], '28-20': ['ipl:a thou forsake:perf'], '28-25': ['one_num way', 'seven way:pl'], '28-63': ['rejoice:fu to you:pl:a destroy:inf'], '28-67': ['evening it be:opt:excl', 'morning it be:opt:excl'], '28-68': ['with ship:pl', 'no man you:pl:a buy:fu'], '29-5': ['forty year:pl', 'ipl lead:perf'], '29-6': ['ipl kjv_lord your/god be:pr'], '29-7': ['wesg strike:pa'], '29-8': ['half of kjv_manasseh'], '29-14': ['i make:pr'], '29-19': ['peace i have:fu'], '29-29': ['secret thing:pl', 'to wesg'], '30-6': ['heart:a kjv_circumcise:fu'], '30-12': ['for wesg'], '30-14': ['in thy/mouth and in thy/heart'], '30-20': ['thy/life and of thy/day:pl length he be:pr']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['deuteronomy-' + ref]['analysis'])
        self.assertNotEqual(lang.compile('i be:pr')['text'], lang.compile('ipl be:pr')['text'])
        self.assertNotEqual(lang.compile('wepl be:pr')['text'], lang.compile('wesg be:pr')['text'])
        self.assertEqual('data/language/archaic-kjv-29', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
