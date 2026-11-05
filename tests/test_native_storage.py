"""The storage envelope preserves content and rejects corrupt/oversized data."""
from copy import deepcopy
import base64
import hashlib
import json
import unittest
import zlib
from vayrshemon.native_storage import pack, unpack


class NativeStorageTests(unittest.TestCase):
    def payload(self):
        return dict(shellPreview={'colorMode':'mono-white','pngBase64':'preview'},
                    format='vayrshemon.document',formatVersion='0.6.0',
                    state={'documentId':'structural-test','pages':[{'text':'A\u0301 rôun 𐀀\n'*100} for _ in range(100)]},
                    history=[{'label':'original'}], engine={'application':'test'})

    def test_roundtrip_keeps_every_value_and_preview(self):
        original = self.payload()
        before = deepcopy(original)
        wire = pack(original)
        self.assertEqual('shellPreview', next(iter(wire)))
        self.assertEqual('0.7.0', wire['formatVersion'])
        self.assertNotIn('state', wire)
        self.assertLess(len(json.dumps(wire)), len(json.dumps(original))//5)
        self.assertEqual(original, unpack(json.loads(json.dumps(wire))))
        self.assertEqual(before, original)
        self.assertIs(original, unpack(original))

    def test_declared_size_checks_and_bomb_bound(self):
        with self.assertRaisesRegex(ValueError,'EXPANDED_LIMIT'):
            pack(self.payload(), expanded_limit=100)
        with self.assertRaisesRegex(ValueError,'COMPRESSED_LIMIT'):
            pack(self.payload(), compressed_limit=10)
        wire = pack(self.payload())
        for size in (0, -1, True, 1000000000000):
            bad = deepcopy(wire); bad['stateEncoding']['expandedBytes'] = size
            with self.assertRaisesRegex(ValueError,'EXPANDED_LIMIT'):
                unpack(bad)
        bad = deepcopy(wire); bad['stateEncoding']['expandedBytes'] = 16
        with self.assertRaisesRegex(ValueError,'EXPANDED_LIMIT'):
            unpack(bad)
        with self.assertRaisesRegex(ValueError,'COMPRESSED_LIMIT'):
            unpack(wire, compressed_limit=10)

    def test_truncation_concatenation_checksum_and_base64(self):
        wire = pack(self.payload())
        raw = base64.b64decode(wire['stateEncoding']['data'])
        for altered in (raw[:-1], raw + zlib.compress(b'{}'), raw + b'trailing'):
            bad = deepcopy(wire); bad['stateEncoding']['data'] = base64.b64encode(altered).decode()
            with self.assertRaisesRegex(ValueError,'STREAM_LENGTH'):
                unpack(bad)
        bad = deepcopy(wire); bad['stateEncoding']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError,'CHECKSUM_MISMATCH'):
            unpack(bad)
        bad = deepcopy(wire); bad['stateEncoding']['data'] += '!'
        with self.assertRaisesRegex(ValueError,'BASE64'):
            unpack(bad)
        bad = deepcopy(wire); bad['state'] = {}
        with self.assertRaisesRegex(ValueError,'FIELDS'):
            unpack(bad)

    def test_inner_json_preserves_strict_validation(self):
        for raw,error in [(b'{"x":1,"x":2}','DUPLICATE_JSON_KEY'),
                          (b'{"x":NaN}','NONFINITE_JSON_NUMBER'),
                          (b'[]','STATE_REQUIRED')]:
            wire = pack(self.payload())
            wire['stateEncoding'].update(expandedBytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                                         data=base64.b64encode(zlib.compress(raw)).decode())
            with self.assertRaisesRegex(ValueError,error):
                unpack(wire)


if __name__ == '__main__':
    unittest.main()
