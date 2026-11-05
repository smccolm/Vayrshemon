"""Read-only adapters around the exact Workbench shaping and paint engines.

No authoring session, Forge, recovery, undo history or document writes.
Qt fonts/layouts live only in the rendering process's main thread.
"""
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
import hashlib,json,math,os,struct,time,zlib
from PySide6.QtCore import QRectF,Qt,QCoreApplication,QEvent
from PySide6.QtGui import QImage,QPainter
from .storage import ROOT,LOCAL,BookIndex,dumps,engine_key,frame_path,prune_cache
from vayrshemon.fonts import FontRegistry
from vayrshemon.frame import FrameSession
from vayrshemon.paint import Renderer
from vayrshemon.studio_typesetting import StudioComposition
from vayrshemon.incremental import StoryCache
from vayrshemon import pages,page_numbering
from tools.m0.common import load_json
from vayrshemon.schema_validation import NativeDocumentValidator


class QuietLog:
    def emit(self,*args,**kwargs): pass


def publish_cache(temp,path):
    """Immutable hash-keyed entries: competing workers may publish the same key.

    Windows refuses replacing an entry while another worker has it open.
    The first complete atomic rename wins; the equivalent later one is dropped.
    """
    try:
        if not path.exists():os.rename(temp,path)
    except OSError:
        if not path.exists():raise
    finally:temp.unlink(missing_ok=True)


class SnapshotFonts(FontRegistry):
    def resolve(self,identity):
        # Registration validates original file bytes once. Rendering uses the
        # immutable privately registered copy, never rereads a TTF per glyph.
        return self.faces[identity] if identity in self.faces else super().resolve(identity)


class ReadingPaint(Renderer):
    """Persist exact original glyph tiles; never lower the bevel sampling rate."""
    def __init__(self,book):
        super().__init__(book)
        self.disk=LOCAL/'glyphs'/hashlib.sha256(dumps([engine_key(),book.state['paint']])).hexdigest()
        self.disk.mkdir(parents=True,exist_ok=True);self.disk_seen={};self.disk_bytes=0
    def tile(self,binding,gid,em,scale,component='composite'):
        scale=max(4. if em<128 else 2.,math.ceil(scale*2)/2)
        identity=(json.dumps(binding,sort_keys=True),gid,round(em,6),scale,component)
        if identity in self.disk_seen:return self.disk_seen[identity]
        path=self.disk/(hashlib.sha256(dumps(identity)).hexdigest()+'.tile')
        try:
            data=path.read_bytes();size=struct.unpack('<I',data[:4])[0];head=json.loads(data[4:4+size]);raw=zlib.decompress(data[4+size:])
            image=QImage(raw,head['width'],head['height'],head['stride'],QImage.Format(head['format'])).copy();area=QRectF(*head['area'])
        except (OSError,ValueError,KeyError,zlib.error):
            image,area=super().tile(binding,gid,em,scale,component)
            if image is not None:
                head=dumps(dict(width=image.width(),height=image.height(),stride=image.bytesPerLine(),format=image.format().value,area=[area.x(),area.y(),area.width(),area.height()]))
                temp=path.with_suffix('.'+str(os.getpid())+'.tmp');temp.write_bytes(struct.pack('<I',len(head))+head+zlib.compress(bytes(image.constBits()),1));publish_cache(temp,path)
        if image is not None and self.disk_bytes+image.sizeInBytes()<=96*1024*1024:
            self.disk_seen[identity]=(image,area);self.disk_bytes+=image.sizeInBytes()
        return image,area


