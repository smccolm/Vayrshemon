"""M5 language snapshots and portable records. Earlier native formats stay frozen."""
from copy import deepcopy
from .api import obj, BOOL
from .studio_contracts import STATE as STUDIO_STATE, DOCUMENT as STUDIO_DOCUMENT

TEXT = {'type': 'string', 'maxLength': 20000}
ID = {'type': 'string', 'pattern': '^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$'}
HASH = {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
STATUS = {'enum': ['draft', 'attested', 'uncertain', 'disputed', 'retired']}
INT = {'type': 'integer', 'minimum': 0}
SCALAR = {'type': 'integer', 'minimum': 0, 'maximum': 1114111, 'not': {'minimum': 55296, 'maximum': 57343}}
def array(item, limit=2000): return {'type': 'array', 'items': item, 'maxItems': limit}
def full(**fields): return obj(fields, tuple(fields))
CITATION = full(sourceId=ID, locator=TEXT)
BASE = dict(id=ID, label=TEXT, status=STATUS, citations=array(CITATION), notes=TEXT)
def record(fields, required=()): return obj(dict(BASE, **fields), ('id', 'label', 'status', 'citations', *required))
FEATURES = {'type': 'object', 'maxProperties': 50, 'additionalProperties': TEXT}
FORM = full(form=TEXT, scalar=SCALAR, transliteration={'type': ['string', 'null'], 'maxLength': 100})
SYMBOL = full(id=ID, name=TEXT, kind={'enum': ['letter', 'digit', 'separator', 'punctuation']}, status=STATUS, forms=array(FORM, 20))
VARIANT = full(text=TEXT, script=TEXT, sourceFonts=array(TEXT, 20), note=TEXT)
SENSE = full(id=ID, definition=TEXT, status=STATUS, citations=array(CITATION))
TOKEN = full(start=INT, end=INT, surface=TEXT, morphemes=array(TEXT, 100), glosses=array(TEXT, 100), entryIds=array(ID, 100), senseIds=array(ID, 100), morphologyIds=array(ID, 100), status=STATUS)
RECORDS = {
    'sources': record(dict(path=TEXT, sha256=HASH, kind={'enum': ['docx', 'image', 'mapping', 'other']}), ('path', 'sha256', 'kind')),
    'orthographies': record(dict(version=TEXT, normalization={'const': 'none'}, fontSha256s=array(HASH, 128), symbols=array(SYMBOL), unresolvedScalars=array(SCALAR)), ('version', 'normalization', 'fontSha256s', 'symbols', 'unresolvedScalars')),
    'inputLayouts': record(dict(orthographyId=ID, keys=array(full(key=TEXT, text=TEXT))), ('orthographyId', 'keys')),
    'transliterations': record(dict(orthographyId=ID, mappings=array(full(source=TEXT, target=TEXT)), unknownPolicy={'const': 'preserve'}), ('orthographyId', 'mappings', 'unknownPolicy')),
    'lexicon': record(dict(headword=TEXT, orthographyId={'type': ['string', 'null']}, pronunciation=TEXT, ipa=TEXT, partOfSpeech=TEXT, senses=array(SENSE, 100), variants=array(VARIANT, 100), etymology=TEXT, exampleIds=array(ID, 100), audioLinks=array(TEXT, 100)), ('headword', 'orthographyId', 'pronunciation', 'ipa', 'partOfSpeech', 'senses', 'variants', 'etymology', 'exampleIds', 'audioLinks')),
    'morphology': record(dict(kind={'enum': ['root', 'affix', 'clitic', 'paradigm', 'inflection', 'derivation']}, form=TEXT, features=FEATURES, entryIds=array(ID), cells=array(full(label=TEXT, form=TEXT, features=FEATURES, status=STATUS, citations=array(CITATION)))), ('kind', 'form', 'features', 'entryIds', 'cells')),
    'grammar': record(dict(topic={'enum': ['tense', 'aspect', 'pronouns', 'construction', 'phonology', 'other']}, statement=TEXT, morphologyIds=array(ID), exampleIds=array(ID), alternatives=array(full(statement=TEXT, status=STATUS, citations=array(CITATION)))), ('topic', 'statement', 'morphologyIds', 'exampleIds', 'alternatives')),
    'corpus': record(dict(text=TEXT, translation=TEXT, transliteration=TEXT, rawGloss=TEXT, orthographyId={'type': ['string', 'null']}, sourceFonts=array(TEXT, 100), tokens=array(TOKEN), offsetUnit={'const': 'unicode-scalar'}), ('text', 'translation', 'transliteration', 'rawGloss', 'orthographyId', 'sourceFonts', 'tokens', 'offsetUnit')),
    'numberConventions': record(dict(digits=array(TEXT, 12), digitNames=array(TEXT, 12), radixPoint=TEXT, minus=TEXT, repeatOpen=TEXT, repeatClose=TEXT, readingPolicy={'enum': ['digits-only', 'positional-unverified']}), ('digits', 'digitNames', 'radixPoint', 'minus', 'repeatOpen', 'repeatClose', 'readingPolicy')),
}
COLLECTIONS = tuple(RECORDS)
DATA = full(**{key: array(schema) for key, schema in RECORDS.items()})
REVISION = full(id=ID, parentId={'type': ['string', 'null']}, label=TEXT, createdAt=TEXT, sha256=HASH,
                collections=full(**{key: array(HASH) for key in COLLECTIONS}))
ANCHOR = full(frameId=ID, start=INT, end=INT, text=TEXT, frameSha256=HASH)
LINK = full(id=ID, revisionId=ID, corpusId=ID, source=ANCHOR, translation=ANCHOR,
            adaptation=TEXT, offsetUnit={'const': 'utf16-code-unit'})
LANGUAGE = full(version={'const': '1.0.0'}, activeRevisionId=ID,
                objects={'type': 'object', 'propertyNames': HASH, 'additionalProperties': {'type': 'object'}, 'maxProperties': 10000},
                revisions=array(REVISION, 256), links=array(LINK, 2000))
PACKAGE = full(format={'const': 'vayrshemon.language'}, formatVersion={'const': '1.0.0'}, label=TEXT, sha256=HASH, data=DATA)
STATE = deepcopy(STUDIO_STATE)
STATE['properties']['language'] = LANGUAGE
STATE['required'].append('language')
DOCUMENT = deepcopy(STUDIO_DOCUMENT)
DOCUMENT['properties']['state'] = STATE
DOCUMENT['properties']['formatVersion'] = {'const': '0.5.0'}
DOCUMENT['$id'] = 'urn:vayrshemon:schema:language-document:0.5.0'
