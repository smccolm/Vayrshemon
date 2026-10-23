"""M3 API: explicit layout policy, diagnostics and optical research tools."""
from copy import deepcopy
from PySide6.QtCore import QTextBoundaryFinder
from .api import obj,BOOL,STRING,RANGE
from .editor_api import EditorAPI,METHODS as M2_METHODS
from .typesetting_contracts import ID,FRAME_SETTINGS,GRID,COLLISION,OPTICAL,PROFILE,PARAGRAPH_RULE,settings
from .session import utf16_length,scalar_offset


METHODS=deepcopy(M2_METHODS)
METHODS.update({
 'typesetting.read':('Read persisted frame policy, flow chains and versioned line-break profiles.',False,obj()),
 'typesetting.configure':('Enable derived layout, leading distribution and baseline grid for the source frame.',True,obj(dict(frame_id=ID,enabled=BOOL,leadingDistribution=FRAME_SETTINGS['properties']['leadingDistribution'],grid=obj(GRID['properties'])))),
 'paragraph.rules':('Apply keep-with-next, keep-together and widow/orphan minima to selected paragraphs.',True,obj(dict(**RANGE,**{k:v for k,v in PARAGRAPH_RULE['properties'].items() if k!='blockId'}),('start','end'))),
 'flow.set':('Flow one source story through empty equal-width frames; never duplicate or delete source text.',True,obj(dict(source_frame_id=ID,targets={'type':'array','items':ID,'uniqueItems':True,'maxItems':127}),('source_frame_id','targets'))),
 'breaks.profile':('Create a new revision of explicit language line-break tailoring; no automatic hyphenation dictionary.',True,PROFILE),
 'breaks.inspect':('Inspect native and tailored Unicode break opportunities with source offsets.',False,obj()),
 'breaks.insert':('Explicitly insert a soft hyphen or line separator at a grapheme boundary.',True,obj(dict(offset={'type':'integer','minimum':0},kind={'enum':['soft-hyphen','line-separator','zero-width-space']}),('offset','kind'))),
 'collision.configure':('Set allow/warn/repair, minimum clearance, expansion/iteration budget and reserved bounds.',True,obj(dict(frame_id=ID,**COLLISION['properties']))),
 'collision.inspect':('Report before/after collisions, protected joins, solver decisions and unresolved constraints.',False,obj(dict(page_id=ID))),
 'optical.set':('Replace explicit pair spacing rules, stored separately from font kerning. Legacy independence must be declared.',True,obj(dict(frame_id=ID,rules={'type':'array','items':OPTICAL,'maxItems':256}),('rules',))),
 'pairs.inspect':('Measure an isolated pair with/without font kerning and explicit optical spacing; live source is unchanged.',False,obj(dict(text={'type':'string','minLength':1,'maxLength':32},font_id={'type':['string','null']},language=STRING,size={'type':'number','minimum':1,'maximum':300},delta={'type':'number','minimum':-20,'maximum':20}),('text',))),
 'specimen.create':('Create an editable dense specimen on a new page from explicit source symbols.',True,obj(dict(symbols={'type':'string','minLength':1,'maxLength':256},font_id={'type':['string','null']},language=STRING,size={'type':'number','minimum':1,'maximum':300}),('symbols',))),
})


