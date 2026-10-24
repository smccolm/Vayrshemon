"""Verify bundled identities and existing-runtime use without reinstalling."""
from copy import deepcopy
import hashlib
from pathlib import Path
import shutil
import unittest
import uuid
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtWidgets import QApplication
from tools.m0.synthetic import make_font
from vayrshemon import bundled_fonts
from vayrshemon.file_api import FileSession
from vayrshemon.reading import ROMAN_SHA,SCRIPT_SHA,font

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class BundledFontTests(unittest.TestCase):
    def setUp(self):
        self.root=ROOT/'.local/test-bundled-fonts'/uuid.uuid4().hex
        shutil.copytree(ROOT/'schemas',self.root/'schemas');shutil.copytree(ROOT/'data',self.root/'data')
        self.book=FileSession(self.root,recovery=False)

    def tearDown(self):
        self.book.finish()
        for frame in self.book.frames.values():frame.deleteLater()
        self.book.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);APP.processEvents()

    def test_exact_assets_default_layers_and_roman_available(self):
        result=bundled_fonts.verify(ROOT);self.assertEqual(result['fonts'],4)
        records=bundled_fonts.records(ROOT)
        self.assertEqual(set(self.book.fonts.faces),set(records))
        self.assertFalse((self.root/'Inputs').exists())
        for fid,record in records.items():
            face=self.book.fonts.resolve(fid)
            self.assertEqual(face.path,bundled_fonts.path(self.root,record))
            self.assertEqual(hashlib.sha256(face.path.read_bytes()).hexdigest(),record['sha256'])
            self.assertEqual(face.sha256,record['sha256'])
            original=ROOT/'Inputs'/record['source']
            if original.exists():self.assertEqual(bundled_fonts.path(ROOT,record).read_bytes(),original.read_bytes())
        recipe=self.book.fonts.recipe
        self.assertEqual(recipe['master'],'font:'+SCRIPT_SHA+':0')
        self.assertEqual([records[r['fontId']]['role'] for r in recipe['layers']],['glow','interior','script-master'])
        roman=font(self.book,'transliteration');self.assertEqual(roman.sha256,ROMAN_SHA)
        # Existing raw-font paths still preserve the complete cmap and outlines.
        self.assertTrue(self.book.fonts.resolve(recipe['master']).raw(50).isValid())
        self.assertTrue(roman.raw(22).isValid())

    def test_missing_saved_paths_use_exact_bundle_and_valid_paths_stay(self):
        state=self.book.capture();pages=deepcopy(state['pages']);recipe=deepcopy(state['recipe'])
        old=self.root/'existing.ttf';shutil.copy2(self.book.fonts.resolve('font:'+ROMAN_SHA+':0').path,old)
        for source in state['fontSources']:
            source['path']=str(old if source['sha256']==ROMAN_SHA else self.root/'absent'/source['sha256'])
        resolved=self.book.resolve_fonts(state)
        self.assertEqual(resolved['pages'],pages);self.assertEqual(resolved['recipe'],recipe)
        for source in resolved['fontSources']:
            expected=old if source['sha256']==ROMAN_SHA else bundled_fonts.path(self.root,self.book.fonts.bundled[source['fontId']])
            self.assertEqual(Path(source['path']),expected)
        self.assertNotEqual(resolved,state)

    def test_explicit_missing_or_changed_font_is_not_silently_replaced(self):
        state=self.book.capture();source=state['fontSources'][0]
        with self.assertRaisesRegex(ValueError,'MISSING_FONTS'):
            self.book.resolve_fonts(state,{source['fontId']:str(self.root/'explicit-missing.ttf')})
        bad=self.root/'changed.ttf';bad.write_bytes(b'changed source font')
        source['path']=str(bad)
        with self.assertRaisesRegex(ValueError,'FONT_HASH_MISMATCH'):self.book.resolve_fonts(state)
        synthetic=self.root/'external.ttf';make_font(synthetic)
        face=self.book.fonts.register(synthetic);synthetic.unlink()
        self.assertEqual(self.book.fonts.document_path(synthetic,face.sha256),synthetic)
        with self.assertRaisesRegex(ValueError,'FONT_MISSING_OR_CHANGED'):self.book.fonts.resolve(face.font_id)

    def test_verifier_rejects_damaged_or_missing_bundled_asset(self):
        record=next(iter(bundled_fonts.records(self.root).values()));path=bundled_fonts.path(self.root,record)
        path.write_bytes(b'bad font')
        with self.assertRaisesRegex(ValueError,'RUNTIME_FONT_HASH_MISMATCH'):bundled_fonts.verify(self.root)
        path.unlink()
        with self.assertRaises(FileNotFoundError):bundled_fonts.verify(self.root)
