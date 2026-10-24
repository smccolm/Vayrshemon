"""Construction gloss fidelity, immutable labels, guards and public controls."""
from copy import deepcopy
from pathlib import Path
import json,subprocess,sys,unittest,uuid
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication,QEvent
from tests.test_m12 import fixture as reading_fixture
from tools.m0.common import load_json
from vayrshemon import gloss
from vayrshemon.forge import ForgeProject,digest
from vayrshemon.gloss_api import GlossSession,GlossAPI,METHODS
from vayrshemon.gloss_window import GlossWindow

ROOT=Path(__file__).resolve().parents[1];APP=QApplication.instance() or QApplication([])


def fixture():
    s=reading_fixture()
    # Use explicit descriptive feature names rather than this older synthetic
    # fixture's local acc/nom shorthand. No production-language inference.
    for r in s['laboratory']['rules']:
        if r['kind']=='forms':
            for slot in r['config']['slots']:
                if slot['feature']=='case':slot['values']={dict(acc='accusative',nom='nominative').get(k,k):v for k,v in slot['values'].items()}
    for c in s['laboratory']['cases']:
        for t in c['tokens']:
            if 'case' in t['features']:t['features']['case']=dict(acc='accusative',nom='nominative').get(t['features']['case'],t['features']['case'])
    p=gloss.prepare(s,'page');s['research'][gloss.KEY]=p;return s


class GlossTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m13'/uuid.uuid4().hex;self.work.mkdir(parents=True);self.snapshot=fixture();self.project=ForgeProject.create(self.work/'test.vayforge','Gloss',self.snapshot)

    def test_source_order_offsets_case_and_grammar_survive(self):
        s=self.snapshot;before=deepcopy(s);r=gloss.inspect(s,'page');self.assertEqual(s,before)
        p=r['paragraphs'][0];tokens=p['clauses'][0]['tokens'];c=next(c for c in s['laboratory']['cases'] if c['id']==p['clauses'][0]['caseId'])
        self.assertEqual([t['surface'] for t in tokens],[c['text'][t['start']:t['end']] for t in c['tokens']])
        self.assertEqual([t['entryId'] for t in tokens],[t['entryId'] for t in c['tokens']])
        for t in tokens:self.assertEqual(p['source'][slice(*t['sourceScalar'])],t['surface']);self.assertTrue(t['analyses'])
        self.assertIn('prs.',p['text']);self.assertIn('acc.',p['text'])
        s['research'][gloss.KEY]['showSimpleAspect']=False
        compact=gloss.inspect(s,'page');self.assertNotIn('simp.',compact['paragraphs'][0]['text']);self.assertFalse(compact['showSimpleAspect'])

    def test_unknown_stale_or_unbound_analysis_is_never_guessed(self):
        for code,mutate in [
            ('LABEL_MISSING',lambda s:s['research'][gloss.KEY]['entries'].clear()),
            ('STALE_DICTIONARY_LABEL',lambda s:s['language']['lexicon'][0].update(notes='Changed sense context')),
            ('BOUND_TEST_REQUIRED',lambda s:s['tests'][0].pop('caseIds')),
            ('TAGS',lambda s:next(iter(s['research'][gloss.KEY]['entries'].values()))['tags'].append('guess.')),
        ]:
            s=deepcopy(self.snapshot);mutate(s)
            with self.assertRaisesRegex(ValueError,code):gloss.inspect(s,'page')
        s=deepcopy(self.snapshot);cid=s['tests'][0]['caseIds'][0][0];c=next(c for c in s['laboratory']['cases'] if c['id']==cid);c['tokens'][0]['features']={}
        with self.assertRaisesRegex(ValueError,'CASE_REJECTED'):gloss.inspect(s,'page')

    def test_profile_editing_guard_and_frozen_versions(self):
        s=GlossSession(ROOT,source_fonts=False,recovery=False);s.forge=self.project;api=GlossAPI(s)
        try:
            head=self.project.status()['head'];p=deepcopy(self.snapshot['research'][gloss.KEY]);next(iter(p['entries'].values()))['label']='Revised'
            def call(project_id,generation):return api.call('forge.gloss.put',dict(project_id=project_id,expected_generation=generation,profile=p),expected_revision=s.revision,idempotency_key=uuid.uuid4().hex)
            self.assertFalse(call('wrong',0)['ok']);self.assertTrue(call(self.project.status()['projectId'],0)['ok'])
            self.assertFalse(call(self.project.status()['projectId'],0)['ok'])
            self.assertEqual(self.project.read(head)['snapshot'],self.snapshot)
            self.project.commit('Gloss labels revised',self.project.status()['generation'])
            self.assertNotEqual(gloss.inspect(self.project.read()['snapshot'],'page')['profileSha256'],gloss.inspect(self.snapshot,'page')['profileSha256'])
            path=self.work/'export.json';self.project.export(path);restored=ForgeProject.restore(path,self.work/'restored.vayforge');self.assertEqual(restored.read()['snapshot'],self.project.read()['snapshot'])
        finally:s.finish()

    def test_forge_ui_preview_and_editable_labels(self):
        s=GlossSession(ROOT,source_fonts=False,recovery=False);s.forge=self.project;api=GlossAPI(s);w=GlossWindow(s,api)
        try:
            before=s.capture();w.show_forge(section='Gloss',gloss_test='page',gloss_preview=True);panel=w.forge_panel.gloss
            self.assertGreater(panel.tokens.rowCount(),0);self.assertIn('prs.',panel.prose.toPlainText());self.assertIn('Pinned references',panel.explanation.toPlainText())
            panel.load();self.assertGreater(panel.entries.rowCount(),0);eid=panel.entries.item(0,0).text();panel.entries.item(0,1).setText('Clear label');self.assertTrue(panel.dirty);self.assertTrue(panel.save())
            self.assertEqual(self.project.read()['snapshot']['research'][gloss.KEY]['entries'][eid]['label'],'Clear label');self.assertEqual(s.capture(),before)
            panel.load();panel.entries.item(0,2).setText('unrecognized.');self.assertFalse(panel.save());self.assertTrue(panel.dirty)
            w.forge_panel.refresh();self.assertEqual(panel.entries.item(0,2).text(),'unrecognized.')
            panel.entries.item(0,2).setText('');self.assertTrue(w.forge_panel.flush());self.assertFalse(panel.dirty)
        finally:w.job_timer.stop();w.forge_panel.timer.stop();w.hide();s.window=None;w.deleteLater();s.finish();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)

    def test_copy_preflight_protects_source_and_existing_targets(self):
        from vayrshemon.gloss_copy import create
        from types import SimpleNamespace
        head=self.project.status()['head'];state={'pages':[]};book=SimpleNamespace(capture=lambda:deepcopy(state))
        for version,target,code in [(head,self.work,'DIRECTORY_EXISTS'),('draft',self.work/'new','FROZEN_VERSION_REQUIRED'),(head,self.work/'new','TWO_PAGE_FOUR_FRAME_SOURCE_REQUIRED')]:
            with self.assertRaisesRegex(ValueError,code):create(book,self.project,version,'page',target)
        self.assertEqual(state,{'pages':[]});self.assertFalse((self.work/'new').exists())
        source=self.snapshot['tests'][0]['paragraphs'][0]['text']
        def frame(x,text):
            return {'x':str(x),'content':{'document':{'stories':[{'blocks':[{'runs':[{'text':text}]}]}]}}}
        for first,third,last,code in [('changed','','Synthetic test data.','SOURCE_TEXT_MISMATCH'),(source,'occupied','Synthetic test data.','RESERVED_COLUMN_NOT_EMPTY'),(source,'','different English','ENGLISH_TEXT_MISMATCH')]:
            state['pages']=[dict(frames=[frame(0,first),frame(400,source)]),dict(frames=[frame(0,third),frame(400,last)])]
            before=deepcopy(state)
            with self.assertRaisesRegex(ValueError,code):create(book,self.project,head,'page',self.work/'new')
            self.assertEqual(state,before);self.assertFalse((self.work/'new').exists())

    def test_feature_labels_cover_aspect_without_inventing_features(self):
        # The existing annotated fixture has no aspect feature: the gloss must
        # not invent simple aspect just because its display option is enabled.
        r=gloss.inspect(self.snapshot,'page');self.assertNotIn('simp.',r['paragraphs'][0]['text'])
        self.assertEqual(gloss.FEATURES['aspect']['perfect'],'perf.')
        s=deepcopy(self.snapshot);eid=next(iter(s['research'][gloss.KEY]['entries']));s['research'][gloss.KEY]['entries'][eid]['tags']=['sg.']
        self.assertIn('sg.',gloss.inspect(s,'page')['paragraphs'][0]['text'])
        next(r for r in s['laboratory']['rules'] if r['id']=='verb')['config']['slots'].append(dict(feature='aspect',values={'simple':''}))
        for c in s['laboratory']['cases']:
            for t in c['tokens']:
                if t['entryId']=='root':t['features']['aspect']='simple'
        self.assertIn('simp.',gloss.inspect(s,'page')['paragraphs'][0]['text'])
        s['research'][gloss.KEY]['showSimpleAspect']=False
        self.assertNotIn('simp.',gloss.inspect(s,'page')['paragraphs'][0]['text'])

    def test_published_contracts_and_headless_mcp(self):
        self.assertEqual(len(METHODS),150)
        self.assertEqual(len(load_json(ROOT/'data/gloss-capabilities.json')['capabilities']),150)
        messages=[dict(jsonrpc='2.0',id=1,method='initialize',params={}),dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=2,method='tools/list')]
        p=subprocess.run([sys.executable,'-m','vayrshemon','mcp','--headless','--gloss','--no-source-fonts'],input='\n'.join(json.dumps(m) for m in messages)+'\n',text=True,capture_output=True,cwd=ROOT,timeout=40)
        self.assertEqual(p.returncode,0,p.stderr);responses=[json.loads(line) for line in p.stdout.splitlines()];tools=next(r['result']['tools'] for r in responses if r.get('id')==2)
        self.assertEqual(len(tools),150);self.assertTrue(any(t['name']=='page_gloss_copy' for t in tools))


if __name__=='__main__':unittest.main()
