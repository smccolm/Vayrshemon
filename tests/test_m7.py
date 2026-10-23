"""Forge persistence, stale writers, historical reproducibility and real Qt edits."""
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
import uuid
from unittest.mock import patch
if os.name!='nt': os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtTest import QTest
from tools.m0.common import load_json,write_json
from vayrshemon.forge import ForgeProject,empty_snapshot,digest
from vayrshemon.forge_api import ForgeSession,ForgeAPI
from vayrshemon.forge_window import ForgeWindow
from vayrshemon.forge_archive import symbol_frequency
ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class ForgeTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m7'/uuid.uuid4().hex;self.work.mkdir(parents=True)
        self.p=ForgeProject.create(self.work/'language.vayforge','Test language')

    def wiki(self,text='Original rule'):
        return dict(id='rule',title='Grammar',body=text,ruleIds=[])

    def test_atomic_versions_branches_stale_writers_and_wiki_history(self):
        head=self.p.status()['head'];other=ForgeProject(self.p.path)
        self.p.put('wiki',self.wiki(),0)
        with self.assertRaisesRegex(ValueError,'STALE_FORGE'): other.put('wiki',self.wiki('Lost update'),0)
        self.assertEqual(self.p.read()['snapshot']['wiki'][0]['body'],'Original rule')
        v1=self.p.commit('Language 0.1',1)['head']
        self.p.put('wiki',self.wiki('Edited rule'),2)
        self.assertEqual(self.p.read(v1)['snapshot']['wiki'][0]['body'],'Original rule')
        self.p.branch('experiment',3,head)
        self.assertEqual(self.p.read()['snapshot']['wiki'],[])
        self.p.checkout('main',4)
        self.assertEqual(self.p.read()['snapshot']['wiki'][0]['body'],'Edited rule')
        v2=self.p.commit('Language 0.2',5)['head']
        self.assertEqual(self.p.diff(v1,v2)['collections']['wiki']['changed'],['rule'])
        with self.p.connect() as db:
            with self.assertRaisesRegex(sqlite3.IntegrityError,'IMMUTABLE'): db.execute('DELETE FROM commits')

    def test_invalid_record_rolls_back_and_bundle_preserves_draft_and_hashes(self):
        with self.assertRaises(ValueError): self.p.put('wiki',dict(self.wiki(),ruleIds=['missing']),0)
        self.assertEqual(self.p.status()['generation'],0)
        self.p.put('wiki',self.wiki(),0);v=self.p.commit('v1',1)['head'];self.p.put('wiki',self.wiki('draft'),2)
        path=self.work/'bundle.json';self.p.export(path)
        restored=ForgeProject.restore(path,self.work/'restored.vayforge')
        self.assertEqual(restored.history(),self.p.history())
        self.assertEqual(restored.read()['snapshot'],self.p.read()['snapshot']);self.assertEqual(restored.read(v)['snapshot']['wiki'][0]['body'],'Original rule')
        payload=load_json(path);payload['data']['branches'][0]['draft']['wiki'][0]['body']='corrupt';write_json(self.work/'bad.json',payload)
        with self.assertRaisesRegex(ValueError,'BUNDLE_INVALID'): ForgeProject.restore(self.work/'bad.json',self.work/'bad.vayforge')
        self.assertFalse((self.work/'bad.vayforge').exists())

    def test_transaction_failure_keeps_last_complete_draft(self):
        with self.assertRaises(RuntimeError):
            with self.p.writer(0) as (db,meta):
                db.execute('UPDATE branches SET draft=?',(json.dumps(empty_snapshot()),));raise RuntimeError('simulated crash before commit')
        self.assertEqual(ForgeProject(self.p.path).status()['generation'],0)

    def test_letter_identity_not_unicode_casefold(self):
        mapping=load_json(ROOT/'data/orthography/thimfora-79.json')
        counts=symbol_frequency(['Aa'+chr(223)+chr(222)+'?🙂'],mapping)
        byid={r['symbolId']:r['count'] for r in counts['letters']}
        self.assertEqual(byid['thimfora.letter.004'],2);self.assertEqual(byid['thimfora.letter.037'],2)
        self.assertEqual(counts['letterCount'],4);self.assertIn('U+1F642',counts['unknownSlots'])

    def test_api_contract_generations_idempotency_and_document_separation(self):
        shutil.copytree(ROOT/'schemas',self.work/'schemas');(self.work/'data').mkdir();shutil.copy2(ROOT/'data/fonts.json',self.work/'data/fonts.json')
        s=ForgeSession(self.work,source_fonts=False,recovery=False);api=ForgeAPI(s)
        try:
            original=s.capture()
            opened=api.call('forge.open',dict(path=str(self.p.path)),expected_revision=s.revision,idempotency_key='open')
            self.assertTrue(opened['ok'],opened)
            params=dict(collection='wiki',record=self.wiki(),expected_generation=0,project_id=self.p.status()['projectId'])
            value=api.call('forge.record.put',params,expected_revision=s.revision,idempotency_key='wiki')
            self.assertTrue(value['ok'],value);self.assertEqual(api.call('forge.record.put',params,expected_revision=s.revision,idempotency_key='wiki'),value)
            stale=api.call('forge.record.put',params,expected_revision=s.revision,idempotency_key='stale')
            self.assertFalse(stale['ok']);self.assertEqual(s.capture(),original)
            wrong=dict(params,project_id='different-project',expected_generation=1)
            self.assertFalse(api.call('forge.record.put',wrong,expected_revision=s.revision,idempotency_key='wrong-project')['ok'])
            self.assertEqual(s.revision,original['revision']);self.assertEqual(len(s._undo),0)
        finally: s.finish()

    def test_real_remote_client_and_mcp_advertise_forge(self):
        from vayrshemon.api import LocalServer
        shutil.copytree(ROOT/'schemas',self.work/'schemas');(self.work/'data').mkdir();shutil.copy2(ROOT/'data/fonts.json',self.work/'data/fonts.json')
        s=ForgeSession(self.work,source_fonts=False,recovery=False);s.forge=self.p;api=ForgeAPI(s);server=LocalServer(api,publish=False)
        script="""import json,sys,uuid
from pathlib import Path
from vayrshemon.api import remote_call
r,d=Path(sys.argv[1]),Path(sys.argv[2])
st=remote_call(r,'session.status',descriptor=d)['result']
p=remote_call(r,'forge.status',descriptor=d)['result']
v=remote_call(r,'forge.record.put',dict(collection='wiki',record=dict(id='remote',title='Remote wiki',body='Through live socket',ruleIds=[]),expected_generation=p['generation'],project_id=p['projectId']),descriptor=d,expected_revision=st['revision'],document_id=st['documentId'],idempotency_key=uuid.uuid4().hex)
print(json.dumps(v))
"""
        process=subprocess.Popen([sys.executable,'-c',script,str(self.work),str(server.descriptor)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            deadline=time.monotonic()+20
            while process.poll() is None and time.monotonic()<deadline: APP.processEvents();QTest.qWait(10)
            output,error=process.communicate(timeout=2);self.assertEqual(process.returncode,0,error)
            self.assertTrue(json.loads(output)['ok'],output);self.assertEqual(self.p.read()['snapshot']['wiki'][0]['id'],'remote')
            request='\n'.join(json.dumps(r) for r in [
                dict(jsonrpc='2.0',id=0,method='initialize',params=dict(protocolVersion='2024-11-05',capabilities={},clientInfo=dict(name='M7 regression',version='1'))),
                dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=1,method='tools/list')])+'\n'
            result=subprocess.run([sys.executable,'-m','vayrshemon','--root',str(self.work),'mcp','--descriptor',str(server.descriptor)],input=request,capture_output=True,text=True,cwd=ROOT,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr);self.assertIn('forge',result.stdout)
            self.assertIn('expected_generation',result.stdout);self.assertIn('project_id',result.stdout)
        finally:
            if process.poll() is None: process.kill();process.communicate()
            server.close();s.finish()

    def test_real_wiki_edit_autosaves_and_historical_view_is_readonly(self):
        shutil.copytree(ROOT/'schemas',self.work/'schemas');(self.work/'data').mkdir();shutil.copy2(ROOT/'data/fonts.json',self.work/'data/fonts.json')
        self.p.put('wiki',self.wiki(),0);v=self.p.commit('v1',1)['head']
        s=ForgeSession(self.work,source_fonts=False,recovery=False);s.forge=self.p;api=ForgeAPI(s);w=ForgeWindow(s,api)
        try:
            w.show();APP.processEvents();before=s.capture();w.show_forge(section='Wiki');panel=w.forge_panel;panel.wiki_list.setCurrentRow(0)
            panel.wiki_editor.insertPlainText('Edited ');self.assertIsNotNone(panel.pending);self.assertTrue(panel.flush())
            self.assertIn('Edited ',self.p.read()['snapshot']['wiki'][0]['body']);self.assertEqual(self.p.read(v)['snapshot']['wiki'][0]['body'],'Original rule')
            w.show_forge(version=v,section='Wiki');panel.wiki_list.setCurrentRow(0)
            self.assertTrue(panel.wiki_editor.isReadOnly());self.assertEqual(panel.wiki_editor.toPlainText(),'Original rule');self.assertEqual(s.capture(),before)
        finally:
            w.hide();w.job_timer.stop();w.deleteLater();s.window=None;s.finish();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);APP.processEvents()

    def test_dictionary_autosave_reselection_keeps_latest_record(self):
        shutil.copytree(ROOT/'schemas',self.work/'schemas');(self.work/'data').mkdir();shutil.copy2(ROOT/'data/fonts.json',self.work/'data/fonts.json')
        entry=dict(id='word',label='Word',status='draft',citations=[],notes='',headword='original',orthographyId=None,pronunciation='',ipa='',partOfSpeech='noun',senses=[dict(id='word.sense',definition='A test word',status='draft',citations=[])],variants=[],etymology='',exampleIds=[],audioLinks=[])
        self.p.put('lexicon',entry,0)
        s=ForgeSession(self.work,source_fonts=False,recovery=False);s.forge=self.p;w=ForgeWindow(s,ForgeAPI(s))
        try:
            w.show();APP.processEvents();w.show_forge(section='Dictionary',record_id='word');panel=w.forge_panel
            for new in ('changed','revised'):
                panel.fields['headword'].setText(new);panel.queue('lexicon');self.assertTrue(panel.flush())
                panel.table.clearSelection();panel.table.selectRow(0)
                self.assertEqual(panel.fields['headword'].text(),new)
                self.assertEqual(self.p.read()['snapshot']['language']['lexicon'][0]['headword'],new)
            self.assertEqual(self.p.read()['snapshot']['language']['lexicon'][0]['notes'].count('Forge editorial draft'),1)
        finally:
            w.hide();w.job_timer.stop();w.deleteLater();s.window=None;s.finish();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);APP.processEvents()

    @unittest.skipUnless((ROOT/'.local/baselines/visual.workbench.2026-10-23/approved.vay.json').exists(),'Private approved baseline unavailable')
    def test_novel_run_preserves_presentation_and_pins_snapshot(self):
        from vayrshemon.forge_archive import archive_snapshot,proposal
        from vayrshemon.forge_runner import run,presentation
        snapshot=proposal(archive_snapshot(ROOT),ROOT);self.p.replace_draft(snapshot,0);version=self.p.commit('Draft 0.1',1)['head']
        report=run(ROOT,self.p,version,snapshot['tests'][0]['id'],self.work/'run')
        self.assertEqual(report['status'],'Needs review',report);self.assertEqual(report['checks'][2]['count'],0)
        actual=load_json(report['document'])['state'];baseline=load_json(ROOT/'.local/baselines/visual.workbench.2026-10-23/approved.vay.json')['state']
        self.assertNotEqual(actual['documentId'],baseline['documentId']);self.assertEqual(presentation(actual),presentation(baseline))
        self.assertTrue(Path(report['proof']).exists());self.assertEqual(self.p.runs()[0]['version'],version)
        self.assertEqual(actual['language']['links'],[])


if __name__=='__main__': unittest.main()
