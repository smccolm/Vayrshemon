"""Book loading must preserve validation and scan paragraph groups linearly."""
from copy import deepcopy
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator,ValidationError
from vayrshemon import schema_validation
from vayrshemon.automatic_alignment import AutomaticAlignment


class StateOnly:
    def _restore(self,state,**kwargs):self.state=state


class AlignmentScan(AutomaticAlignment,StateOnly):
    def locate(self,*args):raise AssertionError('Full-book search during restore')


def frame(fid,x,count=1,text='Structural test'):
    return dict(frameId=fid,x=str(x),content={'document':{'stories':[{
        'blocks':[{'runs':[{'text':text}]} for _ in range(count)]}]}})


class BookLoadingTests(unittest.TestCase):
    def test_restore_scans_pairs_directly_and_preserves_mismatch_diagnostics(self):
        state={'pages':[{'pageId':str(i),'frames':[frame(str(i)+'b',100),frame(str(i)+'a',0)]}
                        for i in range(1000)]}
        before=deepcopy(state)
        book=AlignmentScan()
        with patch('vayrshemon.automatic_alignment.spread_frames',side_effect=AssertionError('Repeated page search')):
            book._restore(state,take_ownership=True)
            self.assertEqual(book.automatic_alignment['status'],'ready')
            self.assertEqual(state,before)
            state['pages'][-1]['frames'][0]=frame('999b',100,2)
            book._restore(state)
        self.assertEqual(book.automatic_alignment['status'],'paused')
        self.assertEqual(book.automatic_alignment['issues'][0]['frameIds'],['998a','998b','999a','999b'])

    def test_accelerated_schema_matches_reference_without_mutating_data(self):
        self.assertIsNotNone(schema_validation.jsonschema_rs)
        schema={'type':'object','required':['n','text'],'additionalProperties':False,
                'properties':{'n':{'type':'integer','minimum':0,'maximum':65536},
                              'text':{'type':'string','maxLength':4},
                              'values':{'type':'array','uniqueItems':True,'items':{'enum':['a','b']}}}}
        cases=[{'n':0,'text':'É𐀀'}, {'n':1.0,'text':'x'}, {'n':True,'text':'x'},
               {'n':65537,'text':'x'}, {'n':1,'text':'12345'}, {'n':1},
               {'n':1,'text':'x','extra':0}, {'n':1,'text':'x','values':['a','a']},
               {'n':1,'text':'x','values':['a','b']}]
        for value in cases:
            before=deepcopy(value)
            if Draft202012Validator(schema).is_valid(value):schema_validation.validate(schema,value)
            else:
                with self.assertRaises(ValidationError):schema_validation.validate(schema,value)
            self.assertEqual(value,before)
