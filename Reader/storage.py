"""Disposable page-addressable cache. Original native files are never written."""
from pathlib import Path
import hashlib
import json
import os
import re
import sqlite3
import time
import zlib
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[1]
LOCAL = Path(os.environ.get('VAY_READER_CACHE',str(ROOT / 'Reader' / '.local'))).resolve()
CACHE_VERSION = 2


@lru_cache(maxsize=1)
def engine_key():
    files=[ROOT/'Reader'/n for n in ('render.py','storage.py')]+[ROOT/'vayrshemon'/n for n in ('typesetting.py','studio_typesetting.py','paint.py','roman_paint.py','pages.py','page_numbering.py','print_edition.py','frame.py','session.py')]
    return hashlib.sha256(b''.join(p.read_bytes() for p in sorted(files))).hexdigest()[:20]


def frame_path(source_hash,number,palette,view,scale):
    key=hashlib.sha256(dumps([engine_key(),source_hash,number,palette,view,round(scale,3)])).hexdigest()
    return LOCAL/'frames'/(key+'.frame')


def dumps(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')


def pack(value): return zlib.compress(dumps(value), 1)
def unpack(value): return json.loads(zlib.decompress(value))


def identity(path):
    path = Path(path).resolve(strict=True)
    stat = path.stat()
    return dict(path=str(path), size=stat.st_size, mtime=stat.st_mtime_ns,
                ctime=stat.st_ctime_ns, inode=stat.st_ino, version=CACHE_VERSION)


def cache_path(path):
    return LOCAL / 'books' / (hashlib.sha256(dumps(identity(path))).hexdigest() + '.sqlite')


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda: f.read(4 * 1024 * 1024), b''): h.update(data)
    return h.hexdigest()


def prune_cache(folder,pattern,budget,keep=()):
    """Evict only generated entries beneath Reader's disposable cache root."""
    folder=Path(folder).resolve()
    if not folder.is_relative_to(LOCAL.resolve()):raise ValueError('Cache outside Reader')
    entries=[];keep={Path(p).resolve() for p in keep}
    for path in folder.glob(pattern):
        try:
            if path.resolve().is_relative_to(folder):
                stat=path.stat();entries.append((stat.st_mtime_ns,stat.st_size,path))
        except OSError:pass
    total=sum(size for _,size,_ in entries)
    for _,size,path in sorted(entries):
        if total<=budget:break
        if path.resolve() in keep:continue
        try:path.unlink();total-=size
        except OSError:pass # In-use Windows entries are retained.


