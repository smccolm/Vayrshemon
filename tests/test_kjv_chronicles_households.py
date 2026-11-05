import unittest
from tools.kjv_archive import load_register, read


class ChroniclesHouseholdsTests(unittest.TestCase):
    def test_kinship_scope_namesakes_and_group_quantities(self):
        prior, _ = load_register('0.10-kjv.76')
        lang, manifest = load_register('0.10-kjv.77')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'chronicles-households-cases.json')}
        self.assertEqual(55, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
            self.assertFalse({'i','ipl','wesg','wepl','one'} & set(result['keys']))
        for ref, parts in {
            '3': ['daughter of kjv_shua_father', 'kjv_three'],
            '4': ['wife of his/son', 'kjv_zerah_judah', 'five be:pa'],
            '7': ['kjv_achar', 'kjv_accursed_devoted thing'],
            '9': ['kjv_ram_person'],
            '13': ['kjv_eliab_jesse', 'kjv_abinadab_jesse two:ord', 'kjv_shimma kjv_three:ord'],
            '15': ['kjv_david seven:ord'],
            '17': ['kjv_jether_amasa kjv_ishmeelite'],
            '18': ['kjv_caleb_hezron son of kjv_hezron', 'her/son:pl'],
            '21': ['he kjv_three+twenty year:pl old'],
            '22': ['kjv_three and twenty city:pl'],
            '23': ['he kjv_geshur and kjv_aram_land', 'from they take:pa', 'kjv_three+twenty city:pl'],
            '24': ['then kjv_abiah_hezron wife of kjv_hezron'],
            '25': ['kjv_ram_jerahmeel first+born'],
            '31': ['child:pl of kjv_sheshan kjv_ahlai'],
            '32': ['kjv_jether_jada without child:pl'],
            '34': ['no son:pl but daughter:pl', 'kjv_egyptian'],
            '35': ['his/daughter:a to kjv_jarha his/servant for wife'],
            '42': ['son:pl of kjv_mareshah_line father of kjv_hebron_line'],
            '46': ['kjv_ephah_caleb kjv_concubine', 'kjv_gazez_caleb', 'kjv_gazez_haran'],
            '49': ['daughter of kjv_caleb_hezron kjv_achsa'],
            '50': ['kjv_caleb_hur son of kjv_hur_caleb first+born of kjv_ephratah_woman'],
            '52': ['half of kjv_manahethite:pl'],
            '54': ['kjv_ataroth house of kjv_joab', 'half of kjv_manahethite:pl'],
            '55': ['kjv_family:pl of kjv_scribe:pl', 'kjv_hemath_rechab father of house of kjv_rechab_house'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['1-chronicles-2-' + ref]['analysis'])
        self.assertIn('kjv_jether_amasa', prior.lexicon)
        self.assertEqual('data/language/archaic-kjv-76', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
