"""Local-time filename suggestions only; exporting still requires a chosen path."""
from datetime import datetime
from pathlib import Path
import re


def suggested_proof_path(session, extension, *, page_side=None):
    if page_side not in (None,'Left','Right'):raise ValueError('INVALID_PROOF_PAGE_SIDE')
    title=re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', session.state['title']).strip(' .')[:80] or 'page'
    when=datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')[:-3]
    name=when if extension.lower() in ('png','svg') else title+'_'+when
    if page_side:name+='_'+page_side
    return str(session.root/'.local'/f'{name}.{extension}')


def spread_png_paths(path, count=2):
    """Accept either the common stem or one suggested side; use one timestamp."""
    if count not in (1,2):raise ValueError('PNG_SPREAD_PAGE_COUNT')
    p=Path(path);stem=p.name[:-4] if p.name.lower().endswith('.png') else p.name
    stem=re.sub(r'_(left|right)$','',stem,flags=re.IGNORECASE)
    if not stem:raise ValueError('PNG_FILENAME_REQUIRED')
    return [str(p.with_name(stem+'_'+side+'.png')) for side in ('Left','Right')[:count]]
