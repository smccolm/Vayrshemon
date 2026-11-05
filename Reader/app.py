"""Independent reading surface: all loading, shaping and paint work is off-UI."""
from collections import OrderedDict
from pathlib import Path
import argparse,json,math,os,secrets,sys,time,traceback,uuid,zlib,struct
from PySide6.QtCore import Qt,QTimer,QProcess,QProcessEnvironment,QRectF,QPointF,Signal,QObject,QRunnable,QThreadPool
from PySide6.QtGui import QAction,QIcon,QKeySequence,QPainter,QColor,QImage,QIntValidator
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QLineEdit,QSlider,QComboBox,QAbstractScrollArea,QFileDialog,QMessageBox,QProgressBar,QDialog,QListWidget,QDialogButtonBox,QPlainTextEdit)
from .storage import ROOT,LOCAL,BookIndex,cache_path,dumps,identity,frame_path
from .performance import Performance


class DecodeSignals(QObject):
    done=Signal(object,object,object,float,object)

class DecodeFrame(QRunnable):
    def __init__(self,key,path,epoch):
        super().__init__();self.key=key;self.path=Path(path);self.epoch=epoch;self.signals=DecodeSignals()
    def run(self):
        started=time.perf_counter()
        try:
            with self.path.open('rb') as f:
                length=struct.unpack('<I',f.read(4))[0]
                if length>4096:raise ValueError('Invalid cached frame')
                head=json.loads(f.read(length));decoder=zlib.decompressobj();raw=decoder.decompress(f.read(),128*1024*1024+1)
            if not decoder.eof or len(raw)!=head['height']*head['stride'] or len(raw)>128*1024*1024:raise ValueError('Invalid cached frame size')
            image=QImage(raw,head['width'],head['height'],head['stride'],QImage.Format.Format_ARGB32_Premultiplied).copy()
            self.signals.done.emit(self.key,image,self.epoch,(time.perf_counter()-started)*1000,None)
        except Exception as error:self.signals.done.emit(self.key,None,self.epoch,(time.perf_counter()-started)*1000,str(error))


class Worker:
    def __init__(self,window,cache,background=False):
        self.window=window;self.background=background;self.ready=False;self.busy=None;self.buffer=bytearray();self.closed=False;self.actual_pid=None
        self.process=QProcess(window);self.process.setWorkingDirectory(str(ROOT))
        env=QProcessEnvironment.systemEnvironment();env.insert('QT_QPA_PLATFORM','offscreen');env.insert('PYTHONUTF8','1')
        for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):env.insert(name,'1')
        self.process.setProcessEnvironment(env)
        self.process.readyReadStandardOutput.connect(self.read)
        self.process.readyReadStandardError.connect(self.errors)
        self.process.finished.connect(self.finished)
        self.process.start(str(ROOT/'.venv/Scripts/python.exe'),['-u','-X','utf8','-m','Reader.worker',str(cache)])
    def errors(self):
        data=bytes(self.process.readAllStandardError())
        with (LOCAL/'logs'/f'worker-{os.getpid()}.log').open('ab') as f:f.write(data)
    def finished(self,code,status):
        if not self.closed and code:
            self.ready=False;self.busy=None;self.window.fail('Rendering process stopped. See Reader logs. Code '+str(code))
    def send(self,op,params,context=None):
        if not self.ready or self.busy:return False
        request=dict(id=uuid.uuid4().hex,op=op,params=params);self.busy=(request,context,time.perf_counter())
        self.process.write(dumps(request)+b'\n');return True
    def read(self):
        if self.closed:return
        self.buffer.extend(bytes(self.process.readAllStandardOutput()))
        while b'\n' in self.buffer:
            line,_,rest=self.buffer.partition(b'\n');self.buffer=bytearray(rest)
            try:msg=json.loads(line)
            except Exception:continue
            if msg.get('event')=='ready':self.ready=True;self.actual_pid=msg.get('pid');self.window.dispatch();continue
            task=self.busy;self.busy=None
            if task:self.window.worker_result(self,task,msg)
            self.window.dispatch()
    def close(self):
        self.closed=True;self.process.kill();self.process.waitForFinished(1000)


