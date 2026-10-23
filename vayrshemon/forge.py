"""Independent transactional language projects. Content hashes identify frozen versions.

SQLite serializes writers; generation guards prevent stale editors losing work.
Every branch owns an autosaved draft. A commit atomically freezes language,
dictionary, wiki, tests and editorial decisions. Document history is separate.
"""
from copy import deepcopy
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import uuid
from .authoring import stamp
from .language import empty_data, validate_data

FORMAT = 'vayrshemon.forge'
VERSION = '1.0.0'
NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$')


def encoded(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value): return hashlib.sha256(encoded(value).encode()).hexdigest()


def empty_snapshot():
    return dict(language=empty_data(), wiki=[], tests=[], decisions=[], research={})


def validate(snapshot):
    if set(snapshot) != {'language', 'wiki', 'tests', 'decisions', 'research'}:
        raise ValueError('FORGE_SNAPSHOT_FIELDS')
    if len(encoded(snapshot)) > 32*1024*1024: raise ValueError('FORGE_SNAPSHOT_LIMIT')
    validate_data(snapshot['language'])
    for kind in ('wiki', 'tests'):
        values=snapshot[kind]
        if not isinstance(values,list) or len(values)>2000: raise ValueError('FORGE_COLLECTION_LIMIT')
        seen=set()
        for row in values:
            if not isinstance(row,dict) or not NAME.fullmatch(row.get('id','')) or row['id'] in seen:
                raise ValueError('FORGE_RECORD_ID')
            seen.add(row['id'])
            fields={'id','title','body','ruleIds'} if kind=='wiki' else {'id','title','paragraphs','ruleIds'}
            if set(row)!=fields or not isinstance(row['title'],str) or len(row['title'])>200:
                raise ValueError('FORGE_RECORD_FIELDS')
            rules={r['id'] for r in snapshot['language']['grammar']}
            if not isinstance(row['ruleIds'],list) or not set(row['ruleIds'])<=rules:
                raise ValueError('FORGE_RULE_REFERENCE_MISSING')
            if kind=='wiki':
                if not isinstance(row['body'],str) or len(row['body'])>100000: raise ValueError('FORGE_WIKI_LIMIT')
            else:
                if not 1<=len(row['paragraphs'])<=20: raise ValueError('FORGE_TEST_PARAGRAPHS')
                for pair in row['paragraphs']:
                    if set(pair)!={'text','translation','analysis'} or any(not isinstance(t,str) or not 1<=len(t)<=10000 for t in pair.values()):
                        raise ValueError('FORGE_TEST_PAIR')
    if not isinstance(snapshot['decisions'],list) or not isinstance(snapshot['research'],dict):
        raise ValueError('FORGE_EDITORIAL_FIELDS')


