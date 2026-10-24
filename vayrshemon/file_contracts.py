"""M14 native 0.6 wrapper; editable state remains the approved M5 structure."""
from copy import deepcopy
from .api import obj
from .language_contracts import DOCUMENT as LEGACY_DOCUMENT,HASH

PREVIEW=obj(dict(version={'const':1},revision={'type':'integer','minimum':0},stateSha256=HASH,
    colorMode={'enum':['color','mono-black','mono-white']},pageMode={'enum':['one','two']},
    pageIds={'type':'array','items':{'type':'string'},'minItems':1,'maxItems':2,'uniqueItems':True},
    width={'type':'integer','minimum':1,'maximum':1024},height={'type':'integer','minimum':1,'maximum':1024},
    pngSha256=HASH,pngBase64={'type':'string','maxLength':4194304}),
    ('version','revision','stateSha256','colorMode','pageMode','pageIds','width','height','pngSha256','pngBase64'))
DOCUMENT=deepcopy(LEGACY_DOCUMENT)
DOCUMENT['$id']='urn:vayrshemon:schema:file-document:0.6.0'
DOCUMENT['properties']['formatVersion']={'const':'0.6.0'}
# Internal worker snapshots need no thumbnail. Every user save supplies one.
DOCUMENT['properties']['shellPreview']=PREVIEW
