"""Route a touch key to the active native text frame and its saved run format."""
from . import reading
from .frame import ALIGNMENTS
from .session import KIND, LANGUAGE, SOURCE, STYLE, checked_text, scalar_offset


NATIVE = {'script': reading.SCRIPT_SHA, 'roman': reading.ROMAN_SHA}
LABELS = {'script': 'Vayrshemon', 'roman': 'Transliteration 7', 'gloss': 'Construction gloss', 'english': 'English'}


def column_role(frame, fmt):
    name = frame['name'].casefold().strip()
    if name == 'construction gloss' or name == 'gloss':
        return 'gloss'
    if 'english' in name or name.endswith(' source'):
        return 'english'
    if name in ('vayrshemon', 'thimfora 79'):
        return 'script'
    if name in ('transliteration', 'transliteration 7'):
        return 'roman'
    # Older and user-renamed frames can have any name. At a fallback
    # punctuation run use the other runs in this frame to identify its script.
    for role, sha in NATIVE.items():
        if fmt.property(SOURCE) == sha:
            return role
    if fmt.property(LANGUAGE) == 'language.en' and fmt.property(STYLE) != 'style.archive-punctuation':
        return 'english'
    for block in frame['content']['document']['stories'][0]['blocks']:
        for run in block['runs']:
            if run['type'] == 'legacy':
                for role, sha in NATIVE.items():
                    if run['sourceFontSha256'] == sha:
                        return role
    return 'english'


def selected_alignment(cursor):
    end = cursor.selectionEnd()
    block = cursor.document().findBlock(cursor.selectionStart())
    first = block.blockFormat().alignment()
    block = block.next()
    while block.isValid() and block.position() < end:
        if block.blockFormat().alignment() != first:
            return None
        block = block.next()
    return next((name for name, flag in ALIGNMENTS.items() if first & flag), 'left')


def insertion_format(editor, role, text):
    native = editor.session
    fmt = editor.currentCharFormat()
    styles = {s['styleId']: s for s in native.model['styles']}
    style = styles.get(fmt.property(STYLE), native.model['styles'][0])
    custom = role in NATIVE
    punctuation = styles.get('style.archive-punctuation')
    if custom:
        sha = NATIVE[role]
        fid = 'font:' + sha + ':0'
        face = native.fonts.faces.get(fid) or native.fonts.resolve(fid)
    else:
        roman = 'font:' + reading.ROMAN_SHA + ':0'
        # Published right columns can use the Roman body face for ordinary
        # English. It is still a Unicode run. Other English fonts stay local.
        if style['fontId'] != roman and fmt.property(KIND) != 'legacy':
            if style['styleId'] != 'style.archive-punctuation' and (
                    style['fontId'] or not any(s['fontId'] == roman for s in styles.values())):
                return fmt
        face = native.fonts.faces.get(roman)
    literal = bool(face and (ord(text) not in face.cmap or
                   (not custom and (ord(text) > 127 or text in '·()+-[]{}/'))))
    wanted = face.font_id if face else None
    if literal:
        wanted = punctuation['fontId'] if punctuation else None
    legacy = custom and not literal
    kind = 'legacy' if legacy else 'unicode'
    if style['fontId'] == wanted and (fmt.property(KIND) or 'unicode') == kind:
        return fmt
    # Return to the actual body style after a punctuation key, even when the
    # archived script column has 50 pt letters and 22 pt punctuation.
    position = editor.textCursor().selectionStart()
    spans = sorted(native.spans(), key=lambda span:
                   max(0, position - span[0] - span[1], span[0] - position))
    for _, _, _, candidate in spans:
        saved = styles.get(candidate.property(STYLE))
        if saved and saved['fontId'] == wanted and candidate.property(KIND) == kind:
            return candidate
    if literal and punctuation:
        # Some published frames declare the 22 pt punctuation style but have
        # never needed it. Use that exact size even for the first such key.
        return native.format_for(dict(styleId=punctuation['styleId'], languageId='language.en',
                                      type='unicode', runId='run.keyboard-punctuation'))
    # A new or empty frame may never have used this face. Reuse the editor's
    # style creation, feature inheritance and orthography mapping.
    saved_cursor = editor.textCursor()
    pos = saved_cursor.selectionStart()
    native.format_range(pos, pos, font_id=wanted,
                        language='language.vayrshemon' if legacy else 'language.en',
                        size=int(style['fontSizeMicroPoints']) / 1e6, color=style['color'])
    result = native.insertion_format[1]
    editor.setTextCursor(saved_cursor)
    return result


def type_character(editor, role, text):
    cursor = editor.textCursor()
    if not editor.within_document_limit(text):
        return False
    before = editor.session.text()
    checked_text(before[:scalar_offset(before, cursor.selectionStart())] + text +
                 before[scalar_offset(before, cursor.selectionEnd()):])
    with editor.book.typing_command():
        fmt = insertion_format(editor, role, text)
        cursor.insertText(text, fmt)
        editor.session.insertion_format = (cursor.position(), fmt)
        editor.setTextCursor(cursor)
    return True
