"""Join an ordered volume-index.json into one native book, without reflowing text.

The source files are never changed. Differing global formatting, duplicate IDs,
conflicting language records and an existing destination are rejected.
"""
import argparse
from copy import deepcopy
import hashlib
from pathlib import Path
from time import perf_counter
from tools.m0.common import load_json, write_json
from vayrshemon.authoring import identity


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assemble(index_path, title):
    index_path = Path(index_path).resolve()
    entries = load_json(index_path)
    if not isinstance(entries, list) or not entries: raise ValueError('EMPTY_VOLUME_INDEX')
    state = None
    page_ids, frame_ids, revisions, language_objects = set(), set(), {}, {}
    sources = []
    document_id = identity('document')
    for entry in entries:
        path = (index_path.parent / entry['file']).resolve(strict=True)
        if not path.is_relative_to(index_path.parent): raise ValueError('VOLUME_PATH_OUTSIDE_INDEX')
        file_sha = sha(path)
        payload = load_json(path)
        if payload.get('format') != 'vayrshemon.document' or payload.get('formatVersion') != '0.6.0':
            raise ValueError('NATIVE_VAY_VOLUME_REQUIRED')
        source = payload['state']
        if state is None:
            state = deepcopy(source)
            state.update(documentId=document_id, title=title, revision=0, pages=[])
            state['typesetting']['frames'] = {}
            state['typesetting']['flows'] = []
            state['language']['links'] = []
        for field in ('recipe', 'paint', 'styles', 'features', 'fontSources'):
            if source[field] != state[field]: raise ValueError('VOLUME_FORMAT_DIFFERS: ' + field)
        if source['typesetting']['profiles'] != state['typesetting']['profiles']:
            raise ValueError('VOLUME_LINE_BREAK_PROFILES_DIFFER')
        first = len(state['pages']) + 1
        for page in source['pages']:
            if page['pageId'] in page_ids: raise ValueError('DUPLICATE_PAGE_ID')
            page_ids.add(page['pageId'])
            page = deepcopy(page)
            for frame in page['frames']:
                if frame['frameId'] in frame_ids: raise ValueError('DUPLICATE_FRAME_ID')
                frame_ids.add(frame['frameId'])
                frame['content']['document']['documentId'] = document_id
            state['pages'].append(page)
        state['typesetting']['frames'].update(deepcopy(source['typesetting']['frames']))
        state['typesetting']['flows'].extend(deepcopy(source['typesetting']['flows']))
        for key, value in source['language']['objects'].items():
            if key in language_objects and language_objects[key] != value: raise ValueError('LANGUAGE_OBJECT_CONFLICT')
            language_objects[key] = value
        for revision in source['language']['revisions']:
            key = revision['id']
            if key in revisions and revisions[key] != revision: raise ValueError('LANGUAGE_REVISION_CONFLICT')
            revisions[key] = revision
        for link in source['language']['links']:
            if link not in state['language']['links']: state['language']['links'].append(deepcopy(link))
        state['language']['activeRevisionId'] = source['language']['activeRevisionId']
        if sha(path) != file_sha: raise ValueError('SOURCE_CHANGED_DURING_COMBINATION')
        sources.append(dict(path=str(path), sha256=file_sha, firstPage=first, lastPage=len(state['pages'])))
    state['language']['objects'] = deepcopy(language_objects)
    state['language']['revisions'] = deepcopy(list(revisions.values()))
    state['activeFrameId'] = state['pages'][0]['frames'][0]['frameId']
    return state, sources


def verify_pages(state, sources):
    """Every source byte represented in page data must match, except the book ID."""
    count = 0
    for source in sources:
        path = Path(source['path'])
        if sha(path) != source['sha256']: raise ValueError('SOURCE_CHANGED_AFTER_COMBINATION')
        original = load_json(path)['state']
        for expected, actual in zip(original['pages'], state['pages'][source['firstPage']-1:source['lastPage']], strict=True):
            expected = deepcopy(expected)
            for frame in expected['frames']:
                frame['content']['document']['documentId'] = state['documentId']
            if expected != actual: raise ValueError('PAGE_CHANGED: ' + expected['pageId'])
            count += 1
        for fid, config in original['typesetting']['frames'].items():
            if config != state['typesetting']['frames'][fid]: raise ValueError('TYPESETTING_CHANGED: ' + fid)
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('index', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--title', required=True)
    args = parser.parse_args()
    if args.output.exists(): raise ValueError('COMBINED_DESTINATION_EXISTS')
    from PySide6.QtWidgets import QApplication
    from vayrshemon.file_api import FileSession
    app = QApplication.instance() or QApplication([])
    started = perf_counter()
    state, sources = assemble(args.index, args.title)
    print(f'Assembled {len(state["pages"])} pages from {len(sources)} files.', flush=True)
    root = Path(__file__).resolve().parents[1]
    book = FileSession(root, source_fonts=False, recovery=False)
    try:
        book._restore(book.resolve_fonts(state))
        book._state = book.capture()
        verify_pages(book._state, sources)
        print('Every page and typesetting record matches. Saving native book and font-complete backup.', flush=True)
        result = book.save(args.output, preview_mode='two')
        saved = load_json(args.output)
        count = verify_pages(saved['state'], sources)
        report = dict(path=str(args.output.resolve()), sha256=sha(args.output), pages=count, spreads=count//2,
                      sourceFiles=sources, exactPageComparison=True, elapsedSeconds=perf_counter()-started, save=result)
        write_json(args.output.with_suffix('.verification.json'), report)
        print(f'Saved and verified {count} pages: {args.output} ({perf_counter()-started:.1f}s)', flush=True)
    finally: book.finish()


if __name__ == '__main__': main()
