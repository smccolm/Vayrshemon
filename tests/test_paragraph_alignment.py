"""Four-column reading rows align without rewriting or shrinking their text."""
from copy import deepcopy
from pathlib import Path
import unittest,uuid
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QCoreApplication,QEvent,QMimeData
from PySide6.QtGui import QInputMethodEvent
from PySide6.QtTest import QTest
from vayrshemon.gloss_api import GlossSession,GlossAPI
from vayrshemon.paragraph_alignment import without_before
from vayrshemon.session import utf16_length
from vayrshemon import pages
from tools.parallel_translation_fixture import paragraph_starts

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

    def assert_aligned(self):
        starts=[]
        for page in self.s.state['pages']:
            report=pages.inspect(self.s,page_id=page['pageId'],max_glyphs=20000)
            starts.extend([[l['baseline'] for l in paragraph_starts(report,f['frameId'])] for f in page['frames']])
        for row in zip(*starts):self.assertLessEqual(max(row)-min(row),.027)

    def test_text_edit_reflows_in_same_undo_and_survives_save(self):
        self.call('page.paragraphs.align');before=self.s.capture();revision=self.s.revision
        self.call('document.edit',start=0,end=0,text='A clearer translation takes some more words. '*4)
        self.assertEqual(self.s.revision,revision+1);self.assert_aligned()
        self.assertEqual(self.s.automatic_alignment['status'],'aligned')
        after=self.s.capture();self.assertNotEqual(before['pages'][0]['frames'][0]['content']['paragraphs'],after['pages'][0]['frames'][0]['content']['paragraphs'])
        self.call('history.undo');restored=self.s.capture();restored['revision']=before['revision'];self.assertEqual(restored,before)
        self.call('history.redo');self.assert_aligned();self.assertEqual(self.s.capture()['pages'],after['pages'])
        directory=ROOT/'.local/test-automatic-alignment'/uuid.uuid4().hex;directory.mkdir(parents=True)
        self.call('document.save-as',path=str(directory/'reading.vay.json'))
        reopened=GlossSession(ROOT,source_fonts=False,recovery=False)
        try:
            reopened.open(directory/'reading.vay.json',advance_revision=False)
            self.assertEqual(reopened.capture()['pages'],after['pages'])
            r=GlossAPI(reopened).call('document.edit',dict(start=0,end=0,text='Again. '),expected_revision=reopened.revision,idempotency_key=uuid.uuid4().hex)
            self.assertTrue(r['ok'],r);self.assertEqual(reopened.automatic_alignment['status'],'aligned')
        finally:reopened.finish()

    def test_unequal_counts_pause_and_resume_without_losing_edits(self):
        self.call('page.paragraphs.align')
        for i,fid in enumerate(self.ids):
            self.call('frame.select',frame_id=fid);before=self.s.active.text()
            self.call('document.edit',start=0,end=0,text='New paragraph.\n')
            self.assertEqual(self.s.active.text(),'New paragraph.\n'+before)
            self.assertEqual(self.s.automatic_alignment['status'],'paused' if i<3 else 'aligned')
        self.assert_aligned()

    def test_overset_retains_text_and_spacing_until_text_fits(self):
        self.call('page.paragraphs.align');before=self.s.capture();revision=self.s.revision
        text='Lengthy synthetic test text. '*100
        self.call('document.edit',start=0,end=0,text=text)
        self.assertTrue(self.s.active.text().startswith(text));self.assertEqual(self.s.revision,revision+1)
        self.assertEqual(self.s.automatic_alignment['status'],'paused');self.assertIn('OVERSET',str(self.s.automatic_alignment))
        for a,b in zip(before['pages'],self.s.capture()['pages']):
            for old,new in zip(a['frames'],b['frames']):self.assertEqual(old['content']['paragraphs'],new['content']['paragraphs'])
        self.call('document.edit',start=0,end=utf16_length(text),text='');self.assert_aligned();self.assertEqual(self.s.automatic_alignment['status'],'aligned')

    def test_native_typing_paste_ime_close_and_reopen(self):
        from vayrshemon.gloss_window import GlossWindow
        self.call('page.paragraphs.align');w=GlossWindow(self.s,self.api);w.show();w.configure_workspace(source=True,diagnostics=False)
        try:
            self.call('selection.set',start=0,end=0);w.editor.setFocus();before=self.s.capture();revision=self.s.revision
            QTest.keyClicks(w.editor,'X');self.assertEqual(self.s.revision,revision+1);self.assert_aligned()
            self.call('history.undo');self.assertEqual(self.s.capture()['pages'],before['pages'])
            self.call('selection.set',start=0,end=0);mime=QMimeData();mime.setText('A clearer translation takes some more words. '*4)
            w.editor.insertFromMimeData(mime);self.assert_aligned();self.assertEqual(self.s.automatic_alignment['status'],'aligned')
            self.call('history.undo');self.assertEqual(self.s.capture()['pages'],before['pages'])
            self.call('selection.set',start=0,end=0);event=QInputMethodEvent();event.setCommitString('Z');QApplication.sendEvent(w.editor,event)
            self.assert_aligned();self.call('history.undo');self.assertEqual(self.s.capture()['pages'],before['pages'])
            snapshot=self.s.capture();QTest.mouseClick(w.close_source_button,Qt.MouseButton.LeftButton)
            self.assertFalse(w.workspace_state()['source']);self.assertEqual(self.s.capture(),snapshot)
            w.configure_workspace(source=True);self.assertTrue(w.close_source_button.isVisible());self.assertEqual(self.s.capture(),snapshot)
        finally:
            w.job_timer.stop();w.forge_panel.timer.stop();w.hide();self.s.window=None;self.s._editor=None;w.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)

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
