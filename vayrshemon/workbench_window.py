"""M3 desktop controls use exactly the same commands as CLI and MCP clients."""
import json
from copy import deepcopy
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel,QCheckBox,QComboBox,QLineEdit,QListWidget,QListWidgetItem,QAbstractItemView,QPlainTextEdit
from .editor_window import EditorWindow
from .typesetting_contracts import settings,profile
from .typesetting import boundaries,slice16


class WorkbenchWindow(EditorWindow):
    def __init__(self,book,api):
        self._workbench_signature=None
        super().__init__(book,api)
        for label in self.findChildren(QLabel):
            if label.text()=='AUTHORING  /  M2': label.setText('TYPESETTING  /  M3')
            if label.text().startswith('Frames are independent.'):
                label.setText('Frames can be linked in the Flow tab. Overflow keeps all source text; page export clips at the page edge.')
        self.build_typesetting_tab(); self.build_flow_tab(); self.build_breaks_tab(); self.build_pairs_tab()
        self.editor.cursorPositionChanged.connect(self.sync_rules)
        self.workbench_output=QPlainTextEdit(); self.workbench_output.setReadOnly(True)
        self.inspection.addTab(self.workbench_output,'Typesetting decisions')
        self.refresh()

    def note(self,form,text):
        label=QLabel(text); label.setWordWrap(True); form.addRow(label)

    def combo(self,values):
        control=QComboBox(); control.addItems(values); return control

    def build_typesetting_tab(self):
        form=self.add_scroll_tab('Typeset')
        self.typeset_enabled=QCheckBox('Enable derived page layout'); form.addRow(self.typeset_enabled)
        self.distribution=self.combo(['after','split','before']); form.addRow('Extra leading',self.distribution)
        self.grid_enabled=QCheckBox('Snap baselines to page grid'); form.addRow(self.grid_enabled)
        self.grid_step=self.spin('Baseline grid step',12,.01,1000); self.grid_offset=self.spin('Baseline grid offset',0,0,10000)
        form.addRow('Grid step · pt',self.grid_step); form.addRow('Grid offset · pt',self.grid_offset)
        form.addRow(self.button('Apply layout policy',self.apply_typesetting))
        self.policy=self.combo(['warn','allow','repair']); form.addRow('Collision policy',self.policy)
        self.clearance=self.spin('Minimum clearance',0,0,100); self.expansion=self.spin('Maximum added leading',72,0,1000)
        self.iterations=self.spin('Maximum repair iterations',8,1,16,0)
        form.addRow('Clearance · pt',self.clearance); form.addRow('Expansion budget · pt',self.expansion); form.addRow('Iterations',self.iterations)
        self.fixed_frame=QCheckBox('Repair must fit existing frames'); form.addRow(self.fixed_frame)
        self.bound_kind=self.combo(['ink','stroke','effect']); form.addRow('Collision bounds',self.bound_kind)
        self.stroke=self.spin('Reserved stroke width',0,0,100); self.effect=self.spin('Reserved effect padding',0,0,100)
        form.addRow('Stroke reserve · pt',self.stroke); form.addRow('Effect reserve · pt',self.effect)
        self.note(form,'Repair adds bounded vertical leading. Source text and font sizes stay fixed. Stroke and effect reserves describe space only; M3 does not paint decorative effects.')
        form.addRow(self.button('Apply collision policy',self.apply_collision))
        form.addRow(self.button('Inspect before / after',lambda:self.show_result('collision.inspect')))

    def build_flow_tab(self):
        form=self.add_scroll_tab('Flow')
        self.keep_next=QCheckBox('Keep paragraph with next'); self.keep_together=QCheckBox('Keep paragraph together')
        form.addRow(self.keep_next); form.addRow(self.keep_together)
        self.widows=self.spin('Minimum final lines',2,1,20,0); self.orphans=self.spin('Minimum initial lines',2,1,20,0)
        form.addRow('Widows',self.widows); form.addRow('Orphans',self.orphans)
        form.addRow(self.button('Apply to selected paragraphs',lambda:self.invoke('paragraph.rules',**self.selected_range(),keepWithNext=self.keep_next.isChecked(),keepTogether=self.keep_together.isChecked(),widows=int(self.widows.value()),orphans=int(self.orphans.value()))))
        self.note(form,'Select empty frames of the same width, in document order. All text stays in the source frame. The preview flows it across the linked frames.')
        self.flow_targets=QListWidget(); self.flow_targets.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection); form.addRow(self.flow_targets)
        form.addRow(self.button('Link selected frames',lambda:self.invoke('flow.set',source_frame_id=self.source_id(),targets=[self.flow_targets.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.flow_targets.count()) if self.flow_targets.item(i).isSelected()])))
        form.addRow(self.button('Unlink continuation frames',lambda:self.invoke('flow.set',source_frame_id=self.source_id(),targets=[])))
        form.addRow(self.button('Edit story source',lambda:self.invoke('frame.select',frame_id=self.source_id())))

    def build_breaks_tab(self):
        form=self.add_scroll_tab('Breaks')
        self.break_language=self.combo(['language.en','language.vayrshemon','language.und'])
        self.break_language.currentTextChanged.connect(self.sync_profile); form.addRow('Language',self.break_language)
        self.wrap=self.combo(['word','grapheme','none']); form.addRow('Wrap',self.wrap)
        self.emergency=QCheckBox('Emergency break at grapheme boundaries'); form.addRow(self.emergency)
        self.break_after=QLineEdit(); self.prohibit_before=QLineEdit(); self.prohibit_after=QLineEdit()
        form.addRow('Allow after characters',self.break_after); form.addRow('Prohibit before',self.prohibit_before); form.addRow('Prohibit after',self.prohibit_after)
        self.profile_revision=QLabel(); form.addRow(self.profile_revision)
        form.addRow(self.button('Save next profile revision',self.apply_profile))
        form.addRow(self.button('Inspect break opportunities',lambda:self.show_result('breaks.inspect')))
        for title,kind in [('Insert soft hyphen','soft-hyphen'),('Insert forced line break','line-separator'),('Insert zero-width break','zero-width-space')]:
            form.addRow(self.button(title,lambda k=kind:self.invoke('breaks.insert',offset=self.editor.textCursor().position(),kind=k)))
        self.note(form,'Unicode line breaks come from pinned Qt 6.8.3. Tailoring is versioned in the document. Hyphenation is manual; inserted controls are real source characters.')

    def build_pairs_tab(self):
        form=self.add_scroll_tab('Pairs')
        self.pair_text=QLineEdit('AV'); self.pair_delta=self.spin('Optical pair adjustment',0,-20,20)
        form.addRow('Two graphemes',self.pair_text); form.addRow('Optical delta · pt',self.pair_delta)
        self.note(form,'Uses the font, language and size selected in Text. Explicit pair adjustments are separate from the font’s kern feature.')
        form.addRow(self.button('Compare kern / optical',lambda:self.show_result('pairs.inspect',text=self.pair_text.text(),font_id=self.font_choice.currentData(),language=self.language.currentData(),size=self.font_size.value(),delta=self.pair_delta.value())))
        self.independent_legacy=QCheckBox('These legacy symbols are independent'); form.addRow(self.independent_legacy)
        form.addRow(self.button('Store explicit pair rule',self.apply_pair))
        form.addRow(self.button('Clear pair rules',lambda:self.invoke('optical.set',rules=[])))
        self.specimen_symbols=QLineEdit('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'); form.addRow('Specimen symbols',self.specimen_symbols)
        form.addRow(self.button('Create dense specimen page',lambda:self.invoke('specimen.create',symbols=self.specimen_symbols.text(),font_id=self.font_choice.currentData(),language=self.language.currentData(),size=self.font_size.value())))

    def source_id(self): return self.book.source_for(self.book.state['activeFrameId'])

    def sync_rules(self):
        if not hasattr(self,'keep_next'): return
        from .session import BLOCK
        block=self.editor.textCursor().block()
        bid=getattr(block.userData(),'identity',None) or block.blockFormat().property(BLOCK)
        config=self.book.state['typesetting']['frames'].get(self.source_id(),settings())
        rule=next((r for r in config['paragraphs'] if r['blockId']==bid),dict(keepWithNext=False,keepTogether=False,widows=1,orphans=1))
        self.keep_next.setChecked(rule['keepWithNext']); self.keep_together.setChecked(rule['keepTogether']); self.widows.setValue(rule['widows']); self.orphans.setValue(rule['orphans'])

    def apply_typesetting(self):
        self.invoke('typesetting.configure',enabled=self.typeset_enabled.isChecked(),leadingDistribution=self.distribution.currentText(),grid=dict(enabled=self.grid_enabled.isChecked(),step=self.grid_step.value(),offset=self.grid_offset.value()))

    def apply_collision(self):
        self.invoke('collision.configure',mode=self.policy.currentText(),clearance=self.clearance.value(),maximumExpansion=self.expansion.value(),iterations=int(self.iterations.value()),fixedFrame=self.fixed_frame.isChecked(),bounds=self.bound_kind.currentText(),strokeWidth=self.stroke.value(),effectPadding=self.effect.value())

    def show_result(self,method,**params):
        result=self.invoke(method,**params)
        if result is not None: self.workbench_output.setPlainText(json.dumps(result,ensure_ascii=False,indent=2)); self.inspection.setCurrentWidget(self.workbench_output)

    def sync_profile(self):
        if not hasattr(self,'wrap'): return
        p=next((p for p in self.book.state['typesetting']['profiles'] if p['languageId']==self.break_language.currentText()),profile(self.break_language.currentText()))
        self.wrap.setCurrentText(p['wrap']); self.emergency.setChecked(p['emergency'])
        self.break_after.setText(p['breakAfter']); self.prohibit_before.setText(p['prohibitBefore']); self.prohibit_after.setText(p['prohibitAfter'])
        self.profile_revision.setText('Current revision '+str(p['revision'])+' · manual hyphenation')

    def apply_profile(self):
        p=profile(self.break_language.currentText()); old=next((p for p in self.book.state['typesetting']['profiles'] if p['languageId']==self.break_language.currentText()),None)
        p.update(revision=old['revision']+1 if old else 1,wrap=self.wrap.currentText(),emergency=self.emergency.isChecked(),breakAfter=self.break_after.text(),prohibitBefore=self.prohibit_before.text(),prohibitAfter=self.prohibit_after.text())
        self.invoke('breaks.profile',**p)

    def apply_pair(self):
        text=self.pair_text.text(); offsets=boundaries(text)
        if len(offsets)!=3: raise ValueError('Pair must contain exactly two graphemes')
        left,right=slice16(text,0,offsets[1]),slice16(text,offsets[1],offsets[2]); font=self.font_choice.currentData()
        rules=deepcopy(self.book.state['typesetting']['frames'].get(self.source_id(),settings())['optical'])
        rules=[r for r in rules if (r['left'],r['right'],r['fontId'])!=(left,right,font)]
        rules.append(dict(left=left,right=right,fontId=font,delta=self.pair_delta.value(),independentLegacy=self.independent_legacy.isChecked()))
        self.invoke('optical.set',rules=rules)

    def refresh(self):
        super().refresh()
        self.setWindowTitle(self.windowTitle().replace('M2 / 0.3.0','M3 / 0.4.0'))
        if not hasattr(self,'workbench_output'): return
        source=self.source_id(); target=source!=self.book.state['activeFrameId']
        self.editor.setReadOnly(target)
        self.frame_heading.setText('CONTINUATION · select “Edit story source” in Flow' if target else 'SOURCE TEXT · typeset page shown at right')
        spec=self.book.state['typesetting']; signature=json.dumps([source,self.book.state['activeFrameId'],spec,self._tree_signature],sort_keys=True)
        if signature==self._workbench_signature: return
        config=spec['frames'].get(source,settings()); c=config['collision']; g=config['grid']
        self.typeset_enabled.setChecked(source in spec['frames'] and config['enabled']); self.distribution.setCurrentText(config['leadingDistribution'])
        self.grid_enabled.setChecked(g['enabled']); self.grid_step.setValue(g['step']); self.grid_offset.setValue(g['offset'])
        self.policy.setCurrentText(c['mode']); self.clearance.setValue(c['clearance']); self.expansion.setValue(c['maximumExpansion']); self.iterations.setValue(c['iterations'])
        self.fixed_frame.setChecked(c['fixedFrame']); self.bound_kind.setCurrentText(c['bounds']); self.stroke.setValue(c['strokeWidth']); self.effect.setValue(c['effectPadding'])
        selected=next((f['targets'] for f in spec['flows'] if f['source']==source),[]); self.flow_targets.clear()
        for page in self.book.state['pages']:
            for frame in page['frames']:
                if frame['frameId']==source: continue
                item=QListWidgetItem(page['name']+' / '+frame['name']); item.setData(Qt.ItemDataRole.UserRole,frame['frameId']); self.flow_targets.addItem(item); item.setSelected(frame['frameId'] in selected)
        self.sync_profile(); self.sync_rules(); self._workbench_signature=signature
