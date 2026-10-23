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
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, shift
from scipy.spatial import cKDTree
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QImage, QPainter, QColor, QPainterPath, QTransform

VERSION='1.0.0'
# Implementation changes are distinct from the persisted recipe/state format.
ENGINE_VERSION='1.1.0'
LEGACY_DEFAULT=dict(recipeId='paint.individual-glyphs',version=VERSION,revision=1,
    rim='#0674da',highlight='#ffffff',recess='#0d11a2',edge='#020918',glow='#beffff',
    bevel=.030,depth=1.64,edgeWidth=.001,glowRadius=.017,glowOpacity=.56,
    shadowRadius=.004,shadowX=.003,shadowY=.005,shadowOpacity=.8,
    lightAzimuth=120,lightElevation=30,gradient=.10)
# Optional additions keep existing 1.0.0 recipes readable, with their original
# lighting. New documents and the explicit Restore button opt into this profile.
DEFAULT=dict(LEGACY_DEFAULT,lightingModel='individual-glyphs-1',referenceGradients=True,
    recess='#080fa2',recessTop='#0e1153',recessBottom='#0d1167',edge='#000000',
    interiorBevel=.065,highlightOpacity=.66,bevelShadowOpacity=.75,
    normalSmoothing=.001,glowRadius=.020,glowRange=.49,glowSpread=.00051,
    shadowRadius=.001667,shadowX=.0025,shadowY=.00433,shadowOpacity=.75,gradient=0.)
MAX_TILE_PIXELS=6_000_000
CACHE_BYTES=96*1024*1024


