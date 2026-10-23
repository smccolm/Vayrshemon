"""M5 desktop, Python, CLI and MCP controls share one guarded writer."""
from copy import deepcopy
import json
from .api import obj, BOOL, STRING
from .studio_api import StudioAPI, METHODS as M4_METHODS
from .language_contracts import COLLECTIONS, RECORDS, ID, INT, TEXT
from .authoring import identity
from . import language as lang, pages, publication

COLLECTION = {'enum':list(COLLECTIONS)}
LIMIT = {'type':'integer','minimum':1,'maximum':2000}
ANCHOR_ARGS = obj(dict(frame_id=ID,start=INT,end=INT),('frame_id','start','end'))
METHODS = deepcopy(M4_METHODS)
METHODS['ui.workspace'][2]['properties']['panel']['enum'] += ['Language','Lexicon','Grammar','Corpus','Symbols','Numbers']
METHODS.update({
 'language.read':('Read a language revision, collection or record with immutable identities and provenance.',False,obj(dict(revision_id=ID,collection=COLLECTION,record_id=ID))),
 'language.revisions':('List language revisions pinned in this document, including hashes and collection counts.',False,obj()),
 'language.diff':('Inspect added, removed and changed records before adopting another revision. Page text never changes.',False,obj(dict(before=ID,after=ID),('before','after'))),
 'language.adopt':('Pin a previously retained language revision; existing corpus links retain their original revision.',True,obj(dict(revision_id=ID),('revision_id',))),
 'language.record.put':('Create or replace one typed record as a new immutable language revision. Stable IDs survive edits.',True,obj(dict(collection=COLLECTION,record={'type':'object'},label=TEXT),('collection','record'))),
 'language.record.delete':('Remove a record in a new revision; referenced records cannot be removed. Undo restores the prior pin.',True,obj(dict(collection=COLLECTION,record_id=ID),('collection','record_id'))),
 'language.archive.import':('Verify and import both local translation charts, language terms, glosses, tense conflict, orthography and Unta data into a new revision.',True,obj()),
 'language.import':('Import a hash-checked portable language package as a new revision; retain the previous revision.',True,obj(dict(path=STRING),('path',))),
 'language.export':('Export the selected revision as portable, hash-checked JSON with original citations. Does not include document text or fonts.',True,obj(dict(path=STRING),('path',))),
 'language.publish':('Publish a searchable, printable dictionary, grammar book or interlinear corpus from the pinned data.',True,obj(dict(path=STRING,kind={'enum':['dictionary','grammar','corpus']}),('path','kind'))),
 'lexicon.search':('Search headwords, senses, labels and variants literally; no normalization of historical spellings.',False,obj(dict(query=TEXT,limit=LIMIT))),
 'orthography.transliterate':('Apply an explicit transliteration profile. Forward trace preserves unknown slots and ambiguous reverse readings.',False,obj(dict(profile_id=ID,text=TEXT,reverse=BOOL,trace={'type':'object'}),('profile_id','text'))),
 'orthography.input':('Insert a registered symbol key through the guarded native text writer; requires an exact compatible selected font.',True,obj(dict(layout_id=ID,key=TEXT,start=INT,end=INT,font_id=STRING),('layout_id','key','start','end','font_id'))),
 'corpus.search':('Literal concordances and surface frequencies in the pinned corpus. Entry search uses explicit token links.',False,obj(dict(query=TEXT,entry_id=ID,limit=LIMIT))),
 'corpus.links':('Inspect bilingual document links, including stale text ranges and links pinned to older language revisions.',False,obj()),
 'corpus.link':('Link a cited corpus pair to explicit source/translation UTF-16 document ranges. Adaptations must be documented.',True,obj(dict(corpus_id=ID,source=ANCHOR_ARGS,translation=ANCHOR_ARGS,adaptation=TEXT),('corpus_id','source','translation'))),
 'corpus.unlink':('Remove a document corpus link; undo restores it.',True,obj(dict(link_id=ID),('link_id',))),
 'numbers.format':('Format exact integer-string numerator/denominator values in a versioned base-12 convention; report repeats or truncation.',False,obj(dict(convention_id=ID,numerator={'type':'string','pattern':'^-?[0-9]{1,256}$'},denominator={'type':'string','pattern':'^-?[0-9]{1,256}$'},max_places={'type':'integer','minimum':1,'maximum':1024}),('convention_id','numerator'))),
 'numbers.parse':('Parse finite or repeating base-12 notation to an exact reduced rational, without floating point.',False,obj(dict(convention_id=ID,text=TEXT),('convention_id','text'))),
})
# Typed alternatives are exported to MCP rather than accepting arbitrary records.
METHODS['language.record.put'][2]['allOf'] = [
 {'if':{'properties':{'collection':{'const':key}}},'then':{'properties':{'record':schema}}} for key,schema in RECORDS.items()]


