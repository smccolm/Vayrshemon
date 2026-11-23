"""Mine written forms from actual native pages, including print and earlier witnesses."""
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import unicodedata
import zipfile

from tools.dampier_completion_audit import state_chunks
from vayrshemon.reading import SCRIPT_SHA

ROOT = Path(__file__).resolve().parents[1]
TITLE = 'Vayrshemon Dictionary'
EDITION = TITLE + ' - Four-Column Progressive Edition'
BOOK = ROOT / 'Saves' / EDITION
WORK = BOOK / 'Working'
DB = WORK / 'corpus.sqlite3'
ARCHIVE_CACHE = ROOT / '.local/dictionary-archive-witnesses'
PACKAGE = ROOT / 'data/language/later-dramatic-0.13'


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def page_stream(path):
    envelope = read(path)
    if 'state' in envelope:
        yield from envelope['state']['pages']
        return
    chunks = iter(state_chunks(envelope.pop('stateEncoding')))
    del envelope
    tail = ''
    marker = re.compile(r'"pages"\s*:\s*\[\s*(?=\{\s*"pageId")')
    for chunk in chunks:
        data = tail + chunk
        match = marker.search(data)
        if match:
            data = data[match.end():]
            break
        tail = data[-128:]
    else:
        raise ValueError(f'Cannot locate pages in {path}')
    decoder = json.JSONDecoder()
    while True:
        data = data.lstrip(' \r\n\t,')
        if data.startswith(']'):
            for _ in chunks:
                pass  # Finish the native state's checksum.
            return
        try:
            page, end = decoder.raw_decode(data)
        except json.JSONDecodeError:
            data += next(chunks)
            continue
        if 'frames' not in page:
            raise ValueError(f'Invalid page array in {path}')
        yield page
        data = data[end:]


ORTH = read(PACKAGE / 'orthography.json')
MINIMA = str.maketrans({v:k for k,v in ORTH['maximaPairs'].items()})
ALPHABET = ''.join(ORTH['maximaPairs']) + ''.join(ORTH['maximaPairs'].values())
# Some saved native names use a fallback font for an individual Roman
# accented vowel. Font boundaries are not linguistic word boundaries.
ROMAN = ''.join(chr(i) for i in range(0xc0,0x250) if unicodedata.name(chr(i),'').startswith('LATIN '))
FALLBACK_MINIMA = str.maketrans({c:c.lower() for c in ROMAN if c not in ALPHABET+'ÀÁ'})
CHARS = re.escape(ALPHABET + ROMAN + '0123456789ÀÁ')
WORDS = re.compile(rf'[{CHARS}]+(?:[’\'\-][{CHARS}]+|(?<=[0-9ÀÁ]):[0-9ÀÁ]+)*')
TOKENIZATION='native runs with in-word literal accents, revision 2'


def written(text):
    return WORDS.findall(unicodedata.normalize('NFC',text))


@lru_cache(maxsize=150000)
def normalize(text):
    return text.translate(FALLBACK_MINIMA).translate(MINIMA).replace("'", '’')


def native_blocks(page):
    for frame in page['frames']:
        doc = frame.get('content', {}).get('document', {})
        script = {s['styleId'] for s in doc.get('styles', []) if SCRIPT_SHA in (s.get('fontId') or '')}
        for story in doc.get('stories', []):
            for block in story['blocks']:
                pieces, has_script = [], False
                for run in block['runs']:
                    text = run.get('sourceText', run.get('text', ''))
                    if run.get('sourceFontSha256') == SCRIPT_SHA or run.get('styleId') in script:
                        pieces.append(text)
                        has_script = True
                    elif run.get('styleId','').startswith('style.archive-punctuation') or not any(c.isalnum() for c in text):
                        pieces.append(text)
                    else:
                        pieces.append(' ')
                if has_script:
                    yield ''.join(pieces)


def publications():
    for root in [ROOT / 'Saves', ROOT / 'Special Projects']:
        for path in sorted(root.rglob('*.vay')):
            if path.is_relative_to(BOOK) or path.stem.startswith(TITLE) or path.name == 'Black on white.vay':
                continue
            yield path
    yield from (p for p in archived_files() if p.suffix.lower()=='.vay' and not p.stem.startswith(TITLE))


@lru_cache(maxsize=1)
def archive_index():
    manifest=ARCHIVE_CACHE/'inventory.json'
    return read(manifest) if manifest.exists() else {}


def archived_files():
    index=archive_index()
    if index:
        for folder,record in sorted(index.items()):
            yield from (ARCHIVE_CACHE/folder/name for name in record['members'])
    else:
        yield from sorted(p for p in ARCHIVE_CACHE.rglob('*') if p.is_file())


def witness_name(path):
    if path.is_relative_to(ARCHIVE_CACHE):
        archive, *member = path.relative_to(ARCHIVE_CACHE).parts
        index=archive_index()
        source=ROOT/index[archive]['path'] if archive in index else next((ROOT / 'Saves').rglob(archive))
        return source.relative_to(ROOT).as_posix() + '!/' + '/'.join(member)
    return path.relative_to(ROOT).as_posix()


