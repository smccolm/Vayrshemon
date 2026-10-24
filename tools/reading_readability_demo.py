"""Reproducible larger Roman reading and a separately versioned literary coda.

Derives private text from the selected Forge snapshot. Never changes its source
test, language rules, fonts or the immutable English presentation baseline.
"""
from copy import deepcopy
from pathlib import Path
import argparse
import json
import uuid

from PySide6.QtWidgets import QApplication
from tools.m0.common import load_json, write_json, file_hash
from vayrshemon import forge_lab, reading, spelling, pages
from vayrshemon.forge import validate, digest
from vayrshemon.forge_runner import align_paragraphs
from vayrshemon.reliability_session import ReliabilitySession
from vayrshemon.reliability_api import ReliabilityAPI
from vayrshemon.session import utf16_length, SCALE


TEST_ID = 'tempest-reading-coda'


def proposal(source):
    s = deepcopy(source)
    original = next(t for t in s['tests'] if t['id'] == 'tempest-dreams')
    lookup = {c['id']: c for c in s['laboratory']['cases']}
    groups = [[lookup[k] for k in ids] for ids in original['caseIds']]
    lex = {e['id']: e for e in s['language']['lexicon']}

    def token(case, role):
        t = deepcopy(next(t for t in case['tokens'] if t['role'] == role))
        return t, case['text'][t['start']:t['end']]

    def finite(entry, tense, aspect='simple'):
        return dict(role='verb', entryId=entry, features=dict(tense=tense, aspect=aspect)), lex[entry]['headword'] + {'past':'iz','present':'ow'}[tense] + {'simple':'ya','perfect':'fu'}[aspect]

    def clause(key, title, template, items):
        c = deepcopy(template)
        c.update(id='reading.coda.' + key, title=title, tokens=[], text='',
                 note='Original editorial coda, not Shakespeare or an attested archive quotation. Existing lexicon, inflections, discourse restrictions and Maxima policy; literary meaning still needs review.')
        pieces = []
        offset = 0
        for t, word in items:
            t.update(start=offset, end=offset+len(word)); c['tokens'].append(t)
            pieces.append(word); offset += len(word)+1
        c['text'] = spelling.inspect_text(' '.join(pieces)+'.', s['spelling'], spelling.pairs(s))['text']
        s['laboratory']['cases'].append(c)
        return c

    # The coda looks back on the performance, then returns to the shared "we".
    # Context serves that reading; no new word order or random synonym rule.
    dream, sleep = groups[2]
    revels, actors = groups[0][:2]
    subject, _ = token(revels, 'subject')
    c1 = clause('celebration', 'Our celebration was dream-substance', dream, [
        token(dream, 'predicate'), (subject, lex['m8.ourplay']['headword']+'lÉy'),
        finite('forge.be', 'past')])
    obj, _ = token(sleep, 'object'); obj['entryId'] = 'm8.dreamform'
    c2 = clause('vision', 'We see fragile dream-substance', sleep, [
        (obj, lex['m8.dreamform']['headword']+'get'), token(sleep, 'modifier'),
        token(dream, 'subject'), finite('forge.see', 'present')])
    c3 = clause('shadows', 'We have become shadow-forms', actors, [
        token(dream, 'subject'), token(actors, 'predicate'), finite('m8.become', 'present', 'perfect')])
    test = deepcopy(original)
    test.update(id=TEST_ID, title='The Tempest · a dream and its afterimage')
    test['caseIds'].append([c['id'] for c in (c1,c2,c3)])
    test['paragraphs'].append(dict(text=' '.join(c['text'] for c in (c1,c2,c3)),
        translation='Our celebration was a dream. We see its fragile form; we have become its shadows.',
        analysis='Original editorial coda after the Shakespeare selection, not an additional Shakespeare quotation. Literal back-reading: Our celebration was dream-substance. We see fragile dream-substance. We have become shadow-forms. English its connects the images rhetorically; no possessive suffix is asserted in the script. Existing discourse permits an unmarked established dream-object, and established subject-first we; full marking is retained for the new shadow predicate. No new dictionary entries or grammar rules.'))
    s['tests'].append(test)
    s['wiki'].append(dict(id='reading-larger-roman', title='Larger Roman reading and literary coda', ruleIds=original['ruleIds'], body='''# Longer reading specimen

The original three-paragraph Tempest selection is retained unchanged. A fourth paragraph is an original editorial coda, not Shakespeare: "Our celebration was a dream. We see its fragile form; we have become its shadows." Its literal back-reading and compression are recorded in the test analysis. Three additional annotated clauses use only the existing vocabulary, inflections, discourse conditions and Maxima policy. Mechanical acceptance does not establish literary equivalence.

The user requested larger transliteration and more vertical page use. This separate editable reading uses 28 pt transliteration 7 with 36 pt leading. The Thimfora column remains 50 pt / 38 pt. Page, frames, margins and both independent paint treatments remain unchanged. Paragraph starts are measured again. This is a reading variant; the frozen English baseline and earlier releases remain intact.
'''))
    validate(s)
    result = forge_lab.evaluate(s)
    if result['counts'].get('Fail'):
        raise ValueError([(r['caseId'], r['actual']) for r in result['results'] if r['status']=='Fail'])
    assert next(t for t in s['tests'] if t['id']=='tempest-dreams') == original
    assert s['language'] == source['language']
    return s, result


