"""Real merges, release gates, responsive centering and the desktop PNG button."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import uuid
from PySide6.QtCore import QCoreApplication,QEvent,Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QPushButton,QMessageBox
from tests.test_m8 import fixture
from vayrshemon.forge import ForgeProject,digest,encoded
from vayrshemon import forge_merge,forge_release,forge_lab,pages
from vayrshemon.integration_api import IntegrationSession,IntegrationAPI,METHODS
from vayrshemon.integration_window import IntegrationWindow
from tools.m0.common import write_json,file_hash

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m9'/uuid.uuid4().hex;self.work.mkdir(parents=True)
        self.snapshot=fixture();self.snapshot['wiki']=[dict(id='rule',title='Rule',body='Base',ruleIds=['grammar'])]
        self.snapshot['tests']=[dict(id='page',title='Synthetic bound page',ruleIds=['grammar'],paragraphs=[dict(text='tal mi lumow',translation='A synthetic example.',analysis='Structural data.')],caseIds=[['clause']])]
        self.p=ForgeProject.create(self.work/'language.vayforge','Integration tests',self.snapshot)

    def edit(self,mutate,label):
        s=self.p.read()['snapshot'];mutate(s);self.p.replace_draft(s,self.p.status()['generation'])
        return self.p.commit(label,self.p.status()['generation'])['head']

    def branch(self,name,version): self.p.branch(name,self.p.status()['generation'],version)
    def checkout(self,name): self.p.checkout(name,self.p.status()['generation'])

    def diverge(self):
        base=self.p.status()['head'];self.branch('source',base)
        def source(s): s['wiki'][0]['body']='Source';s['wiki'].append(dict(id='new',title='New',body='Added',ruleIds=[]))
        theirs=self.edit(source,'Source changes');self.checkout('main')
        def target(s): s['wiki'][0]['body']='Target';s['wiki'][0]['title']='Independent title'
        ours=self.edit(target,'Target changes');return base,ours,theirs

    def test_three_way_field_merge_records_both_parents_and_explicit_choice(self):
        base,ours,theirs=self.diverge();plan=forge_merge.preview(self.p,'source')
        self.assertEqual(plan['base'],base);self.assertEqual([c['path'] for c in plan['conflicts']],['/wiki/rule/body'])
        before=self.p.read()
        with self.assertRaisesRegex(ValueError,'UNRESOLVED'): forge_merge.apply(self.p,'source',plan['planId'],'Merge',{},plan['generation'])
        self.assertEqual(self.p.read(),before)
        result=forge_merge.apply(self.p,'source',plan['planId'],'Merged',{'/wiki/rule/body':{'choice':'theirs'}},plan['generation'])
        self.assertEqual(self.p.status()['version'],'1.1.0')
        s=self.p.read()['snapshot'];self.assertEqual(s['wiki'][0]['body'],'Source');self.assertEqual(s['wiki'][0]['title'],'Independent title');self.assertEqual(len(s['wiki']),2)
        row=next(c for c in self.p.history() if c['id']==result['head']);self.assertEqual(row['parents'],[ours,theirs])
        self.assertEqual(self.p.read(base)['snapshot'],self.snapshot)
        with self.assertRaisesRegex(ValueError,'ALREADY_CONTAINED'): forge_merge.preview(self.p,'source')
        bundle=self.work/'history.json';self.p.export(bundle);restored=ForgeProject.restore(bundle,self.work/'restored.vayforge')
        self.assertEqual(restored.history(),self.p.history());self.assertEqual(restored.read()['snapshot'],s)
        self.checkout('source');self.edit(lambda s:s['wiki'][0].update(title='Second source'),'Advance source');self.checkout('main')
        self.assertEqual(forge_merge.preview(self.p,'source')['base'],theirs)

    def test_dirty_drafts_and_stale_plans_never_overwrite(self):
        self.diverge();plan=forge_merge.preview(self.p,'source')
        draft=self.p.read()['snapshot'];draft['research']['unsaved']='retained';self.p.replace_draft(draft,self.p.status()['generation'])
        with self.assertRaisesRegex(ValueError,'DIRTY'): forge_merge.preview(self.p,'source')
        with self.assertRaisesRegex(ValueError,'STALE_FORGE'): forge_merge.apply(self.p,'source',plan['planId'],'Merge',{},plan['generation'])
        self.assertEqual(self.p.read()['snapshot'],draft)
        self.checkout('source');source_draft=self.p.read()['snapshot'];source_draft['research']['pending']=True;self.p.replace_draft(source_draft,self.p.status()['generation']);self.checkout('main')
        self.assertEqual(self.p.read()['snapshot'],draft)
        self.p.commit('Retain draft',self.p.status()['generation'])
        newer=forge_merge.preview(self.p,'source')
        with self.assertRaisesRegex(ValueError,'STALE_PLAN'): forge_merge.apply(self.p,'source',plan['planId'],'Merge',{},newer['generation'])
        self.assertNotIn('pending',self.p.read()['snapshot']['research'])

    def test_delete_edit_conflicts_and_atomic_lists_and_invalid_cross_references(self):
        base=self.p.status()['head'];self.branch('source',base)
        self.edit(lambda s:s['wiki'].clear(),'Delete wiki');self.checkout('main')
        self.edit(lambda s:s['wiki'][0].update(body='Edited'),'Edit wiki')
        p=forge_merge.preview(self.p,'source');self.assertEqual(p['conflicts'][0]['path'],'/wiki/rule');self.assertFalse(p['conflicts'][0]['theirs']['present'])
        forge_merge.apply(self.p,'source',p['planId'],'Delete resolution',{'/wiki/rule':{'choice':'delete'}},p['generation'])
        self.assertEqual(self.p.read()['snapshot']['wiki'],[])
        conflicts=[];result=forge_merge.merge_values(['a'],['b'],['c'],{},conflicts,'/order');self.assertEqual(len(conflicts),1)
        self.assertEqual(result,['b'])
        self.branch('bad-source',self.p.status()['head']);self.edit(lambda s:s['wiki'].append(dict(id='new',title='Source',body='Source',ruleIds=[])),'Source add');self.checkout('main')
        self.edit(lambda s:s['wiki'].append(dict(id='new',title='Target',body='Target',ruleIds=[])),'Target add')
        p=forge_merge.preview(self.p,'bad-source');before=self.p.read()
        with self.assertRaises(ValueError): forge_merge.apply(self.p,'bad-source',p['planId'],'Invalid',{'/wiki/new':{'choice':'custom','value':{'id':'invalid'}}},p['generation'])
        self.assertEqual(self.p.read(),before)

    def evidence(self):
        version=self.p.status()['head'];suite=forge_lab.run(self.p,version,self.work/'suite')
        report=forge_lab.evaluate(self.p.read(version)['snapshot']);folder=self.work/'page';folder.mkdir()
        for name in ('document.json','proof.png'): (folder/name).write_bytes(b'synthetic evidence')
        write_json(folder/'language.json',report)
        page=dict(runId=uuid.uuid4().hex,version=version,projectId=self.p.status()['projectId'],testId='page',status='Needs review',createdAt='synthetic',manifestPath=str(folder/'run.json'),document=str(folder/'document.json'),documentSha256=file_hash(folder/'document.json'),proof=str(folder/'proof.png'),proofSha256=file_hash(folder/'proof.png'),languageResults=dict(path=str(folder/'language.json'),sha256=file_hash(folder/'language.json')),test=self.snapshot['tests'][0],checks=[dict(name='Semantic review',status='Needs review')])
        write_json(folder/'run.json',page);self.p.record_run(page)
        return dict(name='0.3.0-experimental.1',version=version,channel='experimental',notes='Synthetic release; meaning is unreviewed.',suite_run_id=suite['runId'],workbench_run_id=page['runId'],expected_generation=self.p.status()['generation'])

    def test_release_is_immutable_and_bundle_retains_evidence_after_branch_moves(self):
        args=self.evidence();r=forge_release.create(self.p,**args);self.assertEqual(r['acceptance']['status'],'proposed');self.assertEqual(self.p.status()['version'],'1.1.0')
        self.edit(lambda s:s['wiki'][0].update(body='Later'),'Later version')
        self.assertEqual(forge_release.list_releases(self.p)[0],r)
        with self.p.connect() as db:
            with self.assertRaisesRegex(sqlite3.IntegrityError,'IMMUTABLE_RELEASE'): db.execute('DELETE FROM releases')
        with self.assertRaisesRegex(ValueError,'NAME_EXISTS'): forge_release.create(self.p,**dict(args,expected_generation=self.p.status()['generation']))
        export=forge_release.export(self.p,r['name'],self.work/'release.json');value=json.loads(Path(export['path']).read_text());self.assertEqual(value['sha256'],digest(value['data']))
        self.p.export(self.work/'history.json');restored=ForgeProject.restore(self.work/'history.json',self.work/'restored.vayforge')
        self.assertEqual(forge_release.list_releases(restored),[r])

    def test_release_rejects_stable_gaps_wrong_version_and_tampered_proof(self):
        args=self.evidence()
        with self.assertRaisesRegex(ValueError,'STABLE_GATES'): forge_release.create(self.p,**dict(args,channel='stable',reviewer='Synthetic tester'))
        new=self.edit(lambda s:s['wiki'][0].update(body='New'),'New')
        with self.assertRaisesRegex(ValueError,'VERSION_MISMATCH'): forge_release.create(self.p,**dict(args,version=new,expected_generation=self.p.status()['generation']))
        (self.work/'page/proof.png').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'ARTIFACT_CHANGED'): forge_release.create(self.p,**dict(args,expected_generation=self.p.status()['generation']))
        self.assertEqual(forge_release.list_releases(self.p),[])

    def session(self):
        root=self.work/'app';root.mkdir();shutil.copytree(ROOT/'schemas',root/'schemas');(root/'data').mkdir();shutil.copy2(ROOT/'data/fonts.json',root/'data/fonts.json')
        s=IntegrationSession(root,source_fonts=False,recovery=False);s.forge=self.p;return s,IntegrationAPI(s)

    def close(self,s,w):
        w.hide();w.job_timer.stop();w.deleteLater();s.window=None;s.finish();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);APP.processEvents()

    def test_qt_merge_choices_and_release_display_use_the_guarded_dispatcher(self):
        self.diverge();s,api=self.session();w=IntegrationWindow(s,api);before=s.capture()
        try:
            w.show();APP.processEvents();w.show_forge(section='Merges',merge_source='source')
            p=w.forge_panel.integration;self.assertEqual(p.conflicts.rowCount(),1)
            p.conflicts.cellWidget(0,4).setCurrentIndex(2);p.label.setText('Qt merged');QTest.mouseClick(p.apply_button,Qt.MouseButton.LeftButton)
            self.assertIn('MERGED',p.summary.toPlainText());self.assertEqual(self.p.read()['snapshot']['wiki'][0]['body'],'Source');self.assertEqual(s.capture(),before)
            self.assertEqual(api.version,'0.10.0');self.assertEqual(len(METHODS),127)
        finally:self.close(s,w)

    def test_single_page_centers_on_resize_zoom_and_sidebar_but_retains_hand_pan(self):
        s,api=self.session();w=IntegrationWindow(s,api)
        try:
            w.show();APP.processEvents();original=s.capture()
            def centered():
                APP.processEvents();w.preview.update_page();v=w.preview.navigation_state();area=pages.page_rect(s.current_page())
                for pos,extent,size in zip(v['pageOrigin'],(area.width(),area.height()),v['viewport']): self.assertAlmostEqual(pos+extent*v['zoom']/2,(size+24)/2,delta=1)
            centered();w.resize(1350,820);centered();w.sidebar_dock.configure(expanded=False);centered()
            w.preview.pan_by(51,37);v=w.preview.navigation_state();w.preview.update_page();self.assertEqual(w.preview.navigation_state(),v)
            self.assertEqual(s.capture(),original)
            s.view['zoom']=0.46;w.preview.update_page();centered()
        finally:self.close(s,w)

    def test_fit_height_and_width_buttons_replace_fit_page_without_reformatting(self):
        s,api=self.session();w=IntegrationWindow(s,api)
        try:
            w.show();APP.processEvents();original=deepcopy(s.state['pages'])
            buttons={b.text():b for b in w.findChildren(QPushButton)};self.assertNotIn('Fit page',buttons)
            for name,axis in [('Fit Height','height'),('Fit Width','width')]:
                w.preview.pan_by(80,50);QTest.mouseClick(buttons[name],Qt.MouseButton.LeftButton);APP.processEvents()
                area=pages.page_rect(s.current_page());v=w.preview.viewport();actual=getattr(area,axis)()*s.view['zoom']
                available=getattr(v,axis)()-56
                self.assertLessEqual(actual,available+1);self.assertLess(available-actual,getattr(area,axis)()*.011+1)
                self.assertEqual(s.state['pages'],original)
                if name=='Fit Width':
                    w.preview.update_page();nav=w.preview.navigation_state()
                    self.assertEqual(nav['pageOrigin'][1],w.preview.RULER)
                    self.assertAlmostEqual(nav['pageOrigin'][0]+area.width()*nav['zoom']/2,(v.width()+w.preview.RULER)/2,delta=1)
            with self.assertRaisesRegex(ValueError,'CHOOSE_ONE'):w.configure_workspace(fit_height=True,fit_width=True)
        finally:self.close(s,w)

    @unittest.skipUnless((ROOT/'.local/baselines/visual.workbench.2026-10-23/approved.vay.json').exists(),'Private approved presentation absent')
    def test_png_button_exports_approved_enlarged_page_with_timestamp_and_supported_dpi(self):
        s=IntegrationSession(ROOT,source_fonts=False,recovery=False);s.open(ROOT/'.local/baselines/visual.workbench.2026-10-23/approved.vay.json',advance_revision=False);api=IntegrationAPI(s);w=IntegrationWindow(s,api)
        try:
            original=s.capture();destination=self.work/'button-proof.png'
            def choose(*args,**kwargs):
                self.assertRegex(args[2],r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_\d{3}\.png$');return str(destination), 'PNG (*.png)'
            w.show();APP.processEvents()
            with patch('vayrshemon.integration_window.QFileDialog.getSaveFileName',side_effect=choose):
                QTest.mouseClick(next(b for b in w.findChildren(QPushButton) if b.text()=='PNG'),Qt.MouseButton.LeftButton)
            deadline=time.monotonic()+90
            while time.monotonic()<deadline:
                APP.processEvents();jobs=s.jobs.status()['jobs']
                if jobs and jobs[-1]['status']!='running':break
                QTest.qWait(100)
            self.assertTrue(jobs);job=jobs[-1];self.assertEqual(job['status'],'completed',job)
            result=job['result'];self.assertLess(result['preflight']['dpi'],300);self.assertGreater(result['preflight']['dpi'],288)
            image=QImage(str(destination));self.assertFalse(image.isNull());self.assertGreater(image.width(),3400)
            self.assertEqual(s.capture(),original);self.assertEqual(file_hash(destination),result['sha256'])
            write_json(self.work/'png-button-result.json',result)
        finally:self.close(s,w)

    def test_headless_mcp_advertises_merge_release_controls(self):
        messages=[dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2024-11-05',capabilities={},clientInfo=dict(name='test',version='1'))),dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=2,method='tools/list')]
        p=subprocess.run([sys.executable,'-m','vayrshemon','mcp','--headless','--integration','--no-source-fonts'],input='\n'.join(json.dumps(m) for m in messages)+'\n',text=True,capture_output=True,cwd=ROOT,timeout=30)
        self.assertEqual(p.returncode,0,p.stderr);responses=[json.loads(line) for line in p.stdout.splitlines()];tools=next(r['result']['tools'] for r in responses if r.get('id')==2)
        self.assertEqual(len(tools),127);self.assertTrue(any('forge_merge_apply' in t['name'] for t in tools))

    def test_api_merge_idempotency_and_project_identity_guard(self):
        self.diverge();s,api=self.session()
        try:
            plan=forge_merge.preview(self.p,'source');params=dict(project_id=plan['projectId'],expected_generation=plan['generation'],source='source',plan_id=plan['planId'],label='API merged',resolutions={'/wiki/rule/body':{'choice':'theirs'}})
            guards=dict(expected_revision=s.revision,document_id=s.state['documentId'],idempotency_key='merge-test',origin='mcp')
            bad=api.call('forge.merge.apply',dict(params,project_id='another'),**dict(guards,idempotency_key='wrong-project'))
            self.assertFalse(bad['ok']);self.assertIn('PROJECT_ID_MISMATCH',bad['error']['message'])
            first=api.call('forge.merge.apply',params,**guards);self.assertTrue(first['ok'],first)
            self.assertEqual(api.call('forge.merge.apply',params,**guards),first)
        finally:s.finish()

    def test_png_overwrite_requires_confirmation_and_keeps_concurrent_changes(self):
        s,api=self.session();w=IntegrationWindow(s,api);destination=self.work/'existing.png';destination.write_bytes(b'original')
        try:
            with patch('vayrshemon.integration_window.QFileDialog.getSaveFileName',return_value=(str(destination),'PNG')),patch('vayrshemon.integration_window.QMessageBox.question',return_value=QMessageBox.StandardButton.No):
                w.export_png()
            self.assertEqual(s.jobs.status()['jobs'],[]);self.assertEqual(destination.read_bytes(),b'original')
            with patch('vayrshemon.integration_window.QFileDialog.getSaveFileName',return_value=(str(destination),'PNG')),patch('vayrshemon.integration_window.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):
                w.export_png()
            deadline=time.monotonic()+40
            while time.monotonic()<deadline:
                job=s.jobs.status()['jobs'][-1]
                if job['status']!='running':break
                QTest.qWait(100)
            self.assertEqual(job['status'],'completed',job);self.assertFalse(QImage(str(destination)).isNull())
            job=s.jobs.start(path=str(destination),format='png',mode='mono',dpi=72,raster_policy='raster',page_id=s.current_page()['pageId'],replace_sha256=file_hash(destination))
            destination.write_bytes(b'concurrent edit')
            deadline=time.monotonic()+40
            while time.monotonic()<deadline:
                job=s.jobs.status(job['jobId'])
                if job['status']!='running':break
                QTest.qWait(100)
            self.assertEqual(job['status'],'failed');self.assertIn('TARGET_CHANGED',job['error']);self.assertEqual(destination.read_bytes(),b'concurrent edit')
        finally:self.close(s,w)
