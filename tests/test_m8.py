"""Executable positive/negative rules, immutable comparisons and real test editing."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid
from unittest.mock import patch
if os.name!='nt': os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtTest import QTest
from vayrshemon.forge import ForgeProject,empty_snapshot,digest,validate
from vayrshemon.forge_lab import evaluate,compare,compile_rules,empty_lab
from vayrshemon.archive_language import base
from vayrshemon.laboratory_api import LaboratoryAPI,LaboratorySession
from vayrshemon.laboratory_window import LaboratoryWindow
ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


def fixture():
    s=empty_snapshot();d=s['language']
    d['grammar']=[dict(base('grammar','Synthetic construction',None,''),topic='construction',statement='Synthetic root + tense; object subject verb.',morphologyIds=[],exampleIds=[],alternatives=[])]
    for key,form in [('root','lum'),('noun','tal'),('person','mi')]:
        d['lexicon'].append(dict(base(key,key,None,''),headword=form,orthographyId=None,pronunciation='',ipa='',partOfSpeech='test',senses=[dict(id=key+'.sense',definition=key,status='draft',citations=[])],variants=[],etymology='',exampleIds=[],audioLinks=[]))
    s['laboratory']=empty_lab();lab=s['laboratory']
    lab['rules']=[dict(id='verb',title='Finite verb',grammarId='grammar',kind='forms',config=dict(entryIds=['root'],prefixes=[''],slots=[dict(feature='tense',values={'present':'ow','future':'at'})])),
                  dict(id='bare',title='Bare words',grammarId='grammar',kind='forms',config=dict(entryIds=['noun','person'],prefixes=[''],slots=[])),
                  dict(id='analysis',title='Exhaustive token analysis',grammarId='grammar',kind='analysis',config=dict(formRuleIds=['verb','bare'])),
                  dict(id='order',title='Object Subject Verb',grammarId='grammar',kind='order',config=dict(patterns=[['object','subject','verb']])),
                  dict(id='meaning',title='Meaning',grammarId='grammar',kind='review',config=dict(reason='An editor must assess meaning.'))]
    def case(key,text,expect,rules,kind='word',tokens=None): return dict(id=key,title=key,kind=kind,text=text,expected=expect,ruleIds=rules,tokens=tokens or [],note='Synthetic data, not Vayrshemon.')
    tokens=[dict(start=0,end=3,role='object',entryId='noun',features={}),dict(start=4,end=6,role='subject',entryId='person',features={}),dict(start=7,end=12,role='verb',entryId='root',features={'tense':'present'})]
    lab['cases']=[case('present','lumow','accept',['verb']),case('future','lumat','accept',['verb']),case('wrong-suffix','lumzz','reject',['verb']),case('clause','tal mi lumow','accept',['analysis','order'],'clause',tokens),case('meaning-review','tal mi lumow','review',['meaning'],'review')]
    validate(s);return s


class LaboratoryTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m8'/uuid.uuid4().hex;self.work.mkdir(parents=True);self.snapshot=fixture();self.p=ForgeProject.create(self.work/'language.vayforge','Language tests',self.snapshot)

    def test_negative_cases_are_executed_and_review_is_not_pass(self):
        report=evaluate(self.snapshot);self.assertEqual(report['counts'],{'Pass':4,'Needs review':1})
        bad=deepcopy(self.snapshot);bad['laboratory']['cases'][2]['text']='lumow'
        self.assertEqual(evaluate(bad)['results'][2]['status'],'Fail')
        coverage={r['ruleId']:r for r in report['coverage']};self.assertTrue(coverage['verb']['bidirectional']);self.assertFalse(coverage['meaning']['covered'])
        self.assertEqual(evaluate(empty_snapshot())['status'],'Unsupported')

    def test_word_order_features_and_unconsumed_text_cannot_silently_pass(self):
        for change in ('roles','feature','tail','no-tokens'):
            s=deepcopy(self.snapshot);c=s['laboratory']['cases'][3]
            if change=='roles': c['tokens'][0]['role']='subject'
            elif change=='feature': c['tokens'][2]['features']['tense']='future'
            elif change=='tail': c['text']+=' mystery'
            else: c['tokens']=[]
            r=evaluate(s)['results'][3];self.assertEqual(r['actual'],'reject',change);self.assertEqual(r['status'],'Fail',change)
        s=deepcopy(self.snapshot);s['tests']=[dict(id='bound',title='Bound prose',ruleIds=['grammar'],paragraphs=[dict(text='tal mi lumow',translation='Synthetic English.',analysis='Synthetic case binding.')],caseIds=[['clause']])]
        validate(s)
        s['tests'][0]['paragraphs'][0]['text']='tal mi lumat'
        with self.assertRaisesRegex(ValueError,'PAGE_CASE_TEXT_MISMATCH'): validate(s)

    def test_compiler_is_bounded_and_validates_references_and_offsets(self):
        for change in ('reference','span','kind','limit'):
            s=deepcopy(self.snapshot)
            if change=='reference': s['laboratory']['rules'][0]['config']['entryIds']=['missing']
            elif change=='span': s['laboratory']['cases'][3]['tokens'][1]['start']=1
            elif change=='kind': s['laboratory']['rules'][0]['kind']='python'
            else: s['laboratory']['rules'][0]['config']['slots']=[dict(feature=str(i),values={str(n):str(n) for n in range(32)}) for i in range(6)]
            with self.assertRaisesRegex(ValueError,'LAB_'): validate(s)

    def test_inventory_uses_scalar_identity_without_unicode_case_folding(self):
        s=deepcopy(self.snapshot);s['language']['orthographies']=[dict(base('ortho','Synthetic slots',None,''),version='1',normalization='none',fontSha256s=['0'*64],symbols=[dict(id='letter.1',name='Synthetic',kind='letter',status='draft',forms=[dict(form='minima',scalar=223,transliteration='x')])],unresolvedScalars=[])]
        s['laboratory']['rules']=[dict(id='inventory',title='Slots',grammarId='grammar',kind='inventory',config=dict(orthographyId='ortho',extraCharacters=' '))]
        template=deepcopy(s['laboratory']['cases'][0]);template.update(ruleIds=['inventory'],text='ß',expected='accept');s['laboratory']['cases']=[template];validate(s)
        self.assertEqual(evaluate(s)['results'][0]['status'],'Pass')
        template['text']='ss';self.assertEqual(evaluate(s)['results'][0]['actual'],'reject')
        template['text']='🙂';self.assertEqual(evaluate(s)['results'][0]['checks'][0]['detail']['unknownScalars'],[dict(offset=0,scalar='U+1F642')])

    def test_role_constraints_reject_valid_word_in_wrong_role(self):
        s=deepcopy(self.snapshot);rule=next(r for r in s['laboratory']['rules'] if r['id']=='order')
        rule['config'].update(roleEntries={'object':['root']},roleFeatures={'verb':[{'tense':'future'}]});validate(s)
        row=evaluate(s)['results'][3];self.assertEqual(row['actual'],'reject');self.assertEqual(row['checks'][-1]['detail']['roleConstraintViolations'],[0,7])

    def test_case_pinned_comparison_detects_rule_regression_despite_changed_tests(self):
        before=self.p.status()['head'];s=deepcopy(self.snapshot);s['laboratory']['rules'][0]['config']['slots'][0]['values']['future']='zz';s['laboratory']['cases'][1]['text']='lumzz'
        self.p.replace_draft(s,0);after=self.p.commit('Change future suffix',1)['head']
        report=compare(self.p,before,after);self.assertEqual(report['caseVersion'],before)
        future=next(r for r in report['cases'] if r['caseId']=='future');self.assertTrue(future['regression'])
        self.assertEqual(report['before']['suiteSha256'],report['after']['suiteSha256'])
        self.assertEqual(self.p.read(before)['snapshot'],self.snapshot)

    def test_transactional_lab_edit_removal_and_portable_history(self):
        rule=deepcopy(self.snapshot['laboratory']['rules'][0]);rule['title']='Edited'
        self.p.lab_edit('rules',0,record=rule)
        with self.assertRaisesRegex(ValueError,'STALE_FORGE'): self.p.lab_edit('rules',0,record=rule)
        with self.assertRaisesRegex(ValueError,'LAB_'): self.p.lab_edit('rules',1,record_id='verb')
        self.assertEqual(self.p.status()['generation'],1)
        head=self.p.commit('v2',1)['head'];self.p.export(self.work/'bundle.json');restored=ForgeProject.restore(self.work/'bundle.json',self.work/'restored.vayforge')
        self.assertEqual(restored.read(head)['snapshot'],self.p.read(head)['snapshot'])
        self.assertEqual(self.p.diff(self.p.history()[-1]['id'],head)['collections']['laboratory.rules']['changed'],['verb'])

    def session(self):
        shutil.copytree(ROOT/'schemas',self.work/'schemas');(self.work/'data').mkdir();shutil.copy2(ROOT/'data/fonts.json',self.work/'data/fonts.json')
        s=LaboratorySession(self.work,source_fonts=False,recovery=False);s.forge=self.p;return s,LaboratoryAPI(s)

    def test_guarded_api_runs_persist_hashes_without_mutating_book(self):
        s,api=self.session();original=s.capture()
        try:
            version=self.p.status()['head'];params=dict(version=version,directory=str(self.work/'run'))
            result=api.call('forge.lab.run',params,expected_revision=s.revision,idempotency_key='run');self.assertTrue(result['ok'],result)
            self.assertEqual(api.call('forge.lab.run',params,expected_revision=s.revision,idempotency_key='run'),result)
            self.assertEqual(len(self.p.runs()),1);self.assertEqual(result['result']['snapshotSha256'],digest(self.snapshot));self.assertEqual(s.capture(),original)
            bad=api.call('forge.lab.remove',dict(collection='cases',record_id='present',project_id='wrong',expected_generation=0),expected_revision=s.revision,idempotency_key='wrong');self.assertFalse(bad['ok']);self.assertEqual(self.p.status()['generation'],0)
        finally: s.finish()

    def test_real_qt_case_edit_history_and_failed_validation_retains_text(self):
        s,api=self.session();w=LaboratoryWindow(s,api);lab=w.forge_panel.laboratory
        try:
            before=self.p.status()['head'];w.show_forge(section='Laboratory',record_id='present');lab.fields['text'].setPlainText('lumat');lab.changed();self.assertTrue(lab.save())
            self.assertEqual(self.p.read()['snapshot']['laboratory']['cases'][0]['text'],'lumat')
            self.assertEqual(self.p.read(before)['snapshot']['laboratory']['cases'][0]['text'],'lumow')
            lab.fields['tokens'].setPlainText('not json');lab.changed();self.assertFalse(lab.save());self.assertTrue(lab.dirty);self.assertEqual(lab.fields['tokens'].toPlainText(),'not json')
            lab.fields['tokens'].setPlainText('[]');self.assertTrue(lab.save());w.show_forge(section='Laboratory',version=before,record_id='present');self.assertTrue(lab.fields['text'].isReadOnly());self.assertEqual(lab.fields['text'].toPlainText(),'lumow')
            w.show_forge(section='Laboratory',draft=True);self.assertFalse(lab.fields['text'].isReadOnly())
            # A second writer advances the generation while the form is being
            # edited. The failed save retains text; explicit reload recovers it.
            lab.fields['text'].setPlainText('unsaved conflict');lab.changed()
            status=self.p.status();self.p.put('wiki',dict(id='other',title='Other editor',body='Concurrent write',ruleIds=[]),status['generation'])
            self.assertFalse(lab.save());self.assertEqual(lab.fields['text'].toPlainText(),'unsaved conflict')
            with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes): w.forge_panel.reload()
            self.assertFalse(lab.dirty);self.assertEqual(lab.fields['text'].toPlainText(),'lumat')
            from vayrshemon.forge_lab import run
            report=run(self.p,before,self.work/'ui-suite');w.show_forge(section='Laboratory',run_id=report['runId'])
            self.assertEqual(lab.results.rowCount(),5);self.assertIn('Needs review',lab.notice.text())
            w.show_forge(section='Laboratory',lab_view='Coverage');self.assertIs(lab.views.currentWidget(),lab.coverage)
            w.show_forge(section='Laboratory',record_id='clause',lab_view='Results');self.assertEqual(lab.results.currentRow(),3)
            w.show_forge(section='Laboratory',compare_before=before,compare_after=before);self.assertIn('unchanged',lab.comparison.toPlainText())
            with self.assertRaisesRegex(ValueError,'VERSIONS_REQUIRED'): w.show_forge(compare_before=before)
        finally:
            w.hide();w.job_timer.stop();w.deleteLater();s.window=None;s.finish();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);APP.processEvents()

    def test_mcp_headless_advertises_executable_tests(self):
        messages=[dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2024-11-05',capabilities={},clientInfo=dict(name='test',version='1'))),dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=2,method='tools/list')]
        process=subprocess.run([sys.executable,'-m','vayrshemon','mcp','--headless','--laboratory','--no-source-fonts'],input='\n'.join(json.dumps(m) for m in messages)+'\n',text=True,capture_output=True,cwd=ROOT,timeout=30)
        self.assertEqual(process.returncode,0,process.stderr)
        replies=[json.loads(line) for line in process.stdout.splitlines()];tools=next(r['result']['tools'] for r in replies if r.get('id')==2)
        self.assertTrue(any('forge_lab_compare' in t['name'] for t in tools));self.assertEqual(len(tools),121)

    @unittest.skipUnless((ROOT/'.local/baselines/visual.workbench.2026-10-23/approved.vay.json').exists(),'Private approved presentation absent')
    def test_bilingual_runner_preserves_soft_verse_lines_and_protected_presentation(self):
        from vayrshemon.forge_runner import run
        from tools.m0.common import load_json
        s=deepcopy(self.snapshot);s['tests']=[dict(id='verse',title='Verse',ruleIds=['grammar'],paragraphs=[dict(text='a\nb',translation='First line\nSecond line',analysis='Synthetic structural text.')])]
        self.p.replace_draft(s,0);head=self.p.commit('Verse fixture',1)['head']
        result=run(ROOT,self.p,head,'verse',self.work/'verse',language_report=evaluate(s))
        self.assertNotIn(result['status'],('Error','Fail'),result)
        document=load_json(result['document']);frames=document['state']['pages'][0]['frames']
        run=frames[1]['content']['document']['stories'][0]['blocks'][0]['runs'][0]
        self.assertIn('\u2028',run['text']);self.assertEqual(len(frames[1]['content']['paragraphs']),1)
        self.assertEqual(result['checks'][0]['status'],'Pass');self.assertEqual(result['checks'][2]['count'],0)
