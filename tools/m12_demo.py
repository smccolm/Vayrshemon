"""Demonstrate exact Roman readings and an independently versioned continuity proposal."""
from pathlib import Path
import argparse,json,shutil,time,uuid
from unittest.mock import patch
from PySide6.QtWidgets import QApplication,QPushButton
from PySide6.QtGui import QImage
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from vayrshemon.reading_api import ReadingSession,ReadingAPI
from vayrshemon.reading_window import ReadingWindow
from vayrshemon.api import LocalServer
from vayrshemon import reading
from vayrshemon.forge import ForgeProject
from vayrshemon.forge_runner import presentation
from tools.m0.common import load_json,write_json,file_hash
from tools.m12_language import propose
from tools.approved_baseline import rgba_hash,content_hash


def build(root,out):
    root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    source=root/'.local/demos/m11-maxima-v0.12.0';prior=load_json(source/'demo.json');source_hash=file_hash(source/'Vayrshemon.vayforge')
    s=ReadingSession(root,source_fonts=False,recovery=False);s.open(prior['editable'],advance_revision=False);api=ReadingAPI(s);transcript=[]
    def call(method,**params):
        if 'expected_generation' in api.methods[method][2]['properties']:
            status=s.forge.status();params.update(project_id=status['projectId'],expected_generation=status['generation'])
        reply=api.call(method,params,expected_revision=s.revision,document_id=s.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp')
        transcript.append(dict(method=method,params=params,reply=reply));write_json(out/'api-transcript.json',transcript)
        if not reply['ok']:raise RuntimeError(reply)
        return reply['result']
    call('forge.restore',path=str(source/'forge-history-final.json'),destination=str(out/'Vayrshemon.vayforge'))
    before=prior['finalVersion'];original=s.capture();call('forge.branch',name='reading-continuity-0.6',version=before)
    old=call('forge.read')['snapshot'];snapshot=propose(old);call('forge.draft.replace',snapshot=snapshot)
    if snapshot['language']['lexicon']!=old['language']['lexicon'] or next(t for t in snapshot['tests'] if t['id']=='tempest-dreams')!=next(t for t in old['tests'] if t['id']=='tempest-dreams'):raise ValueError('DEMO_PRIOR_TEXT_CHANGED')
    w=ReadingWindow(s,api);w.showMaximized();QTest.qWait(300)
    call('ui.forge',section='Reading',reading_test='tempest-dreams',reading_mode='transliteration',reading_preview=True);QTest.qWait(200);call('ui.capture',path=str(out/'01-roman-reading.png'))
    call('ui.forge',section='Wiki',record_id='m12-reading-and-continuity')
    wiki=w.forge_panel.wiki_editor;wiki.setPlainText(wiki.toPlainText()+'\n\nDemo review: original Tempest spellings and eight sentence-initial Maxima retained. All 47 letter pairs have distinct corresponding Roman forms. The new continuity passage remains a separate optional proposal; the fuller subject expression is retained.\n')
    if not w.forge_panel.flush():raise ValueError('DEMO_WIKI_SAVE_FAILED')
    after=call('forge.commit',label='0.6.0 · Parallel reading and continuous subjects')['head']
    call('ui.forge',section='Wiki',version=after,record_id='m12-reading-and-continuity');QTest.qWait(200);call('ui.capture',path=str(out/'02-versioned-wiki.png'))
    regression=call('forge.lab.compare',before=before,after=after);write_json(out/'previous-suite-comparison.json',regression)
    if any(r['regression'] for r in regression['cases']):raise ValueError('DEMO_OLD_CASE_REGRESSION')
    suite=call('forge.lab.run',version=after,directory=str(out/'suite'))
    audit=call('forge.variation.run',version=after,test_id='tempest-dreams',directory=str(out/'audit'))
    spelling_audit=call('forge.spelling.run',version=after,test_id='tempest-dreams',directory=str(out/'spelling'))
    if spelling_audit['status']!='Pass':raise ValueError('DEMO_SPELLING_FAILED')
    if s.capture()!=original:raise ValueError('DEMO_FORGE_CHANGED_WORKBENCH')
    call('ui.forge',section='Laboratory',version=after,run_id=suite['runId'],lab_view='Results');QTest.qWait(200);call('ui.capture',path=str(out/'03-language-test-results.png'))
    runs={}
    for key,test,mode in [('english','tempest-dreams','translation'),('full','actors-continuity-full','transliteration'),('implicit','actors-continuity-implicit','transliteration'),('transliteration','tempest-dreams','transliteration')]:
        run=call('forge.test.run',version=after,test_id=test,reading_mode=mode,directory=str(out/key));runs[key]=run
        if run['status'] in ('Fail','Error'):raise ValueError('DEMO_PAGE_FAILED: '+json.dumps(dict(key=key,status=run['status'],error=run.get('error'),checks=run['checks'])))
        # Only this script's temporary view/selection state is discarded.
        call('document.open',path=run['document'],discardUnsaved=True);call('ui.forge',tab='workbench');call('ui.sidebar',expanded=False)
        call('ui.workspace',source=False,diagnostics=False,guides=False,fit_height=True);QTest.qWait(200);call('ui.capture',path=str(out/('04-'+key+'.png')))
    run=runs['transliteration']
    release=call('forge.release.create',name='0.6.0-experimental.1',version=after,channel='experimental',notes='Exact Thimfora / original transliteration 7 readings preserve Maxima and legacy slots. A separate optional continuous-subject proposal retains full forms and requires an explicit adjacent antecedent. Tempest, prior cases and dictionary remain unchanged. Mechanical checks do not certify literary meaning or author acceptance; the original Roman p sidebearing remains visible for review.',suite_run_id=suite['runId'],workbench_run_id=run['runId'])
    call('forge.release.export',name=release['name'],path=str(out/(release['name']+'.vayrelease.json')));call('forge.export',path=str(out/'forge-history-final.json'))
    editable=out/'Working-Tempest-0.6.0-transliteration.vay.json';shutil.copy2(run['document'],editable);call('document.open',path=str(editable),discardUnsaved=True);call('ui.forge',tab='workbench');call('ui.sidebar',expanded=False)
    call('ui.workspace',source=False,diagnostics=False,guides=False,fit_height=True);call('view.tool',tool='select');call('document.save',path=str(editable));QTest.qWait(300);call('ui.capture',path=str(out/'05-approved-reading-workbench.png'))
    baseline=load_json(root/'.local/baselines/visual.workbench.2026-10-23/approved.vay.json')['state']
    if not reading.presentation_matches(s.capture(),baseline,'transliteration'):raise ValueError('DEMO_PRESENTATION_CHANGED')
    left,right=reading.pairs(s.capture())
    if reading.text_blocks(left)!=reading.text_blocks(right):raise ValueError('DEMO_READING_CHANGED_SLOTS')
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
    if file_hash(source/'Vayrshemon.vayforge')!=source_hash:raise ValueError('DEMO_M11_PROJECT_CHANGED')
    manifest=dict(project=str(s.forge.path),beforeVersion=before,finalVersion=after,release=release,suite=suite,audit=audit,spelling=spelling_audit,run=run,runs=runs,proof=jobs[-1],shareImage=str(destination[-1]),sharePixelsSha256=rgba_hash(image),shareDimensions=[image.width(),image.height()],previousCaseRegressions=0,originalWorkbenchUnchanged=True,oldProjectUnchanged=True,dictionaryUnchanged=True,tempestUnchanged=True,presentationSha256=content_hash(presentation(baseline)),editable=str(editable),sessionId=s.session_id)
    write_json(out/'demo.json',manifest);return s,api,w


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',type=Path,required=True);parser.add_argument('--serve',action='store_true');parser.add_argument('--open-existing',action='store_true');args=parser.parse_args()
    app=QApplication.instance() or QApplication([]);root=Path(__file__).resolve().parents[1]
    if args.open_existing:
        m=load_json(args.directory/'demo.json');s=ReadingSession(root,source_fonts=False,recovery=True);s.open(m['editable'],advance_revision=False);s.forge=ForgeProject(m['project']);api=ReadingAPI(s);w=ReadingWindow(s,api);w.showMaximized();QTest.qWait(200)
        w.show_forge(section='Laboratory',version=m['finalVersion'],run_id=m['suite']['runId']);w.show_forge(section='Orthography',version=m['finalVersion'],spelling_test='tempest-dreams',spelling_run=m['spelling']['runId']);w.show_forge(section='Reading',version=m['finalVersion'],reading_test='tempest-dreams',reading_mode='transliteration',reading_preview=True);w.show_forge(tab='workbench');w.sidebar_dock.configure(expanded=False);w.configure_workspace(source=False,diagnostics=False,guides=False,fit_height=True)
    else:s,api,w=build(root,args.directory)
    if args.serve:
        server=LocalServer(api);app.aboutToQuit.connect(server.close);return app.exec()
    w.hide();w.job_timer.stop();s.finish();return 0


if __name__=='__main__':raise SystemExit(main())