def build(path, progress=lambda *args: None):
    """One-time checked import; independent compressed page records thereafter."""
    from tools.m0.common import load_json
    from vayrshemon.native_storage import MAX_FILE_BYTES
    started = time.perf_counter(); source = identity(path); target = cache_path(path)
    if target.exists():
        try:
            with BookIndex(target) as book:
                if book.meta['source'] == source:
                    os.utime(target,None)
                    return dict(cache=str(target), cached=True, milliseconds=(time.perf_counter()-started)*1000)
        except (ValueError,KeyError,TypeError,sqlite3.DatabaseError,zlib.error):pass
    if source['size'] > MAX_FILE_BYTES: raise ValueError('Native file exceeds the supported size limit')
    stages = {}
    def mark(name, percent):
        stages[name] = round((time.perf_counter()-started)*1000, 2); progress(name, percent)
    mark('Reading and verifying native document', 3)
    sha = file_hash(path)
    payload = load_json(path)
    if payload.get('format') != 'vayrshemon.document': raise ValueError('Choose a native .vay document')
    # Keep all currently supported modern and compressed native saves. Older
    # lab documents remain explicitly unsupported rather than silently changed.
    if payload.get('formatVersion') not in ('0.5.0', '0.6.0'):
        raise ValueError('Open this legacy document in the Workbench and save it as .vay first')
    mark('Validating document structure', 20)
    from vayrshemon.file_contracts import DOCUMENT
    from vayrshemon.language_contracts import DOCUMENT as LEGACY
    from vayrshemon.schema_validation import validate
    validate(DOCUMENT if payload['formatVersion']=='0.6.0' else LEGACY, payload)
    state = payload['state']; count = len(state['pages'])
    if not 1 <= count <= 32768: raise ValueError('Unsupported page count')
    pages = state['pages']; typesetting = state.get('typesetting', {})
    ids = {}; headers = []
    for i, page in enumerate(pages, 1):
        if page['pageId'] in ids: raise ValueError('Duplicate page identity')
        ids[page['pageId']] = i
        headers.append({k: v for k, v in page.items() if k != 'frames'})
    frame_pages = {f['frameId']: i for i,p in enumerate(pages,1) for f in p['frames']}
    if len(frame_pages) != sum(len(p['frames']) for p in pages): raise ValueError('Duplicate frame identity')
    groups = {i: {i} for i in range(1,count+1)}
    for flow in typesetting.get('flows', []):
        touched = {frame_pages[f] for f in [flow['source'], *flow['targets']]}
        union = set().union(*(groups[i] for i in touched))
        for i in union: groups[i] = union
    # Language annotations are editable-workbench evidence, not paint input.
    # The original retains them. Do not unpack a 55 MB annotation graph every
    # time somebody opens a book or starts a rendering worker.
    global_state = {k:v for k,v in state.items() if k not in ('pages','typesetting','printEdition','language')}
    global_state['typesetting'] = {k:v for k,v in typesetting.items() if k != 'frames'}
    global_state['typesetting']['frames'] = {}
    edition = state.get('printEdition')
    if edition:
        global_state['printEdition'] = {k:v for k,v in edition.items() if k not in ('pages','verses')}
        global_state['printEdition']['pages'] = {}
        global_state['printEdition']['verses'] = []
    sections=[]; seen=set()
    for n,p in enumerate(headers,1):
        match=re.match(r'^(.*?)\s+(\d+):\d+',p['name'])
        if match and match[1] not in seen:
            seen.add(match[1]);sections.append(dict(name=match[1],page=n))
    work_openings=[dict(name=p['name'].removeprefix('Work opening · '),page=n)
                   for n,p in enumerate(headers,1) if p['name'].startswith('Work opening · ')]
    if work_openings:
        sections=work_openings
    if edition:
        sections=[dict(name=s.get('book',s.get('name',str(i+1))),page=ids.get(s.get('pageId'),s.get('pageNumber',1))) for i,s in enumerate(edition.get('sections',[]))]
    meta = dict(version=CACHE_VERSION, source=source, sha256=sha, pageCount=count,
                title=state['title'], pageMode=payload.get('shellPreview',{}).get('pageMode','one'),
                initialPage=frame_pages.get(state.get('activeFrameId'),1), state=global_state,
                headers=headers, sections=sections)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix('.'+str(os.getpid())+'.tmp')
    con = sqlite3.connect(temp)
    try:
        con.executescript('PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; CREATE TABLE metadata (key TEXT PRIMARY KEY, value BLOB); CREATE TABLE pages (number INTEGER PRIMARY KEY, data BLOB, text TEXT); CREATE VIRTUAL TABLE search USING fts5(text, content=pages, content_rowid=number, tokenize="unicode61 remove_diacritics 0");')
        mark('Indexing individual pages', 30)
        for n, page in enumerate(pages, 1):
            fids = [f['frameId'] for f in page['frames']]
            record = dict(page=page, frames={k:typesetting.get('frames',{}).get(k) for k in fids if k in typesetting.get('frames',{})},
                          connected=sorted(groups[n]), printPage=edition['pages'][page['pageId']] if edition else None)
            texts = ['\n'.join(''.join(r.get('text',r.get('sourceText','')) for r in b['runs']) for b in f['content']['document']['stories'][0]['blocks']) for f in page['frames']]
            con.execute('INSERT INTO pages VALUES (?,?,?)', (n,pack(record),'\n\n'.join(texts)))
            if n % 256 == 0: progress('Indexing pages', 30+int(n/count*60))
        con.execute("INSERT INTO search(search) VALUES ('rebuild')")
        mark('Verifying source and publishing index', 94)
        if identity(path)!=source or file_hash(path)!=sha: raise ValueError('Source changed during indexing; open it again')
        con.execute('INSERT INTO metadata VALUES (?,?)', ('book',pack(meta)))
        con.commit(); con.close(); con=None
        os.replace(temp,target)
    finally:
        if con: con.close()
        temp.unlink(missing_ok=True)
    elapsed=(time.perf_counter()-started)*1000
    result=dict(cache=str(target),cached=False,pageCount=count,sha256=sha,milliseconds=round(elapsed,2),stages=stages,cacheBytes=target.stat().st_size)
    (target.with_suffix('.report.json')).write_bytes(dumps(result))
    prune_cache(target.parent,'*.sqlite',2*1024**3,keep=(target,))
    progress('Ready',100)
    return result


class BookIndex:
    def __init__(self,path):
        self.path=Path(path)
        self.connection=sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True)
        try:
            self.meta=unpack(self.connection.execute("SELECT value FROM metadata WHERE key='book'").fetchone()[0])
            if self.meta['version']!=CACHE_VERSION: raise ValueError('Reading index needs rebuilding')
        except Exception:self.connection.close();raise
    def __enter__(self): return self
    def __exit__(self,*args): self.close()
    def close(self): self.connection.close()
    def page(self,number):
        row=self.connection.execute('SELECT data FROM pages WHERE number=?',(number,)).fetchone()
        if row is None: raise ValueError('Page out of range')
        return unpack(row[0])
    def text(self,number):
        row=self.connection.execute('SELECT text FROM pages WHERE number=?',(number,)).fetchone()
        if row is None: raise ValueError('Page out of range')
        return row[0]
    def search(self,query,limit=200):
        if not query.strip(): return []
        # Literal words/phrase; no untrusted FTS operators.
        query='"'+query.replace('"','""')+'"'
        return [dict(page=n,snippet=s) for n,s in self.connection.execute("SELECT rowid,snippet(search,0,'[',']',' … ',20) FROM search WHERE search MATCH ? LIMIT ?",(query,limit))]

