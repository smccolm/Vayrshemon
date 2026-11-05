"""Synthetic layout fixtures, not invented Vayrshemon translations."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from PySide6.QtWidgets import QApplication,QPlainTextEdit
from PySide6.QtGui import QImage,QColor
from pypdf import PdfReader
from tools.kjv_print_edition import Composer,ROOT
from vayrshemon.file_api import FileSession,FileAPI
from vayrshemon import pages,page_numbering,print_edition,publication

APP=QApplication.instance() or QApplication([])


class NativePrintTests(unittest.TestCase):
    def setUp(self):
        self.book=FileSession(ROOT,recovery=False);self.book.log.emit=lambda *a,**k:None
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'.local');self.folder=Path(self.temp.name)
        self.units=[dict(id=f'{b:02}.001.{v:03}',reference='synthetic',chapter=1,verse=v,
                         text=('Memon mEMon ráun ly. '*30 if v==1 else 'Memon.')) for b in (1,2) for v in (1,2)]

    def tearDown(self):self.book.finish();self.temp.cleanup()

    def build(self,art=False,compact=False,right_openings=False):
        paths=[]
        if art:
            for i in range(2):
                im=QImage(110,142,QImage.Format.Format_RGB32);im.fill(QColor('white'));im.setPixelColor(55,71,QColor('black'))
                path=self.folder/f'{i}.png';im.save(str(path));paths.append(path)
        composer=Composer(self.book.capture(),*(paths or [None,None]),compact=compact,right_openings=right_openings)
        state=composer.compose_all(self.units,progress=lambda *a,**k:None)
        self.book._restore(state);self.book._state=self.book.capture()
        return state

    def test_order_exact_text_binding_and_read_only(self):
        state=self.build(right_openings=True);edition=state['printEdition'];spec=list(edition['pages'].values())
        self.assertEqual([s['kind'] for s in spec[:4]],['title','blank','frontispiece','opening'])
        self.assertEqual([s['side'] for s in spec[:4]],['center','right','left','right'])
        for section in edition['sections']:
            index=next(i for i,p in enumerate(state['pages']) if p['pageId']==section['pageId'])
            self.assertEqual(index%2,1)
        self.assertEqual(len(edition['verses']),4)
        for unit,record in zip(self.units,edition['verses']):self.assertEqual(print_edition.hash_text(unit['text']),record['sha256'])
        for p in state['pages']:
            comp=self.book.composition('mono',p['pageId'])
            self.assertEqual(comp.collision_report()['afterCount'],0)
            for line,path in zip(comp.spec['lines'],comp.drawings):
                actual=path.boundingRect()
                self.assertLess(max(abs(a-b) for a,b in zip(line['bounds'],[actual.x(),actual.y(),actual.width(),actual.height()])),.05)
            with page_numbering.scope(self.book,'two'):
                number=page_numbering.placement(self.book,p)
                self.assertNotEqual(number['status'],'blocked')
                if number['status']=='placed':
                    x,y,w,h=number['bounds'];self.assertAlmostEqual((y+h)/ (4/3),764)
        api=FileAPI(self.book)
        with self.assertRaisesRegex(ValueError,'FIXED_PRINT_EDITION'):api.dispatch('document.edit',{})
        self.assertEqual(api.dispatch('publication.edition.inspect',{})['verseCount'],4)
        bad=deepcopy(state);bad['pages'][3]['frames'][0]['content']['document']['stories'][0]['blocks'][0]['runs'][0]['text']+='x'
        with self.assertRaisesRegex(ValueError,'PRINT_SOURCE_CHANGED'):self.book.validate(bad)

    def test_book_opening_uses_next_page_without_inter_book_blank(self):
        self.units=[dict(id=f'{b:02}.001.001',reference='synthetic',chapter=1,verse=1,text='Memon.') for b in (1,2,3)]
        state=self.build(compact=True);edition=state['printEdition'];spec=list(edition['pages'].values())
        self.assertEqual([s['kind'] for s in spec],['title','blank','frontispiece','opening','opening','opening'])
        self.assertEqual([s['side'] for s in spec[3:]],['right','left','right'])
        self.assertEqual([s['folio'] for s in spec[3:]],[1,2,3])
        for page in state['pages'][3:]:
            with page_numbering.scope(self.book,'two'):
                self.assertEqual(page_numbering.placement(self.book,page)['status'],'placed')

    def test_self_contained_save_reopen_and_exports(self):
        self.build(art=True);target=self.folder/'complete.vay'
        self.book.save(target,preview_mode='two');before=self.book.content_digest(self.book.capture())
        self.book.open(target,advance_revision=False)
        self.assertEqual(before,self.book.content_digest(self.book.capture()))
        self.assertEqual(self.book.saved_page_mode,'two');self.assertEqual(self.book.view['monochromePaper'],'white')
        first=self.book.state['pages'][0];png=self.folder/'title.png';svg=self.folder/'title.svg';pdf=self.folder/'sample.pdf'
        pages.render(self.book,png,page_id=first['pageId'],mode='mono',dpi=96)
        pages.export_svg(self.book,svg,page_id=first['pageId'],mode='mono')
        import xml.etree.ElementTree as ET
        self.assertTrue(any(e.tag.split('}')[-1]=='image' for e in ET.parse(svg).iter()))
        publication.export(self.book,pdf,format='pdf',mode='mono',page_id=first['pageId'],pdf_view='two')
        reader=PdfReader(pdf);self.assertEqual(len(reader.pages),1);self.assertTrue(list(reader.pages[0].images))
        for image in self.book.state['printEdition']['assets'].values():self.assertTrue(image['png'])

    def test_numbering_changes_are_safe_and_undoable(self):
        self.build();page=self.book.state['pages'][3];self.book._state=self.book.capture()
        api=FileAPI(self.book)
        with self.book.command('Hide numbers'):page_numbering.configure(self.book,enabled=False)
        self.assertEqual(page_numbering.placement(self.book,page)['status'],'hidden')
        api.dispatch('history.undo',{});self.assertEqual(page_numbering.placement(self.book,page)['status'],'placed')
        with page_numbering.scope(self.book,'two'):
            page_numbering.configure(self.book,right=dict(vertical='top'))
            self.assertEqual(page_numbering.placement(self.book,page)['status'],'blocked')

    def test_preserves_editorial_punctuation_and_long_compounds(self):
        self.units[1]['text']='Memon (mEMon) [ráun] - ly. '+('Memon'*120)+'.'
        self.build()
        for page in self.book.state['pages']:
            comp=self.book.composition('mono',page['pageId'])
            for line,path in zip(comp.spec['lines'],comp.drawings):
                b=path.boundingRect()
                self.assertLess(max(abs(a-v) for a,v in zip(line['bounds'],[b.x(),b.y(),b.width(),b.height()])),.05)
        self.assertEqual(self.book.state['printEdition']['verses'][1]['sha256'],print_edition.hash_text(self.units[1]['text']))

    def test_compact_profile_retains_source_and_exports_at_saved_size(self):
        self.units[0]['text']='Pá '+('Memon mEMon ráun ly. '*300)
        self.units[1]['text']='Memon (mEMon) [ráun] - ly.'
        large=self.build();original_hashes=[v['sha256'] for v in large['printEdition']['verses']]
        compact=self.build(compact=True)
        self.assertLess(len(compact['pages']),len(large['pages']))
        self.assertEqual(compact['printEdition']['layoutVersion'],'letter-compact.1')
        self.assertEqual([v['sha256'] for v in compact['printEdition']['verses']],original_hashes)
        for p in compact['pages']:
            comp=self.book.composition('mono',p['pageId'])
            self.assertEqual(comp.collision_report()['afterCount'],0)
            for line,path in zip(comp.spec['lines'],comp.drawings):
                b=path.boundingRect()
                self.assertLess(max(abs(a-v) for a,v in zip(line['bounds'],[b.x(),b.y(),b.width(),b.height()])),.05)
        target=self.folder/'compact.vay';self.book.save(target,preview_mode='two')
        self.book.open(target,advance_revision=False)
        self.assertEqual(print_edition.typography(self.book.state['printEdition']),print_edition.COMPACT_TYPE)
        page=self.book.state['pages'][3];pdf=self.folder/'compact-body.pdf'
        publication.export(self.book,pdf,format='pdf',mode='mono',page_id=page['pageId'],pdf_view='two')
        self.assertEqual(len(PdfReader(pdf).pages),1)
        bad=deepcopy(compact);bad['printEdition']['typography']['bodySizePt']=36
        with self.assertRaisesRegex(ValueError,'PRINT_TYPOGRAPHY_PROFILE'):self.book.validate(bad)
        bad=deepcopy(compact);bad['pages']=[bad['pages'][0]]*2001
        with self.assertRaisesRegex(ValueError,'PRINT_SHEET_LIMIT'):print_edition.validate(bad)


if __name__=='__main__':unittest.main()
