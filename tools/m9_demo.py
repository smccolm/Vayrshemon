"""Demonstrate M9 using the retained M8 literary proposal and approved page.

All source text, language history, proofs and captures remain in ignored .local.
The two branch reviews change documentation and test coverage, not printed text.
"""
from copy import deepcopy
from pathlib import Path
import argparse
import json
import shutil
import time
import uuid
from unittest.mock import patch
from PySide6.QtWidgets import QApplication,QPushButton
from PySide6.QtGui import QImage
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from vayrshemon.integration_api import IntegrationSession,IntegrationAPI
from vayrshemon.integration_window import IntegrationWindow
from vayrshemon.api import LocalServer
from vayrshemon.forge import digest
from tools.m0.common import load_json,write_json,file_hash
from tools.approved_baseline import rgba_hash


def build(root,out):
    root=Path(root).resolve();out=Path(out).resolve()
    out.mkdir(parents=True,exist_ok=False)
    source=root/'.local/demos/m8-forge-v0.9.0-final';prior=load_json(source/'demo.json')
    source_hash=file_hash(source/'Vayrshemon.vayforge')
    s=IntegrationSession(root,source_fonts=False,recovery=False);s.open(source/'Working-Tempest-0.2.3.vay.json',advance_revision=False)
    api=IntegrationAPI(s);transcript=[]
    def call(method,**params):
        if 'expected_generation' in api.methods[method][2]['properties']:
            status=s.forge.status();params.update(project_id=status['projectId'],expected_generation=status['generation'])
        reply=api.call(method,params,expected_revision=s.revision,document_id=s.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp')
        transcript.append(dict(method=method,params=params,reply=reply));write_json(out/'api-transcript.json',transcript)
        if not reply['ok']: raise RuntimeError(reply)
        return reply['result']
    call('forge.restore',path=str(source/'forge-history-final.json'),destination=str(out/'Vayrshemon.vayforge'))
    original=s.capture()
    call('forge.branch',name='integration-foundation',version=prior['finalVersion'])
    snapshot=call('forge.read')['snapshot']
    snapshot['wiki'].append(dict(id='m9-release-policy',title='Literary release policy',body='Retain the three paired Shakespeare paragraphs. Record interpretive losses and unresolved meaning review.',ruleIds=[]))
    call('forge.draft.replace',snapshot=snapshot);base=call('forge.commit',label='0.2.4 · Release review foundation')['head']
    call('forge.branch',name='lexical-review',version=base)
    snapshot=call('forge.read')['snapshot']
    next(w for w in snapshot['wiki'] if w['id']=='m9-release-policy')['body']='Release as an experimental literary adaptation. Preserve both branch reviews, the ef’ nominalizer, and the original Shakespeare translation notes. Meaning remains an author review task.'
    next(r for r in snapshot['language']['lexicon'] if r['id']=='m8.sleep')['notes']+='\nM9 lexical review: retain the verbal root; noun sleep in the bound page requires the documented ef’ event nominalizer. No pronunciation or attestation claim is added.'
    call('forge.draft.replace',snapshot=snapshot);theirs=call('forge.commit',label='Lexical review · event nominalization and release wording')['head']
    call('forge.branch',name='release-0.3',version=base)
    snapshot=call('forge.read')['snapshot']
    next(w for w in snapshot['wiki'] if w['id']=='m9-release-policy').update(title='Experimental literary release: review and evidence',body='Retain all three paired paragraphs. Require frozen suite results and the approved Workbench proof before making a release.')
    for key in ('sleep','breathe'):
        case=deepcopy(next(c for c in snapshot['laboratory']['cases'] if c['id']==f'events.m8.{key}.true'))
        case.update(id=f'm9.events.{key}.trailing',title=f'Event noun {key}: reject an extra trailing scalar',text=case['text']+'¤',expected='reject',note='Negative boundary test: the event paradigm must consume the entire word; the extra scalar is deliberately invalid.')
        snapshot['laboratory']['cases'].append(case)
    call('forge.draft.replace',snapshot=snapshot);ours=call('forge.commit',label='Test review · exact event-word boundaries')['head']
    w=IntegrationWindow(s,api);w.showMaximized();QTest.qWait(500)
    call('ui.forge',section='Merges',merge_source='lexical-review')
    panel=w.forge_panel.integration;plan=panel.plan
    if [c['path'] for c in plan['conflicts']]!=['/wiki/m9-release-policy/body']: raise ValueError('DEMO_UNEXPECTED_CONFLICTS')
    panel.label.setText('0.3.0 · Merge lexical and test reviews')
    panel.conflicts.cellWidget(0,4).setCurrentIndex(2)
    QTest.qWait(200);call('ui.capture',path=str(out/'01-merge-review.png'))
    # Exercise the real conflict-resolution button and its guarded dispatcher.
    QTest.mouseClick(panel.apply_button,Qt.MouseButton.LeftButton);QTest.qWait(200)
    merged=s.forge.status()['head']
    if merged==ours: raise ValueError('DEMO_MERGE_FAILED: '+w.forge_panel.message.text())
    call('ui.capture',path=str(out/'02-merged.png'))
    if s.capture()!=original: raise ValueError('DEMO_FORGE_CHANGED_WORKBENCH')
    suite=call('forge.lab.run',version=merged,directory=str(out/'suite'))
    run=call('forge.test.run',version=merged,test_id='tempest-dreams',directory=str(out/'tempest'))
    if run['status'] in ('Fail','Error'): raise ValueError('DEMO_PAGE_FAILED: '+json.dumps(run))
    same_pixels=rgba_hash(QImage(run['proof']))==rgba_hash(QImage(str(source/'tempest-bound/proof.png')))
    if not same_pixels: raise ValueError('DEMO_PIXEL_REGRESSION')
    call('ui.forge',section='Releases');panel.version.setCurrentIndex(panel.version.findData(merged))
    panel.name.setText('0.3.0-experimental.1');panel.notes.setPlainText('Merged lexical and test reviews from 0.2.4. Retains all Shakespeare text and approved typography. Adds two negative event-word boundary assertions. Literary meaning, general prose parsing and conservative collision warnings remain open; this is a proposed language release, not author acceptance.')
    panel.create_release()
    releases=call('forge.releases')['releases']
    if not releases: raise ValueError('DEMO_RELEASE_FAILED: '+w.forge_panel.message.text())
    release=releases[0]
    call('ui.forge',section='Releases',release_name=release['name']);QTest.qWait(200);call('ui.capture',path=str(out/'03-release.png'))
    call('forge.release.export',name=release['name'],path=str(out/(release['name']+'.vayrelease.json')))
    call('forge.export',path=str(out/'forge-history-final.json'))
    call('ui.forge',section='Laboratory',version=merged,run_id=suite['runId'],lab_view='Results');QTest.qWait(200);call('ui.capture',path=str(out/'04-test-results.png'))
    editable=out/'Working-Tempest-0.3.0.vay.json';shutil.copy2(run['document'],editable)
    call('document.open',path=str(editable));call('ui.forge',tab='workbench');call('ui.sidebar',expanded=False)
    call('ui.workspace',source=False,diagnostics=False,guides=False,fit_height=True);call('view.tool',tool='select')
    call('document.save',path=str(editable));QTest.qWait(400);call('ui.capture',path=str(out/'05-centered-workbench.png'))
    # Supply the output path to the real button, retaining its timestamp suggestion.
    destination=[]
    def choose(parent,title,suggested,filter,**kwargs):
        destination.append(out/Path(suggested).name);return str(destination[-1]),filter
    with patch('vayrshemon.integration_window.QFileDialog.getSaveFileName',side_effect=choose):
        QTest.mouseClick(next(b for b in w.findChildren(QPushButton) if b.text()=='PNG'),Qt.MouseButton.LeftButton)
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        QTest.qWait(100);jobs=s.jobs.status()['jobs']
        if jobs and jobs[-1]['status']!='running':break
    if not jobs or jobs[-1]['status']!='completed': raise ValueError('DEMO_PNG_BUTTON_FAILED: '+str(jobs))
    if file_hash(source/'Vayrshemon.vayforge')!=source_hash: raise ValueError('DEMO_M8_PROJECT_CHANGED')
    manifest=dict(project=str(s.forge.path),base=base,ours=ours,theirs=theirs,mergedVersion=merged,release=release,suite=suite,run=run,proof=jobs[-1],pixelIdenticalToM8=same_pixels,originalWorkbenchUnchanged=True,oldProjectUnchanged=True,editable=str(editable),sessionId=s.session_id)
    write_json(out/'demo.json',manifest)
    return s,api,w


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',type=Path,required=True);parser.add_argument('--serve',action='store_true');parser.add_argument('--open-existing',action='store_true');args=parser.parse_args()
    app=QApplication.instance() or QApplication([])
    root=Path(__file__).resolve().parents[1]
    if args.open_existing:
        from vayrshemon.forge import ForgeProject
        manifest=load_json(args.directory/'demo.json')
        s=IntegrationSession(root,source_fonts=False,recovery=True);s.open(manifest['editable'],advance_revision=False);s.forge=ForgeProject(manifest['project']);api=IntegrationAPI(s)
        w=IntegrationWindow(s,api);w.showMaximized();QTest.qWait(200)
        w.show_forge(section='Releases',release_name=manifest['release']['name'])
        w.show_forge(section='Laboratory',version=manifest['mergedVersion'],run_id=manifest['suite']['runId'])
        w.show_forge(tab='workbench');w.sidebar_dock.configure(expanded=False)
        w.configure_workspace(source=False,diagnostics=False,guides=False,fit_height=True)
    else:s,api,w=build(root,args.directory)
    if args.serve:
        server=LocalServer(api);app.aboutToQuit.connect(server.close);return app.exec()
    w.hide();w.job_timer.stop();s.finish();return 0


if __name__=='__main__':raise SystemExit(main())