def initial(): return dict(version=VERSION,recipe=deepcopy(DEFAULT),bindings=[],background='#FFFFFFFF',rasterDpi=300)
def signature(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def rgb(color): return np.array([int(color[i:i+2],16) for i in (1,3,5)],dtype=np.float32)/255

REFERENCE_PROFILE=json.loads((Path(__file__).resolve().parents[1]/'data/individual-glyphs-lighting.json').read_text())
PROFILE_HASH=signature(REFERENCE_PROFILE)
REFERENCE_GLYPHS={item['glyphName']:item for item in REFERENCE_PROFILE['glyphs']}


def padding(recipe,em):
    # Blur support is explicitly truncated at 3 sigma, including subpixel AA.
    spread=recipe.get('glowSpread',DEFAULT['glowSpread']) if recipe.get('lightingModel')=='individual-glyphs-1' else 0
    return .5+em*(recipe['edgeWidth']+max(3*recipe['glowRadius']+spread,3*recipe['shadowRadius']+max(abs(recipe['shadowX']),abs(recipe['shadowY']))))


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


def vector_distance(path,alpha,area,scale):
    """Interior distance to subpixel outline segments, not binary pixel centers.

    Qt flattens only for this lighting field; the original curves still produce
    the coverage mask. Short segments bound the nearest-midpoint search error.
    Chunked queries avoid a full canvas x boundary distance allocation.
    """
    segments=[]
    flatten=8.
    # ADD coverage also means ADD relief: buried overlap edges are not bevels.
    # Simplify after scaling so Qt's boolean flattening stays subpixel even at
    # reading size. Original curves remain untouched in the coverage mask.
    boundary=QTransform.fromScale(scale*flatten,scale*flatten).map(path).simplified()
    for polygon in boundary.toSubpathPolygons():
        points=np.array([(p.x()/flatten-area.x()*scale,p.y()/flatten-area.y()*scale) for p in polygon])
        if len(points)<2: continue
        if not np.array_equal(points[0],points[-1]): points=np.vstack((points,points[0]))
        for a,b in zip(points,points[1:]):
            length=np.linalg.norm(b-a)
            if length<1e-9: continue
            n=max(1,math.ceil(length))
            starts=a+(b-a)*np.arange(n)[:,None]/n
            segments.extend(zip(starts,starts+(b-a)/n))
    result=np.zeros(alpha.shape,dtype=np.float32)
    if not segments: return result
    starts,ends=np.asarray(segments).transpose(1,0,2)
    vectors=ends-starts;length2=np.sum(vectors*vectors,axis=1)
    tree=cKDTree((starts+ends)/2)
    yy,xx=np.nonzero(alpha>0);k=min(3,len(starts))
    for offset in range(0,len(xx),65536):
        y=yy[offset:offset+65536];x=xx[offset:offset+65536]
        points=np.column_stack((x+.5,y+.5))
        _,indices=tree.query(points,k=list(range(1,k+1)))
        relative=points[:,None,:]-starts[indices];v=vectors[indices]
        t=np.clip(np.sum(relative*v,axis=2)/length2[indices],0,1)
        distance2=np.sum((relative-v*t[:,:,None])**2,axis=2)
        result[y,x]=np.sqrt(distance2.min(axis=1))
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

    def reference_gradient(self,binding,gid):
        recipe=self.book.state['paint']['recipe']
        if recipe.get('lightingModel')!='individual-glyphs-1' or not recipe.get('referenceGradients',True) or binding['fontId']!=REFERENCE_PROFILE['fontId']: return None
        name=self.book.fonts.resolve(binding['fontId']).glyph_order[gid]
        entry=REFERENCE_GLYPHS.get(name)
        if entry is None: return None
        return dict(profileId=REFERENCE_PROFILE['profileId'],profileHash=PROFILE_HASH,
            gradientId=entry['gradient'],stops=REFERENCE_PROFILE['gradients'][entry['gradient']],
            source=entry['source'],sourceSha256=entry['sha256'])

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

    def registration(self,binding,gid,em,origin=(0.,0.)):
        """Inspect layer coordinates without independently centering any layer."""
        master=self.book.fonts.resolve(binding['fontId']);name=master.glyph_order[gid]
        paths=self.paths(binding,gid,em)
        fields=(('outline','fontId',0),('interior','interiorFontId',2),('glow','glowFontId',1))
        layers=[]
        for role,key,index in fields:
            if key not in binding: continue
            face=self.book.fonts.resolve(binding[key]);bounds=paths[index].boundingRect()
            layers.append(dict(role=role,fontId=face.font_id,glyphId=face.glyph_order.index(name),glyphName=name,
                em=em,unitsPerEm=face.units_per_em,advance=face.metrics[name][0],sideBearing=face.metrics[name][1],
                origin=list(origin),transform=[1,0,0,1,*origin],
                localBounds=[bounds.x(),bounds.y(),bounds.width(),bounds.height()],
                fillRule='add-subpaths' if role=='interior' else 'source-font'))
        return dict(placement='master-origin',paintOrder=['glow','interior','outline-shadow','outline-edge','outline'],layers=layers,
                    referenceGradient=self.reference_gradient(binding,gid))

    def tile(self,binding,gid,em,scale,component='composite'):
        recipe=self.book.state['paint']['recipe']
        calibrated=recipe.get('lightingModel')=='individual-glyphs-1'
        setting=lambda key:recipe.get(key,DEFAULT[key])
        # At least 4 samples per logical pixel at reading size. Export uses its
        # requested DPI, with 2x AA, never a magnified preview bitmap.
        scale=max(4. if em<128 else 2.,math.ceil(scale*2)/2)
        key=(ENGINE_VERSION,PROFILE_HASH,signature(recipe),signature(binding),gid,round(em,6),scale,component)
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
        glow_mask=silhouette
        if calibrated and setting('glowSpread'):
            distance=distance_transform_edt(silhouette<.5)
            glow_mask=np.maximum(silhouette,np.clip(setting('glowSpread')*empx+.5-distance,0,1))
        glow=blur(glow_mask,recipe['glowRadius'])
        if calibrated:
            # Archived soft glow: 49% range, custom contour (0,0), (53,38),
            # (255,255). Range is applied before the contour, not as opacity.
            glow=np.interp(np.clip(glow/setting('glowRange'),0,1),[0,53/255,1],[0,38/255,1])
        glow=glow*(1-silhouette)*recipe['glowOpacity']
        if component!='surface': over(rgb(recipe['glow']),glow)

        def shade(alpha,base,recess=False):
            if not alpha.any(): return
            inside=alpha>=.5
            distance=vector_distance(paths[2 if recess else 0],alpha,area,scale) if calibrated else distance_transform_edt(inside)-distance_transform_edt(~inside)
            # Linear chisel, with a small normal filter to suppress grid stair
            # steps. Interior relief slopes inward; ridge relief slopes outward.
            bevel=max(1,(setting('interiorBevel') if calibrated and recess else recipe['bevel']*(65/30 if recess else 1))*empx)
            height=np.clip(distance,0,bevel)
            height=gaussian_filter(height,max(.7,(setting('normalSmoothing') if calibrated else .0012)*empx),truncate=3)
            dy,dx=np.gradient(height)
            nx=-dx*recipe['depth']; ny=-dy*recipe['depth']; nz=np.ones(shape)
            norm=np.sqrt(nx*nx+ny*ny+nz*nz);nx/=norm;ny/=norm;nz/=norm
            az=math.radians(recipe['lightAzimuth']); el=math.radians(recipe['lightElevation'])
            lx,ly,lz=math.cos(az)*math.cos(el),-math.sin(az)*math.cos(el),math.sin(el)
            lambert=np.clip(nx*lx+ny*ly+nz*lz,0,1)
            base=rgb(base); highlight=rgb(recipe['highlight'])
            intensity=np.clip((lambert-lz)*2,-1,1)
            if calibrated and recess:
                # The 90-degree, layer-aligned PSD gradient runs bottom to top.
                # It follows the interior ink, never the padded glow canvas.
                bounds=paths[2].boundingRect()
                y=area.top()+(np.arange(shape[0])+.5)/scale
                position=np.clip((bounds.bottom()-y)/max(bounds.height(),1e-9),0,1)
                bottom,top=rgb(setting('recessBottom')),rgb(setting('recessTop'))
                mid=1981/4096;midpoint=.53
                reference=self.reference_gradient(binding,gid)
                if reference:
                    stops=reference['stops'];bottom,base,top=[rgb(s['color']) for s in stops]
                    mid=stops[1]['position'];midpoint=stops[1]['midpoint']
                t=np.clip((position-mid)/(1-mid),0,1)**(math.log(.5)/math.log(midpoint))
                lower=bottom[None,:]+(base-bottom)[None,:]*np.clip(position/mid,0,1)[:,None]
                upper=base[None,:]+(top-base)[None,:]*t[:,None]
                base=np.where((position<mid)[:,None],lower,upper)[:,None,:]
            lit=base*(1+np.minimum(intensity,0)[:,:,None]*(setting('bevelShadowOpacity') if calibrated else .65))
            amount=np.maximum(intensity,0)[:,:,None]*(setting('highlightOpacity') if calibrated else .75)
            lit=1-(1-lit)*(1-highlight*amount) if calibrated else lit*(1-amount)+highlight*amount
            if recess and not calibrated: lit*=.78
            gradient=np.linspace(1+recipe['gradient'],1-recipe['gradient'],shape[0])[:,None,None]
            over(np.clip(lit*gradient,0,1),alpha)
        # Photoshop's three geometrically distinct layers share one origin.
        # The 80 font supplies glow only, never an opaque fill/stroke. The 79
        # outline casts its shadow onto the 81 interior beneath it.
        if component!='glow':
            shade(interior,recipe['recess'],True)
            shadow=shift(blur(rim,recipe['shadowRadius']),
                         (recipe['shadowY']*empx,recipe['shadowX']*empx),order=1,mode='constant',prefilter=False)
            over(np.zeros(3),shadow*recipe['shadowOpacity'])
            edge=recipe['edgeWidth']*empx
            if edge:
                distance=distance_transform_edt(rim<.5)
                over(rgb(recipe['edge']),np.maximum(rim,np.clip(edge+.5-distance,0,1)))
            shade(rim,recipe['rim'])
        # Store straight RGBA; Qt handles premultiplication during composition.
        alpha=result[:,:,3:4]; color=np.divide(result[:,:,:3],alpha,out=np.zeros_like(result[:,:,:3]),where=alpha>0)
        rgba=np.clip(np.concatenate([color,alpha],axis=2)*255+.5,0,255).astype(np.uint8)
        image=QImage(rgba.data,shape[1],shape[0],shape[1]*4,QImage.Format.Format_RGBA8888).copy()
        cost=image.sizeInBytes()
        while self.cache and self.bytes+cost>CACHE_BYTES:
            _,(old,_) = self.cache.popitem(last=False); self.bytes-=old.sizeInBytes()
        if cost<=CACHE_BYTES: self.cache[key]=(image,area);self.bytes+=cost
        return image,area

    def draw(self,painter,binding,gid,em,scale,origin=(0.,0.),component='composite'):
        calibrated=self.book.state['paint']['recipe'].get('lightingModel')=='individual-glyphs-1'
        components=('glow','surface') if calibrated and component=='composite' else (component,)
        painter.save()
        try:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            for part in components:
                image,area=self.tile(binding,gid,em,scale,part)
                if image is None: continue
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen if calibrated and part=='glow' else QPainter.CompositionMode.CompositionMode_SourceOver)
                painter.drawImage(area.translated(QPointF(*origin)),image)
        finally: painter.restore()

    def paint(self,painter,glyph,component='composite'):
        binding=self.binding(glyph['fontId'])
        if not binding: return False
        transform=painter.deviceTransform(); scale=max(math.hypot(transform.m11(),transform.m12()),math.hypot(transform.m21(),transform.m22()))
        self.draw(painter,binding,glyph['glyphId'],glyph['pixelSize'],scale*2,glyph['origin'],component)
        return True
