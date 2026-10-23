"""Context gates, repetition evidence, immutable history and real Forge editing."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest
import uuid
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtWidgets import QApplication
from tests.test_m8 import fixture as laboratory_fixture
from vayrshemon.forge import ForgeProject,validate
from vayrshemon import forge_lab,forge_merge,forge_release,variation
from vayrshemon.variation_api import VariationSession,VariationAPI,METHODS
from vayrshemon.variation_window import VariationWindow

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


def fixture():
    s=laboratory_fixture();lab=s['laboratory']
    lab['rules'].append(dict(id='classified',title='Synthetic marked noun',grammarId='grammar',kind='forms',config=dict(entryIds=['noun'],prefixes=['ka'],slots=[dict(feature='case',values={'nom':'n','acc':'t'})])))
    lab['rules'][2]['config']['formRuleIds'].append('classified')
    v=variation.empty();s['variation']=v
    v['alternations']=[dict(id='known',title='Known neutral literary subject',grammarId='grammar',formRuleId='classified',fromPrefix='ka',toPrefix='',when=dict(register=['literary'],givenness=['established'],focus=['neutral'],role=['subject']),note='Synthetic condition fixture, not invented Vayrshemon.',status='proposed')]
    v['watch']=[dict(id='class',label='Synthetic class prefix',text='ka',minCount=2,minShare=.1)]
    tokens=[dict(start=0,end=6,role='object',entryId='noun',features={'case':'acc'}),dict(start=7,end=13,role='subject',entryId='noun',features={'case':'nom'}),dict(start=14,end=19,role='verb',entryId='root',features={'tense':'present'})]
    lab['cases'].append(dict(id='marked',title='Marked clause',kind='clause',text='katalt kataln lumow',expected='accept',ruleIds=['analysis','order'],tokens=tokens,note='Synthetic.'))
    s['tests']=[dict(id='page',title='Synthetic repetition',ruleIds=['grammar'],paragraphs=[dict(text='katalt kataln lumow',translation='Synthetic test data.',analysis='No language claim.')],caseIds=[['marked']])]
    validate(s);return s


class VariationTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m10'/uuid.uuid4().hex;self.work.mkdir(parents=True);self.snapshot=fixture()
        self.p=ForgeProject.create(self.work/'test.vayforge','Variation test',self.snapshot)

    def test_full_forms_remain_optional_and_every_condition_is_required(self):
        good=dict(register='literary',givenness='established',focus='neutral',role='subject')
        def allowed(context):return {r['surface'] for r in variation.forms(self.snapshot,'noun',{'case':'nom'},context)['forms'] if r['allowed']}
        self.assertEqual(allowed(good),{'kataln','taln'})
        for key,bad in [('register','formal'),('givenness','new'),('focus','contrast'),('role','object')]:
            self.assertEqual(allowed(dict(good,**{key:bad})),{'kataln'})
            missing=dict(good);del missing[key];self.assertEqual(allowed(missing),{'kataln'})
        self.assertEqual(variation.forms(self.snapshot,'noun',{'case':'wrong'},good)['forms'],[])

    def test_clause_context_is_checked_and_token_context_overrides_case(self):
        c=deepcopy(self.snapshot['laboratory']['cases'][-1]);c.update(text='katalt taln lumow',context=dict(register='literary',givenness='established',focus='neutral'))
        c['tokens'][1].update(start=7,end=11);c['tokens'][2].update(start=12,end=17)
        compiled=forge_lab.compile_rules(self.snapshot)
        self.assertEqual(forge_lab.check_case(c,compiled)['actual'],'accept')
        c['tokens'][1]['context']={'focus':'contrast'}
        self.assertEqual(forge_lab.check_case(c,compiled)['actual'],'reject')
        c['tokens'][1]['context']={'role':'object'};self.snapshot['laboratory']['cases']=[c];self.snapshot['tests']=[]
        with self.assertRaisesRegex(ValueError,'CONTEXT_ROLE_MISMATCH'):validate(self.snapshot)

    def test_alternatives_do_not_chain_or_remove_inner_prefix_or_case(self):
        s=deepcopy(self.snapshot);s['laboratory']['rules'][-1]['config']['prefixes']=['kaef'];v=s['variation']['alternations'][0];v.update(fromPrefix='kaef',toPrefix='ef')
        validate(s);forms=variation.forms(s,'noun',{'case':'nom'},dict(register='literary',givenness='established',focus='neutral',role='subject'))['forms']
        self.assertEqual({r['surface'] for r in forms},{'kaeftaln','eftaln'})
        s['variation']['alternations'].append(dict(v,id='cascade',fromPrefix='ef',toPrefix=''))
        with self.assertRaisesRegex(ValueError,'PREFIX_REFERENCE'):validate(s)

    def test_invalid_conditions_and_aggregate_limits_are_rejected(self):
        for change in ['context','prefix','reference','limit','threshold']:
            s=deepcopy(self.snapshot)
            if change=='context':s['variation']['alternations'][0]['when']['register']=['arbitrary']
            elif change=='prefix':s['variation']['alternations'][0]['fromPrefix']='k'
            elif change=='reference':s['variation']['alternations'][0]['grammarId']='absent'
            elif change=='limit':s['variation']['watch']*=33
            else:s['variation']['watch'][0]['minShare']=float('nan')
            with self.assertRaises((ValueError,TypeError),msg=change):validate(s)
        s=deepcopy(self.snapshot);del s['variation'];s['laboratory']['cases'][0]['context']={}
        with self.assertRaisesRegex(ValueError,'CONTEXT_REQUIRES_VARIATION'):validate(s)

    def test_advisory_audit_reports_locations_without_casefolding(self):
        r=variation.audit(self.snapshot,'page');w=r['watched'][0]
        self.assertEqual((r['tokenCount'],w['count'],w['clauseOpenings'],w['longestConsecutiveTokens']),(3,2,1,2));self.assertEqual(r['status'],'Needs review')
        self.assertEqual(w['locations'][1]['sourceStart'],7)
        s=deepcopy(self.snapshot);s['tests'][0].pop('caseIds');s['tests'][0]['paragraphs'][0]['text']='ß ss ß';s['variation']['watch'][0]['text']='ß'
        r=variation.audit(s,'page');self.assertFalse(r['boundToCases']);self.assertEqual(r['watched'][0]['count'],2)
        self.assertEqual(r['repeatedWords'],[dict(text='ß',count=2)])

    def test_comparison_uses_identical_watch_config_and_frozen_versions(self):
        before=self.p.status()['head'];s=self.p.read()['snapshot'];s['variation']['watch'][0]['minCount']=3
        self.p.replace_draft(s,0);after=self.p.commit('Threshold review',1)['head'];r=variation.compare(self.p,before,after,'page')
        self.assertEqual(r['before']['watchSha256'],r['after']['watchSha256']);self.assertEqual(r['changes'][0]['delta'],0)
        self.assertEqual(self.p.read(before)['snapshot'],self.snapshot)
        run=variation.run(self.p,after,'page',self.work/'audit');self.assertEqual(run,self.p.runs()[0])
        with self.assertRaisesRegex(ValueError,'DIRECTORY_EXISTS'):variation.run(self.p,after,'page',self.work/'audit')

    def test_merge_and_restore_preserve_extension_and_envelope(self):
        before=self.p.status()['head'];self.p.branch('other',0,before)
        s=self.p.read()['snapshot'];s['variation']['alternations'][0]['note']='Other review';self.p.replace_draft(s,1);self.p.commit('Review',2);self.p.checkout('main',3)
        plan=forge_merge.preview(self.p,'other');forge_merge.apply(self.p,'other',plan['planId'],'Merged',{},plan['generation'])
        self.assertEqual(self.p.status()['version'],'1.2.0');self.assertEqual(self.p.read()['snapshot']['variation']['alternations'][0]['note'],'Other review')
        self.p.export(self.work/'history.json');p=ForgeProject.restore(self.work/'history.json',self.work/'restored.vayforge')
        self.assertEqual(p.read()['snapshot'],self.p.read()['snapshot']);self.assertEqual(p.status()['version'],'1.2.0')
        self.assertFalse(any(r['regression'] for r in forge_lab.compare(self.p,before,self.p.status()['head'])['cases']))

    def test_api_guards_stale_edits_and_published_contracts(self):
        s=VariationSession(ROOT,source_fonts=False,recovery=False);s.forge=self.p;api=VariationAPI(s)
        try:
            params=dict(project_id=self.p.status()['projectId'],expected_generation=0,variation=self.snapshot['variation'])
            def call(**changes):return api.call('forge.variation.replace',dict(params,**changes),expected_revision=s.revision,document_id=s.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp')
            self.assertFalse(call(project_id='wrong')['ok']);self.assertTrue(call()['ok']);self.assertFalse(call()['ok'])
            self.assertEqual(len(METHODS),133)
            for file in ('variation-capabilities.json','variation-mcp-tools.json'):
                self.assertEqual(json.loads((ROOT/'data'/file).read_text(encoding='utf-8'))['apiVersion'],'0.11.0')
        finally:s.finish()

    def test_release_verifies_variation_evidence_and_never_downgrades(self):
        from tools.m0.common import write_json,file_hash
        version=self.p.status()['head'];suite=forge_lab.run(self.p,version,self.work/'suite');folder=self.work/'page';folder.mkdir()
        for name in ('document.json','proof.png'):(folder/name).write_bytes(b'Synthetic artifact for evidence validation')
        write_json(folder/'language.json',forge_lab.evaluate(self.snapshot));audit=variation.audit(self.snapshot,'page');write_json(folder/'variation.json',audit)
        page=dict(runId=uuid.uuid4().hex,version=version,projectId=self.p.status()['projectId'],testId='page',status='Needs review',createdAt='synthetic',manifestPath=str(folder/'run.json'),document=str(folder/'document.json'),documentSha256=file_hash(folder/'document.json'),proof=str(folder/'proof.png'),proofSha256=file_hash(folder/'proof.png'),languageResults=dict(path=str(folder/'language.json'),sha256=file_hash(folder/'language.json')),variationResults=dict(path=str(folder/'variation.json'),sha256=file_hash(folder/'variation.json')),test=self.snapshot['tests'][0],checks=[dict(name='Human meaning review',status='Needs review')])
        write_json(folder/'run.json',page);self.p.record_run(page)
        args=dict(name='synthetic-experimental',version=version,channel='experimental',notes='Synthetic gate test.',suite_run_id=suite['runId'],workbench_run_id=page['runId'],expected_generation=self.p.status()['generation'])
        write_json(folder/'variation.json',dict(audit,tokenCount=999))
        with self.assertRaisesRegex(ValueError,'VARIATION_EVIDENCE_MISMATCH'):forge_release.create(self.p,**args)
        self.assertEqual(forge_release.list_releases(self.p),[])
        write_json(folder/'variation.json',audit);forge_release.create(self.p,**args);self.assertEqual(self.p.status()['version'],'1.2.0')

    def test_ui_retains_invalid_stale_input_and_lab_preserves_context(self):
        s=VariationSession(ROOT,source_fonts=False,recovery=False);s.forge=self.p;api=VariationAPI(s);w=VariationWindow(s,api)
        try:
            w.show_forge(section='Variation');panel=w.forge_panel.variation;original=s.capture()
            panel.config.setPlainText('{invalid');self.assertFalse(panel.save());w.forge_panel.refresh();self.assertEqual(panel.config.toPlainText(),'{invalid')
            panel.config.setPlainText(json.dumps(self.snapshot['variation']));self.assertTrue(panel.save())
            panel.config.setPlainText(json.dumps(self.snapshot['variation'],indent=3));self.p.replace_draft(self.p.read()['snapshot'],self.p.status()['generation']);self.assertFalse(panel.save());self.assertTrue(panel.dirty)
            panel.dirty=False;w.forge_panel.refresh();lab=w.forge_panel.laboratory;lab.records.setCurrentRow(0);lab.set_text('context','{"register":"formal"}');self.assertTrue(lab.save())
            self.assertEqual(self.p.read()['snapshot']['laboratory']['cases'][0]['context'],{'register':'formal'});self.assertEqual(s.capture(),original)
            panel.audit();self.assertEqual(panel.report['tokenCount'],3)
        finally:
            panel.dirty=False;lab.dirty=False;w.job_timer.stop();w.forge_panel.timer.stop();w.hide();s.window=None;w.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);s.finish()

    def test_headless_mcp_publishes_all_variation_controls(self):
        messages=[dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2024-11-05',capabilities={},clientInfo=dict(name='test',version='1'))),dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=2,method='tools/list')]
        request='\n'.join(json.dumps(m) for m in messages)+'\n'
        p=subprocess.run([sys.executable,'-m','vayrshemon','mcp','--headless','--variation','--no-source-fonts'],input=request,text=True,capture_output=True,cwd=ROOT,timeout=40)
        self.assertEqual(p.returncode,0,p.stderr);reply=json.loads(p.stdout.splitlines()[-1]);rows=reply['result']['tools'];self.assertEqual(len(rows),133);self.assertTrue(any('forge_variation_compare' in r['name'] for r in rows))


if __name__=='__main__':unittest.main()
