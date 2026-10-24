"""Exact font readings, protected copies and explicit discourse continuity."""
from copy import deepcopy
import json,subprocess,sys,unittest,uuid
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from PySide6.QtCore import QCoreApplication,QEvent
from tests.test_m11 import fixture as maxima_fixture
from tools.m0.synthetic import make_font
from tools.parallel_translation_fixture import compose
from tools.m0.common import write_json,file_hash
from vayrshemon import reading,forge_lab,spelling,forge_release
from vayrshemon.forge import ForgeProject,validate
from vayrshemon.reading_api import ReadingSession,ReadingAPI,METHODS
from vayrshemon.reading_window import ReadingWindow

ROOT=Path(__file__).resolve().parents[1];APP=QApplication.instance() or QApplication([])


def fixture():
    s=maxima_fixture();orth=s['language']['orthographies'][0];orth['id']='thimfora-79';orth['fontSha256s']=[reading.SCRIPT_SHA];s['spelling']['orthographyId']=orth['id'];s['reading']=reading.policy();s['variation']['formatVersion']='1.2.0'
    for r in s['laboratory']['rules']:
        if r['kind']=='inventory':r['config']['orthographyId']=orth['id']
    first=deepcopy(next(c for c in s['laboratory']['cases'] if c['id']==s['tests'][0]['caseIds'][0][0]));first['id']='continuity.first'
    second=deepcopy(first);second.update(id='continuity.second',context=dict(register='literary',topic='subject',givenness='established',focus='neutral'),antecedent=dict(caseId=first['id'],entryId=next(t['entryId'] for t in first['tokens'] if t['role']=='subject')))
    parts=[];tokens=[];offset=0
    for t in first['tokens']:
        if t['role']=='subject':continue
        word=first['text'][t['start']:t['end']];t=deepcopy(t);t.update(start=offset,end=offset+len(word));offset+=len(word)+1;tokens.append(t);parts.append(word)
    first['text']+='.';second.update(text=' '.join(parts)+'.',tokens=tokens,ruleIds=[r for r in first['ruleIds'] if r!='order']+['continuity.order','continuity'])
    when=dict(register=['literary'],topic=['subject'],givenness=['established'],focus=['neutral'])
    s['laboratory']['rules']+=[dict(id='continuity.order',title='Synthetic elided order',grammarId='grammar',kind='order',config=dict(patterns=[['subject','verb']],alternatives=[dict(id='implicit',pattern=[t['role'] for t in tokens],when=when,note='Synthetic continuation')])) ,dict(id='continuity',title='Synthetic subject continuity',grammarId='grammar',kind='continuity',config=dict(omittedRole='subject',when=when))]
    s['laboratory']['cases'] += [first,second];s['tests'].append(dict(id='continuity',title='Synthetic discourse fixture',ruleIds=['grammar'],caseIds=[[first['id'],second['id']]],paragraphs=[dict(text=first['text']+' '+second['text'],translation='Structural test data, not invented language.',analysis='Explicit synthetic participant identity.')]))
    validate(s);return s


class ReadingTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m12'/uuid.uuid4().hex;self.work.mkdir(parents=True);self.snapshot=fixture();self.p=ForgeProject.create(self.work/'test.vayforge','Reading',self.snapshot)

    def test_modes_preserve_exact_slots_case_and_english(self):
        before=self.p.read();s=self.snapshot;s['tests'][0]['paragraphs'][0]['text']='Þá Kß. àl?';s['tests'][0].pop('caseIds')
        for mode in ('transliteration','literal'):
            r=reading.inspect(s,'page',mode);self.assertEqual(r['paragraphs'][0]['right'],'Þá Kß. àl?');self.assertTrue(r['exactSlotsPreserved']);self.assertEqual(r['paragraphs'][0]['maxima'],3)
        self.assertEqual(reading.inspect(s,'page','translation')['paragraphs'][0]['right'],s['tests'][0]['paragraphs'][0]['translation']);self.assertEqual(self.p.read(),before)

    def test_unsupported_profile_and_missing_orthography_fail(self):
        for field,value in [('transliterationFontSha256','0'*64),('normalization','NFC'),('orthographyId','missing')]:
            s=deepcopy(self.snapshot);s['reading'][field]=value
            with self.assertRaises(ValueError):validate(s)
        with self.assertRaisesRegex(ValueError,'MODE_INVALID'):reading.inspect(self.snapshot,'page','guess')

    def test_continuity_requires_context_reference_and_same_participant(self):
        compiled=forge_lab.compile_rules(self.snapshot);c=deepcopy(self.snapshot['laboratory']['cases'][-1]);self.assertEqual(forge_lab.check_case(c,compiled)['actual'],'accept')
        for key in c['context']:
            bad=deepcopy(c);bad['context'].pop(key);self.assertEqual(forge_lab.check_case(bad,compiled)['actual'],'reject')
        bad=deepcopy(c);bad.pop('antecedent');self.assertEqual(forge_lab.check_case(bad,compiled)['actual'],'reject')
        bad=deepcopy(c);bad['antecedent']['entryId']='verb';self.assertEqual(forge_lab.check_case(bad,compiled)['actual'],'reject')
        bad=deepcopy(c);bad['tokens'].append(dict(start=len(c['text']),end=len(c['text'])+1,role='subject',entryId='noun',features={}));self.assertEqual(forge_lab.check_case(bad,compiled)['actual'],'reject')

    def test_invalid_antecedent_clause_does_not_license_ellipsis(self):
        compiled=forge_lab.compile_rules(self.snapshot);c=self.snapshot['laboratory']['cases'][-1]
        compiled['continuity']['antecedents']['continuity.first']['text']='? bogus .'
        self.assertEqual(forge_lab.check_case(c,compiled)['actual'],'reject')

    def test_bound_pages_reject_nonadjacent_or_cross_paragraph_antecedents(self):
        s=deepcopy(self.snapshot);p=s['tests'][-1];p['caseIds'][0].insert(1,p['caseIds'][0][0]);p['paragraphs'][0]['text']=s['laboratory']['cases'][-2]['text']+' '+p['paragraphs'][0]['text']
        validate(s) # Same explicitly repeated predecessor is still immediate.
        p['caseIds'][0]=p['caseIds'][0][2:];p['paragraphs'][0]['text']=s['laboratory']['cases'][-1]['text']
        with self.assertRaisesRegex(ValueError,'ANTECEDENT_NOT_ADJACENT'):validate(s)

    def test_maxima_apply_remaps_bound_antecedents_and_retains_old_cases(self):
        plan=spelling.preview(self.p,'continuity');result=spelling.apply(self.p,'continuity',plan['planId'],plan['generation']);s=self.p.read()['snapshot'];ids=s['tests'][-1]['caseIds'][0];second=next(c for c in s['laboratory']['cases'] if c['id']==ids[1]);self.assertEqual(second['antecedent']['caseId'],ids[0]);self.assertIn(self.snapshot['laboratory']['cases'][-1],s['laboratory']['cases']);self.assertEqual(result['audit']['missingCount'],0)

    def test_history_preserves_reading_profile_and_old_frozen_cases(self):
        self.assertEqual(self.p.status()['version'],'1.4.0');self.p.export(self.work/'history.json');q=ForgeProject.restore(self.work/'history.json',self.work/'restored.vayforge');self.assertEqual(q.read()['snapshot'],self.snapshot);self.assertFalse(forge_lab.evaluate(self.snapshot)['counts'].get('Fail'))

    def test_public_copy_is_independent_preserves_styles_and_reopens(self):
        s=ReadingSession(ROOT,source_fonts=False,recovery=False);api=ReadingAPI(s);make_font(self.work/'script.ttf');make_font(self.work/'roman.ttf',advance=610)
        def call(method,**params):
            r=api.call(method,params,expected_revision=s.revision,idempotency_key=uuid.uuid4().hex,origin='fixture');self.assertTrue(r['ok'],r);return r['result']
        try:
            f=call('fonts.load',path=str(self.work/'script.ttf'))['fontId'];roman=s.fonts.register(self.work/'roman.ttf')
            compose(ROOT,call,[dict(original=[dict(text='AA AA AA',font='synthetic')],translation='A source translation.'),dict(original=[dict(text='AA AA',font='synthetic')],translation='A retained second paragraph.')],{'synthetic':f})
            original=s.capture()
            with patch.object(reading,'SCRIPT_SHA',s.fonts.faces[f].sha256),patch.object(reading,'font',return_value=roman):r=reading.copy(s,'transliteration',self.work/'copy')
            self.assertEqual(s.capture(),original);self.assertTrue(r['sourceUnchanged']);self.assertFalse(QImage(r['proof']).isNull());self.assertEqual(r['missingGlyphs'],0)
            s.open(r['document']);state=s.capture();left,right=reading.pairs(state);self.assertEqual(reading.text_blocks(left),reading.text_blocks(right));self.assertTrue(reading.presentation_matches(state,original,'transliteration'));self.assertEqual(state['recipe'],original['recipe'])
        finally:s.finish()

    def test_sidebearing_exception_does_not_hide_real_overflow(self):
        g=dict(sourceFrameId='right',fontId='font:'+reading.ROMAN_SHA+':0',glyphId=112,sourceUtf16=[0,1],inkBounds=[9.9375,15,6,8]);layout=dict(frames=[dict(frameId='left',rect=[0,10,8,100],overflow=False,layout=dict(lines=[])),dict(frameId='right',rect=[10,10,20,100],overflow=True,layout=dict(lines=[dict(advanceBounds=[10,15,10,12])]))],glyphs=[g],truncated=False)
        self.assertAlmostEqual(reading.sidebearing_review(layout,'transliteration')['glyphs'][0]['leftOverhangPoints'],.046875)
        g['inkBounds'][0]=9.5;self.assertIsNone(reading.sidebearing_review(layout,'transliteration'));g['inkBounds']=[9.9375,15,30,8];self.assertIsNone(reading.sidebearing_review(layout,'transliteration'));self.assertIsNone(reading.sidebearing_review(layout,'translation'))

    def test_ui_modes_and_guarded_profile_enable(self):
        s=ReadingSession(ROOT,source_fonts=False,recovery=False);s.forge=self.p;api=ReadingAPI(s);w=ReadingWindow(s,api)
        try:
            w.show_forge(section='Reading',reading_test='page',reading_mode='literal');self.assertEqual(w.forge_panel.reading.mode.currentData(),'literal');self.assertEqual(w.reading_mode.currentData(),'transliteration')
            make_font(self.work/'preview.ttf');face=s.fonts.register(self.work/'preview.ttf')
            with patch.object(s.fonts,'resolve',return_value=face),patch.object(reading,'font',return_value=face):w.show_forge(section='Reading',reading_test='page',reading_preview=True)
            APP.processEvents()
            for edit in (w.forge_panel.reading.left,w.forge_panel.reading.right):self.assertEqual(edit.font().family(),face.family);self.assertEqual(edit.document().defaultFont().family(),face.family)
            r=api.call('forge.reading.enable',dict(project_id='wrong',expected_generation=0),expected_revision=s.revision,origin='desktop');self.assertFalse(r['ok']);self.assertEqual(self.p.status()['generation'],0)
            r=api.call('forge.reading.enable',dict(project_id=self.p.status()['projectId'],expected_generation=0),expected_revision=s.revision,origin='desktop');self.assertTrue(r['ok'],r)
        finally:w.job_timer.stop();w.forge_panel.timer.stop();w.hide();s.window=None;w.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);s.finish()

    def test_release_requires_matching_reading_evidence(self):
        version=self.p.status()['head'];suite=forge_lab.run(self.p,version,self.work/'suite');folder=self.work/'page';folder.mkdir()
        for name in ('document.json','proof.png'):(folder/name).write_bytes(b'Synthetic evidence')
        page=dict(runId=uuid.uuid4().hex,version=version,projectId=self.p.status()['projectId'],testId='page',status='Needs review',createdAt='synthetic',manifestPath=str(folder/'run.json'),document=str(folder/'document.json'),documentSha256=file_hash(folder/'document.json'),proof=str(folder/'proof.png'),proofSha256=file_hash(folder/'proof.png'),test=self.snapshot['tests'][0],checks=[dict(name='Review',status='Needs review')])
        from vayrshemon.variation import audit
        for name,r in [('language',forge_lab.evaluate(self.snapshot)),('variation',audit(self.snapshot,'page')),('spelling',spelling.audit(self.snapshot,'page')),('reading',reading.inspect(self.snapshot,'page'))]:
            write_json(folder/(name+'.json'),r);page[name+'Results']=dict(path=str(folder/(name+'.json')),sha256=file_hash(folder/(name+'.json')))
        page['readingResults']['mode']='transliteration';write_json(folder/'run.json',page);self.p.record_run(page);args=dict(name='synthetic',version=version,channel='experimental',notes='Synthetic scope',suite_run_id=suite['runId'],workbench_run_id=page['runId'],expected_generation=self.p.status()['generation'])
        (folder/'reading.json').write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'READING_EVIDENCE_MISMATCH'):forge_release.create(self.p,**args)

    def test_headless_mcp_and_published_contracts(self):
        self.assertEqual(len(METHODS),144);self.assertEqual(json.loads((ROOT/'data/reading-capabilities.json').read_text(encoding='utf-8'))['apiVersion'],'0.13.0')
        msgs=[dict(jsonrpc='2.0',id=1,method='initialize',params={}),dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=2,method='tools/list')]
        p=subprocess.run([sys.executable,'-m','vayrshemon','mcp','--headless','--reading','--no-source-fonts'],input=''.join(json.dumps(m)+'\n' for m in msgs),capture_output=True,text=True,cwd=ROOT,timeout=40);self.assertEqual(p.returncode,0,p.stderr);r=json.loads(p.stdout.splitlines()[-1]);self.assertEqual(len(r['result']['tools']),144)


if __name__=='__main__':unittest.main()
