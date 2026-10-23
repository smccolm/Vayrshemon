"""File identities and private, process-only Qt font registrations."""
from dataclasses import dataclass
import hashlib
from io import BytesIO
from pathlib import Path

from fontTools.ttLib import TTFont
from PySide6.QtCore import QByteArray
from PySide6.QtGui import QFont, QFontDatabase, QRawFont

from tools.m0.common import load_json


@dataclass
class Face:
    font_id: str
    sha256: str
    path: Path
    family: str
    original_family: str
    qt_id: int
    data: bytes
    glyph_order: list
    cmap: dict
    metrics: dict
    units_per_em: int
    table_hashes: dict

    def raw(self, pixel_size):
        raw = QRawFont(QByteArray(self.data), pixel_size, QFont.HintingPreference.PreferNoHinting)
        if not raw.isValid():
            raise ValueError('FONT_RAW_LOAD_FAILED: ' + self.font_id)
        return raw


class FontRegistry:
    def __init__(self, root, diagnostics):
        self.root = Path(root)
        self.diagnostics = diagnostics
        self.faces = {}
        self.by_family = {}
        self.records = {entry['fontId']: entry for entry in load_json(self.root / 'data/fonts.json')['fonts']}
        self.recipe = None
        self._raw_cache = {}

    def register(self, path, expected_sha=None):
        path = Path(path).resolve(strict=True)
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('FONT_TOO_LARGE: limit is 64 MiB')
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if expected_sha and sha != expected_sha:
            raise ValueError('FONT_HASH_MISMATCH: ' + str(path))
        identity = f'font:{sha}:0'
        if identity in self.faces:
            return self.faces[identity]
        if len(self.faces) >= 128 or sum(len(face.data) for face in self.faces.values()) + len(data) > 256*1024*1024:
            raise ValueError('FONT_SESSION_LIMIT: 128 files / 256 MiB; save and start a new session')
        source = TTFont(BytesIO(data), recalcTimestamp=False)
        if 'glyf' not in source or 'fvar' in source:
            raise ValueError('M1_REQUIRES_STATIC_TRUETYPE_OUTLINES')
        order = source.getGlyphOrder()
        cmap = source.getBestCmap() or {}
        family = 'Vayrshemon_' + sha[:32]
        original = source['name'].getDebugName(1) or path.stem
        table_hashes = {tag: hashlib.sha256(source.getTableData(tag)).hexdigest()
                        for tag in ('cmap', 'glyf', 'hmtx', 'GPOS', 'GSUB', 'kern') if tag in source}
        # QFont selects by family. Give exact files unique private family names;
        # preserve every outline/positioning table and never rewrite the source.
        for record in source['name'].names:
            if record.nameID in (1, 3, 4, 6, 16, 21):
                record.string = family.encode(record.getEncoding())
        for name_id in (1, 3, 4, 6, 16, 21):
            source['name'].setName(family, name_id, 3, 1, 0x409)
        if 'DSIG' in source:
            del source['DSIG']
        buffer = BytesIO()
        source.save(buffer)
        private_data = buffer.getvalue()
        check = TTFont(BytesIO(private_data), recalcTimestamp=False)
        if any(hashlib.sha256(check.getTableData(tag)).hexdigest() != digest for tag, digest in table_hashes.items()):
            raise ValueError('PRIVATE_FONT_CHANGED_GEOMETRY')
        qt_id = QFontDatabase.addApplicationFontFromData(QByteArray(private_data))
        if qt_id < 0 or family not in QFontDatabase.applicationFontFamilies(qt_id):
            raise ValueError('FONT_PRIVATE_REGISTRATION_FAILED: ' + str(path))
        face = Face(identity, sha, path, family, original, qt_id, private_data,
                    order, cmap, dict(source['hmtx'].metrics), source['head'].unitsPerEm, table_hashes)
        self.faces[identity] = face
        self.by_family[family] = face
        self.diagnostics.emit('fonts', 'FONT_LOADED', fontId=identity, source=str(path),
                              originalFamily=original, privateFamily=family, glyphs=len(order))
        return face

    def resolve(self, identity):
        if identity in self.faces:
            face = self.faces[identity]
            if not face.path.is_file() or hashlib.sha256(face.path.read_bytes()).hexdigest() != face.sha256:
                raise ValueError('FONT_MISSING_OR_CHANGED: ' + str(face.path))
            return face
        record = self.records.get(identity)
        if not record:
            raise ValueError('FONT_UNRESOLVED: register the exact file first: ' + identity)
        return self.register(self.root / 'Inputs' / record['asset']['path'], record['asset']['sha256'])

    def load_source_recipe(self):
        paths = ('font files/Thimfora_80_Infill.ttf', 'font files/Thimfora_81_Fragments.ttf',
                 'font files/Thimfora_79.ttf')
        faces = []
        for path in paths:
            record = next(record for record in self.records.values() if record['asset']['path'] == path)
            faces.append(self.resolve(record['fontId']))
        self.set_recipe(faces[2], faces)
        return faces[2]

    def set_recipe(self, master, layers):
        self.recipe = self.recipe_for(master, layers)
        self.diagnostics.emit('fonts', 'LAYER_RECIPE_VALIDATED', master=master.font_id,
                              layers=[face.font_id for face in layers], placement='master-origins',
                              effects='flat fills; Photoshop glow/bevel deferred to M4')

    @staticmethod
    def recipe_for(master, layers):
        if len(layers) != 3:
            raise ValueError('THREE_LAYERS_REQUIRED')
        for face in layers:
            if face.units_per_em != master.units_per_em or face.cmap != master.cmap:
                raise ValueError('LAYER_CMAP_OR_SCALE_MISMATCH')
            if set(face.glyph_order) != set(master.glyph_order):
                raise ValueError('LAYER_GLYPH_MAPPING_MISMATCH')
            if any(face.metrics[name][0] != master.metrics[name][0] for name in master.glyph_order):
                raise ValueError('LAYER_ADVANCE_MISMATCH')
        return dict(recipeId='recipe.thimfora.flat-lab', revision='0.1.0', master=master.font_id,
                           layers=[dict(fontId=face.font_id, color=color, enabled=True,
                                        glyphMap=[face.glyph_order.index(name) for name in master.glyph_order])
                                   for face, color in zip(layers, ('#43b8a0', '#164e78', '#78d9f2'))])

    def raw(self, identity, pixels):
        key = (identity, pixels)
        if key not in self._raw_cache:
            if len(self._raw_cache) > 128:
                self._raw_cache.clear()
            self._raw_cache[key] = self.faces[identity].raw(pixels)
        return self._raw_cache[key]

    def describe(self):
        return [dict(fontId=f.font_id, sha256=f.sha256, path=str(f.path), family=f.original_family,
                     privateFamily=f.family, glyphCount=len(f.glyph_order)) for f in self.faces.values()]
