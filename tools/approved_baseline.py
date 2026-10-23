"""Verify the explicitly approved page; never regenerate its expected hashes."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tools.m0.common import load_json, write_json, file_hash

MANIFEST = 'data/formatting/approved-workbench-20261023.json'


def protected_state(state):
    value = {key:deepcopy(state[key]) for key in ('pages', 'paint', 'recipe', 'features', 'styles', 'typesetting')}
    value['fonts'] = sorted((dict(fontId=f['fontId'], sha256=f['sha256']) for f in state['fontSources']), key=lambda f:f['fontId'])
    return value


def content_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def rgba_hash(image):
    from PySide6.QtGui import QImage
    image = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return hashlib.sha256(bytes(image.constBits())).hexdigest()


def check_state(state, manifest):
    if content_hash(protected_state(state)) != manifest['protectedStateSha256']:
        raise ValueError('APPROVED_PAGE_CHANGED: compare and review; never automatically replace the baseline')


def verify(root, out):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QImage
    from vayrshemon.reliability_session import ReliabilitySession
    from vayrshemon import pages
    root, out = Path(root), Path(out)
    manifest = load_json(root/MANIFEST)
    source, proof = root/manifest['source']['path'], root/manifest['proof']['path']
    if file_hash(source) != manifest['source']['sha256'] or file_hash(proof) != manifest['proof']['sha256']:
        raise ValueError('APPROVED_REFERENCE_CHANGED: retain and restore the approved source/proof')
    app = QApplication.instance() or QApplication([])
    session = ReliabilitySession(root, source_fonts=False, recovery=False)
    try:
        session.open(source)
        check_state(session.capture(), manifest)
        expected = QImage(str(proof))
        if expected.isNull() or rgba_hash(expected) != manifest['proof']['rgbaSha256']:
            raise ValueError('APPROVED_REFERENCE_PIXELS_CHANGED')
        out.mkdir(parents=True, exist_ok=True)
        actual, report = pages.render(session, path=out/'approved-page.png', mode='color', dpi=manifest['proof']['dpi'])
        layout = pages.inspect(session, max_glyphs=20000)
        result = dict(baselineId=manifest['id'], application=session.application_version,
                      sourceVerified=True, protectedStateVerified=True,
                      rgbaIdentical=actual.size()==expected.size() and rgba_hash(actual)==rgba_hash(expected),
                      geometryIdentical=layout['geometryHash']==manifest['geometryHash'],
                      render=report, geometryHash=layout['geometryHash'],
                      collisions=layout['collisionReport']['afterCount'],
                      overflow=sum(f['overflow'] for f in layout['frames']))
        write_json(out/'verification.json', result)
        if not result['rgbaIdentical'] or not result['geometryIdentical']:
            raise ValueError('APPROVED_RENDERING_CHANGED: inspect '+str(out/'verification.json'))
        return result
    finally:
        session.finish()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(Path(__file__).resolve().parents[1], args.out), indent=2))
