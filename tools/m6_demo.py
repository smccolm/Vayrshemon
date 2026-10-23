"""Copy the current standard page into M6 without saving or closing the source."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import time
import uuid
from PySide6.QtWidgets import QApplication
from tools.m0.common import write_json,load_json
from vayrshemon.api import remote_call
from vayrshemon.reliability_session import ReliabilitySession
from vayrshemon.reliability_api import ReliabilityAPI
from vayrshemon import pages


def build(root,out,source=None,descriptor=None):
    root=Path(root);out=Path(out).resolve()
    if out.exists(): raise ValueError('DEMO_DIRECTORY_ALREADY_EXISTS')
    out.mkdir(parents=True)
    app=QApplication.instance() or QApplication([])
    if descriptor:
        status=remote_call(root,'session.status',descriptor=descriptor)
        current=remote_call(root,'document.read',descriptor=descriptor)
        if not status['ok'] or not current['ok']: raise ValueError('LIVE_SOURCE_READ_FAILED')
        snapshot=dict(format='vayrshemon.document',formatVersion='0.5.0',state=current['result']['document'],history=[],engine=status['result']['engine'])
        write_json(out/'source-session-status.json',status)
    else: snapshot=load_json(source)
    write_json(out/'source-snapshot.vay.json',snapshot)
    if len(snapshot['state']['pages'])!=1 or len(snapshot['state']['pages'][0]['frames'])!=2: raise ValueError('STANDARD_TWO_COLUMN_SOURCE_REQUIRED')
    s=ReliabilitySession(root,source_fonts=False,recovery=False);api=ReliabilityAPI(s);transcript=[]
    def call(method,**params):
        result=api.call(method,params,expected_revision=s.revision,document_id=s.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp');transcript.append(dict(method=method,response=result))
        if not result['ok']: raise ValueError(result)
        return result['result']
    try:
        s.open(out/'source-snapshot.vay.json');before=s.capture()
        call('document.title',title='Vayrshemon-English-M6')
        saved=call('document.save-as',path=str(out/'Vayrshemon-English-M6.vay.json'))
        if s.capture()['pages']!=before['pages'] or s.state['paint']!=before['paint'] or s.state['language']!=before['language']: raise ValueError('DEMO_CHANGED_SOURCE_CONTENT')
        jobs=[]
        for kind in ('png','svg','pdf'):
            job=call('jobs.export',path=str(out/('standard.'+kind)),format=kind,mode='color',dpi=144,raster_policy='raster')
            deadline=time.monotonic()+120
            while time.monotonic()<deadline:
                app.processEvents();status=s.jobs.status(job['jobId'])
                if status['status']!='running': break
                time.sleep(.05)
            if status['status']!='completed': raise ValueError(status)
            jobs.append(status)
        report=pages.inspect(s,max_glyphs=20000);write_json(out/'layout.json',report)
        verification=dict(application=s.application_version,api=api.version,sourceRevision=snapshot['state']['revision'],
            sourceSessionUntouched=True,pagesPreserved=True,paintPreserved=True,languagePreserved=True,saved=saved,
            glyphs=len(report['glyphs']),geometryHash=report['geometryHash'],collisions=report['collisionReport']['afterCount'],
            overflow=sum(f['overflow'] for f in report['frames']),jobs=jobs,performance=call('performance.inspect'))
        write_json(out/'verification.json',verification);write_json(out/'api-transcript.json',transcript)
        return dict(document=saved['path'],backup=saved['backup'],sourceRevision=verification['sourceRevision'])
    finally:s.finish()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--source',type=Path);g.add_argument('--descriptor',type=Path);a=p.parse_args()
    print(json.dumps(build(Path(__file__).resolve().parents[1],a.out,a.source,a.descriptor),indent=2))
