"""Compact, accessible icon controls for one-page and facing-page views."""
from PySide6.QtCore import Qt,QSize,QRectF
from PySide6.QtGui import QIcon,QPixmap,QPainter,QPen,QColor,QPainterPath
from PySide6.QtWidgets import QPushButton,QButtonGroup
from tools.m0.common import load_json,write_json


def page_icon(count):
    pix=QPixmap(56,48);pix.fill(Qt.GlobalColor.transparent);pix.setDevicePixelRatio(2)
    painter=QPainter(pix);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor('#24516e'),1.2));painter.setBrush(QColor('#f8fbfd'))
    for x in ([8] if count==1 else [1,15]):
        outline=QPainterPath();outline.moveTo(x,2);outline.lineTo(x+8,2);outline.lineTo(x+12,6)
        outline.lineTo(x+12,22);outline.lineTo(x,22);outline.closeSubpath();painter.drawPath(outline)
        painter.drawLine(x+8,2,x+8,6);painter.drawLine(x+8,6,x+12,6)
        for y in (10,14,18):painter.drawLine(x+3,y,x+9,y)
    painter.end();return QIcon(pix)


class PageControls:
    def __init__(self,window):
        self.window=window;self.path=window.book.root/'.local/workspace/page-view.json';self.error=None
        window.zoom.setFixedWidth(190);window.zoom_label.setMinimumWidth(34)
        self.group=QButtonGroup(window);self.group.setExclusive(True);self.buttons={}
        for index,(mode,count,label) in enumerate((('one',1,'One page'),('two',2,'Two pages'))):
            button=QPushButton();button.setCheckable(True);button.setIcon(page_icon(count));button.setIconSize(QSize(28,24));button.setFixedSize(38,30)
            button.setAccessibleName(label);button.setToolTip(label+' · view the current page' if mode=='one' else label+' · view facing pages side by side')
            button.setObjectName('pageView'+str(count));self.group.addButton(button);self.buttons[mode]=button
            button.clicked.connect(lambda checked=False,m=mode:window.invoke('view.pages',mode=m))
            window.zoom_row.insertWidget(2+index,button)
        window.zoom_row.insertSpacing(2,12);window.zoom_row.insertStretch(5,1)
        mode='one'
        if self.path.exists():
            try:
                if self.path.stat().st_size>1024:raise ValueError('PAGE_VIEW_PREFERENCES_TOO_LARGE')
                saved=load_json(self.path)
                if saved.get('version')!='1.0.0' or saved.get('mode') not in self.buttons:raise ValueError('INVALID_PAGE_VIEW_PREFERENCES')
                mode=saved['mode']
            except (ValueError,OSError) as error:self.error=str(error);window.book.log.exception('page-view',error)
        self.set_mode(mode,persist=False)

    def set_mode(self,mode,persist=True):
        if mode not in self.buttons:raise ValueError('UNKNOWN_PAGE_VIEW_MODE')
        canvas=self.window.preview;canvas.page_mode=mode;canvas._center_signature=None;canvas.center_page()
        for key,button in self.buttons.items():button.setChecked(key==mode)
        if persist:
            try:write_json(self.path,dict(version='1.0.0',mode=mode));self.error=None
            except OSError as error:self.error=str(error);self.window.book.log.exception('page-view',error)
        return dict(canvas.navigation_state(),preferenceError=self.error)
