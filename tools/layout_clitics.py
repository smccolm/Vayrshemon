"""Optional line breaks at authored phrase-clitic boundaries, without new text.

Apply only when a long host plus a bound ending cannot fit its approved frame.
An isolated boundary character receives a tailoring profile; the rest of the
word is never assigned grapheme wrapping. Native save/export retains the rule.
"""
from copy import deepcopy
import re
from tools.compose_historical_book import uid
from vayrshemon.session import utf16_length
from vayrshemon.typesetting_contracts import profile

ID = 'language.vayrshemon.phrase-clitic-break'
GLOSS_ID = 'language.vayrshemon.gloss-tag-break'
FEATURES = {'relpair', 'reltriple', 'relquad', 'dep', 'add', 'subend'}
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêë'

def rule():
    value = profile(ID)
    value['breakAfter'] = LETTERS
    return value

def gloss_rule():
    value = profile(GLOSS_ID)
    value['breakAfter'] = ',.'
    # Keep a gloss compound together. Qt's end-of-line hyphen ink can project
    # beyond its nominal advance; using the earlier word/tag boundary avoids it.
    value['prohibitAfter'] = '-'
    return value

def apply_gloss(frame):
    """Wrap long grammatical annotations at their existing tag separators."""
    content=frame['content'];offset=0;cuts=[];count=0
    for block in content['document']['stories'][0]['blocks']:
        text=''.join(r.get('sourceText',r.get('text','')) for r in block['runs'])
        positions={m.start()+i for m in re.finditer(r'\([^)]*\)',text)
                   for i,c in enumerate(m[0]) if c in ',.'}
        positions.update(i for i,c in enumerate(text) if c=='-')
        runs=[];local=0
        for run in block['runs']:
            field='sourceText' if 'sourceText' in run else 'text';value=run[field]
            inside={at-local for at in positions if local<=at<local+len(value)}
            edges=sorted({0,len(value),*(i for at in inside for i in (at,at+1))})
            for a,b in zip(edges,edges[1:]):
                part=deepcopy(run);part['runId']=uid('run');part[field]=value[a:b]
                if a in inside and b==a+1:part['languageId']=GLOSS_ID
                runs.append(part)
            local+=len(value)
        block['runs']=runs
        assert ''.join(r.get('sourceText',r.get('text','')) for r in runs)==text
        for at in positions:cuts.extend([offset+utf16_length(text[:at]),offset+utf16_length(text[:at+1])])
        offset+=utf16_length(text)+1;count+=len(positions)
    characters=[]
    for span in content['characters']:
        edges=[span['start']]+sorted({p for p in cuts if span['start']<p<span['end']})+[span['end']]
        for a,b in zip(edges,edges[1:]):characters.append(dict(start=a,end=b,attributes=deepcopy(span['attributes'])))
    content['characters']=characters
    return count

def apply(frame, units, compiler):
    content = frame['content']; offset = 0; cuts = []; count = 0
    for block, unit in zip(content['document']['stories'][0]['blocks'], units):
        text = ''.join(r.get('sourceText', r.get('text', '')) for r in block['runs'])
        positions = set()
        for token in re.findall(r'[A-Za-z_][A-Za-z_+/:\-]*', unit['analysis']):
            token = token.rstrip(':'); features = token.split('/')[-1].split(':')[1:]
            if not set(features) & FEATURES: continue
            form = compiler.word(token)[0]
            if len(form.split()[-1]) < 20: continue
            for variant in {form, compiler.maxima(form)}:
                for match in re.finditer(re.escape(variant), text):
                    tail = len(variant)
                    for feature in reversed(features):
                        if feature not in compiler.suffix: continue
                        suffix = compiler.suffix[feature][0]
                        tail -= len(suffix)
                        if feature in FEATURES and tail > 0 and variant[tail-1] in LETTERS:
                            positions.add(match.start()+tail-1)
        for at in positions:
            cuts.extend([offset+utf16_length(text[:at]), offset+utf16_length(text[:at+1])])
        runs = []; local = 0
        for run in block['runs']:
            field = 'sourceText' if 'sourceText' in run else 'text'; value = run[field]
            inside = {at-local for at in positions if local <= at < local+len(value)}
            if inside:
                boundaries = sorted({0,len(value),*(i for at in inside for i in (at,at+1))})
                for a,b in zip(boundaries,boundaries[1:]):
                    part = deepcopy(run); part['runId'] = uid('run'); part[field] = value[a:b]
                    if a in inside and b == a+1: part['languageId'] = ID
                    runs.append(part)
            else: runs.append(run)
            local += len(value)
        block['runs'] = runs
        assert ''.join(r.get('sourceText',r.get('text','')) for r in runs) == text
        offset += utf16_length(text)+1; count += len(positions)
    characters = []
    for span in content['characters']:
        edges = [span['start']]+sorted({p for p in cuts if span['start']<p<span['end']})+[span['end']]
        for a,b in zip(edges,edges[1:]):
            characters.append(dict(start=a,end=b,attributes=deepcopy(span['attributes'])))
    content['characters'] = characters
    return count
