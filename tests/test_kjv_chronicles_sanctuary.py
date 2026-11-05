import unittest
from tools.kjv_archive import load_register, read


class ChroniclesSanctuaryTests(unittest.TestCase):
    def test_ancestry_senses_and_city_allocations(self):
        prior, _ = load_register('0.10-kjv.78')
        lang, manifest = load_register('0.10-kjv.79')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'chronicles-sanctuary-cases.json')}
        self.assertEqual(81, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
            self.assertFalse({'i','ipl','wesg','wepl','one'} & set(result['keys']))
        for ref, parts in {
            '1':['kjv_gershon'], '2':['kjv_hebron_kohath'],
            '3':['child:pl of kjv_amram','kjv_miriam'],
            '9':['kjv_azariah_ahimaaz','kjv_johanan_azariah'],
            '10':['kjv_azariah_johanan','office:a of priest'],
            '11':['kjv_amariah_azariah','kjv_ahitub_later'],
            '15':['kjv_captivity','by hand of nebuchadnezzar'],
            '16':['kjv_gershom_levi'], '22':['kjv_amminadab_kohath'],
            '23':['kjv_assir_later'], '28':['first+born kjv_vashni'],
            '31':['after kjv_ark_chest rest:pp'],
            '32':['their/office:a attend:pa','kjv_service_order'],
            '33':['kjv_heman_singer','kjv_shemuel_singer_line'],
            '34':['kjv_eliel_jeroham son of kjv_toah'],
            '38':['kjv_izhar son of kjv_kohath'],
            '39':['at kjv_right_side of he','kjv_berachiah_asaph'],
            '43':['kjv_jahath_gershom son of kjv_gershom_levi'],
            '44':['at left side','kjv_ethan_singer'],
            '47':['kjv_mahli_mushi son of kjv_mushi'],
            '49':['altar of burn:psv kjv_offering','altar of kjv_incense','kjv_atonement'],
            '54':['their/fortress:pl in their/kjv_coast_region:pl'],
            '56':['kjv_caleb son of kjv_jephunneh'],
            '58':['kjv_hilen','kjv_debir_city'],
            '60':['kjv_alemeth','ten and kjv_three city:pl'],
            '61':['half kjv_tribe namely out of half kjv_tribe','ten city:pl'],
            '62':['ten and kjv_three city:pl'], '63':['twelve city:pl'],
            '70':['kjv_aner_city','kjv_bileam'],
            '73':['kjv_ramoth_issachar','kjv_anem'],
            '76':['kjv_kedesh in kjv_galilee'],
            '78':['east side of kjv_jordan','kjv_jahzah'],
            '80':['kjv_ramoth_refuge in kjv_gilead'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['1-chronicles-6-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-78', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
