"""Four-column reading rows align without rewriting or shrinking their text."""
from copy import deepcopy
from pathlib import Path
import unittest,uuid
from PySide6.QtWidgets import QApplication
from vayrshemon.gloss_api import GlossSession,GlossAPI
from vayrshemon.paragraph_alignment import without_before
from vayrshemon.session import utf16_length

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class ParagraphAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.s=GlossSession(ROOT,source_fonts=False,recovery=False);self.api=GlossAPI(self.s);self.ids=[]
        self.call('page.configure',width=600,height=1000)
        for i in range(4):
            if i==2:self.call('page.add',width=600,height=1000)
            elif i==1 or i==3:self.call('frame.add',x=310,y=40,width=240,height=900,name='Synthetic column')
            self.call('frame.configure',x=40 if i%2==0 else 310,y=40,width=240,height=900)
            self.ids.append(self.s.state['activeFrameId'])
            text='\n'.join(('Synthetic text. '*n).strip() for n in ([3,1,2],[1,3,1],[2,2,4],[1,1,1])[i])
            self.call('document.edit',start=0,end=utf16_length(self.s.active.text()),text=text)
            self.call('document.format',start=0,end=utf16_length(text),size=26 if i==0 else 18)
            self.call('paragraph.format',start=0,end=utf16_length(text),before=1,after=24,lineHeight=dict(mode='exact',value=38))
            self.call('typesetting.configure',enabled=i<2,grid=dict(enabled=False,step=12,offset=0))

    def tearDown(self):self.s.finish()

    def call(self,method,**params):
        r=self.api.call(method,params,expected_revision=self.s.revision,idempotency_key=uuid.uuid4().hex)
        self.assertTrue(r['ok'],r);return r['result']

    def test_baselines_typography_one_undo_and_repeat(self):
        before=self.s.capture();revision=self.s.revision
        result=self.call('page.paragraphs.align')
        self.assertEqual(result['paragraphs'],3);self.assertLessEqual(result['maxErrorPt'],.02)
        self.assertEqual(self.s.revision,revision+1)
        aligned=self.s.capture()
        for a,b in zip(before['pages'],aligned['pages']):
            for old,new in zip(a['frames'],b['frames']):self.assertEqual(without_before(old),without_before(new))
        self.call('page.paragraphs.align');self.assertEqual(self.s.capture(),aligned)
        self.call('history.undo');restored=self.s.capture();restored['revision']=before['revision'];self.assertEqual(restored,before)
        self.call('history.redo');restored=self.s.capture();restored['revision']=aligned['revision'];self.assertEqual(restored,aligned)

    def test_count_mismatch_and_overset_leave_document_unchanged(self):
        self.call('document.edit',start=0,end=0,text='Extra paragraph.\n')
        before=self.s.capture();r=self.api.call('page.paragraphs.align',{},expected_revision=self.s.revision,idempotency_key=uuid.uuid4().hex)
        self.assertFalse(r['ok']);self.assertIn('COUNT_MISMATCH',str(r));self.assertEqual(self.s.capture(),before)
        self.call('history.undo');self.call('frame.configure',height=50)
        before=self.s.capture();history=deepcopy(self.s.history)
        r=self.api.call('page.paragraphs.align',{},expected_revision=self.s.revision,idempotency_key=uuid.uuid4().hex)
        self.assertFalse(r['ok']);self.assertIn('OVERSET',str(r));self.assertEqual(self.s.capture(),before);self.assertEqual(self.s.history,history)


if __name__=='__main__':unittest.main()