class Canvas(QAbstractScrollArea):
    painted=Signal()
    def __init__(self,window):
        super().__init__();self.owner=window;self.drag=None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus);self.setAccessibleName('Reader pages');self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
        for bar in (self.horizontalScrollBar(),self.verticalScrollBar()):bar.valueChanged.connect(self.viewport().update)
    def geometry_pages(self):
        result=[];x=0
        if not self.owner.meta:return result
        for number in self.owner.visible():
            p=self.owner.meta['headers'][number-1];w=int(p['width'])/1e6*4/3;h=int(p['height'])/1e6*4/3
            result.append((number,QRectF(x,0,w,h)));x+=w+32
        return result
    def extent(self):
        items=self.geometry_pages()
        return (items[-1][1].right(),max(r.height() for _,r in items)) if items else (1,1)
    def layout_pages(self,center=True):
        w,h=self.extent();z=self.owner.zoom
        self.horizontalScrollBar().setRange(0,max(0,math.ceil(w*z+32-self.viewport().width())))
        self.verticalScrollBar().setRange(0,max(0,math.ceil(h*z+32-self.viewport().height())))
        self.horizontalScrollBar().setPageStep(self.viewport().width());self.verticalScrollBar().setPageStep(self.viewport().height())
        if center:self.horizontalScrollBar().setValue(self.horizontalScrollBar().maximum()//2);self.verticalScrollBar().setValue(0)
        self.viewport().update()
    def paintEvent(self,event):
        started=time.perf_counter();p=QPainter(self.viewport());p.fillRect(self.viewport().rect(),QColor('#d8dfe5'))
        w,h=self.extent();z=self.owner.zoom
        x=max(16,(self.viewport().width()-w*z)/2)-self.horizontalScrollBar().value()
        y=max(16,(self.viewport().height()-h*z)/2)-self.verticalScrollBar().value()
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if not self.owner.meta:
            p.setPen(QColor('#52616c'));p.drawText(self.viewport().rect(),Qt.AlignmentFlag.AlignCenter,'Open a .vay book to read')
        for number,rect in self.geometry_pages():
            dest=QRectF(x+rect.x()*z,y,rect.width()*z,rect.height()*z)
            if not dest.intersects(QRectF(self.viewport().rect())):continue
            image=self.owner.best_image(number)
            p.fillRect(dest,QColor('white' if self.owner.palette=='white' else 'black'))
            if image is not None:p.drawImage(dest,image)
            else:
                p.setPen(QColor('#808080'));p.drawText(dest,Qt.AlignmentFlag.AlignCenter,'Loading page '+str(number))
        p.end();elapsed=(time.perf_counter()-started)*1000
        self.owner.perf.record('paint',elapsed,page=self.owner.page)
        self.owner.presented()
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.owner.fit_mode:self.owner.update_fit()
        self.layout_pages(False);self.owner.render_timer.start(120)
    def mousePressEvent(self,event):
        if event.button() in (Qt.MouseButton.LeftButton,Qt.MouseButton.MiddleButton):self.drag=event.position();self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor);self.setFocus()
    def mouseMoveEvent(self,event):
        if self.drag is not None:
            delta=event.position()-self.drag;self.drag=event.position();self.owner.pan(-delta.x(),-delta.y())
    def mouseReleaseEvent(self,event):self.drag=None;self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
    def wheelEvent(self,event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.owner.set_zoom(self.owner.zoom*(1.1 if event.angleDelta().y()>0 else 1/1.1));event.accept()
        else:super().wheelEvent(event)
    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Right,Qt.Key.Key_PageDown):self.owner.navigate(direction='next');return
        if event.key() in (Qt.Key.Key_Left,Qt.Key.Key_PageUp):self.owner.navigate(direction='previous');return
        if event.key()==Qt.Key.Key_Home:self.owner.navigate(page=1);return
        if event.key()==Qt.Key.Key_End and self.owner.meta:self.owner.navigate(page=self.owner.meta['pageCount']);return
        super().keyPressEvent(event)


