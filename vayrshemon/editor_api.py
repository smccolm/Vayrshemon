"""Authoring API 0.3: UI, CLI and MCP share the document writer."""
from copy import deepcopy
from .api import API,METHODS as LAB_METHODS,obj,STRING,NUMBER,BOOL,RANGE
from .editor_contracts import FORMAT_FIELDS,PARAGRAPH,STYLE,ID
from . import pages

METHODS=deepcopy(LAB_METHODS)
METHODS.pop('reference.load')
METHODS.update({
 'document.new':('Create a new document; explicit discard is required for unsaved text.',True,obj(dict(title={'type':'string','maxLength':200},width=NUMBER,height=NUMBER,discardUnsaved=BOOL))),
 'document.title':('Rename the document.',True,obj(dict(title={'type':'string','maxLength':200}),('title',))),
 'document.read':('Read every page/frame and the selected frame text; offsets belong to the selected frame.',False,obj()),
 'document.open':('Open or migrate a document; fontPaths resolves exact hashes at new paths.',True,obj(dict(path=STRING,discardUnsaved=BOOL,fontPaths={'type':'object','additionalProperties':STRING}),('path',))),
 'document.preflight':('Validate a file and list exact missing font identities without changing the document.',False,obj(dict(path=STRING),('path',))),
 'document.save-as':('Save at a new path, retaining the previous document and its recovery history.',True,obj(dict(path=STRING),('path',))),
 'document.recent':('List recent local document paths.',False,obj()),
 'document.format':('Format a UTF-16 range, retaining explicit font/language and custom spacing.',True,obj(dict(**RANGE,**FORMAT_FIELDS),('start','end'))),
 'document.find':('Find literal text on grapheme boundaries across all frames.',False,obj(dict(text={'type':'string','minLength':1},case_sensitive=BOOL,whole_word=BOOL,all_frames=BOOL),('text',))),
 'document.replace':('Replace all literal matches as one undoable transaction.',True,obj(dict(text={'type':'string','minLength':1},replacement=STRING,case_sensitive=BOOL,whole_word=BOOL,all_frames=BOOL),('text','replacement'))),
 'paragraph.format':('Set line height, paragraph spacing, alignment and left tab stops.',True,obj(dict(**RANGE,**PARAGRAPH['properties'],lineHeight=obj(dict(mode={'enum':['multiple','exact','at-least']},value={'type':'number','exclusiveMinimum':0,'maximum':100}),('mode','value'))),('start','end'))),
 'page.add':('Add an independent page with a full content frame.',True,obj(dict(width=NUMBER,height=NUMBER))),
 'page.delete':('Remove a page and its frames; undo restores all content.',True,obj(dict(page_id=ID),('page_id',))),
 'page.configure':('Set dimensions and margins for one page. Full content frames follow its content area.',True,obj(dict(width=NUMBER,height=NUMBER,unit={'enum':['pt','mm','in']},page_id=ID,margins=obj({k:{'type':'number','minimum':0} for k in ('top','right','bottom','left')},('top','right','bottom','left'))))),
 'frame.add':('Add an independent text frame to the selected page; coordinates use points.',True,obj(dict(x=NUMBER,y=NUMBER,width=NUMBER,height=NUMBER,name={'type':'string','maxLength':100}))),
 'frame.select':('Select the editing frame and invalidate commands prepared for a previous frame.',True,obj(dict(frame_id=ID),('frame_id',))),
 'frame.configure':('Set frame position, dimensions, label and visible/clipped overflow.',True,obj(dict(frame_id=ID,x=NUMBER,y=NUMBER,width=NUMBER,height=NUMBER,name={'type':'string','maxLength':100},overflow={'enum':['show','clip']}))),
 'frame.delete':('Remove a text frame; undo restores its full semantic text.',True,obj(dict(frame_id=ID),('frame_id',))),
 'selection.set':('Select a grapheme-aligned UTF-16 range, optionally in another frame.',True,obj(dict(**RANGE,frame_id=ID),('start','end'))),
 'styles.list':('List named character styles.',False,obj()),
 'styles.define':('Create or replace a named character style.',True,STYLE),
 'styles.apply':('Apply a named character style to the selected frame range.',True,obj(dict(**RANGE,name=STRING),('start','end','name'))),
 'recipe.configure':('Validate and select three compatible fonts for registered flat color.',True,obj(dict(master=ID,layers={'type':'array','items':ID,'minItems':3,'maxItems':3}),('master','layers'))),
 'palette.apply':('Apply an explicit three-color palette to the current recipe.',True,obj(dict(colors={'type':'array','items':{'type':'string','pattern':'^#[0-9a-fA-F]{6}$'},'minItems':3,'maxItems':3}),('colors',))),
 'clipboard.read':('Return plain source text and semantic clipboard data for a selection.',False,obj(RANGE,('start','end'))),
 'clipboard.paste':('Paste validated semantic clipboard data without discarding run metadata.',True,obj(dict(**RANGE,fragment={'type':'object'}),('start','end','fragment'))),
 'recovery.list':('List recoverable checkpoints from sessions that are no longer running.',False,obj()),
 'recovery.restore':('Recover an interrupted session without overwriting its source document.',True,obj(dict(path=STRING,discardUnsaved=BOOL,fontPaths={'type':'object','additionalProperties':STRING}),('path',))),
 'history.list':('List revision summaries, undo capacity and the last durable revision.',False,obj()),
 'layout.inspect':('Inspect the page and all its frame glyphs, including overflow.',False,obj(dict(page_id=ID,max_glyphs={'type':'integer','minimum':1,'maximum':100000}))),
 'layout.hit-test':('Map page coordinates to frame identity and native UTF-16 caret.',False,obj(dict(x=NUMBER,y=NUMBER,page_id=ID),('x','y'))),
 'render.svg':('Export a portable outline SVG proof; bitmap-only glyphs fail explicitly.',True,obj(dict(path=STRING,page_id=ID,mode={'enum':['mono','color']}),('path',))),
})
METHODS['render.png'][2]['properties']['page_id']=ID
METHODS['history.undo']=('Undo a document, page, frame, text or formatting transaction.',True,obj())
METHODS['history.redo']=('Redo an undone document transaction.',True,obj())


