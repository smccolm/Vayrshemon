import copy
from contextlib import contextmanager
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import unittest
import uuid
from zipfile import ZipFile

from tools.m0.assets import catalog_assets, verify_assets
from tools.m0.common import confined_path, file_hash, load_json, write_json
from tools.m0.contracts import check_repository, validate_document_semantics, validators
from tools.m0.docx import extract_docx
from tools.m0.fonts import font_registry
from tools.m0.mapping import decode_legacy, restore_legacy
from tools.m0.synthetic import make_font

ROOT = Path(__file__).resolve().parents[1]
EMPTY_SELECTIONS = {"assets": [], "relationships": []}


@contextmanager
def workspace_temporary_directory():
    # Ordinary inherited directory permissions also work under Windows
    # restricted tokens; Python 3.12.7 mkdtemp's private ACL does not.
    base = (ROOT / ".local/test-work").resolve()
    if not base.is_relative_to(ROOT.resolve()):
        raise ValueError("TEST_TEMP_PATH_ESCAPE")
    path = base / str(uuid.uuid4())
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        resolved = path.resolve()
        if resolved.parent != base or path.is_symlink():
            raise ValueError("TEST_TEMP_CLEANUP_PATH_CHANGED")
        shutil.rmtree(resolved)


class MappingPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping = load_json(ROOT / "data/orthography/thimfora-79.json")
        cls.font = cls.mapping["fontSha256s"][0]

    def test_all_chart_forms_and_digits_have_distinct_slots(self):
        letters = [entry for entry in self.mapping["entries"] if entry["kind"] == "letter"]
        self.assertEqual(len(letters), 94)
        self.assertEqual(len({entry["symbolId"] for entry in letters}), 47)
        for identity in {entry["symbolId"] for entry in letters}:
            self.assertEqual({entry["form"] for entry in letters if entry["symbolId"] == identity}, {"maxima", "minima"})
        digits = [entry for entry in self.mapping["entries"] if entry["kind"] == "digit"]
        self.assertEqual({entry["scalar"] for entry in digits}, set(range(48, 58)) | {192, 193})
        self.assertEqual([item["value"] for item in self.mapping["inventory"] if item["kind"] == "digit"], list(range(12)))

    def test_independently_transcribed_chart_slots(self):
        entries = {entry["scalar"]: entry for entry in self.mapping["entries"]}
        self.assertEqual((entries[74]["symbolId"], entries[106]["form"]), ("thimfora.letter.001", "minima"))
        self.assertEqual(entries[195]["symbolId"], "thimfora.letter.002")
        self.assertEqual(entries[193]["symbolId"], "unta.digit.11")
        self.assertNotEqual(entries[210]["symbolId"], entries[212]["symbolId"])

    def test_every_encoded_slot_round_trips_including_unresolved(self):
        text = "".join(chr(entry["scalar"]) for entry in self.mapping["entries"])
        decoded = decode_legacy(text, self.mapping, self.font)
        self.assertEqual(restore_legacy(decoded), text)
        self.assertEqual(sum(unit["status"] == "unresolved" for unit in decoded["units"]), 13)

    def test_unknown_unicode_is_preserved_without_normalization(self):
        text = "A\u0301 Á\u00a0\t\r\n\x00😀\u00be"
        decoded = decode_legacy(text, self.mapping, self.font)
        self.assertEqual(restore_legacy(decoded), text)
        emoji = next(unit for unit in decoded["units"] if unit["sourceScalar"] == 0x1F600)
        self.assertEqual(emoji["offset"], text.index("😀"))
        self.assertEqual(emoji["status"], "unresolved")
        self.assertIsNone(emoji["symbolId"])

    def test_seeded_arbitrary_scalars_survive(self):
        randomizer = random.Random(20261022)
        scalars = [randomizer.randrange(0x110000) for _ in range(1000)]
        text = "".join(chr(value) for value in scalars if not 0xD800 <= value <= 0xDFFF)
        self.assertEqual(restore_legacy(decode_legacy(text, self.mapping, self.font)), text)

    def test_wrong_font_never_applies_profile(self):
        with self.assertRaisesRegex(ValueError, "MAPPING_FONT_MISMATCH"):
            decode_legacy("Jj", self.mapping, "0" * 64)

    def test_lone_surrogate_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_UNICODE_SCALAR"):
            decode_legacy("\ud800", self.mapping, self.font)

    def test_corrupted_roundtrip_is_detected(self):
        decoded = decode_legacy("Jj", self.mapping, self.font)
        decoded["units"][0]["sourceScalar"] = 75
        with self.assertRaisesRegex(ValueError, "LEGACY_ROUNDTRIP_MISMATCH"):
            restore_legacy(decoded)


