"""Four-column reading rows align without rewriting or shrinking their text."""
from copy import deepcopy
from pathlib import Path
import unittest,uuid
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QCoreApplication,QEvent,QMimeData
from PySide6.QtGui import QInputMethodEvent
from PySide6.QtTest import QTest
from vayrshemon.gloss_api import GlossSession,GlossAPI
from vayrshemon.file_api import FileSession
from vayrshemon.paragraph_alignment import without_before
from vayrshemon.session import utf16_length
from vayrshemon import pages
from tools.parallel_translation_fixture import paragraph_starts

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class FourColumnFixture:
    session_type=GlossSession

    def setUp(self):
        self.s=self.session_type(getattr(self,'root',ROOT),source_fonts=False,recovery=False);self.api=GlossAPI(self.s);self.ids=[]
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


class ParagraphAlignmentTests(FourColumnFixture,unittest.TestCase):
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


class KeyboardAlignmentTests(FourColumnFixture,unittest.TestCase):
    session_type=FileSession

    def setUp(self):
        import shutil, tempfile
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        shutil.copytree(ROOT/'schemas', self.root/'schemas')
        for part in ('runtime-fonts', 'orthography', 'keyboard'):
            shutil.copytree(ROOT/'data'/part, self.root/'data'/part)
        shutil.copy2(ROOT/'data/fonts.json', self.root/'data/fonts.json')
        super().setUp()

    def test_align_one_row_and_keep_manual_spacing_while_typing(self):
        from vayrshemon.file_api import FileAPI
        from vayrshemon.file_window import FileWindow
        from vayrshemon.session import SCALE
        from vayrshemon.typesetting import Composition

        def rows():
            columns = []
            for page in self.s.state['pages']:
                composition = Composition(self.s, page_id=page['pageId'], line_metrics=True)
                for frame in page['frames']:
                    lines = [l for l in composition.lines if l['frameId'] == frame['frameId']]
                    columns.append([l['baseline']/SCALE for i, l in enumerate(lines)
                                    if i == 0 or lines[i-1]['blockId'] != l['blockId']])
            return list(zip(*columns))

        self.call('page.paragraphs.align')
        w = FileWindow(self.s, FileAPI(self.s))
        try:
            w.show()
            w.configure_workspace(source=True)
            pos = self.s.active.doc.lastBlock().position()
            self.call('selection.set', frame_id=self.ids[-1], start=pos+2, end=pos+3)
            APP.processEvents()
            controls = w.paragraph_controls
            initial = rows()
            saved = self.s.capture()['pages']
            selection = self.s.selection()
            field = controls.fields['before']
            field.setValue(max(field.value(), 24) + 10)
            QTest.mouseClick(controls.apply, Qt.MouseButton.LeftButton)
            self.assertFalse(controls.auto.isChecked(), (w.last_error, controls.isEnabled(), w.editor.textCursor().blockNumber(), field.value()))
            self.assertEqual(self.s.selection(), selection)
            manual = self.s.capture()['pages']
            moved = rows()
            self.assertEqual(moved[:-1], initial[:-1])
            self.assertGreater(max(moved[-1])-min(moved[-1]), 9)
            self.call('selection.set', start=pos+1, end=pos+1)
            QTest.keyClicks(w.editor, 'x')
            self.assertEqual(self.s.automatic_alignment['status'], 'manual')
            self.call('history.undo')
            self.assertEqual(self.s.capture()['pages'], manual)
            before = self.s.revision
            QTest.mouseClick(controls.match, Qt.MouseButton.LeftButton)
            self.assertEqual(self.s.revision, before+1, w.last_error)
            final = rows()
            self.assertEqual(final[:-1], initial[:-1])
            self.assertLessEqual(max(final[-1])-min(final[-1]), .02)
            after = self.s.capture()['pages']
            for old_page, new_page in zip(saved, after):
                for old, new in zip(old_page['frames'], new_page['frames']):
                    self.assertEqual(without_before(old), without_before(new))
            QTest.mouseClick(controls.match, Qt.MouseButton.LeftButton)
            self.assertEqual(self.s.revision, before+1)
            self.call('history.undo')
            self.assertEqual(self.s.capture()['pages'], manual)
            self.call('history.redo')
            self.assertEqual(self.s.capture()['pages'], after)
        finally:
            self.s.spread_auto_alignment(self.ids[0], True)
            w.job_timer.stop()
            w.forge_panel.timer.stop()
            w.timer.stop()
            w.hide()
            self.s.window = self.s._editor = None
            w.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_one_typing_edit_recovers_and_undoes_all_reflowed_columns(self):
        from vayrshemon.typing_storage import read_checkpoint
        self.call('page.paragraphs.align')
        book=self.s
        book.recovery_enabled=True
        book.checkpoint()
        before=book.capture()
        with book.typing_command('Input method'):
            book.active.edit(0,0,'A clearer translation takes some more words. '*4)
        self.assertGreater(len(book._undo[-1].contents),1)
        self.assertEqual(book.automatic_alignment['status'],'aligned')
        after=book.capture()
        self.assertEqual(read_checkpoint(book.recovery_path,book.max_file_bytes)['state'],after)
        self.call('history.undo')
        self.assertEqual(book.capture()['pages'],before['pages'])
        self.call('history.redo')
        self.assertEqual(book.capture()['pages'],after['pages'])


if __name__=='__main__':unittest.main()
