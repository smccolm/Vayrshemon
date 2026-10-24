"""Workspace page arrangements; document coordinates and proofs stay page-local."""
from PySide6.QtCore import QRectF
from .pages import page_rect
from .session import SCALE

GUTTER_PT = 24


def arrangement(book, mode='one'):
    if mode not in ('one', 'two'):
        raise ValueError('UNKNOWN_PAGE_VIEW_MODE')
    current = book.current_page()['pageId']
    index = next(i for i,p in enumerate(book.state['pages']) if p['pageId']==current)
    start = index if mode=='one' else index//2*2
    selected = book.state['pages'][start:start+(1 if mode=='one' else 2)]
    result=[]; x=0.
    for page in selected:
        rect=page_rect(page).translated(x,0)
        result.append((page,rect)); x=rect.right()+GUTTER_PT*SCALE
    return result


def boundary(arrangement):
    result=QRectF()
    for _,rect in arrangement: result=result.united(rect)
    return result
