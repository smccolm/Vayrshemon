"""The user's standard bilingual page, independent of the open desktop session."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import unittest
import uuid

if os.name!='nt': os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from tools.m0.synthetic import make_font
from tools.parallel_translation_fixture import compose,definition,local_material,paragraph_starts
from vayrshemon.session import SCALE
from vayrshemon.typesetting_api import TypesettingAPI
from vayrshemon.typesetting_session import TypesettingSession

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class ParallelTranslationTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-parallel-translation'/uuid.uuid4().hex
        self.work.mkdir(parents=True)
        shutil.copytree(ROOT/'schemas',self.work/'schemas')
        for name in ('data/fonts.json','data/orthography/thimfora-79.json'):
            path=self.work/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,path)
        self.book=TypesettingSession(self.work,source_fonts=False,recovery=False)
        self.api=TypesettingAPI(self.book)

    def tearDown(self):
        self.book.finish()
        for frame in self.book.frames.values(): frame.deleteLater()
        self.book.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        APP.processEvents()

    def call(self,method,**params):
        result=self.api.call(method,params,expected_revision=self.book.revision,
                             document_id=self.book.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='fixture')
        self.assertTrue(result['ok'],result)
        return result['result']

    def assert_standard(self,ids,text):
        state=self.book.capture();self.assertEqual(len(state['pages']),1)
        page=state['pages'][0]
        self.assertEqual((page['width'],page['height']),('612000000','792000000'))
        self.assertEqual(page['margins'],dict(top='42000000',right='48000000',bottom='48000000',left='48000000'))
        self.assertEqual(len(page['frames']),2)
        self.assertEqual(state['typesetting']['flows'],[],'Translation must not be a continuation of the original')
        for role,x,language in [('original','48000000','language.vayrshemon'),('translation','324000000','language.en')]:
            frame=next(f for f in page['frames'] if f['frameId']==ids[role])
            self.assertEqual((frame['x'],frame['y'],frame['width'],frame['height']),(x,'42000000','240000000','702000000'))
            self.assertEqual(self.book.frames[ids[role]].text(),text[role])
            runs=[r for b in frame['content']['document']['stories'][0]['blocks'] for r in b['runs']]
            self.assertTrue(all(r['languageId']==language for r in runs))
            self.assertEqual(self.book.source_for(ids[role]),ids[role])
        report=self.call('layout.inspect')
        left=paragraph_starts(report,ids['original']);right=paragraph_starts(report,ids['translation'])
        self.assertEqual(len(left),2);self.assertEqual(len(right),2)
        for a,b in zip(left,right): self.assertAlmostEqual(a['baseline'],b['baseline'],places=4)
        for frame in report['frames']:
            bottom=frame['rect'][1]+frame['rect'][3]
            for line in frame['layout']['lines']: self.assertLessEqual(line['baseline']+line['descent'],bottom)
        return report

    def round_trip_and_export(self,ids,text):
        before=self.book.capture();report=self.assert_standard(ids,text)
        path=self.work/'parallel-translation.vay.json';self.call('document.save',path=str(path))
        self.call('document.open',path=str(path))
        after=self.book.capture()
        self.assertGreater(after['revision'],before['revision'])
        before['revision']=after['revision']
        self.assertEqual(after,before)
        reopened=self.assert_standard(ids,text);self.assertEqual(report['geometryHash'],reopened['geometryHash'])
        png=self.work/'parallel-translation.png'
        self.call('render.png',path=str(png),mode='mono',dpi=96)
        image=QImage(str(png));self.assertFalse(image.isNull());self.assertEqual((image.width(),image.height()),(816,1056))
        self.assertEqual(report['geometryHash'],self.call('layout.inspect')['geometryHash'])
        (self.work/'layout.json').write_text(json.dumps(reopened),encoding='utf-8')
        return reopened

    def test_public_layout_independent_edit_undo_and_round_trip(self):
        font=self.work/'synthetic.ttf';make_font(font)
        fid=self.call('fonts.load',path=str(font))['fontId']
        pairs=[dict(original=[dict(text='AA AA AA AA AA AA AA AA',font='synthetic')],translation='First synthetic translation.'),
               dict(original=[dict(text='AA AA AA AA AA AA AA AA AA AA AA AA',font='synthetic')],
                    translation='A second synthetic passage checks wrapping in the separate English column.')]
        ids,text=compose(ROOT,self.call,pairs,{'synthetic':fid})
        before=self.assert_standard(ids,text);self.assertFalse(any(f['overflow'] for f in before['frames']))
        for role,other in [('original','translation'),('translation','original')]:
            self.call('frame.select',frame_id=ids[role])
            other_content=deepcopy(next(f for f in self.book.capture()['pages'][0]['frames'] if f['frameId']==ids[other])['content'])
            self.call('document.edit',start=0,end=0,text='A ')
            self.assertEqual(self.book.frames[ids[role]].text(),'A '+text[role])
            self.assertEqual(other_content,next(f for f in self.book.capture()['pages'][0]['frames'] if f['frameId']==ids[other])['content'])
            self.call('history.undo')
            self.assertEqual(before['geometryHash'],self.assert_standard(ids,text)['geometryHash'])
        self.round_trip_and_export(ids,text)

    def test_local_attested_passages_and_exact_font_runs(self):
        local=definition(ROOT)['localFixture']
        if not all((ROOT/'Inputs'/item['path']).is_file() for item in [local['source'],*local['fonts']]):
            self.skipTest('Local source document/fonts absent; public structural case still runs')
        pairs,fonts=local_material(ROOT,self.call)
        ids,text=compose(ROOT,self.call,pairs,fonts)
        report=self.round_trip_and_export(ids,text)
        self.assertFalse(any(g['missingGlyph'] for g in report['glyphs']))
        # The historical source has one transliteration-font clitic inside the
        # script paragraph. Keep the exact run identity and scalar at that offset.
        glyph=next(g for g in report['glyphs'] if g['sourceFrameId']==ids['original'] and g['sourceUtf16'][0]==186)
        self.assertEqual(glyph['selectedFontId'],fonts['transliteration 5'])
        self.assertEqual(text['original'][186],'\u00be')
        # Record the known natural overhang rather than suppressing diagnostics.
        # Original glyphs must remain visible and within a 1 pt left allowance;
        # vertical overflow and horizontal escape to the translation are failures.
        for frame in report['frames']:
            x,y,w,h=frame['rect']
            for g in frame['layout']['glyphs']:
                gx,gy,gw,gh=g['inkBounds']
                if gw and gh:
                    self.assertGreaterEqual(gx,x-SCALE);self.assertLessEqual(gx+gw,x+w+0.01)
                    self.assertGreaterEqual(gy,y-0.01);self.assertLessEqual(gy+gh,y+h+0.01)
        (self.work/'source-provenance.json').write_text(json.dumps(local,indent=2),encoding='utf-8')


if __name__=='__main__': unittest.main()
