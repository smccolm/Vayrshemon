"""Current-user-only Reader API, independent of the Workbench endpoint."""
import json,os,secrets,time,uuid
from pathlib import Path
from PySide6.QtCore import QTimer,QCoreApplication
from PySide6.QtNetwork import QLocalServer,QLocalSocket
from .storage import LOCAL,dumps

METHODS={
 'reader.status':'Reading state, readiness, page count and worker processes',
 'reader.open':'Open a local native book without writing it',
 'reader.close':'Close the book, keeping the reader open',
 'reader.page':'Jump to a 1-based page or previous/next page or spread',
 'reader.mode':'Select one or two pages',
 'reader.palette':'Choose white, black or color',
 'reader.zoom':'Set zoom from 0.1 to 3',
 'reader.fit':'Fit height or width',
 'reader.pan':'Move the reading viewport',
 'reader.search':'Asynchronous literal phrase search; inspect status for results',
 'reader.bookmark':'Bookmark the current page in Reader preferences',
 'reader.capture':'Capture the Reader window to a PNG',
 'reader.performance':'Timing summaries and recent events including slow operations',
}

class Server:
    def __init__(self,window):
        self.window=window;self.token=secrets.token_hex(32);self.server=QLocalServer(window);self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self.name=f'Vayrshemon-Reader-{os.getpid()}-{uuid.uuid4().hex[:8]}'
        if not self.server.listen(self.name):raise OSError(self.server.errorString())
        self.clients={};self.server.newConnection.connect(self.connect)
        self.folder=LOCAL/'run';self.folder.mkdir(parents=True,exist_ok=True);self.path=self.folder/(str(os.getpid())+'.json')
        data=dumps(dict(serverName=self.name,token=self.token,pid=os.getpid(),apiVersion='1.0.0'))
        self.path.write_bytes(data);(self.folder/'active.json').write_bytes(data)
    def connect(self):
        while self.server.hasPendingConnections():
            sock=self.server.nextPendingConnection()
            if len(self.clients)>=16:sock.abort();continue
            self.clients[sock]=bytearray();sock.setReadBufferSize(65537)
            sock.readyRead.connect(lambda s=sock:self.read(s));sock.disconnected.connect(lambda s=sock:self.release(s))
            timer=QTimer(sock);timer.setSingleShot(True);timer.timeout.connect(sock.abort);timer.start(10000)
    def release(self,sock):self.clients.pop(sock,None);sock.deleteLater()
    def read(self,sock):
        data=self.clients.get(sock)
        if data is None:return
        data.extend(bytes(sock.readAll()))
        if len(data)>65536:sock.abort();return
        if b'\n' not in data:return
        try:
            req=json.loads(data)
            if not secrets.compare_digest(str(req.get('token','')),self.token):raise ValueError('Unauthorized')
            started=time.perf_counter();result=self.dispatch(req['method'],req.get('params',{}))
            elapsed=(time.perf_counter()-started)*1000
            self.window.perf.record('api_dispatch',elapsed,method=req['method']);out=dict(ok=True,result=result,dispatchMs=elapsed)
        except Exception as error:out=dict(ok=False,error=str(error))
        sock.write(dumps(out)+b'\n');sock.disconnectFromServer()
    def dispatch(self,method,p):
        w=self.window
        if method=='reader.status':return w.status()
        if method=='reader.open':return dict(actionId=w.open_document(p['path'],p.get('restore',True)))
        if method=='reader.close':w.close_document();return w.status()
        if method=='reader.page':return dict(actionId=w.navigate(p.get('page'),p.get('direction')))
        if method=='reader.mode':return dict(actionId=w.set_mode(p['mode']))
        if method=='reader.palette':return dict(actionId=w.set_palette(p['palette']))
        if method=='reader.zoom':return dict(actionId=w.set_zoom(p['zoom']))
        if method=='reader.fit':return dict(actionId=w.fit(p['fit']))
        if method=='reader.pan':w.pan(float(p.get('dx',0)),float(p.get('dy',0)));return w.status()
        if method=='reader.search':w.search(p['query']);return dict(started=True)
        if method=='reader.bookmark':w.bookmark();return dict(page=w.page)
        if method=='reader.capture':
            path=Path(p['path']).resolve();path.parent.mkdir(parents=True,exist_ok=True)
            if path.suffix.lower()!='.png':raise ValueError('Capture must be PNG')
            if not w.grab().save(str(path),'PNG'):raise OSError('Capture failed')
            return dict(path=str(path))
        if method=='reader.performance':return dict(summary=w.perf.summary(),events=list(w.perf.events)[-min(3000,int(p.get('limit',100))):])
        if method=='reader.quit':QTimer.singleShot(0,w.close);return dict(closing=True)
        raise ValueError('Unknown Reader method')
    def close(self):
        self.server.close();self.path.unlink(missing_ok=True)
        active=self.folder/'active.json'
        try:
            if json.loads(active.read_bytes())['pid']==os.getpid():active.unlink()
        except (OSError,ValueError):pass


def call(method,params=None,descriptor=None):
    app=QCoreApplication.instance() or QCoreApplication([])
    info=json.loads(Path(descriptor or LOCAL/'run/active.json').read_bytes());sock=QLocalSocket();sock.connectToServer(info['serverName'])
    if not sock.waitForConnected(5000):raise ConnectionError(sock.errorString())
    sock.write(dumps(dict(token=info['token'],method=method,params=params or {}))+b'\n')
    if not sock.waitForBytesWritten(5000):raise ConnectionError('Reader request failed')
    data=bytearray();end=time.monotonic()+15
    while b'\n' not in data:
        if sock.bytesAvailable() or sock.waitForReadyRead(1000):data.extend(bytes(sock.readAll()))
        if time.monotonic()>end:raise TimeoutError('Reader did not respond')
    result=json.loads(data)
    if not result['ok']:raise RuntimeError(result['error'])
    return result

if __name__=='__main__':
    import sys
    print(json.dumps(call(sys.argv[1],json.loads(sys.argv[2]) if len(sys.argv)>2 else {}),indent=2))