class ForgeProject:
    def __init__(self,path):
        self.path=Path(path).resolve()
        self._validated=set()
        if not self.path.is_file(): raise ValueError('FORGE_PROJECT_NOT_FOUND')
        with self.connect() as db:
            meta=self._meta(db)
            if meta.get('format')!=FORMAT or meta.get('version')!=VERSION: raise ValueError('FORGE_FORMAT_UNSUPPORTED')
            if db.execute('PRAGMA quick_check').fetchone()[0]!='ok': raise ValueError('FORGE_DATABASE_CORRUPT')
        self.read()

    @classmethod
    def create(cls,path,title,snapshot=None):
        path=Path(path).resolve(); snapshot=deepcopy(snapshot or empty_snapshot());validate(snapshot)
        if not title.strip() or len(title)>200: raise ValueError('FORGE_TITLE_REQUIRED')
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb'): pass
        db=sqlite3.connect(path)
        try:
            db.executescript('''
                CREATE TABLE meta (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL);
                CREATE TABLE commits (id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE branches (name TEXT PRIMARY KEY, head TEXT NOT NULL REFERENCES commits(id), draft TEXT NOT NULL);
                CREATE TABLE runs (id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TRIGGER immutable_commit_update BEFORE UPDATE ON commits BEGIN SELECT RAISE(ABORT,'IMMUTABLE_COMMIT'); END;
                CREATE TRIGGER immutable_commit_delete BEFORE DELETE ON commits BEGIN SELECT RAISE(ABORT,'IMMUTABLE_COMMIT'); END;
            ''')
            revision=dict(parent=None,label='Initial archive',createdAt=stamp(),snapshot=snapshot)
            head=digest(revision)
            with db:
                db.execute('INSERT INTO commits VALUES (?,?)',(head,encoded(revision)))
                db.execute('INSERT INTO branches VALUES (?,?,?)',('main',head,encoded(snapshot)))
                db.execute('INSERT INTO meta VALUES (1,?)',(encoded(dict(format=FORMAT,version=VERSION,projectId=uuid.uuid4().hex,title=title,generation=0,branch='main')),))
        finally: db.close()
        return cls(path)

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=5)
        try:
            db.execute('PRAGMA foreign_keys=ON'); db.execute('PRAGMA synchronous=FULL')
            yield db
        finally: db.close()

    def _meta(self,db): return json.loads(db.execute('SELECT body FROM meta WHERE id=1').fetchone()[0])

    def _commit(self,db,key):
        row=db.execute('SELECT body FROM commits WHERE id=?',(key,)).fetchone()
        if not row: raise ValueError('FORGE_VERSION_NOT_FOUND')
        value=json.loads(row[0])
        if digest(value)!=key: raise ValueError('FORGE_COMMIT_HASH_MISMATCH')
        if key not in self._validated:
            validate(value['snapshot'])
            if len(self._validated)>64: self._validated.clear()
            self._validated.add(key)
        return value

    def read(self,version=None):
        with self.connect() as db:
            db.execute('BEGIN'); meta=self._meta(db)
            head,draft=db.execute('SELECT head,draft FROM branches WHERE name=?',(meta['branch'],)).fetchone()
            commit=self._commit(db,version or head); draft=json.loads(draft);validate(draft)
            value=commit['snapshot'] if version else draft
            return dict(**meta,path=str(self.path),head=head,selectedVersion=version,
                        dirty=digest(draft)!=digest(self._commit(db,head)['snapshot']),snapshot=value,
                        branches=[dict(name=n,head=h) for n,h in db.execute('SELECT name,head FROM branches ORDER BY name')])

    @contextmanager
    def writer(self,expected_generation):
        with self.connect() as db:
            try:
                db.execute('BEGIN IMMEDIATE');meta=self._meta(db)
                if type(expected_generation)!=int or expected_generation!=meta['generation']:
                    raise ValueError('STALE_FORGE_GENERATION: refresh the project before writing')
                yield db,meta
                meta['generation']+=1
                db.execute('UPDATE meta SET body=? WHERE id=1',(encoded(meta),));db.commit()
            except BaseException:
                db.rollback(); raise

    def put(self,collection,record,expected_generation):
        with self.writer(expected_generation) as (db,meta):
            draft=json.loads(db.execute('SELECT draft FROM branches WHERE name=?',(meta['branch'],)).fetchone()[0])
            rows=draft[collection] if collection in ('wiki','tests') else draft['language'][collection]
            old=next((i for i,r in enumerate(rows) if r['id']==record.get('id')),None)
            if old is None: rows.append(deepcopy(record))
            else: rows[old]=deepcopy(record)
            validate(draft)
            db.execute('UPDATE branches SET draft=? WHERE name=?',(encoded(draft),meta['branch']))
        return self.status()

    def replace_draft(self,snapshot,expected_generation):
        validate(snapshot)
        with self.writer(expected_generation) as (db,meta):
            db.execute('UPDATE branches SET draft=? WHERE name=?',(encoded(snapshot),meta['branch']))
        return self.status()

    def commit(self,label,expected_generation):
        if not label.strip() or len(label)>200: raise ValueError('FORGE_VERSION_LABEL_REQUIRED')
        with self.writer(expected_generation) as (db,meta):
            head,draft=db.execute('SELECT head,draft FROM branches WHERE name=?',(meta['branch'],)).fetchone()
            snapshot=json.loads(draft);validate(snapshot)
            if digest(snapshot)==digest(self._commit(db,head)['snapshot']): raise ValueError('FORGE_NO_CHANGES')
            value=dict(parent=head,label=label,createdAt=stamp(),snapshot=snapshot);key=digest(value)
            db.execute('INSERT INTO commits VALUES (?,?)',(key,encoded(value)))
            db.execute('UPDATE branches SET head=? WHERE name=?',(key,meta['branch']))
        return self.status()

    def branch(self,name,expected_generation,version=None):
        if not NAME.fullmatch(name): raise ValueError('FORGE_BRANCH_NAME')
        with self.writer(expected_generation) as (db,meta):
            head=version or db.execute('SELECT head FROM branches WHERE name=?',(meta['branch'],)).fetchone()[0]
            snapshot=self._commit(db,head)['snapshot']
            db.execute('INSERT INTO branches VALUES (?,?,?)',(name,head,encoded(snapshot)))
            meta['branch']=name
        return self.status()

    def checkout(self,name,expected_generation):
        with self.writer(expected_generation) as (db,meta):
            if not db.execute('SELECT 1 FROM branches WHERE name=?',(name,)).fetchone(): raise ValueError('FORGE_BRANCH_NOT_FOUND')
            meta['branch']=name
        return self.status()

    def history(self):
        with self.connect() as db:
            return [dict(id=key,**{k:v for k,v in self._commit(db,key).items() if k!='snapshot'}) for key, in db.execute('SELECT id FROM commits ORDER BY rowid DESC')]

    def status(self): return {k:v for k,v in self.read().items() if k!='snapshot'}

    def diff(self,before,after):
        a=self.read(before)['snapshot'];b=self.read(after)['snapshot'];result={}
        for key in (*a['language'],'wiki','tests'):
            aa={r['id']:r for r in (a[key] if key in a else a['language'][key])}
            bb={r['id']:r for r in (b[key] if key in b else b['language'][key])}
            result[key]=dict(added=sorted(bb.keys()-aa.keys()),removed=sorted(aa.keys()-bb.keys()),changed=sorted(k for k in aa.keys()&bb.keys() if aa[k]!=bb[k]))
        return dict(collections=result,decisionsChanged=a['decisions']!=b['decisions'],researchChanged=a['research']!=b['research'])

    def record_run(self,value):
        with self.connect() as db,db:
            self._commit(db,value['version'])
            db.execute('INSERT INTO runs VALUES (?,?)',(value['runId'],encoded(value)))

    def runs(self):
        with self.connect() as db: return [json.loads(row[0]) for row in db.execute('SELECT body FROM runs ORDER BY rowid DESC')]

    def export(self,path):
        from tools.recovery import exclusive_write
        with self.connect() as db:
            db.execute('BEGIN')
            data=dict(meta=self._meta(db),commits={k:self._commit(db,k) for k, in db.execute('SELECT id FROM commits')},
                      branches=[dict(name=n,head=h,draft=json.loads(d)) for n,h,d in db.execute('SELECT name,head,draft FROM branches')],
                      runs=[json.loads(b) for b, in db.execute('SELECT body FROM runs')])
        envelope=dict(format=FORMAT+'.bundle',formatVersion=VERSION,sha256=digest(data),data=data)
        exclusive_write(Path(path),encoded(envelope).encode());return dict(path=str(path),sha256=envelope['sha256'])

    @classmethod
    def restore(cls,path,destination):
        from tools.m0.common import load_json
        value=load_json(path);data=value['data']
        if value['format']!=FORMAT+'.bundle' or value['formatVersion']!=VERSION or value['sha256']!=digest(data): raise ValueError('FORGE_BUNDLE_INVALID')
        for key,commit in data['commits'].items():
            if digest(commit)!=key: raise ValueError('FORGE_BUNDLE_HASH_MISMATCH')
            validate(commit['snapshot'])
            if commit['parent'] is not None and commit['parent'] not in data['commits']: raise ValueError('FORGE_PARENT_MISSING')
        for b in data['branches']:
            validate(b['draft'])
            if not NAME.fullmatch(b['name']) or b['head'] not in data['commits']: raise ValueError('FORGE_BRANCH_INVALID')
        if data['meta']['branch'] not in [b['name'] for b in data['branches']]: raise ValueError('FORGE_ACTIVE_BRANCH_MISSING')
        project=cls.create(destination,data['meta']['title'])
        with project.connect() as db,db:
            # Replace only the temporary origin of this NEW destination. Never
            # alter a user project or a retained committed revision in place.
            db.execute('DELETE FROM branches')
            db.execute('DROP TRIGGER immutable_commit_delete')
            db.execute('DELETE FROM commits')
            db.execute("CREATE TRIGGER immutable_commit_delete BEFORE DELETE ON commits BEGIN SELECT RAISE(ABORT,'IMMUTABLE_COMMIT'); END")
            for key,commit in data['commits'].items(): db.execute('INSERT OR IGNORE INTO commits VALUES (?,?)',(key,encoded(commit)))
            for b in data['branches']: db.execute('INSERT INTO branches VALUES (?,?,?)',(b['name'],b['head'],encoded(b['draft'])))
            db.execute('UPDATE meta SET body=? WHERE id=1',(encoded(data['meta']),))
            for run in data['runs']:
                if run['version'] not in data['commits']: raise ValueError('FORGE_RUN_VERSION_MISSING')
                db.execute('INSERT INTO runs VALUES (?,?)',(run['runId'],encoded(run)))
        return project
