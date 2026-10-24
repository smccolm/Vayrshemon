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
SUPPORTED_VERSIONS = ('1.0.0','1.1.0','1.2.0','1.3.0','1.4.0')
NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$')


def encoded(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value): return hashlib.sha256(encoded(value).encode()).hexdigest()


def empty_snapshot():
    return dict(language=empty_data(), wiki=[], tests=[], decisions=[], research={})


def promote(meta,version):
    if tuple(map(int,version.split('.')))>tuple(map(int,meta['version'].split('.'))):meta['version']=version


def snapshot_version(snapshot):
    return '1.4.0' if 'reading' in snapshot or snapshot.get('variation',{}).get('formatVersion')=='1.2.0' else '1.3.0' if 'spelling' in snapshot or snapshot.get('variation',{}).get('formatVersion')=='1.1.0' else '1.2.0' if 'variation' in snapshot else '1.0.0'


def validate(snapshot):
    required={'language','wiki','tests','decisions','research'}
    if not required<=set(snapshot)<=required|{'laboratory','variation','spelling','reading'}:
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
            if set(row) not in (fields, fields|{'caseIds'} if kind=='tests' else fields) or not isinstance(row['title'],str) or len(row['title'])>200:
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
    if 'variation' in snapshot:
        from .variation import validate as validate_variation
        validate_variation(snapshot)
    if 'spelling' in snapshot:
        from .spelling import validate as validate_spelling
        validate_spelling(snapshot)
    if 'reading' in snapshot:
        from .reading import validate as validate_reading
        validate_reading(snapshot)
    if 'laboratory' in snapshot:
        from .forge_lab import validate_lab
        validate_lab(snapshot)
    cases={c['id']:c for c in snapshot.get('laboratory',{}).get('cases',[])}
    for test in snapshot['tests']:
        if 'caseIds' not in test: continue
        bindings=test['caseIds']
        if not isinstance(bindings,list) or len(bindings)!=len(test['paragraphs']): raise ValueError('LAB_PAGE_BINDINGS')
        for ids,pair in zip(bindings,test['paragraphs']):
            if not isinstance(ids,list) or not 1<=len(ids)<=256 or any(i not in cases or cases[i]['kind']!='clause' or cases[i]['expected']!='accept' for i in ids): raise ValueError('LAB_PAGE_CASE_REFERENCE')
            if ' '.join(cases[i]['text'] for i in ids)!=pair['text']: raise ValueError('LAB_PAGE_CASE_TEXT_MISMATCH: edit the bound cases and page together, or explicitly remove the bindings')
            for index,cid in enumerate(ids):
                if cases[cid].get('antecedent') and (index==0 or cases[cid]['antecedent']['caseId']!=ids[index-1]):raise ValueError('LAB_PAGE_ANTECEDENT_NOT_ADJACENT')


