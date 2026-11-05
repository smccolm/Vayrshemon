"""Compact document numbering dialog, with no permanent reading-toolbar row."""
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QGridLayout,QLabel,QCheckBox,QComboBox,
                              QDoubleSpinBox,QDialogButtonBox,QMenu)
from . import page_numbering


class NumberingDialog(QDialog):
    def __init__(self,window):
        super().__init__(window);self.window=window
        self.setWindowTitle('Page numbering');self.setMinimumWidth(540)
        layout=QVBoxLayout(self);value=page_numbering.settings(window.book)
        self.enabled=QCheckBox('Show page numbers');self.enabled.setChecked(value['enabled']);layout.addWidget(self.enabled)
        self.multiple_only=QCheckBox('Only number documents with multiple pages')
        self.multiple_only.setChecked(value.get('minimumPages',1)==2);layout.addWidget(self.multiple_only)
        note=QLabel('Unta numerals · base 12 · each physical page keeps its number.\nNumbers are saved with the document and included in exports.')
        note.setWordWrap(True);layout.addWidget(note)
        grid=QGridLayout();layout.addLayout(grid);self.rows={}
        for col,label in enumerate(('Applies to','Show','Top / bottom','Left / right')):grid.addWidget(QLabel(label),0,col)
        for row,(key,label) in enumerate((('single','Single-page mode'),('left','Left pages in two-page mode'),('right','Right pages in two-page mode')),1):
            show=QCheckBox();show.setAccessibleName(label+' visibility');show.setChecked(value[key]['visible'])
            vertical=QComboBox();horizontal=QComboBox()
            for control,items,field in ((vertical,('top','bottom'),'vertical'),(horizontal,('left','right'),'horizontal')):
                for item in items:control.addItem(item.title(),item)
                control.setCurrentIndex(control.findData(value[key][field]));control.setAccessibleName(label+' '+field+' position')
            self.rows[key]=(show,vertical,horizontal)
            for col,widget in enumerate((QLabel(label),show,vertical,horizontal)):grid.addWidget(widget,row,col)
        self.font_size=QDoubleSpinBox();self.font_size.setRange(8,150);self.font_size.setValue(value['sizePt']);self.font_size.setSuffix(' pt')
        self.inset=QDoubleSpinBox();self.inset.setRange(2,144);self.inset.setValue(value['edgeInsetPt']);self.inset.setSuffix(' pt')
        self.font_size.setAccessibleName('Number font size in points')
        self.inset.setAccessibleName('Preferred distance from top or bottom edge in points')
        grid.addWidget(QLabel('Number font size'),4,0);grid.addWidget(self.font_size,4,2,1,2)
        grid.addWidget(QLabel('Preferred distance from top / bottom edge'),5,0,1,2);grid.addWidget(self.inset,5,2,1,2)
        safety=QLabel('Keeps 4 pt clear of text frames and visible text effects. Numbers may move within the chosen margin to fit. If there is no safe space, the number is withheld and export reports the affected page. Body text is never moved.')
        safety.setWordWrap(True);layout.addWidget(safety)
        self.status=QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Apply|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept_settings);buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings);layout.addWidget(buttons)
        self.refresh_status()

    def apply_settings(self):
        values=dict(enabled=self.enabled.isChecked(),sizePt=self.font_size.value(),edgeInsetPt=self.inset.value(),
                    minimumPages=2 if self.multiple_only.isChecked() else 1)
        for key,(show,vertical,horizontal) in self.rows.items():
            values[key]=dict(visible=show.isChecked(),vertical=vertical.currentData(),horizontal=horizontal.currentData())
        result=self.window.invoke('page.numbering.configure',**values)
        if result:self.refresh_status()
        return result

    def accept_settings(self):
        if self.apply_settings():self.accept()

    def refresh_status(self):
        report=page_numbering.inspect(self.window.book)
        problems=[p['message'] for p in report['pages'] if p['status']=='blocked']
        self.status.setText('\n'.join(problems) if problems else 'Current visible pages: '+', '.join(f"{p['pageNumber']} ({p['status']})" for p in report['pages']))


class NumberingControls:
    def __init__(self,window):
        self.window=window
        menu=next(m for m in window.findChildren(QMenu) if m.title()=='View')
        menu.addSeparator();self.action=menu.addAction('Page numbering…',self.open)
        self.action.setToolTip('Show Unta page numbers and set separate single, left and right page positions. Saved with the document.')
        self.warning=QLabel();self.warning.setStyleSheet('color: #ffdb89; padding: 0 8px;')
        self.warning.setAccessibleName('Page numbering warning');window.statusBar().addPermanentWidget(self.warning)
        self.warning.hide()

    def open(self):
        dialog=NumberingDialog(self.window);dialog.exec();dialog.deleteLater()

    def sync(self):
        if not page_numbering.enabled_for(self.window.book.state):
            self.warning.hide();return
        report=page_numbering.inspect(self.window.book)
        problems=[p['message'] for p in report['pages'] if p['status']=='blocked']
        self.warning.setVisible(bool(problems));self.warning.setText('Page number needs space')
        self.warning.setToolTip('\n'.join(problems))
