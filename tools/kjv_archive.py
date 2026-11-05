"""Index the supplied KJV and verify deliberately frozen historical editions.

This module does not translate English. All 66 biblical sections belong to one
Bible deliverable. Authored, source-aligned verse ledgers establish coverage;
individual sections and source indexing are not the completed Bible.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.10-kjv.1'
PACKAGE = ROOT / 'data/language/archaic-kjv-1'
PROJECT = ROOT / 'Saves' / ('KJV Archive v' + VERSION)
BOOKS = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
         'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings',
         '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah',
         'Esther', 'Job', 'Psalms', 'Proverbs', 'Ecclesiastes',
         'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel',
         'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah',
         'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
         'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans',
         '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
         'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
         '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James',
         '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation']
VERSE = re.compile(r'(?<!\w)(\d+):(\d+)\s+')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    from tools.m0.common import load_json
    return load_json(path)


def write_new(path, value):
    """An archive build may not overwrite an earlier edition, even identically."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def translation_coverage(index, ledgers):
    """Count source-bound authored verses; never equate a source index with translation.

    Layout continuations must first be rejoined to their verse ledger. A verse
    appears once here, irrespective of how many paragraphs/pages it occupies.
    This is a coverage check, not independent certification of literary quality.
    """
    expected = {v['id']: v for book in index['books'] for v in book['verses']}
    if len(expected) != index['verseCount']:
        raise ValueError('BIBLE_SOURCE_COUNT')
    seen = set()
    for ledger in ledgers:
        if ledger['sourceSha256'] != index['sourceSha256']:
            raise ValueError('BIBLE_SOURCE_HASH_MISMATCH')
        for unit in ledger['units']:
            identity = unit['id']
            if identity not in expected:
                raise ValueError('BIBLE_UNKNOWN_VERSE: ' + identity)
            if identity in seen:
                raise ValueError('BIBLE_DUPLICATE_VERSE: ' + identity)
            if unit['source'] != expected[identity]['source']:
                raise ValueError('BIBLE_SOURCE_VERSE_CHANGED: ' + identity)
            if any(not isinstance(unit.get(k), str) or not unit[k].strip()
                   for k in ('analysis', 'text', 'gloss', 'backReading', 'note')):
                raise ValueError('BIBLE_UNAUTHORED_VERSE: ' + identity)
            seen.add(identity)
    sections = []
    for book in index['books']:
        covered = sum(v['id'] in seen for v in book['verses'])
        sections.append(dict(number=book['number'], name=book['name'],
                             authoredVerses=covered, sourceVerses=book['verseCount'],
                             complete=covered == book['verseCount']))
    return dict(scope='One complete Bible; biblical books are major sections',
                sourceVerses=len(expected), authoredVerses=len(seen),
                remainingVerses=len(expected)-len(seen), complete=len(seen)==len(expected),
                missingVerseIds=[identity for identity in expected if identity not in seen],
                sections=sections)


def require_complete_bible(index, ledgers):
    coverage = translation_coverage(index, ledgers)
    if not coverage['complete']:
        raise ValueError(f'INCOMPLETE_BIBLE: {coverage["authoredVerses"]}/{coverage["sourceVerses"]} verses')
    return coverage


def parse_source(path, names=BOOKS):
    raw = Path(path).read_bytes()
    text = raw.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    starts = list(re.finditer(r'(?m)^1:1\s', text))
    if len(starts) != len(names):
        raise ValueError(f'BOOK_COUNT: {len(starts)} != {len(names)}')
    books = []
    previous_end = 0
    for i, start in enumerate(starts):
        boundary = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        segment_markers = list(VERSE.finditer(text, start.start(), boundary))
        last_marker = segment_markers[-1].end()
        separator = re.search(r'\n{3,}', text[last_marker:boundary])
        end = last_marker + separator.start() if separator else boundary
        # Psalms has internal large gaps. Only cut after the last verse marker.
        if VERSE.search(text[end:boundary]):
            raise ValueError('UNPARSED_VERSE_AFTER_BOOK: ' + names[i])
        markers = list(VERSE.finditer(text, start.start(), end))
        verses = []
        previous_chapter, previous_verse = 1, 0
        for j, marker in enumerate(markers):
            chapter, verse = map(int, marker.groups())
            if not ((chapter == previous_chapter and verse == previous_verse + 1)
                    or (chapter == previous_chapter + 1 and verse == 1)):
                raise ValueError(f'VERSE_SEQUENCE: {names[i]} {chapter}:{verse}')
            stop = markers[j + 1].start() if j + 1 < len(markers) else end
            original = text[marker.end():stop].rstrip()
            if not original.strip():
                raise ValueError('EMPTY_VERSE')
            verses.append(dict(id=f'{i+1:02d}.{chapter:03d}.{verse:03d}',
                               reference=f'{names[i]} {chapter}:{verse}',
                               chapter=chapter, verse=verse,
                               start=marker.end(), end=marker.end()+len(original),
                               original=original, source=' '.join(original.split())))
            previous_chapter, previous_verse = chapter, verse
        books.append(dict(number=i+1, name=names[i], chapters=previous_chapter,
                          verseCount=len(verses), verses=verses,
                          frontmatter=text[previous_end:start.start()].strip(),
                          sourceStart=start.start(), sourceEnd=end))
        previous_end = end
    if sum(b['verseCount'] for b in books) != len(VERSE.findall(text)):
        raise ValueError('SOURCE_MARKER_COVERAGE')
    return dict(source=str(Path(path).resolve()), sourceSha256=hashlib.sha256(raw).hexdigest(),
                offsetConvention='Unicode scalar offsets in UTF-8-sig decoded source with LF newlines',
                normalizedSourceSha256=hashlib.sha256(text.encode('utf8')).hexdigest(),
                books=books, verseCount=sum(b['verseCount'] for b in books))