class ForgeProject:
    def __init__(self,path):
        self.path=Path(path).resolve()
        self._validated=set()
        if not self.path.is_file(): raise ValueError('FORGE_PROJECT_NOT_FOUND')
        with self.connect() as db:
            meta=self._meta(db)
            if meta.get('format')!=FORMAT or meta.get('version') not in SUPPORTED_VERSIONS: raise ValueError('FORGE_FORMAT_UNSUPPORTED')
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
                db.execute('INSERT INTO meta VALUES (1,?)',(encoded(dict(format=FORMAT,version=snapshot_version(snapshot),projectId=uuid.uuid4().hex,title=title,generation=0,branch='main')),))
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
            promote(meta,snapshot_version(snapshot))
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
            rows=[dict(id=key,**{k:v for k,v in self._commit(db,key).items() if k!='snapshot'}) for key, in db.execute('SELECT id FROM commits')]
            # Bundle JSON canonicalizes hash keys, so restore insertion order is
            # not history. Sort immutable timestamps with a deterministic tie.
            return sorted(rows,key=lambda r:(r['createdAt'],r['id']),reverse=True)

    def status(self): return {k:v for k,v in self.read().items() if k!='snapshot'}

    def diff(self,before,after):
        a=self.read(before)['snapshot'];b=self.read(after)['snapshot'];result={}
        for key in (*a['language'],'wiki','tests'):
            aa={r['id']:r for r in (a[key] if key in a else a['language'][key])}
            bb={r['id']:r for r in (b[key] if key in b else b['language'][key])}
            result[key]=dict(added=sorted(bb.keys()-aa.keys()),removed=sorted(aa.keys()-bb.keys()),changed=sorted(k for k in aa.keys()&bb.keys() if aa[k]!=bb[k]))
        for kind in ('rules','cases'):
            aa={r['id']:r for r in a.get('laboratory',{}).get(kind,[])}
            bb={r['id']:r for r in b.get('laboratory',{}).get(kind,[])}
            result['laboratory.'+kind]=dict(added=sorted(bb.keys()-aa.keys()),removed=sorted(aa.keys()-bb.keys()),changed=sorted(k for k in aa.keys()&bb.keys() if aa[k]!=bb[k]))
        return dict(collections=result,decisionsChanged=a['decisions']!=b['decisions'],researchChanged=a['research']!=b['research'],variationChanged=a.get('variation')!=b.get('variation'),spellingChanged=a.get('spelling')!=b.get('spelling'),readingChanged=a.get('reading')!=b.get('reading'))

    def lab_edit(self,collection,expected_generation,record=None,record_id=None):
        from .forge_lab import empty_lab
        if collection not in ('rules','cases'): raise ValueError('LAB_COLLECTION')
        with self.writer(expected_generation) as (db,meta):
            draft=json.loads(db.execute('SELECT draft FROM branches WHERE name=?',(meta['branch'],)).fetchone()[0])
            rows=draft.setdefault('laboratory',empty_lab())[collection]
            key=record['id'] if record is not None else record_id
            index=next((i for i,r in enumerate(rows) if r['id']==key),None)
            if record is None:
                if index is None: raise ValueError('LAB_RECORD_NOT_FOUND')
                rows.pop(index)
            elif index is None: rows.append(deepcopy(record))
            else: rows[index]=deepcopy(record)
            validate(draft)
            db.execute('UPDATE branches SET draft=? WHERE name=?',(encoded(draft),meta['branch']))
        return self.status()

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
            from .forge_release import read_all
            releases=read_all(db)
            if releases: data['releases']=releases
        envelope=dict(format=FORMAT+'.bundle',formatVersion=data['meta']['version'],sha256=digest(data),data=data)
        exclusive_write(Path(path),encoded(envelope).encode());return dict(path=str(path),sha256=envelope['sha256'])

    @classmethod
    def restore(cls,path,destination):
        from tools.m0.common import load_json
        value=load_json(path);data=value['data']
        if value['format']!=FORMAT+'.bundle' or value['formatVersion'] not in SUPPORTED_VERSIONS or value['formatVersion']!=data['meta']['version'] or value['sha256']!=digest(data): raise ValueError('FORGE_BUNDLE_INVALID')
        for key,commit in data['commits'].items():
            if digest(commit)!=key: raise ValueError('FORGE_BUNDLE_HASH_MISMATCH')
            validate(commit['snapshot'])
            from .forge_merge import parents
            if any(p not in data['commits'] for p in parents(commit)): raise ValueError('FORGE_PARENT_MISSING')
        from .forge_release import validate_release,ensure_table
        for release in data.get('releases',[]):
            validate_release(release['releaseId'],{k:v for k,v in release.items() if k!='releaseId'},data['commits'])
            if release['projectId']!=data['meta']['projectId']: raise ValueError('RELEASE_PROJECT_MISMATCH')
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
            if data.get('releases'):
                ensure_table(db)
                for release in data['releases']:
                    db.execute('INSERT INTO releases VALUES (?,?,?)',(release['name'],release['releaseId'],encoded({k:v for k,v in release.items() if k!='releaseId'})))
        return project
