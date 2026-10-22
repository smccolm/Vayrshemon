"""Deterministic JSON, asset identity, and local path handling."""

import hashlib
import json
import os
from pathlib import Path
import tempfile


def load_json(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_JSON_KEY: " + key)
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError("NONFINITE_JSON_NUMBER: " + value)

    return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      object_pairs_hook=unique_pairs, parse_constant=reject_constant)


def json_text(value):
    return json.dumps(value, ensure_ascii=True, indent=2, allow_nan=False) + "\n"


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(json_text(value))
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def file_hash(path):
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError(f"ASSET_CHANGED_DURING_READ: {path.name}")
    return digest.hexdigest()


def asset_id(relative_path):
    return "asset:" + hashlib.sha256(relative_path.encode("utf-8")).hexdigest()


def confined_path(root, relative_path):
    """Resolve a portable relative path, rejecting escapes and Windows syntax."""
    if not relative_path or "\\" in relative_path or ":" in relative_path:
        raise ValueError("INVALID_ASSET_PATH")
    parts = relative_path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError("INVALID_ASSET_PATH")
    root = Path(root).resolve()
    path = root.joinpath(*parts).resolve()
    if not path.is_relative_to(root):
        raise ValueError("ASSET_PATH_ESCAPE")
    return path


def asset_ref(catalog, relative_path):
    for asset in catalog["assets"]:
        if asset["path"] == relative_path:
            return {key: asset[key] for key in ("assetId", "path", "sha256")}
    raise ValueError(f"ASSET_NOT_CATALOGUED: {relative_path}")
