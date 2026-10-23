"""M4 paint and publication contracts. Frozen M1-M3 schemas remain unchanged."""
from copy import deepcopy
from .api import obj,BOOL
from .typesetting_contracts import STATE as M3_STATE,DOCUMENT as M3_DOCUMENT
from .paint import DEFAULT,VERSION

COLOR={'type':'string','pattern':'^#[0-9a-fA-F]{6}$'}
FONT={'type':'string','pattern':'^font:[0-9a-f]{64}:0$'}
def number(low,high): return dict(type='number',minimum=low,maximum=high)
RECIPE_FIELDS={key:deepcopy(COLOR) for key in ('rim','highlight','recess','edge','glow')}
RECIPE_FIELDS.update(bevel=number(.001,.1),depth=number(.1,8),edgeWidth=number(0,.02),
    glowRadius=number(0,.08),glowOpacity=number(0,1),shadowRadius=number(0,.08),
    shadowX=number(-.1,.1),shadowY=number(-.1,.1),shadowOpacity=number(0,1),
    lightAzimuth=number(0,360),lightElevation=number(5,85),gradient=number(0,1))
RECIPE=obj(dict(recipeId={'type':'string','minLength':1,'maxLength':100},version={'const':VERSION},revision={'type':'integer','minimum':1},**RECIPE_FIELDS),tuple(DEFAULT))
BINDING_FIELDS=dict(fontId=FONT,enabled=BOOL,kind={'enum':['layered','derived']},glowFontId=FONT,interiorFontId=FONT)
BINDING=obj(BINDING_FIELDS,('fontId','enabled','kind'))
BINDING['allOf']=[{'if':{'properties':{'kind':{'const':'layered'}}},'then':{'required':['glowFontId','interiorFontId']},'else':{'not':{'anyOf':[{'required':['glowFontId']},{'required':['interiorFontId']}]}}}]
PAINT=obj(dict(version={'const':VERSION},recipe=RECIPE,bindings={'type':'array','items':BINDING,'maxItems':128},
    background={'type':'string','pattern':'^#[0-9a-fA-F]{8}$'},rasterDpi={'type':'integer','minimum':72,'maximum':600}),('version','recipe','bindings','background','rasterDpi'))
STATE=deepcopy(M3_STATE);STATE['properties']['paint']=PAINT;STATE['required'].append('paint')
DOCUMENT=deepcopy(M3_DOCUMENT);DOCUMENT['properties']['state']=STATE
DOCUMENT['properties']['formatVersion']={'const':'0.4.0'}
DOCUMENT['$id']='urn:vayrshemon:schema:studio-document:0.4.0'