def compose(root, source_path, snapshot, out, size=28, leading=36):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    original = load_json(source_path)
    payload = deepcopy(original); state = payload['state']
    test = next(t for t in snapshot['tests'] if t['id']==TEST_ID)
    state.update(documentId='document.'+uuid.uuid4().hex, revision=0, title=test['title']+' · larger Roman reading')
    payload['history'] = []
    for frame in reading.pairs(state):
        content = frame['content']; doc = content['document']; doc['documentId'] = state['documentId']
        template = deepcopy(doc['stories'][0]['blocks'][0]); blocks=[]; characters=[]; offset=0
        for pair in test['paragraphs']:
            b=deepcopy(template); b['blockId']='block.'+uuid.uuid4().hex
            run=deepcopy(b['runs'][0]); run.update(runId='run.'+uuid.uuid4().hex, sourceText=pair['text']); b['runs']=[run]; blocks.append(b)
            end=offset+utf16_length(pair['text']); characters.append(dict(start=offset,end=end,attributes=deepcopy(content['characters'][0]['attributes']))); offset=end+1
        doc['stories'][0]['blocks']=blocks; content['characters']=characters
        content['paragraphs']=[dict(alignment='left',before=1.,after=24.,tabs=[]) for _ in blocks]
    write_json(out/'scaffold.vay.json',payload)
    session=ReliabilitySession(root,source_fonts=False,recovery=False)
    try:
        session.open(out/'scaffold.vay.json'); api=ReliabilityAPI(session)
        def call(method,**params):
            r=api.call(method,params,expected_revision=session.revision,idempotency_key=uuid.uuid4().hex)
            if not r['ok']:raise ValueError(r['error']['message'])
            return r['result']
        left,right=reading.pairs(state)
        call('frame.select',frame_id=right['frameId'])
        end=utf16_length(session.active.text())
        call('document.format',start=0,end=end,size=size)
        call('paragraph.format',start=0,end=end,lineHeight=dict(mode='exact',value=leading))
        align_paragraphs(session,len(test['paragraphs']))
        call('frame.select',frame_id=left['frameId'])
        path=out/'Dream-and-afterimage.vay.json';session.save(path)
        layout=pages.inspect(session,max_glyphs=20000);write_json(out/'layout.json',layout)
        final=session.capture();fl,fr=reading.pairs(final)
        assert reading.text_blocks(fl)==reading.text_blocks(fr)
        assert final['paint']==original['state']['paint']
        assert final['recipe']==original['state']['recipe']
        assert fl['content']['document']['styles']==left['content']['document']['styles']
        for f,old in zip(reading.pairs(final),reading.pairs(original['state'])):
            assert {k:v for k,v in f.items() if k!='content'}=={k:v for k,v in old.items() if k!='content'}
        measures=[]
        for f in layout['frames']:
            x,y,w,h=f['rect']; lines=f['layout']['lines']; bottom=max(l['advanceBounds'][1]+l['advanceBounds'][3] for l in lines)
            measures.append(dict(frameId=f['frameId'],lines=len(lines),filledPercent=100*(bottom-y)/h,verticalFits=bottom<=y+h+.01,overflow=f['overflow']))
        if not all(m['verticalFits'] for m in measures):raise ValueError('READING_VERTICAL_OVERFLOW: '+str(measures))
        image,render=pages.render(session,path=out/'proof.png',mode='color',dpi=144)
        overhangs=[]
        for f in layout['frames']:
            x,y,w,h=f['rect']
            for g in layout['glyphs']:
                if g['sourceFrameId']!=f['frameId']:continue
                a,b,c,d=g['inkBounds']
                if c>0 and d>0 and (a<x-.01 or a+c>x+w+.01 or b<y-.01 or b+d>y+h+.01):
                    overhangs.append(dict(frameId=f['frameId'],glyphId=g['glyphId'],sourceUtf16=g['sourceUtf16'],leftPoints=max(0,(x-a)/SCALE),rightPoints=max(0,(a+c-x-w)/SCALE),topPoints=max(0,(y-b)/SCALE),bottomPoints=max(0,(b+d-y-h)/SCALE)))
        report=dict(document=str(path),sha256=file_hash(path),sourceSha256=file_hash(source_path),testId=TEST_ID,testSha256=digest(test),snapshotSha256=digest(snapshot),romanSizePt=size,romanLeadingPt=leading,scriptSizePt=50,scriptLeadingPt=38,frames=measures,missingGlyphs=sum(bool(g['missingGlyph'] or g.get('fallbackReason')) for g in layout['glyphs']),exactSlotsPreserved=True,paintPreserved=True,collisionWarnings=layout['collisionReport']['afterCount'],inkOverhangs=overhangs,render=render)
        write_json(out/'review.json',report)
        return report
    finally:session.finish()


def main():
    p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--size',type=float,default=28);p.add_argument('--leading',type=float,default=36);a=p.parse_args()
    app=QApplication.instance() or QApplication([]);s,suite=proposal(load_json(a.snapshot))
    out=Path(a.out);report=compose(Path.cwd(),Path(a.source),s,out,a.size,a.leading)
    write_json(out/'proposal.json',s);write_json(out/'suite.json',suite)
    print(json.dumps(dict(report=report,suite=suite['counts']),ensure_ascii=True))


if __name__=='__main__':main()
