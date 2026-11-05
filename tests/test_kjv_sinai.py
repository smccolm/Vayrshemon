import unittest
from tools.kjv_archive import load_register, read


class SinaiRegisterTests(unittest.TestCase):
    def test_person_identity_legal_senses_and_parent_are_preserved(self):
        parent,_=load_register('0.10-kjv.12')
        lang,manifest=load_register('0.10-kjv.13')
        self.assertEqual(parent.lexicon,{k:lang.lexicon[k] for k in parent.lexicon})
        for attr in ('pairs','suffix','roman','possessors'):
            self.assertEqual(getattr(parent,attr),getattr(lang,attr))
        cases={c['id']:c for c in read(lang.folder/'sinai-cases.json')}
        self.assertEqual(169,len(cases))
        for c in cases.values():
            with self.subTest(verse=c['id']):
                result=lang.compile(c['analysis'])
                self.assertEqual(c['expectedText'],result['text'])
                self.assertEqual(c['expectedGloss'],result['gloss'])
        checks={'exodus-19-4':['iplself'], 'exodus-19-8':['wesg'],
                'exodus-20-2':['ipl be:pr'],'exodus-20-3':['other kjv_god:pl'],
                'exodus-21-5':['i love:pr'],'exodus-21-22':['her/fruit:n from she depart:pr','harm:n follow:pr not'],
                'exodus-23-21':['in he mypl/name:n be:pr','he pardon:fu not'],
                'exodus-24-3':['one_num voice','wesg'],'exodus-24-14':['we:du']}
        for ref,parts in checks.items():
            for part in parts:self.assertIn(part,cases[ref]['analysis'])
        for left,right in [('kjv_stripe_blow','kjv_stripe'),('kjv_gore_horn','gore')]:
            self.assertNotEqual(lang.word(left)[1],lang.word(right)[1])
        self.assertEqual('data/language/archaic-kjv-12',manifest['basePackage'])


if __name__=='__main__':unittest.main()
