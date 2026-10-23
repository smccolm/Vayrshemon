"""A separate color review copy, never an in-place historical text migration.

The archival DOCX/test-seven fixture remains unchanged. This copy explicitly
adopts the 79/81/80 family requested for color proofs. Private text stays local.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
from fontTools.ttLib import TTFont
from tools.parallel_translation_fixture import local_material,compose,definition


def layered_material(root,call):
    root=Path(root);spec=json.loads((root/'data/formatting/parallel-translation-layered.json').read_text())
    evidence=spec['mappingEvidence']
    if hashlib.sha256((root/'Inputs'/evidence['path']).read_bytes()).hexdigest()!=evidence['sha256']:
        raise ValueError('LAYERED_REVIEW_MAPPING_EVIDENCE_CHANGED')
    pairs,_=local_material(root,call)
    fonts={role:call('fonts.load',path=str(root/'Inputs'/item['path']),sha256=item['sha256'])['fontId'] for role,item in spec['fonts'].items()}
    master_path=root/'Inputs'/spec['fonts']['outline']['path']
    with TTFont(master_path) as font: cmap=font.getBestCmap()
    old_path=root/'Inputs'/definition(root)['localFixture']['fonts'][0]['path']
    with TTFont(old_path) as font: old_cmap=font.getBestCmap()
    result=[];changes=[];offset=0
    for pair in pairs:
        original=''.join(r['text'] for r in pair['original']);converted=[]
        for ch in original:
            mapped=chr(spec['scalarMap'].get(str(ord(ch)),ord(ch)))
            if ord(mapped) not in cmap and mapped not in '\n\r': raise ValueError('LAYERED_REVIEW_UNMAPPED_SCALAR: '+hex(ord(ch)))
            if mapped==ch and old_cmap.get(ord(ch))!=cmap.get(ord(ch)): raise ValueError('LAYERED_REVIEW_GLYPH_NAME_CHANGED: '+hex(ord(ch)))
            if mapped!=ch: changes.append(dict(offset=offset,sourceScalar=ord(ch),targetScalar=ord(mapped)))
            converted.append(mapped);offset+=1
        offset+=1
        result.append(dict(original=[dict(text=''.join(converted),font='Thimfora 79')],translation=pair['translation']))
    provenance=dict(profile=spec['profileId'],revision=spec['revision'],source=definition(root)['localFixture'],
        sourceTextSha256=hashlib.sha256('\n'.join(''.join(r['text'] for r in p['original']) for p in pairs).encode()).hexdigest(),
        changes=changes,offsetUnit='unicode-scalar',sourceFilesModified=False,
        note='Review copy adopts the 79/81/80 typeface. It is not the unchanged historical font/run fixture.',fonts=spec['fonts'],mappingEvidence=evidence)
    return result,fonts,provenance


def compose_layered(root,call):
    pairs,fonts,provenance=layered_material(root,call)
    style=deepcopy(definition(root)['referenceTypography'])
    # The canonical family's glyphs occupy less of the em than test seven.
    # Use a separately recorded review size, retaining the approved page frames.
    style['original']['size']=50;style['previewMode']='color'
    ids,text=compose(root,call,pairs,{'Thimfora 79':fonts['outline']},typography=style)
    call('paint.bind',fontId=fonts['outline'],glowFontId=fonts['glow'],interiorFontId=fonts['interior'],kind='layered',enabled=True)
    provenance['typography']=style
    return ids,text,provenance
