# Project working standards

Use [the approved parallel translation standard](docs/FORMATTING.md) for bilingual demos, formatting examples, and regression work unless the user asks for a different layout. It is a portrait page with exactly two full-height, independent text columns: Vayrshemon on the left and its English translation on the right. Do not add a title, column headings, or a footer by default.

Use attested source/translation pairs and the original hash-identified script fonts. Synthetic test strings are structural test data, never invented Vayrshemon. Keep original Inputs, extracted text, proofs, and local documents ignored.

For changes affecting authoring, layout, fonts, persistence, or export, include `test_parallel_translation.py` in validation. It is included in the normal unittest discovery run used by setup.bat. Read the standard's limitations before claiming automatic translation alignment or a clean collision report.
