"""M3 layout contract. M2's schema remains available for lossless migration."""
from copy import deepcopy
from .api import obj,BOOL,STRING
from .editor_contracts import STATE as M2_STATE,EDITOR_DOCUMENT as M2_DOCUMENT,ID

POINT={'type':'number','minimum':0,'maximum':10000}
GRID=obj(dict(enabled=BOOL,step={'type':'number','exclusiveMinimum':0,'maximum':1000},offset=POINT),('enabled','step','offset'))
COLLISION=obj(dict(mode={'enum':['allow','warn','repair']},clearance={'type':'number','minimum':0,'maximum':100},
                   maximumExpansion={'type':'number','minimum':0,'maximum':1000},iterations={'type':'integer','minimum':1,'maximum':16},
                   fixedFrame=BOOL,bounds={'enum':['ink','stroke','effect']},strokeWidth={'type':'number','minimum':0,'maximum':100},effectPadding={'type':'number','minimum':0,'maximum':100}),
              ('mode','clearance','maximumExpansion','iterations','fixedFrame','bounds','strokeWidth','effectPadding'))
PARAGRAPH_RULE=obj(dict(blockId=ID,keepWithNext=BOOL,keepTogether=BOOL,widows={'type':'integer','minimum':1,'maximum':20},orphans={'type':'integer','minimum':1,'maximum':20}),
                   ('blockId','keepWithNext','keepTogether','widows','orphans'))
OPTICAL=obj(dict(left={'type':'string','minLength':1,'maxLength':16},right={'type':'string','minLength':1,'maxLength':16},fontId={'type':['string','null']},
                 delta={'type':'number','minimum':-20,'maximum':20},independentLegacy=BOOL),('left','right','fontId','delta','independentLegacy'))
PROFILE=obj(dict(languageId=ID,revision={'type':'integer','minimum':1},wrap={'enum':['word','grapheme','none']},emergency=BOOL,
                 breakAfter={'type':'string','maxLength':100},prohibitBefore={'type':'string','maxLength':100},prohibitAfter={'type':'string','maxLength':100},
                 hyphenation={'const':'manual-only'}),('languageId','revision','wrap','emergency','breakAfter','prohibitBefore','prohibitAfter','hyphenation'))
FRAME_SETTINGS=obj(dict(enabled=BOOL,leadingDistribution={'enum':['before','split','after']},grid=GRID,collision=COLLISION,
                        paragraphs={'type':'array','items':PARAGRAPH_RULE,'maxItems':2000},optical={'type':'array','items':OPTICAL,'maxItems':256}),
                   ('enabled','leadingDistribution','grid','collision','paragraphs','optical'))
TYPESETTING=obj(dict(version={'const':'0.1.0'},frames={'type':'object','propertyNames':ID,'additionalProperties':FRAME_SETTINGS,'maxProperties':128},
                     flows={'type':'array','maxItems':64,'items':obj(dict(source=ID,targets={'type':'array','items':ID,'uniqueItems':True,'maxItems':127}),('source','targets'))},
                     profiles={'type':'array','items':PROFILE,'maxItems':64}),('version','frames','flows','profiles'))
STATE=deepcopy(M2_STATE); STATE['properties']['typesetting']=TYPESETTING; STATE['required'].append('typesetting')
DOCUMENT=deepcopy(M2_DOCUMENT); DOCUMENT['properties']['state']=STATE; DOCUMENT['properties']['formatVersion']={'const':'0.3.0'}
DOCUMENT['$id']='urn:vayrshemon:schema:typesetting-document:0.3.0'


def settings():
    return dict(enabled=True,leadingDistribution='after',grid=dict(enabled=False,step=12,offset=0),
                collision=dict(mode='warn',clearance=0,maximumExpansion=72,iterations=8,fixedFrame=True,bounds='ink',strokeWidth=0,effectPadding=0),
                paragraphs=[],optical=[])


def profile(language='language.en'):
    return dict(languageId=language,revision=1,wrap='word',emergency=False,breakAfter='',prohibitBefore='',prohibitAfter='',hyphenation='manual-only')


def initial(): return dict(version='0.1.0',frames={},flows=[],profiles=[profile(),profile('language.vayrshemon')])
