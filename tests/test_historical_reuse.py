"""Measured spread reuse must not accept changed typography or stale proofs."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest

from tools.compose_historical_book import reusable_spreads
from tools.kjv_archive import ROOT, digest


class HistoricalReuseTests(unittest.TestCase):
    def test_explicit_new_source_font_preserves_checked_old_fonts(self):
        temp_root = ROOT / '.local' / 'test-historical-reuse'
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as folder:
            path = Path(folder) / 'book.vay'
            old_font = dict(fontId='body', sha256='body-hash')
            added_font = dict(fontId='source-signs', sha256='sign-hash')
            engine = dict(qt='6', fonts=[old_font])
            state = dict(recipe={}, paint={}, styles={}, features={}, fontSources=[old_font],
                         typesetting=dict(profiles={}), pages=[])
            path.write_text(json.dumps(dict(engine=engine, state=state)), encoding='utf8')
            (path.parent/'layout-validation.json').write_text(json.dumps(dict(
                sha256=digest(path), templateSha256='template', checks=[])), encoding='utf8')
            (path.parent/'page-index.json').write_text('{"spreads":[]}', encoding='utf8')
            current_engine = dict(engine, fonts=[old_font, added_font])
            current_state = dict(state, fontSources=[old_font, added_font])
            with self.assertRaisesRegex(ValueError, 'ENGINE_MISMATCH'):
                reusable_spreads(path, 'template', current_engine, current_state)
            self.assertEqual(reusable_spreads(path, 'template', current_engine, current_state,
                                             additional_font_ids=['source-signs']), {})
            changed = dict(current_engine, fonts=[dict(old_font, sha256='changed'), added_font])
            with self.assertRaisesRegex(ValueError, 'ENGINE_MISMATCH'):
                reusable_spreads(path, 'template', changed, current_state,
                                 additional_font_ids=['source-signs', 'body'])
            missing = dict(current_engine, fonts=[added_font])
            with self.assertRaisesRegex(ValueError, 'ENGINE_MISMATCH'):
                reusable_spreads(path, 'template', missing, current_state,
                                 additional_font_ids=['source-signs', 'body'])
            changed_state = dict(current_state, fontSources=[dict(old_font, path='different'), added_font])
            with self.assertRaisesRegex(ValueError, 'FORMAT_MISMATCH'):
                reusable_spreads(path, 'template', current_engine, changed_state,
                                 additional_font_ids=['source-signs'])

    def test_rendering_changes_and_stale_files_are_rejected(self):
        temp_root = ROOT / '.local' / 'test-historical-reuse'
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as folder:
            path = Path(folder) / 'book.vay'
            engine = dict(qt='6', fonts=[dict(sha256='font-a')],
                          lightingProfileHash='light-a', languageRevision='old')
            state = dict(recipe={}, paint={}, styles={}, features={}, fontSources=[],
                         typesetting=dict(profiles={}), pages=[])
            payload = dict(engine=engine, state=state)
            def write(name, data):
                (path.parent / name).write_text(json.dumps(data), encoding='utf8')
            write(path.name, payload)
            write('layout-validation.json', dict(sha256=digest(path), templateSha256='template', checks=[]))
            write('page-index.json', dict(spreads=[]))
            # Provenance alone cannot invalidate identical compiled strings.
            self.assertEqual(reusable_spreads(path, 'template', dict(engine, languageRevision='new'), state), {})
            for key, value in [('qt', '7'), ('fonts', []), ('lightingProfileHash', 'light-b')]:
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'ENGINE_MISMATCH'):
                    reusable_spreads(path, 'template', dict(engine, **{key:value}), state)
            changed = deepcopy(state)
            changed['paint'] = {'color': 'different'}
            with self.assertRaisesRegex(ValueError, 'FORMAT_MISMATCH'):
                reusable_spreads(path, 'template', engine, changed)
            with self.assertRaisesRegex(ValueError, 'PROOF_HASH_MISMATCH'):
                reusable_spreads(path, 'different-template', engine, state)
            path.write_text(path.read_text() + ' ', encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'PROOF_HASH_MISMATCH'):
                reusable_spreads(path, 'template', engine, state)
