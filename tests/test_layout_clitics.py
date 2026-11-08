import unittest
from tools.layout_clitics import apply, ID, apply_gloss, GLOSS_ID, gloss_rule
from tools.kjv_archive import load_register
from vayrshemon.session import utf16_length


class CliticBreakTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lang,_=load_register('0.10-kjv.281')

    def frame(self,text):
        return {'content':{'document':{'stories':[{'blocks':[{'runs':[{'runId':'run.fixture','type':'legacy','sourceText':text,'languageId':'language.vayrshemon'}]}]}]},'characters':[{'start':0,'end':utf16_length(text),'attributes':{'tracking':0}}]}}

    def test_break_is_only_at_a_bound_clitic_and_keeps_exact_text(self):
        analysis='kjv_congregation/kjv_tabernacle:relpair'
        text=self.lang.compile(analysis)['text'];frame=self.frame(text)
        self.assertEqual(1,apply(frame,[{'analysis':analysis}],self.lang))
        runs=frame['content']['document']['stories'][0]['blocks'][0]['runs']
        self.assertEqual(text,''.join(r['sourceText'] for r in runs))
        boundary=[r for r in runs if r['languageId']==ID]
        self.assertEqual(1,len(boundary));self.assertEqual(1,len(boundary[0]['sourceText']))
        tail=next(i for i,r in enumerate(runs) if r['languageId']==ID)
        self.assertTrue(runs[tail+1]['sourceText'].startswith('’yë'))
        spans=frame['content']['characters']
        self.assertEqual(0,spans[0]['start']);self.assertEqual(utf16_length(text),spans[-1]['end'])
        self.assertTrue(all(a['end']==b['start'] for a,b in zip(spans,spans[1:])))

    def test_ordinary_possessive_and_short_host_do_not_gain_breaks(self):
        for analysis in ('kjv_congregation/kjv_tabernacle','he:add','holy holy holy'):
            text=self.lang.compile(analysis)['text'];frame=self.frame(text)
            self.assertEqual(0,apply(frame,[{'analysis':analysis}],self.lang))
            self.assertEqual(text,frame['content']['document']['stories'][0]['blocks'][0]['runs'][0]['sourceText'])

    def test_long_gloss_tags_wrap_without_splitting_compound_hyphens(self):
        text='when(unmarked.continuation) · their-faith · see(pst.)'
        frame=self.frame(text);self.assertGreater(apply_gloss(frame),0)
        runs=frame['content']['document']['stories'][0]['blocks'][0]['runs']
        self.assertEqual(text,''.join(r['sourceText'] for r in runs))
        self.assertEqual('-',gloss_rule()['prohibitAfter'])
        self.assertTrue(all(r['sourceText'] in ',.-' for r in runs if r['languageId']==GLOSS_ID))

    def test_genesis_isles_possessive_can_wrap_at_native_boundaries(self):
        lang,_=load_register('0.10-kjv.285')
        analysis='nation:pl/kjv_isle:pl:n'
        text=lang.compile(analysis)['text']
        frame=self.frame(text)
        self.assertEqual(apply(frame,[{'analysis':analysis}],lang),0)
        self.assertGreater(apply(frame,[{'analysis':analysis}],lang,lexical_boundaries=True),0)
        runs=frame['content']['document']['stories'][0]['blocks'][0]['runs']
        self.assertEqual(''.join(r['sourceText'] for r in runs),text)
        offsets=set();end=0
        for r in runs:
            end+=len(r['sourceText'])
            if r['languageId']==ID:offsets.add(end)
        self.assertIn(text.index('’'),offsets)
        self.assertIn(text.index(lang.lexicon['sea']['form'])+len(lang.lexicon['sea']['form']),offsets)
