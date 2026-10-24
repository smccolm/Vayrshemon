"""Script case pairs, bounded explicit edits, context orders and immutable evidence."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest
import uuid
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication,QEvent,Qt
from PySide6.QtTest import QTest
from tests.test_m10 import fixture as variation_fixture
from vayrshemon.archive_language import base
from vayrshemon.forge import ForgeProject,validate,digest
from vayrshemon import spelling,variation,forge_lab,forge_merge,forge_release
from vayrshemon.spelling_api import SpellingSession,SpellingAPI,METHODS
from vayrshemon.spelling_window import SpellingWindow
from tools.m0.common import write_json,file_hash

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


def fixture():
    s=variation_fixture();s['variation']['formatVersion']='1.1.0'
    s['language']['orthographies']=[dict(base('ortho','Synthetic pairs',None,'',status='draft'),version='1',normalization='none',fontSha256s=['0'*64],symbols=[dict(id='letter.'+str(ord(lo)),name='Synthetic '+str(ord(lo)),kind='letter',status='draft',forms=[dict(form='minima',scalar=ord(lo),transliteration=None),dict(form='maxima',scalar=ord(hi),transliteration=None)]) for lo,hi in [('k','K'),('t','T'),('m','M'),('l','L'),('ß','Þ'),('á','à')]],unresolvedScalars=[])]
    s['spelling']=dict(formatVersion='1.0.0',orthographyId='ortho',grammarId='grammar',formRuleIds=['verb','bare','classified'],terminalCharacters='.!?',openingCharacters='“”"()',initialForm='maxima')
    order=next(r for r in s['laboratory']['rules'] if r['id']=='order');order['config']['alternatives']=[dict(id='topic',pattern=['subject','object','verb'],when=dict(register=['literary'],topic=['subject'],focus=['neutral'],givenness=['established']),note='Synthetic topic construction.')]
    validate(s);return s


class SpellingTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m11'/uuid.uuid4().hex;self.work.mkdir(parents=True);self.snapshot=fixture();self.p=ForgeProject.create(self.work/'test.vayforge','Spelling',self.snapshot)

    def test_pairs_do_not_use_unicode_case_and_wrapped_lines_do_not_capitalize(self):
        s=self.snapshot;r=spelling.inspect_text('“ßá tal;\nmi.” átal! (tal?)',s['spelling'],spelling.pairs(s))
        self.assertEqual(r['text'],'“Þá tal;\nmi.” àtal! (Tal?)');self.assertEqual(len(r['changes']),3)
        again=spelling.inspect_text(r['text'],s['spelling'],spelling.pairs(s));self.assertEqual(again['changes'],[])
        self.assertEqual(spelling.inspect_text('9 tal',s['spelling'],spelling.pairs(s))['unmappedInitials'],[dict(offset=0,scalar='U+0039')])

    def test_all_archived_letter_pairs_have_exact_distinct_maxima(self):
        chart=json.loads((ROOT/'data/orthography/chart-transcription.json').read_text(encoding='utf-8'));mapping=json.loads((ROOT/'data/orthography/thimfora-79.json').read_text(encoding='utf-8'));entries={r['scalar']:r for r in mapping['entries']}
        self.assertEqual(len(chart['letters']),47)
        for ordinal,hi,lo,*_ in chart['letters']:
            self.assertEqual(entries[hi]['symbolId'],entries[lo]['symbolId']);self.assertEqual(entries[hi]['form'],'maxima');self.assertNotEqual(entries[hi]['glyphId'],entries[lo]['glyphId'])

    def test_preview_is_read_only_apply_clones_cases_and_preserves_offsets_and_english(self):
        before=self.p.read();plan=spelling.preview(self.p,'page');self.assertEqual(self.p.read(),before);self.assertEqual(plan['audit']['missingCount'],1)
        result=spelling.apply(self.p,'page',plan['planId'],plan['generation']);s=self.p.read()['snapshot'];self.assertEqual(result['audit']['maximaInitialCount'],1)
        self.assertEqual(s['tests'][0]['paragraphs'][0]['text'],'Katalt kataln lumow');self.assertEqual(s['tests'][0]['paragraphs'][0]['translation'],self.snapshot['tests'][0]['paragraphs'][0]['translation'])
        new=next(c for c in s['laboratory']['cases'] if c['id']==result['addedCaseIds'][0]);old=self.snapshot['laboratory']['cases'][-1]
        self.assertEqual(new['tokens'],old['tokens']);self.assertIn(old,s['laboratory']['cases']);self.assertEqual(forge_lab.evaluate(s)['counts'].get('Fail',0),0)
        with self.assertRaisesRegex(ValueError,'STALE_GENERATION'):spelling.apply(self.p,'page',plan['planId'],plan['generation'])
        now=spelling.preview(self.p,'page')
        with self.assertRaisesRegex(ValueError,'NO_CHANGES'):spelling.apply(self.p,'page',now['planId'],now['generation'])

    def test_missing_maxima_fail_the_explicit_rule_and_internal_maxima_do_not_pass_forms(self):
        plan=spelling.preview(self.p,'page');r=spelling.apply(self.p,'page',plan['planId'],plan['generation']);s=self.p.read()['snapshot'];c=next(c for c in s['laboratory']['cases'] if c['id']==r['addedCaseIds'][0]);compiled=forge_lab.compile_rules(s)
        self.assertEqual(forge_lab.check_case(c,compiled)['actual'],'accept')
        c['text']='katalt kataln lumow';self.assertEqual(forge_lab.check_case(c,compiled)['actual'],'reject')
        c['text']='Katalt Kataln lumow';c['tokens'][1]['context']={'position':'sentence-initial'};self.assertEqual(forge_lab.check_case(c,compiled)['actual'],'reject')
        options=variation.forms(s,'noun',{'case':'nom'},dict(register='literary',givenness='established',focus='neutral',role='subject',position='sentence-initial'))['forms'];self.assertIn('Taln',{r['surface'] for r in options if r['allowed']})

    def test_topic_order_requires_each_condition_but_retains_default_order(self):
        good=dict(register='literary',topic='subject',focus='neutral',givenness='established');c=deepcopy(self.snapshot['laboratory']['cases'][3]);c['tokens'][0]['role']='subject';c['tokens'][1]['role']='object';c['context']=good;compiled=forge_lab.compile_rules(self.snapshot)
        self.assertEqual(forge_lab.check_case(c,compiled)['actual'],'accept')
        for key in good:
            c['context']=dict(good);del c['context'][key];self.assertEqual(forge_lab.check_case(c,compiled)['actual'],'reject')
        for key,val in [('register','formal'),('topic','none'),('focus','contrast'),('givenness','new')]:
            c['context']=dict(good,**{key:val});self.assertEqual(forge_lab.check_case(c,compiled)['actual'],'reject')
        self.assertTrue(variation.orders(self.snapshot,'order',good)['patterns'][-1]['allowed'])
        c=deepcopy(self.snapshot['laboratory']['cases'][3]);c['context']=good;self.assertEqual(forge_lab.check_case(c,compiled)['actual'],'accept')

    def test_mapping_ambiguities_and_incompatible_versions_are_rejected(self):
        for kind in ('duplicate','missing','rule','context-version'):
            s=deepcopy(self.snapshot)
            if kind=='duplicate':s['language']['orthographies'][0]['symbols'][1]['forms'][1]['scalar']=ord('K')
            elif kind=='missing':s['language']['orthographies'][0]['symbols'][0]['forms'].pop()
            elif kind=='rule':s['spelling']['formRuleIds']=['order']
            else:s['variation']['formatVersion']='1.0.0'
            with self.assertRaises(Exception,msg=kind):validate(s)

    def test_capitalization_does_not_hide_repetition_and_old_versions_are_unchanged(self):
        before=self.p.status()['head'];plan=spelling.preview(self.p,'page');spelling.apply(self.p,'page',plan['planId'],plan['generation']);after=self.p.commit('Maxima',self.p.status()['generation'])['head']
        r=variation.compare(self.p,before,after,'page');self.assertEqual(r['changes'][0]['delta'],0);self.assertEqual(r['after']['watched'][0]['count'],2);self.assertEqual(r['before']['letterIdentitySha256'],r['after']['letterIdentitySha256'])
        self.assertEqual(self.p.read(before)['snapshot'],self.snapshot);self.assertFalse(any(c['regression'] for c in forge_lab.compare(self.p,before,after)['cases']))
        self.p.export(self.work/'history.json');restored=ForgeProject.restore(self.work/'history.json',self.work/'restored.vayforge');self.assertEqual(restored.status()['version'],'1.3.0');self.assertEqual(restored.read()['snapshot'],self.p.read()['snapshot'])

    def test_apply_rejects_modified_plan_and_unbound_page_without_mutation(self):
        before=self.p.read()
        with self.assertRaisesRegex(ValueError,'STALE_PLAN'):spelling.apply(self.p,'page','wrong',0)
        self.assertEqual(self.p.read(),before)
        s=deepcopy(self.snapshot);s['tests'][0].pop('caseIds');self.p.replace_draft(s,0);plan=spelling.preview(self.p,'page');before=self.p.read()
        with self.assertRaisesRegex(ValueError,'BOUND_CASES_REQUIRED'):spelling.apply(self.p,'page',plan['planId'],plan['generation'])
        self.assertEqual(self.p.read(),before)

    def test_ui_preview_apply_and_failed_policy_save_retain_text(self):
        s=SpellingSession(ROOT,source_fonts=False,recovery=False);s.forge=self.p;api=SpellingAPI(s);w=SpellingWindow(s,api);panel=w.forge_panel.spelling;original=s.capture()
        try:
            w.show_forge(section='Orthography',spelling_test='page',spelling_preview=True);self.assertEqual(panel.table.rowCount(),1)
            QTest.mouseClick(panel.apply_button,Qt.MouseButton.LeftButton);self.assertEqual(panel.report['maximaInitialCount'],1);self.assertEqual(s.capture(),original)
            panel.config.setPlainText('{bad');self.assertFalse(panel.save());w.forge_panel.refresh();self.assertEqual(panel.config.toPlainText(),'{bad');self.assertFalse(w.forge_panel.flush())
        finally:panel.dirty=False;w.job_timer.stop();w.forge_panel.timer.stop();w.hide();s.window=None;w.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);s.finish()

    def test_release_requires_matching_spelling_evidence(self):
        plan=spelling.preview(self.p,'page');spelling.apply(self.p,'page',plan['planId'],plan['generation']);version=self.p.commit('Maxima',self.p.status()['generation'])['head'];snapshot=self.p.read()['snapshot'];suite=forge_lab.run(self.p,version,self.work/'suite');folder=self.work/'page';folder.mkdir()
        for name in ('document.json','proof.png'):(folder/name).write_bytes(b'Synthetic evidence artifact')
        page=dict(runId=uuid.uuid4().hex,version=version,projectId=self.p.status()['projectId'],testId='page',status='Needs review',createdAt='synthetic',manifestPath=str(folder/'run.json'),document=str(folder/'document.json'),documentSha256=file_hash(folder/'document.json'),proof=str(folder/'proof.png'),proofSha256=file_hash(folder/'proof.png'),test=snapshot['tests'][0],checks=[dict(name='Human meaning',status='Needs review')])
        for key,report in [('language',forge_lab.evaluate(snapshot)),('variation',variation.audit(snapshot,'page')),('spelling',spelling.audit(snapshot,'page'))]:
            write_json(folder/(key+'.json'),report);page[key+'Results']=dict(path=str(folder/(key+'.json')),sha256=file_hash(folder/(key+'.json')))
        write_json(folder/'run.json',page);self.p.record_run(page);args=dict(name='synthetic',version=version,channel='experimental',notes='Structural test',suite_run_id=suite['runId'],workbench_run_id=page['runId'],expected_generation=self.p.status()['generation'])
        (folder/'spelling.json').write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'SPELLING_EVIDENCE_MISMATCH'):forge_release.create(self.p,**args)
        write_json(folder/'spelling.json',spelling.audit(snapshot,'page'));forge_release.create(self.p,**args);self.assertEqual(self.p.status()['version'],'1.3.0')

    def test_mcp_contract_and_guarded_api(self):
        self.assertEqual(len(METHODS),140);self.assertEqual(json.loads((ROOT/'data/spelling-capabilities.json').read_text(encoding='utf-8'))['apiVersion'],'0.12.0')
        messages=[dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2024-11-05',capabilities={},clientInfo=dict(name='test',version='1'))),dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=2,method='tools/list')]
        p=subprocess.run([sys.executable,'-m','vayrshemon','mcp','--headless','--spelling','--no-source-fonts'],input='\n'.join(json.dumps(m) for m in messages)+'\n',capture_output=True,text=True,cwd=ROOT,timeout=40)
        self.assertEqual(p.returncode,0,p.stderr);r=next(json.loads(line) for line in p.stdout.splitlines() if json.loads(line).get('id')==2);self.assertEqual(len(r['result']['tools']),140)


if __name__=='__main__':unittest.main()
