"""Single-threaded document session shared by desktop, CLI and MCP."""
from contextlib import contextmanager
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import platform
import time
import uuid

import PySide6
from PySide6.QtCore import QObject, Signal, Qt, qVersion
from PySide6.QtGui import (QFont, QImage, QTextBlockFormat, QTextCharFormat,
                          QTextCursor, QTextDocument, QTextFormat, QTextOption, QColor)
from PySide6.QtWidgets import QApplication

from tools.m0.common import load_json, write_json
from tools.m0.contracts import validators, validate_document_semantics
from tools.m0.synthetic import document, unicode_run
from . import __version__
from .diagnostics import Diagnostics
from .fonts import FontRegistry

STYLE, LANGUAGE, KIND, SOURCE, MAPPING, RUN = range(int(QTextFormat.Property.UserProperty) + 1,
                                                 int(QTextFormat.Property.UserProperty) + 7)
BLOCK = int(QTextFormat.Property.UserProperty) + 20
MAX_TEXT = 100_000
MAX_PAGE_POINTS = 1_000_000
SCALE = 96 / 72


def utf16_length(text):
    return len(text.encode('utf-16-le')) // 2


def scalar_offset(text, utf16):
    if not isinstance(utf16, int) or isinstance(utf16, bool) or utf16 < 0:
        raise ValueError('INVALID_UTF16_OFFSET')
    encoded = text.encode('utf-16-le')
    if utf16 * 2 > len(encoded):
        raise ValueError('OFFSET_OUT_OF_RANGE')
    try:
        return len(encoded[:utf16 * 2].decode('utf-16-le'))
    except UnicodeDecodeError as error:
        raise ValueError('OFFSET_SPLITS_SURROGATE_PAIR') from error


def checked_text(text):
    if not isinstance(text, str) or len(text) > MAX_TEXT:
        raise ValueError('TEXT_LIMIT: maximum 100,000 Unicode scalars in the M1 lab')
    if any(0xD800 <= ord(c) <= 0xDFFF or c in '\r\u2029\x00' for c in text):
        raise ValueError('UNSUPPORTED_TEXT_CONTROL: use LF for paragraph breaks; surrogates, NUL, CR and U+2029 are rejected, never normalized')
    return text


def micro_points(value, unit='pt'):
    factors = {'pt': Decimal(1), 'mm': Decimal(360) / 127, 'in': Decimal(72)}
    if unit not in factors:
        raise ValueError('UNKNOWN_PAGE_UNIT')
    result = Decimal(str(value)) * factors[unit] * 1_000_000
    if not result.is_finite() or result <= 0 or result > MAX_PAGE_POINTS * 1_000_000:
        raise ValueError('PAGE_LIMIT: dimensions must be positive and at most 1,000,000 points')
    return str(result.quantize(Decimal(1), rounding=ROUND_HALF_UP))