def unpack_witnesses():
    """Only historical manuscripts and their authoring ledgers enter the staging cache."""
    from shutil import copyfileobj, which
    exe = which('7z') or r'C:\Program Files\7-Zip\7z.exe'
    paths=sorted(p for base in ('Saves','Special Projects') for p in (ROOT/base).rglob('*')
                 if p.is_file() and p.suffix.lower() in {'.zip','.7z'} and not p.is_relative_to(BOOK))
    duplicates=Counter(p.name for p in paths)
    old_index=archive_index()
    inventory={}
    for path in paths:
        relative=path.relative_to(ROOT).as_posix()
        folder_name=path.name if duplicates[path.name]==1 else path.name+'-'+hashlib.sha256(relative.encode()).hexdigest()[:16]
        folder = ARCHIVE_CACHE / folder_name
        receipt = folder / 'source.sha256'
        digest = sha(path)
        previous=old_index.get(folder_name)
        if previous and previous['sha256']==digest and all((folder/n).is_file() for n in previous['members']):
            inventory[folder_name]=previous
            continue
        folder.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == '.7z':
            listing = subprocess.check_output([exe,'l','-slt','-sccUTF-8',str(path)]).decode('utf8')
            members = [line[7:] for line in listing.splitlines() if line.startswith('Path = ')]
        else:
            with zipfile.ZipFile(path) as archive:
                members = archive.namelist()
        wanted = [n for n in members if n.lower().endswith(('.vay','ledger.json'))]
        inventory[folder_name]=dict(path=relative,sha256=digest,members=wanted)
        for n in wanted:
            if not (folder / n).resolve().is_relative_to(folder):
                raise ValueError(f'Invalid archive member {n}')
        if receipt.is_file() and receipt.read_text()==digest and all((folder/n).is_file() for n in wanted):
            continue
        if wanted and path.suffix.lower() == '.7z':
            subprocess.run([exe,'x','-y','-bd','-bso0','-o'+str(folder),str(path),*wanted],check=True)
        elif wanted:
            with zipfile.ZipFile(path) as archive:
                for n in wanted:
                    dest = folder / n
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(n) as src, dest.open('wb') as out:
                        copyfileobj(src,out)
        receipt.write_text(digest)
    from vayrshemon.json_stream import write_atomic
    ARCHIVE_CACHE.mkdir(parents=True,exist_ok=True)
    write_atomic(ARCHIVE_CACHE/'inventory.json',inventory)
    archive_index.cache_clear()


def connect():
    WORK.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB, timeout=120)
    db.executescript('''
    CREATE TABLE IF NOT EXISTS manuscripts(path TEXT PRIMARY KEY, sha TEXT, pages INTEGER, tokens INTEGER);
    CREATE TABLE IF NOT EXISTS written(manuscript TEXT, form TEXT, spelling TEXT, occurrences INTEGER, first_page INTEGER, example TEXT,
        PRIMARY KEY(manuscript,form));
    CREATE INDEX IF NOT EXISTS written_form ON written(form);
    CREATE TABLE IF NOT EXISTS word_boundaries(path TEXT PRIMARY KEY, version TEXT);
    ''')
    return db


def analyze_witness(path):
    counts,first=Counter(),{}
    page_no=0
    for page_no,page in enumerate(page_stream(path),1):
        for block in native_blocks(page):
            tokens=written(block)
            for index,token in enumerate(tokens):
                form=normalize(token)
                counts[form]+=1
                if form not in first:
                    first[form]=(token,page_no,' '.join(tokens[max(0,index-3):index+4]))
    return page_no,counts.total(),[(w,first[w][0],n,*first[w][1:]) for w,n in counts.items()]


def scan(workers=6):
    from concurrent.futures import ProcessPoolExecutor,as_completed
    with connect() as db:
        active = set()
        needed=[]
        for path in publications():
            name = witness_name(path)
            active.add(name)
            digest = sha(path)
            if db.execute('SELECT 1 FROM manuscripts m JOIN word_boundaries b ON b.path=m.path WHERE m.path=? AND sha=? AND b.version=?',(name,digest,TOKENIZATION)).fetchone():
                continue
            needed.append((path,name,digest))
        with ProcessPoolExecutor(max_workers=workers) as pool:
            jobs={pool.submit(analyze_witness,p):(n,h) for p,n,h in sorted(needed,key=lambda a:-a[0].stat().st_size)}
            for completed,job in enumerate(as_completed(jobs),1):
                name,digest=jobs.pop(job)
                page_no,total,records=job.result()
                with db:
                    db.execute('DELETE FROM written WHERE manuscript=?',(name,))
                    db.executemany('INSERT INTO written VALUES(?,?,?,?,?,?)',((name,*r) for r in records))
                    db.execute('INSERT OR REPLACE INTO manuscripts VALUES(?,?,?,?)',(name,digest,page_no,total))
                    db.execute('INSERT OR REPLACE INTO word_boundaries VALUES(?,?)',(name,TOKENIZATION))
                print(f'{completed}/{len(needed)} · {page_no:5} pages, {len(records):6} forms | {name}',flush=True)
        for name, in db.execute('SELECT path FROM manuscripts').fetchall():
            if name not in active:
                db.execute('DELETE FROM manuscripts WHERE path=?',(name,))
                db.execute('DELETE FROM written WHERE manuscript=?',(name,))
                db.execute('DELETE FROM word_boundaries WHERE path=?',(name,))


if __name__ == '__main__':
    scan()