class ReadingBook:
    def __init__(self,index):
        self.index=index; self.root=ROOT; self.log=QuietLog(); self.revision=0; self.window=None
        self.meta=index.meta; self.state=deepcopy(self.meta['state']); self.state['pages']=[dict(p,frames=[]) for p in self.meta['headers']]
        self.fonts=SnapshotFonts(ROOT,self.log)
        for source in self.state['fontSources']:
            self.fonts.register(self.fonts.document_path(source['path'],source['sha256']),source['sha256'])
        self.fonts.recipe=deepcopy(self.state['recipe'])
        # Setup/tests validate the installed schemas themselves. Reading needs
        # the document validator, not recursive meta-validation of 30 unrelated
        # Forge/API schemas on every worker startup (previously ~3.8 seconds).
        from jsonschema import Draft202012Validator
        from referencing import Registry,Resource
        schemas=[load_json(p) for p in (ROOT/'schemas').glob('*.schema.json')]
        registry=Registry().with_resources((s['$id'],Resource.from_contents(s)) for s in schemas)
        native=load_json(ROOT/'schemas/document.schema.json')
        self.checks={'document':NativeDocumentValidator(Draft202012Validator(native,registry=registry),schemas)}
        self.paint_renderer=ReadingPaint(self);self.story_cache=StoryCache();self.frames={};self.compositions=OrderedDict();self.loaded=set()
        self.saved_page_mode=self.meta['pageMode'];self.number=1;self._numbering_page_mode=None
    @property
    def view(self):return self.state['view']
    @property
    def features(self):return self.state['features']
    def current_page(self):return self.state['pages'][self.number-1]
    def fingerprint(self):return dict(reader=True,sourceSha256=self.meta['sha256'])
    def source_for(self,fid):
        return next((f['source'] for f in self.state['typesetting']['flows'] if fid in f['targets']),fid)
    def prepare(self,number,palette,view):
        self.number=number;self.saved_page_mode=view
        self.view.update(mode='color' if palette=='color' else 'mono',monochromePaper='black' if palette=='black' else 'white')
        self._numbering_page_mode=view
        record=self.index.page(number); group=set(record['connected'])
        if group!=self.loaded:
            for frame in self.frames.values():frame.deleteLater()
            self.frames={};self.compositions.clear();self.story_cache.clear()
            for n in self.loaded:self.state['pages'][n-1]=dict(self.meta['headers'][n-1],frames=[])
            self.state['typesetting']['frames']={}
            if self.state.get('printEdition'):self.state['printEdition']['pages']={}
            for n in sorted(group):
                item=record if n==number else self.index.page(n)
                page=item['page'];self.state['pages'][n-1]=page
                self.state['typesetting']['frames'].update(item['frames'])
                if item['printPage']:self.state['printEdition']['pages'][page['pageId']]=item['printPage']
                if not self.state.get('printEdition'):
                    for frame in page['frames']:
                        native=FrameSession(ROOT,self.fonts,frame['content'],self.checks,self.features)
                        self.frames[frame['frameId']]=native
            self.loaded=group
            QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.state['activeFrameId']=record['page']['frames'][0]['frameId']
        return record['page']
    def composition(self,mode=None,page_id=None):
        mode=mode or self.view['mode'];page_id=page_id or self.current_page()['pageId'];key=(page_id,mode)
        if key not in self.compositions:
            cls=StudioComposition
            if self.state.get('printEdition'):
                from vayrshemon.print_edition import Composition
                cls=Composition
            self.compositions[key]=cls(self,mode,page_id)
            while len(self.compositions)>4:self.compositions.popitem(last=False)
        return self.compositions[key]


def read_image(path):
    with Path(path).open('rb') as f:
        length=struct.unpack('<I',f.read(4))[0]
        if length>4096:raise ValueError('Invalid frame header')
        header=json.loads(f.read(length));raw=zlib.decompress(f.read())
    if len(raw)!=header['height']*header['stride'] or len(raw)>160*1024*1024:raise ValueError('Invalid frame size')
    image=QImage(raw,header['width'],header['height'],header['stride'],QImage.Format.Format_ARGB32_Premultiplied).copy()
    return image


def write_image(path,image):
    path.parent.mkdir(parents=True,exist_ok=True)
    head=dumps(dict(width=image.width(),height=image.height(),stride=image.bytesPerLine()))
    temp=path.with_suffix('.'+str(os.getpid())+'.tmp')
    temp.write_bytes(struct.pack('<I',len(head))+head+zlib.compress(bytes(image.constBits()),1));publish_cache(temp,path)


class Engine:
    def __init__(self,cache):
        self.index=BookIndex(cache); self.book=None; self.signature=engine_key()
        self.folder=LOCAL/'frames';self.folder.mkdir(parents=True,exist_ok=True);self.writes=0
    def render(self,number,palette='white',view='two',scale=1.):
        started=time.perf_counter();meta=self.index.meta
        if type(number) is not int or not 1<=number<=meta['pageCount']:raise ValueError('Page out of range')
        if palette not in ('white','black','color') or view not in ('one','two'):raise ValueError('Invalid reading mode')
        if not math.isfinite(scale) or not .1<=scale<=4:raise ValueError('Zoom out of range')
        scale=round(scale,3)
        path=frame_path(meta['sha256'],number,palette,view,scale)
        if path.exists():
            os.utime(path,None)
            return dict(path=str(path),cached=True,milliseconds=(time.perf_counter()-started)*1000,number=number,palette=palette,view=view,scale=scale)
        init=time.perf_counter()
        if self.book is None:self.book=ReadingBook(self.index)
        initialized=time.perf_counter();page=self.book.prepare(number,palette,view);prepared=time.perf_counter()
        area=pages.page_rect(page);w,h=math.ceil(area.width()*scale),math.ceil(area.height()*scale)
        if w*h>32_000_000:raise ValueError('Zoom image exceeds the 32 megapixel reading limit')
        self.book.composition(page_id=page['pageId']);composed=time.perf_counter()
        # Use the complete original raster path, including DPI and clipping.
        # Below 25% retain a higher-resolution source for the UI to scale down.
        image,_=pages.render(self.book,page_id=page['pageId'],mode=self.book.view['mode'],dpi=max(24,scale*96),page_mode=view)
        painted=time.perf_counter();write_image(path,image);finished=time.perf_counter()
        self.writes+=1
        if self.writes%16==1:self.prune()
        return dict(path=str(path),cached=False,milliseconds=(finished-started)*1000,number=number,palette=palette,view=view,scale=scale,
                    stages=dict(fontsMs=(initialized-init)*1000,pageMs=(prepared-initialized)*1000,composeMs=(composed-prepared)*1000,paintMs=(painted-composed)*1000,encodeMs=(finished-painted)*1000))
    def prune(self):
        prune_cache(self.folder,'*.frame',512*1024**2)
        prune_cache(LOCAL/'glyphs','*/*.tile',256*1024**2)

