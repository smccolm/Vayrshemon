"""Immutable named language releases with pinned, independently checked evidence."""
from pathlib import Path
import json
from .forge import NAME, digest, encoded, promote
from .authoring import stamp
from . import forge_lab


def table_exists(db):
    return bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='releases'").fetchone())


def ensure_table(db):
    db.execute('CREATE TABLE IF NOT EXISTS releases (name TEXT PRIMARY KEY, id TEXT UNIQUE NOT NULL, body TEXT NOT NULL)')
    for action in ('UPDATE', 'DELETE'):
        db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_release_{action.lower()} BEFORE {action} ON releases BEGIN SELECT RAISE(ABORT,'IMMUTABLE_RELEASE'); END")


def validate_release(key, value, commits):
    if digest(value) != key or value['version'] not in commits: raise ValueError('RELEASE_HASH_OR_VERSION_INVALID')
    if not NAME.fullmatch(value['name']) or value['channel'] not in ('experimental', 'stable'): raise ValueError('RELEASE_METADATA_INVALID')
    if value['snapshotSha256'] != digest(commits[value['version']]['snapshot']): raise ValueError('RELEASE_SNAPSHOT_MISMATCH')
    for report in (value['suite'], value['workbench']):
        if report['version'] != value['version'] or report['projectId'] != value['projectId']: raise ValueError('RELEASE_EVIDENCE_VERSION_MISMATCH')


def read_all(db):
    if not table_exists(db): return []
    result = []
    for key, body in db.execute('SELECT id,body FROM releases ORDER BY rowid DESC'):
        value = json.loads(body)
        if digest(value) != key: raise ValueError('RELEASE_HASH_MISMATCH')
        result.append(dict(releaseId=key, **value))
    return result


def list_releases(project):
    with project.connect() as db: return read_all(db)


def create(project, name, version, channel, notes, suite_run_id, workbench_run_id, expected_generation, reviewer=''):
    if not NAME.fullmatch(name) or channel not in ('experimental', 'stable'): raise ValueError('RELEASE_NAME_OR_CHANNEL_INVALID')
    if not notes.strip() or len(notes) > 20000 or len(reviewer) > 200: raise ValueError('RELEASE_NOTES_REQUIRED')
    from tools.m0.common import file_hash, load_json
    with project.writer(expected_generation) as (db, meta):
        snapshot = project._commit(db, version)['snapshot']; fresh = forge_lab.evaluate(snapshot)
        def run(key):
            row = db.execute('SELECT body FROM runs WHERE id=?', (key,)).fetchone()
            if not row: raise ValueError('RELEASE_RUN_MISSING')
            value = json.loads(row[0])
            if value['version'] != version or value['projectId'] != meta['projectId']: raise ValueError('RELEASE_RUN_VERSION_MISMATCH')
            if value['status'] in ('Fail', 'Error'): raise ValueError('RELEASE_TEST_FAILURE')
            if load_json(value['manifestPath']) != value: raise ValueError('RELEASE_RUN_MANIFEST_CHANGED')
            return value
        suite = run(suite_run_id); page = run(workbench_run_id)
        if suite.get('kind') != 'language-suite' or not page.get('document'): raise ValueError('RELEASE_EVIDENCE_KIND')
        if any(suite.get(k) != v for k, v in fresh.items()): raise ValueError('RELEASE_SUITE_STALE')
        if not fresh['caseCount'] or fresh['counts'].get('Fail'): raise ValueError('RELEASE_TEST_FAILURE')
        if page.get('test') not in snapshot['tests'] or not page.get('test', {}).get('caseIds'): raise ValueError('RELEASE_BOUND_PAGE_REQUIRED')
        for path, sha in [(page['document'], page['documentSha256']), (page['proof'], page['proofSha256']),
                          (page['languageResults']['path'], page['languageResults']['sha256'])]:
            if file_hash(Path(path)) != sha: raise ValueError('RELEASE_ARTIFACT_CHANGED: ' + path)
        if load_json(page['languageResults']['path']) != fresh: raise ValueError('RELEASE_PAGE_SUITE_MISMATCH')
        if 'variation' in snapshot:
            from .variation import audit
            evidence=page.get('variationResults')
            if not evidence or file_hash(Path(evidence['path']))!=evidence['sha256'] or load_json(evidence['path'])!=audit(snapshot,page['testId']):
                raise ValueError('RELEASE_VARIATION_EVIDENCE_MISMATCH')
        if any(c['status'] in ('Fail', 'Error') for c in page['checks']): raise ValueError('RELEASE_TEST_FAILURE')
        if channel == 'stable' and (fresh['status'] != 'Pass' or fresh['unimplementedGrammar']
                or any(c['status'] != 'Pass' for c in page['checks']) or not reviewer.strip()):
            raise ValueError('RELEASE_STABLE_GATES: all assertions, coverage scope and page checks must pass; name the accepting reviewer')
        value = dict(format='vayrshemon.language-release', formatVersion='1.0.0', projectId=meta['projectId'], name=name,
                     version=version, snapshotSha256=digest(snapshot), channel=channel, notes=notes, createdAt=stamp(),
                     acceptance=dict(status='accepted' if channel == 'stable' else 'proposed', reviewer=reviewer), suite=suite, workbench=page)
        key = digest(value); ensure_table(db); promote(meta,'1.2.0' if 'variation' in snapshot else '1.1.0')
        if db.execute('SELECT 1 FROM releases WHERE name=?', (name,)).fetchone(): raise ValueError('RELEASE_NAME_EXISTS')
        db.execute('INSERT INTO releases VALUES (?,?,?)', (name, key, encoded(value)))
    return dict(releaseId=key, **value)


def export(project, name, path):
    from tools.recovery import exclusive_write
    value = next((r for r in list_releases(project) if r['name'] == name), None)
    if value is None: raise ValueError('RELEASE_NOT_FOUND')
    with project.connect() as db: commit = project._commit(db, value['version'])
    data = dict(release=value, commit=commit)
    # Portable dictionary, grammar, wiki and assertions with embedded reports.
    # Font/proof binaries stay separate; their hashes and original paths remain.
    envelope = dict(format='vayrshemon.language-release.bundle', formatVersion='1.0.0', sha256=digest(data), data=data)
    exclusive_write(Path(path), encoded(envelope).encode())
    return dict(path=str(path), sha256=envelope['sha256'], releaseId=value['releaseId'])
