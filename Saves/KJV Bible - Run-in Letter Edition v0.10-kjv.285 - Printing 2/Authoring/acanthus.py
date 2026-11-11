"""Place the four supplied engravings by their visible ink in the run-in edition."""
from base64 import b64encode
from functools import lru_cache
from hashlib import sha256
from PIL import Image
from compose import INNER, OUTER, ROOT, pe

ART = ROOT/'Inputs/Print artwork'
FILES = {
    'title': ('Title Page.png','777a4fd9c6c6192d785c4f1148b166ef927eeb3d9b118f308358c783b3c3b8e0'),
    'frontispiece': ('Engraved acanthus frontispiece with foliate knot.png','4ce7a02771c897a548c56a5a94ac207073037858552ea96d7e5c76ae6f24d6a0'),
    'left': ('Left-hand Horizontal acanthus fleur ornament.png','1c0d6593c04a4f91dc7bcad36a00b4afe59c1d9551da3bad0ab65d521cd50cdf'),
    'right': ('Mirrored right-hand printer’s ornament.png','59e66deda83bd3c1e59b8bf86ed4666ea91ffd54e15e585660852af20175a025'),
}
TEXT_WIDTH = 612-INNER-OUTER
FLEUR_WIDTH = 126.
FLEUR_INSET = 14.


@lru_cache(maxsize=4)
def source(role):
    name,key=FILES[role]
    path=ART/name
    data=path.read_bytes()
    assert sha256(data).hexdigest()==key,name
    with Image.open(path) as image:
        rgba=image.convert('RGBA')
        white=Image.new('RGBA',rgba.size,'white')
        white.alpha_composite(rgba)
        ink=white.convert('L').point(lambda l:255 if l<110 else 0).getbbox()
        assert ink is not None
        entry=dict(width=image.width,height=image.height,png=b64encode(data).decode('ascii'))
    return key,entry,ink


def place(role,left,center_y,width):
    key,asset,(x0,y0,x1,y1)=source(role)
    scale=width/(x1-x0)
    # Retain the complete PNG; its blank or transparent padding is outside the ink box.
    return dict(asset=key,rect=[left-x0*scale,center_y-(y0+y1)*scale/2,
                                asset['width']*scale,asset['height']*scale])


def vine_paths(spec):
    # Both old vines are between the double-rule banner edges and the book title.
    # Select their ink exclusively inside its two side panels.
    title=next(p for p in spec['paths'] if p['role']=='book-title')
    tx,_,tw,_=title['bounds']
    return [p for p in spec['paths'] if p['role']=='ornament'
            and p['bounds'][1]>56 and p['bounds'][1]+p['bounds'][3]<140
            and (p['bounds'][0]+p['bounds'][2]<=tx or p['bounds'][0]>=tx+tw)]


def expected_images(spec):
    if spec['kind']=='title': return [place('title',(612-TEXT_WIDTH)/2,392,TEXT_WIDTH)]
    if spec['kind']=='frontispiece': return [place('frontispiece',OUTER,392,TEXT_WIDTH)]
    if spec['kind']!='opening': return []
    left=INNER if spec['side']=='right' else OUTER
    return [place('left',left+FLEUR_INSET,98,FLEUR_WIDTH),
            place('right',left+TEXT_WIDTH-FLEUR_INSET-FLEUR_WIDTH,98,FLEUR_WIDTH)]


def apply(state):
    edition=state['printEdition']
    for role in FILES:
        key,asset,_=source(role)
        if key in edition['assets']: assert asset==edition['assets'][key]
        else: edition['assets'][key]=asset
    changed=[]
    for page in state['pages']:
        spec=edition['pages'][page['pageId']]
        if spec['kind']=='opening':
            old=vine_paths(spec)
            assert len(old)==58 and not spec['images']
            removed={id(p) for p in old}
            spec['paths']=[p for p in spec['paths'] if id(p) not in removed]
        if spec['kind'] in ('title','frontispiece','opening'):
            spec['images']=expected_images(spec)
            changed.append(page['pageId'])
    assert len(changed)==68
    return changed


def check(state):
    edition=state['printEdition']
    assert len(edition['assets'])==4 and len(edition['sections'])==66
    for role in FILES:
        key,asset,_=source(role)
        assert edition['assets'][key]==asset
    for pg in state['pages']:
        spec=edition['pages'][pg['pageId']]
        assert spec['images']==expected_images(spec)
        if spec['kind']=='opening':
            from PySide6.QtCore import QRectF
            assert not vine_paths(spec)
            assert len(spec['images'])==2
            for image in spec['images']:
                b=QRectF(*image['rect'])
                for path in spec['paths']: assert not pe.decode_path(path).intersects(b),(pg['name'],path['role'])
                for line in spec['lines']: assert not b.intersects(QRectF(*line['bounds']))
