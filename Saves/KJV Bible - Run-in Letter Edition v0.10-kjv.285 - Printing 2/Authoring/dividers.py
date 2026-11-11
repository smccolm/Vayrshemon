"""Center each internal chapter numeral in its existing horizontal measure."""
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainterPath
from compose import pe


def rule(start,stop,y,height,role):
    assert start<stop
    path=QPainterPath()
    path.addRect(QRectF(start,y-height/2,stop-start,height))
    return pe.encode_path(path,role)


def center(state):
    counts={'fullWidth':0,'inline':0}
    specs=state['printEdition']['pages']
    for page in state['pages']:
        spec=specs[page['pageId']]
        paths=[]
        for item in spec['paths']:
            if item['role']!='chapter-heading':
                paths.append(item)
                continue
            old=paths.pop()
            assert old['role']=='ornament'
            rx,_,rw,weight=old['bounds']
            assert abs(weight-.45)<1e-6
            x,y,w,h=item['bounds']
            if rw>100:
                kind='fullWidth'
                start=int(page['margins']['left'])/1e6
                end=612-int(page['margins']['right'])/1e6
                gap=8.
                assert abs(start-x)<1e-6 and abs(end-rx-rw)<.05
            else:
                kind='inline'
                start,end=x,rx+rw
                gap=3.
            counts[kind]+=1
            new_x=(start+end-w)/2
            glyph=pe.decode_path(item).translated(new_x-x,0)
            mid_y=y+h/2
            paths.extend((rule(start,new_x-gap,mid_y,weight,'chapter-rule-left'),
                          pe.encode_path(glyph,'chapter-heading'),
                          rule(new_x+w+gap,end,mid_y,weight,'chapter-rule-right')))
        spec['paths']=paths
    assert sum(counts.values())==1123
    return counts


def check(state):
    counts={'fullWidth':0,'inline':0}
    for page in state['pages']:
        spec=state['printEdition']['pages'][page['pageId']]
        for j,item in enumerate(spec['paths']):
            if item['role']!='chapter-heading':continue
            before,after=spec['paths'][j-1],spec['paths'][j+1]
            assert (before['role'],after['role'])==('chapter-rule-left','chapter-rule-right')
            a,b,c=(QRectF(*p['bounds']) for p in (before,item,after))
            assert abs(a.width()-c.width())<1e-6 and abs(a.height()-.45)<1e-6 and abs(c.height()-.45)<1e-6
            assert a.right()<b.left()<b.right()<c.left()
            assert abs((b.left()-a.right())-(c.left()-b.right()))<1e-6
            assert max(abs(box.center().y()-b.center().y()) for box in (a,c))<1e-6
            if a.width()>50:
                counts['fullWidth']+=1
                left=int(page['margins']['left'])/1e6
                right=612-int(page['margins']['right'])/1e6
                assert max(abs(a.left()-left),abs(c.right()-right),abs(b.center().x()-(left+right)/2))<1e-6
            else: counts['inline']+=1
            for line in spec['lines']:
                assert not any(box.intersects(QRectF(*line['bounds'])) for box in (a,b,c)),(page['name'],item)
    assert counts=={'fullWidth':1068,'inline':55}
    return counts
