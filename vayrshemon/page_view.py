"""Workspace page arrangements; document coordinates and proofs stay page-local."""
from PySide6.QtCore import QRectF
from .pages import page_rect
from .session import SCALE

GUTTER_PT = 24


def starts_with_recto(state):
    """A title or centered opening contents page followed by a verso starts on the recto."""
    pages = state['pages']
    specs = (state.get('printEdition') or {}).get('pages', {})
    if len(pages) < 2 or specs.get(pages[1]['pageId'], {}).get('side') != 'left':
        return False
    first = specs.get(pages[0]['pageId'], {})
    return first.get('kind') == 'title' or (first.get('kind'), first.get('side')) == ('contents', 'center')


def visible_numbers(page, count, mode, cover_first=False):
    if mode == 'one' or (cover_first and page == 1):
        return range(page, page+1)
    first = 2 if cover_first else 1
    start = first + 2*((page-first)//2)
    return range(start, min(start+2, count+1))


def arrangement(book, mode='one'):
    if mode not in ('one', 'two'):
        raise ValueError('UNKNOWN_PAGE_VIEW_MODE')
    current = book.current_page()['pageId']
    index = next(i for i,p in enumerate(book.state['pages']) if p['pageId']==current)
    indices = visible_numbers(index+1,len(book.state['pages']),mode,starts_with_recto(book.state))
    selected = book.state['pages'][indices.start-1:indices.stop-1]
    result=[]; x=0.
    for page in selected:
        rect=page_rect(page).translated(x,0)
        result.append((page,rect)); x=rect.right()+GUTTER_PT*SCALE
    return result


def boundary(arrangement):
    result=QRectF()
    for _,rect in arrangement: result=result.united(rect)
    return result
