"""Build an M6.1 demo copy and verify it against the approved larger page."""
import argparse
import json
from pathlib import Path
import time
import uuid
from PySide6.QtWidgets import QApplication
from tools.m0.common import load_json, write_json
from tools.approved_baseline import MANIFEST, check_state, rgba_hash
from vayrshemon.reliability_session import ReliabilitySession
from vayrshemon.reliability_api import ReliabilityAPI
from vayrshemon import pages


def build(root, source, out):
    root, source, out = Path(root), Path(source), Path(out)
    if out.exists(): raise ValueError('DEMO_DIRECTORY_ALREADY_EXISTS')
    original = load_json(source)
    manifest = load_json(root/MANIFEST)
    check_state(original['state'], manifest)
    out.mkdir(parents=True)
    write_json(out/'source-snapshot.vay.json', original)
    app = QApplication.instance() or QApplication([])
    session = ReliabilitySession(root, source_fonts=False, recovery=False)
    api = ReliabilityAPI(session)
    transcript = []
    def call(method, **params):
        response = api.call(method, params, expected_revision=session.revision,
                            document_id=session.state['documentId'], origin='mcp', idempotency_key=uuid.uuid4().hex)
        transcript.append(dict(method=method, params=params, response=response))
        if not response['ok']: raise ValueError(response)
        return response['result']
    try:
        session.open(source)
        call('document.title', title='Vayrshemon-English — M6.1 approved page')
        saved = call('document.save-as', path=str(out/'Vayrshemon-English-M6.1.vay.json'))
        check_state(session.capture(), manifest)
        if session.state['language'] != original['state']['language']:
            raise ValueError('DEMO_LANGUAGE_CHANGED')
        image, rendered = pages.render(session, path=out/'approved-page.png', mode='color', dpi=144)
        if rgba_hash(image) != manifest['proof']['rgbaSha256']:
            raise ValueError('DEMO_PIXELS_CHANGED')
        jobs = []
        for kind in ('svg', 'pdf'):
            job = call('jobs.export', path=str(out/('approved-page.'+kind)), format=kind,
                       mode='color', dpi=144, raster_policy='raster')
            deadline = time.monotonic()+120
            while time.monotonic()<deadline:
                app.processEvents()
                result = session.jobs.status(job['jobId'])
                if result['status']!='running': break
                time.sleep(.05)
            if result['status']!='completed': raise ValueError(result)
            jobs.append(result)
        report = pages.inspect(session, max_glyphs=20000)
        if report['geometryHash'] != manifest['geometryHash']:
            raise ValueError('DEMO_GEOMETRY_CHANGED')
        write_json(out/'layout.json', report)
        verification = dict(application=session.application_version, api=api.version,
                            baselineId=manifest['id'], protectedStateVerified=True,
                            rgbaIdentical=True, geometryIdentical=True, languagePreserved=True,
                            saved=saved, render=rendered, jobs=jobs)
        write_json(out/'verification.json', verification)
        return dict(document=saved['path'], rgbaIdentical=True, geometryIdentical=True)
    finally:
        write_json(out/'api-transcript.json', transcript)
        session.finish()


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(Path(__file__).resolve().parents[1], args.source, args.out), indent=2))
