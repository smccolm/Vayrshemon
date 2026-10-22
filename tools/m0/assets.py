"""Inventory original assets without modifying or copying their contents."""

from collections import Counter, defaultdict
import os
from pathlib import Path

from .common import asset_id, confined_path, file_hash


def catalog_assets(archive, selections, progress=lambda **event: None):
    archive = Path(archive).resolve()
    if not archive.is_dir():
        raise ValueError("ARCHIVE_MISSING")
    selected = {item["path"]: item for item in selections["assets"]}
    paths = []
    for directory, folders, files in os.walk(archive, followlinks=False):
        for name in folders + files:
            path = Path(directory, name)
            stat = path.lstat()
            if path.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
                raise ValueError(f"ARCHIVE_LINK_REJECTED: {path.relative_to(archive)}")
        paths.extend(Path(directory, name) for name in files)
    paths.sort(key=lambda path: path.relative_to(archive).as_posix())
    records = []
    contents = defaultdict(list)
    stems = defaultdict(list)
    for index, path in enumerate(paths):
        relative = path.relative_to(archive).as_posix()
        digest = file_hash(path)
        selection = selected.get(relative)
        record = {
            "assetId": asset_id(relative), "path": relative,
            "sha256": digest, "bytes": path.stat().st_size,
            "extension": path.suffix.lower(),
            "reviewStatus": selection["reviewStatus"] if selection else "catalogued",
            "roles": selection["roles"] if selection else [],
        }
        records.append(record)
        contents[digest].append(record["assetId"])
        stems[path.with_suffix("").relative_to(archive).as_posix().casefold()].append(record)
        if (index + 1) % 100 == 0 or index + 1 == len(paths):
            progress(code="CATALOG_PROGRESS", completed=index + 1, total=len(paths))
    missing = sorted(set(selected) - {record["path"] for record in records})
    if missing:
        raise ValueError("SELECTED_ASSET_MISSING: " + ", ".join(missing))
    relations = []
    for digest, members in sorted(contents.items()):
        if len(members) > 1:
            relations.append({"type": "identical-content", "status": "verified",
                              "sha256": digest, "assetIds": members})
    for stem, members in sorted(stems.items()):
        if len({item["extension"] for item in members}) > 1:
            relations.append({"type": "same-stem-candidate", "status": "unverified",
                              "stem": stem, "assetIds": [item["assetId"] for item in members]})
    for relation in selections["relationships"]:
        paths_in_relation = [relation["from"], relation["to"], relation["evidencePath"]]
        if any(path not in {r["path"] for r in records} for path in paths_in_relation):
            raise ValueError("RELATIONSHIP_ASSET_MISSING")
        relations.append({"type": relation["type"], "status": relation.get("status", "source-attested"),
                          "assetIds": [asset_id(relation["from"]), asset_id(relation["to"])],
                          "evidenceAssetId": asset_id(relation["evidencePath"]),
                          "locator": relation["locator"]})
    return {
        "schemaVersion": "0.1.0", "archiveRoot": "Inputs",
        "summary": {"fileCount": len(records), "totalBytes": sum(r["bytes"] for r in records),
                    "extensions": dict(sorted(Counter(r["extension"] for r in records).items()))},
        "assets": records, "relationships": relations,
    }


def verify_assets(archive, catalog, selected_paths=None):
    archive = Path(archive).resolve()
    wanted = None if selected_paths is None else set(selected_paths)
    known = {item["path"] for item in catalog["assets"]}
    if wanted is not None and wanted - known:
        raise ValueError("ASSET_NOT_CATALOGUED: " + ", ".join(sorted(wanted - known)))
    checked, issues = 0, []
    if wanted is None and archive.is_dir():
        present = {path.relative_to(archive).as_posix() for path in archive.rglob("*") if path.is_file()}
        issues.extend({"path": path, "code": "ASSET_NOT_CATALOGUED"} for path in sorted(present - known))
    for record in catalog["assets"]:
        if wanted is not None and record["path"] not in wanted:
            continue
        path = confined_path(archive, record["path"])
        if not path.is_file():
            issues.append({"path": record["path"], "code": "ASSET_MISSING"})
        elif file_hash(path) != record["sha256"]:
            issues.append({"path": record["path"], "code": "ASSET_HASH_MISMATCH"})
        checked += 1
    return {"checked": checked, "issues": issues, "ok": not issues}
