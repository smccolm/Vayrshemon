"""Build a separate M5 standard page and evidence bundle from a saved M4 page.

Archive text, fonts and generated books stay under ignored .local. Run with
--source <saved M4 document> --out <new empty directory>. No live session closes.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import uuid
from PySide6.QtWidgets import QApplication
from tools.m0.common import write_json
from vayrshemon.language_session import LanguageSession
from vayrshemon.language_api import LanguageAPI
from vayrshemon import language as lang


def build(root,source,out):
    root=Path(root);source=Path(source);out=Path(out)
    if out.exists(): raise ValueError('DEMO_DIRECTORY_ALREADY_EXISTS')
    out.mkdir(parents=True)
    app=QApplication.instance() or QApplication([])
    session=LanguageSession(root,source_fonts=False,recovery=False);api=LanguageAPI(session);transcript=[]
    def call(method,**params):
        result=api.call(method,params,expected_revision=session.revision,document_id=session.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp')
        transcript.append(dict(method=method,params=params,response=result))
        if not result['ok']: raise ValueError(result)
        return result['result']
    try:
        session.open(source);original=deepcopy(session.capture())
        if len(original['pages'])!=1 or len(original['pages'][0]['frames'])!=2: raise ValueError('STANDARD_TWO_COLUMN_SOURCE_REQUIRED')
        call('language.archive.import')
        data=call('language.read')['data']
        # Add one explicit, reviewable lexical association from the attested
        # causative conjunction/gloss. Preserve the unannotated archive revision.
        entry=next(r for r in data['lexicon'] if r['id'].startswith('chart-1.') and r['headword']=='kenst')
        pair=next(r for r in data['corpus'] if r['id']=='polished.2')
        token=next(t for t in pair['tokens'] if t['surface']==entry['headword'])
        token.update(entryIds=[entry['id']],senseIds=[entry['senses'][0]['id']],morphemes=[token['surface']],glosses=['for<1causative conjunction>'],status='uncertain')
        pair['notes']+=' Demo review association: identical kenst spelling and causative gloss in the cited chart and polished example. Exact historical font/orthography remains unresolved.'
        pair['citations']+=entry['citations']
        call('language.record.put',collection='corpus',record=pair,label='Review: link attested causative conjunction to its source entry')
        frames=sorted(original['pages'][0]['frames'],key=lambda f:int(f['x']));left,right=frames
        texts={f['frameId']:session.frames[f['frameId']].text() for f in frames}
        data=call('language.read')['data']
        for pair in data['corpus']:
            expected=pair['text'].replace(chr(190),chr(8217))
            a=texts[left['frameId']].find(expected);b=texts[right['frameId']].find(pair['translation'])
            if min(a,b)<0: raise ValueError('STANDARD_TEXT_DOES_NOT_MATCH_ATTESTED_PAIR')
            call('corpus.link',corpus_id=pair['id'],source=dict(frame_id=left['frameId'],start=lang.utf16_length(texts[left['frameId']][:a]),end=lang.utf16_length(texts[left['frameId']][:a+len(expected)])),
                 translation=dict(frame_id=right['frameId'],start=lang.utf16_length(texts[right['frameId']][:b]),end=lang.utf16_length(texts[right['frameId']][:b+len(pair['translation'])])),
                 adaptation='Existing M4 79/81/80 review copy: U+00BE to U+2019 per data/formatting/parallel-translation-layered.json and Translation 1.psd. Source corpus text and original DOCX unchanged.')
        if session.capture()['pages']!=original['pages'] or session.state['paint']!=original['paint']: raise ValueError('M5_DEMO_CHANGED_PAGE_OR_PAINT')
        call('document.title',title='Vayrshemon-English-M5')
        call('document.save-as',path=str(out/'Vayrshemon-English-M5.vay.json'))
        for kind in ('png','svg','pdf'):
            call('publication.export',path=str(out/('standard.'+kind)),format=kind,mode='color',dpi=144 if kind=='png' else 300,raster_policy='raster')
        for kind in ('dictionary','grammar','corpus'): call('language.publish',path=str(out/(kind+'.html')),kind=kind)
        call('language.export',path=str(out/'language.json'))
        links=call('corpus.links');numbers={c['id']:call('numbers.format',convention_id=c['id'],numerator='1',denominator='7') for c in data['numberConventions']}
        layout=call('layout.inspect');write_json(out/'layout.json',layout)
        verification=dict(source=str(source),sourceSha256=lang.hashlib.sha256(source.read_bytes()).hexdigest(),pageAndPaintUnchanged=True,
            counts={k:len(v) for k,v in data.items()},links=links,numbers=numbers,languageRevision=session.state['language']['activeRevisionId'],
            nativeVersion=session.file_version,apiVersion=api.version,capabilities=len(api.methods),lexicalReviewEntry=entry['id'])
        write_json(out/'verification.json',verification);write_json(out/'api-transcript.json',transcript)
        print(json.dumps(dict(ok=True,path=str(out),counts=verification['counts'],links=len(links['links']),methods=len(api.methods))))
        return verification
    finally: session.finish()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();build(Path(__file__).resolve().parents[1],args.source,args.out)
