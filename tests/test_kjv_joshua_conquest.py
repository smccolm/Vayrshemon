import unittest
from tools.kjv_archive import load_register, read


class JoshuaConquestTests(unittest.TestCase):
    def test_trespass_treaty_and_conquest(self):
        old, _ = load_register('0.10-kjv.32')
        lang, manifest = load_register('0.10-kjv.33')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(old, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'joshua-conquest-cases.json')}
        self.assertEqual(178, len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                result = lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'], result['text'])
                self.assertEqual(c['expectedGloss'], result['gloss'])
        checks = {'7-1': ['kjv_achan of kjv_carmi son', 'of kjv_zabdi son', 'of kjv_zerah son', 'against of kjv_israel child:pl'], '7-3': ['about two+thousand or kjv_three+thousand', 'few only'], '7-5': ['about thirty and six', 'heart:pl melt:pa'], '7-7': ['wesg:a destroy:inf', 'wesg be:pp:opt:excl'], '7-8': ['i say:fu:excl'], '7-9': ['ourone/name', 'thy/great name'], '7-11': ['mypl/kjv_covenant', 'ipl command:pa', 'kjv_dissemble:perf'], '7-12': ['any more ipl be:fu except'], '7-14': ['kjv_tribe', 'kjv_family', 'kjv_household', 'man by man'], '7-15': ['he and all which he have:pr'], '7-20': ['i sin:perf', 'i do:perf'], '7-21': ['two+hundred', 'fifty', 'kjv_covet:pa', 'silver under it'], '7-24': ['of kjv_zerah son', 'his/son:pl and his/daughter:pl'], '7-25': ['he:a stone:pa', 'they:a burn:caus:pa', 'they:a they stone:pp'], '8-1': ['ipl give:perf'], '8-2': ['only its/spoil and its/kjv_livestock'], '8-3': ['thirty+thousand'], '8-5': ['i and all people who with i', 'wesg flee:fu'], '8-6': ['they say:fu: before wesg'], '8-12': ['about five+thousand'], '8-15': ['as if before they beat:psv:pa'], '8-17': ['kjv_ai or kjv_bethel'], '8-18': ['kjv_spear', 'ipl give:fu'], '8-23': ['king:a alive'], '8-25': ['both of man:pl and woman:pl twelve+thousand', 'even all of kjv_ai man:pl'], '8-26': ['until of kjv_ai all inhabitant:pl'], '8-29': ['kjv_corpse', 'sun down', 'until evening'], '8-31': ['of whole stone:pl altar', 'any iron no man'], '8-33': ['stranger', 'half of they opposite mountain kjv_gerizim', 'half of they opposite mountain kjv_ebal_mountain'], '8-35': ['woman:pl and little child:pl and stranger:pl'], '9-2': ['one_num purpose'], '9-4': ['as if kjv_ambassador:pl', 'kjv_bottle:pl'], '9-5': ['with patch:pl shoe:pl', 'kjv_mouldy'], '9-6': ['wepl come:perf', 'kjv_league:a with wesg'], '9-8': ['servant:pl wesg be:pr'], '9-11': ['ourone/kjv_elder:pl', 'to wepl speak:pa', 'servant:pl wesg be:pr'], '9-12': ['of wepl house:pl', 'wepl take:pa'], '9-14': ['counsel:a at of kjv_lord mouth ask:pa not'], '9-18': ['they:a strike:pa not', 'kjv_murmur:pa'], '9-19': ['wepl swear:perf', 'wepl touch:pr:may not'], '9-20': ['wrath upon wesg', 'wepl swear:pa'], '9-23': ['slave:pl be:ev', 'of my/god house'], '9-24': ['of wepl life:pl', 'afraid wepl'], '9-25': ['in thine/hand wesg be:pr'], '10-4': ['i:a help:imp', 'wepl strike:pr:can'], '10-6': ['thy/hand:a', 'wesg:a save:imp'], '10-8': ['ipl deliver:perf'], '10-10': ['kjv_lord before kjv_israel they:a kjv_discomfit:pa'], '10-11': ['with hail+stone:pl', 'more than'], '10-12': ['sun, upon kjv_gibeon thou still stand:imp', 'thou moon'], '10-13': ['kjv_jasher', 'about whole day'], '10-14': ['before it or after it', 'to of man voice listen:pa'], '10-15': ['to kjv_gilgal return:pa'], '10-20': ['until consume:psv:pa', 'rest which remain:pa'], '10-21': ['at kjv_makkedah'], '10-26': ['they:a slay:pa and on five kjv_tree:pl they:a hang:pa'], '10-27': ['at of sun go:ev down'], '10-32': ['kjv_second day'], '10-37': ['its/king'], '10-38': ['kjv_debir_city'], '10-41': ['kjv_goshen_canaan'], '10-42': ['at one_num time'], '10-43': ['to kjv_gilgal return:pa'], '11-1': ['kjv_jobab_madon', 'kjv_shimron_city'], '11-4': ['as sand', 'many:ev'], '11-6': ['tomorrow about this time', 'ipl deliver:fu', 'kjv_hough:fu'], '11-9': ['kjv_hough:pa', 'burn:caus:pa'], '11-13': ['none of they:a burn:caus:pa except kjv_hazor'], '11-16': ['kjv_goshen_canaan'], '11-18': ['long time'], '11-19': ['except kjv_hivite:pl of kjv_gibeon'], '11-20': ['of kjv_lord it be:pa', 'heart:pl:a hard make:inf', 'no favour'], '11-22': ['none', 'only in kjv_gaza in kjv_gath and in kjv_ashdod'], '11-23': ['whole land:a', 'land from war rest:pa'], '12-2': ['half kjv_gilead'], '12-6': ['half of kjv_manasseh kjv_tribe'], '12-13': ['kjv_debir_city'], '12-15': ['kjv_libnah_city', 'kjv_adullam_city'], '12-17': ['kjv_hepher_city'], '12-22': ['of kjv_carmel kjv_jokneam'], '12-23': ['of kjv_gilgal nation:pl king'], '12-24': ['kjv_tirzah_city', 'all king:pl thirty and one_num']}
        for ref, parts in checks.items():
            for part in parts:
                self.assertIn(part, cases['joshua-' + ref]['analysis'])
        self.assertNotEqual(lang.lexicon['kjv_league']['meaning'], lang.lexicon['league']['meaning'])
        self.assertEqual(lang.lexicon['kjv_tirzah']['form'], lang.lexicon['kjv_tirzah_city']['form'])
        self.assertNotEqual(lang.lexicon['kjv_tirzah']['semanticId'], lang.lexicon['kjv_tirzah_city']['semanticId'])
        self.assertNotEqual(lang.compile('i be:pr')['text'], lang.compile('ipl be:pr')['text'])
        self.assertNotEqual(lang.compile('wepl be:pr')['text'], lang.compile('wesg be:pr')['text'])
        self.assertEqual('data/language/archaic-kjv-32', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
