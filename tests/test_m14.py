"""Saved-revision previews, legacy compatibility and real native shell decoding."""
import base64,hashlib,json,os,subprocess,sys,unittest,uuid
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from jsonschema import Draft202012Validator
from tools.m0.synthetic import make_font
from tools.m0.common import load_json,write_json
from vayrshemon.file_api import FileSession,FileAPI,METHODS
from vayrshemon.file_contracts import DOCUMENT
from vayrshemon import saved_preview
from tests.test_monochrome import pixels

ROOT=Path(__file__).resolve().parents[1];APP=QApplication.instance() or QApplication([])


class FileTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m14'/uuid.uuid4().hex;self.work.mkdir(parents=True)
        self.book=FileSession(ROOT,source_fonts=False,recovery=False);self.api=FileAPI(self.book)
        font=self.work/'synthetic.ttf';make_font(font);fid=self.call('fonts.load',path=str(font))['fontId']
        self.call('page.configure',width=200,height=240)
        self.call('document.edit',start=0,end=0,text='A A\nA')
        self.call('document.format',start=0,end=5,font_id=fid,size=24,color='#1155AAFF')
        self.call('page.add',width=200,height=240)
        self.call('document.edit',start=0,end=0,text='AA')
        self.call('document.format',start=0,end=2,font_id=fid,size=24,color='#1155AAFF')

    def tearDown(self):self.book.finish()

    def call(self,method,**params):
        r=self.api.call(method,params,expected_revision=self.book.revision,idempotency_key=uuid.uuid4().hex)
        self.assertTrue(r['ok'],r);return r['result']

    def test_round_trip_all_modes_single_spread_and_unsaved_changes(self):
        for mode,paper,key in [('color','black','color'),('mono','black','mono-black'),('mono','white','mono-white')]:
            self.call('view.configure',mode=mode,monochromePaper=paper)
            for arrangement in ('one','two'):
                state=self.book.capture();path=self.work/f'{key}-{arrangement}.vay'
                result=self.call('document.save-as',path=str(path),preview_mode=arrangement)
                value=load_json(path);Draft202012Validator(DOCUMENT).validate(value)
                self.assertEqual(self.book.capture(),state);self.assertEqual(value['state'],state)
                preview=value['shellPreview'];self.assertEqual(preview['colorMode'],key);self.assertEqual(len(preview['pageIds']),1 if arrangement=='one' else 2)
                raw=saved_preview.validate(preview,state);image=QImage.fromData(raw,'PNG')
                self.assertEqual(max(image.width(),image.height()),1024)
                if arrangement=='two':self.assertGreater(image.width(),image.height())
                else:self.assertLess(image.width(),image.height())
                if mode=='mono':
                    data=pixels(image);self.assertTrue((data[:,:,0]==data[:,:,1]).all());self.assertTrue((data[:,:,1]==data[:,:,2]).all())
                self.assertIsNone(result['backupError']);self.assertFalse(self.book.dirty)
                before=path.read_bytes();self.call('document.title',title='Unsaved '+uuid.uuid4().hex)
                self.assertEqual(path.read_bytes(),before)
                self.assertEqual(self.call('document.saved-preview')['preview']['revision'],state['revision'])
                self.book.open(path,advance_revision=False);self.assertEqual(self.book.capture(),state);self.assertEqual(self.book.saved_page_mode,arrangement)

    def test_failed_preview_retains_previous_file_and_dirty_edit(self):
        path=self.work/'atomic.vay';self.book.save(path);before=path.read_bytes()
        self.call('document.title',title='Keep this unsaved edit')
        with patch('vayrshemon.saved_preview.create',side_effect=ValueError('test preview failed')):
            with self.assertRaisesRegex(ValueError,'preview failed'):self.book.save(path)
        self.assertEqual(path.read_bytes(),before);self.assertTrue(self.book.dirty);self.assertEqual(self.book.state['title'],'Keep this unsaved edit')

    def test_external_change_during_preview_is_preserved(self):
        path=self.work/'external.vay';self.book.save(path)
        original=saved_preview.create
        def changed(*args):
            result=original(*args);path.write_bytes(b'External newer file');return result
        with patch('vayrshemon.saved_preview.create',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'DOCUMENT_CHANGED_ON_DISK'):self.book.save(path)
        self.assertEqual(path.read_bytes(),b'External newer file')

    def test_font_complete_backup_restores_embedded_preview_offline(self):
        from tools.recovery import restore_backup
        path=self.work/'backup.vay';result=self.book.save(path,preview_mode='two')
        restored=restore_backup(result['backup']['path'],self.work/'restored')
        self.assertTrue(restored['path'].endswith('.vay'));self.book.open(restored['path'],advance_revision=False)
        self.assertEqual(self.book.saved_preview['pngSha256'],result['preview']['pngSha256'])

    def test_ui_extension_defaults_and_saved_spread_reopen(self):
        from vayrshemon.file_window import FileWindow
        from PySide6.QtCore import QCoreApplication,QEvent
        path=self.work/'visible.vay';self.book.save(path,preview_mode='two');self.book.open(path,advance_revision=False);state=self.book.capture()
        window=FileWindow(self.book,self.api)
        try:
            self.assertEqual(window.preview.page_mode,'two');self.assertEqual(self.book.capture(),state)
            with patch('vayrshemon.file_window.QFileDialog.getSaveFileName',return_value=(str(self.work/'Native document'),'')) as dialog:
                window.save_as();self.assertTrue(str(self.book.saved_path).endswith('Native document.vay'));self.assertIn('*.vay',dialog.call_args.args[3])
            self.assertEqual(self.book.saved_preview['pageMode'],'two')
        finally:
            window.job_timer.stop();window.forge_panel.timer.stop();window.hide();self.book.window=None;window.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)

    def test_corrupt_or_stale_preview_does_not_replace_open_document(self):
        path=self.work/'good.vay';self.book.save(path);value=load_json(path);before=self.book.capture()
        for field,change in [('colorMode','mono-white'),('stateSha256','0'*64),('pngSha256','0'*64),('width',0),('pngBase64','%%%')]:
            invalid=deepcopy(value);invalid['shellPreview'][field]=change;target=self.work/(field+'.vay');write_json(target,invalid)
            with self.assertRaises(Exception):self.book.open(target)
            self.assertEqual(self.book.capture(),before)

    def test_legacy_formats_and_json_extension_remain_readable(self):
        from vayrshemon.authoring import AuthoringSession
        from vayrshemon.typesetting_session import TypesettingSession
        from vayrshemon.studio_session import StudioSession
        from vayrshemon.language_session import LanguageSession
        for cls in (AuthoringSession,TypesettingSession,StudioSession,LanguageSession):
            old=cls(ROOT,source_fonts=False,recovery=False)
            try:
                path=self.work/(old.file_version+'.vay.json');old.save(path);old_bytes=path.read_bytes();state=old.capture()
                self.book.open(path,advance_revision=False)
                for field in ('pages','fontSources','styles','recipe'):
                    self.assertEqual(self.book.capture()[field],state[field])
                self.book.save(self.work/(old.file_version+'.vay'));self.assertEqual(path.read_bytes(),old_bytes)
            finally:old.finish()
        from vayrshemon.session import Session
        lab=Session(ROOT,source_fonts=False)
        path=self.work/'old.vaylab.json';lab.save(path)
        self.book.open(path,advance_revision=False);self.assertTrue(self.book.migrated_from)

    def test_new_file_api_contracts_and_cli_detection(self):
        self.assertEqual(len(METHODS),153)
        published=load_json(ROOT/'data/file-mcp-tools.json');self.assertEqual(len(published['tools']),len(METHODS))
        schema=load_json(ROOT/'schemas/file-command.schema.json')
        Draft202012Validator(schema).validate(dict(apiVersion='0.15.0',method='document.save',params=dict(path='x.vay',preview_mode='two'),documentId=self.book.state['documentId'],expectedRevision=self.book.revision,idempotencyKey='test'))
        path=self.work/'command.vay';self.book.save(path)
        result=subprocess.run([sys.executable,'-m','vayrshemon','inspect','--document',str(path),'--out',str(self.work/'inspect.json')],cwd=ROOT,capture_output=True,text=True,timeout=90)
        self.assertEqual(result.returncode,0,result.stderr[-3000:]);self.assertTrue((self.work/'inspect.json').exists())

    @unittest.skipUnless(os.name=='nt','Windows native provider')
    def test_native_provider_decodes_modes_and_rejects_malformed_files(self):
        from tools.shell_probe import direct
        builds=list((ROOT/'.local/shell').glob('*/build.json'))
        if not builds:self.skipTest('Run setup.bat to build the native provider')
        dll=Path(load_json(max(builds,key=lambda p:p.stat().st_mtime))['dll'])
        for mode,paper,key in [('color','black','color'),('mono','black','mono-black'),('mono','white','mono-white')]:
            self.call('view.configure',mode=mode,monochromePaper=paper);path=self.work/f'{key} Maxima Ω.vay';self.book.save(path,preview_mode='two')
            info,image=direct(dll,path,1024);self.assertTrue(info['icon'].endswith(f'memon-{key}.ico'));self.assertEqual(info['alpha'],2)
            png=base64.b64decode(load_json(path)['shellPreview']['pngBase64']);expected=QImage.fromData(png,'PNG')
            self.assertTrue((pixels(image)==pixels(expected)).all())
        value=load_json(path)
        for i,raw in enumerate((b'garbage',b'['*1000+b']'*1000,json.dumps(dict(value,shellPreview=dict(value['shellPreview'],pngBase64='SGVsbG8='))).encode(),b'{"format":"vayrshemon.document","format":"x"}')):
            invalid=self.work/f'bad-{i}.vay';invalid.write_bytes(raw)
            with self.assertRaises(OSError):direct(dll,invalid)
