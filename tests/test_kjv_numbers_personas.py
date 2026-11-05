import unittest
from tools.kjv_archive import load_register,read

class NumbersPersonaTests(unittest.TestCase):
    def test_corporate_person_is_not_uniform_first_person(self):
        parent,_=load_register('0.10-kjv.22');lang,manifest=load_register('0.10-kjv.23')
        self.assertEqual(parent.lexicon,{k:lang.lexicon[k] for k in parent.lexicon})
        for f in ('pairs','suffix','possessors','roman'):
            self.assertEqual(getattr(parent,f),getattr(lang,f))
        cases={c['id']:c for c in read(lang.folder/'numbers-personas-cases.json')}
        self.assertEqual(245,len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                actual=lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'],actual['text'])
                self.assertEqual(c['expectedGloss'],actual['gloss'])
        checks={
          '17-6':['twelve rod:pl','among their/rod:pl'],
          '18-20':['ipl thy/part and thy/inheritance'],
          '18-26':['of tithe ten:ord part'],
          '19-12':['purify:pr not','kjv_clean_ritual he be:fu not'],
          '19-21':['water:a touch:pr','kjv_unclean_ritual'],
          '20-8':['to rock','speak:imp'], '20-10':['we:du'],
          '20-11':['two time:pl strike:pa'],
          '20-17':['wesg','ipl thee:a pray:pr'],
          '20-18':['against thee with sword ipl'],
          '20-19':['wesg go:fu','ipl and mypl/kjv_livestock','mypl/foot:pl'],
          '21-2':['mypl/hand','ipl completely destroy:fu'],
          '21-5':['no bread','this kjv_light_bread bread'],
          '22-14':['wepl'],'22-20':['ipl say:fu'],
          '22-28':['what to thee i do:perf','kjv_three time:pl'],
          '22-32':['against thee stand:inf i'],
          '22-33':['slay:pp:opt','save:pp:opt'],
          '23-19':['false he speak','his/mind:a he change'],
          '24-4':['kjv_trance','eye:pl open'],
          '24-17':['now not','near not','kjv_sheth/child:pl'],
          '25-8':['both of they','her/belly'],
          '25-9':['twenty+thousand and four+thousand'],
          '25-12':['mypl/kjv_covenant of peace','ipl give:pr']}
        for ref,parts in checks.items():
            for part in parts:self.assertIn(part,cases['numbers-'+ref]['analysis'])
        for ref in ('22-28','22-32'):self.assertNotIn('ipl',cases['numbers-'+ref]['analysis'])
        self.assertNotIn('strike',cases['numbers-20-8']['analysis'])
        self.assertNotIn('satan',cases['numbers-22-22']['analysis'])
        self.assertEqual('data/language/archaic-kjv-22',manifest['basePackage'])

if __name__=='__main__':unittest.main()
