"""Reproducible private Forge demo; original inputs and approved reference stay intact."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import uuid
from PySide6.QtWidgets import QApplication
from tools.m0.common import load_json,write_json,file_hash
from tools.approved_baseline import MANIFEST,check_state
from vayrshemon.forge_api import ForgeSession,ForgeAPI
from vayrshemon.forge_archive import proposal


def build(root,out):
    root,out=Path(root),Path(out)
    if out.exists(): raise ValueError('DEMO_DIRECTORY_EXISTS')
    out.mkdir(parents=True)
    app=QApplication.instance() or QApplication([])
    s=ForgeSession(root,source_fonts=False,recovery=False);api=ForgeAPI(s);transcript=[]
    def call(method,**params):
        if 'expected_generation' in api.methods[method][2]['properties']:
            status=s.forge.status();params.update(expected_generation=status['generation'],project_id=status['projectId'])
        result=api.call(method,params,expected_revision=s.revision,document_id=s.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp')
        transcript.append(dict(method=method,params=params,response=result))
        if not result['ok']: raise ValueError(result['error']['message'])
        return result['result']
    try:
        manifest=load_json(root/MANIFEST);source=root/manifest['source']['path'];baseline=load_json(source)
        if file_hash(source)!=manifest['source']['sha256']: raise ValueError('APPROVED_REFERENCE_CHANGED')
        check_state(baseline['state'],manifest);write_json(out/'approved-workbench.vay.json',baseline);s.open(out/'approved-workbench.vay.json');original=s.capture()
        call('forge.create',path=str(out/'Vayrshemon.vayforge'),title='Vayrshemon · Language Forge',archive=True)
        archive=call('forge.read')['snapshot'];archive_head=s.forge.status()['head']
        call('forge.branch',name='extrapolation-0.1',version=archive_head)
        draft=proposal(archive,root)
        review=root/'data/language/dictionary-inspiration.json'
        if review.exists():
            records=load_json(review)['sources']
            for r in records:
                if file_hash(root/r['path'])!=r['sha256']: raise ValueError('DICTIONARY_REVIEW_SOURCE_CHANGED')
                r['reviewScope']='Front matter extracted through PDF page 14; page 9 rendered for visual review. Middle Egyptian is scanned; no full dictionary OCR. Inspiration only, excluded from Vayrshemon frequency counts.'
            draft['research']['dictionaryInspiration']=records
            draft['wiki'].append(dict(id='dictionary-design',title='Dictionary design and source inspiration',ruleIds=['forge.rule.lexicon'],body='# Dictionary design\n\nThe ten supplied dictionaries inform the structure, not the vocabulary of this version.\n\n- Frequency dictionary: report corpus size, counts and sampling separately from lexical coverage.\n- Historical/etymological and dialect dictionaries: preserve variant witnesses and their provenance.\n- Bilingual and phonetic dictionaries: keep headword, gloss and pronunciation distinct; unknown IPA stays blank.\n- Idiom dictionary: constructions can have meanings beyond isolated roots.\n- Grammar dictionary: define terminology and connect related rules.\n- Technical and Middle Egyptian dictionaries: retain domain and writing-system distinctions.\n\nReview scope: front matter and sampled pages, not an exhaustive reading of every entry. Source hashes and page ranges are in Research.'))
        call('forge.draft.replace',snapshot=draft);v1=call('forge.commit',label='Vayrshemon 0.1.0 · source-derived proposal')['head']
        page=deepcopy(next(r for r in draft['wiki'] if r['id']=='order'))
        page['body']+='\n\n## Revision 0.1.1 — clause audit\nKeep the accusative suffix on the noun head before its following modifier. The novel jewel clause is OBJECT-ACC + blue-COUNT.MOD + I + see-PAST-SIMPLE. The English translation uses subject–verb–object order. This is an explicit proposal for the new branch, not a rewrite of the source gloss.\n\nFor a clause joined by the causative conjunction, retain a complete object–subject–verb clause on each side. Intransitive learn clauses contain only subject + finite verb.'
        call('forge.record.put',collection='wiki',record=page)
        entry=deepcopy(next(r for r in draft['language']['lexicon'] if r['id']=='forge.story'))
        entry['etymology']+=' Revision 0.1.1: current 79 spelling mapped by the named ren letter from the Venik instructions; the original chart spelling is retained in variants. Used as a count noun with thing determiner and accusative case in the novel test.'
        call('forge.record.put',collection='lexicon',record=entry)
        v2=call('forge.commit',label='Vayrshemon 0.1.1 · wiki and dictionary review')['head']
        diff=call('forge.diff',before=v1,after=v2)
        report=call('forge.test.run',version=v2,test_id=draft['tests'][0]['id'],directory=str(out/'novel-test'))
        if report['status'] in ('Error','Fail'): raise ValueError(report)
        call('forge.export',path=str(out/'forge-history.json'))
        if s.capture()!=original: raise ValueError('FORGE_CHANGED_OPEN_WORKBENCH')
        check_state(s.capture(),manifest)
        result=dict(project=str(s.forge.path),approvedWorkbench=str(out/'approved-workbench.vay.json'),archiveVersion=archive_head,firstProposal=v1,editedVersion=v2,
                    dictionaryEntries=len(draft['language']['lexicon']),wikiPages=len(draft['wiki']),diff=diff,run=report,openDocumentUnchanged=True)
        write_json(out/'demo.json',result);return result
    finally:
        write_json(out/'api-transcript.json',transcript);s.finish()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=build(Path(__file__).resolve().parents[1],a.out.resolve())
    print(json.dumps({k:result[k] for k in ('project','firstProposal','editedVersion','dictionaryEntries','wikiPages','openDocumentUnchanged')}))
