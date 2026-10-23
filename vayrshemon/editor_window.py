"""Native M2 authoring window with semantic clipboard and a shared page canvas."""
import json
import math
from pathlib import Path
from PySide6.QtCore import Qt,QPointF,QRectF,QTimer,QMimeData
from PySide6.QtGui import QAction,QColor,QKeySequence,QPainter,QPen,QTextCursor
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QSplitter,
    QTabWidget,QTreeWidget,QTreeWidgetItem,QLabel,QLineEdit,QComboBox,QDoubleSpinBox,QPushButton,QCheckBox,
    QSlider,QPlainTextEdit,QFileDialog,QMessageBox,QInputDialog,QAbstractScrollArea,QMenu,QDialog,QDialogButtonBox,QListWidget,QScrollArea)
from .desktop import Editor,accessibility
from .authoring import MIME,point
from .session import SCALE,STYLE,LANGUAGE,utf16_length,scalar_offset
from . import pages


class RichEditor(Editor):
    def __init__(self,book,api):
        super().__init__(book.active)
        self.book,self.api=book,api
        book._editor=self
        self.setAcceptDrops(False)
        self.setAccessibleName('Text in selected frame')

    def execute(self,method,**params):
        result=self.api.call(method,params,expected_revision=self.book.revision,origin='desktop')
        if not result['ok']:
            self.book.log.emit('desktop','EDIT_REJECTED',level='warning',message=result['error']['message'])
            if self.book.window: self.book.window.statusBar().showMessage(result['error']['message'],15000)
        return result

    def keyPressEvent(self,event):
        if event.matches(QKeySequence.StandardKey.Undo): self.execute('history.undo'); return
        if event.matches(QKeySequence.StandardKey.Redo): self.execute('history.redo'); return
        if event.text() and not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if not self.within_document_limit(event.text()): return
        try:
            with self.book.command('Typing'): super().keyPressEvent(event)
        except Exception as error:
            self.book.log.exception('input',error)
            if self.book.window: self.book.window.last_error=str(error)

    def within_document_limit(self,text):
        cursor=self.textCursor(); before=self.book.text()
        removed=scalar_offset(before,cursor.selectionEnd())-scalar_offset(before,cursor.selectionStart())
        if sum(len(frame.text()) for frame in self.book.frames.values())-removed+len(text)>200_000:
            self.book.log.emit('input','INPUT_REJECTED',level='warning',message='DOCUMENT_LIMIT: 200,000 total scalars')
            return False
        return True

    def inputMethodEvent(self,event):
        if not self.within_document_limit(event.commitString()): event.ignore(); return
        try:
            with self.book.command('Input method'): super().inputMethodEvent(event)
        except Exception as error:
            self.book.log.exception('input',error)
            if self.book.window: self.book.window.last_error=str(error)

    def createMimeDataFromSelection(self):
        cursor=self.textCursor()
        fragment=self.book.copy_fragment(cursor.selectionStart(),cursor.selectionEnd())
        mime=QMimeData(); mime.setText(fragment['text'])
        mime.setData(MIME,json.dumps(fragment,ensure_ascii=True,allow_nan=False).encode())
        return mime

    def insertFromMimeData(self,source):
        cursor=self.textCursor()
        try:
            if source.hasFormat(MIME):
                data=bytes(source.data(MIME))
                if len(data)>4*1024*1024: raise ValueError('CLIPBOARD_LIMIT: 4 MiB')
                fragment=json.loads(data)
                self.execute('clipboard.paste',start=cursor.selectionStart(),end=cursor.selectionEnd(),fragment=fragment)
            else:
                raw=source.text(); text=raw.replace('\r\n','\n').replace('\r','\n')
                if raw!=text: self.book.log.emit('clipboard','LINE_ENDINGS_CONVERTED',fromConvention='CR/CRLF',toConvention='LF')
                self.execute('document.edit',start=cursor.selectionStart(),end=cursor.selectionEnd(),text=text)
        except Exception as error:
            self.book.log.exception('clipboard',error)
            if self.book.window: self.book.window.statusBar().showMessage(str(error),15000)

    def contextMenuEvent(self,event):
        menu=QMenu(self)
        for label,callback,enabled in [('Undo',lambda:self.execute('history.undo'),bool(self.book._undo)),
                                       ('Redo',lambda:self.execute('history.redo'),bool(self.book._redo)),
                                       ('Cut',self.cut,self.textCursor().hasSelection()),('Copy',self.copy,self.textCursor().hasSelection()),
                                       ('Paste',self.paste,self.canPaste()),('Select all',self.selectAll,True)]:
            action=menu.addAction(label); action.setEnabled(enabled); action.triggered.connect(callback)
        menu.exec(event.globalPos())


