"""Hash-bound local specimen definitions and public contract fixtures."""

from .common import asset_ref


def build_fixtures(catalog, registry):
    master = "font files/Thimfora_79.ttf"
    infill = "font files/Thimfora_80_Infill.ttf"
    interior = "font files/Thimfora_81_Fragments.ttf"
    fonts = {font["asset"]["path"]: font["fontId"] for font in registry["fonts"]}

    def local(fixture_id, kind, assets, requirements, assertions, notes):
        return {"fixtureId": fixture_id, "kind": kind, "availability": "local-archive",
                "assets": [asset_ref(catalog, path) for path in assets],
                "fontIds": [fonts[path] for path in assets if path in fonts],
                "requirements": requirements, "assertions": assertions, "documentPath": None, "notes": notes}

    def public(fixture_id, kind, document, requirements, assertions):
        return {"fixtureId": fixture_id, "kind": kind, "availability": "public-synthetic",
                "assets": [], "fontIds": [], "requirements": requirements, "assertions": assertions,
                "documentPath": document, "notes": "Project-authored structural fixture; no rendering baseline has been established."}

    return {"schemaVersion": "0.1.0", "fixtures": [
        local("fixture.alphabet", "alphabet", ["Origins_2_Thimfora_2.jpg", "Thimfora 79 - Full Set - 2.docx", master],
              ["TEXT-01", "FONT-01"], ["47 distinct letters, each with maxima and minima", "Exact source-scalar round trip"],
              "Chart is the code assignment authority for this profile; older revisions require their own mapping."),
        local("fixture.digits", "digits", ["Unta - Base 12.jpg", master], ["TEXT-01", "LANG-01"],
              ["Exactly 12 digits with values 0 through 11", "Values 10 and 11 use legacy slots 192 and 193"],
              "Numeric interpretation follows the selected chart; historic name variants remain independent."),
        local("fixture.mixed-legacy", "mixed-language", ["Versions Best/Polished Examples.docx", "font files/Test/test seven.ttf",
              "font files/Transliteration/transliteration 5.ttf"], ["TEXT-01", "DATA-01"],
              ["Preserve run boundaries, direct font references, original XML and code points", "Do not apply the Thimfora 79 profile to these fonts"],
              "M0 evidence extraction only. Full style/theme resolution and semantic conversion are deferred."),
        local("fixture.kerning", "kerning", ["Versions Rough/Kerning Pairs.txt", "Versions Rough/Kerning List.txt", master],
              ["LAYOUT-01", "FONT-01"], ["Decode as explicit Windows-1252 with strict errors", "M1: measure shaped positions without adding a second kerning pass"],
              "M0 verifies source bytes/mapping preservation; it does not establish shaping-position goldens."),
        local("fixture.color", "color", [master, infill, interior, "font files/How to Make High Quality Color Text with Photoshop.txt", "Origins_A Blue Jewel.jpg"],
              ["FONT-02", "LAYOUT-02", "EXPORT-01"], ["Source positioning tables and advances agree", "M1: verify shared glyph origins visually", "M4: check effect and export fidelity"],
              "Interior side bearings intentionally differ. The reference is not yet a pixel golden for an implemented renderer."),
        local("fixture.family-collision", "font-identity", ["Versions Rough/Thimfora Barim Aug 10 2011.ttf", "Versions Rough/Thimfora Venik July 16 2011.ttf"],
              ["FONT-01", "VERSION-01"], ["Same internal family remains two distinct file identities"], "Never resolve these files by family name alone."),
        public("fixture.unicode-public", "mixed-language", "tests/fixtures/documents/unicode.json", ["TEXT-01", "TEXT-02", "DATA-01"],
               ["Preserve combining marks, supplementary scalars, RTL text, and whitespace", "No implicit normalization"]),
        public("fixture.symbols-public", "alphabet", "tests/fixtures/documents/symbols.json", ["TEXT-01", "VERSION-01"],
               ["All chart letter forms and digits have stable IDs", "Unknown legacy text remains intact"]),
        public("fixture.spacing-public", "line-spacing", "tests/fixtures/documents/spacing.json", ["PAGE-01", "LAYOUT-01", "LAYOUT-02"],
               ["Fractional custom dimensions remain exact", "M1/M3: inspect dense lines, overhangs, and effect clearance"]),
    ]}
