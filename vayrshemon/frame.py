"""A frame has one native text document; page composition never reshapes its glyphs."""
from copy import deepcopy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor, QTextBlockFormat, QTextOption, QTextFormat
from .session import Session, SCALE, STYLE, LANGUAGE,checked_text,scalar_offset

TRACKING, WORD_SPACING, BASELINE = range(int(QTextFormat.Property.UserProperty)+30,int(QTextFormat.Property.UserProperty)+33)

ALIGNMENTS = {'left':Qt.AlignmentFlag.AlignLeft,'center':Qt.AlignmentFlag.AlignHCenter,
              'right':Qt.AlignmentFlag.AlignRight,'justify':Qt.AlignmentFlag.AlignJustify}


class FrameSession(Session):
    def __init__(self, root, fonts, content, checks=None, features=None):
        super().__init__(root,source_fonts=False,fonts=fonts,diagnostics=fonts.diagnostics,checks=checks)
        self.owner = None
        self.insertion_format=None
        if features is not None: self.features=deepcopy(features)
        self.load_package(content)

    def make_demo(self,source_fonts=True):
        self.load_model(self.model)

    def attributes(self, fmt):
        font = fmt.font()
        tracking = font.letterSpacing()/SCALE if font.letterSpacingType()==QFont.SpacingType.AbsoluteSpacing else 0
        return {key:fmt.property(prop) if fmt.hasProperty(prop) else fallback
                for key,prop,fallback in [('tracking',TRACKING,tracking),('wordSpacing',WORD_SPACING,font.wordSpacing()/SCALE),('baseline',BASELINE,fmt.baselineOffset())]}

    def put_attributes(self, cursor, values, fmt=None):
        fmt = fmt if fmt is not None else cursor.charFormat()
        font = fmt.font()
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing,values.get('tracking',0)*SCALE)
        font.setWordSpacing(values.get('wordSpacing',0)*SCALE)
        fmt.setFont(font)
        fmt.setBaselineOffset(values.get('baseline',0))
        for key,prop in [('tracking',TRACKING),('wordSpacing',WORD_SPACING),('baseline',BASELINE)]:
            fmt.setProperty(prop,values.get(key,0))
        cursor.setCharFormat(fmt)
        if not cursor.hasSelection() and not cursor.block().text(): cursor.setBlockCharFormat(fmt)
        return fmt

    def package(self):
        model, features = self.snapshot(with_features=True)
        paragraphs=[]
        characters=[dict(start=start,end=start+length,attributes=self.attributes(fmt)) for start,length,_,fmt in self.spans()]
        block=self.doc.begin()
        while block.isValid():
            bf=block.blockFormat()
            if not block.text(): characters.append(dict(start=block.position(),end=block.position(),attributes=self.attributes(block.charFormat())))
            alignment=next((name for name,value in ALIGNMENTS.items() if bf.alignment() & value),'left')
            paragraphs.append(dict(alignment=alignment,before=bf.topMargin()/SCALE,after=bf.bottomMargin()/SCALE,
                                   tabs=[tab.position/SCALE for tab in bf.tabPositions()]))
            block=block.next()
        return dict(document=model,styleFeatures=features,
                    characters=sorted(characters,key=lambda c:c['start']),
                    paragraphs=paragraphs)

    def load_package(self, content):
        self.style_features=deepcopy(content['styleFeatures'])
        self.load_model(content['document'])
        self._loading=True
        try:
            for part in content['characters']:
                cursor=self.range_cursor(part['start'],part['end'],grapheme=False)
                self.put_attributes(cursor,part['attributes'])
            block=self.doc.begin()
            for paragraph in content['paragraphs']:
                if not block.isValid():
                    raise ValueError('PARAGRAPH_COUNT_MISMATCH')
                cursor=QTextCursor(block)
                bf=block.blockFormat()
                bf.setAlignment(ALIGNMENTS[paragraph['alignment']])
                bf.setTopMargin(paragraph['before']*SCALE)
                bf.setBottomMargin(paragraph['after']*SCALE)
                tabs=[]
                for position in paragraph['tabs']:
                    tab=QTextOption.Tab()
                    tab.position=position*SCALE
                    tab.type=QTextOption.TabType.LeftTab
                    tabs.append(tab)
                bf.setTabPositions(tabs)
                cursor.setBlockFormat(bf)
                block=block.next()
        finally:
            self._loading=False
        self.doc.setUndoRedoEnabled(False)

    def format_range(self,start,end,**values):
        extras={key:values.pop(key) for key in ('tracking','wordSpacing','baseline') if key in values}
        self.range_cursor(start,end)
        previous=[(max(start,p),min(end,p+n),fmt) for p,n,_,fmt in self.spans() if p<end and p+n>start]
        if start==end:
            previous=[(start,end,self.range_cursor(start,end).charFormat())]
        with self.transaction():
            for first,last,fmt in previous:
                attributes=self.attributes(fmt)
                if values:
                    style=next((s for s in self.model['styles'] if s['styleId']==fmt.property(STYLE)),self.model['styles'][0])
                    inherited=dict(font_id=style['fontId'],language=fmt.property(LANGUAGE) or 'language.en',
                                   size=int(style['fontSizeMicroPoints'])/1e6,color=style['color'])
                    inherited.update(values)
                    super().format_range(first,last,**inherited)
                attributes.update(extras)
                applied=self.put_attributes(self.range_cursor(first,last,grapheme=False),attributes,
                                            self._last_format if first==last and values else None)
                if first==last: self.insertion_format=(first,applied)
            if self.editor:
                cursor=self.range_cursor(start,end)
                self.editor.setTextCursor(cursor)
                if start==end:
                    self.editor.setCurrentCharFormat(self.insertion_format[1])
        return dict(revision=self.revision)

    def edit(self,start,end,text):
        if self.composing: raise ValueError('COMPOSITION_ACTIVE')
        before=self.text(); cursor=self.range_cursor(start,end)
        checked_text(before[:scalar_offset(before,start)]+text+before[scalar_offset(before,end):])
        with self.transaction():
            if start==end and self.insertion_format and start==self.insertion_format[0]:
                cursor.insertText(text,self.insertion_format[1])
                self.insertion_format=(cursor.position(),self.insertion_format[1])
            else: cursor.insertText(text)
        if self.editor: self.editor.setTextCursor(cursor)
        return dict(revision=self.revision,caretUtf16=cursor.position())

    def paragraph_format(self,start,end,**values):
        cursor=self.range_cursor(start,end)
        first,last=cursor.selectionStart(),cursor.selectionEnd()
        block=self.doc.findBlock(first)
        with self.transaction():
            while block.isValid() and (block.position()<last or block.position()==first or first==last):
                bf=block.blockFormat()
                if 'alignment' in values: bf.setAlignment(ALIGNMENTS[values['alignment']])
                if 'before' in values: bf.setTopMargin(values['before']*SCALE)
                if 'after' in values: bf.setBottomMargin(values['after']*SCALE)
                if 'lineHeight' in values:
                    line=values['lineHeight']
                    modes={'multiple':QTextBlockFormat.LineHeightTypes.ProportionalHeight,'exact':QTextBlockFormat.LineHeightTypes.FixedHeight,
                           'at-least':QTextBlockFormat.LineHeightTypes.MinimumHeight}
                    bf.setLineHeight(line['value']*(100 if line['mode']=='multiple' else SCALE),modes[line['mode']].value)
                if 'tabs' in values:
                    tabs=[]
                    for position in values['tabs']:
                        tab=QTextOption.Tab(); tab.position=position*SCALE; tab.type=QTextOption.TabType.LeftTab; tabs.append(tab)
                    bf.setTabPositions(tabs)
                QTextCursor(block).setBlockFormat(bf)
                if first==last: break
                block=block.next()
        return dict(revision=self.revision)
