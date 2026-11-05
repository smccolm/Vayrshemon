"""M14 native 0.6 wrapper; editable state remains the approved M5 structure."""
from copy import deepcopy
from .api import obj
from .language_contracts import DOCUMENT as LEGACY_DOCUMENT,HASH
from .book_session import MAX_PAGES,MAX_FRAMES
from .numbering_contracts import SETTINGS

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
STATE=DOCUMENT['properties']['state']
STATE['properties']['pageNumbering']=SETTINGS
from .print_edition import SCHEMA as PRINT_EDITION
STATE['properties']['printEdition']=PRINT_EDITION
STATE['properties']['pages']['maxItems']=MAX_PAGES
STATE['properties']['typesetting']['properties']['frames']['maxProperties']=MAX_FRAMES

# This envelope decodes to DOCUMENT before ordinary schema/semantic validation.
from .native_storage import MAX_EXPANDED_BYTES, MAX_COMPRESSED_BYTES
PACKED_DOCUMENT=obj(dict(format={'const':'vayrshemon.document'},formatVersion={'const':'0.7.0'},
    shellPreview=PREVIEW,history=DOCUMENT['properties']['history'],engine=DOCUMENT['properties']['engine'],
    stateEncoding=obj(dict(codec={'const':'zlib-json-v1'},expandedBytes={'type':'integer','minimum':1,'maximum':MAX_EXPANDED_BYTES},
        sha256=HASH,data={'type':'string','maxLength':4*((MAX_COMPRESSED_BYTES+2)//3)}),
        ('codec','expandedBytes','sha256','data'))),('format','formatVersion','stateEncoding','history','engine'))
FILE_DOCUMENT={'$schema':'https://json-schema.org/draft/2020-12/schema',
    '$id':'urn:vayrshemon:schema:native-storage:0.7.0','oneOf':[DOCUMENT,PACKED_DOCUMENT]}
