import unittest
from tools.kjv_archive import load_register, read


class KingsSiegeVoicesTests(unittest.TestCase):
    def test_nested_speakers_collective_beneficiaries_and_material_senses(self):
        prior, _ = load_register('0.10-kjv.71')
        lang, manifest = load_register('0.10-kjv.72')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings2-siege-voices-cases.json')}
        self.assertEqual(74, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        for ref, parts in {
            '18-14': ['ipl transgress:perf', 'ipl carry:fu'],
            '18-20': ['ipl have:pr', 'against ipl thou rebel:pr'],
            '18-22': ['ourone/god wesg trust:pr'],
            '18-23': ['my/lord king of kjv_assyria', 'i deliver:fu'],
            '18-26': ['wepl understand:pr', 'with wepl'],
            '18-27': ['their/own kjv_urine:a'],
            '18-30': ['wesg:a kjv_lord surely deliver:fu'],
            '18-31': ['with ipl agree:ev:a by gift', 'his/kjv_cistern'],
            '19-12': ['kjv_haran_place', 'kjv_eden_thelasar'],
            '19-15': ['thou alone'],
            '19-19': ['ourone/god i thou:a beseech:pr', 'wesg:a'],
            '19-20': ['ipl hear:perf'],
            '19-23': ['mypl/chariot:pl', 'kjv_lodging_place:pl'],
            '19-24': ['foreign water:pl'],
            '19-25': ['ipl form:perf', 'kjv_desolate:caus:inf'],
            '19-28': ['mypl/kjv_restraint_hook:a', 'mypl/bridle'],
            '19-32': ['kjv_siege_mound:a'],
            '19-34': ['ipl defence:fu', 'mypl/servant kjv_david'],
            '19-35': ['hundred+thousand and eight+ten+thousand and five+thousand:a'],
            '19-37': ['kjv_adrammelech_sennacherib and kjv_sharezer', 'kjv_esarhaddon'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['2-kings-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-71', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