class AssetAndFontTests(unittest.TestCase):
    def test_catalog_is_deterministic_and_relationships_are_distinct(self):
        with workspace_temporary_directory() as folder:
            root = Path(folder)
            (root / "source.txt").write_bytes(b"original")
            (root / "copy.txt").write_bytes(b"original")
            (root / "source.png").write_bytes(b"different")
            catalog = catalog_assets(root, EMPTY_SELECTIONS)
            self.assertEqual(catalog, catalog_assets(root, EMPTY_SELECTIONS))
            relations = {item["type"]: item for item in catalog["relationships"]}
            self.assertEqual(relations["identical-content"]["status"], "verified")
            self.assertEqual(relations["same-stem-candidate"]["status"], "unverified")
            self.assertEqual((root / "source.txt").read_bytes(), b"original")

    def test_missing_changed_and_uncatalogued_assets_are_reported(self):
        with workspace_temporary_directory() as folder:
            root = Path(folder)
            (root / "a").write_bytes(b"a")
            (root / "b").write_bytes(b"b")
            catalog = catalog_assets(root, EMPTY_SELECTIONS)
            (root / "a").write_bytes(b"changed")
            (root / "b").unlink()
            (root / "new").write_bytes(b"new")
            result = verify_assets(root, catalog)
            self.assertFalse(result["ok"])
            self.assertEqual({item["code"] for item in result["issues"]}, {"ASSET_MISSING", "ASSET_HASH_MISMATCH", "ASSET_NOT_CATALOGUED"})

    def test_selected_verification_does_not_silently_ignore_unknown_path(self):
        with workspace_temporary_directory() as folder:
            with self.assertRaisesRegex(ValueError, "ASSET_NOT_CATALOGUED"):
                verify_assets(folder, {"assets": []}, ["missing.ttf"])

    def test_portable_asset_paths_reject_escape_and_drive_syntax(self):
        with workspace_temporary_directory() as folder:
            for path in ("../escape", "/absolute", "C:/file", "a\\b", "a//b", "a/./b"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    confined_path(folder, path)

    def test_synthetic_font_rebuilds_identically(self):
        with workspace_temporary_directory() as folder:
            root = Path(folder)
            make_font(root / "one.ttf")
            make_font(root / "two.ttf")
            self.assertEqual(file_hash(root / "one.ttf"), file_hash(root / "two.ttf"))

    def test_same_family_files_keep_distinct_identities(self):
        with workspace_temporary_directory() as folder:
            root = Path(folder)
            make_font(root / "one.ttf", 600)
            make_font(root / "two.ttf", 700)
            registry = font_registry(root, catalog_assets(root, EMPTY_SELECTIONS))
            self.assertEqual(len(registry["familyCollisions"]), 1)
            self.assertNotEqual(registry["fonts"][0]["fontId"], registry["fonts"][1]["fontId"])
            glyph = next(item for item in registry["fonts"][0]["coverage"] if item["scalar"] == 65)
            self.assertEqual((glyph["glyphId"], glyph["advance"]), (2, 600))
            self.assertEqual(registry["fonts"][0]["mappingStatus"], "unreviewed")

    def test_font_change_after_cataloguing_is_rejected(self):
        with workspace_temporary_directory() as folder:
            root = Path(folder)
            make_font(root / "one.ttf", 600)
            catalog = catalog_assets(root, EMPTY_SELECTIONS)
            make_font(root / "one.ttf", 700)
            with self.assertRaisesRegex(ValueError, "FONT_HASH_MISMATCH"):
                font_registry(root, catalog)


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validators = validators(ROOT)

    def test_full_check_runs_in_copy_without_inputs(self):
        with workspace_temporary_directory() as folder:
            root = Path(folder)
            for relative in ("data", "schemas", "tests", "docs", "tools", "vayrshemon"):
                shutil.copytree(ROOT / relative, root / relative, ignore=shutil.ignore_patterns('__pycache__'))
            for relative in ("requirements-m0.txt", "requirements-m1.txt", "requirements-m2.txt", "requirements-m3.txt"):
                shutil.copy2(ROOT / relative, root / relative)
            self.assertFalse((root / "Inputs").exists())
            result = check_repository(root)
            self.assertTrue(result["ok"], result["issues"])

    def test_invalid_dimensions_and_schema_versions_are_rejected(self):
        original = load_json(ROOT / "tests/fixtures/documents/spacing.json")
        for value in ("0", "-1", 123, "NaN", "001", "1e20"):
            document = copy.deepcopy(original)
            document["pages"][0]["widthMicroPoints"] = value
            with self.subTest(value=value):
                self.assertFalse(self.validators["document"].is_valid(document))
        original["schemaVersion"] = "99.0.0"
        self.assertFalse(self.validators["document"].is_valid(original))

    def test_dimension_integer_overflow_is_rejected_semantically(self):
        document = load_json(ROOT / "tests/fixtures/documents/spacing.json")
        document["pages"][0]["widthMicroPoints"] = str(2**63)
        self.assertIn("DIMENSION_OUT_OF_INT64_RANGE", validate_document_semantics(document))

    def test_document_reference_and_geometry_errors_are_detected(self):
        document = load_json(ROOT / "tests/fixtures/documents/unicode.json")
        document["pages"][0]["frames"][0]["storyId"] = "story.missing"
        document["pages"][0]["marginsMicroPoints"]["left"] = document["pages"][0]["widthMicroPoints"]
        document["stories"][0]["blocks"][0]["runs"][0]["styleId"] = "style.missing"
        errors = validate_document_semantics(document)
        self.assertIn("FRAME_STORY_REFERENCE_MISSING", errors)
        self.assertIn("RUN_STYLE_REFERENCE_MISSING", errors)
        self.assertIn("PAGE_MARGINS_LEAVE_NO_CONTENT", errors)

    def test_transaction_requires_revision_idempotency_and_declared_offsets(self):
        command = load_json(ROOT / "tests/fixtures/commands/transaction.json")
        for key in ("expectedRevision", "idempotencyKey", "requestId"):
            invalid = copy.deepcopy(command)
            del invalid[key]
            self.assertFalse(self.validators["command"].is_valid(invalid))
        command["operations"][0]["position"]["offsetUnit"] = "utf16"
        self.assertFalse(self.validators["command"].is_valid(command))

    def test_unresolved_mapping_cannot_claim_a_symbol(self):
        mapping = load_json(ROOT / "data/orthography/thimfora-79.json")
        unresolved = next(entry for entry in mapping["entries"] if entry["status"] == "unresolved")
        unresolved["symbolId"] = "invented.symbol"
        self.assertFalse(self.validators["mapping"].is_valid(mapping))

    def test_json_rejects_duplicate_keys_and_nonfinite_numbers(self):
        with workspace_temporary_directory() as folder:
            path = Path(folder) / "invalid.json"
            for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_json(path)


class DocxAndCliTests(unittest.TestCase):
    def test_docx_preserves_unicode_runs_fonts_and_unknown_nodes(self):
        with workspace_temporary_directory() as folder:
            path = Path(folder) / "synthetic.docx"
            xml = '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p>
            <w:r><w:rPr><w:rFonts w:ascii="Historic Unknown"/></w:rPr><w:t xml:space="preserve"> Jj Á Á 😀 </w:t><w:tab/><w:br/></w:r>
            <w:hyperlink><w:r><w:t>linked</w:t><w:drawing/></w:r></w:hyperlink>
            </w:p></w:body></w:document>'''
            with ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", xml.encode("utf-8"))
            before = file_hash(path)
            result = extract_docx(path)
            self.assertEqual(result["sourceSha256"], before)
            self.assertEqual(file_hash(path), before)
            self.assertEqual(result["sourceParts"]["word/document.xml"]["xml"], xml)
            self.assertEqual(result["directFontNames"], ["Historic Unknown"])
            runs = result["paragraphs"][0]["runs"]
            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[0]["tokens"][0]["text"], " Jj Á Á 😀 ")
            self.assertEqual([item["kind"] for item in runs[0]["tokens"]], ["t", "tab", "br"])
            self.assertEqual(runs[0]["semanticStatus"], "unresolved")
            self.assertEqual(result["warnings"][0]["code"], "DOCX_UNSUPPORTED_RUN_NODE")

    def test_cli_does_not_write_logs_or_outputs_into_archive(self):
        with workspace_temporary_directory() as folder:
            root = Path(folder)
            archive = root / "Inputs"
            archive.mkdir()
            for argument in ("--out", "--log"):
                destination = archive / "original.txt"
                destination.write_bytes(b"KEEP")
                command = [sys.executable, "-m", "tools.m0", "--root", str(root)]
                command += (["--log", str(destination), "capabilities"] if argument == "--log" else ["capabilities", "--out", str(destination)])
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(destination.read_bytes(), b"KEEP")
                self.assertIn("ORIGINAL_SOURCE_OUTPUT_REJECTED", result.stderr)

    def test_cli_logs_errors_with_traceback_without_polluting_json_output(self):
        result = subprocess.run([sys.executable, "-m", "tools.m0", "extract-docx", "missing-m0-fixture.docx"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        events = [json.loads(line) for line in result.stderr.splitlines()]
        error = next(event for event in events if event["code"] == "COMMAND_FAILED")
        self.assertTrue(error["traceId"])
        self.assertIn("FileNotFoundError", error["traceback"])

    def test_cli_legacy_bytes_roundtrip_and_strict_codec(self):
        mapping = load_json(ROOT / "data/orthography/thimfora-79.json")
        with workspace_temporary_directory() as folder:
            path = Path(folder) / "legacy.txt"
            original = b"Jj\xc2\xc3\r\n\xbe"
            path.write_bytes(original)
            command = [sys.executable, "-m", "tools.m0", "decode-legacy", str(path), "--encoding", "cp1252",
                       "--font-sha256", mapping["fontSha256s"][0]]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            decoded = json.loads(result.stdout)
            self.assertEqual(restore_legacy(decoded).encode("cp1252"), original)
            self.assertIn("COMMAND_COMPLETED", result.stderr)
            path.write_bytes(b"\x81")
            invalid = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertEqual(invalid.stdout, "")
            self.assertIn("UnicodeDecodeError", invalid.stderr)


if __name__ == "__main__":
    unittest.main()
