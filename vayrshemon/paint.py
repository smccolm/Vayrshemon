"""M4 deterministic outline-derived lighting. No reference bitmaps enter the renderer.

Distances are fractions of an em. Tiles are supersampled, alpha bounded, and
cached by the complete recipe and source identity. Photoshop is a reference,
not a required runtime or a promise of pixel-identical proprietary blending.
"""
from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
import math
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, shift
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QImage, QPainter, QColor, QPainterPath

VERSION='1.0.0'
# Implementation changes are distinct from the persisted recipe/state format.
ENGINE_VERSION='1.0.1'
DEFAULT=dict(recipeId='paint.individual-glyphs',version=VERSION,revision=1,
    rim='#0674da',highlight='#ffffff',recess='#0d11a2',edge='#020918',glow='#beffff',
    bevel=.030,depth=1.64,edgeWidth=.001,glowRadius=.017,glowOpacity=.56,
    shadowRadius=.004,shadowX=.003,shadowY=.005,shadowOpacity=.8,
    lightAzimuth=120,lightElevation=30,gradient=.10)
MAX_TILE_PIXELS=6_000_000
CACHE_BYTES=96*1024*1024


def initial(): return dict(version=VERSION,recipe=deepcopy(DEFAULT),bindings=[],background='#FFFFFFFF',rasterDpi=300)
def signature(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def rgb(color): return np.array([int(color[i:i+2],16) for i in (1,3,5)],dtype=np.float32)/255


def padding(recipe,em):
    # Blur support is explicitly truncated at 3 sigma, including subpixel AA.
    return .5+em*(recipe['edgeWidth']+max(3*recipe['glowRadius'],3*recipe['shadowRadius']+max(abs(recipe['shadowX']),abs(recipe['shadowY']))))


def mask(path,area,scale):
    w,h=math.ceil(area.width()*scale),math.ceil(area.height()*scale)
    image=QImage(w,h,QImage.Format.Format_RGBA8888); image.fill(Qt.GlobalColor.transparent)
    painter=QPainter(image); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(scale,scale); painter.translate(-area.x(),-area.y())
    painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(Qt.GlobalColor.white); painter.drawPath(path); painter.end()
    return np.frombuffer(image.constBits(),np.uint8).reshape(h,image.bytesPerLine())[:,:w*4].reshape(h,w,4)[:,:,3].astype(np.float32)/255


def union_subpaths(path):
    # Archived interior instructions specify ADD each closed shape, not XOR.
    result=QPainterPath();result.setFillRule(Qt.FillRule.WindingFill)
    parts=[];part=None;i=0
    while i<path.elementCount():
        element=path.elementAt(i)
        if element.isMoveTo():
            if part is not None: parts.append(part)
            part=QPainterPath(QPointF(element.x,element.y))
        elif element.isLineTo(): part.lineTo(element.x,element.y)
        elif element.isCurveTo():
            b,c=path.elementAt(i+1),path.elementAt(i+2)
            part.cubicTo(element.x,element.y,b.x,b.y,c.x,c.y);i+=2
        i+=1
    if part is not None: parts.append(part)
    for part in parts:
        part.closeSubpath();polygon=list(part.toFillPolygon())
        area=sum(a.x()*b.y()-b.x()*a.y() for a,b in zip(polygon,polygon[1:]))
        result.addPath(part if area>=0 else part.toReversed())
    return result


def derived_paths(raw,gid):
    """Shade attested ink only, preserving curves, fill rule and every counter.

    A single font cannot distinguish a recessed channel from intentional empty
    space. Interior fills require an explicit layered binding; closing contours
    or unioning their polygons would silently paint over genuine counters.
    """
    rim=raw.pathForGlyph(gid)
    return rim,QPainterPath(rim),QPainterPath()


class Renderer:
    def __init__(self,book): self.book=book; self.cache=OrderedDict(); self.bytes=0

    def binding(self,font_id):
        return next((b for b in self.book.state['paint']['bindings'] if b['fontId']==font_id and b['enabled']),None)

    def paths(self,binding,gid,em):
        fonts=self.book.fonts; raw=fonts.raw(binding['fontId'],em)
        if not 0<=gid<len(fonts.resolve(binding['fontId']).glyph_order): raise ValueError('GLYPH_ID_OUT_OF_RANGE')
        if binding['kind']=='layered':
            name=fonts.resolve(binding['fontId']).glyph_order[gid]
            def layer(fid):
                face=fonts.resolve(fid); return fonts.raw(fid,em).pathForGlyph(face.glyph_order.index(name))
            return raw.pathForGlyph(gid),layer(binding['glowFontId']),union_subpaths(layer(binding['interiorFontId']))
        return derived_paths(raw,gid)

    def bounds(self,binding,gid,em):
        paths=self.paths(binding,gid,em); area=QRectF()
        for path in paths:
            if not path.isEmpty(): area=area.united(path.boundingRect())
        if area.isEmpty(): return area
        pad=padding(self.book.state['paint']['recipe'],em)
        return area.adjusted(-pad,-pad,pad,pad)

    def tile(self,binding,gid,em,scale):
        recipe=self.book.state['paint']['recipe']
        # At least 4 samples per logical pixel at reading size. Export uses its
        # requested DPI, with 2x AA, never a magnified preview bitmap.
        scale=max(4. if em<128 else 2.,math.ceil(scale*2)/2)
        key=(ENGINE_VERSION,signature(recipe),signature(binding),gid,round(em,6),scale)
        if key in self.cache:
            value=self.cache.pop(key);self.cache[key]=value;return value
        paths=self.paths(binding,gid,em); area=self.bounds(binding,gid,em)
        if area.isEmpty(): return None,area
        # Align only the tile raster; preserve the source path's exact origin.
        area=QRectF(math.floor(area.left()*scale)/scale,math.floor(area.top()*scale)/scale,
                    (math.ceil(area.right()*scale)-math.floor(area.left()*scale))/scale,
                    (math.ceil(area.bottom()*scale)-math.floor(area.top()*scale))/scale)
        if math.ceil(area.width()*scale)*math.ceil(area.height()*scale)>MAX_TILE_PIXELS:
            raise ValueError('PAINT_TILE_LIMIT: reduce glyph size or raster DPI')
        rim,silhouette,interior=[mask(path,area,scale) for path in paths]
        shape=rim.shape; result=np.zeros((*shape,4),dtype=np.float32); empx=em*scale

        def over(color,alpha):
            alpha=np.clip(alpha,0,1)
            result[:,:,:3]*=(1-alpha[:,:,None]); result[:,:,:3]+=color*alpha[:,:,None]
            result[:,:,3]*=(1-alpha); result[:,:,3]+=alpha

        def blur(alpha,radius): return gaussian_filter(alpha,max(.01,radius*empx),truncate=3,mode='constant')
        glow=blur(silhouette,recipe['glowRadius'])*recipe['glowOpacity']
        over(rgb(recipe['glow']),glow)
        shadow=shift(blur(silhouette,recipe['shadowRadius']),
                     (recipe['shadowY']*empx,recipe['shadowX']*empx),order=1,mode='constant',prefilter=False)
        over(np.zeros(3),shadow*recipe['shadowOpacity'])
        edge=recipe['edgeWidth']*empx
        if edge:
            distance=distance_transform_edt(silhouette<.5)
            over(rgb(recipe['edge']),np.maximum(silhouette,np.clip(edge+.5-distance,0,1)))

        def shade(alpha,base,recess=False):
            if not alpha.any(): return
            inside=alpha>=.5
            distance=distance_transform_edt(inside)-distance_transform_edt(~inside)
            # Linear chisel, with a small normal filter to suppress grid stair
            # steps. Interior relief slopes inward; ridge relief slopes outward.
            bevel=max(1,recipe['bevel']*empx*(65/30 if recess else 1))
            height=np.clip(distance,0,bevel)
            height=gaussian_filter(height,max(.7,.0012*empx),truncate=3)
            dy,dx=np.gradient(height)
            nx=-dx*recipe['depth']; ny=-dy*recipe['depth']; nz=np.ones(shape)
            norm=np.sqrt(nx*nx+ny*ny+nz*nz);nx/=norm;ny/=norm;nz/=norm
            az=math.radians(recipe['lightAzimuth']); el=math.radians(recipe['lightElevation'])
            lx,ly,lz=math.cos(az)*math.cos(el),-math.sin(az)*math.cos(el),math.sin(el)
            lambert=np.clip(nx*lx+ny*ly+nz*lz,0,1)
            hx,hy,hz=lx,ly,lz+1; hn=math.sqrt(hx*hx+hy*hy+hz*hz)
            spec=np.clip((nx*hx+ny*hy+nz*hz)/hn,0,1)**14
            base=rgb(base); highlight=rgb(recipe['highlight'])
            intensity=np.clip((lambert-lz)*2,-1,1)
            lit=base[None,None,:]*(1+np.minimum(intensity,0)[:,:,None]*.65)
            amount=np.maximum(intensity,0)[:,:,None]*.75
            lit=lit*(1-amount)+highlight[None,None,:]*amount
            if recess: lit*=.78
            gradient=np.linspace(1+recipe['gradient'],1-recipe['gradient'],shape[0])[:,None,None]
            over(np.clip(lit*gradient,0,1),alpha)
        shade(interior,recipe['recess'],True);shade(rim,recipe['rim'])
        # Store straight RGBA; Qt handles premultiplication during composition.
        alpha=result[:,:,3:4]; color=np.divide(result[:,:,:3],alpha,out=np.zeros_like(result[:,:,:3]),where=alpha>0)
        rgba=np.clip(np.concatenate([color,alpha],axis=2)*255+.5,0,255).astype(np.uint8)
        image=QImage(rgba.data,shape[1],shape[0],shape[1]*4,QImage.Format.Format_RGBA8888).copy()
        cost=image.sizeInBytes()
        while self.cache and self.bytes+cost>CACHE_BYTES:
            _,(old,_) = self.cache.popitem(last=False); self.bytes-=old.sizeInBytes()
        if cost<=CACHE_BYTES: self.cache[key]=(image,area);self.bytes+=cost
        return image,area

    def paint(self,painter,glyph):
        binding=self.binding(glyph['fontId'])
        if not binding: return False
        transform=painter.deviceTransform(); scale=max(math.hypot(transform.m11(),transform.m12()),math.hypot(transform.m21(),transform.m22()))
        image,area=self.tile(binding,glyph['glyphId'],glyph['pixelSize'],scale*2)
        if image is not None:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawImage(area.translated(QPointF(*glyph['origin'])),image)
        return True
