import unittest
from tools.kjv_archive import load_register, read


class JoshuaInheritanceTests(unittest.TestCase):
    def test_many_self_and_inheritance(self):
        old, _ = load_register('0.10-kjv.33')
        lang, manifest = load_register('0.10-kjv.34')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'joshua-inheritance-cases.json')}
        self.assertEqual(167, len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                result = lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'], result['text'])
                self.assertEqual(c['expectedGloss'], result['gloss'])
        checks = {'13-1': ['yet very much land to possess:psv:inf'], '13-3': ['five of kjv_philistine:pl lord:pl', 'also kjv_avite:pl'], '13-6': ['ipl drive:fu out', 'by kjv_lot', 'ipl command:perf'], '13-7': ['nine kjv_tribe:pl', 'half of kjv_manasseh'], '13-12': ['remain:pr part remain:pa'], '13-13': ['drive:pa not out', 'to this day dwell:pr'], '13-14': ['of kjv_levi kjv_tribe:pl', 'kjv_sacrifice:pl their/inherit:ev'], '13-17': ['her/city:pl', 'kjv_bamothbaal', 'kjv_bethbaalmeon'], '13-18': ['kjv_jahaza', 'kjv_mephaath'], '13-19': ['kjv_zarethshahar', 'of valley mountain'], '13-21': ['kjv_evi', 'kjv_rekem', 'kjv_zur', 'kjv_hur_midian', 'kjv_reba', 'of kjv_sihon duke:pl'], '13-22': ['kjv_balaam', 'kjv_divine:ag'], '13-25': ['half of of kjv_ammon child:pl land', 'before kjv_rabbah'], '13-26': ['kjv_debir_boundary'], '13-27': ['kjv_chinnereth', 'his/boundary'], '13-29': ['half of kjv_manasseh', 'half of of kjv_manasseh'], '13-30': ['six+ten city:pl'], '13-31': ['one_num half of of kjv_machir child:pl'], '13-33': ['kjv_lord of kjv_israel god their/inherit:ev'], '14-1': ['kjv_eleazar priest', 'kjv_joshua of kjv_nun son', 'father:pl head:pl'], '14-3': ['two kjv_tribe:pl and half'], '14-4': ['kjv_suburb_land', 'kjv_substance_estate', 'except city:pl'], '14-6': ['about i and thou'], '14-7': ['forty year:pl old i', 'in my/heart'], '14-8': ['heart:a melt:inf make:pa', 'completely i follow:pa'], '14-9': ['kjv_moses on that day swear:pa', 'kjv_lord my/god'], '14-10': ['forty and five', 'eight+ten and five'], '14-12': ['if so kjv_lord with i be:fu', 'i be:fu:can'], '14-15': ['kjv_arba', 'land from war rest:pa'], '15-1': ['kjv_lot_portion', 'kjv_zin'], '15-2': ['kjv_bay_water'], '15-3': ['round to kjv_karkaa turn:pa'], '15-4': ['your/kjv_south boundary'], '15-7': ['kjv_debir_achor', 'kjv_adummim', 'kjv_enshemesh', 'kjv_enrogel'], '15-8': ['of kjv_hinnom son valley', 'same kjv_jerusalem'], '15-9': ['kjv_ephron_mountain', 'kjv_baalah_place', 'which kjv_kirjathjearim'], '15-10': ['mountain kjv_jearim', 'kjv_chesalon'], '15-13': ['kjv_arba of kjv_anak father'], '15-14': ['kjv_three son:pl', 'kjv_sheshai', 'kjv_ahiman', 'kjv_talmai'], '15-16': ['kjv_achsah my/daughter', 'i give:fu'], '15-17': ['of kjv_kenaz son of kjv_caleb brother'], '15-18': ['she urge:pa', 'her/ass she descend:pa', 'what thou desire:pr'], '15-19': ['to i blessing', 'kjv_upper spring:pl and kjv_lower spring:pl'], '15-25': ['kjv_hazor, kjv_hadattah', 'kjv_hezron_place which kjv_hazor'], '15-32': ['twenty and nine'], '15-36': ['kjv_gederah and kjv_gederothaim', 'fourteen city:pl'], '15-41': ['sixteen city:pl'], '15-49': ['kjv_kirjathsannah which kjv_debir_city'], '15-54': ['kjv_kirjatharba which kjv_hebron'], '15-57': ['kjv_cain_city'], '15-60': ['kjv_kirjathbaal which kjv_kirjathjearim', 'kjv_rabbah_judah'], '15-63': ['be:pa:can not', 'at kjv_jerusalem to this day'], '16-3': ['kjv_lower kjv_bethhoron'], '16-5': ['kjv_upper kjv_bethhoron'], '16-9': ['separate city:pl', 'among of of kjv_manasseh'], '16-10': ['drive:pa not out', 'under kjv_tribute serve:pr'], '17-1': ['first+born', 'of war man'], '17-2': ['kjv_shechem_person', 'kjv_male child:pl'], '17-3': ['no son:pl but daughter:pl', 'kjv_noah_daughter', 'kjv_tirzah'], '17-4': ['to wepl inherit:ev', 'of wepl brother:pl', 'of their/father brother:pl'], '17-5': ['ten kjv_portion_share:pl', 'besides'], '17-7': ['kjv_right_side hand'], '17-8': ['of kjv_tappuah_city land', 'kjv_tappuah_city on of kjv_manasseh boundary', 'kjv_ephraim'], '17-11': ['kjv_bethshean', 'kjv_ibleam', 'kjv_dor', 'kjv_endor', 'kjv_taanach', 'kjv_megiddo', 'kjv_three country:pl'], '17-12': ['be:pa:can not', 'dwell:inf will:pa'], '17-13': ['kjv_tribute', 'completely they:a drive:pa not out'], '17-14': ['to ipl only one_num kjv_lot_portion and one_num kjv_portion_share', 'great people ipl be:pr', 'ipl:a until now bless:perf'], '17-15': ['great people thou be:pr', 'for thyself'], '17-16': ['hill for wesg enough be:pr not', 'of iron chariot:pl'], '17-17': ['to kjv_ephraim and to kjv_manasseh', 'great people thou be:pr'], '17-18': ['though of iron chariot:pl', 'though strong'], '18-1': ['kjv_tabernacle', 'land before they subdue:psv:pa'], '18-4': ['kjv_three man:pl for each kjv_tribe', 'they:a i send:fu'], '18-6': ['before kjv_lord ourone/god', 'kjv_lot:pl:a i cast:pr:may'], '18-7': ['kjv_priesthood their/inherit:ev', 'half of kjv_manasseh'], '18-9': ['seven part:pl in book', 'army at kjv_shiloh'], '18-11': ['kjv_benjamin', 'between of kjv_judah child:pl and of kjv_joseph'], '18-13': ['kjv_atarothadar', 'kjv_lower kjv_bethhoron'], '18-14': ['of sea corner', 'kjv_direction_quarter'], '18-17': ['kjv_geliloth', 'kjv_bohan'], '18-19': ['kjv_bethhoglah', 'kjv_north kjv_bay_water', 'kjv_south end'], '18-24': ['kjv_chepharhaammonai', 'twelve city:pl'], '18-26': ['kjv_mizpeh_benjamin'], '18-27': ['kjv_rekem_city'], '18-28': ['kjv_jebusi which kjv_jerusalem', 'kjv_gibeath', 'kjv_kirjath', 'fourteen city:pl']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['joshua-' + ref]['analysis'])
        self.assertNotEqual(lang.lexicon['bay']['meaning'], lang.lexicon['kjv_bay_water']['meaning'])
        self.assertNotEqual(lang.lexicon['lower']['pos'], lang.lexicon['kjv_lower']['pos'])
        self.assertIn('great people ipl be:pr', cases['joshua-17-14']['analysis'])
        self.assertIn('hill for wesg', cases['joshua-17-16']['analysis'])
        self.assertIn('great people thou be:pr', cases['joshua-17-17']['analysis'])
        self.assertNotEqual(lang.compile('i be:pr')['text'], lang.compile('ipl be:pr')['text'])
        self.assertNotEqual(lang.compile('wepl be:pr')['text'], lang.compile('wesg be:pr')['text'])
        self.assertEqual('data/language/archaic-kjv-33', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
