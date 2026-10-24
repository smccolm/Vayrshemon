"""Build the app's Memon icons from its exact code-native glyph paths.

The checked-in single-glyph geometry permits reproducible icons without shipping
private font files. Extraction is explicit and never part of ordinary setup.
"""
import argparse,io,json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QBuffer,QByteArray,QIODevice
from PySide6.QtGui import QImage,QPainter,QPainterPath,QTransform,QColor
from PIL import Image
from tools.m0.common import write_json,file_hash
from vayrshemon.paint import Renderer

ROOT=Path(__file__).resolve().parents[1]


def extract(document):
    from vayrshemon.gloss_api import GlossSession
    book=GlossSession(ROOT,source_fonts=False,recovery=False)
    try:
        book.open(document,advance_revision=False)
        binding=next(b for b in book.state['paint']['bindings'] if b['kind']=='layered' and b['enabled'])
        renderer=Renderer(book);gid=book.fonts.resolve(binding['fontId']).glyph_order.index('M')
        paths=renderer.paths(binding,gid,1000)
        result=dict(version=1,glyphName='M',reference='Maxima_28_Memon.jpg',
            referenceSha256=file_hash(ROOT/'Inputs/Versions Best/Individual Glyphs/Maxima_28_Memon.jpg'),
            em=1000,recipe=deepcopy(book.state['paint']['recipe']),binding=binding,
            gradient=renderer.reference_gradient(binding,gid),
            paths=[dict(fillRule=p.fillRule().value,elements=[[p.elementAt(i).type.value,p.elementAt(i).x,p.elementAt(i).y] for i in range(p.elementCount())]) for p in paths])
        write_json(ROOT/'data/icons/memon-paths.json',result)
    finally:book.finish()


def load_paths(spec):
    paths=[]
    for record in spec['paths']:
        path=QPainterPath();path.setFillRule(Qt.FillRule(record['fillRule']));items=record['elements'];i=0
        while i<len(items):
            kind,x,y=items[i]
            if kind==0:path.moveTo(x,y)
            elif kind==1:path.lineTo(x,y)
            elif kind==2:path.cubicTo(x,y,*items[i+1][1:],*items[i+2][1:]);i+=2
            i+=1
        paths.append(path)
    return paths


def build():
    folder=ROOT/'data/icons';spec=json.loads((folder/'memon-paths.json').read_text());paths=load_paths(spec)
    class IconRenderer(Renderer):
        def paths(self,binding,gid,em):return [QTransform.fromScale(em/spec['em'],em/spec['em']).map(p) for p in paths]
        def reference_gradient(self,binding,gid):return spec['gradient']
    renderer=IconRenderer(SimpleNamespace(state={'paint':{'recipe':spec['recipe']}}));binding=spec['binding']
    # Center the visible silhouette, including its descending curl, rather than
    # the original rectangular photograph. Identical transform in all modes.
    ink=paths[1].boundingRect();edge=256;em=spec['em']*(edge*.78/max(ink.width(),ink.height()))
    scaled=QTransform.fromScale(em/spec['em'],em/spec['em']).map(paths[1]);center=scaled.boundingRect().center()
    for mode in ('color','mono-black','mono-white'):
        image=QImage(edge,edge,QImage.Format.Format_ARGB32_Premultiplied);image.fill(QColor('white' if mode=='mono-white' else 'black'))
        painter=QPainter(image);painter.setRenderHint(QPainter.RenderHint.Antialiasing);painter.translate(edge/2-center.x(),edge/2-center.y())
        if mode=='color':renderer.draw(painter,binding,0,em,1)
        else:painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(QColor('black' if mode=='mono-white' else 'white'));painter.drawPath(scaled)
        painter.end();image.save(str(folder/f'memon-{mode}.png'))
        data=QByteArray();buffer=QBuffer(data);buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG')
        # ICO is a standard multi-resolution asset container; Pillow packs the
        # code-rendered icon into the Windows sizes, including high-DPI lists.
        Image.open(io.BytesIO(bytes(data))).save(folder/f'memon-{mode}.ico',sizes=[(n,n) for n in (16,20,24,32,40,48,64,96,128,256)])
    print('Built centered Memon icons: color, white on black, black on white.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--extract-source',type=Path);args=parser.parse_args()
    app=QApplication.instance() or QApplication([])
    if args.extract_source:extract(args.extract_source)
    build()
