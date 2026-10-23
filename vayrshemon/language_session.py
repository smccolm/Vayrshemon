"""M5 adds a versioned language library to M4 without changing painted text."""
from copy import deepcopy
from jsonschema import Draft202012Validator
from .studio_session import StudioSession
from .studio_contracts import DOCUMENT as M4_DOCUMENT
from .typesetting_contracts import DOCUMENT as M3_DOCUMENT, initial as typesetting_initial
from .editor_contracts import EDITOR_DOCUMENT as M2_DOCUMENT
from .authoring import AuthoringSession
from .paint import initial as paint_initial
from .language_contracts import STATE, DOCUMENT
from . import language


class LanguageSession(StudioSession):
    state_schema = STATE
    document_schema = DOCUMENT
    file_version = '0.5.0'

    def new_state(self, *args, **kwargs):
        state = super().new_state(*args, **kwargs)
        state['language'] = language.initial()
        return state

    def migrate(self, payload, path):
        if payload.get('format') == 'vayrshemon.document':
            version = payload.get('formatVersion')
            schema = {self.file_version:DOCUMENT, '0.4.0':M4_DOCUMENT, '0.3.0':M3_DOCUMENT, '0.2.0':M2_DOCUMENT}.get(version)
            if schema is None: raise ValueError('UNSUPPORTED_DOCUMENT_VERSION')
            Draft202012Validator(schema).validate(payload)
            state = deepcopy(payload['state'])
            if version == self.file_version: return state, False
        else: state, _ = AuthoringSession.migrate(self, payload, path)
        state.setdefault('typesetting', typesetting_initial())
        state.setdefault('paint', paint_initial())
        state['language'] = language.initial()
        return state, True

    def validate(self, state):
        super().validate(state)
        # Validate a language graph once per content change. Text edits don't
        # require revalidating every immutable record; hashes guard the cache.
        signature = language.digest(state['language'])
        if signature != self.__dict__.get('_validated_language'):
            language.validate_state(state['language'])
            self._validated_language = signature

    def fingerprint(self):
        value = super().fingerprint()
        value.update(languageVersion='1.0.0', languageRevision=self.state['language']['activeRevisionId'], corpusOffsets='unicode-scalar; document links UTF-16', numbers='exact rational / base 12')
        return value
