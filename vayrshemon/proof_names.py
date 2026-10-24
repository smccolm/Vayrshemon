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


def spread_proof_paths(path, count=2, extension='png'):
    """Accept either the common stem or one suggested side; use one timestamp."""
    if extension not in ('png','svg'):raise ValueError('SPREAD_PROOF_FORMAT')
    if count not in (1,2):raise ValueError(extension.upper()+'_SPREAD_PAGE_COUNT')
    suffix='.'+extension
    p=Path(path);stem=p.name[:-len(suffix)] if p.name.lower().endswith(suffix) else p.name
    stem=re.sub(r'_(left|right)$','',stem,flags=re.IGNORECASE)
    if not stem:raise ValueError(extension.upper()+'_FILENAME_REQUIRED')
    return [str(p.with_name(stem+'_'+side+suffix)) for side in ('Left','Right')[:count]]


def spread_png_paths(path, count=2):
    return spread_proof_paths(path,count,'png')