class Session(QObject):
    changed = Signal()

    def __init__(self, root, *, source_fonts=True, fonts=None, diagnostics=None, checks=None):
        super().__init__()
        self.root = Path(root).resolve()
        self.session_id = 'session.' + uuid.uuid4().hex
        self.log = diagnostics or Diagnostics(self.root, self.session_id)
        self.fonts = fonts or FontRegistry(self.root, self.log)
        self.doc = QTextDocument(self)
        self.metrics_device = QImage(1, 1, QImage.Format.Format_ARGB32_Premultiplied)
        self.metrics_device.setDotsPerMeterX(3780)
        self.metrics_device.setDotsPerMeterY(3780)
        self.doc.setUseDesignMetrics(True)
        self.doc.documentLayout().setPaintDevice(self.metrics_device)
        self.doc.setDefaultFont(QFont('Segoe UI' if platform.system() == 'Windows' else 'DejaVu Sans', 16))
        option = self.doc.defaultTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.doc.setDefaultTextOption(option)
        self.revision = 0
        self._loading = False
        self._batch_depth = 0
        self._pending = False
        self.editor = None
        self.window = None
        self.composing = False
        self.saved_path = None
        self.saved_hash = None
        self.saved_revision = None
        self.view = dict(mode='color', baselines=False, origins=False, bounds=False, zoom=.65)
        self.features = {'kern': True, 'liga': True}
        self.style_features = {}
        self.timings = []
        self.model = document('document.' + uuid.uuid4().hex, [unicode_run('')])
        self.model['title'] = 'Untitled font laboratory'
        self.model['layoutProfile'] = 'layout.qt-6.8.3-m1'
        self.model['styles'][0]['fontSizeMicroPoints'] = '18000000'
        self.model['styles'][0]['lineHeight'] = {'mode': 'multiple', 'factor': 1.3}
        self.checks = checks if checks is not None else validators(self.root)
        self.doc.contentsChanged.connect(self._contents_changed)
        self.make_demo(source_fonts)
        self.log.emit('core', 'SESSION_STARTED', version=__version__, engine=self.fingerprint())

    def fingerprint(self):
        return dict(application=__version__, qt=qVersion(), pyside=PySide6.__version__,
                    python=platform.python_version(), os=platform.platform(),
                    platformPlugin=QApplication.platformName(), layout='QTextDocument/QTextLayout',
                    logicalDpi=96, units='logical-pixels-at-96-dpi', designMetrics=True,
                    defaultFont=self.doc.defaultFont().family(), features=self.features,
                    fonts=[dict(fontId=f.font_id, sha256=f.sha256) for f in self.fonts.faces.values()])

    def make_demo(self, source_fonts=True):
        model = deepcopy(self.model)
        model['revision'] = 0
        model['stories'][0]['blocks'][0]['runs'] = [unicode_run('Vayrshemon / font and input laboratory', 'run.heading')]
        model['stories'][0]['blocks'].append(dict(blockId='block.2', type='paragraph', direction='auto',
                                                runs=[unicode_run('Type, select, compose, and inspect. A\u0301 / Á / 😀', 'run.instructions')]))
        if source_fonts and (self.root / 'Inputs/font files/Thimfora_79.ttf').is_file():
            master = self.fonts.load_source_recipe()
            model['fonts'] = [dict(fontId=master.font_id, sha256=master.sha256, faceIndex=0)]
            model['styles'].append(dict(styleId='style.script', fontId=master.font_id, fontSizeMicroPoints='42000000',
                                        lineHeight={'mode': 'multiple', 'factor': 1.25}, color='#111827FF'))
            mapping = load_json(self.root / 'data/orthography/thimfora-79.json')
            letters = [e for e in mapping['entries'] if e['kind'] == 'letter']
            letters.sort(key=lambda e: (e['symbolId'], e['form']))
            text = ' '.join(chr(e['scalar']) for e in letters[:24])
            run = dict(runId='run.script', languageId='language.vayrshemon', styleId='style.script', type='legacy',
                       sourceText=text, sourceFontSha256=master.sha256,
                       mappingProfileRef={'profileId': mapping['profileId'], 'revision': mapping['revision']}, normalization='none')
            model['stories'][0]['blocks'].append(dict(blockId='block.3', type='paragraph', direction='auto', runs=[run]))
            mixed = deepcopy(run)
            mixed.update(runId='run.mixed-script', sourceText='Jj 0123456789ÀÁ')
            model['stories'][0]['blocks'].append(dict(blockId='block.4', type='paragraph', direction='auto',
                                                     runs=[unicode_run('English + ', 'run.mixed-english'), mixed]))
        else:
            self.log.emit('fonts', 'SOURCE_ARCHIVE_UNAVAILABLE', level='warning',
                          message='English lab available; load local TTFs to inspect custom lettering.')
        self.load_model(model)

    def _contents_changed(self):
        if self._loading:
            return
        if self._batch_depth:
            self._pending = True
            return
        self.revision += 1
        self.changed.emit()
        self.log.emit('document', 'DOCUMENT_CHANGED', revision=self.revision, characters=self.doc.characterCount()-1)

    @contextmanager
    def transaction(self):
        self._batch_depth += 1
        cursor = QTextCursor(self.doc)
        cursor.beginEditBlock()
        try:
            yield
        finally:
            cursor.endEditBlock()
            self._batch_depth -= 1
            if not self._batch_depth and self._pending:
                self._pending = False
                self._contents_changed()

    def format_for(self, run):
        style = next(s for s in self.model['styles'] if s['styleId'] == run['styleId'])
        fmt = QTextCharFormat()
        font = QFont(self.doc.defaultFont())
        if style['fontId']:
            font.setFamilies([self.fonts.faces[style['fontId']].family])
        font.setPointSizeF(int(style['fontSizeMicroPoints']) / 1_000_000)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        features = self.style_features.get(style['styleId'], self.features)
        font.setKerning(features['kern'])
        font.setFeature(QFont.Tag('liga'), int(features['liga']))
        fmt.setFont(font)
        rgba = style['color']
        fmt.setForeground(QColor(int(rgba[1:3], 16), int(rgba[3:5], 16), int(rgba[5:7], 16), int(rgba[7:9], 16)))
        for key, value in ((STYLE, run['styleId']), (LANGUAGE, run['languageId']), (KIND, run['type']), (RUN, run['runId'])):
            fmt.setProperty(key, value)
        if run['type'] == 'legacy':
            fmt.setProperty(SOURCE, run['sourceFontSha256'])
            fmt.setProperty(MAPPING, json.dumps(run['mappingProfileRef'], sort_keys=True))
        return fmt

    def configure_layout(self):
        was_loading = self._loading
        self._loading = True
        page = self.model['pages'][0]
        margin = int(page['marginsMicroPoints']['left']) / 1_000_000 * SCALE
        self.doc.setDocumentMargin(margin)
        width = int(page['widthMicroPoints']) / 1_000_000 * SCALE
        if self.editor:
            self.editor.setLineWrapColumnOrWidth(round(width))
        self.doc.setTextWidth(width)
        self.doc.documentLayout().setPaintDevice(self.metrics_device)
        self._loading = was_loading

    def validate_model(self, model):
        self.checks['document'].validate(model)
        issues = validate_document_semantics(model)
        if issues:
            raise ValueError(', '.join(issues))
        if len(model['pages']) != 1 or len(model['stories']) != 1:
            raise ValueError('M1_SUPPORTS_ONE_PAGE_AND_ONE_STORY: multi-page editing is M2')
        page = model['pages'][0]
        for field in ('widthMicroPoints', 'heightMicroPoints'):
            micro_points(Decimal(page[field]) / 1_000_000)
        if len(set(page['marginsMicroPoints'].values())) != 1:
            raise ValueError('M1_REQUIRES_EQUAL_PAGE_MARGINS')
        expected_frame = dict(frameId='unused', storyId=model['stories'][0]['storyId'],
                              xMicroPoints=page['marginsMicroPoints']['left'], yMicroPoints=page['marginsMicroPoints']['top'],
                              widthMicroPoints=str(int(page['widthMicroPoints'])-2*int(page['marginsMicroPoints']['left'])),
                              heightMicroPoints=str(int(page['heightMicroPoints'])-2*int(page['marginsMicroPoints']['top'])), overflow='show')
        if len(page['frames']) != 1 or any(page['frames'][0][key] != value for key, value in expected_frame.items() if key != 'frameId'):
            raise ValueError('M1_REQUIRES_ONE_FULL_CONTENT_FRAME_WITH_VISIBLE_OVERFLOW')
        all_text = []
        for block in model['stories'][0]['blocks']:
            block_text = []
            for run in block['runs']:
                if run['type'] == 'symbols':
                    raise ValueError('M1_SYMBOL_SEQUENCE_EDITING_UNSUPPORTED: use the explicit legacy projection; original remains intact')
                block_text.append(checked_text(run.get('text', run.get('sourceText', ''))))
            all_text.append(''.join(block_text))
        checked_text('\n'.join(all_text))
        for style in model['styles']:
            if not 1 <= int(style['fontSizeMicroPoints']) / 1_000_000 <= 1000:
                raise ValueError('M1_FONT_SIZE_LIMIT: 1..1000 pt')
        if len(model['styles']) > 2000:
            raise ValueError('M1_STYLE_LIMIT: 2000 styles')

    def load_model(self, model):
        self.validate_model(model)
        for font in model['fonts']:
            self.fonts.resolve(font['fontId'])
        self._loading = True
        try:
            self.model = deepcopy(model)
            for style in model['styles']:
                self.style_features.setdefault(style['styleId'], deepcopy(self.features))
            self.doc.clear()
            cursor = QTextCursor(self.doc)
            for index, block in enumerate(model['stories'][0]['blocks']):
                block_format = QTextBlockFormat()
                block_format.setProperty(BLOCK, block['blockId'])
                block_format.setLayoutDirection({'auto': Qt.LayoutDirection.LayoutDirectionAuto,
                                                'ltr': Qt.LayoutDirection.LeftToRight,
                                                'rtl': Qt.LayoutDirection.RightToLeft}[block['direction']])
                first_style = next(s for s in model['styles'] if s['styleId'] == block['runs'][0]['styleId']) if block['runs'] else model['styles'][0]
                line = first_style['lineHeight']
                if line['mode'] == 'multiple':
                    block_format.setLineHeight(line['factor'] * 100, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
                else:
                    mode = QTextBlockFormat.LineHeightTypes.FixedHeight if line['mode'] == 'exact' else QTextBlockFormat.LineHeightTypes.MinimumHeight
                    block_format.setLineHeight(int(line['microPoints']) / 1_000_000 * SCALE, mode.value)
                if index:
                    cursor.insertBlock(block_format)
                else:
                    cursor.setBlockFormat(block_format)
                for run in block['runs']:
                    fmt = self.format_for(run)
                    cursor.setCharFormat(fmt)
                    cursor.insertText(run.get('text', run.get('sourceText', '')), fmt)
                if not cursor.block().text() and block['runs']:
                    # Empty paragraphs need a persistent insertion format. A
                    # temporary cursor format alone is lost by the next cursor.
                    cursor.setBlockCharFormat(fmt)
            self.revision = model['revision']
            self.configure_layout()
            self.doc.clearUndoRedoStacks()
        finally:
            self._loading = False
        self.changed.emit()

    def text(self):
        # toPlainText converts NBSP into an ordinary space. Raw text preserves it.
        return self.doc.toRawText().replace('\u2029', '\n')

    def spans(self):
        result = []
        block = self.doc.begin()
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                if fragment.isValid():
                    result.append((fragment.position(), fragment.length(), fragment.text(), fragment.charFormat()))
                iterator += 1
            block = block.next()
        return result

    def snapshot(self, *, with_features=False):
        result = deepcopy(self.model)
        style_features = deepcopy(self.style_features)
        result['revision'] = self.revision
        blocks, seen = [], set()
        block = self.doc.begin()
        while block.isValid():
            identity = block.blockFormat().property(BLOCK) or f'block.qt.{block.position()}'
            if identity in seen:
                identity = f'block.qt.{block.position()}'
            seen.add(identity)
            runs = []
            iterator = block.begin()
            while not iterator.atEnd():
                f = iterator.fragment()
                if f.isValid():
                    fmt = f.charFormat()
                    run_id = fmt.property(RUN) or f'run.qt.{f.position()}'
                    if run_id in seen:
                        run_id = f'run.qt.{f.position()}'
                    seen.add(run_id)
                    run = dict(runId=run_id, languageId=fmt.property(LANGUAGE) or 'language.en',
                               styleId=fmt.property(STYLE) or result['styles'][0]['styleId'],
                               type=fmt.property(KIND) or 'unicode', normalization='none')
                    if run['type'] == 'legacy':
                        run.update(sourceText=f.text(), sourceFontSha256=fmt.property(SOURCE),
                                   mappingProfileRef=json.loads(fmt.property(MAPPING) or 'null'))
                    else:
                        run['text'] = f.text()
                    runs.append(run)
                iterator += 1
            if not runs:
                fmt = block.charFormat()
                runs = [dict(runId=f'run.empty.{block.position()}', languageId=fmt.property(LANGUAGE) or 'language.en',
                             styleId=fmt.property(STYLE) or result['styles'][0]['styleId'], type='unicode', text='', normalization='none')]
                if fmt.property(KIND)=='legacy':
                    runs[0].pop('text')
                    runs[0].update(type='legacy',sourceText='',sourceFontSha256=fmt.property(SOURCE),
                                   mappingProfileRef=json.loads(fmt.property(MAPPING) or 'null'))
            direction = {Qt.LayoutDirection.LeftToRight: 'ltr', Qt.LayoutDirection.RightToLeft: 'rtl'}.get(block.blockFormat().layoutDirection(), 'auto')
            # Qt owns paragraph leading; M0 encodes it on the first run style.
            # Preserve it when a character-format selection spans paragraphs
            # with different leading, without rewriting the live document.
            bf = block.blockFormat()
            if bf.lineHeightType() == QTextBlockFormat.LineHeightTypes.ProportionalHeight.value:
                leading = dict(mode='multiple',factor=bf.lineHeight()/100)
            elif bf.lineHeightType() in (QTextBlockFormat.LineHeightTypes.FixedHeight.value,QTextBlockFormat.LineHeightTypes.MinimumHeight.value):
                leading = dict(mode='exact' if bf.lineHeightType()==QTextBlockFormat.LineHeightTypes.FixedHeight.value else 'at-least',
                               microPoints=str(round(bf.lineHeight()/SCALE*1_000_000)))
            else:
                leading = dict(mode='multiple',factor=1.0)
            for run in runs:
                style = next(s for s in result['styles'] if s['styleId']==run['styleId'])
                if style['lineHeight'] != leading:
                    features = deepcopy(style_features.get(style['styleId'],self.features))
                    style = deepcopy(style)
                    style.pop('styleId')
                    style['lineHeight'] = leading
                    style['styleId'] = 'style.'+hashlib.sha256(json.dumps([style,features],sort_keys=True).encode()).hexdigest()[:16]
                    if style['styleId'] not in {s['styleId'] for s in result['styles']}:
                        result['styles'].append(style)
                    style_features[style['styleId']] = features
                    run['styleId'] = style['styleId']
            blocks.append(dict(blockId=identity, type='paragraph', direction=direction, runs=runs))
            block = block.next()
        result['stories'][0]['blocks'] = blocks
        return (result,style_features) if with_features else result

    def range_cursor(self, start, end, *, grapheme=True):
        text = self.text()
        scalar_offset(text, start)
        scalar_offset(text, end)
        if end < start:
            raise ValueError('REVERSED_RANGE')
        if grapheme and text:
            from PySide6.QtCore import QTextBoundaryFinder
            finder = QTextBoundaryFinder(QTextBoundaryFinder.BoundaryType.Grapheme, text)
            for offset in (start, end):
                finder.setPosition(offset)
                if not finder.isAtBoundary():
                    raise ValueError('RANGE_SPLITS_GRAPHEME')
        cursor = QTextCursor(self.doc)
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        return cursor

    def edit(self, start, end, text):
        checked_text(text)
        if self.composing:
            raise ValueError('COMPOSITION_ACTIVE')
        cursor = self.range_cursor(start, end)
        before = self.text()
        checked_text(before[:scalar_offset(before, start)] + text + before[scalar_offset(before, end):])
        with self.transaction():
            cursor.insertText(text)
        if self.editor:
            self.editor.setTextCursor(cursor)
        return dict(revision=self.revision, caretUtf16=cursor.position())

    def format_range(self, start, end, *, font_id=None, language='language.en', size=18, color='#111827FF'):
        if not 1 <= size <= 1000:
            raise ValueError('M1_FONT_SIZE_LIMIT')
        cursor = self.range_cursor(start, end)
        face = self.fonts.resolve(font_id) if font_id else None
        block_style_id = cursor.charFormat().property(STYLE) or self.model['styles'][0]['styleId']
        line_height = deepcopy(next(s['lineHeight'] for s in self.model['styles'] if s['styleId'] == block_style_id))
        style = dict(fontId=font_id, fontSizeMicroPoints=micro_points(size), lineHeight=line_height, color=color)
        style['styleId'] = 'style.' + hashlib.sha256(json.dumps([style,self.features], sort_keys=True).encode()).hexdigest()[:16]
        run = dict(runId='run.' + uuid.uuid4().hex, styleId=style['styleId'], languageId=language,
                   type='legacy' if face and language == 'language.vayrshemon' else 'unicode', text='', normalization='none')
        if run['type'] == 'legacy':
            run.pop('text')
            mapping = load_json(self.root / 'data/orthography/thimfora-79.json')
            profile = {'profileId': mapping['profileId'], 'revision': mapping['revision']} if face.sha256 in mapping['fontSha256s'] else None
            run.update(sourceText='', sourceFontSha256=face.sha256, mappingProfileRef=profile)
        candidate = deepcopy(self.model)
        if style['styleId'] not in {s['styleId'] for s in candidate['styles']}:
            candidate['styles'].append(style)
        if face and face.font_id not in {f['fontId'] for f in candidate['fonts']}:
            candidate['fonts'].append(dict(fontId=face.font_id, sha256=face.sha256, faceIndex=0))
        self.checks['document'].validate(candidate)
        self.style_features[style['styleId']] = deepcopy(self.features)
        self.model = candidate
        previous = self.revision
        with self.transaction():
            fmt = self.format_for(run)
            self._last_format = fmt
            cursor.setCharFormat(fmt)
            if self.editor:
                self.editor.setTextCursor(cursor)
                self.editor.setCurrentCharFormat(fmt)
        if self.revision == previous:
            self._contents_changed()
        return dict(revision=self.revision, styleId=style['styleId'])

    def set_page(self, width, height, unit='pt'):
        candidate = deepcopy(self.model)
        page = candidate['pages'][0]
        page['widthMicroPoints'], page['heightMicroPoints'] = micro_points(width, unit), micro_points(height, unit)
        margin = int(page['marginsMicroPoints']['left'])
        if min(int(page['widthMicroPoints']), int(page['heightMicroPoints'])) <= margin * 2:
            raise ValueError('PAGE_MARGINS_LEAVE_NO_CONTENT')
        page['frames'][0].update(widthMicroPoints=str(int(page['widthMicroPoints'])-2*margin),
                                 heightMicroPoints=str(int(page['heightMicroPoints'])-2*margin))
        self.model = candidate
        self.configure_layout()
        self._contents_changed()
        return deepcopy(page)

    def output_path(self, path):
        path = Path(path).resolve()
        if path.is_relative_to(self.root / 'Inputs') or path.is_relative_to(self.root / '.git'):
            raise ValueError('PROTECTED_OUTPUT_PATH')
        if any(path == f.path for f in self.fonts.faces.values()):
            raise ValueError('SOURCE_FONT_WRITE_PROTECTED')
        return path

    def save(self, path):
        if self.composing:
            raise ValueError('COMPOSITION_ACTIVE')
        path = self.output_path(path)
        if path.exists():
            if path != self.saved_path:
                raise ValueError('SAVE_AS_TARGET_EXISTS: choose a new path')
            if hashlib.sha256(path.read_bytes()).hexdigest() != self.saved_hash:
                raise ValueError('DOCUMENT_CHANGED_ON_DISK')
        model, style_features = self.snapshot(with_features=True)
        self.validate_model(model)
        for font in model['fonts']:
            self.fonts.resolve(font['fontId'])
        payload = dict(format='vayrshemon.lab', formatVersion='0.1.0', document=model,
                       lab=dict(features=self.features, styleFeatures=style_features, view=self.view, recipe=self.fonts.recipe,
                                fontSources=[dict(fontId=f.font_id, sha256=f.sha256, path=str(f.path)) for f in self.fonts.faces.values()]),
                       engine=self.fingerprint())
        write_json(path, payload)
        self.saved_path, self.saved_hash = path, hashlib.sha256(path.read_bytes()).hexdigest()
        self.saved_revision = self.revision
        self.log.emit('persistence', 'DOCUMENT_SAVED', path=str(path), revision=self.revision, sha256=self.saved_hash)
        return dict(path=str(path), revision=self.revision, sha256=self.saved_hash)

    def open(self, path, *, advance_revision=False):
        path = Path(path).resolve(strict=True)
        if path.stat().st_size > 8 * 1024 * 1024:
            raise ValueError('DOCUMENT_TOO_LARGE')
        payload = load_json(path)
        from jsonschema import Draft202012Validator
        from .contracts import LAB_DOCUMENT
        Draft202012Validator(LAB_DOCUMENT).validate(payload)
        self.validate_model(payload['document'])
        lab = payload['lab']
        for source in lab['fontSources']:
            if source['fontId'] != f"font:{source['sha256']}:0":
                raise ValueError('FONT_ID_HASH_MISMATCH')
            self.fonts.register(source['path'], source['sha256'])
        for font in payload['document']['fonts']:
            self.fonts.resolve(font['fontId'])
        recipe = lab.get('recipe')
        if recipe:
            master = self.fonts.resolve(recipe['master'])
            layers = [self.fonts.resolve(layer['fontId']) for layer in recipe['layers']]
            expected_recipe = self.fonts.recipe_for(master, layers)
            for expected, actual in zip(expected_recipe['layers'], recipe['layers']):
                if expected['glyphMap'] != actual['glyphMap'] or not QColor(actual['color']).isValid() or type(actual['enabled']) is not bool:
                    raise ValueError('INVALID_COLOR_RECIPE')
        self.fonts.recipe = deepcopy(recipe)
        self.features = deepcopy(lab['features'])
        self.style_features = deepcopy(lab['styleFeatures'])
        self.view = deepcopy(lab['view'])
        loaded_model = deepcopy(payload['document'])
        if advance_revision:
            # A live reopen must never make an old optimistic command valid again.
            loaded_model['revision'] = max(self.revision + 1, loaded_model['revision'])
        self.load_model(loaded_model)
        self.saved_path, self.saved_hash = path, hashlib.sha256(path.read_bytes()).hexdigest()
        self.saved_revision = self.revision
        self.log.emit('persistence', 'DOCUMENT_OPENED', path=str(path), revision=self.revision,
                      fileRevision=payload['document']['revision'])
        return dict(path=str(path), revision=self.revision)
