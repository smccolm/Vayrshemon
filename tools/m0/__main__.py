"""Machine-readable evidence CLI with correlated JSONL diagnostics."""

import argparse
import base64
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import traceback
import uuid

from . import VERSION
from .assets import catalog_assets, verify_assets
from .common import json_text, load_json, write_json
from .docx import extract_docx
from .fonts import font_registry
from .mapping import build_mapping, decode_legacy, restore_legacy


class Diagnostics(logging.Handler):
    def __init__(self, trace_id, log_path):
        super().__init__()
        self.trace_id = trace_id
        self.file = None
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self.file = log_path.open("a", encoding="utf-8", newline="\n")

    def event(self, level="info", **fields):
        payload = {"timestamp": datetime.now(timezone.utc).isoformat(), "level": level,
                   "subsystem": "m0-evidence", "traceId": self.trace_id, "toolVersion": VERSION, **fields}
        line = json.dumps(payload, ensure_ascii=True, allow_nan=False)
        print(line, file=sys.stderr, flush=True)
        if self.file:
            self.file.write(line + "\n")
            self.file.flush()

    def emit(self, record):
        self.event(level=record.levelname.lower(), code="LIBRARY_LOG", logger=record.name, message=record.getMessage())

    def close(self):
        if self.file:
            self.file.close()
            self.file = None
        super().close()


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    result.add_argument("--log", type=Path)
    sub = result.add_subparsers(dest="command", required=True)
    for name in ("catalog", "fonts", "mapping", "fixtures", "check", "verify-assets", "capabilities"):
        command = sub.add_parser(name)
        command.add_argument("--out", type=Path)
        if name in ("catalog", "fonts", "verify-assets"):
            command.add_argument("--archive", type=Path)
        if name == "verify-assets":
            command.add_argument("--all", action="store_true", help="Hash the entire archive; default checks selected assets")
    extract = sub.add_parser("extract-docx")
    extract.add_argument("path", type=Path)
    extract.add_argument("--out", type=Path)
    decode = sub.add_parser("decode-legacy")
    decode.add_argument("path", type=Path)
    decode.add_argument("--encoding", required=True, choices=("utf-8", "utf-8-sig", "cp1252", "utf-16"))
    decode.add_argument("--font-sha256", required=True)
    decode.add_argument("--out", type=Path)
    return result


def run(args, log):
    root = args.root.resolve()
    data = root / "data"
    archive = getattr(args, "archive", None) or root / "Inputs"
    if args.command == "catalog":
        return catalog_assets(archive, load_json(data / "source-selections.json"), log.event)
    if args.command == "fonts":
        return font_registry(archive, load_json(data / "assets.json"), log.event)
    if args.command == "mapping":
        return build_mapping(load_json(data / "orthography/chart-transcription.json"),
                             load_json(data / "fonts.json"), load_json(data / "assets.json"))
    if args.command == "verify-assets":
        selected = None if args.all else [item["path"] for item in load_json(data / "source-selections.json")["assets"]]
        return verify_assets(archive, load_json(data / "assets.json"), selected)
    if args.command == "extract-docx":
        return extract_docx(args.path)
    if args.command == "decode-legacy":
        original = args.path.read_bytes()
        # Strict decoding deliberately fails on invalid bytes; no replacement
        # or fallback codec is ever selected implicitly.
        text = original.decode(args.encoding, errors="strict")
        decoded = decode_legacy(text, load_json(data / "orthography/thimfora-79.json"), args.font_sha256)
        restore_legacy(decoded)
        decoded["sourceEncoding"] = args.encoding
        decoded["sourceBytesBase64"] = base64.b64encode(original).decode("ascii")
        return decoded
    if args.command == "capabilities":
        return load_json(data / "capabilities.json")
    if args.command == "fixtures":
        from .fixtures import build_fixtures
        return build_fixtures(load_json(data / "assets.json"), load_json(data / "fonts.json"))
    if args.command == "check":
        from .contracts import check_repository
        return check_repository(root)
    raise ValueError("UNKNOWN_COMMAND")


def main():
    args = parser().parse_args()
    archive = (getattr(args, "archive", None) or args.root / "Inputs").resolve()
    protected = (args.root / "Inputs").resolve()
    for output in (args.out, args.log):
        if output and (output.resolve().is_relative_to(archive) or output.resolve().is_relative_to(protected)
                       or (getattr(args, "path", None) and output.resolve() == args.path.resolve())):
            print(json.dumps({"level": "error", "code": "ORIGINAL_SOURCE_OUTPUT_REJECTED"}), file=sys.stderr)
            return 1
    log = Diagnostics(str(uuid.uuid4()), args.log)
    logging.getLogger().addHandler(log)
    try:
        log.event(code="COMMAND_STARTED", command=args.command)
        value = run(args, log)
        if args.out:
            write_json(args.out, value)
            print(json_text({"ok": value.get("ok", True), "output": str(args.out), "traceId": log.trace_id}), end="")
        else:
            print(json_text(value), end="")
        success = value.get("ok", True)
        log.event(code="COMMAND_COMPLETED", command=args.command, ok=success)
        return 0 if success else 1
    except Exception as error:
        log.event(level="error", code="COMMAND_FAILED", command=args.command,
                  message=str(error), exceptionType=type(error).__name__, traceback=traceback.format_exc())
        return 1
    finally:
        logging.getLogger().removeHandler(log)
        log.close()


if __name__ == "__main__":
    sys.exit(main())
