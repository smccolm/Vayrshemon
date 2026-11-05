"""Later-register grammatical contrasts, including intentional repetitions."""
from collections import Counter
import json
import unittest
from tools.editorial_language import EditorialLanguage, ROOT, load_current


class DramaticFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lang = EditorialLanguage(ROOT/'data/language/later-dramatic-0.12')
        cls.parent = EditorialLanguage(ROOT/'data/language/later-dramatic-0.11')

    def test_inherited_words_and_case_map_are_unchanged(self):
        self.assertEqual(self.parent.pairs, self.lang.pairs)
        self.assertEqual(self.parent.roman, self.lang.roman)
        for key, entry in self.parent.lexicon.items():
            self.assertEqual(entry, self.lang.lexicon[key], key)
        self.assertEqual(6, len(self.lang.lexicon)-len(self.parent.lexicon))

    def test_current_pin_and_immutable_compiler_history(self):
        import hashlib
        current,pin=load_current()
        self.assertEqual('0.12',pin['version']);self.assertEqual(self.lang.folder,current.folder)
        manifest=json.loads((current.folder/'manifest.json').read_text(encoding='utf8'))
        self.assertEqual('8a2fea375887f59085624f64c85975be0cc95ae96bd90f40aaa2ca71e5901570',manifest['parentHead'])
        self.assertEqual('0.10-kjv.281',manifest['historicalReference']['version'])
        old=json.loads((self.parent.folder/'manifest.json').read_text(encoding='utf8'))
        archived=ROOT/'data/language/compiler-history'/(old['compilerSha256']+'.py')
        self.assertEqual(old['compilerSha256'],hashlib.sha256(archived.read_bytes()).hexdigest())

    def test_first_person_roles_are_not_collapsed(self):
        forms=[]
        for key in ('i','ipl','wesg','wepl'):
            result=self.lang.compile(f'to {key}:dep {key} speak:pr.')
            self.assertEqual(2, result['keys'].count(key))
            forms.append(self.lang.word(key+':dep')[0])
        self.assertEqual(4,len(set(forms)))
        for bad in ('king:dep','my/heart:dep','i:dep:pl'):
            with self.subTest(bad=bad),self.assertRaises(ValueError):self.lang.word(bad)

    def test_phrase_and_word_scope_are_separate(self):
        self.assertTrue(self.lang.reading(self.lang.word('go:imp:excl:add')[0]).endswith('’hā’oi'))
        self.assertEqual(self.lang.word('i')[0],self.lang.word('i:cont')[0])
        for bad in ('king:relpair:reltriple','i:add:cont','king:subend','go:add:imp','go:pr:subend:psv'):
            with self.subTest(bad=bad),self.assertRaises(ValueError):self.lang.word(bad)
        result=self.lang.compile('who i be:pr:subend be:pr.')
        self.assertEqual(2,result['keys'].count('be'))
        self.assertEqual(3,len({self.lang.word('father:'+f)[0] for f in ('relpair','reltriple','relquad')}))

    def test_explicit_source_decisions_conserve_content(self):
        decisions=json.loads((self.lang.folder/'decisions.json').read_text(encoding='utf8'))
        self.assertEqual(20,len(decisions['editorialRevisions']))
        for case in decisions['editorialRevisions']:
            before=self.parent.compile(case['before']);after=self.lang.compile(case['after'])
            self.assertEqual(Counter(before['keys'])-Counter({'and':1}),Counter(after['keys']))
            self.assertEqual(case['after'],case['before'].replace(case['windowBefore'],case['windowAfter']))
            self.assertTrue(case['source'] and case['reason'])

    def test_reviewed_corpus_maxima_and_readings(self):
        cases=json.loads((self.lang.folder/'flow-cases.json').read_text(encoding='utf8'))
        for case in cases:
            result=self.lang.compile(case['analysis'],initial=case['initial'])
            self.assertEqual(case['expectedText'],result['text'],case['id'])
            self.assertEqual(case['expectedGloss'],result['gloss'],case['id'])
        for analysis in ('no no no.','write:imp write:imp.','truth truth be:pr.','which which be:pr.','and i.'):
            self.assertEqual(self.parent.compile(analysis),self.lang.compile(analysis))

