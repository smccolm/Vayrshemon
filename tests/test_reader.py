"""Reader preserves native pages and renders without writing the original."""
from copy import deepcopy
from pathlib import Path
import json,tempfile,unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from Reader import storage
from Reader.render import Engine,read_image,publish_cache
from vayrshemon.file_api import FileSession
from vayrshemon import pages,page_numbering
from tools.kjv_print_edition import Composer

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])

class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'.local');self.folder=Path(self.temp.name)
        self.patch=patch('Reader.storage.LOCAL',self.folder/'cache');self.patch.start()
        self.render_patch=patch('Reader.render.LOCAL',self.folder/'cache');self.render_patch.start();self.engines=[]
        self.book=FileSession(ROOT,recovery=False);self.book.log.emit=lambda *a,**k:None
    def tearDown(self):
        for engine in self.engines:engine.index.close()
        self.book.finish();self.render_patch.stop();self.patch.stop();self.temp.cleanup()
    def native(self):
        # Structural test strings only; no synthetic language data.
        state=self.book.capture();first=state['pages'][0]
        self.book.active.edit(0,0,'Memon mEMon. Structural reader test.');self.book.add_page();self.book.active.edit(0,0,'Second structural page.')
        path=self.folder/'structural.vay';self.book.save(path);return path
    def test_index_random_access_search_source_hash_and_invalidation(self):
        path=self.native();before=storage.file_hash(path);result=storage.build(path)
        with storage.BookIndex(result['cache']) as index:
            self.assertEqual(index.meta['pageCount'],2)
            self.assertNotIn('language',index.meta['state'])
            self.assertEqual(index.page(2)['page'],self.book.capture()['pages'][1])
            self.assertEqual(index.search('Structural reader')[0]['page'],1)
            with self.assertRaises(ValueError):index.page(3)
        self.assertTrue(storage.build(path)['cached']);self.assertEqual(storage.file_hash(path),before)
        old=storage.cache_path(path);path.write_bytes(path.read_bytes()+b'\n');self.assertNotEqual(storage.cache_path(path),old)
    def test_same_native_pixels_and_global_folio_number(self):
        path=self.native();result=storage.build(path);engine=Engine(result['cache']);self.engines.append(engine)
        for n in (1,2):
            for palette in ('white','black'):
                self.book.view.update(mode='mono',monochromePaper=palette)
                expected,_=pages.render(self.book,page_id=self.book.state['pages'][n-1]['pageId'],mode='mono',dpi=48,page_mode='two')
                actual=read_image(engine.render(n,palette,'two',.5)['path'])
                self.assertEqual(bytes(actual.constBits()),bytes(expected.constBits()))
                self.assertEqual(page_numbering.placement(engine.book,engine.book.current_page())['pageNumber'],n)
    def test_compact_illuminated_native_reader(self):
        units=[dict(id='01.001.001',reference='structural',chapter=1,verse=1,text='Memon mEMon ráun ly. '*10)]
        state=Composer(self.book.capture(),None,None,compact=True).compose_all(units,progress=lambda *a,**k:None)
        self.book._restore(state);self.book._state=self.book.capture();path=self.folder/'print.vay';self.book.save(path,preview_mode='two')
        result=storage.build(path);engine=Engine(result['cache']);self.engines.append(engine)
        self.assertEqual(engine.index.meta['sections'][0]['page'],4)
        for n in (1,3,4):
            expected,_=pages.render(self.book,page_id=self.book.state['pages'][n-1]['pageId'],mode='mono',dpi=48,page_mode='two')
            actual=read_image(engine.render(n,'white','two',.5)['path'])
            self.assertEqual(bytes(actual.constBits()),bytes(expected.constBits()))
    def test_cache_publication_keeps_first_complete_value(self):
        target=self.folder/'test.frame';target.write_bytes(b'first');temp=self.folder/'second.tmp';temp.write_bytes(b'second')
        with target.open('rb') as opened:
            publish_cache(temp,target);self.assertEqual(opened.read(),b'first')
        self.assertFalse(temp.exists());self.assertEqual(target.read_bytes(),b'first')
    def test_navigation_keeps_explicit_right_target_and_steps_to_left(self):
        from Reader.app import Window
        with patch('Reader.control.Server'):
            window=Window();window.meta=dict(pageCount=20780,headers=[dict(width='612000000',height='792000000')]*20780,state={})
            window.schedule=lambda:None;window.mode='two';window.navigate(page=20000)
            self.assertEqual(window.page,20000);self.assertEqual(window.visible(),[19999,20000])
            window.navigate(direction='next');self.assertEqual(window.page,20001)
            window.navigate(page=20780);window.navigate(direction='next');self.assertEqual(window.visible(),[20779,20780])
            with self.assertRaises(ValueError):window.navigate(page=20781)
            window.mode='one';window.navigate(page=20);window.navigate(direction='previous');self.assertEqual(window.page,19)
            window.meta=None;window.close()

    def test_prefetch_cannot_evict_visible_high_zoom_pages(self):
        from Reader.app import Window
        class SizedImage:
            def sizeInBytes(self):return 100*1024*1024
        with patch('Reader.control.Server'):
            window=Window();window.meta=dict(pageCount=10,headers=[],state={});window.mode='two';window.page=1
            first=window.key(1);second=window.key(2)
            for n in range(1,9):window.remember_image(window.key(n),SizedImage())
            self.assertIn(first,window.images);self.assertIn(second,window.images)
            self.assertLessEqual(window.image_bytes,256*1024*1024)
            window.meta=None;window.close()

if __name__=='__main__':unittest.main()
