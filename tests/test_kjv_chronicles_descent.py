import re
import unittest
from tools.kjv_archive import load_register, read


class ChroniclesDescentTests(unittest.TestCase):
    def test_source_identity_petition_and_inheritance(self):
        prior, _ = load_register('0.10-kjv.77')
        lang, manifest = load_register('0.10-kjv.78')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'chronicles-descent-cases.json')}
        self.assertEqual(93, len(cases))
        irefs = set()
        for ref, case in cases.items():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
            self.assertNotIn('!', result['text'])
            self.assertFalse({'ipl', 'wesg', 'wepl', 'one'} & set(result['keys']))
            if re.search(r'(?<![a-z_])i(?![a-z_])', case['analysis']):
                irefs.add(ref)
        self.assertEqual({'1-chronicles-4-9','1-chronicles-4-10','1-chronicles-5-3'}, irefs)
        for ref, parts in {
            '3-1':['kjv_daniel_david','kjv_ahinoam_jezreel'],
            '3-5':['kjv_bathshua daughter of kjv_ammiel_bathshua'],
            '3-8':['kjv_elishama_david and kjv_eliada and kjv_eliphelet_david nine'],
            '3-16':['kjv_jeconiah his/son kjv_zedekiah_jeconiah his/son'],
            '3-19':['son:pl of kjv_pedaiah_jeconiah kjv_zerubbabel','kjv_shelomith_zerubbabel their/sister'],
            '3-22':['kjv_hattush and kjv_igeal and kjv_bariah and kjv_neariah_shemaiah and kjv_shaphat_shemaiah six'],
            '4-9':['because i with sorrow he:a born:pa'],
            '4-10':['bless:opt','wide:caus:opt','thy/hand with i be:opt','sorrow:neg:caus:may:excl','request:pa grant:pa'],
            '4-14':['kjv_joab_seraiah','valley of kjv_charashim','artisan:pl'],
            '4-17':['and she kjv_miriam_line'],
            '4-21':['kjv_er_shelah father of kjv_lecah','fine linen:a work:pa'],
            '4-27':['sixteen son:pl and six daughter:pl','have:neg:pa'],
            '4-33':['kjv_baal_place','their/kjv_genealogy'],
            '4-40':['fruitful kjv_pasture','with peace'],
            '4-41':['completely destroy:pa','in their/place:pl dwell:pa'],
            '4-42':['five+hundred man:pl'],
            '5-1':['his/birthright to son:pl of kjv_joseph','reckon:neg:psv:pr'],
            '5-2':['chief ruler','birthright of kjv_joseph'],
            '5-3':['i say:pr','kjv_hanoch_reuben'],
            '5-5':['kjv_baal_person'],
            '5-10':['kjv_saul_israel'],
            '5-14':['kjv_gilead_gad'],
            '5-18':['half kjv_tribe','forty+thousand and four+thousand and seven+hundred and six+ten'],
            '5-20':['he their/request:a grant:pa'],
            '5-21':['fifty+thousand','two+hundred+thousand and fifty+thousand','ass:pl two+thousand','man:pl hundred+thousand'],
            '5-26':['kjv_pul','kjv_tilgathpilneser','kjv_hara','river kjv_gozan'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['1-chronicles-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-77', manifest['basePackage'])
        self.assertIn('kjv_elishama_david', prior.lexicon)
        self.assertIn('kjv_zerah_simeon', prior.lexicon)


if __name__ == '__main__':
    unittest.main()
