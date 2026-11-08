import unittest
from tools.kjv_archive import load_register, read
from tools.kjv_native_vocabulary import VERSION, PACKAGE, prior


class HistoricalNativeVocabulary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lang, _ = load_register(VERSION)

    def test_source_alphabet_and_ordinary_last(self):
        lang=self.lang
        word=lambda k:lang.reading(lang.word(k)[0])
        self.assertEqual(word('last'),word('end:adj'))
        self.assertEqual(word('kjv_omega_letter_revelation'),word('last')+' '+word('write')+word('mark'))
        self.assertEqual(word('kjv_alpha_letter_revelation'),word('first')+' '+word('write')+word('mark'))
        self.assertEqual(word('kjv_omega_letter_revelation'),'hüŧh’na īvden')
        self.assertFalse(any('endin' in e['form'].casefold() for e in lang.lexicon.values()))

    def test_native_roots_and_two_kinds_of_bark(self):
        form=lambda k:self.lang.lexicon[k]['form']
        self.assertEqual(form('tree_bark'),'yëlshal')
        self.assertNotEqual(form('tree_bark'),form('bark'))
        self.assertEqual(form('wink'),form('eye')+form('shut'))
        self.assertEqual(form('wake'),form('awaken'))
        self.assertIn(form('drum'),form('kjv_timbrel'))
        self.assertIn(form('sea'),form('kjv_red_sea'))
        self.assertNotEqual(form('kjv_jachin_pillar'),form('kjv_jachin'))

    def test_name_identity_affiliation_and_quantity(self):
        parent,_=load_register(prior.VERSION)
        for k,v in parent.lexicon.items():
            self.assertEqual(v.get('semanticId'),self.lang.lexicon[k].get('semanticId'),k)
        self.assertEqual(self.lang.lexicon['kjv_jerusalem']['roman'],'yerūshalem')
        self.assertTrue(self.lang.lexicon['kjv_tishbite']['form'].endswith('’na'))
        self.assertEqual(self.lang.lexicon['kjv_jesus_matthew']['roman'],'yeshūa')
        for k in read(PACKAGE/'quantities.json'):
            self.assertEqual(self.lang.lexicon[k],parent.lexicon[k],k)

    def test_current_flow_fixtures(self):
        for row in read(PACKAGE/'flow-cases.json'):
            result=self.lang.compile(row['analysis'])
            self.assertEqual(result['text'],row['text'],row['reference'])
            self.assertEqual(result['gloss'],row['gloss'],row['reference'])

    def test_offices_and_affiliations_have_native_structure(self):
        lex=self.lang.lexicon
        self.assertEqual(lex['kjv_roman_john']['form'],self.lang.maxima(lex['kjv_rome_acts']['form'])+'’na')
        self.assertEqual(lex['kjv_syrian']['form'],self.lang.maxima(lex['kjv_syria']['form'])+'’na')
        self.assertIn(lex['cup']['form'],lex['kjv_rabshakeh']['form'])
        self.assertIn(lex['house']['form'],lex['kjv_rabsaris']['form'])
        self.assertNotEqual(lex['kjv_rabsaris']['semanticId'],lex['kjv_rabsaris_babylon']['semanticId'])
        self.assertNotEqual(lex['kjv_tartan']['form'],lex['kjv_rabshakeh']['form'])
        keys=['kjv_sabeans_'+b for b in ('job','isaiah','ezekiel','joel')]
        self.assertEqual(len({lex[k]['semanticId'] for k in keys}),4)
        self.assertTrue(all(lex[k]['form'].endswith(' '+lex['group']['form']) for k in keys))