def safe_member(root, relative):
    root = Path(root).resolve()
    candidate = (root / relative).resolve()
    if candidate == root or not candidate.is_relative_to(root):
        raise ValueError('ARCHIVE_PATH_OUTSIDE_ROOT')
    return candidate


def verify_seal(folder):
    folder = Path(folder)
    seal = read(folder / 'FROZEN.json')
    if seal['policy'] != 'never-modernize':
        raise ValueError('MISSING_FREEZE_POLICY')
    for relative, expected in seal['files'].items():
        if digest(safe_member(folder, relative)) != expected:
            raise ValueError('FROZEN_FILE_CHANGED: ' + relative)
    return seal


def assert_can_consolidate(folder):
    """A historical edition stays historical, regardless of newer language heads."""
    if (Path(folder) / 'FROZEN.json').exists():
        verify_seal(folder)
        raise ValueError('NEVER_MODERNIZE: this KJV edition is excluded from consolidation')


def seal(folder, metadata):
    folder = Path(folder)
    files = {p.relative_to(folder).as_posix(): digest(p)
             for p in sorted(folder.rglob('*')) if p.is_file() and p.name != 'FROZEN.json'}
    write_new(folder / 'FROZEN.json', dict(metadata, policy='never-modernize', files=files))
    return verify_seal(folder)


def verify_register(version=VERSION):
    registry = read(ROOT / 'data/language/historical.json')
    matches = [r for r in registry['registers'] if r['version'] == version]
    if len(matches) != 1:
        raise ValueError('ARCHAIC_REGISTER_NOT_UNIQUE: ' + version)
    registered = matches[0]
    package = safe_member(ROOT, registered['package'])
    if digest(package / 'manifest.json') != registered['manifestSha256']:
        raise ValueError('ARCHAIC_REGISTER_MANIFEST_CHANGED')
    manifest = read(package / 'manifest.json')
    if manifest['version'] != version or manifest['policy'] != 'never-modernize':
        raise ValueError('ARCHAIC_REGISTER_IDENTITY')
    for name, expected in manifest['files'].items():
        if digest(safe_member(package, name)) != expected:
            raise ValueError('ARCHAIC_REGISTER_FILE_CHANGED: ' + name)
    if digest(safe_member(ROOT, manifest['compilerPath'])) != manifest['compilerSha256']:
        raise ValueError('ARCHAIC_REGISTER_COMPILER_CHANGED')
    # Use its pinned baseline, not a future current.json after consolidation.
    baseline = safe_member(ROOT, manifest['basePackage'])
    if digest(baseline / 'manifest.json') != manifest['baseManifestSha256']:
        raise ValueError('ARCHAIC_REGISTER_PARENT_CHANGED')
    return manifest


def load_register(version=VERSION):
    """Load the sealed compiler, independent of later modern-language changes."""
    manifest = verify_register(version)
    registered = next(r for r in read(ROOT / 'data/language/historical.json')['registers']
                      if r['version'] == version)
    package = safe_member(ROOT, registered['package'])
    spec = importlib.util.spec_from_file_location('vayrshemon_frozen_kjv_compiler',
                                                 ROOT / manifest['compilerPath'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.EditorialLanguage(package), manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index-source', type=Path)
    parser.add_argument('--verify-register', action='store_true')
    parser.add_argument('--register-version', default=VERSION,
                        help='Explicit historical version; the default stays the original frozen register')
    parser.add_argument('--verify-edition', type=Path)
    args = parser.parse_args()
    if args.index_source:
        source = parse_source(args.index_source)
        write_new(PROJECT / 'source-index.json', source)
        print(f'Indexed {len(source["books"])} books / {source["verseCount"]} verses; no translation implied.')
    if args.verify_register:
        manifest = verify_register(args.register_version)
        print('Verified historical register', manifest['version'], manifest['forgeHead'])
    if args.verify_edition:
        print('Verified frozen edition', verify_seal(args.verify_edition)['book'])
    if not any((args.index_source, args.verify_register, args.verify_edition)):
        parser.print_help()


if __name__ == '__main__':
    main()
