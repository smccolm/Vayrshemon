"""Independent Roman relief keeps source geometry and the script recipe intact."""
from copy import deepcopy
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch
import numpy as np
from PySide6.QtWidgets import QApplication
from tools.m0.synthetic import make_font
from tools.parallel_translation_fixture import compose
from vayrshemon.reading_api import ReadingSession,ReadingAPI
from vayrshemon import reading,paint

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class RomanPaintTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-roman-paint'/uuid.uuid4().hex;self.work.mkdir(parents=True)
        make_font(self.work/'roman.ttf');self.book=ReadingSession(ROOT,source_fonts=False,recovery=False);self.api=ReadingAPI(self.book)
        self.face=self.book.fonts.register(self.work/'roman.ttf')
        compose(ROOT,self.call,[dict(original=[dict(text='AA AA',font='synthetic')],translation='AA AA')],{'synthetic':self.face.font_id})

    def tearDown(self):self.book.finish()

    def call(self,method,**params):
        r=self.api.call(method,params,expected_revision=self.book.revision,idempotency_key=uuid.uuid4().hex,origin='test')
        self.assertTrue(r['ok'],r);return r['result']

    def test_binding_roundtrip_undo_and_independent_recipe(self):
        before=self.book.capture();binding=reading.roman_binding(self.face.font_id)
        self.call('paint.bind',**binding);self.assertEqual(self.book.capture()['pages'],before['pages'])
        renderer=self.book.paint_renderer;image,area=renderer.tile(binding,2,40,4)
        pixels=bytes(image.constBits());self.call('paint.configure',rim='#ff0000',glowOpacity=0)
        again,_=renderer.tile(binding,2,40,4);self.assertEqual(bytes(again.constBits()),pixels)
        self.call('history.undo');self.call('history.undo');self.assertEqual(self.book.state['paint'],before['paint'])
        self.call('history.redo');path=self.work/'reading.vay.json';self.call('document.save',path=str(path));self.call('document.open',path=str(path))
        self.assertEqual(self.book.state['paint']['bindings'][-1],binding)
        self.assertEqual(bytes(renderer.tile(binding,2,40,4)[0].constBits()),pixels)
        self.assertEqual(self.book.capture()['pages'],before['pages'])

    def test_masks_have_bounded_glow_and_real_outline_coverage(self):
        binding=reading.roman_binding(self.face.font_id);renderer=self.book.paint_renderer
        for em,scale in ((24,4),(100,4)):
            surface,area=renderer.tile(binding,2,em,scale,'surface');glow,_=renderer.tile(binding,2,em,scale,'glow')
            alpha=np.frombuffer(surface.constBits(),np.uint8).reshape(surface.height(),surface.width(),4)[:,:,3]
            expected=paint.mask(renderer.paths(binding,2,em)[0],area,scale)*255
            np.testing.assert_allclose(alpha,expected,atol=1)
            rgba=np.frombuffer(glow.constBits(),np.uint8).reshape(glow.height(),glow.width(),4)
            self.assertGreater(rgba[:,:,3].max(),0)
            self.assertLess(rgba[[0,-1],:,3].max(),3);self.assertLess(rgba[:,[0,-1],3].max(),3)
        bad=dict(binding,kind='layered',glowFontId=self.face.font_id,interiorFontId=self.face.font_id)
        self.assertFalse(self.api.call('paint.bind',bad,expected_revision=self.book.revision,origin='test')['ok'])

    def test_reading_default_and_presentation_guard(self):
        baseline=self.book.capture();state=deepcopy(baseline)
        with patch.object(reading,'ROMAN_SHA',self.face.sha256):
            reading.apply_font(state,self.face)
            self.assertIn(reading.roman_binding(self.face.font_id),state['paint']['bindings'])
            self.assertTrue(reading.presentation_matches(state,baseline,'transliteration'))
            changed=deepcopy(state);changed['paint']['recipe']['bevel']*=2
            self.assertFalse(reading.presentation_matches(changed,baseline,'transliteration'))
            changed=deepcopy(state);changed['paint']['bindings'][-1]['profile']='wrong'
            self.assertFalse(reading.presentation_matches(changed,baseline,'transliteration'))
            self.assertFalse(reading.presentation_matches(state,baseline,'translation'))


if __name__=='__main__':unittest.main()
