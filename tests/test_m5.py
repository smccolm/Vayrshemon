"""M5 preservation, language revisions, actual archive, exact arithmetic and UI exports."""
from copy import deepcopy
from fractions import Fraction
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid
if os.name!='nt': os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from jsonschema import Draft202012Validator
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtWidgets import QApplication,QPushButton
from tools.m0.synthetic import make_font
from vayrshemon.language_session import LanguageSession
from vayrshemon.language_api import LanguageAPI,METHODS
from vayrshemon.language_contracts import DOCUMENT,PACKAGE
from vayrshemon.language_window import LanguageWindow
from vayrshemon.studio_session import StudioSession
from vayrshemon import language as lang
from vayrshemon.mcp import tools

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


def entry(rid='entry.one'):
    return dict(id=rid,label='Synthetic entry',status='draft',citations=[],notes='',headword='A',orthographyId=None,
        pronunciation='',ipa='',partOfSpeech='noun',senses=[dict(id=rid+'.sense1',definition='Synthetic test meaning',status='draft',citations=[])],
        variants=[],etymology='',exampleIds=[],audioLinks=[])


def corpus(text='A😀 B',rid='corpus.one'):
    return dict(id=rid,label='Synthetic corpus',status='draft',citations=[],notes='',text=text,translation='Test translation',
        transliteration='',rawGloss='',orthographyId=None,sourceFonts=[],tokens=lang.tokens(text),offsetUnit='unicode-scalar')


def convention():
    return dict(id='ascii',label='Synthetic ASCII digits',status='draft',citations=[],notes='',digits=list('0123456789AB'),
        digitNames=[str(n) for n in range(12)],radixPoint='.',minus='-',repeatOpen='(',repeatClose=')',readingPolicy='digits-only')


class LanguageTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m5'/uuid.uuid4().hex;self.work.mkdir(parents=True)
        shutil.copytree(ROOT/'schemas',self.work/'schemas')
        for file in ('data/fonts.json','data/orthography/thimfora-79.json'):
            p=self.work/file;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/file,p)
        self.s=LanguageSession(self.work,source_fonts=False,recovery=False);self.api=LanguageAPI(self.s);self.window=None

    def tearDown(self):
        if self.window:
            self.window.hide();self.window.deleteLater();self.s.window=None
        self.s.finish()
        for frame in self.s.frames.values(): frame.deleteLater()
        self.s.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);APP.processEvents()

    def call(self,method,**params):
        r=self.api.call(method,params,expected_revision=self.s.revision,document_id=self.s.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp')
        self.assertTrue(r['ok'],r);return r['result']

    def reject(self,method,**params):
        before=self.s.capture();r=self.api.call(method,params,expected_revision=self.s.revision,document_id=self.s.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp')
        self.assertFalse(r['ok'],r);self.assertEqual(before,self.s.capture());return r

    def put(self,key,value): return self.call('language.record.put',collection=key,record=value)

    def test_revision_fork_diff_adoption_and_no_text_rewrite(self):
        self.call('document.edit',start=0,end=0,text='Historical 😀 quotation')
        before=self.s.capture()['pages'];empty=self.s.state['language']['activeRevisionId']
        first=self.put('lexicon',entry())['id'];r=entry();r['senses'][0]['definition']='Revised meaning'
        second=self.put('lexicon',r)['id']
        diff=self.call('language.diff',before=first,after=second)
        self.assertEqual(len(diff['collections']['lexicon']['changed']),1)
        self.assertEqual(self.call('language.read',revision_id=first,collection='lexicon')['data'][0],entry())
        self.call('language.adopt',revision_id=first);branch=self.put('lexicon',entry('entry.two'))
        self.assertEqual(branch['parentId'],first)
        self.assertEqual(len(self.s.state['language']['objects']),3) # shared immutable entry.one is not copied
        self.assertEqual(self.s.capture()['pages'],before)
        self.call('history.undo');self.assertEqual(self.s.state['language']['activeRevisionId'],first)
        self.call('history.redo');self.assertEqual(self.s.state['language']['activeRevisionId'],branch['id'])
        self.call('language.adopt',revision_id=empty);self.assertEqual(self.call('lexicon.search')['total'],0)
        self.assertEqual(self.s.capture()['pages'],before)

    def test_references_sense_ids_and_failed_edits_are_atomic(self):
        self.put('lexicon',entry());r=corpus('A');r['tokens'][0].update(entryIds=['entry.one'],senseIds=['entry.one.sense1'],morphemes=['A'],glosses=['TEST'])
        self.put('corpus',r)
        self.reject('language.record.delete',collection='lexicon',record_id='entry.one')
        r['tokens'][0]['senseIds']=['missing'];self.reject('language.record.put',collection='corpus',record=r)
        r['tokens'][0]['senseIds']=[];r['tokens'][0]['surface']='wrong';self.reject('language.record.put',collection='corpus',record=r)
        r=entry('entry.two');r['senses'][0]['id']='entry.one.sense1';self.reject('language.record.put',collection='lexicon',record=r)
        r=entry();r['citations']=[dict(sourceId='missing',locator='test')];self.reject('language.record.put',collection='lexicon',record=r)

    def test_document_links_surrogates_adaptation_staleness_and_old_revision(self):
        self.put('lexicon',entry());r=corpus();r['tokens'][0].update(entryIds=['entry.one'],senseIds=['entry.one.sense1'])
        self.put('corpus',r);self.call('document.edit',start=0,end=0,text=r['text']);left=self.s.state['activeFrameId']
        right=self.call('frame.add',x=320,y=18,width=240,height=650,name='English')['frameId']
        self.call('document.edit',start=0,end=0,text=r['translation'])
        args=dict(corpus_id=r['id'],source=dict(frame_id=left,start=0,end=lang.utf16_length(r['text'])),translation=dict(frame_id=right,start=0,end=len(r['translation'])))
        link=self.call('corpus.link',**args)
        self.assertTrue(self.call('corpus.links')['links'][0]['valid'])
        self.assertEqual(len(self.call('corpus.search',entry_id='entry.one')['documentOccurrences']),1)
        broken=deepcopy(args);broken['source']['end']=2;self.reject('corpus.link',**broken) # splits surrogate
        self.call('document.edit',start=0,end=0,text='!')
        self.assertFalse(self.call('corpus.links')['links'][0]['valid'])
        self.call('history.undo');self.assertTrue(self.call('corpus.links')['links'][0]['valid'])
        older=link['revisionId'];self.put('lexicon',entry('entry.two'))
        self.assertFalse(self.call('corpus.links')['links'][0]['usesActiveRevision'])
        self.call('language.adopt',revision_id=older)
        self.call('frame.delete',frame_id=left);self.assertIn('SOURCE_FRAME_MISSING',self.call('corpus.links')['links'][0]['diagnostics'])
        self.call('history.undo');self.assertTrue(self.call('corpus.links')['links'][0]['valid'])

    def test_corpus_literal_search_and_frequency_preserve_legacy_case(self):
        self.put('corpus',corpus('A a A\u0301 😀 A'))
        result=self.call('corpus.search',query='A',limit=2)
        self.assertEqual(result['total'],3);self.assertTrue(result['truncated'])
        self.assertEqual(result['frequencies'][0],dict(text='A',count=2))
        result=self.call('corpus.search',query='😀');self.assertEqual(result['hits'][0]['start'],7)
        self.assertEqual(self.call('corpus.search',query='á')['total'],0)

    def test_trace_preserves_ambiguous_transliteration_and_unknown_scalars(self):
        p=dict(id='profile',mappings=[dict(source='A',target='x'),dict(source='B',target='x')])
        result=lang.transliterate(p,'AB?😀')
        self.assertEqual(result['text'],'xx?😀');self.assertEqual(len(result['diagnostics']),2)
        with self.assertRaisesRegex(ValueError,'AMBIGUOUS'): lang.transliterate(p,result['text'],reverse=True)
        self.assertEqual(lang.transliterate(p,result['text'],trace=result['trace'])['text'],'AB?😀')
        forged=deepcopy(result['trace']);forged['original']='changed'
        with self.assertRaises(ValueError): lang.transliterate(p,result['text'],trace=forged)
        prefix=dict(id='p',mappings=[dict(source='A',target='x'),dict(source='B',target='xy')])
        with self.assertRaisesRegex(ValueError,'AMBIGUOUS'): lang.transliterate(prefix,'xy',reverse=True)

    def test_exact_base12_finite_repeating_negative_and_large_values(self):
        c=convention()
        for n in range(-17,18):
            for d in range(1,49):
                rendered=lang.number_format(c,str(n),str(d));parsed=lang.number_parse(c,rendered['text'])
                self.assertTrue(rendered['exact']);self.assertEqual(Fraction(int(parsed['numerator']),int(parsed['denominator'])),Fraction(n,d))
        value=10**100+123;rendered=lang.number_format(c,str(value),'7')
        self.assertEqual(Fraction(**{k:int(v) for k,v in lang.number_parse(c,rendered['text']).items() if k in ('numerator','denominator')}),Fraction(value,7))
        self.assertEqual(lang.number_format(c,'1','7')['text'],'0.(186A35)')
        self.assertEqual(lang.number_format(c,'1','8')['text'],'0.16')
        short=lang.number_format(c,'1','7',2);self.assertTrue(short['truncated']);self.assertFalse(short['exact'])
        for bad in ('0.','0.()','0.(1','0.1(2))','-','0…','0.1.2'):
            with self.assertRaises(ValueError): lang.number_parse(c,bad)
        with self.assertRaises(ValueError): lang.number_format(c,'1','0')
        self.put('numberConventions',c);self.reject('numbers.format',convention_id='ascii',numerator=0.1)

    def test_portable_package_hash_import_and_publication_escape(self):
        e=entry();e['headword']='<script>alert(1)</script>';self.put('lexicon',e)
        path=self.work/'language.json';self.call('language.export',path=str(path))
        payload=json.loads(path.read_text());Draft202012Validator(PACKAGE).validate(payload)
        rid=self.call('language.import',path=str(path))['id']
        self.assertEqual(self.call('language.read',collection='lexicon')['data'],[e])
        self.reject('language.export',path=str(path))
        payload['data']['lexicon'][0]['headword']='tamper';path.write_text(json.dumps(payload))
        self.reject('language.import',path=str(path))
        html=self.work/'dictionary.html';self.call('language.publish',kind='dictionary',path=str(html))
        output=html.read_text(encoding='utf-8');self.assertIn('&lt;script&gt;',output);self.assertNotIn('<script>',output);self.assertIn(rid,output)

    def test_m4_migration_and_native_roundtrip_preserve_exact_paint_and_source(self):
        old=StudioSession(self.work,source_fonts=False,recovery=False)
        with old.command('test text'): old.active.edit(0,0,'A😀 historical')
        old.state['paint']['recipe']['lightAzimuth']=213;old.state['paint']['background']='#FF000000'
        original=self.work/'m4.vay.json';old.save(original);before=original.read_bytes();expected=deepcopy(old.capture());old.finish()
        self.s.open(original);self.assertEqual(self.s.capture()['pages'],expected['pages']);self.assertEqual(self.s.state['paint'],expected['paint'])
        self.reject('document.save',path=str(original))
        self.put('lexicon',entry());saved=self.work/'m5.vay.json';self.call('document.save',path=str(saved))
        capture=self.s.capture();self.call('document.open',path=str(saved),discardUnsaved=True)
        result=self.s.capture();capture.pop('revision');result.pop('revision');self.assertEqual(result,capture)
        self.assertEqual(original.read_bytes(),before)
        payload=json.loads(saved.read_text());Draft202012Validator(DOCUMENT).validate(payload)
        h=next(iter(payload['state']['language']['objects']));payload['state']['language']['objects'][h]['label']='tampered';saved.write_text(json.dumps(payload))
        self.reject('document.open',path=str(saved),discardUnsaved=True)

    def test_input_palette_font_guard_and_undo(self):
        font=self.work/'synthetic.ttf';make_font(font);fid=self.call('fonts.load',path=str(font))['fontId'];sha=fid.split(':')[1]
        orth=dict(id='ortho',label='Synthetic',status='draft',citations=[],version='1',normalization='none',fontSha256s=[sha],symbols=[dict(id='letter.a',name='A',kind='letter',status='draft',forms=[dict(form='default',scalar=65,transliteration='a')])],unresolvedScalars=[])
        self.put('orthographies',orth)
        self.put('inputLayouts',dict(id='keys',label='Synthetic',status='draft',citations=[],orthographyId='ortho',keys=[dict(key='letter.a',text='A')]))
        self.call('orthography.input',layout_id='keys',key='letter.a',font_id=fid,start=0,end=0)
        self.assertEqual(self.s.text(),'A');self.call('history.undo');self.assertEqual(self.s.text(),'')
        source=self.s.state['activeFrameId']
        target=self.call('frame.add',x=18,y=18,width=576,height=756,name='Continuation')['frameId']
        self.call('flow.set',source_frame_id=source,targets=[target])
        self.call('frame.select',frame_id=target)
        self.reject('orthography.input',layout_id='keys',key='letter.a',font_id=fid,start=0,end=0)
        self.call('frame.select',frame_id=source)
        orth['fontSha256s']=['0'*64];self.put('orthographies',orth)
        self.reject('orthography.input',layout_id='keys',key='letter.a',font_id=fid,start=0,end=0)

    def test_api_stale_retry_and_published_contracts(self):
        params=dict(collection='lexicon',record=entry());key=uuid.uuid4().hex;revision=self.s.revision
        def call(): return self.api.call('language.record.put',params,expected_revision=revision,document_id=self.s.state['documentId'],idempotency_key=key,origin='mcp')
        first=call();self.assertTrue(first['ok']);self.assertEqual(call(),first)
        stale=self.api.call('language.record.put',params,expected_revision=revision,document_id=self.s.state['documentId'],idempotency_key='new-key',origin='mcp')
        self.assertFalse(stale['ok']);self.assertIn('STALE_REVISION',stale['error']['code'])
        self.assertEqual(json.loads((ROOT/'data/language-mcp-tools.json').read_text())['tools'],tools(METHODS))
        self.assertEqual(json.loads((ROOT/'schemas/language-document.schema.json').read_text()),DOCUMENT)

    def test_bottom_buttons_and_publish_dialog_suggest_timestamped_names(self):
        self.window=LanguageWindow(self.s,self.api);self.window.show();APP.processEvents()
        defaults=[]
        def cancel(*args,**kwargs): defaults.append(args[2]);return '', ''
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',side_effect=cancel):
            for label in ('PNG','SVG proof'):
                button=next(b for b in self.window.findChildren(QPushButton) if b.text()==label);button.click()
            self.window.export_proof('pdf')
        self.assertEqual([Path(p).suffix for p in defaults],['.png','.svg','.pdf'])
        for name in defaults:
            prefix='^' if Path(name).suffix=='.png' else '_'
            self.assertRegex(Path(name).name,prefix+r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_\d{3}\.(png|svg|pdf)$')
        self.assertEqual(self.s.revision,0)
        self.put('lexicon',entry())
        self.call('ui.workspace',panel='Language')
        APP.processEvents()
        panel=self.window.sidebar.currentWidget()
        self.assertEqual(panel.horizontalScrollBar().maximum(),0)

    @unittest.skipUnless((ROOT/'Inputs/Versions Best/Polished Examples.docx').exists(),'Local archive unavailable')
    def test_actual_archive_competing_entries_gloss_conflict_and_nta_roundtrip(self):
        from vayrshemon.archive_language import seed
        data=seed(ROOT);self.assertEqual(len(data['lexicon']),733)
        self.assertEqual(next(r for r in data['lexicon'] if r['id']=='chart-1.t2.r1')['headword'],'kenst')
        self.assertTrue(any(r['id'].startswith('chart-original.') for r in data['lexicon']))
        self.assertTrue(any(r['id'].startswith('chart-1.') for r in data['lexicon']))
        self.assertEqual(sum(r['status']=='disputed' for r in data['morphology']),2)
        self.assertEqual(len(data['orthographies'][0]['symbols']),59)
        self.assertEqual([t['glosses'][0] for t in data['corpus'][0]['tokens']][1],'I(singular)')
        self.assertTrue(all(not t['entryIds'] for r in data['corpus'] for t in r['tokens']))
        c=data['numberConventions'][0];rendered=lang.number_format(c,'1729','144');value=lang.number_parse(c,rendered['text'])
        self.assertEqual(Fraction(int(value['numerator']),int(value['denominator'])),Fraction(1729,144))
        self.put('sources',next(r for r in data['sources'] if r['id']=='mapping-79'))
        self.put('orthographies',data['orthographies'][0]);self.put('numberConventions',c)
        fid=self.call('fonts.load',path=str(ROOT/'Inputs/font files/Thimfora_79.ttf'))['fontId']
        self.window=LanguageWindow(self.s,self.api);self.window.show();APP.processEvents()
        self.window.format_number();APP.processEvents()
        self.assertEqual(self.window.number_text.font().family(),self.s.fonts.resolve(fid).family)
        self.assertGreaterEqual(self.window.number_text.height(),72)
        self.assertIn('unta.chart-2',self.window.number_result.toPlainText())
        before=len(json.dumps(data));state=lang.initial();lang.append_revision(state,data,'Archive')
        data['lexicon'][0]['notes']+=' reviewed';lang.append_revision(state,data,'One edit')
        self.assertLess(len(json.dumps(state)),before*1.5) # immutable objects are shared across revisions

    def test_forced_exit_checkpoint_recovers_language_revision(self):
        code="""from pathlib import Path
import json,os,sys
from PySide6.QtWidgets import QApplication
from vayrshemon.language_session import LanguageSession
from vayrshemon.language_api import LanguageAPI
from tests.test_m5 import entry
app=QApplication.instance() or QApplication([]);s=LanguageSession(Path(sys.argv[1]),source_fonts=False,recovery=True);api=LanguageAPI(s)
r=api.call('language.record.put',dict(collection='lexicon',record=entry()),expected_revision=s.revision,origin='desktop')
assert r['ok'],r
Path(sys.argv[1],'checkpoint-path.txt').write_text(str(s.recovery_path))
os._exit(0)
"""
        process=subprocess.run([sys.executable,'-c',code,str(self.work)],cwd=ROOT,capture_output=True,timeout=30)
        self.assertEqual(process.returncode,0,process.stderr.decode(errors='replace')[-2000:])
        checkpoint=(self.work/'checkpoint-path.txt').read_text();self.call('recovery.restore',path=checkpoint,discardUnsaved=True)
        self.assertEqual(self.call('language.read',collection='lexicon')['data'],[entry()])


if __name__=='__main__': unittest.main()
