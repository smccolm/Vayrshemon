"""Deterministic three-way merges of frozen language snapshots, never drafts.

Record arrays merge by stable ID; ordinary arrays (word order, source witnesses,
paragraphs) are atomic. Missing values differ from JSON null. Resolutions and both
parents are part of the immutable commit, not transient editor preferences.
"""
from copy import deepcopy
import json
from .forge import digest, encoded, validate
from .authoring import stamp

MISSING = object()


def parents(commit):
    values = commit.get('parents', [commit['parent']] if commit['parent'] else [])
    if (not isinstance(values, list) or len(values) > 2 or len(set(values)) != len(values)
            or any(not isinstance(p, str) for p in values)
            or (values[0] if values else None) != commit['parent']):
        raise ValueError('FORGE_PARENT_INVALID')
    return values


def ancestors(project, db, head):
    found = set(); todo = [head]
    while todo:
        key = todo.pop()
        if key in found: continue
        found.add(key)
        if len(found) > 10000: raise ValueError('MERGE_HISTORY_LIMIT')
        todo.extend(parents(project._commit(db, key)))
    return found


def boxed(value):
    return {'present': False} if value is MISSING else {'present': True, 'value': deepcopy(value)}


def merge_values(base, ours, theirs, resolutions, conflicts, path=''):
    if ours == theirs: return deepcopy(ours) if ours is not MISSING else MISSING
    if ours == base: return deepcopy(theirs) if theirs is not MISSING else MISSING
    if theirs == base: return deepcopy(ours) if ours is not MISSING else MISSING
    if all(isinstance(v, dict) for v in (base, ours, theirs)):
        result = {}
        for key in sorted(base.keys() | ours.keys() | theirs.keys()):
            pointer = path + '/' + key.replace('~', '~0').replace('/', '~1')
            value = merge_values(base.get(key, MISSING), ours.get(key, MISSING), theirs.get(key, MISSING), resolutions, conflicts, pointer)
            if value is not MISSING: result[key] = value
        return result
    if all(isinstance(v, list) and all(isinstance(r, dict) and isinstance(r.get('id'), str) for r in v) for v in (base, ours, theirs)):
        maps = [{r['id']: r for r in rows} for rows in (base, ours, theirs)]
        if any(len(m) != len(v) for m, v in zip(maps, (base, ours, theirs))): raise ValueError('MERGE_DUPLICATE_ID')
        result = []
        for key in dict.fromkeys([r['id'] for r in ours + theirs + base]):
            pointer = path + '/' + key.replace('~', '~0').replace('/', '~1')
            value = merge_values(*(m.get(key, MISSING) for m in maps), resolutions, conflicts, pointer)
            if value is not MISSING: result.append(value)
        return result
    conflict = dict(path=path, base=boxed(base), ours=boxed(ours), theirs=boxed(theirs))
    conflicts.append(conflict)
    resolution = resolutions.get(path)
    if resolution is None: return ours  # Preview only; applying requires every choice.
    if not isinstance(resolution, dict): raise ValueError('MERGE_RESOLUTION_INVALID')
    choice = resolution.get('choice')
    if choice == 'custom' and set(resolution) == {'choice', 'value'}: return deepcopy(resolution['value'])
    if set(resolution) != {'choice'} or choice not in ('ours', 'theirs', 'base', 'delete'): raise ValueError('MERGE_RESOLUTION_INVALID')
    return {'ours': ours, 'theirs': theirs, 'base': base, 'delete': MISSING}[choice]


def calculate(project, db, meta, source, resolutions=None):
    row = db.execute('SELECT head,draft FROM branches WHERE name=?', (meta['branch'],)).fetchone()
    ours, draft = row; source_row = db.execute('SELECT head FROM branches WHERE name=?', (source,)).fetchone()
    if not source_row: raise ValueError('MERGE_SOURCE_BRANCH_MISSING')
    theirs = source_row[0]
    if digest(json.loads(draft)) != digest(project._commit(db, ours)['snapshot']):
        raise ValueError('MERGE_TARGET_DRAFT_DIRTY: commit the target draft first; all branch drafts remain saved')
    a = ancestors(project, db, ours); b = ancestors(project, db, theirs)
    if theirs in a: raise ValueError('MERGE_ALREADY_CONTAINED')
    common = a & b
    if not common: raise ValueError('MERGE_NO_COMMON_ANCESTOR')
    obsolete = set()
    for key in common: obsolete.update(ancestors(project, db, key) - {key})
    bases = common - obsolete
    if len(bases) != 1: raise ValueError('MERGE_AMBIGUOUS_BASE: criss-cross history needs an explicit intermediate merge')
    base = bases.pop(); conflicts = []
    snapshot = merge_values(*(project._commit(db, k)['snapshot'] for k in (base, ours, theirs)), resolutions or {}, conflicts)
    plan = dict(projectId=meta['projectId'], generation=meta['generation'], target=meta['branch'], source=source,
                base=base, ours=ours, theirs=theirs, conflicts=conflicts)
    plan['planId'] = digest(plan)
    return plan, snapshot


def preview(project, source):
    with project.connect() as db:
        db.execute('BEGIN')
        plan, snapshot = calculate(project, db, project._meta(db), source)
        try: validate(snapshot); plan['validationError'] = None
        except ValueError as error: plan['validationError'] = str(error)
        return plan


def apply(project, source, plan_id, label, resolutions, expected_generation):
    if not isinstance(label, str) or not label.strip() or len(label) > 200: raise ValueError('FORGE_VERSION_LABEL_REQUIRED')
    if not isinstance(resolutions, dict): raise ValueError('MERGE_RESOLUTION_INVALID')
    with project.writer(expected_generation) as (db, meta):
        plan, snapshot = calculate(project, db, meta, source, resolutions)
        if plan['planId'] != plan_id: raise ValueError('MERGE_STALE_PLAN')
        if set(resolutions) != {c['path'] for c in plan['conflicts']}: raise ValueError('MERGE_UNRESOLVED_OR_UNKNOWN_CONFLICT')
        validate(snapshot)
        # Older executables must reject this graph rather than export only its
        # first-parent history or silently drop release records.
        meta['version']='1.1.0'
        commit = dict(parent=plan['ours'], parents=[plan['ours'], plan['theirs']], label=label, createdAt=stamp(), snapshot=snapshot,
                      merge=dict(base=plan['base'], sourceBranch=source, targetBranch=meta['branch'], planId=plan_id, resolutions=deepcopy(resolutions)))
        key = digest(commit)
        db.execute('INSERT INTO commits VALUES (?,?)', (key, encoded(commit)))
        db.execute('UPDATE branches SET head=?,draft=? WHERE name=?', (key, encoded(snapshot), meta['branch']))
    return dict(project.status(), mergeVersion=key)
