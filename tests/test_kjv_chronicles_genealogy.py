import unittest
from tools.kjv_archive import load_register, read


class ChroniclesGenealogyTests(unittest.TestCase):
    def test_namesakes_source_variants_and_unexpanded_lists(self):
        prior, _ = load_register('0.10-kjv.75')
        lang, manifest = load_register('0.10-kjv.76')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'chronicles-genealogy-cases.json')}
        self.assertEqual(54, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
            self.assertFalse({'i','ipl','wesg','wepl'} & set(result['keys']))
        for ref, parts in {
            '1': ['kjv_sheth_adam', 'kjv_enosh'],
            '4': ['kjv_noah kjv_shem kjv_ham and kjv_japheth'],
            '7': ['kjv_tarshish_person'],
            '8': ['kjv_put_person'],
            '12': ['kjv_casluhim:a [of whom kjv_philistine:pl come:pa]'],
            '17': ['kjv_meshech_shem'],
            '18': ['kjv_shelah_arphaxad'],
            '19': ['two son:pl', 'name of one_num', 'earth kjv_divide:psv:pa'],
            '22': ['kjv_ebal_joktan'],
            '27': ['kjv_abram same kjv_abraham be:pr'],
            '30': ['kjv_hadad_ishmael'],
            '33': ['kjv_henoch_midian', 'kjv_abida'],
            '36': ['kjv_timna and kjv_amalek'],
            '38': ['kjv_ezar'],
            '39': ['kjv_timna sister of kjv_lotan'],
            '40': ['kjv_aiah_zibeon'],
            '41': ['kjv_amram_dishon'],
            '42': ['kjv_ezer'],
            '43': ['before any king over child:pl of kjv_israel', 'kjv_bela_king'],
            '44': ['kjv_jobab_king'],
            '48': ['kjv_shaul_edom', 'kjv_rehoboth_river'],
            '50': ['kjv_hadad_pai', 'kjv_pai'],
            '51': ['kjv_hadad_pai also die:pa', 'kjv_duke kjv_aliah'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['1-chronicles-1-' + ref]['analysis'])
        for ref in ['1','2','3','4','24','25','26']:
            keys = lang.compile(cases['1-chronicles-1-' + ref]['analysis'])['keys']
            self.assertNotIn('son', keys)
            self.assertNotIn('beget', keys)
        self.assertEqual('data/language/archaic-kjv-75', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