class EditorAPI(API):
    version='0.3.0'
    methods=METHODS

    def dispatch(self,method,params):
        s=self.session
        if method=='session.status':
            return dict(sessionId=s.session_id,documentId=s.state['documentId'],revision=s.revision,dirty=s.dirty,
                        activeFrameId=s.state['activeFrameId'],activePageId=s.current_page()['pageId'],composing=s.composing,
                        savedPath=str(s.saved_path) if s.saved_path else None,durableRevision=s.durable_revision,recoveryError=s.recovery_error,
                        recoveryPath=str(s.recovery_path),logPath=str(s.log.path),engine=s.fingerprint(),capabilities=list(self.methods),selection=self.selection())
        if method in ('document.new','document.open','recovery.restore'):
            values=dict(params)
            if s.dirty and s.revision>0 and not values.pop('discardUnsaved',False): raise ValueError('UNSAVED_CHANGES: save or explicitly discard')
            values.pop('discardUnsaved',None)
            if method=='document.new': return s.new(**values)
            if method=='document.open': return s.open(values['path'],font_paths=values.get('fontPaths'))
            return s.recover(values['path'],font_paths=values.get('fontPaths'))
        if method in ('document.save','document.save-as'): return s.save(params['path'])
        if method=='document.preflight': return s.preflight(params['path'])
        if method=='document.recent': return dict(files=s.recent())
        if method=='document.read': return dict(document=s.capture(),text=s.text(),activeFrameId=s.state['activeFrameId'],offsetUnit='utf16-code-unit')
        if method=='document.find': return s.find(**params)
        if method=='recovery.list': return dict(candidates=s.recovery_list())
        if method=='history.list': return dict(revisions=s.history,undoAvailable=bool(s._undo),redoAvailable=bool(s._redo),undoLimit=80,durableRevision=s.durable_revision)
        if method in ('history.undo','history.redo'): return s.history_move(method.endswith('redo'))
        if method=='styles.list': return dict(styles=s.state['styles'])
        if method=='layout.inspect': return pages.inspect(s,**params)
        if method=='layout.hit-test': return pages.hit_test(s,**params)
        if method=='render.png': return pages.render(s,**params)[1]
        if method=='render.svg': return pages.export_svg(s,**params)
        if method=='clipboard.read': return s.copy_fragment(**params)
        if method=='frame.select':
            result=s.select_frame(params['frame_id'])
            s.revision+=1; s._state=s.capture(); s.checkpoint(); s.changed.emit()
            return result
        if method=='selection.set':
            if not s.editor: raise ValueError('SELECTION_REQUIRES_DESKTOP')
            values=dict(params)
            frame_id=values.pop('frame_id',None)
            if frame_id and frame_id!=s.state['activeFrameId']:
                s.locate(frame_id)
                s.frames[frame_id].range_cursor(values['start'],values['end'])
                self.dispatch('frame.select',dict(frame_id=frame_id))
            return super().dispatch(method,values)
        if not self.methods[method][1]: return super().dispatch(method,params)
        with s.command(method):
            result=self.mutate(method,params)
        if isinstance(result,dict) and 'revision' in result: result['revision']=s.revision
        return result

    def mutate(self,method,params):
        s=self.session
        if method=='fonts.load':
            result=super().dispatch(method,params)
            face=s.fonts.resolve(result['fontId'])
            if face.font_id not in {source['fontId'] for source in s.state['fontSources']}:
                s.state['fontSources'].append(dict(fontId=face.font_id,sha256=face.sha256,path=str(face.path)))
            return result
        if method=='document.title': s.state['title']=params['title']; return dict(title=s.state['title'])
        if method=='document.replace': return s.replace(**params)
        if method=='paragraph.format': return s.active.paragraph_format(**params)
        if method=='page.add': return s.add_page(**params)
        if method=='page.delete': return s.delete_page(**params)
        if method=='page.configure': return s.configure_page(**params)
        if method=='frame.add': return s.add_frame(**params)
        if method=='frame.configure': return s.configure_frame(**params)
        if method=='frame.delete': return s.delete_frame(**params)
        if method=='clipboard.paste': return s.paste_fragment(**params)
        if method=='styles.define':
            if params['format'].get('font_id'): s.fonts.resolve(params['format']['font_id'])
            s.state['styles']=[style for style in s.state['styles'] if style['name'].casefold()!=params['name'].casefold()]+[deepcopy(params)]
            return dict(name=params['name'])
        if method=='styles.apply':
            style=next((v for v in s.state['styles'] if v['name']==params['name']),None)
            if style is None: raise ValueError('STYLE_NOT_FOUND')
            return s.active.format_range(params['start'],params['end'],**style['format'])
        if method=='recipe.configure':
            s.fonts.set_recipe(s.fonts.resolve(params['master']),[s.fonts.resolve(fid) for fid in params['layers']])
            return dict(recipe=s.fonts.recipe)
        if method=='palette.apply':
            if not s.fonts.recipe: raise ValueError('NO_LAYER_RECIPE')
            for layer,color in zip(s.fonts.recipe['layers'],params['colors']): layer['color']=color
            return dict(recipe=s.fonts.recipe)
        if method=='features.configure':
            before=[(p,p+n,s.active.attributes(fmt)) for p,n,_,fmt in s.spans()]
            s.active.features.update(params)
            result=super().dispatch(method,params)
            for start,end,attributes in before: s.active.put_attributes(s.range_cursor(start,end,grapheme=False),attributes)
            return result
        return super().dispatch(method,params)

    def selection(self):
        value=super().selection()
        if value: value['frameId']=self.session.state['activeFrameId']
        return value