class TypesettingAPI(EditorAPI):
    version='0.4.0'
    methods=METHODS

    def dispatch(self,method,params):
        s=self.session
        if method=='typesetting.read': return deepcopy(s.state['typesetting'])
        if method=='collision.inspect': return s.composition().collision_report(params.get('page_id'))
        if method=='breaks.inspect':
            from .typesetting import break_opportunities
            from .session import LANGUAGE
            profiles={p['languageId']:p for p in s.state['typesetting']['profiles']}; blocks=[]
            block=s.active.doc.begin()
            while block.isValid():
                def language_at(offset):
                    iterator=block.begin(); position=block.position()+offset
                    while not iterator.atEnd():
                        fragment=iterator.fragment()
                        if fragment.isValid() and fragment.position()<=position<fragment.position()+fragment.length():
                            return fragment.charFormat().property(LANGUAGE) or 'language.en'
                        iterator+=1
                    return 'language.en'
                positions,reasons=break_opportunities(block.text(),profiles,language_at)
                blocks.append(dict(start=block.position(),opportunities=[dict(offset=block.position()+p,**reasons[p]) for p in positions if p in reasons]))
                block=block.next()
            return dict(engine='QTextBoundaryFinder / Qt 6.8.3',blocks=blocks,hyphenation=dict(provider='manual-only',automatic=False,futureProviderContract='Return source UTF-16 grapheme boundaries; never mutate source text.'))
        if method=='pairs.inspect': return self.pair_probe(**params)
        protected_methods={'document.edit','document.format','paragraph.format','paragraph.rules','styles.apply','clipboard.paste','breaks.insert','features.configure'}
        if method in protected_methods and s.source_for(s.state['activeFrameId'])!=s.state['activeFrameId']:
            raise ValueError('FLOW_TARGET_READ_ONLY: select the source frame to edit its story')
        if method=='selection.set' and params.get('frame_id'):
            params=dict(params); params['frame_id']=s.source_for(params['frame_id'])
        result=super().dispatch(method,params)
        if method=='session.status': result['typesettingVersion']='0.1.0'; result['sourceFrameId']=s.source_for(s.state['activeFrameId'])
        return result

    def mutate(self,method,params):
        s=self.session
        if method=='typesetting.configure': return s.configure_typesetting(**params)
        if method=='collision.configure':
            values=dict(params); fid=values.pop('frame_id',None)
            return s.configure_typesetting(fid,collision=values)
        if method=='flow.set': return s.set_flow(**params)
        if method=='breaks.profile':
            profiles=s.state['typesetting']['profiles']; old=next((p for p in profiles if p['languageId']==params['languageId']),None)
            if old and params['revision']<=old['revision']: raise ValueError('PROFILE_REVISION_MUST_INCREASE')
            s.state['typesetting']['profiles']=[p for p in profiles if p['languageId']!=params['languageId']]+[deepcopy(params)]
            s.configure_typesetting(enabled=True)
            return dict(profile=deepcopy(params))
        if method=='optical.set':
            return s.configure_typesetting(params.get('frame_id'),optical=params['rules'])
        if method=='breaks.insert':
            return s.active.edit(params['offset'],params['offset'],{'soft-hyphen':'\u00ad','line-separator':'\u2028','zero-width-space':'\u200b'}[params['kind']])
        if method=='paragraph.rules':
            from .session import BLOCK
            values=dict(params); start=values.pop('start'); end=values.pop('end'); s.active.range_cursor(start,end)
            fid=s.state['activeFrameId']; config=s.state['typesetting']['frames'].setdefault(fid,settings()); rules=config['paragraphs']; block=s.active.doc.findBlock(start)
            while block.isValid() and (block.position()<end or block.position()<=start<block.position()+block.length()):
                bid=getattr(block.userData(),'identity',None) or block.blockFormat().property(BLOCK) or f'block.qt.{block.position()}'
                rule=next((r for r in rules if r['blockId']==bid),None)
                if rule is None: rule=dict(blockId=bid,keepWithNext=False,keepTogether=False,widows=2,orphans=2); rules.append(rule)
                rule.update(values)
                if start==end: break
                block=block.next()
            s.invalidate_composition(); return dict(rules=deepcopy(rules))
        if method=='specimen.create':
            symbols=params['symbols']; from .typesetting import boundaries,slice16
            offsets=boundaries(symbols); units=[slice16(symbols,a,b) for a,b in zip(offsets,offsets[1:])]
            units=[u for u in units if not u.isspace()]
            if not units or len(units)>64: raise ValueError('SPECIMEN_LIMIT: 1..64 graphemes')
            text=' '.join(units)+'\n'+''.join(units)+'\n'+' '.join(a+b for a,b in zip(units,units[1:]))
            page=s.add_page(); s.active.edit(0,0,text)
            s.active.format_range(0,utf16_length(text),font_id=params.get('font_id'),language=params.get('language','language.en'),size=params.get('size',36))
            s.configure_typesetting(enabled=True)
            return dict(**page,sourceText=text)
        return super().mutate(method,params)

    def pair_probe(self,text,font_id=None,language='language.en',size=36,delta=0):
        from .frame import FrameSession
        from .authoring import blank_content
        from .typesetting import boundaries
        from . import layout
        offsets=boundaries(text)
        if len(offsets)!=3: raise ValueError('PAIR_REQUIRES_TWO_GRAPHEMES')
        s=self.session; temporary=FrameSession(s.root,s.fonts,blank_content(s.state['documentId'],'1000000000','300000000'),s.checks)
        try:
            temporary.edit(0,0,text); variants={}
            for name,kern,spacing in [('kernOff',False,0),('kernOn',True,0),('optical',True,delta)]:
                temporary.features['kern']=kern
                temporary.format_range(0,utf16_length(text),font_id=font_id,language=language,size=size,tracking=0)
                if spacing: temporary.format_range(0,offsets[1],tracking=spacing)
                report=layout.inspect(temporary)
                variants[name]=dict(width=report['lines'][0]['width']/ (96/72),glyphs=report['glyphs'],geometryHash=report['geometryHash'])
            return dict(text=text,units='points',variants=variants,fontKerningDelta=variants['kernOn']['width']-variants['kernOff']['width'],opticalDelta=variants['optical']['width']-variants['kernOn']['width'],sourceUnchanged=True)
        finally: temporary.deleteLater()
