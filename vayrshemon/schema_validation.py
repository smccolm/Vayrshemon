"""Accelerate native-book schema checks without changing their contracts.

The reference validator still produces errors. All semantic, checksum, font
and size checks remain in their existing callers. Older milestone installs
without the accelerator retain the reference implementation.
"""
from functools import lru_cache
import json
from jsonschema import Draft202012Validator

try:
    import jsonschema_rs
except ImportError:
    jsonschema_rs = None


@lru_cache(maxsize=32)
def _compiled(schema_text):
    return jsonschema_rs.Draft202012Validator(
        json.loads(schema_text), validate_formats=False, offline=True)


def validate(schema, instance):
    if jsonschema_rs is not None:
        validator = _compiled(json.dumps(schema, sort_keys=True))
        if validator.is_valid(instance):
            return
    Draft202012Validator(schema).validate(instance)


class NativeDocumentValidator:
    """Reuse the native frame schema, keeping the original error interface."""
    def __init__(self, reference, schemas):
        self.reference = reference
        self.fast = None
        if jsonschema_rs is not None:
            registry = jsonschema_rs.Registry([(s['$id'], s) for s in schemas])
            self.fast = jsonschema_rs.Draft202012Validator(
                reference.schema, registry=registry, validate_formats=False, offline=True)

    def validate(self, instance):
        if self.fast is not None and self.fast.is_valid(instance):
            return
        self.reference.validate(instance)

    def __getattr__(self, name):
        return getattr(self.reference, name)
