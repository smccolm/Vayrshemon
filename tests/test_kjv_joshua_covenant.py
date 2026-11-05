import unittest
from tools.kjv_archive import load_register, read

class JoshuaCovenantTests(unittest.TestCase):
    def test_complete_section_and_speaker_scopes(self):
        old, _ = load_register('0.10-kjv.34')
        lang, manifest = load_register('0.10-kjv.35')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs','suffix','prefix','possessors','roman'):
            self.assertEqual(getattr(old,field),getattr(lang,field))
        cases={c['id']:c for c in read(lang.folder/'joshua-covenant-cases.json')}
        self.assertEqual(188,len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                result=lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'],result['text'])
                self.assertEqual(c['expectedGloss'],result['gloss'])
        checks={'19-2': ['kjv_beersheba and kjv_sheba_city'], '19-6': ['ten and kjv_three city:pl'], '19-9': ['too much', 'within of they inherit:ev'], '19-12': ['kjv_japhia_city'], '19-28': ['kjv_hebron_asher', 'kjv_kanah_place'], '19-34': ['to kjv_judah upon kjv_jordan'], '19-38': ['kjv_iron_city', 'ten and nine'], '19-43': ['kjv_elon_city'], '19-47': ['kjv_leshem', 'of sword edge', 'kjv_dan after'], '19-50': ['city which he ask:pa'], '20-2': ['ipl speak:pa'], '20-3': ['without know:ev and without intend:ev'], '20-4': ['of of city gate', 'of that city kjv_elder:pl'], '20-5': ['deliver:fu not', 'without intend:ev', 'before he:a hate:pa not'], '20-6': ['until before kjv_congregation', 'and until of high priest'], '20-8': ['kjv_ramoth_refuge'], '20-9': ['stranger', 'until before kjv_congregation'], '21-4': ['ten and kjv_three'], '21-5': ['half of kjv_manasseh', 'ten city:pl'], '21-6': ['ten and kjv_three'], '21-7': ['twelve city:pl'], '21-12': ['kjv_caleb'], '21-41': ['forty and eight'], '22-2': ['my/voice', 'i command:pa'], '22-5': ['kjv_cleave_adhere:inf', 'all your/heart', 'all your/soul'], '22-7': ['one_num half', 'its/other half'], '22-8': ['kjv_brass', 'with your/brother:pl kjv_divide:imp'], '22-12': ['to to war against they'], '22-14': ['ten prince:pl', 'thousand:pl'], '22-17': ['clean:psv:pr wesg be:pr not', 'although'], '22-19': ['kjv_unclean_ritual', 'besides of kjv_lord'], '22-20': ['alone perish:pa not'], '22-22': ['kjv_lord of god:pl god, kjv_lord of god:pl god', 'wesg:a this day save:imp:excl not'], '22-23': ['meal kjv_offering', 'require:opt:excl'], '22-25': ['between wesg and you:pl', 'ourone/child:pl'], '22-27': ['burn:psv ourone/kjv_offering:pl', 'peace ourone/kjv_offering:pl'], '22-28': ['pattern', 'ourone/father:pl'], '22-29': ['forbid:opt:excl'], '22-31': ['among wesg', 'wepl perceive:pr', 'out of of kjv_lord hand'], '22-33': ['kjv_please_satisfy:pa', 'intend:pa not'], '23-2': ['old', 'i be:pr'], '23-4': ['which remain:pr', 'i cut:perf off'], '23-5': ['drive:fu out'], '23-7': ['swear:caus:imp'], '23-8': ['kjv_cleave_adhere:imp'], '23-10': ['one_num man', 'thousand:a'], '23-13': ['snare:pl and trap:pl', 'kjv_scourge_lash:pl', 'thorn:pl'], '23-15': ['all evil thing:pl:a bring:fu'], '24-2': ['kjv_flood_river', 'kjv_nachor'], '24-3': ['ipl take:pa', 'kjv_multiply:caus:pa'], '24-7': ['he darkness:a', 'what in egypt ipl do:perf'], '24-10': ['ipl will:pa not', 'he bless:pa'], '24-12': ['two of kjv_amorite:pl king:pl', 'thy/sword nor with thy/bow'], '24-15': ['i and my/house', 'wesg serve:fu'], '24-16': ['god forbid:opt:excl'], '24-19': ['be:pr:can not', 'jealous', 'forgive:fu not'], '24-20': ['hurt:a do:fu', 'consume:fu', 'after'], '24-22': ['witness:pl against yourselves', 'witness:pl wepl be:pr'], '24-24': ['wesg serve:fu'], '24-27': ['this stone', 'it hear:perf'], '24-29': ['hundred and ten'], '24-32': ['kjv_shechem_hamor', 'hundred of silver piece:pl'], '24-33': ['kjv_eleazar', 'he:a they bury:pa']}
        for ref,parts in checks.items():
            for part in parts:self.assertIn(part,cases['joshua-'+ref]['analysis'])
        self.assertNotEqual(lang.compile('wepl serve:fu')['text'],lang.compile('wesg serve:fu')['text'])
        self.assertIn('i and my/house',cases['joshua-24-15']['analysis'])
        self.assertIn('witness:pl wepl be:pr',cases['joshua-24-22']['analysis'])
        self.assertEqual('data/language/archaic-kjv-34',manifest['basePackage'])

if __name__=='__main__':unittest.main()
