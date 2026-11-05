import unittest
from tools.kjv_archive import load_register, read

class JudgesOpeningTests(unittest.TestCase):
    def test_complete_section_and_speaker_scopes(self):
        old, _ = load_register('0.10-kjv.35')
        lang, manifest = load_register('0.10-kjv.36')
        self.assertEqual(old.lexicon, {k: lang.lexicon[k] for k in old.lexicon})
        for field in ('pairs','suffix','prefix','possessors','roman'):
            self.assertEqual(getattr(old,field),getattr(lang,field))
        cases={c['id']:c for c in read(lang.folder/'judges-opening-cases.json')}
        self.assertEqual(145,len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                result=lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'],result['text'])
                self.assertEqual(c['expectedGloss'],result['gloss'])
        checks={'1-1': ['for wesg', 'after of kjv_joshua death'], '1-2': ['his/hand ipl deliver:perf'], '1-3': ['with ipl into mypl/kjv_lot_portion', 'we:du fight:pr:may', 'ipl go:fu'], '1-4': ['ten+thousand'], '1-7': ['seven+ten', 'their/food', 'my/table', 'as i do:perf'], '1-8': ['fight:pp', 'take:pp', 'set:pp'], '1-13': ['younger brother'], '1-14': ['she urge:pa', 'ass she descend:pa'], '1-15': ['kjv_upper', 'kjv_lower'], '1-16': ['kjv_kenite', 'father+in+law', 'kjv_palm_tree'], '1-19': ['kjv_lord with kjv_judah', 'be:pa:can not', 'of iron chariot:pl'], '1-21': ['kjv_benjamin', 'to this day'], '1-24': ['to wepl', 'wepl show:fu'], '1-26': ['city:a build:pa', 'kjv_luz call:pa'], '1-27': ['kjv_bethshean', 'kjv_taanach', 'kjv_dor', 'kjv_ibleam', 'kjv_megiddo', 'dwell:inf kjv_canaanite:pl will:pa'], '1-28': ['kjv_tribute', 'drive:pa not out'], '1-32': ['kjv_asherite:pl among kjv_canaanite:pl'], '1-34': ['kjv_amorite:pl', 'force:pa', 'they will:pa not'], '1-35': ['kjv_heres', 'kjv_aijalon', 'kjv_shaalbim', 'kjv_tribute'], '2-1': ['of kjv_lord angel', 'ipl make:pa', 'mypl/kjv_covenant', 'never ipl break:fu'], '2-2': ['no kjv_league', 'mypl/voice', 'why this'], '2-3': ['ipl drive:fu not out', 'thorn:pl', 'snare'], '2-6': ['kjv_joshua people:a go:inf let:pp'], '2-7': ['see:pp'], '2-9': ['kjv_timnathheres'], '2-10': ['another generation', 'know:pa not'], '2-13': ['kjv_baal_deity', 'kjv_ashtaroth_deities'], '2-14': ['sell:pa', 'be:pa:can'], '2-15': ['against they for evil'], '2-17': ['will:pa not', 'kjv_whoring:pa'], '2-18': ['groan:ev:pl', 'kjv_relent:pa'], '2-20': ['mypl/kjv_covenant', 'mypl/voice'], '2-22': ['ipl test:pr:may', 'or not'], '2-23': ['neither they:a', 'he deliver:pa'], '3-2': ['war:a they:a teach:inf'], '3-7': ['kjv_grove_cult:pl'], '3-8': ['kjv_chushanrishathaim', 'eight year:pl'], '3-10': ['spirit upon he come:pa'], '3-12': ['kjv_lord kjv_eglon_king', 'strengthen:pa'], '3-15': ['left+hand man', 'gift:a'], '3-16': ['two edge:pl', 'kjv_cubit length', 'kjv_right_side thigh'], '3-17': ['fat man'], '3-18': ['carry:pa'], '3-19': ['kjv_quarry:pl', 'kjv_errand:a', 'i have:pr'], '3-20': ['from god kjv_message:a to thou i have:pr'], '3-22': ['kjv_haft', 'kjv_fat', 'be:pa:can not', 'kjv_filth come:pa'], '3-24': ['his/foot:pl:a', 'cover:pr'], '3-25': ['ashamed', 'key:a', 'dead fall:pp'], '3-29': ['about ten+thousand', 'all strong', 'no man escape:pa'], '3-30': ['eight+ten'], '3-31': ['six+hundred', 'ox kjv_goad'], '4-3': ['nine+hundred', 'twenty year:pl'], '4-4': ['kjv_deborah_judge kjv_prophetess', 'she kjv_israel:a', 'judge:pa'], '4-7': ['kjv_kishon_river', 'ipl draw:fu', 'ipl deliver:fu'], '4-8': ['then i go:fu', 'then i go:fu not'], '4-9': ['i go:fu', 'thy/honour be:fu not', 'of woman hand'], '4-11': ['kjv_heber_kenite', 'kjv_zaanaim kjv_plain_land'], '4-14': ['rise:imp:excl', 'go:perf out not?'], '4-15': ['kjv_discomfit:pa', 'descend:pa down'], '4-17': ['peace between', 'of kjv_heber_kenite'], '4-19': ['little water', 'of milk kjv_bottle'], '4-20': ['any man here be:pr?', 'no thou say:fu'], '4-21': ['kjv_temple_head:pl', 'deeply asleep and weary'], '5-3': ['i even i', 'i praise:a'], '5-4': ['thou out of kjv_seir', 'water:a drop:pa'], '5-7': ['i kjv_deborah_judge', 'as mother', 'i rise:pa'], '5-8': ['forty+thousand', 'see:psv:pa be:pa?'], '5-11': ['kjv_archer:pl noise', 'tell:fu'], '5-12': ['thy/kjv_captivity:a captive lead:imp'], '5-13': ['he:a who remain:pr', 'kjv_lord i:a'], '5-14': ['write:ag pen:a hold:pr'], '5-15': ['heart thought:pl'], '5-16': ['heart search:ev:pl'], '5-17': ['in ship:pl', 'kjv_breach_coast'], '5-20': ['star:pl in their/course:pl', 'fight:pa'], '5-21': ['that ancient river', 'my/soul'], '5-22': ['kjv_prance:ev:pl kjv_prance:ev:pl', 'break:psv:pa'], '5-23': ['of kjv_lord help to of kjv_lord help'], '5-25': ['butter:a', 'lord:adj kjv_dish'], '5-26': ['his/head:a she strike:pa off'], '5-27': ['where he bow:pa there dead he fall:pa down'], '5-28': ['mother', 'why'], '5-29': ['to herself'], '5-30': ['maiden or two', 'on both side:pl', 'neck:pl?'], '5-31': ['thy/enemy:pl', 'who he:a love:pr', 'forty year:pl']}
        for ref,parts in checks.items():
            for part in parts:self.assertIn(part,cases['judges-'+ref]['analysis'])
        self.assertNotEqual(lang.compile('wepl serve:fu')['text'],lang.compile('wesg serve:fu')['text'])
        self.assertIn('we:du fight:pr:may',cases['judges-1-3']['analysis'])
        self.assertIn('i kjv_deborah_judge',cases['judges-5-7']['analysis'])
        self.assertIn('ipl draw:fu',cases['judges-4-7']['analysis'])
        self.assertEqual(4,cases['judges-5-12']['analysis'].count('awake:imp:excl'))
        self.assertIn('set:pp',cases['judges-4-11']['analysis'])
        self.assertNotIn('pitch:',cases['judges-4-11']['analysis'])
        self.assertNotEqual(lang.lexicon['temple']['meaning'],lang.lexicon['kjv_temple_head']['meaning'])
        self.assertEqual('data/language/archaic-kjv-35',manifest['basePackage'])

if __name__=='__main__':unittest.main()
