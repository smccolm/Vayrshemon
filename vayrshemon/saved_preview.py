"""Bounded, self-contained Explorer preview of the revision actually saved.

The editable state stays unchanged. No fonts, external image paths or executable
content are needed by the native shell reader. This module runs in the editor.
"""
import base64
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
from PySide6.QtCore import QBuffer,QByteArray,QIODevice,Qt
from PySide6.QtGui import QImage,QPainter
from . import page_view,pages
from .monochrome import palette

MAX_EDGE=1024
MAX_PNG=3*1024*1024
MODES=('color','mono-black','mono-white')


def state_hash(state):
    return hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def color_mode(state):
    if state['view']['mode']=='color':return 'color'
    paper,_=palette(state.get('paint',{}).get('background','#FFFFFFFF'),state['view'].get('monochromePaper','auto'))
    return 'mono-white' if paper.red()==255 else 'mono-black'


def create(book,state,mode):
    arranged=page_view.arrangement(book,mode);area=page_view.boundary(arranged)
    scale=MAX_EDGE/max(area.width(),area.height())
    width,height=max(1,math.ceil(area.width()*scale)),max(1,math.ceil(area.height()*scale))
    image=QImage(width,height,QImage.Format.Format_ARGB32_Premultiplied);image.fill(Qt.GlobalColor.transparent)
    if image.isNull():raise MemoryError('SAVED_PREVIEW_ALLOCATION_FAILED')
    painter=QPainter(image)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(scale,scale)
        for page,rect in arranged:
            painter.save();painter.translate(rect.topLeft())
            pages.paint(book,painter,page_id=page['pageId'],mode=state['view']['mode'],guides=False,overlays={})
            painter.restore()
    finally:painter.end()
    data=QByteArray();buffer=QBuffer(data);buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer,'PNG'):raise OSError('SAVED_PREVIEW_PNG_FAILED')
    raw=bytes(data)
    if len(raw)>MAX_PNG:raise ValueError('SAVED_PREVIEW_TOO_LARGE')
    if book.capture()!=state:raise ValueError('DOCUMENT_CHANGED_DURING_PREVIEW')
    return dict(version=1,revision=state['revision'],stateSha256=state_hash(state),colorMode=color_mode(state),
        pageMode=mode,pageIds=[p['pageId'] for p,_ in arranged],width=width,height=height,
        pngSha256=hashlib.sha256(raw).hexdigest(),pngBase64=base64.b64encode(raw).decode('ascii'))


def validate(preview,state):
    if preview['stateSha256']!=state_hash(state) or preview['revision']!=state['revision']:raise ValueError('SAVED_PREVIEW_STATE_MISMATCH')
    if preview['colorMode']!=color_mode(state):raise ValueError('SAVED_PREVIEW_MODE_MISMATCH')
    ids=[p['pageId'] for p in state['pages']]
    wanted=preview['pageIds']
    if any(p not in ids for p in wanted) or len(wanted)!=(1 if preview['pageMode']=='one' else min(2,len(ids)-ids.index(wanted[0]))):raise ValueError('SAVED_PREVIEW_PAGES_MISMATCH')
    if wanted!=ids[ids.index(wanted[0]):ids.index(wanted[0])+len(wanted)]:raise ValueError('SAVED_PREVIEW_PAGES_MISMATCH')
    try:raw=base64.b64decode(preview['pngBase64'],validate=True)
    except (ValueError,TypeError) as error:raise ValueError('SAVED_PREVIEW_ENCODING') from error
    if len(raw)>MAX_PNG or hashlib.sha256(raw).hexdigest()!=preview['pngSha256']:raise ValueError('SAVED_PREVIEW_HASH_MISMATCH')
    # Inspect the PNG header before decoding; do not allocate unbounded pixels.
    import struct
    if len(raw)<33 or raw[:16]!=b'\x89PNG\r\n\x1a\n\0\0\0\rIHDR':raise ValueError('SAVED_PREVIEW_PNG_HEADER')
    width,height=struct.unpack('>II',raw[16:24])
    if (width,height)!=(preview['width'],preview['height']) or not 1<=min(width,height)<=max(width,height)<=MAX_EDGE:raise ValueError('SAVED_PREVIEW_DIMENSIONS')
    if QImage.fromData(raw,'PNG').isNull():raise ValueError('SAVED_PREVIEW_PNG_INVALID')
    return raw


def summary(preview):
    return {k:deepcopy(v) for k,v in preview.items() if k!='pngBase64'} if preview else None


def notify_saved(path):
    if os.name=='nt':
        import ctypes
        # SHCNE_UPDATEITEM / SHCNF_PATHW: invalidate this file, not Explorer's
        # entire cache. No Explorer restart, registry edit or rendering here.
        ctypes.windll.shell32.SHChangeNotify(0x2000,0x0005,ctypes.c_wchar_p(str(Path(path).resolve())),None)
