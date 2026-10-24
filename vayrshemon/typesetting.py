"""Bounded native shaping, frame flow and conservative collision constraints.

All positions are derived. Source documents, font sizes and font kerning tables
are never edited by the solver. Public distances use points; geometry uses 96dpi.
"""
from copy import deepcopy
import hashlib
import json
import math
import time
import unicodedata
from bisect import bisect_right
from PySide6.QtCore import QPointF,QRectF,Qt,QTextBoundaryFinder
from PySide6.QtGui import QFont,QTextLayout,QTextOption,QTextFormat,QTextCharFormat,QPainterPath,QPainter,QColor,QPen,QGlyphRun
from . import layout
from .session import SCALE,STYLE,LANGUAGE,KIND,scalar_offset,utf16_length,BLOCK
from .typesetting_contracts import profile as default_profile

MAX_GLYPHS=20000
MAX_SCALARS=30000
MAX_COMPARISONS=200000
EPS=1e-5


def box(values): return QRectF(*values)
def numbers(rect): return layout.rectangle(rect)
def hash_value(value): return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=True).encode()).hexdigest()
def frame_rect(frame): return QRectF(*(int(frame[k])/1e6*SCALE for k in ('x','y','width','height')))
def slice16(text,start,end): return text[scalar_offset(text,start):scalar_offset(text,end)]


def boundaries(text,kind=QTextBoundaryFinder.BoundaryType.Grapheme):
    finder=QTextBoundaryFinder(kind,text); result=[0]
    while True:
        value=finder.toNextBoundary()
        if value<0: break
        result.append(value)
    return result


def break_opportunities(text,profiles,language_at):
    """Tailor native UAX #14 opportunities without inserting source characters."""
    graphemes=boundaries(text); native=set(boundaries(text,QTextBoundaryFinder.BoundaryType.Line))
    allowed={0}; reasons={}; total=utf16_length(text)
    for index,end in enumerate(graphemes[1:]):
        start=graphemes[index]
        left=slice16(text,start,end); right=slice16(text,end,graphemes[index+2]) if index+2<len(graphemes) else ''
        p=profiles.get(language_at(start),default_profile(language_at(start)))
        reason='native-unicode' if end in native else None
        if p['wrap']=='grapheme': reason='explicit-grapheme-profile'
        if left and left[-1] in p['breakAfter']: reason='language-tailoring'
        if p['wrap']=='none': reason=None
        # Never weaken nonbreaking controls, joiners, or mandatory breaks.
        if any(c in left+right for c in ('\u00a0','\u202f','\u2060','\ufeff','\u200d')): reason=None
        if (right and right[0] in p['prohibitBefore']) or (left and left[-1] in p['prohibitAfter']): reason=None
        if left.endswith('\u2028'): reason='explicit-line-separator'
        if end==total: reason='end-of-paragraph'
        if reason: allowed.add(end); reasons[end]=dict(reason=reason,languageId=p['languageId'],profileRevision=p['revision'])
    return sorted(allowed),reasons


def independent(text,fmt,rule=None):
    if any(unicodedata.category(c).startswith('M') or c in '\u200c\u200d' for c in text): return False
    if fmt.property(KIND)=='legacy': return bool(rule and rule['independentLegacy'])
    # Unknown joining scripts remain protected. This intentionally conservative
    # subset is for optical pair spacing, not a claim about Unicode segmentation.
    return all(ord(c)<0x250 and unicodedata.bidirectional(c) not in ('R','AL','AN') for c in text)