class LanguageAPI(StudioAPI):
    version = '0.6.0'
    methods = METHODS

    def dispatch(self, method, params):
        s = self.session; state = s.state['language']
        if method=='language.read':
            data = lang.dataset(state, params.get('revision_id'))
            if params.get('record_id') and not params.get('collection'): raise ValueError('COLLECTION_REQUIRED')
            value = lang.find_record(data, params['collection'], params['record_id']) if params.get('record_id') else data[params['collection']] if params.get('collection') else data
            return dict(revision=deepcopy(lang.revision(state, params.get('revision_id'))), data=value)
        if method=='language.revisions':
            return dict(activeRevisionId=state['activeRevisionId'], revisions=[{k:deepcopy(v) for k,v in r.items() if k!='collections'} | dict(counts={k:len(v) for k,v in r['collections'].items()}) for r in state['revisions']])
        if method=='language.diff': return lang.diff(state, **params)
        if method=='corpus.links': return dict(links=lang.inspect_links(s))
        if method in ('language.export','language.publish'):
            target = pages.target(s, params['path'])
            if method=='language.export': payload=json.dumps(lang.export_package(lang.dataset(state), lang.revision(state)['label']), ensure_ascii=True, indent=2).encode('utf-8')
            else:
                from .language_publication import html_book
                payload=html_book(state,params['kind']).encode('utf-8')
            publication.atomic(target,payload)
            return dict(path=str(target),bytes=len(payload),sha256=lang.hashlib.sha256(payload).hexdigest(),languageRevision=state['activeRevisionId'])
        if method in ('lexicon.search','corpus.search','orthography.transliterate','numbers.format','numbers.parse'):
            data=lang.dataset(state)
            if method=='lexicon.search':
                query=params.get('query','');limit=params.get('limit',200)
                found=[r for r in data['lexicon'] if any(query in v for v in [r['label'],r['headword'],r['pronunciation'],*[x['definition'] for x in r['senses']],*[v['text'] for v in r['variants']]])]
                return dict(records=found[:limit],total=len(found),truncated=len(found)>limit,languageRevision=state['activeRevisionId'])
            if method=='corpus.search':
                if params.get('entry_id'): lang.find_record(data,'lexicon',params['entry_id'])
                result=lang.search(data,**params)
                matched={h['corpusId'] for h in result['hits']}
                result['documentOccurrences']=[l for l in lang.inspect_links(s) if l['corpusId'] in matched and l['usesActiveRevision']]
                result['documentOccurrenceScope']='Linked source/translation ranges; adapted text is not assigned guessed token offsets.'
                return dict(result,languageRevision=state['activeRevisionId'])
            if method=='orthography.transliterate':
                values=dict(params);profile=lang.find_record(data,'transliterations',values.pop('profile_id'))
                return lang.transliterate(profile,**values)
            values=dict(params);convention=lang.find_record(data,'numberConventions',values.pop('convention_id'))
            return (lang.number_format if method=='numbers.format' else lang.number_parse)(convention,**values)
        return super().dispatch(method,params)

    def mutate(self, method, params):
        s=self.session;state=s.state['language']
        if method=='language.adopt':
            rev=lang.revision(state,params['revision_id']);state['activeRevisionId']=rev['id']
            return dict(languageRevision=rev['id'],rewritesDocumentText=False)
        if method in ('language.record.put','language.record.delete','language.archive.import','language.import'):
            data=lang.dataset(state);label=method
            if method=='language.archive.import':
                from .archive_language import seed
                data=seed(s.root);label='Archive transcription · competing readings retained'
            elif method=='language.import':
                package=lang.read_package(params['path']);data=package['data'];label=package['label']
            else:
                key=params['collection'];rid=params['record']['id'] if method.endswith('put') else params['record_id']
                if method.endswith('delete'): lang.find_record(data,key,rid)
                data[key]=[r for r in data[key] if r['id']!=rid]
                if method.endswith('put'): data[key].append(deepcopy(params['record']))
                label=params.get('label') or ('Update ' if method.endswith('put') else 'Remove ')+rid
            return lang.append_revision(state,data,label)
        if method=='orthography.input':
            if s.source_for(s.state['activeFrameId'])!=s.state['activeFrameId']: raise ValueError('FLOW_TARGET_READ_ONLY: select the source frame to edit its story')
            data=lang.dataset(state);layout=lang.find_record(data,'inputLayouts',params['layout_id']);orth=lang.find_record(data,'orthographies',layout['orthographyId'])
            font=s.fonts.resolve(params['font_id'])
            if font.sha256 not in orth['fontSha256s']: raise ValueError('ORTHOGRAPHY_FONT_MISMATCH')
            key=next((k for k in layout['keys'] if k['key']==params['key']),None)
            if key is None: raise ValueError('INPUT_KEY_NOT_FOUND')
            if any(ord(ch) not in font.cmap and ch not in '\n\t' for ch in key['text']): raise ValueError('INPUT_FONT_GLYPH_MISSING')
            s.active.edit(params['start'],params['end'],key['text'])
            s.active.format_range(params['start'],params['start']+lang.utf16_length(key['text']),font_id=params['font_id'])
            return dict(text=key['text'],orthographyId=orth['id'],languageRevision=state['activeRevisionId'])
        if method=='corpus.link':
            record=lang.find_record(lang.dataset(state),'corpus',params['corpus_id'])
            source=lang.anchor(s,**params['source']);translation=lang.anchor(s,**params['translation'])
            adaptation=params.get('adaptation','')
            if (source['text']!=record['text'] or translation['text']!=record['translation']) and not adaptation.strip(): raise ValueError('CORPUS_ADAPTATION_NOTE_REQUIRED')
            link=dict(id=identity('link'),revisionId=state['activeRevisionId'],corpusId=record['id'],source=source,translation=translation,adaptation=adaptation,offsetUnit='utf16-code-unit')
            state['links'].append(link);return deepcopy(link)
        if method=='corpus.unlink':
            if not any(l['id']==params['link_id'] for l in state['links']): raise ValueError('CORPUS_LINK_NOT_FOUND')
            state['links']=[l for l in state['links'] if l['id']!=params['link_id']]
            return dict(removed=params['link_id'])
        return super().mutate(method,params)
