"""Native M4 controls. Every action uses the same guarded API as MCP clients."""
from PySide6.QtWidgets import QLabel,QLineEdit,QFileDialog,QApplication,QComboBox,QCheckBox
from .workbench_window import WorkbenchWindow
from .paint import DEFAULT


class StudioWindow(WorkbenchWindow):
    def __init__(self,book,api):
        self.paint_controls={}
        super().__init__(book,api)
        for label in self.findChildren(QLabel):
            if label.text()=='TYPESETTING  /  M3': label.setText('GLYPH STUDIO  /  M4')
            if 'M3 does not paint' in label.text(): label.setText('M4 includes actual decorative extents in effect bounds. Extra manual reserves still describe unpainted space. Use effect bounds to check glow clearance.')
        form=self.add_scroll_tab('Paint')
        self.note(form,'Individual Glyphs uses Thimfora 79 (outline), 81 (interior) and 80 (glow) at one shared origin. Choose Thimfora 79 in Text to apply this treatment.')
        form.addRow(self.button('Apply three-font treatment',self.bind_selected))
        form.addRow(self.button('Apply Roman bevel and glow',self.bind_roman))
        self.note(form,'Roman readings use their own archived blue bevel and glow. The palette and lighting controls below adjust the script treatment.')
        form.addRow(self.button('Disable relief on selected font',lambda:self.bind_selected(False)))
        control=self.combo(['individual-glyphs-1','legacy-1']);form.addRow('Lighting profile',control);self.paint_controls['lightingModel']=control
        control=QCheckBox('Use each glyph’s reference gradient');control.setChecked(True);form.addRow(control);self.paint_controls['referenceGradients']=control
        self.note(form,'Uncheck reference gradients to use custom interior colors below. Reference choices are recorded in glyph and layout diagnostics.')
        for key in ('rim','highlight','recess','recessTop','recessBottom','edge','glow'):
            control=QLineEdit(DEFAULT[key]);form.addRow(key.capitalize(),control);self.paint_controls[key]=control
        for key,label,low,high in [('bevel','Bevel · em',.001,.1),('depth','Relief depth',.1,8),('edgeWidth','Edge · em',0,.02),
                                  ('interiorBevel','Interior bevel · em',.001,.15),('normalSmoothing','Normal smoothing · em',0,.01),
                                  ('highlightOpacity','Bevel highlight opacity',0,1),('bevelShadowOpacity','Bevel shadow opacity',0,1),
                                  ('glowRadius','Glow sigma · em',0,.08),('glowOpacity','Glow opacity',0,1),
                                  ('glowRange','Glow range',.01,1),('glowSpread','Glow spread · em',0,.02),
                                  ('shadowRadius','Shadow sigma · em',0,.08),('shadowX','Shadow X · em',-.1,.1),('shadowY','Shadow Y · em',-.1,.1),
                                  ('shadowOpacity','Shadow opacity',0,1),('lightAzimuth','Light angle',0,360),('lightElevation','Light elevation',5,85),('gradient','Vertical gradient',0,1)]:
            control=self.spin(label,DEFAULT[key],low,high,6);form.addRow(label,control);self.paint_controls[key]=control
        form.addRow(self.button('Apply lighting and palette',self.apply_paint))
        form.addRow(self.button('Restore Individual Glyphs recipe',lambda:self.invoke('paint.configure',**{k:v for k,v in DEFAULT.items() if k not in ('recipeId','revision','version')})))
        form.addRow(self.button('Inspect recipe and bindings',lambda:self.show_result('paint.read')))
        form=self.add_scroll_tab('Publish')
        self.note(form,'Decorative PDF and SVG proofs rasterize at the selected DPI. They do not contain searchable text. Keep the native document for editing, copying and search.')
        self.paper=self.combo(['White','Black','Transparent']);form.addRow('Page background',self.paper)
        self.proof_dpi=self.spin('Export DPI',300,72,600,0);form.addRow('Raster DPI',self.proof_dpi)
        form.addRow(self.button('Apply page background',lambda:self.invoke('publication.configure',background={'White':'#FFFFFFFF','Black':'#FF000000','Transparent':'#00000000'}[self.paper.currentText()],rasterDpi=int(self.proof_dpi.value()))))
        form.addRow(self.button('Preflight all pages',lambda:self.show_result('publication.preflight',format='pdf',mode=self.book.view['mode'],dpi=int(self.proof_dpi.value()),raster_policy='raster')))
        for kind in ('png','svg','pdf'): form.addRow(self.button('Export '+kind.upper()+(' · all pages' if kind=='pdf' else ' · current page'),lambda k=kind:self.export_proof(k)))
        self.note(form,'The COLR v0 font is an explicit flat-color fallback. Lighting and glow remain available in the editor and raster proofs.')
        form.addRow(self.button('Build flat COLR font',self.build_font))
        view_menu=self.menuBar().addMenu('View')
        view_menu.addAction('Page focus').triggered.connect(lambda:self.invoke('ui.workspace',source=False,diagnostics=False,guides=False,fit_page=True))
        view_menu.addAction('Edit with diagnostics').triggered.connect(lambda:self.invoke('ui.workspace',source=True,diagnostics=True,guides=True,fit_page=True))
        for label in ('Paint','Publish'):
            view_menu.addAction(label+' controls').triggered.connect(lambda checked=False,name=label:self.invoke('ui.workspace',panel=name))
        self.mode.setItemText(0,'Color / relief')
        self.refresh()

    def workspace_state(self):
        return dict(source=not self.editor.parentWidget().isHidden(),diagnostics=not self.inspection.isHidden(),guides=getattr(self.preview,'guides',True),panel=self.sidebar.tabText(self.sidebar.currentIndex()))

    def configure_workspace(self,source=None,diagnostics=None,guides=None,fit_page=False,panel=None):
        if source is not None: self.editor.parentWidget().setVisible(source)
        if diagnostics is not None: self.inspection.setVisible(diagnostics)
        if guides is not None: self.preview.guides=guides;self.preview.viewport().update()
        if panel is not None:
            index=next(i for i in range(self.sidebar.count()) if self.sidebar.tabText(i)==panel)
            self.sidebar.setCurrentIndex(index)
        if fit_page:
            self.centralWidget().layout().activate();QApplication.processEvents()
            area=self.preview.display_rect();viewport=self.preview.viewport()
            zoom=max(.1,min(3,(viewport.width()-56)/area.width(),(viewport.height()-56)/area.height()))
            self.invoke('view.configure',zoom=int(zoom*100)/100)
        return self.workspace_state()

    def refresh(self):
        super().refresh()
        self.setWindowTitle(self.windowTitle().replace('M3','M4').replace('0.4.0',self.book.application_version))
        if not self.paint_controls: return
        for key,control in self.paint_controls.items():
            if control.hasFocus(): continue
            value=self.book.state['paint']['recipe'].get(key,'legacy-1' if key=='lightingModel' else DEFAULT[key])
            if isinstance(control,QComboBox): control.setCurrentText(value)
            elif isinstance(control,QCheckBox): control.setChecked(value)
            elif isinstance(control,QLineEdit): control.setText(value)
            else: control.setValue(value)

    def bind_selected(self,enabled=True):
        fid=self.font_choice.currentData()
        if not fid:
            self.statusBar().showMessage('Select a loaded TTF in the Text tab first.',10000);return
        old=next((b for b in self.book.state['paint']['bindings'] if b['fontId']==fid),None)
        if old and (old['kind']=='layered' or old.get('profile') or not enabled): return self.invoke('paint.bind',**dict(old,enabled=enabled))
        recipe=self.book.fonts.recipe
        if recipe and fid==recipe['master']:
            binding=dict(fontId=fid,kind='layered',glowFontId=recipe['layers'][0]['fontId'],interiorFontId=recipe['layers'][1]['fontId'],enabled=enabled)
        else:
            self.statusBar().showMessage('Select Thimfora 79 in Text. Single-font relief cannot recreate the three-font artwork.',15000);return
        self.invoke('paint.bind',**binding)

    def bind_roman(self):
        from .reading import ROMAN_SHA,roman_binding
        fid='font:'+ROMAN_SHA+':0'
        if fid not in {f['fontId'] for f in self.book.state['fontSources']}:
            self.statusBar().showMessage('Create a Transliteration 7 reading copy first.',10000);return
        self.invoke('paint.bind',**roman_binding(fid))

    def apply_paint(self):
        self.invoke('paint.configure',**{k:c.currentText() if isinstance(c,QComboBox) else c.isChecked() if isinstance(c,QCheckBox) else c.text() if isinstance(c,QLineEdit) else c.value() for k,c in self.paint_controls.items()})

    def export_proof(self,kind):
        from .proof_names import suggested_proof_path
        path,_=QFileDialog.getSaveFileName(self,'Export '+kind.upper()+' proof',suggested_proof_path(self.book,kind),kind.upper()+' (*.'+kind+')')
        if path:
            args=dict(path=path,format=kind,mode=self.book.view['mode'],dpi=int(self.proof_dpi.value()),raster_policy='raster')
            if kind!='pdf': args['page_id']=self.book.current_page()['pageId']
            self.show_result('publication.export',**args)

    def build_font(self):
        fid=self.font_choice.currentData()
        if not fid: return
        path,_=QFileDialog.getSaveFileName(self,'Build flat COLR font',str(self.book.root/'.local/color-font.ttf'),'TrueType (*.ttf)')
        if path: self.show_result('font.build',font_id=fid,path=path,treatment='flat-colr-v0')