class Composition:
    def __init__(self,book,mode=None,page_id=None,*,line_metrics=False):
        self.line_metrics=line_metrics
        self.book=book; self.mode=mode or book.view['mode']; self.spec=book.state['typesetting']
        self.frames={f['frameId']:(p,f) for p in book.state['pages'] for f in p['frames']}
        if page_id is not None:
            # Include full linked stories and their neighbouring frames: page
            # collisions may affect pagination, which may reach another page.
            included={page_id}
            while True:
                before=set(included)
                for flow in self.spec['flows']:
                    chain=[flow['source'],*flow['targets']]
                    touched={self.frames[fid][0]['pageId'] for fid in chain}
                    if included & touched: included.update(touched)
                if included==before: break
            self.frames={fid:pair for fid,pair in self.frames.items() if pair[0]['pageId'] in included}
        self.profiles={p['languageId']:p for p in self.spec['profiles']}
        self.stories={}; self.layouts=[]; self.warnings=[]; self.optical=[]; self.glyph_count=0
        self.base=[]; self.final=[]; self.lines=[]; self.base_lines=[]; self.solver=[]
        started=time.perf_counter()
        targets={target for flow in self.spec['flows'] for target in flow['targets']}
        for fid,(_,frame) in self.frames.items():
            if fid in targets: continue
            native=book.frames[fid]; config=self.spec['frames'].get(fid)
            enabled=bool(config and config['enabled'])
            chain=[fid]+next((flow['targets'] for flow in self.spec['flows'] if flow['source']==fid),[])
            if enabled and len(native.text())>MAX_SCALARS: raise ValueError('TYPESETTING_SOURCE_LIMIT: 30,000 scalars per story; disable typesetting for native editing')
            story=dict(source=fid,native=native,config=config if enabled else None,chain=chain,paragraphs=[],glyphs=[],lines=[])
            self.stories[fid]=story
            # Alignment needs the same shaping/placement, without building
            # decorative glyph paths or running diagnostic-only collisions.
            # Never mix these lightweight stories into the paint cache.
            cache=None if line_metrics else getattr(book,'story_cache',None)
            if cache is None: self.shape(story,enabled)
            else: cache.shape(self,story,enabled)
        self.base,self.base_lines,self.base_warnings=self.place({})
        if line_metrics:
            self.lines=self.base_lines
            return
        self.base_collisions,self.base_complete=self.collisions(self.base)
        self.final,self.lines=[dict(g) for g in self.base],deepcopy(self.base_lines)
        self.solve()
        self.final_collisions,self.complete=self.collisions(self.final)
        self.elapsed_ms=(time.perf_counter()-started)*1000
        book.log.emit('typesetting','COMPOSITION_COMPLETED',revision=book.revision,glyphs=self.glyph_count,
                      collisions=len(self.final_collisions),complete=self.complete,elapsedMs=self.elapsed_ms)

    def shape(self,story,enabled):
        native=story['native']; native.doc.documentLayout().documentSize()
        config=story['config']; width=frame_rect(self.frames[story['source']][1]).width()
        groups=[]; line_lookup={}; block=native.doc.begin()
        while block.isValid():
            fragments=[]; iterator=block.begin()
            while not iterator.atEnd():
                fragment=iterator.fragment()
                if fragment.isValid(): fragments.append((fragment.position()-block.position(),fragment.length(),fragment.charFormat()))
                iterator+=1
            def format_at(position):
                return next((f for start,length,f in fragments if start<=position<start+length),block.charFormat())
            bf=block.blockFormat(); block_id=getattr(block.userData(),'identity',None) or bf.property(BLOCK) or f'block.qt.{block.position()}'
            para=dict(blockId=block_id,start=block.position(),before=bf.topMargin(),after=bf.bottomMargin(),lines=[])
            if enabled:
                text=block.text(); option=QTextOption(native.doc.defaultTextOption())
                option.setTextDirection(bf.layoutDirection()); option.setAlignment(bf.alignment()); option.setTabs(bf.tabPositions())
                option.setWrapMode(QTextOption.WrapMode.WrapAnywhere)
                shaped=QTextLayout(text,native.doc.defaultFont(),native.metrics_device)
                shaped.setTextOption(option); shaped.setCacheEnabled(True)
                formats=[]; graphemes=boundaries(text)
                for index,(a,b) in enumerate(zip(graphemes,graphemes[1:])):
                    fmt=QTextCharFormat(format_at(a)); left=slice16(text,a,b)
                    right_end=graphemes[index+2] if index+2<len(graphemes) else b; right=slice16(text,b,right_end)
                    style=next((s for s in native.model['styles'] if s['styleId']==fmt.property(STYLE)),native.model['styles'][0])
                    matches=[r for r in config['optical'] if r['left']==left and r['right']==right and r['fontId']==style['fontId']]
                    if matches:
                        rule=matches[-1]; other=format_at(b)
                        safe=independent(left+right,fmt,rule) and fmt.property(STYLE)==other.property(STYLE)
                        # Do not split a native ligature/connected glyph just
                        # because its source happens to be Latin or legacy slots.
                        def glyph_keys(start,length):
                            return {layout.glyph_key(r.rawFont(),gid,pos) for r in block.layout().glyphRuns(start,length,QTextLayout.GlyphRunRetrievalFlag.RetrieveAll) for gid,pos in zip(r.glyphIndexes(),r.positions())}
                        if safe and glyph_keys(a,b-a).intersection(glyph_keys(b,right_end-b)): safe=False
                        event=dict(sourceFrameId=story['source'],sourceUtf16=[block.position()+a,block.position()+right_end],deltaPoints=rule['delta'],applied=safe)
                        if safe:
                            attrs=native.attributes(fmt); native_font=fmt.font()
                            native_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing,(attrs['tracking']+rule['delta'])*SCALE); fmt.setFont(native_font)
                        else: event['reason']='PROTECTED_JOIN_MARK_OR_FORMAT_BOUNDARY'
                        self.optical.append(event)
                    # Retain imported format changes inside a grapheme (e.g. a
                    # differently colored mark), then coalesce equal formats.
                    cuts=[a]+[start for start,_,_ in fragments if a<start<b]+[b]
                    for first,last in zip(cuts,cuts[1:]):
                        part_format=fmt if first==a else QTextCharFormat(format_at(first))
                        if formats and formats[-1].format==part_format:
                            formats[-1].length+=last-first
                        else:
                            part=QTextLayout.FormatRange(); part.start=first; part.length=last-first; part.format=part_format; formats.append(part)
                shaped.setFormats(formats)
                allowed,reasons=break_opportunities(text,self.profiles,lambda at:format_at(at).property(LANGUAGE) or 'language.en')
                emergency_profiles={key:dict(value,wrap='grapheme') for key,value in self.profiles.items()}
                emergency,_=break_opportunities(text,emergency_profiles,lambda at:format_at(at).property(LANGUAGE) or 'language.en')
                shaped.beginLayout(); local_y=0; line_count=0
                while True:
                    line=shaped.createLine()
                    if not line.isValid(): break
                    line.setLineWidth(width); start=line.textStart(); proposed=start+line.textLength()
                    lower,upper=bisect_right(allowed,start),bisect_right(allowed,proposed)
                    p=self.profiles.get(format_at(start).property(LANGUAGE),default_profile())
                    if upper>lower: end=allowed[upper-1]
                    elif p['emergency'] and p['wrap']!='none':
                        end=max((v for v in emergency if start<v<=proposed),default=next((v for v in emergency if v>start),utf16_length(text)))
                        reasons[end]=dict(reason='emergency-grapheme',languageId=p['languageId'],profileRevision=p['revision'])
                    else: end=next((v for v in allowed if v>start),utf16_length(text))
                    if text and end<=start: raise ValueError('LINE_BREAK_DID_NOT_ADVANCE')
                    # Qt columns count grapheme clusters, not UTF-16 units;
                    # alignmentWidth also caps wrapping. Measure unconstrained
                    # first so a legal unbreakable word can remain overset.
                    columns=max(0,bisect_right(graphemes,end)-bisect_right(graphemes,start))
                    line.setNumColumns(columns)
                    line.setNumColumns(columns,max(width,line.naturalTextWidth()+1/64))
                    line.setPosition(QPointF(0,local_y)); local_y+=line.height()
                    line_count+=1
                    if len(story['lines'])+line_count>10000: raise ValueError('TYPESETTING_LINE_LIMIT')
                shaped.endLayout(); self.layouts.append(shaped)
                if not self.line_metrics:
                    for start,length,fmt in fragments:
                        for run in shaped.glyphRuns(start,length,QTextLayout.GlyphRunRetrievalFlag.RetrieveAll): groups.append((block,shaped,run,fmt))
            else: shaped=block.layout(); reasons={}
            for index in range(shaped.lineCount()):
                line=shaped.lineAt(index); source_start=block.position()+line.textStart()
                natural=line.ascent()+line.descent()
                mode=bf.lineHeightType()
                height=(natural*bf.lineHeight()/100 if mode==1 else bf.lineHeight() if mode==2 else max(natural,bf.lineHeight()) if mode==3 else natural)
                height=max(.01,height)
                item=dict(index=len(story['lines']),blockId=block_id,sourceFrameId=story['source'],sourceUtf16=[source_start,source_start+line.textLength()],
                          ascent=line.ascent(),descent=line.descent(),height=height,width=line.naturalTextWidth(),nativeBaseline=shaped.position().y()+line.y()+line.ascent(),
                          nativeX=shaped.position().x()+line.x(),breakInfo=reasons.get(line.textStart()+line.textLength()),_line=line,_layout=shaped)
                line_lookup[(block.position(),index)]=item; para['lines'].append(item); story['lines'].append(item)
            story['paragraphs'].append(para); block=block.next()
        if self.line_metrics:return
        if not enabled: groups=list(layout.runs(native))
        source_map=layout.source_ranges(groups,MAX_GLYPHS+1)
        for block,shaped,run,fmt in groups:
            raw=run.rawFont(); face=native.fonts.by_family.get(raw.familyName()); style_id=fmt.property(STYLE)
            for gid,position in zip(run.glyphIndexes(),run.positions()):
                self.glyph_count+=1
                if self.glyph_count>MAX_GLYPHS: raise ValueError('TYPESETTING_GLYPH_LIMIT: 20,000 positioned glyphs')
                coverage=source_map.get(block.position(),{}).get(layout.glyph_key(raw,gid,position))
                if coverage is None: raise ValueError('TYPESETTING_SOURCE_MAPPING_UNAVAILABLE: finish composition first')
                start,end=coverage; line=shaped.lineForTextPosition(start); info=line_lookup[(block.position(),line.lineNumber())]
                source=slice16(block.text(),start,end); origin=shaped.position()+position
                paints=[(raw,gid,fmt.foreground().color().name(QColor.NameFormat.HexArgb))]
                recipe=native.fonts.recipe
                if self.mode=='color' and recipe and face and face.font_id==recipe['master']:
                    paints=[(native.fonts.raw(layer['fontId'],raw.pixelSize()),layer['glyphMap'][gid],layer['color']) for layer in recipe['layers'] if layer['enabled']]
                ink=QRectF(); first=True
                for paint_font,paint_gid,_ in paints:
                    area=paint_font.boundingRect(paint_gid).translated(origin)
                    if not area.isEmpty(): ink=area if first else ink.united(area); first=False
                clip=run.boundingRect().translated(shaped.position()) if run.flags() & QGlyphRun.GlyphRunFlag.SplitLigature else None
                if clip is not None: ink=ink.intersected(clip)
                expected=next((s['fontId'] for s in native.model['styles'] if s['styleId']==style_id),None)
                fallback='Explicit system font; geometry is platform-specific.' if expected is None else 'Requested font lacks coverage or Qt substituted a shaping font.' if not face or face.font_id!=expected else None
                story['glyphs'].append(dict(sourceFrameId=story['source'],lineIndex=info['index'],blockId=info['blockId'],sourceUtf16=[block.position()+start,block.position()+end],selectedFontId=expected,fallbackReason=fallback,
                    source=source,glyphId=gid,fontId=face.font_id if face else None,fontFamily=raw.familyName(),missingGlyph=gid==0,origin=[origin.x(),origin.y()],inkBounds=numbers(ink),
                    pixelSize=raw.pixelSize(),rightToLeft=run.isRightToLeft(),features=deepcopy(native.style_features.get(style_id,native.features)),
                    protected=not independent(source,fmt),_paints=paints,_clip=clip,_fmt=fmt))
        # Qt can enumerate fallback-font runs in a different order in another
        # process. Stable source order keeps paint and geometry hashes portable.
        story['glyphs'].sort(key=lambda g:(g['lineIndex'],g['sourceUtf16'],g['origin'],g['fontFamily'],g['glyphId']))

    def place(self,gaps):
        glyphs=[]; lines=[]; warnings=[]
        for fid,story in self.stories.items():
            config=story['config']; placements={}; chain=story['chain']; target=0; y=0
            rules={r['blockId']:r for r in config['paragraphs']} if config else {}
            def position(item,at_y,at_target):
                destination=chain[at_target]; page,frame=self.frames[destination]; area=frame_rect(frame)
                extra=gaps.get((fid,item['index']),0); y0=at_y+extra
                if config:
                    leading=item['height']-item['ascent']-item['descent']; ratio={'before':1,'split':.5,'after':0}[config['leadingDistribution']]
                    baseline=y0+item['ascent']+leading*ratio
                    grid=config['grid']
                    if grid['enabled']:
                        step=grid['step']*SCALE; offset=grid['offset']*SCALE
                        snapped=math.ceil((baseline+area.y()-offset-EPS)/step)*step+offset-area.y()
                        y0+=snapped-baseline; baseline=snapped
                else: baseline=item['nativeBaseline']; y0=baseline-item['ascent']
                output={k:v for k,v in item.items() if not k.startswith('_')}
                output.update(frameId=destination,pageId=page['pageId'],baseline=baseline+area.y(),x=item['nativeX']+area.x(),
                              addedLeading=extra/SCALE,advanceBounds=[item['nativeX']+area.x(),baseline+area.y()-item['ascent'],item['width'],item['ascent']+item['descent']])
                return output,y0+item['height'],max(y0+item['height'],baseline+item['descent'])<=area.height()+EPS
            for para_index,para in enumerate(story['paragraphs']):
                rule=rules.get(para['blockId'],dict(keepWithNext=False,keepTogether=False,widows=1,orphans=1))
                items=para['lines']; remaining=list(items); y+=para['before'] if config else 0
                if config and len(chain)>1 and target<len(chain)-1:
                    required=items if rule['keepTogether'] else items[:rule['orphans']]
                    if rule['keepWithNext'] and para_index+1<len(story['paragraphs']):
                        required=items+story['paragraphs'][para_index+1]['lines'][:1]
                    trial=y
                    for index,item in enumerate(required):
                        if index==len(items): trial+=para['after']+story['paragraphs'][para_index+1]['before']
                        _,trial,fits=position(item,trial,target)
                    if required and not fits: target+=1; y=para['before']
                first_chunk=True
                while remaining:
                    chunk=[]; trial=y
                    for item in remaining:
                        placed,new_y,fits=position(item,trial,target)
                        if config and not fits and target<len(chain)-1: break
                        chunk.append((item,placed,new_y)); trial=new_y
                    if len(chunk)<len(remaining) and config:
                        minimum=rule['orphans'] if first_chunk else 1
                        if len(remaining)-len(chunk)<rule['widows']: chunk=chunk[:max(0,len(remaining)-rule['widows'])]
                        if len(chunk)<minimum or rule['keepTogether']: chunk=[]
                    if not chunk:
                        if target<len(chain)-1: target+=1; y=para['before']; continue
                        # Finite frame chain exhausted: retain the complete text
                        # as overset and explain unsatisfied pagination rules.
                        item=remaining[0]; placed,new_y,_=position(item,y,target); chunk=[(item,placed,new_y)]
                    if config and rule['keepTogether'] and len(chunk)<len(remaining): warnings.append(dict(code='KEEP_TOGETHER_UNSATISFIED',sourceFrameId=fid,blockId=para['blockId']))
                    for item,placed,new_y in chunk:
                        placements[item['index']]=placed; lines.append(placed); y=new_y
                    remaining=remaining[len(chunk):]; first_chunk=False
                    if remaining and target<len(chain)-1: target+=1; y=0
                y+=para['after'] if config else 0
            for original in story['glyphs']:
                item=story['lines'][original['lineIndex']]; placed=placements[original['lineIndex']]
                area=frame_rect(self.frames[placed['frameId']][1]); dx=area.x(); dy=placed['baseline']-item['nativeBaseline']
                glyph=dict(original); glyph.update(frameId=placed['frameId'],pageId=placed['pageId'],origin=[original['origin'][0]+dx,original['origin'][1]+dy])
                ink=box(original['inkBounds']).translated(dx,dy)
                collision=config['collision'] if config else dict(strokeWidth=0,effectPadding=0)
                stroke=collision['strokeWidth']*SCALE/2; effect=collision['effectPadding']*SCALE
                glyph.update(inkBounds=numbers(ink),strokeBounds=numbers(ink.adjusted(-stroke,-stroke,stroke,stroke)),effectBounds=numbers(ink.adjusted(-stroke-effect,-stroke-effect,stroke+effect,stroke+effect)),
                             advanceBounds=placed['advanceBounds'],_clip=original['_clip'].translated(dx,dy) if original['_clip'] is not None else None)
                glyphs.append(glyph)
            # Constraint checks report the actual allocations, including last-frame
            # overflow and rules impossible in the supplied fixed frame chain.
            for para in story['paragraphs']:
                rule=rules.get(para['blockId']); assigned=[placements[l['index']]['frameId'] for l in para['lines']]
                if rule and len(set(assigned))>1:
                    counts=[assigned.count(value) for value in dict.fromkeys(assigned)]
                    if counts[0]<rule['orphans'] or counts[-1]<rule['widows']: warnings.append(dict(code='WIDOW_ORPHAN_UNSATISFIED',sourceFrameId=fid,blockId=para['blockId'],counts=counts))
                if rule and rule['keepWithNext']:
                    index=story['paragraphs'].index(para)
                    if index+1<len(story['paragraphs']) and assigned[-1]!=placements[story['paragraphs'][index+1]['lines'][0]['index']]['frameId']:
                        warnings.append(dict(code='KEEP_WITH_NEXT_UNSATISFIED',sourceFrameId=fid,blockId=para['blockId']))
        return glyphs,lines,warnings

    def clusters(self,glyphs):
        groups={}
        for glyph in glyphs:
            if box(glyph['inkBounds']).isEmpty(): continue
            key=(glyph['sourceFrameId'],glyph['lineIndex'],*glyph['sourceUtf16'])
            config=self.stories[glyph['sourceFrameId']]['config']
            bound=config['collision']['bounds'] if config else 'ink'
            area=box(glyph[bound+'Bounds'])
            if key in groups: groups[key]['bounds']=numbers(box(groups[key]['bounds']).united(area))
            else: groups[key]=dict(sourceFrameId=glyph['sourceFrameId'],frameId=glyph['frameId'],pageId=glyph['pageId'],lineIndex=glyph['lineIndex'],sourceUtf16=glyph['sourceUtf16'],source=glyph['source'],protected=glyph['protected'],bounds=numbers(area))
        return list(groups.values())

    def collisions(self,glyphs):
        if not any(story['config'] for story in self.stories.values()): return [],True
        found=[]; comparisons=0; clusters=self.clusters(glyphs)
        for page_id in dict.fromkeys(c['pageId'] for c in clusters):
            active=[]
            for right in sorted((c for c in clusters if c['pageId']==page_id),key=lambda c:(c['bounds'][0],c['bounds'][1],c['sourceFrameId'],c['sourceUtf16'])):
                rc=box(right['bounds']); active=[left for left in active if box(left['bounds']).right()+100*SCALE>=rc.left()]
                for left in active:
                    comparisons+=1
                    if comparisons>MAX_COMPARISONS: return found,False
                    configs=[self.stories[c['sourceFrameId']]['config'] for c in (left,right)]
                    if not any(configs): continue
                    clearance=max(c['collision']['clearance']*SCALE for c in configs if c)
                    lc=box(left['bounds']); xgap=max(lc.left(),rc.left())-min(lc.right(),rc.right()); ygap=max(lc.top(),rc.top())-min(lc.bottom(),rc.bottom())
                    if xgap>=clearance-EPS or ygap>=clearance-EPS: continue
                    same_line=left['sourceFrameId']==right['sourceFrameId'] and left['lineIndex']==right['lineIndex']
                    protected=same_line and (left['protected'] or right['protected']) and (left['sourceUtf16'][1]==right['sourceUtf16'][0] or right['sourceUtf16'][1]==left['sourceUtf16'][0])
                    direction='horizontal' if same_line else 'vertical' if left['sourceFrameId']==right['sourceFrameId'] and left['frameId']==right['frameId'] else 'cross-frame'
                    found.append(dict(direction=direction,left=left,right=right,clearancePoints=clearance/SCALE,protected=protected,
                                      reason='PROTECTED_JOIN_OR_MARK' if protected else 'BOUNDS_CLEARANCE',severity='info' if all(c is None or c['collision']['mode']=='allow' for c in configs) or protected else 'warning',
                                      overlapPoints=[max(0,clearance-xgap)/SCALE,max(0,clearance-ygap)/SCALE]))
                    if len(found)>=10000: return found,False
                active.append(right)
        return found,True

    def overflowing(self,glyphs,lines,fid):
        for glyph in glyphs:
            if glyph['sourceFrameId']==fid and not box(glyph['inkBounds']).isEmpty() and not frame_rect(self.frames[glyph['frameId']][1]).adjusted(-EPS,-EPS,EPS,EPS).contains(box(glyph['inkBounds'])): return True
        return any(line['sourceFrameId']==fid and box(line['advanceBounds']).bottom()>frame_rect(self.frames[line['frameId']][1]).bottom()+EPS for line in lines)

    def solve(self):
        gaps={}; blocked=set(); used={fid:0 for fid in self.stories}; rounds={fid:0 for fid in self.stories}
        self.placement_warnings=deepcopy(self.base_warnings)
        for iteration in range(16):
            collisions,complete=self.collisions(self.final)
            if not complete: self.solver.append(dict(code='ANALYSIS_LIMIT',iteration=iteration)); break
            requests={}
            for collision in collisions:
                if collision['protected']: continue
                left,right=collision['left'],collision['right']; fid=left['sourceFrameId']; config=self.stories[fid]['config']
                if not config or config['collision']['mode']!='repair': continue
                if collision['direction']!='vertical': continue
                first,last=sorted((left,right),key=lambda c:c['lineIndex'])
                key=(fid,last['lineIndex'])
                if key in blocked: continue
                delta=(box(first['bounds']).bottom()+collision['clearancePoints']*SCALE-box(last['bounds']).top())
                requests[key]=max(requests.get(key,0),delta)
            if not requests: break
            progress=False
            for key,delta in sorted(requests.items()):
                fid,_=key; config=self.stories[fid]['config']; policy=config['collision']; grid=config['grid']
                if rounds[fid]>=policy['iterations']: blocked.add(key); self.solver.append(dict(code='ITERATION_LIMIT',sourceFrameId=fid)); continue
                if grid['enabled']: delta=math.ceil((delta-EPS)/(grid['step']*SCALE))*grid['step']*SCALE
                delta=max(delta,1/64)
                if used[fid]+delta>policy['maximumExpansion']*SCALE+EPS:
                    blocked.add(key); self.solver.append(dict(code='EXPANSION_LIMIT',sourceFrameId=fid,lineIndex=key[1],requestedPoints=delta/SCALE)); continue
                trial=dict(gaps); trial[key]=trial.get(key,0)+delta
                glyphs,lines,warnings=self.place(trial)
                if policy['fixedFrame'] and self.overflowing(glyphs,lines,fid):
                    blocked.add(key); self.solver.append(dict(code='FIXED_FRAME_CONSTRAINT',sourceFrameId=fid,lineIndex=key[1],requestedPoints=delta/SCALE)); continue
                gaps=trial; used[fid]+=delta; self.final,self.lines,self.placement_warnings=glyphs,lines,warnings; progress=True
                self.solver.append(dict(code='LEADING_ADDED',sourceFrameId=fid,lineIndex=key[1],points=delta/SCALE,iteration=iteration+1))
            for fid in {key[0] for key in requests}: rounds[fid]+=1
            if not progress: break
        self.expansion={fid:value/SCALE for fid,value in used.items()}

    @staticmethod
    def public_glyph(glyph): return {k:v for k,v in glyph.items() if not k.startswith('_')}

    def report(self,page_id,max_glyphs=5000):
        page=next(p for p in self.book.state['pages'] if p['pageId']==page_id)
        glyphs=[self.public_glyph(g) for g in self.final if g['pageId']==page_id]
        lines=[line for line in self.lines if line['pageId']==page_id]
        diagnostics=list(self.placement_warnings); records=[]
        if not self.complete: diagnostics.append(dict(code='COLLISION_ANALYSIS_LIMIT',message='Analysis is incomplete; no guarantee of clearance.'))
        for glyph in glyphs:
            if glyph['missingGlyph']: diagnostics.append(dict(code='MISSING_GLYPH',sourceFrameId=glyph['sourceFrameId'],sourceUtf16=glyph['sourceUtf16']))
        for frame in page['frames']:
            fid=frame['frameId']; area=frame_rect(frame)
            own=[g for g in glyphs if g['frameId']==fid]; own_lines=[l for l in lines if l['frameId']==fid]
            overflow=any(not box(g['inkBounds']).isEmpty() and not area.adjusted(-EPS,-EPS,EPS,EPS).contains(box(g['inkBounds'])) for g in own) or any(box(l['advanceBounds']).bottom()>area.bottom()+EPS for l in own_lines)
            if overflow: diagnostics.append(dict(code='FRAME_OVERFLOW',frameId=fid,policy=frame['overflow'],message='All source text is retained.'))
            records.append(dict(frameId=fid,name=frame['name'],rect=numbers(area),overflow=overflow,layout=dict(glyphs=own[:max_glyphs],lines=own_lines)))
        before=[self.public_glyph(g) for g in self.base if g['pageId']==page_id]
        geometry=dict(page=[page['width'],page['height']],glyphs=glyphs,lines=lines)
        return dict(revision=self.book.revision,pageId=page_id,pagePoints=[int(page['width'])/1e6,int(page['height'])/1e6],units='logical-pixels-at-96-dpi',
                    geometryHash=hash_value(geometry),beforeGeometryHash=hash_value(dict(page=geometry['page'],glyphs=before,lines=[l for l in self.base_lines if l['pageId']==page_id])),
                    frames=records,glyphs=glyphs[:max_glyphs],lines=lines,diagnostics=diagnostics,truncated=len(glyphs)>max_glyphs,
                    engine=self.book.fingerprint(),collisionReport=self.collision_report(page_id),baselineDifferences=[dict(sourceFrameId=a['sourceFrameId'],sourceUtf16=a['sourceUtf16'],before=a['baseline'],after=b['baseline'],beforeFrameId=a['frameId'],afterFrameId=b['frameId']) for a,b in zip(self.base_lines,self.lines) if a!=b],
                    opticalAdjustments=self.optical,elapsedMs=self.elapsed_ms)

    def collision_report(self,page_id=None):
        selected=[c for c in self.final_collisions if page_id is None or c['left']['pageId']==page_id]
        unresolved=[c for c in selected if not c['protected']]
        reasons={s['code'] for s in self.solver if s['code']!='LEADING_ADDED'}
        for collision in unresolved:
            if collision['direction']=='horizontal': reasons.add('HORIZONTAL_REQUIRES_EXPLICIT_OPTICAL_RULE')
            elif collision['direction']=='cross-frame': reasons.add('CROSS_FRAME_REQUIRES_MANUAL_LAYOUT')
            else:
                config=self.stories[collision['left']['sourceFrameId']]['config']
                mode=config['collision']['mode'] if config else 'warn'
                reasons.add({'allow':'POLICY_ALLOWS_COLLISION','warn':'POLICY_WARN_ONLY','repair':'VERTICAL_CLEARANCE_UNSATISFIED'}[mode])
        return dict(complete=self.complete,method='conservative axis-aligned bounds; joined clusters are protected',
                    boundsMeaning=dict(advance='line advance box',ink='union of enabled glyph-layer ink',stroke='ink plus half the reserved stroke width',effect='stroke plus reserved effect padding',reservedEffectsArePainted=False),
                    beforeCount=sum(not c['protected'] for c in self.base_collisions if page_id is None or c['left']['pageId']==page_id),afterCount=len(unresolved),protectedCount=sum(c['protected'] for c in selected),
                    collisions=selected,solver=self.solver,expansionPoints=self.expansion,
                    unresolvedReasons=sorted(reasons))

    def paint(self,painter,page_id,mode=None,clip=None,overlays=None,guides=False,outlines=False):
        page=next(p for p in self.book.state['pages'] if p['pageId']==page_id)
        boundary=QRectF(0,0,int(page['width'])/1e6*SCALE,int(page['height'])/1e6*SCALE)
        visible=boundary if clip is None else boundary.intersected(clip)
        background=self.book.state.get('paint',{}).get('background','#FFFFFFFF')
        painter.save(); painter.setClipRect(visible); painter.fillRect(boundary,QColor(background)); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        underlay=getattr(self,'paint_underlay',None)
        separated=underlay(painter,page_id,visible,outlines) if underlay else False
        for glyph in self.final:
            if glyph['pageId']!=page_id: continue
            frame=self.frames[glyph['frameId']][1]; area=frame_rect(frame)
            glyph_clip=visible.intersected(area) if frame['overflow']=='clip' else visible
            if glyph['_clip'] is not None: glyph_clip=glyph_clip.intersected(glyph['_clip'])
            visible_origin=bool(overlays and overlays.get('origins') and glyph_clip.contains(QPointF(*glyph['origin'])))
            if not box(glyph['effectBounds']).intersects(glyph_clip) and not visible_origin: continue
            painter.save(); painter.setClipRect(glyph_clip)
            try:
                painted=False
                if self.mode=='color' and 'paint' in self.book.state:
                    if outlines and self.book.paint_renderer.binding(glyph['fontId']):
                        raise ValueError('PAINT_REQUIRES_RASTER_FALLBACK: use publication.svg with explicit raster policy and DPI')
                    painted=self.book.paint_renderer.paint(painter,glyph,component='surface' if separated else 'composite')
                for raw,gid,color in ([] if painted else glyph['_paints']):
                    origin=QPointF(*glyph['origin'])
                    if outlines:
                        path=raw.pathForGlyph(gid)
                        if path.isEmpty() and not raw.boundingRect(gid).isEmpty(): raise ValueError('VECTOR_GLYPH_HAS_NO_OUTLINE')
                        cutter=QPainterPath(); cutter.addRect(glyph_clip)
                        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor(color)); painter.drawPath(path.translated(origin).intersected(cutter))
                    else:
                        run=QGlyphRun(); run.setRawFont(raw); run.setGlyphIndexes([gid]); run.setPositions([origin])
                        painter.setPen(QColor(color)); painter.drawGlyphRun(QPointF(0,0),run)
                if overlays and overlays.get('bounds'):
                    painter.setBrush(Qt.BrushStyle.NoBrush); painter.setPen(QPen(QColor('#bc7024'),0)); painter.drawRect(box(glyph['effectBounds']))
                if overlays and overlays.get('origins'):
                    painter.setPen(QPen(QColor('#6c4db6'),0)); origin=QPointF(*glyph['origin']); painter.drawEllipse(origin,2,2)
            finally: painter.restore()
        if overlays and overlays.get('baselines'):
            painter.setPen(QPen(QColor('#43999c'),0,Qt.PenStyle.DashLine))
            for line in self.lines:
                if line['pageId']==page_id: painter.drawLine(QPointF(line['x'],line['baseline']),QPointF(line['x']+line['width'],line['baseline']))
        if guides:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for frame in page['frames']:
                area=frame_rect(frame); painter.setPen(QPen(QColor('#3d7499'),0,Qt.PenStyle.DashLine)); painter.drawRect(area)
                source=self.book.source_for(frame['frameId']); config=self.spec['frames'].get(source)
                if config and config['enabled'] and config['grid']['enabled']:
                    step=config['grid']['step']*SCALE; offset=config['grid']['offset']*SCALE
                    painter.setPen(QPen(QColor('#ccdce8'),0,Qt.PenStyle.DotLine))
                    start=max(area.top(),visible.top()); end=min(area.bottom(),visible.bottom())
                    for index in range(math.ceil((start-offset)/step),min(math.floor((end-offset)/step)+1,math.ceil((start-offset)/step)+2000)):
                        y=index*step+offset; painter.drawLine(QPointF(area.left(),y),QPointF(area.right(),y))
            painter.setPen(QPen(QColor('#ce3f54'),1)); painter.setBrush(Qt.BrushStyle.NoBrush)
            for collision in self.final_collisions:
                if collision['left']['pageId']==page_id and not collision['protected'] and collision['severity']=='warning':
                    painter.drawRect(box(collision['left']['bounds']).united(box(collision['right']['bounds'])))
        painter.restore()

    def hit_test(self,page_id,x,y):
        candidates=[line for line in self.lines if line['pageId']==page_id and frame_rect(self.frames[line['frameId']][1]).contains(QPointF(x,y))]
        if not candidates: return dict(frameId=None,pageId=page_id,offset=None,revision=self.book.revision)
        chosen=min(candidates,key=lambda l:abs(y-l['baseline'])+max(0,l['x']-x,x-l['x']-l['width']))
        native=self.stories[chosen['sourceFrameId']]['lines'][chosen['index']]
        offset=native['_line'].xToCursor(x-chosen['x'])+self.stories[chosen['sourceFrameId']]['native'].doc.findBlock(chosen['sourceUtf16'][0]).position()
        return dict(frameId=chosen['sourceFrameId'],targetFrameId=chosen['frameId'],pageId=page_id,offset=offset,revision=self.book.revision)