class PageCanvas(QAbstractScrollArea):
    RULER=24

    def __init__(self,book,invoke):
        super().__init__()
        self.book,self.invoke=book,invoke
        self.setAccessibleName('Page preview with point rulers')
        self.setMinimumWidth(330)
        self.setMouseTracking(True)
        self.pan=None
        for bar in (self.horizontalScrollBar(),self.verticalScrollBar()): bar.valueChanged.connect(self.viewport().update)

    def update_page(self):
        area=pages.page_rect(self.book.current_page()); zoom=self.book.view['zoom']
        self.horizontalScrollBar().setRange(0,max(0,math.ceil(area.width()*zoom)+2*self.RULER-self.viewport().width()))
        self.verticalScrollBar().setRange(0,max(0,math.ceil(area.height()*zoom)+2*self.RULER-self.viewport().height()))
        self.horizontalScrollBar().setPageStep(self.viewport().width()); self.verticalScrollBar().setPageStep(self.viewport().height())
        self.viewport().update()

    def resizeEvent(self,event): super().resizeEvent(event); self.update_page()

    def paintEvent(self,event):
        p=QPainter(self.viewport()); p.fillRect(self.viewport().rect(),QColor('#d8dfe5'))
        zoom=self.book.view['zoom']; dx=self.RULER-self.horizontalScrollBar().value(); dy=self.RULER-self.verticalScrollBar().value()
        p.save(); p.translate(dx,dy); p.scale(zoom,zoom)
        clip=QRectF(-dx/zoom,-dy/zoom,self.viewport().width()/zoom,self.viewport().height()/zoom)
        try:
            pages.paint(self.book,p,clip=clip,overlays=self.book.view,guides=True)
        except Exception as error:
            self.book.log.exception('preview',error)
            p.restore(); p.setPen(QColor('#aa263a'))
            p.drawText(self.viewport().rect().adjusted(30,40,-30,-20),Qt.TextFlag.TextWordWrap,'Preview unavailable: '+str(error)+'\nSource text remains editable. Adjust or disable typesetting to continue.')
            p.end(); return
        p.restore()
        p.fillRect(0,0,self.viewport().width(),self.RULER,QColor('#eef2f5'))
        p.fillRect(0,0,self.RULER,self.viewport().height(),QColor('#eef2f5'))
        p.setPen(QColor('#566b7b'))
        spacing=36 if zoom>=.5 else 144
        for horizontal in (True,False):
            maximum=self.viewport().width() if horizontal else self.viewport().height()
            origin=dx if horizontal else dy
            start=max(0,math.floor(-origin/(SCALE*zoom*spacing)))
            for tick in range(start,start+int(maximum/(SCALE*zoom*spacing))+3):
                position=origin+tick*spacing*SCALE*zoom
                if horizontal:
                    p.drawLine(QPointF(position,18),QPointF(position,24)); p.drawText(QPointF(position+2,13),str(tick*spacing))
                else:
                    p.drawLine(QPointF(18,position),QPointF(24,position)); p.save(); p.translate(12,position+2); p.rotate(-90); p.drawText(QPointF(0,0),str(tick*spacing)); p.restore()
        p.fillRect(0,0,24,24,QColor('#eef2f5')); p.drawText(QPointF(3,16),'pt'); p.end()

    def wheelEvent(self,event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.invoke('view.configure',zoom=max(.1,min(3,round(self.book.view['zoom']+(0.1 if event.angleDelta().y()>0 else -.1),2))))
            event.accept()
        else: super().wheelEvent(event)

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.MiddleButton: self.pan=event.position(); self.setCursor(Qt.CursorShape.ClosedHandCursor); return
        if event.button()==Qt.MouseButton.LeftButton:
            zoom=self.book.view['zoom']
            x=(event.position().x()-self.RULER+self.horizontalScrollBar().value())/zoom
            y=(event.position().y()-self.RULER+self.verticalScrollBar().value())/zoom
            hit=pages.hit_test(self.book,x,y)
            if hit['frameId']:
                self.invoke('selection.set',frame_id=hit['frameId'],start=hit['offset'],end=hit['offset'])
        super().mousePressEvent(event)

    def mouseMoveEvent(self,event):
        if self.pan is not None:
            delta=event.position()-self.pan; self.pan=event.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()-round(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value()-round(delta.y()))
        else: super().mouseMoveEvent(event)

    def mouseReleaseEvent(self,event): self.pan=None; self.unsetCursor(); super().mouseReleaseEvent(event)


class EditorWindow(QMainWindow):
    def __init__(self,book,api):
        super().__init__()
        self.book,self.api=book,api; book.window=self
        self.setWindowTitle('Vayrshemon — M2 Authoring / 0.3.0')
        self.resize(1540,1000); self.setMinimumSize(1100,740)
        self.setStyleSheet('''QMainWindow {background:#e8edf2;} QWidget {font-family:"Segoe UI";font-size:10pt;}
            QPushButton {padding:5px 9px;} QLineEdit,QComboBox,QDoubleSpinBox {min-height:24px;}
            QLabel#heading {color:#17354c;font-size:17pt;font-weight:600;} QStatusBar {background:#17354c;color:white;}
            QTreeWidget {border:0;background:#f4f7f9;} QTabWidget::pane {border:1px solid #c6d1db;}
        ''')
        self._tree_signature=None; self._layout_signature=None; self._font_signature=None
        self.last_error=None
        self.actions={}
        self.build_menu()
        central=QWidget(); column=QVBoxLayout(central); column.setContentsMargins(12,10,12,8)
        top=QHBoxLayout(); brand=QLabel('Vayrshemon'); brand.setObjectName('heading'); top.addWidget(brand)
        top.addWidget(QLabel('AUTHORING  /  M2')); top.addStretch()
        for title,callback in [('New',self.new_file),('Open',self.open_file),('Save',self.save_file),('Save as',self.save_as),
                               ('Undo',lambda:self.invoke('history.undo')),('Redo',lambda:self.invoke('history.redo')),('Find / replace',self.find_dialog)]:
            top.addWidget(self.button(title,callback))
        column.addLayout(top)
        split=QSplitter(Qt.Orientation.Horizontal)
        self.sidebar=QTabWidget(); self.sidebar.setMinimumWidth(280); self.sidebar.setMaximumWidth(390)
        self.build_document_tab(); self.build_layout_tab(); self.build_text_tab(); self.build_color_tab()
        split.addWidget(self.sidebar)
        edit_box=QWidget(); edit_column=QVBoxLayout(edit_box); edit_column.setContentsMargins(2,0,2,0)
        self.frame_heading=QLabel('EDIT FRAME · 100%'); edit_column.addWidget(self.frame_heading)
        self.editor=RichEditor(book,api); edit_column.addWidget(self.editor)
        self.editor.cursorPositionChanged.connect(self.sync_text_controls)
        split.addWidget(edit_box)
        preview_box=QWidget(); preview_column=QVBoxLayout(preview_box); preview_column.setContentsMargins(2,0,0,0)
        preview_row=QHBoxLayout(); preview_row.addWidget(QLabel('PAGE PREVIEW · click a frame to edit'))
        self.mode=QComboBox(); self.mode.addItem('Color layers','color'); self.mode.addItem('Monochrome','mono')
        self.mode.currentIndexChanged.connect(lambda:self.invoke('view.configure',mode=self.mode.currentData()))
        preview_row.addWidget(self.mode); preview_column.addLayout(preview_row)
        self.preview=PageCanvas(book,self.invoke); preview_column.addWidget(self.preview)
        zoom_row=QHBoxLayout(); self.zoom_label=QLabel('80%'); self.zoom=QSlider(Qt.Orientation.Horizontal)
        self.zoom.setRange(10,300); self.zoom.setValue(80); self.zoom.setTracking(False); self.zoom.setAccessibleName('Page preview zoom percent')
        self.zoom.valueChanged.connect(lambda value:self.invoke('view.configure',zoom=value/100))
        zoom_row.addWidget(self.zoom_label); zoom_row.addWidget(self.zoom); zoom_row.addWidget(self.button('PNG',self.export_png)); zoom_row.addWidget(self.button('SVG proof',self.export_svg))
        preview_column.addLayout(zoom_row); split.addWidget(preview_box); split.setSizes([300,510,700]); column.addWidget(split,1)
        self.inspection=QTabWidget(); self.inspection.setMaximumHeight(220); self.inspection.setMinimumHeight(130)
        self.details=QPlainTextEdit(); self.logs=QPlainTextEdit(); self.access=QPlainTextEdit()
        for name,widget in [('Page / glyph inspector',self.details),('Diagnostics / recovery',self.logs),('Accessibility',self.access)]:
            widget.setReadOnly(True); self.inspection.addTab(widget,name)
        column.addWidget(self.inspection)
        self.setCentralWidget(central)
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(120); self.timer.timeout.connect(self.refresh)
        book.changed.connect(self.on_change)
        self.refresh(); self.sync_text_controls()
        if book.recovery_list(): self.statusBar().showMessage('An interrupted session is available. File → Recover interrupted session. Save before replacing current edits.',20000)

    def button(self,text,callback):
        button=QPushButton(text); button.clicked.connect(lambda checked=False:self.guard(callback)); return button

    def spin(self,name,value=0,minimum=0,maximum=1000000,decimals=3):
        control=QDoubleSpinBox(); control.setAccessibleName(name); control.setRange(minimum,maximum); control.setDecimals(decimals); control.setValue(value); return control

    def add_scroll_tab(self,title):
        outer=QScrollArea(); outer.setWidgetResizable(True); container=QWidget(); form=QFormLayout(container)
        form.setContentsMargins(10,10,10,10); outer.setWidget(container); self.sidebar.addTab(outer,title); return form

    def build_menu(self):
        menu=self.menuBar().addMenu('File')
        for text,shortcut,callback in [('New',QKeySequence.StandardKey.New,self.new_file),('Open…',QKeySequence.StandardKey.Open,self.open_file),
                                      ('Save',QKeySequence.StandardKey.Save,self.save_file),('Save as…',QKeySequence.StandardKey.SaveAs,self.save_as)]:
            action=menu.addAction(text); action.setShortcut(shortcut); action.triggered.connect(lambda checked=False,fn=callback:self.guard(fn))
        self.recents=menu.addMenu('Recent documents'); self.recents.aboutToShow.connect(self.populate_recents)
        menu.addAction('Recover interrupted session…',lambda:self.guard(self.recover_dialog))
        menu.addSeparator(); menu.addAction('Export PNG…',lambda:self.guard(self.export_png)); menu.addAction('Export outline SVG…',lambda:self.guard(self.export_svg))
        edit=self.menuBar().addMenu('Edit')
        for name,key,method in [('Undo','Ctrl+Z','history.undo'),('Redo','Ctrl+Y','history.redo')]:
            action=edit.addAction(name); action.setShortcut(key); action.triggered.connect(lambda checked=False,m=method:self.invoke(m))
        action=edit.addAction('Find / replace…'); action.setShortcut(QKeySequence.StandardKey.Find); action.triggered.connect(lambda:self.guard(self.find_dialog))

    def build_document_tab(self):
        form=self.add_scroll_tab('Document')
        self.title_input=QLineEdit(); self.title_input.setAccessibleName('Document title'); form.addRow('Title',self.title_input)
        form.addRow(self.button('Rename',lambda:self.invoke('document.title',title=self.title_input.text())))
        self.tree=QTreeWidget(); self.tree.setHeaderHidden(True); self.tree.setMinimumHeight(230); self.tree.setAccessibleName('Pages and text frames')
        self.tree.itemClicked.connect(self.select_tree); form.addRow(self.tree)
        form.addRow(self.button('Add page',lambda:self.invoke('page.add',width=point(self.book.current_page()['width']),height=point(self.book.current_page()['height']))))
        form.addRow(self.button('Delete selected page',self.delete_page))
        form.addRow(self.button('Add text frame',lambda:self.invoke('frame.add')))
        form.addRow(self.button('Delete selected frame',self.delete_frame))
        self.document_info=QLabel(); self.document_info.setWordWrap(True); form.addRow(self.document_info)
        form.addRow(self.button('Recover interrupted session…',self.recover_dialog))

    def build_layout_tab(self):
        form=self.add_scroll_tab('Layout')
        self.page_width=self.spin('Page width',612,minimum=.001); self.page_height=self.spin('Page height',792,minimum=.001)
        self.units=QComboBox(); self.units.addItems(['pt','mm','in']); self._previous_unit='pt'
        self.units.currentTextChanged.connect(self.convert_units)
        form.addRow('Page units',self.units); form.addRow('Width',self.page_width); form.addRow('Height',self.page_height)
        self.margin_inputs={side:self.spin('Page '+side+' margin',18) for side in ('top','right','bottom','left')}
        for side,control in self.margin_inputs.items(): form.addRow(side.title()+' margin',control)
        form.addRow(self.button('Apply page / margins',self.apply_page))
        form.addRow(QLabel('Selected frame · coordinates in points'))
        self.frame_name=QLineEdit(); form.addRow('Name',self.frame_name)
        self.frame_inputs={key:self.spin('Frame '+key,0,minimum=.001 if key in ('width','height') else 0) for key in ('x','y','width','height')}
        for key,control in self.frame_inputs.items(): form.addRow(key.title(),control)
        self.overflow=QComboBox(); self.overflow.addItem('Show beyond frame','show'); self.overflow.addItem('Clip to frame','clip'); form.addRow('Overflow',self.overflow)
        form.addRow(self.button('Apply frame',self.apply_frame))
        note=QLabel('Frames are independent. Overflow keeps all text and appears in the inspector. Page export clips at the page edge.'); note.setWordWrap(True); form.addRow(note)

    def build_text_tab(self):
        form=self.add_scroll_tab('Text')
        self.font_choice=QComboBox(); self.font_choice.setAccessibleName('Font file'); form.addRow('Font',self.font_choice)
        form.addRow(self.button('Load TTF…',self.load_font))
        self.language=QComboBox()
        for label,value in [('English','language.en'),('Vayrshemon','language.vayrshemon'),('Undetermined','language.undetermined')]: self.language.addItem(label,value)
        form.addRow('Language',self.language)
        self.font_size=self.spin('Font size in points',18,1,1000,2); form.addRow('Size · pt',self.font_size)
        self.text_color=QLineEdit('#111827FF'); form.addRow('Color · RRGGBBAA',self.text_color)
        self.tracking=self.spin('Tracking in points',0,-100,100); self.word_spacing=self.spin('Word spacing in points',0,-100,100); self.baseline=self.spin('Baseline offset percent',0,-100,100)
        form.addRow('Tracking · pt',self.tracking); form.addRow('Word spacing · pt',self.word_spacing); form.addRow('Baseline · %',self.baseline)
        form.addRow(self.button('Apply to selection / next input',self.apply_format))
        self.style_choice=QComboBox(); form.addRow('Named style',self.style_choice)
        form.addRow(self.button('Apply named style',self.apply_style)); form.addRow(self.button('Save controls as named style…',self.define_style))
        self.alignment=QComboBox(); self.alignment.addItems(['left','center','right','justify']); form.addRow('Alignment',self.alignment)
        self.leading_mode=QComboBox(); self.leading_mode.addItems(['multiple','exact','at-least']); form.addRow('Line height mode',self.leading_mode)
        self.leading=self.spin('Line height value',1.2,.01,100); form.addRow('Multiple or points',self.leading)
        self.before=self.spin('Paragraph space before',0,0,10000); self.after=self.spin('Paragraph space after',0,0,10000)
        form.addRow('Before · pt',self.before); form.addRow('After · pt',self.after)
        self.tabs_input=QLineEdit(); self.tabs_input.setPlaceholderText('36, 72, 108'); form.addRow('Left tabs · pt',self.tabs_input)
        form.addRow(self.button('Apply paragraph settings',self.apply_paragraph))
        self.kern=QCheckBox('Kerning'); self.liga=QCheckBox('Standard ligatures')
        for key,check in [('kern',self.kern),('liga',self.liga)]:
            check.setChecked(True); check.toggled.connect(lambda enabled,k=key:self.invoke('features.configure',**{k:enabled})); form.addRow(check)

    def build_color_tab(self):
        form=self.add_scroll_tab('Color')
        self.recipe_master=QComboBox(); form.addRow('Master font',self.recipe_master)
        self.recipe_layers=[QComboBox() for _ in range(3)]
        for label,combo in zip(['Base font','Interior font','Outline font'],self.recipe_layers): form.addRow(label,combo)
        form.addRow(self.button('Validate / select layer recipe',self.apply_recipe))
        self.layer_checks=[]; self.layer_colors=[]
        for index,name in enumerate(['Base','Interior','Outline']):
            check=QCheckBox(name); check.toggled.connect(lambda enabled,i=index:self.invoke('view.configure',layer=i,enabled=enabled)); self.layer_checks.append(check)
            color=QLineEdit(); self.layer_colors.append(color); form.addRow(check,color)
        form.addRow(self.button('Apply palette colors',lambda:self.invoke('palette.apply',colors=[c.text() for c in self.layer_colors])))
        palettes=QComboBox(); palettes.addItems(['Blue jewel','Ink','Amber']); form.addRow('Preset palette',palettes)
        colors=[['#43b8a0','#164e78','#78d9f2'],['#111827','#111827','#111827'],['#e4b94f','#92522b','#f7dc91']]
        form.addRow(self.button('Use preset',lambda:self.invoke('palette.apply',colors=colors[palettes.currentIndex()])))
        self.overlay_checks={}
        for name in ('baselines','origins','bounds'):
            check=QCheckBox(name.title()); check.toggled.connect(lambda enabled,k=name:self.invoke('view.configure',**{k:enabled})); self.overlay_checks[name]=check; form.addRow(check)
        label=QLabel('Flat colors stay registered to the master glyph positions. Portable color-font compilation and decorative effects are M4.'); label.setWordWrap(True); form.addRow(label)

    def guard(self,callback):
        try: return callback()
        except Exception as error:
            self.last_error=str(error)
            self.book.log.exception('desktop',error); self.statusBar().showMessage(str(error),20000); return None

    def invoke(self,method,**params):
        result=self.api.call(method,params,expected_revision=self.book.revision,origin='desktop')
        if not result['ok']:
            self.last_error=result['error']['message']
            self.statusBar().showMessage(result['error']['message'],20000)
            return None
        self.last_error=None
        return result['result']

    def on_change(self): self.preview.update_page(); self.timer.start()

    def refresh(self):
        try:
            self.sync_structure()
            report=pages.inspect(self.book,max_glyphs=1200)
            self.details.setPlainText(json.dumps(report,ensure_ascii=False,indent=2))
            self.logs.setPlainText('\n'.join(json.dumps(e,ensure_ascii=False) for e in self.book.log.tail(50)))
            self.access.setPlainText(json.dumps(accessibility(self.editor),ensure_ascii=False,indent=2))
            overflow=sum(1 for f in report['frames'] if f['overflow'])
            title=self.book.state['title']; self.setWindowTitle(title+(' *' if self.book.dirty else '')+' — Vayrshemon M2 / 0.3.0')
            recovery=('RECOVERY ERROR: '+self.book.recovery_error) if self.book.recovery_error else 'Recovery durable through revision '+str(self.book.durable_revision)
            self.statusBar().showMessage(self.last_error or f"Revision {self.book.revision} · {'unsaved' if self.book.dirty else 'saved'} · {overflow} overflowing frame(s) · {recovery}")
        except Exception as error: self.book.log.exception('desktop',error); self.statusBar().showMessage(str(error),20000)

    def sync_structure(self):
        book=self.book; page,frame=book.locate()
        signature=[(p['pageId'],p['name'],[(f['frameId'],f['name']) for f in p['frames']]) for p in book.state['pages']]
        if signature!=self._tree_signature:
            self.tree.blockSignals(True); self.tree.clear()
            for index,p in enumerate(book.state['pages']):
                item=QTreeWidgetItem([f"{index+1}. {p['name']}"]); item.setData(0,Qt.ItemDataRole.UserRole,p['frames'][0]['frameId']); self.tree.addTopLevelItem(item)
                for f in p['frames']:
                    child=QTreeWidgetItem([f['name']]); child.setData(0,Qt.ItemDataRole.UserRole,f['frameId']); item.addChild(child)
                    if f['frameId']==book.state['activeFrameId']: self.tree.setCurrentItem(child)
                item.setExpanded(True)
            self.tree.blockSignals(False); self._tree_signature=signature
        for index in range(self.tree.topLevelItemCount()):
            item=self.tree.topLevelItem(index)
            for child_index in range(item.childCount()):
                child=item.child(child_index)
                if child.data(0,Qt.ItemDataRole.UserRole)==book.state['activeFrameId']: self.tree.setCurrentItem(child)
        layout_signature=(json.dumps({k:v for k,v in page.items() if k!='frames'},sort_keys=True),json.dumps({k:v for k,v in frame.items() if k!='content'},sort_keys=True))
        if layout_signature!=self._layout_signature:
            self.units.blockSignals(True); self.units.setCurrentText('pt'); self.units.blockSignals(False); self._previous_unit='pt'
            self.page_width.setValue(point(page['width'])); self.page_height.setValue(point(page['height']))
            for key,control in self.margin_inputs.items(): control.setValue(point(page['margins'][key]))
            for key,control in self.frame_inputs.items(): control.setValue(point(frame[key]))
            self.frame_name.setText(frame['name']); self.overflow.setCurrentIndex(self.overflow.findData(frame['overflow']))
            self._layout_signature=layout_signature
        if not self.title_input.hasFocus(): self.title_input.setText(book.state['title'])
        self.frame_heading.setText('EDIT · '+frame['name']+' · 100%')
        self.document_info.setText(f"{len(book.state['pages'])} page(s) · {len(book.frames)} frame(s)\n"+(str(book.saved_path) if book.saved_path else 'Unsaved document'))
        fonts=tuple(book.fonts.faces)
        if fonts!=self._font_signature:
            for combo in [self.font_choice,self.recipe_master,*self.recipe_layers]:
                selected=combo.currentData(); combo.blockSignals(True); combo.clear()
                if combo is self.font_choice: combo.addItem('System English font',None)
                for face in book.fonts.faces.values(): combo.addItem(face.path.stem+' · '+face.sha256[:6],face.font_id)
                combo.setCurrentIndex(max(0,combo.findData(selected))); combo.blockSignals(False)
            self._font_signature=fonts
        self.mode.blockSignals(True); self.mode.setCurrentIndex(self.mode.findData(book.view['mode'])); self.mode.blockSignals(False)
        self.zoom.blockSignals(True); self.zoom.setValue(round(book.view['zoom']*100)); self.zoom.blockSignals(False); self.zoom_label.setText(str(round(book.view['zoom']*100))+'%')
        for key,check in [*self.overlay_checks.items(),('kern',self.kern),('liga',self.liga)]:
            check.blockSignals(True); check.setChecked(book.features[key] if key in ('kern','liga') else book.view[key]); check.blockSignals(False)
        recipe=book.fonts.recipe
        for index,check in enumerate(self.layer_checks):
            check.blockSignals(True); check.setEnabled(bool(recipe)); check.setChecked(bool(recipe and recipe['layers'][index]['enabled'])); check.blockSignals(False)
            if recipe:
                if not self.layer_colors[index].hasFocus(): self.layer_colors[index].setText(recipe['layers'][index]['color'])
                self.recipe_layers[index].setCurrentIndex(self.recipe_layers[index].findData(recipe['layers'][index]['fontId']))
        if recipe: self.recipe_master.setCurrentIndex(self.recipe_master.findData(recipe['master']))
        selected=self.style_choice.currentText(); self.style_choice.clear(); self.style_choice.addItems([s['name'] for s in book.state['styles']]); self.style_choice.setCurrentText(selected)
        self.preview.update_page()

    def sync_text_controls(self):
        if not hasattr(self,'editor'): return
        fmt=self.editor.textCursor().charFormat(); sid=fmt.property(STYLE)
        style=next((s for s in self.book.model['styles'] if s['styleId']==sid),self.book.model['styles'][0])
        self.font_choice.setCurrentIndex(max(0,self.font_choice.findData(style['fontId'])))
        self.font_size.setValue(point(style['fontSizeMicroPoints'])); self.text_color.setText(style['color'])
        self.language.setCurrentIndex(max(0,self.language.findData(fmt.property(LANGUAGE))))
        attrs=self.book.active.attributes(fmt); self.tracking.setValue(attrs['tracking']); self.word_spacing.setValue(attrs['wordSpacing']); self.baseline.setValue(attrs['baseline'])
        bf=self.editor.textCursor().blockFormat()
        from .frame import ALIGNMENTS
        self.alignment.setCurrentText(next((key for key,val in ALIGNMENTS.items() if bf.alignment() & val),'left'))
        self.before.setValue(bf.topMargin()/SCALE); self.after.setValue(bf.bottomMargin()/SCALE); self.tabs_input.setText(', '.join(f'{t.position/SCALE:g}' for t in bf.tabPositions()))
        from PySide6.QtGui import QTextBlockFormat
        modes={QTextBlockFormat.LineHeightTypes.ProportionalHeight.value:'multiple',QTextBlockFormat.LineHeightTypes.FixedHeight.value:'exact',QTextBlockFormat.LineHeightTypes.MinimumHeight.value:'at-least'}
        mode=modes.get(bf.lineHeightType(),'multiple'); self.leading_mode.setCurrentText(mode); self.leading.setValue(bf.lineHeight()/(100 if mode=='multiple' else SCALE) or 1)

    def selected_range(self):
        c=self.editor.textCursor(); return dict(start=c.selectionStart(),end=c.selectionEnd())

    def format_values(self):
        return dict(font_id=self.font_choice.currentData(),language=self.language.currentData(),size=self.font_size.value(),color=self.text_color.text(),
                    tracking=self.tracking.value(),wordSpacing=self.word_spacing.value(),baseline=self.baseline.value())

    def apply_format(self): self.invoke('document.format',**self.selected_range(),**self.format_values()); self.editor.setFocus()
    def apply_paragraph(self):
        tabs=[float(v.strip()) for v in self.tabs_input.text().split(',') if v.strip()]
        self.invoke('paragraph.format',**self.selected_range(),alignment=self.alignment.currentText(),before=self.before.value(),after=self.after.value(),
                    tabs=tabs,lineHeight=dict(mode=self.leading_mode.currentText(),value=self.leading.value()))
        self.editor.setFocus()
    def apply_style(self): self.invoke('styles.apply',**self.selected_range(),name=self.style_choice.currentText())
    def define_style(self):
        name,ok=QInputDialog.getText(self,'Named style','Style name')
        if ok and name.strip(): self.invoke('styles.define',name=name.strip(),format=self.format_values())
    def apply_page(self): self.invoke('page.configure',width=self.page_width.value(),height=self.page_height.value(),unit=self.units.currentText(),margins={k:c.value() for k,c in self.margin_inputs.items()})
    def apply_frame(self): self.invoke('frame.configure',**{k:c.value() for k,c in self.frame_inputs.items()},name=self.frame_name.text(),overflow=self.overflow.currentData())
    def apply_recipe(self): self.invoke('recipe.configure',master=self.recipe_master.currentData(),layers=[c.currentData() for c in self.recipe_layers])
    def convert_units(self,unit):
        factors={'pt':1,'mm':72/25.4,'in':72}; ratio=factors[self._previous_unit]/factors[unit]
        for control in [self.page_width,self.page_height,*self.margin_inputs.values()]: control.setValue(control.value()*ratio)
        self._previous_unit=unit
    def select_tree(self,item,column): self.invoke('frame.select',frame_id=item.data(0,Qt.ItemDataRole.UserRole)); self.sync_text_controls()

    def confirm_discard(self):
        if not self.book.dirty: return True
        answer=QMessageBox.question(self,'Unsaved document','Save changes before continuing?',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel)
        if answer==QMessageBox.StandardButton.Cancel: return False
        if answer==QMessageBox.StandardButton.Save: self.save_file(); return not self.book.dirty
        return True

    def new_file(self):
        if self.confirm_discard(): self.invoke('document.new',discardUnsaved=True)
    def open_file(self):
        path,_=QFileDialog.getOpenFileName(self,'Open document',str(self.book.root/'.local'),'Vayrshemon (*.vay.json *.vaylab.json)')
        if path: self.open_path(path)
    def open_path(self,path):
        if not self.confirm_discard(): return
        preflight=self.invoke('document.preflight',path=path)
        if preflight is None: return
        replacements={}
        for font in preflight['missingFonts']:
            selected,_=QFileDialog.getOpenFileName(self,'Locate exact font '+font['sha256'][:12],str(Path(font['path']).parent),'TrueType (*.ttf)')
            if not selected: return
            replacements[font['fontId']]=selected
        self.invoke('document.open',path=path,fontPaths=replacements,discardUnsaved=True)
    def save_file(self):
        if self.book.saved_path: self.invoke('document.save',path=str(self.book.saved_path))
        else: self.save_as()
    def save_as(self):
        path,_=QFileDialog.getSaveFileName(self,'Save document as',str(self.book.root/'.local/untitled.vay.json'),'Vayrshemon (*.vay.json)')
        if path:
            if not path.endswith('.vay.json'): path+='.vay.json'
            self.invoke('document.save-as',path=path)
    def populate_recents(self):
        self.recents.clear()
        for value in self.book.recent():
            action=self.recents.addAction(value['title']+' — '+value['path']); action.triggered.connect(lambda checked=False,p=value['path']:self.guard(lambda:self.open_path(p)))
    def delete_page(self):
        if QMessageBox.question(self,'Delete page','Delete this page and its text frames? You can undo this.')==QMessageBox.StandardButton.Yes: self.invoke('page.delete',page_id=self.book.current_page()['pageId'])
    def delete_frame(self):
        if QMessageBox.question(self,'Delete frame','Delete this frame and its text? You can undo this.')==QMessageBox.StandardButton.Yes: self.invoke('frame.delete',frame_id=self.book.state['activeFrameId'])
    def load_font(self):
        path,_=QFileDialog.getOpenFileName(self,'Load font',str(self.book.root/'Inputs'),'TrueType (*.ttf)')
        if path: self.invoke('fonts.load',path=path)
    def export_png(self):
        path,_=QFileDialog.getSaveFileName(self,'Export current page',str(self.book.root/'.local/page.png'),'PNG (*.png)')
        if path: self.invoke('render.png',path=path,dpi=144,mode=self.book.view['mode'])
    def export_svg(self):
        path,_=QFileDialog.getSaveFileName(self,'Export outline SVG proof',str(self.book.root/'.local/page.svg'),'SVG (*.svg)')
        if path: self.invoke('render.svg',path=path,mode=self.book.view['mode'])
    def recover_dialog(self):
        candidates=self.book.recovery_list()
        if not candidates: QMessageBox.information(self,'Recovery','No interrupted, unsaved sessions were found.'); return
        labels=[str(c.get('title','Invalid checkpoint'))+' · '+str(c.get('timestamp',c.get('error'))) for c in candidates]
        label,ok=QInputDialog.getItem(self,'Recover interrupted session','Checkpoint',labels,0,False)
        if ok and self.confirm_discard(): self.invoke('recovery.restore',path=candidates[labels.index(label)]['path'],discardUnsaved=True)
    def find_dialog(self):
        dialog=QDialog(self); dialog.setWindowTitle('Find / replace'); dialog.resize(620,380)
        column=QVBoxLayout(dialog); form=QFormLayout(); needle=QLineEdit(); replacement=QLineEdit(); case=QCheckBox('Case sensitive'); whole=QCheckBox('Whole word')
        form.addRow('Find',needle); form.addRow('Replace with',replacement); form.addRow(case,whole); column.addLayout(form)
        results=QListWidget(); column.addWidget(results); matches=[]
        def find():
            result=self.invoke('document.find',text=needle.text(),case_sensitive=case.isChecked(),whole_word=whole.isChecked())
            results.clear(); matches.clear()
            if result:
                matches.extend(result['matches'])
                for match in matches:
                    page,frame=self.book.locate(match['frameId']); results.addItem(page['name']+' / '+frame['name']+' · '+str(match['start'])+' · '+match['text'])
        def replace():
            result=self.invoke('document.replace',text=needle.text(),replacement=replacement.text(),case_sensitive=case.isChecked(),whole_word=whole.isChecked())
            if result: dialog.setWindowTitle(str(result['replacements'])+' replacements — one undo step'); find()
        def select():
            index=results.currentRow()
            if 0<=index<len(matches): self.invoke('selection.set',frame_id=matches[index]['frameId'],start=matches[index]['start'],end=matches[index]['end'])
        results.itemDoubleClicked.connect(lambda _:select())
        row=QHBoxLayout(); row.addWidget(self.button('Find all',find)); row.addWidget(self.button('Go to match',select)); row.addWidget(self.button('Replace all',replace)); column.addLayout(row)
        dialog.exec()
    def closeEvent(self,event):
        if not self.confirm_discard(): event.ignore(); return
        self.book.finish(); event.accept()
