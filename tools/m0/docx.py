"""Preservation-first DOCX evidence extraction, not a document converter.

Retains the XML parts used, direct run properties, source code points, and
unresolved style references. It does not infer language from the font name or
pretend to implement Word's complete style, theme, field, or revision model.
"""

import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .common import file_hash


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{" + NS["w"] + "}"
PARTS = ("word/document.xml", "word/styles.xml", "word/fontTable.xml", "word/theme/theme1.xml")
MAX_PART_BYTES = 16 * 1024 * 1024


def xml_properties(element):
    return ET.tostring(element, encoding="unicode") if element is not None else None


def extract_docx(path):
    path = Path(path)
    source_hash = file_hash(path)
    parts, warnings = {}, []
    with ZipFile(path) as archive:
        for name in PARTS:
            if name not in archive.namelist():
                continue
            info = archive.getinfo(name)
            if info.file_size > MAX_PART_BYTES:
                raise ValueError("DOCX_PART_TOO_LARGE: " + name)
            raw = archive.read(name)
            # ElementTree does not need document type declarations for OOXML.
            if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
                raise ValueError("DOCX_XML_DECLARATION_REJECTED")
            parts[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "xml": raw.decode("utf-8-sig")}
    if "word/document.xml" not in parts:
        raise ValueError("DOCX_DOCUMENT_PART_MISSING")
    root = ET.fromstring(parts["word/document.xml"]["xml"])
    paragraphs = []
    font_names = set()
    for p_index, paragraph in enumerate(root.findall(".//w:p", NS)):
        runs = []
        # Descendant runs include hyperlinks and revisions. Their complete
        # enclosing structure remains available in the retained source XML.
        for r_index, run in enumerate(paragraph.findall(".//w:r", NS)):
            tokens = []
            for child in run:
                tag = child.tag.removeprefix(W)
                if tag in ("t", "delText", "instrText"):
                    tokens.append({"kind": tag, "text": child.text or ""})
                elif tag in ("tab", "br", "cr", "noBreakHyphen", "softHyphen", "sym"):
                    tokens.append({"kind": tag, "attributes": {key.removeprefix(W): val for key, val in child.attrib.items()}})
                elif tag != "rPr":
                    tokens.append({"kind": "unsupported", "tag": tag, "xml": xml_properties(child)})
                    warnings.append({"code": "DOCX_UNSUPPORTED_RUN_NODE", "paragraph": p_index, "run": r_index, "tag": tag})
            fonts = run.find("w:rPr/w:rFonts", NS)
            direct_fonts = {key.removeprefix(W): val for key, val in fonts.attrib.items()} if fonts is not None else {}
            font_names.update(value for key, value in direct_fonts.items() if not key.endswith("Theme"))
            runs.append({"runIndex": r_index, "tokens": tokens, "directFonts": direct_fonts,
                         "propertiesXml": xml_properties(run.find("w:rPr", NS)),
                         "semanticStatus": "unresolved", "styleResolution": "not-performed"})
        paragraphs.append({"paragraphIndex": p_index, "propertiesXml": xml_properties(paragraph.find("w:pPr", NS)), "runs": runs})
    if file_hash(path) != source_hash:
        raise ValueError("DOCX_CHANGED_DURING_READ")
    return {"schemaVersion": "0.1.0", "sourceSha256": source_hash,
            "kind": "docx-evidence", "sourceParts": parts, "directFontNames": sorted(font_names),
            "paragraphs": paragraphs, "warnings": warnings,
            "limitations": ["Not a full DOCX importer; source file remains authoritative.",
                            "Style/theme inheritance, revision visibility and fields are preserved but not evaluated.",
                            "Language and mapping profiles must be assigned from evidence, not font names alone."]}
