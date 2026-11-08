"""Readable labels must not change native names, referents or inherited editions."""
import json
import unittest
from tools.editorial_language import EditorialLanguage,ROOT


class DramaticNamesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=EditorialLanguage(ROOT/'data/language/later-dramatic-0.12')
        cls.new=EditorialLanguage(ROOT/'data/language/later-dramatic-0.13')

    def test_lookup_qualifiers_never_print_as_names(self):
        for key,name in [('bottom_name','Bottom'),('flute_name','Flute'),('snout_name','Snout'),('cobweb_name','Cobweb'),('mote_name','Mote')]:
            self.assertEqual(name,self.new.word(key)[1])
            self.assertEqual(name+'-head(nom.)',self.new.word(key+'/head:n')[1])
            self.assertEqual(self.old.word(key+'/head:n')[0],self.new.word(key+'/head:n')[0])
        self.assertEqual('my-Bottom-head(nom.)',self.new.word('my/bottom_name/head:n')[1])
        self.assertEqual('Bottom-Flute-name(nom.)',self.new.word('bottom_name+flute_name/name:n')[1])
        self.assertEqual('bottom_name-head(nom.)',self.old.word('bottom_name/head:n')[1])

    def test_homonymous_people_remain_different(self):
        for key,parent in [('francis_flute','francis'),('helen_troy','helen')]:
            self.assertEqual(self.new.word(parent)[0],self.new.word(key)[0])
            self.assertNotEqual(self.new.lexicon[parent]['semanticId'],self.new.lexicon[key]['semanticId'])
        self.assertIn('goddess',self.new.lexicon['dian']['meaning'])
        self.assertIn('Widow',self.new.lexicon['diana']['meaning'])

    def test_native_ratification_keeps_repetition_and_force(self):
        self.assertEqual('kom rē’ne',self.new.reading(self.new.word('amen')[0]))
        self.assertEqual('so-be(opt.)',self.new.word('amen')[1])
        self.assertEqual(self.old.compile('amen, amen.')['text'],self.new.compile('amen, amen.')['text'])
        self.assertEqual(['amen','amen'],self.new.compile('amen, amen.')['keys'])

    def test_ordinary_cultural_terms_are_native_derivations(self):
        from tools.dramatic_name_review import NATIVE
        for key,(parts,separator,pos,gloss,meaning) in NATIVE.items():
            e=self.new.lexicon[key]
            self.assertEqual(separator.join(self.new.lexicon[k]['form'] for k in parts),e['form'])
            self.assertNotEqual(self.old.lexicon[key]['form'],e['form'])
            self.assertNotEqual('proper',e['pos'])
            self.assertEqual(gloss,self.new.word(key)[1])
        self.assertEqual('thalsōlum',self.new.reading(self.new.word('centaur')[0]))

    def test_theatrical_distortions_are_preserved(self):
        for key in ['ercles','phibbus','thisne','limander','shafalus','procrus']:
            self.assertEqual(self.old.lexicon[key],self.new.lexicon[key])
            self.assertEqual(self.old.word(key),self.new.word(key))
        self.assertNotEqual(self.new.word('thisne')[0],self.new.word('thisbe')[0])

    def test_maxima_and_pronoun_possession_are_preserved(self):
        self.assertEqual(self.old.pairs,self.new.pairs)
        for analysis in ['my/head:n.','ourone/heart:n.','ourpl/heart:n.','i:dep i speak:pr.','ipl:dep ipl speak:pr.','wesg:dep wesg speak:pr.','wepl:dep wepl speak:pr.','go:imp:excl:add.']:
            self.assertEqual(self.old.compile(analysis),self.new.compile(analysis))
        self.assertEqual('Botem',self.new.reading(self.new.word('bottom_name')[0]))

    def test_only_four_authored_reference_repairs(self):
        data=json.loads((self.new.folder/'name-decisions.json').read_text(encoding='utf8'))
        self.assertEqual({'0027':['diana','dian'],'0097':['francis','francis_flute'],'0611':['helen','helen_troy'],'0672':['helen','helen_troy']},data['sourceUnitRepairs'])
        self.assertEqual(0,data['jesusOccurrences'])

    def test_existing_composed_frame_can_be_rebuilt_twice(self):
        from types import SimpleNamespace
        from tools.compose_historical_book import body,texts
        face=SimpleNamespace(font_id='script',sha256='a'*64,cmap={ord(c):1 for c in 'ABC '})
        literal=SimpleNamespace(font_id='literal',sha256='b'*64,cmap={ord(c):1 for c in 'ABC. '})
        style=dict(styleId='body',fontId='script',fontSizeMicroPoints='50000000',lineHeight=dict(mode='exact',microPoints='38000000'))
        frame=dict(content=dict(document=dict(styles=[style],fonts=[dict(fontId='script')],stories=[dict(blocks=[dict(runs=[dict(styleId='body')])])]),styleFeatures={}))
        body(frame,['A.'],face,literal,0)
        body(frame,['BC.','A.'],face,literal,0)
        self.assertEqual(['BC.','A.'],texts(frame))
        styles=frame['content']['document']['styles']
        self.assertEqual(len(styles),len({s['styleId'] for s in styles}))
        self.assertEqual('50000000',next(s for s in styles if s['styleId']=='body')['fontSizeMicroPoints'])


if __name__=='__main__':unittest.main()
