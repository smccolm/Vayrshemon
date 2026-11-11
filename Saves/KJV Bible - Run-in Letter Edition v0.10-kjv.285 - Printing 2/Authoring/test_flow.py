"""Focused checks for the pagination regressions, using synthetic text."""
import re
import unittest
from compose import BASE_LIMIT,BodyPage,Metrics,QApplication,QRectF,digits


def unit(n,text,chapter=1):
    return dict(id=f'01.{chapter:03}.{n:03}',reference='synthetic',verse=n,chapter=chapter,text=text)


def words(u):
    return list(re.finditer(r'\S+',u['text']))


class PageFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.proof=Metrics()

    def test_verse_starts_on_used_last_line_and_continues_without_renumbering(self):
        page=BodyPage(self.proof,1)
        page.y=714
        first=unit(1,'Memon.')
        self.assertEqual(page.place(first,words(first),0),1)
        next_verse=unit(2,' '.join(['Memon']*30))
        terms=words(next_verse)
        cut=page.place(next_verse,terms,0)
        self.assertTrue(0<cut<len(terms))
        self.assertEqual([l['baseline'] for l in page.lines],[714,714])
        self.assertEqual(page.lines[-1]['prefix'],digits(2)+'  ')
        other=BodyPage(self.proof,1)
        self.assertEqual(other.place(next_verse,terms,cut),len(terms))
        self.assertEqual(other.lines[0]['prefix'],'')
        row=page.rows[-1]
        self.assertEqual(page.text[row['start']:row['end']]+other.text,next_verse['text'])

    def test_chapter_marker_stays_with_first_word_on_last_row(self):
        page=BodyPage(self.proof,1)
        page.y=696
        prev=unit(20,' '.join(['Memon']*16))
        self.assertEqual(page.place(prev,words(prev),0),len(words(prev)))
        nxt=unit(1,' '.join(['Memon']*28),2)
        placed=page.chapter(nxt,words(nxt))
        self.assertTrue(0<placed<len(words(nxt)))
        self.assertEqual(page.chapters,[2])
        label,=[p.boundingRect() for (p,_),r in zip(page.sheet.elements,page.sheet.records) if r['role']=='chapter-heading']
        for l in page.lines:
            box=QRectF(*l['bounds'])
            self.assertFalse(label.intersects(box))
            self.assertLessEqual(box.bottom(),BASE_LIMIT)
        self.assertTrue(any(l['prefix']==digits(1)+'  ' for l in page.lines))


if __name__=='__main__': unittest.main()
