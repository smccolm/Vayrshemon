import unittest
from tools.kjv_archive import load_register,read


class SanctuaryRegisterTests(unittest.TestCase):
    def test_exact_technical_cases_and_person_contrasts(self):
        parent,_=load_register('0.10-kjv.13')
        lang,manifest=load_register('0.10-kjv.14')
        self.assertEqual(parent.lexicon,{k:lang.lexicon[k] for k in parent.lexicon})
        for name in ('pairs','suffix','possessors','roman'):
            self.assertEqual(getattr(parent,name),getattr(lang,name))
        cases={c['id']:c for c in read(lang.folder/'sanctuary-cases.json')}
        self.assertEqual(243,len(cases))
        for case in cases.values():
            with self.subTest(verse=case['id']):
                actual=lang.compile(case['analysis'])
                self.assertEqual(case['expectedText'],actual['text'])
                self.assertEqual(case['expectedGloss'],actual['gloss'])
        checks={
            'exodus-25-22':['between two kjv_cherub:pl','ipl meet:fu'],
            'exodus-25-34':['kjv_candlestick:pl'],
            'exodus-26-2':['two+ten and eight kjv_cubit:pl'],
            'exodus-26-25':['ten and six kjv_socket:pl'],
            'exodus-28-30':['kjv_urim and kjv_thummim','his/heart'],
            'exodus-29-20':['kjv_right_side:m ear/end','kjv_thumb'],
            'exodus-29-42':['with you:pl ipl meet:fu','to thou speak:inf'],
            'exodus-29-45':['their/kjv_god ipl be:fu'],
            'exodus-30-23':['two+hundred and five+ten'],
            'exodus-30-32':['upon of man flesh it pour:psv:fu not'],
            'exodus-31-17':['between ipl','kjv_lord:n make:pa','he rest:pa and kjv_refresh:psv:pa'],
            'exodus-31-18':['two of testimony table:pl','of kjv_god finger']}
        for key,parts in checks.items():
            for part in parts:self.assertIn(part,cases[key]['analysis'])
        self.assertNotIn('kjv_ephah',cases['exodus-29-40']['analysis'])
        for left,right in [('kjv_table_furniture','table'),('kjv_cast_metal','cast'),('kjv_wave_present','kjv_wave'),('kjv_crown_moulding','crown')]:
            self.assertNotEqual(lang.word(left)[1],lang.word(right)[1])
        for a in read(lang.folder/'additions.json'):
            self.assertTrue(set(a['form'])<=lang.letters|set('’ -'),a['key'])
            if a['derivationKeys']:self.assertEqual(a['form'],''.join(lang.lexicon[k]['form'] for k in a['derivationKeys']))
        self.assertEqual('data/language/archaic-kjv-13',manifest['basePackage'])


if __name__=='__main__':unittest.main()
