"""Versioned authoring format. M0 semantic run contracts remain embedded intact."""
from copy import deepcopy
from .api import obj, BOOL, STRING, NUMBER, OFFSET
from .contracts import FEATURES, VIEW, RECIPE, FONT_SOURCE

ID = {'type':'string','pattern':r'^[A-Za-z][A-Za-z0-9._:-]{0,127}$'}
POINTS = {'type':'string','pattern':r'^(0|[1-9][0-9]*)$','maxLength':13}
POSITIVE = dict(POINTS,pattern=r'^[1-9][0-9]*$')
ATTR = obj(dict(tracking={'type':'number','minimum':-100,'maximum':100},
                wordSpacing={'type':'number','minimum':-100,'maximum':100},
                baseline={'type':'number','minimum':-100,'maximum':100}),('tracking','wordSpacing','baseline'))
PARAGRAPH = obj(dict(alignment={'enum':['left','center','right','justify']},
                     before={'type':'number','minimum':0,'maximum':10000},
                     after={'type':'number','minimum':0,'maximum':10000},
                     tabs={'type':'array','items':{'type':'number','minimum':0,'maximum':1000000},'maxItems':100}),
                ('alignment','before','after','tabs'))
PACKAGE = obj(dict(document={'type':'object'},styleFeatures={'type':'object','additionalProperties':FEATURES,'maxProperties':2000},
                   characters={'type':'array','maxItems':100000,'items':obj(dict(start=OFFSET,end=OFFSET,attributes=ATTR),('start','end','attributes'))},
                   paragraphs={'type':'array','maxItems':100000,'items':PARAGRAPH}),
              ('document','styleFeatures','characters','paragraphs'))
FRAME = obj(dict(frameId=ID,name={'type':'string','maxLength':100},x=POINTS,y=POINTS,width=POSITIVE,height=POSITIVE,
                 overflow={'enum':['show','clip']},content=PACKAGE),('frameId','name','x','y','width','height','overflow','content'))
MARGINS = obj({side:POINTS for side in ('top','right','bottom','left')},('top','right','bottom','left'))
PAGE = obj(dict(pageId=ID,name={'type':'string','maxLength':100},width=POSITIVE,height=POSITIVE,margins=MARGINS,
                frames={'type':'array','minItems':1,'maxItems':32,'items':FRAME}),('pageId','name','width','height','margins','frames'))
FORMAT_FIELDS = dict(font_id={'type':['string','null']},language={'type':'string','pattern':r'^language\.[A-Za-z0-9._-]+$'},
                     size={'type':'number','minimum':1,'maximum':1000},color={'type':'string','pattern':'^#[0-9a-fA-F]{8}$'},
                     tracking=ATTR['properties']['tracking'],wordSpacing=ATTR['properties']['wordSpacing'],baseline=ATTR['properties']['baseline'])
STYLE = obj(dict(name={'type':'string','minLength':1,'maxLength':80},format=obj(FORMAT_FIELDS)),('name','format'))
STATE = obj(dict(documentId=ID,title={'type':'string','maxLength':200},revision={'type':'integer','minimum':0},
                 pages={'type':'array','minItems':1,'maxItems':100,'items':PAGE},activeFrameId=ID,
                 fontSources={'type':'array','maxItems':128,'items':FONT_SOURCE},recipe={'anyOf':[{'type':'null'},RECIPE]},
                 features=FEATURES,view=VIEW,styles={'type':'array','maxItems':100,'items':STYLE}),
            ('documentId','title','revision','pages','activeFrameId','fontSources','recipe','features','view','styles'))
HISTORY = obj(dict(revision={'type':'integer','minimum':0},label=STRING,timestamp=STRING,sha256=STRING),('revision','label','timestamp','sha256'))
EDITOR_DOCUMENT = obj(dict(format={'const':'vayrshemon.document'},formatVersion={'const':'0.2.0'},state=STATE,
                           history={'type':'array','maxItems':256,'items':HISTORY},engine={'type':'object'}),
                      ('format','formatVersion','state','history','engine'))
EDITOR_DOCUMENT.update({'$schema':'https://json-schema.org/draft/2020-12/schema',
                        '$id':'urn:vayrshemon:schema:editor-document:0.2.0'})
