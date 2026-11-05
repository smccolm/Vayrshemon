"""Structural print tests use synthetic strings, never invented translations."""
from collections import Counter
import hashlib
from pathlib import Path
import tempfile
import unittest

from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QApplication
from pypdf import PdfReader
from tools.kjv_print_proof import Proof, Page, configure_pdf, digits, digest, reading_copy, ROOT, BODY_BOTTOM

APP=QApplication.instance() or QApplication([])


class LetterPrintProofTests(unittest.TestCase):
    def proof(self):
        proof=Proof()
        proof.plural_i='ráun';proof.singular_we='ly'
        return proof

    def test_untouched_case_and_multi_page_verse_with_no_isolated_line(self):
        proof=self.proof()
        texts=['Pá '+('Memon mEMon ráun ly. '*160), 'Memon.']
        units=[dict(id=str(i),reference='synthetic',chapter=i+1,verse=1,text=t) for i,t in enumerate(texts)]
        proof.compose(units)
        for unit,coverage in zip(units,proof.coverage):
            self.assertEqual(coverage['textSha256'],hashlib.sha256(unit['text'].encode()).hexdigest())
            fragments=coverage['fragments']
            self.assertEqual(fragments[0]['start'],0)
            for a,b in zip(fragments,fragments[1:]):self.assertEqual(a['end'],b['start'])
        counts=Counter(f['physicalPage'] for f in proof.coverage[0]['fragments'])
        self.assertGreater(len(counts),1)
        self.assertTrue(all(n>=2 for n in counts.values()),counts)
        self.assertEqual(proof.coverage[0]['illuminatedInitial'],'P')
        self.assertEqual(proof.coverage[1]['untaVerse'],'1')
        self.assertEqual(digits(12),'10')
        self.assertEqual(digits(31),'27')

    def test_duplex_parity_print_boxes_and_folios(self):
        proof=self.proof()
        units=[dict(id=str(i),reference='synthetic',chapter=1 if i<14 else 2,
                    verse=i+1 if i<14 else i-13,text='Memon mEMon ráun ly. '*12) for i in range(24)]
        proof.compose(units)
        self.assertEqual(len(proof.pages)%2,0)
        for page in proof.pages[2:]:
            if page.folio is None:continue
            self.assertEqual(page.physical,page.folio+2)
            self.assertEqual(page.binding_offset,9 if page.physical%2 else -9)
            self.assertEqual(page.right-page.left,540)
            self.assertEqual(page.left if page.physical%2 else 612-page.right,45)
            folio=next(r for r in page.records if r['role']=='folio')
            bounds=QRectF(*folio['bounds'])
            self.assertAlmostEqual(bounds.bottom(),792-28,places=5)
            self.assertAlmostEqual(bounds.right() if page.physical%2 else bounds.left(),
                                   612-28 if page.physical%2 else 28,places=5)
            for r in page.records:
                if r['role']=='body':
                    self.assertLessEqual(r['bounds'][1]+r['bounds'][3],BODY_BOTTOM)
                    self.assertFalse(bounds.adjusted(-4,-4,4,4).intersects(QRectF(*r['bounds'])))
        with tempfile.TemporaryDirectory(dir=ROOT/'.local') as temp:
            raw,target=Path(temp)/'raw.pdf',Path(temp)/'proof.pdf'
            proof.render(raw);configure_pdf(raw,target,proof)
            reader=PdfReader(target)
            self.assertEqual(reader.pdf_header,'%PDF-1.7')
            self.assertEqual(reader.page_layout,'/TwoPageRight')
            self.assertEqual(reader.viewer_preferences['/Duplex'],'/DuplexFlipLongEdge')
            self.assertEqual(reader.viewer_preferences['/PrintScaling'],'/None')
            self.assertEqual(reader.page_labels[2],'1')
            self.assertEqual(len(reader.pages),len(proof.pages))
            for page in reader.pages:
                self.assertEqual((float(page.mediabox.width),float(page.mediabox.height)),(612,792))
                self.assertFalse(page['/Resources'].get('/XObject',{}),
                                 'This proof must retain vector glyphs and ornament')

    def test_supplied_art_is_uncropped_lossless_and_equally_offset(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.local') as temp:
            temp=Path(temp);art=temp/'synthetic-structural-art.png'
            image=QImage(400,520,QImage.Format.Format_RGB32);image.fill(QColor('white'))
            for y in range(40,480):
                for x in range(40,360):image.setPixelColor(x,y,QColor(25,50,75))
            self.assertTrue(image.save(str(art)))
            original=digest(art)
            proof=Proof(art,art)
            proof.compose([dict(id=str(i),reference='synthetic',chapter=i+1,verse=1,text='Memon.') for i in range(2)])
            for index,offset in [(0,9),(1,-9)]:
                page=proof.pages[index]
                rect=page.images[0][1]
                self.assertAlmostEqual(rect.center().x()-306,offset)
                self.assertAlmostEqual(rect.width()/rect.height(),400/520)
                self.assertTrue(QRectF(0,0,612,792).contains(rect))
                self.assertEqual(page.records[0]['sha256'],original)
                self.assertFalse(page.elements,'No substitute title or painted-over artwork')
            raw,target=temp/'raw.pdf',temp/'proof.pdf'
            proof.render(raw);configure_pdf(raw,target,proof)
            reader=PdfReader(target)
            for page in reader.pages[:2]:
                objects=[v.get_object() for v in page['/Resources']['/XObject'].values()]
                images=[o for o in objects if o.get('/Subtype')=='/Image']
                self.assertEqual(len(images),1)
                self.assertEqual((images[0]['/Width'],images[0]['/Height']),(400,520))
                self.assertEqual(images[0]['/Filter'],'/FlateDecode')
            self.assertEqual(digest(art),original)

    def test_display_blank_preserves_physical_book_and_bookmarks(self):
        units=[dict(id=str(i),reference='synthetic',chapter=i+1,verse=1,
                    text='Pá Memon mEMon ráun ly. '*6) for i in range(2)]
        proof=self.proof();proof.compose(units)
        self.assertEqual(proof.pages[1].binding_offset,-9)
        self.assertEqual(proof.pages[2].binding_offset,9)
        with tempfile.TemporaryDirectory(dir=ROOT/'.local') as temp:
            raw,physical,display=[Path(temp)/name for name in ('raw.pdf','print.pdf','read.pdf')]
            proof.render(raw);configure_pdf(raw,physical,proof)
            prior=digest(physical)
            result=reading_copy(physical,display)
            reader=PdfReader(display);printed=PdfReader(physical)
            self.assertEqual(digest(physical),prior)
            self.assertEqual(printed.page_layout,'/TwoPageRight')
            self.assertEqual(reader.page_layout,'/TwoPageLeft')
            self.assertEqual(reader.page_labels[:4],['Display blank','Title page','Frontispiece','1'])
            self.assertEqual(len(reader.pages),len(printed.pages)+1)
            self.assertIsNone(reader.pages[0].get_contents())
            self.assertFalse(reader.pages[0].get('/Annots'))
            self.assertEqual([reader.get_destination_page_number(v) for v in reader.outline[:3]],[1,2,3])
            self.assertEqual(list(reader.viewer_preferences['/PrintPageRange']),[1,len(reader.pages)-1])
            self.assertEqual(result['printPages'],[2,len(reader.pages)])
            for source,copy in zip(printed.pages,reader.pages[1:]):
                self.assertEqual(source.get_contents().get_data(),copy.get_contents().get_data())
                self.assertEqual(source.mediabox,copy.mediabox)


if __name__=='__main__':unittest.main()
