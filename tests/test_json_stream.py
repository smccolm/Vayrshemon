"""Large-book serialization must retain old hashes and exact Unicode values."""
import hashlib
import json
import unittest
from unittest.mock import patch
from vayrshemon import json_stream


class JsonStreamTests(unittest.TestCase):
    def test_canonical_bytes_and_hash_remain_compatible(self):
        state = {'revision': 17, 'title': 'Rôun \"quoted\"\nA\u0301',
                 'pages': [{'pageId': 'p2', 'value': [True, False, None, -7, 1.25]},
                           {'pageId': 'p1', 'text': '𐀀\\\t'}],
                 'language': {'z': [], 'a': {}}}
        for value in (state, {'shellPreview': {}, 'state': state, 'format': 'vayrshemon.document'},
                      {}, [], 'line\ntext', 42, {1:'one',2:'two'}):
            with self.subTest(value=type(value).__name__):
                canonical = json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()
                self.assertEqual(canonical, b''.join(json_stream.chunks(value, sort_keys=True)))
                self.assertEqual(hashlib.sha256(canonical).hexdigest(), json_stream.canonical_digest(value))
                compact = b''.join(json_stream.chunks(value, compact=True))
                self.assertEqual(json.loads(json.dumps(value)), json.loads(compact))
                self.assertEqual(len(compact), json_stream.byte_count(value))

    def test_book_array_is_never_encoded_as_one_object(self):
        pages = [{'pageId': str(i), 'text': 'Page contents\n'*200} for i in range(2200)]
        state = {'pages': pages, 'title': 'Structural test, not language text'}
        payload = {'state': state, 'shellPreview': {'pngBase64': 'test'}}
        encode = json.dumps
        def guarded(value, **options):
            self.assertIsNot(value, pages)
            self.assertIsNot(value, state)
            self.assertIsNot(value, payload)
            return encode(value, **options)
        with patch.object(json_stream.json, 'dumps', side_effect=guarded):
            chunks = list(json_stream.chunks(payload, compact=True))
        self.assertLess(max(map(len, chunks)), 10000)
        self.assertEqual(payload, json.loads(b''.join(chunks)))
        with self.assertRaisesRegex(ValueError, 'JSON_BYTE_LIMIT'):
            json_stream.byte_count(payload, limit=100)

    def test_nonfinite_values_are_rejected(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.assertRaises(ValueError):
                list(json_stream.chunks({'state': {'pages': [{'value': value}]}}))

    def test_content_hash_ignores_only_view_clocks_without_copying_pages(self):
        from vayrshemon.authoring import AuthoringSession
        state = {'documentId':'book', 'revision':8, 'activeFrameId':'f2',
                 'pages':[{'text':'A\u0301 and rôun'}], 'view':{'mode':'mono'}}
        expected = {key:value for key,value in state.items() if key not in ('revision','activeFrameId')}
        digest = hashlib.sha256(json.dumps(expected, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()).hexdigest()
        with patch('vayrshemon.authoring.deepcopy', side_effect=AssertionError('Hash deepcopied book')):
            self.assertEqual(digest, AuthoringSession.content_digest(state))
        self.assertEqual(8, state['revision'])
        self.assertEqual('f2', state['activeFrameId'])


if __name__ == '__main__':
    unittest.main()