class Window(QMainWindow):
    def __init__(self,started=None):
        super().__init__();self.started=started or time.perf_counter();self.perf=Performance()
        self.meta=None;self.index=None;self.source=None;self.page=1;self.mode='one';self.palette='white';self.zoom=.7;self.fit_mode='height'
        self.images=OrderedDict();self.image_bytes=0;self.pending=[];self.prefetch=[];self.workers=[];self.generation=0
        self.epoch=0;self.decoding=set();self.decode_pool=QThreadPool(self);self.decode_pool.setMaxThreadCount(2);self.decode_jobs={}
        self.action=None;self.action_id=0;self.completed_id=0;self.present_id=0;self.last_error=None;self.opening=False;self.closed=False;self.aux=[];self.last_search=[]
        self.indexer=None;self.index_buffer=bytearray();self.preferences_path=LOCAL/'preferences.json';self.preferences={}
        try:self.preferences=json.loads(self.preferences_path.read_text('utf-8'))
        except (OSError,ValueError):pass
        self.render_timer=QTimer(self);self.render_timer.setSingleShot(True);self.render_timer.timeout.connect(self.schedule)
        self.pref_timer=QTimer(self);self.pref_timer.setSingleShot(True);self.pref_timer.timeout.connect(self.save_preferences)
        self.setWindowTitle('Vayrshemon Reader');self.setWindowIcon(QIcon(str(ROOT/'data/icons/memon-color.ico')))
        self.build_ui();self.resize(1440,900);self.last_tick=time.perf_counter();self.heartbeat=QTimer(self);self.heartbeat.timeout.connect(self.tick);self.heartbeat.start(16)
        from .control import Server
        self.server=Server(self)
    def button(self,text,callback,tip=None):
        b=QPushButton(text);b.clicked.connect(callback)
        if tip:b.setToolTip(tip);b.setAccessibleName(tip)
        return b
    def build_ui(self):
        host=QWidget();outer=QVBoxLayout(host);outer.setContentsMargins(8,6,8,6);outer.setSpacing(4)
        top=QHBoxLayout();top.addWidget(self.button('Open',self.choose_open));top.addWidget(self.button('Fit Height',lambda:self.fit('height')));top.addWidget(self.button('Fit Width',lambda:self.fit('width')))
        self.palette_box=QComboBox();self.palette_box.addItems(['Black on white','White on black','Color / relief']);self.palette_box.setAccessibleName('Reading color mode');self.palette_box.activated.connect(lambda i:self.set_palette(['white','black','color'][i]));top.addWidget(self.palette_box)
        self.book_box=QComboBox();self.book_box.setMinimumWidth(180);self.book_box.setAccessibleName('Book or major section');self.book_box.activated.connect(lambda i:self.navigate(page=self.book_box.itemData(i)));top.addWidget(self.book_box)
        top.addStretch();top.addWidget(self.button('Find',self.find_dialog));top.addWidget(self.button('Bookmark',self.bookmark));outer.addLayout(top)
        self.progress=QProgressBar();self.progress.hide();outer.addWidget(self.progress)
        self.canvas=Canvas(self);outer.addWidget(self.canvas,1)
        bottom=QHBoxLayout();self.zoom_label=QLabel('70%');bottom.addWidget(self.zoom_label)
        self.slider=QSlider(Qt.Orientation.Horizontal);self.slider.setRange(10,300);self.slider.setFixedWidth(180);self.slider.setValue(70);self.slider.setAccessibleName('Zoom');self.slider.valueChanged.connect(lambda n:self.set_zoom(n/100));bottom.addWidget(self.slider)
        self.single=self.button('',lambda:self.set_mode('one'),'Single page');self.double=self.button('',lambda:self.set_mode('two'),'Two pages')
        for b,two in ((self.single,False),(self.double,True)):
            from PySide6.QtGui import QPixmap,QPen
            pix=QPixmap(30,24);pix.fill(Qt.GlobalColor.transparent);p=QPainter(pix);p.setPen(QPen(QColor('#245474'),1.4));p.setBrush(QColor('white'))
            for x in ([2,16] if two else [9]):
                p.drawRect(x,2,11,19)
                for y in (7,11,15):p.drawLine(x+3,y,x+8,y)
            p.end();b.setIcon(QIcon(pix));b.setCheckable(True);bottom.addWidget(b)
        self.previous=self.button('<',lambda:self.navigate(direction='previous'),'Previous page or spread');bottom.addWidget(self.previous)
        bottom.addWidget(QLabel('Page'));self.page_entry=QLineEdit('1');self.page_entry.setFixedWidth(64);self.page_entry.setAccessibleName('Page number');self.page_entry.returnPressed.connect(self.entry_navigate);bottom.addWidget(self.page_entry)
        self.total_label=QLabel('of 0');bottom.addWidget(self.total_label);self.next=self.button('>',lambda:self.navigate(direction='next'),'Next page or spread');bottom.addWidget(self.next);bottom.addStretch();self.detail=QLabel('');bottom.addWidget(self.detail);outer.addLayout(bottom)
        self.setCentralWidget(host)
        file=self.menuBar().addMenu('File');self.menu_action(file,'Open…',self.choose_open,'Ctrl+O');self.menu_action(file,'Close',self.close_document,'Ctrl+W');self.menu_action(file,'Open in Workbench',self.open_workbench);file.addSeparator();self.menu_action(file,'Exit',self.close,'Alt+F4')
        view=self.menuBar().addMenu('View');self.menu_action(view,'Fit Height',lambda:self.fit('height'));self.menu_action(view,'Fit Width',lambda:self.fit('width'));self.menu_action(view,'Fullscreen',self.fullscreen,'F11')
        nav=self.menuBar().addMenu('Navigate');self.menu_action(nav,'Go to page',self.focus_page,'Ctrl+G');self.menu_action(nav,'Find text…',self.find_dialog,'Ctrl+F');self.menu_action(nav,'Bookmarks…',self.bookmarks_dialog,'Ctrl+B');self.menu_action(nav,'Copy current page text',self.copy_text,'Ctrl+Shift+C')
        help=self.menuBar().addMenu('Help');self.menu_action(help,'Performance',self.performance_dialog);self.menu_action(help,'Open logs',lambda:os.startfile(str(LOCAL/'logs')));self.menu_action(help,'About',lambda:QMessageBox.information(self,'Vayrshemon Reader','Vayrshemon Reader 1.0.0\nRead-only native books. Shared original typography.\nReading preferences are separate from your .vay files.'))
        self.sync()
    def menu_action(self,menu,text,callback,shortcut=None):
        action=menu.addAction(text);action.triggered.connect(callback)
        if shortcut:action.setShortcut(QKeySequence(shortcut))
        return action
    def focus_page(self):self.page_entry.setFocus();self.page_entry.selectAll()
    def fullscreen(self):self.showMaximized() if self.isFullScreen() else self.showFullScreen()
    def choose_open(self):
        path,_=QFileDialog.getOpenFileName(self,'Open book',str(ROOT/'Saves'),'Vayrshemon books (*.vay *.vay.json);;All files (*)')
        if path:self.try_open(path)
    def try_open(self,path,restore=True):
        try:self.open_document(path,restore)
        except (OSError,ValueError) as error:self.fail(str(error))
    def begin(self,action,**details):
        if self.action:
            self.perf.record('superseded',(time.perf_counter()-self.action['start'])*1000,operation=self.action['name'])
        self.action_id+=1;self.action=dict(id=self.action_id,name=action,start=time.perf_counter(),details=details,first=False)
        self.last_error=None;return self.action_id
    def open_document(self,path,restore=True):
        path=Path(path).resolve(strict=True)
        if path.suffix.lower() not in ('.vay','.json'):raise ValueError('Choose a .vay book')
        self.close_document(record=False);self.begin('open',path=str(path));self.source=path;self.opening=True;self.restore_preference=restore
        self.progress.setRange(0,100);self.progress.setValue(0);self.progress.setFormat('Preparing reading index…');self.progress.show();self.statusBar().showMessage('Opening '+path.name)
        self.indexer=QProcess(self);self.indexer.setWorkingDirectory(str(ROOT));self.index_buffer=bytearray()
        self.indexer.readyReadStandardOutput.connect(self.index_data);self.indexer.readyReadStandardError.connect(self.index_errors);self.indexer.finished.connect(self.index_finished)
        self.indexer.start(str(ROOT/'.venv/Scripts/python.exe'),['-u','-X','utf8','-m','Reader.index_book',str(path)])
        return self.action_id
    def index_errors(self):
        with (LOCAL/'logs'/f'index-{os.getpid()}.log').open('ab') as f:f.write(bytes(self.indexer.readAllStandardError()))
    def index_finished(self,code,status):
        if code and self.opening:self.fail('Could not open the book. See Reader index log.')
    def index_data(self):
        self.index_buffer.extend(bytes(self.indexer.readAllStandardOutput()))
        while b'\n' in self.index_buffer:
            line,_,rest=self.index_buffer.partition(b'\n');self.index_buffer=bytearray(rest)
            try:msg=json.loads(line)
            except Exception:continue
            if msg['event']=='progress':self.progress.setValue(msg['percent']);self.progress.setFormat(msg['stage']+' · %p%')
            elif msg['event']=='error':self.fail(msg['message'])
            elif msg['event']=='ready':
                self.perf.record('index',msg['milliseconds'],cached=msg['cached']);self.loaded_index(msg['cache'])
    def loaded_index(self,path):
        started=time.perf_counter();self.index=BookIndex(path);self.meta=self.index.meta;self.opening=False;self.progress.hide()
        pref=self.preferences.get(str(self.source),{}) if self.restore_preference else {}
        self.page=max(1,min(self.meta['pageCount'],int(pref.get('page',self.meta['initialPage']))));self.mode=pref.get('mode',self.meta['pageMode'])
        saved=self.meta['state']['view'];self.palette=pref.get('palette','color' if saved['mode']=='color' else ('black' if saved.get('monochromePaper')=='black' else 'white'))
        self.fit_mode=pref.get('fit','height');self.zoom=float(pref.get('zoom',.7));self.update_fit()
        self.book_box.clear()
        for section in self.meta['sections']:self.book_box.addItem(str(section['name']),section['page'])
        self.book_box.setVisible(bool(self.meta['sections']));self.setWindowTitle(self.source.stem+' — Reader')
        self.workers=[Worker(self,path),Worker(self,path,True)]
        self.canvas.layout_pages();self.sync();self.schedule();self.perf.record('index_attach',(time.perf_counter()-started)*1000,pageCount=self.meta['pageCount'])
    def visible(self):
        if not self.meta:return []
        start=self.page if self.mode=='one' else (self.page-1)//2*2+1
        return list(range(start,min(self.meta['pageCount']+1,start+(1 if self.mode=='one' else 2))))
    def scale(self):return min(4,max(.1,math.ceil(self.zoom*self.devicePixelRatioF()*20)/20))
    def key(self,number,scale=None):return (number,self.palette,self.mode,scale if scale is not None else self.scale())
    def best_image(self,number):
        key=self.key(number)
        if key in self.images:self.images.move_to_end(key);return self.images[key]
        candidates=[(abs(k[3]-key[3]),v) for k,v in self.images.items() if k[:3]==key[:3]]
        if candidates:return min(candidates,key=lambda pair:pair[0])[1]
        return None
    def remember_image(self,key,image):
        if key in self.images:self.image_bytes-=self.images.pop(key).sizeInBytes()
        self.images[key]=image;self.image_bytes+=image.sizeInBytes()
        pinned=set()
        for number in self.visible():
            wanted=self.key(number)
            candidates=[k for k in self.images if k[:3]==wanted[:3]]
            if candidates:pinned.add(min(candidates,key=lambda k:abs(k[3]-wanted[3])))
        while self.image_bytes>256*1024*1024:
            discard=next((k for k in self.images if k not in pinned),None)
            if discard is None:break
            self.image_bytes-=self.images.pop(discard).sizeInBytes()
    def schedule(self):
        if not self.meta:return
        self.generation+=1;scale=self.scale()
        # Reopening/navigation can display cached pages before Python's native
        # rendering libraries finish loading in the worker process.
        for n in self.visible():
            key=self.key(n)
            if key not in self.images and key not in self.decoding:
                path=frame_path(self.meta['sha256'],n,self.palette,self.mode,scale)
                if path.exists():
                    try:self.load_image(key,path)
                    except (OSError,ValueError,zlib.error):pass
        self.pending=[dict(number=n,palette=self.palette,view=self.mode,scale=scale) for n in self.visible() if self.key(n) not in self.images and self.key(n) not in self.decoding]
        self.prefetch=[]
        if self.visible():
            start,end=self.visible()[0],self.visible()[-1]
            nearby=list(range(end+1,min(self.meta['pageCount']+1,end+5)))+list(range(max(1,start-2),start))
            self.prefetch=[dict(number=n,palette=self.palette,view=self.mode,scale=scale) for n in nearby if self.key(n) not in self.images]
            if self.palette!='color' and not self.meta['state'].get('printEdition'):
                self.prefetch.extend(dict(number=n,palette='color',view=self.mode,scale=scale) for n in self.visible())
        self.dispatch();self.canvas.viewport().update();self.sync();self.pref_timer.start(500)
    def dispatch(self):
        if not self.workers:return
        front,back=self.workers
        if front.ready and not front.busy:
            if self.pending:front.send('render',self.pending.pop(0),self.generation)
            elif self.aux:
                op,params,context=self.aux.pop(0);front.send(op,params,context)
        if back.ready and not back.busy:
            if self.pending:back.send('render',self.pending.pop(0),self.generation)
            elif not front.busy and self.prefetch:back.send('render',self.prefetch.pop(0),self.generation)
    def worker_result(self,worker,task,msg):
        request,context,sent=task;op=request['op']
        if msg.get('event')=='error':self.fail(msg['message']);return
        result=msg['result'];self.perf.record('worker_'+op,(time.perf_counter()-sent)*1000,background=worker.background,workerMs=msg.get('workerMs'),details=result if op=='render' else None)
        if op=='render':
            params=request['params'];key=(params['number'],params['palette'],params['view'],params['scale'])
            try:
                self.load_image(key,result['path'])
            except Exception as error:self.fail(str(error));return
            self.canvas.viewport().update()
        elif op=='search':
            self.last_search=result;self.perf.record('search',(time.perf_counter()-context['start'])*1000,matches=len(result));self.search_done=True
            from shiboken6 import isValid
            if context.get('list') is not None and isValid(context['list']):
                context['list'].clear()
                for item in result:context['list'].addItem(f"Page {item['page']} · {item['snippet']}")
        elif op=='text':
            QApplication.clipboard().setText(result);self.perf.record('copy',(time.perf_counter()-context['start'])*1000,characters=len(result));self.statusBar().showMessage('Page text copied',2500)
    def load_image(self,key,path):
        if key in self.decoding:return
        self.decoding.add(key);job=DecodeFrame(key,path,self.epoch);self.decode_jobs[(self.epoch,key)]=job;job.signals.done.connect(self.image_decoded);self.decode_pool.start(job)
    def image_decoded(self,key,image,epoch,elapsed,error):
        self.decode_jobs.pop((epoch,key),None)
        if epoch!=self.epoch or self.closed:return
        self.decoding.discard(key)
        if error:
            path=frame_path(self.meta['sha256'],*key)
            path.unlink(missing_ok=True);self.schedule();return
        self.remember_image(key,image);self.perf.record('frame_decode',elapsed,pixels=image.width()*image.height());self.canvas.viewport().update()
    def presented(self):
        if not self.action or not self.meta:return
        now=time.perf_counter()
        if not self.action['first']:
            self.action['first']=True;self.present_id=self.action['id'];self.perf.record(self.action['name']+'_response',(now-self.action['start'])*1000)
        if all(self.key(n) in self.images for n in self.visible()):
            event=self.perf.record(self.action['name'],(now-self.action['start'])*1000,page=self.page,visible=self.visible(),palette=self.palette,mode=self.mode,**self.action['details'])
            self.completed_id=self.action['id'];self.action=None
            self.detail.setText(f"{event['ms']:.0f} ms");self.statusBar().showMessage('Ready')
    def entry_navigate(self):
        try:self.navigate(page=int(self.page_entry.text()))
        except ValueError:self.statusBar().showMessage('Enter a page from 1 to '+str(self.meta['pageCount'] if self.meta else 1),4000);self.sync()
    def navigate(self,page=None,direction=None):
        if not self.meta:return None
        if direction:
            if direction not in ('next','previous'):raise ValueError('Invalid direction')
            start=(self.page-1)//2*2+1 if self.mode=='two' else self.page
            page=max(1,min(self.meta['pageCount'],start+(2 if self.mode=='two' else 1)*(1 if direction=='next' else -1)))
        if type(page) is not int or not 1<=page<=self.meta['pageCount']:raise ValueError('Page out of range')
        self.begin('navigate');self.page=page;self.update_fit();self.canvas.layout_pages();self.schedule();return self.action_id
    def set_mode(self,mode):
        if mode not in ('one','two'):raise ValueError('Invalid page mode')
        self.begin('pages');self.mode=mode;self.update_fit();self.canvas.layout_pages();self.schedule();return self.action_id
    def set_palette(self,palette):
        if palette not in ('white','black','color'):raise ValueError('Invalid color mode')
        if self.meta and self.meta['state'].get('printEdition'):palette='white'
        self.begin('palette');self.palette=palette;self.schedule();return self.action_id
    def set_zoom(self,zoom):
        if not isinstance(zoom,(int,float)) or not math.isfinite(zoom) or not .1<=zoom<=3:raise ValueError('Zoom must be between 10% and 300%')
        self.begin('zoom');self.fit_mode=None;self.zoom=zoom;self.canvas.layout_pages(False);self.sync();self.render_timer.start(140);return self.action_id
    def fit(self,kind):
        if kind not in ('height','width'):raise ValueError('Invalid fit')
        self.begin('fit',fit=kind);self.fit_mode=kind;self.update_fit();self.canvas.layout_pages();self.schedule();return self.action_id
    def update_fit(self):
        if not self.fit_mode or not self.meta:return
        w,h=self.canvas.extent();v=self.canvas.viewport()
        self.zoom=max(.1,min(3,(v.height()-32)/h if self.fit_mode=='height' else (v.width()-32)/w))
    def pan(self,dx,dy):
        started=time.perf_counter();self.canvas.horizontalScrollBar().setValue(self.canvas.horizontalScrollBar().value()+round(dx));self.canvas.verticalScrollBar().setValue(self.canvas.verticalScrollBar().value()+round(dy));self.perf.record('pan',(time.perf_counter()-started)*1000)
    def sync(self):
        count=self.meta['pageCount'] if self.meta else 0
        self.single.setChecked(self.mode=='one');self.double.setChecked(self.mode=='two');self.page_entry.setText(str(self.page));self.total_label.setText('of '+str(count))
        self.previous.setEnabled(bool(count and self.visible()[0]>1));self.next.setEnabled(bool(count and self.visible()[-1]<count));self.page_entry.setValidator(QIntValidator(1,max(1,count)))
        self.zoom_label.setText(f'{self.zoom:.0%}');self.slider.blockSignals(True);self.slider.setValue(round(self.zoom*100));self.slider.blockSignals(False)
        self.palette_box.setCurrentIndex(['white','black','color'].index(self.palette));self.palette_box.setEnabled(not bool(self.meta and self.meta['state'].get('printEdition')))
        if self.meta and self.meta.get('sections'):
            selected=max((i for i,s in enumerate(self.meta['sections']) if s['page']<=self.page),default=0)
            self.book_box.setCurrentIndex(selected)
    def tick(self):
        now=time.perf_counter();delay=(now-self.last_tick)*1000-16;self.last_tick=now
        if delay>50:self.perf.record('heartbeat',delay)
    def fail(self,message):
        self.last_error=message;self.opening=False;self.progress.hide();self.statusBar().showMessage(message);self.perf.record('error',0,message=message);self.action=None
    def save_preferences(self):
        if not self.meta or not self.source:return
        old=self.preferences.get(str(self.source),{})
        self.preferences[str(self.source)]=dict(page=self.page,mode=self.mode,palette=self.palette,zoom=self.zoom,fit=self.fit_mode,bookmarks=old.get('bookmarks',[]))
        temp=self.preferences_path.with_suffix('.'+str(os.getpid())+'.tmp');temp.write_bytes(dumps(self.preferences));os.replace(temp,self.preferences_path)
    def bookmark(self):
        if not self.meta:return
        self.save_preferences();marks=self.preferences[str(self.source)]['bookmarks']
        if self.page not in marks:marks.append(self.page)
        self.save_preferences();self.statusBar().showMessage('Bookmarked page '+str(self.page),2500)
    def bookmarks_dialog(self):
        if not self.meta:return
        marks=self.preferences.get(str(self.source),{}).get('bookmarks',[]);dialog=QDialog(self);dialog.setWindowTitle('Bookmarks');layout=QVBoxLayout(dialog);listing=QListWidget();listing.addItems(['Page '+str(p) for p in marks]);layout.addWidget(listing)
        listing.itemActivated.connect(lambda item:(self.navigate(page=marks[listing.row(item)]),dialog.accept()));dialog.resize(300,400);dialog.exec()
    def search(self,query,listing=None):
        if not self.meta:raise ValueError('No book open')
        if not isinstance(query,str) or len(query)>1000:raise ValueError('Search query is too long')
        self.search_done=False;self.aux=[a for a in self.aux if a[0]!='search'];self.aux.append(('search',dict(query=query,limit=200),dict(start=time.perf_counter(),list=listing)));self.dispatch()
    def find_dialog(self):
        if not self.meta:return
        dialog=QDialog(self);dialog.setWindowTitle('Find in book');layout=QVBoxLayout(dialog);entry=QLineEdit();entry.setPlaceholderText('Text or phrase');listing=QListWidget();layout.addWidget(entry);layout.addWidget(listing);entry.returnPressed.connect(lambda:self.search(entry.text(),listing))
        listing.itemActivated.connect(lambda item:(self.navigate(page=self.last_search[listing.row(item)]['page']),dialog.accept()));dialog.resize(720,450);dialog.exec()
    def copy_text(self):
        if self.meta:self.aux.append(('text',dict(number=self.page),dict(start=time.perf_counter())));self.dispatch()
    def open_workbench(self):
        if not self.source:return
        import subprocess
        subprocess.Popen([str(ROOT/'.venv/Scripts/pythonw.exe'),str(ROOT/'tools/launch_editor.py'),'--document',str(self.source)],cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW)
    def performance_dialog(self):
        dialog=QDialog(self);dialog.setWindowTitle('Reader performance');layout=QVBoxLayout(dialog);text=QPlainTextEdit();text.setReadOnly(True);text.setPlainText(json.dumps(self.perf.summary(),indent=2));layout.addWidget(text);dialog.resize(640,560);dialog.exec()
    def close_document(self,record=True):
        started=time.perf_counter();self.save_preferences();self.render_timer.stop();self.pref_timer.stop()
        if self.indexer and self.indexer.state()!=QProcess.ProcessState.NotRunning:self.indexer.kill();self.indexer.waitForFinished(1000)
        self.indexer=None
        for worker in self.workers:worker.close()
        self.workers=[]
        if self.index:self.index.close()
        self.epoch+=1;self.decoding.clear();self.index=None;self.meta=None;self.source=None;self.images.clear();self.image_bytes=0;self.pending=[];self.prefetch=[];self.aux=[];self.action=None;self.opening=False;self.page=1;self.book_box.clear();self.progress.hide();self.canvas.layout_pages();self.sync();self.setWindowTitle('Vayrshemon Reader')
        if record:self.perf.record('close',(time.perf_counter()-started)*1000)
    def status(self):
        return dict(path=str(self.source) if self.source else None,page=self.page,pageCount=self.meta['pageCount'] if self.meta else 0,visible=self.visible(),mode=self.mode,palette=self.palette,zoom=self.zoom,fit=self.fit_mode,actionId=self.action_id,completedId=self.completed_id,presentId=self.present_id,opening=self.opening,error=self.last_error,
                    busy=bool(self.action),visibleReady=bool(self.meta) and all(self.key(n) in self.images for n in self.visible()),section=self.book_box.currentText(),workers=[dict(pid=w.actual_pid or w.process.processId(),ready=w.ready,busy=bool(w.busy)) for w in self.workers],imageCacheBytes=self.image_bytes,searchDone=getattr(self,'search_done',True),searchResults=self.last_search,pid=os.getpid())
    def closeEvent(self,event):
        self.closed=True;self.heartbeat.stop();self.close_document();self.server.close();self.perf.stream.close();event.accept()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('path',nargs='?');parser.add_argument('--no-restore',action='store_true');parser.add_argument('--started',type=float);args=parser.parse_args()
    LOCAL.mkdir(parents=True,exist_ok=True)
    if os.name=='nt':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Vayrshemon.Reader')
    app=QApplication(sys.argv[:1]);app.setApplicationName('Vayrshemon Reader');app.setOrganizationName('Vayrshemon')
    window=Window(args.started);window.showMaximized()
    QTimer.singleShot(0,lambda:window.perf.record('startup_shell',(time.perf_counter()-window.started)*1000))
    if args.path:QTimer.singleShot(0,lambda:window.try_open(args.path,restore=not args.no_restore))
    return app.exec()

if __name__=='__main__':sys.exit(main())
