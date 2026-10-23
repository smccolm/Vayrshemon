"""Demonstrate a proposed discourse revision without altering M9 or the baseline."""
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
from vayrshemon.variation_api import VariationSession,VariationAPI
from vayrshemon.variation_window import VariationWindow
from vayrshemon.api import LocalServer
from vayrshemon.forge_runner import presentation
from tools.m0.common import load_json,write_json,file_hash
from tools.m10_language import propose
from tools.approved_baseline import rgba_hash,content_hash


def build(root,out):
    root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    source=root/'.local/demos/m9-release-v0.10.0';prior=load_json(source/'demo.json');source_hash=file_hash(source/'Vayrshemon.vayforge')
    s=VariationSession(root,source_fonts=False,recovery=False);s.open(prior['editable'],advance_revision=False);api=VariationAPI(s);transcript=[]
    def call(method,**params):
        if 'expected_generation' in api.methods[method][2]['properties']:
            status=s.forge.status();params.update(project_id=status['projectId'],expected_generation=status['generation'])
        reply=api.call(method,params,expected_revision=s.revision,document_id=s.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp')
        transcript.append(dict(method=method,params=params,reply=reply));write_json(out/'api-transcript.json',transcript)
        if not reply['ok']:raise RuntimeError(reply)
        return reply['result']
    call('forge.restore',path=str(source/'forge-history-final.json'),destination=str(out/'Vayrshemon.vayforge'))
    before=prior['mergedVersion'];original=s.capture();call('forge.branch',name='discourse-0.4',version=before)
    snapshot=propose(call('forge.read')['snapshot']);call('forge.draft.replace',snapshot=snapshot)
    w=VariationWindow(s,api);w.showMaximized();QTest.qWait(400)
    call('ui.forge',section='Variation');panel=w.forge_panel.variation
    # Exercise the real variation draft editor and Save button before committing.
    config=json.loads(panel.config.toPlainText());config['alternations'][0]['note']+=' Demo review: full forms remain available for rhetorical repetition.'
    panel.config.setPlainText(json.dumps(config,ensure_ascii=False,indent=2));QTest.mouseClick(panel.save_button,Qt.MouseButton.LeftButton)
    if panel.dirty:raise ValueError('DEMO_VARIATION_SAVE_FAILED: '+panel.notice.text())
    call('ui.forge',section='Wiki',record_id='m10-lived-discourse')
    wiki=w.forge_panel.wiki_editor;wiki.setPlainText(wiki.toPlainText()+'\n\nReview checkpoint: this page auditions one literary reading. The full forms, earlier cases and 0.3 release remain available for disagreement and revision.\n')
    if not w.forge_panel.flush():raise ValueError('DEMO_WIKI_SAVE_FAILED')
    after=call('forge.commit',label='0.4.0 · Optional literary discourse forms')['head']
    call('ui.forge',section='Wiki',version=after,record_id='m10-lived-discourse');QTest.qWait(200);call('ui.capture',path=str(out/'01-versioned-wiki.png'))
    call('ui.forge',section='Variation',version=after,variation_before=before,variation_after=after,variation_test='tempest-dreams')
    # Compare through the visible button as well as the shared control API.
    QTest.mouseClick(panel.compare_button,Qt.MouseButton.LeftButton);QTest.qWait(200);call('ui.capture',path=str(out/'02-variation-comparison.png'))
    comparison=call('forge.variation.compare',before=before,after=after,test_id='tempest-dreams');write_json(out/'comparison.json',comparison)
    regression=call('forge.lab.compare',before=before,after=after);write_json(out/'previous-suite-comparison.json',regression)
    if any(r['regression'] for r in regression['cases']):raise ValueError('DEMO_OLD_CASE_REGRESSION')
    suite=call('forge.lab.run',version=after,directory=str(out/'suite'))
    audit=call('forge.variation.run',version=after,test_id='tempest-dreams',directory=str(out/'audit'))
    if s.capture()!=original:raise ValueError('DEMO_FORGE_CHANGED_WORKBENCH')
    call('ui.forge',section='Laboratory',version=after,run_id=suite['runId'],lab_view='Results');QTest.qWait(200);call('ui.capture',path=str(out/'03-context-test-results.png'))
    run=call('forge.test.run',version=after,test_id='tempest-dreams',directory=str(out/'tempest'))
    if run['status'] in ('Fail','Error'):raise ValueError('DEMO_PAGE_FAILED: '+json.dumps(run))
    release=call('forge.release.create',name='0.4.0-experimental.1',version=after,channel='experimental',notes='Proposed literary discourse alternatives with explicit context tests and an advisory before/after audit. Earlier full forms and M9 assertions remain. Mechanical checks do not establish naturalness, semantic equivalence or author acceptance.',suite_run_id=suite['runId'],workbench_run_id=run['runId'])
    call('forge.release.export',name=release['name'],path=str(out/(release['name']+'.vayrelease.json')));call('forge.export',path=str(out/'forge-history-final.json'))
    editable=out/'Working-Tempest-0.4.0.vay.json';shutil.copy2(run['document'],editable);call('document.open',path=str(editable));call('ui.forge',tab='workbench');call('ui.sidebar',expanded=False)
    call('ui.workspace',source=False,diagnostics=False,guides=False,fit_height=True);call('view.tool',tool='select');call('document.save',path=str(editable));QTest.qWait(300);call('ui.capture',path=str(out/'04-approved-workbench.png'))
    expected=presentation(load_json(root/'.local/baselines/visual.workbench.2026-10-23/approved.vay.json')['state'])
    if presentation(s.capture())!=expected:raise ValueError('DEMO_PRESENTATION_CHANGED')
    destination=[]
    def choose(parent,title,suggested,filter,**kwargs):destination.append(out/Path(suggested).name);return str(destination[-1]),filter
    with patch('vayrshemon.integration_window.QFileDialog.getSaveFileName',side_effect=choose):QTest.mouseClick(next(b for b in w.findChildren(QPushButton) if b.text()=='PNG'),Qt.MouseButton.LeftButton)
    deadline=time.monotonic()+90;jobs=[]
    while time.monotonic()<deadline:
        QTest.qWait(100);jobs=s.jobs.status()['jobs']
        if jobs and jobs[-1]['status']!='running':break
    if not jobs or jobs[-1]['status']!='completed':raise ValueError('DEMO_PNG_FAILED: '+str(jobs))
    image=QImage(str(destination[-1]))
    if image.isNull() or image.width()<3400:raise ValueError('DEMO_PNG_DECODE_FAILED')
    if file_hash(source/'Vayrshemon.vayforge')!=source_hash:raise ValueError('DEMO_M9_PROJECT_CHANGED')
    manifest=dict(project=str(s.forge.path),beforeVersion=before,finalVersion=after,release=release,suite=suite,audit=audit,run=run,proof=jobs[-1],shareImage=str(destination[-1]),sharePixelsSha256=rgba_hash(image),shareDimensions=[image.width(),image.height()],comparison=comparison,previousCaseRegressions=0,originalWorkbenchUnchanged=True,oldProjectUnchanged=True,presentationSha256=content_hash(expected),editable=str(editable),sessionId=s.session_id)
    write_json(out/'demo.json',manifest);return s,api,w


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',type=Path,required=True);parser.add_argument('--serve',action='store_true');parser.add_argument('--open-existing',action='store_true');args=parser.parse_args()
    app=QApplication.instance() or QApplication([]);root=Path(__file__).resolve().parents[1]
    if args.open_existing:
        from vayrshemon.forge import ForgeProject
        m=load_json(args.directory/'demo.json');s=VariationSession(root,source_fonts=False,recovery=True);s.open(m['editable'],advance_revision=False);s.forge=ForgeProject(m['project']);api=VariationAPI(s);w=VariationWindow(s,api);w.showMaximized();QTest.qWait(200)
        w.show_forge(section='Variation',version=m['finalVersion'],variation_before=m['beforeVersion'],variation_after=m['finalVersion'],variation_test='tempest-dreams')
        w.show_forge(section='Laboratory',version=m['finalVersion'],run_id=m['suite']['runId']);w.show_forge(tab='workbench');w.sidebar_dock.configure(expanded=False);w.configure_workspace(source=False,diagnostics=False,guides=False,fit_height=True)
    else:s,api,w=build(root,args.directory)
    if args.serve:
        server=LocalServer(api);app.aboutToQuit.connect(server.close);return app.exec()
    w.hide();w.job_timer.stop();s.finish();return 0


if __name__=='__main__':raise SystemExit(main())
