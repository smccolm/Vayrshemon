"""Compile authored Milton constructions; retain a source-complete pending queue.

Analysis records: first[-last] physical source line | closing anchor or $ | analysis.
Only a consecutive translated prefix can be published. No automated translation.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import re
from shutil import copy2
from tempfile import TemporaryDirectory

from tools.editorial_language import EditorialLanguage
from tools.prince_working import ROOT, PARENT, HEAD, WORK as PRINCE
from tools.locke_working import WORK as LOCKE
from tools.leviathan_working import number_gloss, roman_value
from tools.shakespeare_lexicon import lexical_entries
from tools.shakespeare_endin import check_clean
from tools.unta_language import quantity, semantic_key
from vayrshemon.archive_language import base

SOURCE = ROOT/'Inputs/Sources/John Milton - Paradise Lost.txt'
BOOK = ROOT/'Saves/Paradise Lost - Four-Column Progressive Edition'
WORK = BOOK/'Working'
HOBBES = ROOT/'Saves/Leviathan - Four-Column Progressive Edition/Working'
SOURCE_HASH = '25b845899c0457b6be470106986b9c2157cc132bc23804e0c635d69c94580032'

def read(path):
    return json.loads(path.read_bytes())

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1)+'\n', encoding='utf8')

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def load_language():
    language = EditorialLanguage(PARENT/'Language')
    language.resolved_possessor_glosses = True
    extra = {}
    for folder in (PRINCE, LOCKE):
        extra.update(read(folder/'dictionary-additions.json')['entries'])
        v = read(folder/'vocabulary.json')
        language.glosses.update({k:x[1] for group in ('names','senses') for k,x in v[group].items()})
        language.glosses.update(v.get('constructionLabels', {}))
        language.glosses.update(v.get('biblicalTitles', {}))
    language.lexicon.update(extra)
    titles = {t['section']:t for t in read(ROOT/'Saves/KJV Bible v0.10-kjv.285/section-index.json')}
    for folder in (HOBBES, WORK):
        v = read(folder/'vocabulary.json')
        added, glosses = lexical_entries(language, v['names'], v['senses'], v.get('places', []))
        for key,name in v.get('biblicalTitles', {}).items():
            form = titles[name]['titleSlots']
            if name == '2 Kings':
                form = form.split(' ')[0]
            added[key] = dict(form=form,roman=language.reading(form),pos='proper',meaning='Scripture title, '+name,origin='Sealed KJV book title.')
            glosses[key] = re.sub(r'^[123] ', '', name)
        assert not set(added) & language.lexicon.keys(), set(added) & language.lexicon.keys()
        language.lexicon.update(added)
        extra.update(added)
        language.glosses.update(glosses)
        language.glosses.update(v.get('constructionLabels', {}))
    for k,e in language.lexicon.items():
        if k.startswith('kjv_') and k not in language.glosses and '_' not in k[4:]:
            language.glosses[k] = k[4:].capitalize() if e['pos']=='proper' else k[4:]
    return language, extra

def source_inventory():
    assert digest(SOURCE)==SOURCE_HASH, 'SOURCE_CHANGED_REVIEW_REQUIRED'
    lines = SOURCE.read_text(encoding='utf8').splitlines()
    rows=[]
    section='Title'
    verse=0
    mode='front'
    for i,text in enumerate(lines,1):
        if not text.strip():
            continue
        m=re.fullmatch(r'BOOK ([IVXLCDM]+)\.',text)
        kind=mode
        if m:
            section='Book '+m[1]; verse=0; mode='argument_heading'; kind='heading'
        elif text=='THE ARGUMENT.':
            mode='argument'; kind='argument_heading'
        elif mode=='argument':
            kind='argument'; mode='verse'
        elif text=='THE END.' or text.startswith('The End of the '):
            kind='colophon'
        elif text=='Paradiſe Loſt.':
            kind='booktitle'
            following=next(t for t in lines[i:] if re.fullmatch(r'BOOK ([IVXLCDM]+)\.',t))
            section='Book '+re.fullmatch(r'BOOK ([IVXLCDM]+)\.',following)[1]
        elif mode=='verse':
            verse+=1; kind='verse'
        rows.append(dict(line=i,text=text,section=section,kind=kind,verse=verse if kind=='verse' else None))
    assert len({r['section'] for r in rows if r['kind']=='heading'})==12
    return lines,rows

def build(stage, compose=False):
    lines,rows=source_inventory()
    by_line={r['line']:r for r in rows}
    language,extra=load_language()
    cursor=0; offset=0; units=[]; numbers=[]; counts=Counter()
    for path in sorted((WORK/'Analyses').glob('*.txt')):
        for record in path.read_text(encoding='utf8').splitlines():
            if not record.strip():continue
            loc,anchor,analysis=record.split(' | ')
            bounds=[int(x) for x in loc.split('-')]
            first,last=bounds[0],bounds[-1]
            assert first==rows[cursor]['line'], ('SOURCE_GAP_OR_REPEAT',loc,rows[cursor]['line'])
            included=[r for r in rows[cursor:] if r['line']<=last]
            assert included and included[-1]['line']==last
            assert len({r['section'] for r in included})==1
            text='\n'.join(lines[first-1:last])
            end=len(text) if anchor=='$' else text.index(anchor,offset)+len(anchor)
            assert end>offset and (end==len(text) or text[end].isspace()), (loc,anchor)
            source=text[offset:end]
            counts[first]+=1
            uid=f'pl.{first:05d}.{counts[first]:03d}'
            def number(m):
                value=int(m[2]);denominator=int(m[3]) if m[3] else 1
                kind='fraction' if m[3] else {'o':'ordinal','t':'times','f':'fold','':'cardinal'}[m[4]]
                notation='digits' if m[1]=='#' else 'words'
                q=quantity(value,kind,denominator,notation=notation)
                k=semantic_key(value,kind,denominator,notation=notation)
                if k not in language.lexicon:
                    language.lexicon[k]=extra[k]=dict(form=q['form'],roman=language.reading(q['spokenForm']),pos='numeral',meaning=f'Unta {kind} {value}',origin='Chart 2 Unta number system.')
                assert language.lexicon[k]['form']==q['form']
                language.glosses[k]='half' if (kind,value,denominator)==('fraction',1,2) else number_gloss(value,kind=='ordinal',notation)+({'times':' times','fold':'fold'}.get(kind,''))
                numbers.append(dict(unit=uid,value=value,denominator=denominator,kind=kind,notation=notation,form=q['form']))
                return k
            analysis=re.sub(r'([#@])(\d+)(?:/(\d+))?([otf]?)',number,analysis)
            analysis=re.sub(r'(?<!:)\b[a-z_]+\b',lambda m:'drama_native_'+m[0] if 'drama_native_'+m[0] in language.lexicon else m[0],analysis)
            row=included[0]
            ref=row['section']+' · '+(str(row['verse'])+('–'+str(included[-1]['verse']) if last!=first else '') if row['kind']=='verse' else row['kind'])
            # QTextDocument's paragraph delimiter is not a verse line break.
            # Preserve the supplied lines using native soft line separators;
            # keep the exact original substring alongside them for reconstruction.
            units.append(dict(id=uid,chapter=row['section'],reference=ref,source=source.replace('\n','\u2028'),originalSource=source,analysis=analysis,sourceLines=[first,last],sourceOffsets=[offset,end],kind=row['kind'],verseLines=[r['verse'] for r in included if r['verse'] is not None],continuesParagraph=offset>0 or row['kind']=='verse'))
            if end==len(text):
                cursor+=len(included);offset=0
            else:
                assert first==last, 'Partial anchors must refer to one prose line'
                offset=end
                while offset<len(text) and text[offset].isspace():offset+=1
    errors=[]
    for u in units:
        try:language.compile(u['analysis'])
        except ValueError as exc:errors.append((u['id'],str(exc)))
    if errors:raise ValueError(errors)
    compiled=language.compile_units(units)
    for u in compiled:
        check_clean(u,language)
        figures=Counter(int(v) for v in re.findall(r'\d+',u['source']))
        m=re.fullmatch(r'BOOK ([IVXLCDM]+)\.',u['source'])
        if m:figures[roman_value(m[1])]+=1
        assert figures==Counter(n['value'] for n in numbers if n['unit']==u['id'] and n['notation']=='digits'),u['id']
    consumed='\n'.join(r['text'] for r in rows[:cursor])
    if offset:consumed+='\n'+rows[cursor]['text'][:offset]
    assert consumed.split()==('\n'.join(u['source'] for u in compiled)).split(), 'SOURCE_PREFIX_CHANGED'
    ledger=dict(book='Paradise Lost',languageVersion='0.14',editionLabel='Four-column progressive edition',status='complete' if cursor==len(rows) else 'incomplete',sourceLabel='Milton · supplied English',sourceSha256=SOURCE_HASH,sourceWords=sum(len(r['text'].split()) for r in rows),translatedSourceWords=sum(len(u['source'].split()) for u in compiled),units=compiled,nextSourceLine=rows[cursor]['line'] if cursor<len(rows) else None,nextSourceOffset=offset)
    write(stage/'ledger.json',ledger)
    write(stage/'source-inventory.json',dict(source=SOURCE.relative_to(ROOT).as_posix(),sha256=SOURCE_HASH,rows=rows))
    write(stage/'unta-readings.json',numbers)
    write(stage/'dictionary-additions.json',dict(parentHead=HEAD,entries=extra))
    write(stage/'source-validation.json',dict(exactTranslatedPrefix=True,sourceHash=SOURCE_HASH,totalWords=ledger['sourceWords'],translatedWords=ledger['translatedSourceWords'],translatedVerseLines=sum(len(u['verseLines']) for u in compiled),pendingWords=ledger['sourceWords']-ledger['translatedSourceWords'],nextSourceLine=ledger['nextSourceLine'],nextSourceOffset=offset))
    print(len(compiled),'units;',ledger['translatedSourceWords'],'/',ledger['sourceWords'],'words; next line',ledger['nextSourceLine'],flush=True)
    if not compose:return ledger
    from tools.compose_historical_book import compose as compose_book
    snap=read(PARENT/'current-snapshot.json'); assert snap['head']==HEAD
    lang=deepcopy(snap['snapshot']['language']);sid='milton.paradise-lost.source'
    lang['sources'].append(dict(base(sid,'Paradise Lost',None,'',status='draft'),kind='other',path=SOURCE.relative_to(ROOT).as_posix(),sha256=SOURCE_HASH))
    keys={k for u in compiled for k in u['keys']}
    for k in sorted(extra.keys() & keys):
        e=extra[k];eid='milton.lex.'+k
        lang['lexicon'].append(dict(base(eid,k,sid,e['origin'],status='draft'),headword=e['form'],orthographyId='thimfora-79',pronunciation=e['roman'],ipa='',partOfSpeech=e['pos'],senses=[dict(id=eid+'.sense',definition=e['meaning'],status='draft',citations=[dict(sourceId=sid,locator=k)])],variants=[],etymology=e['origin'],exampleIds=[],audioLinks=[]))
    write(stage/'snapshot.json',dict(head='working-language-'+sha256(json.dumps(lang,sort_keys=True).encode()).hexdigest(),snapshot=dict(language=lang)))
    target=stage/(BOOK.name+'.vay');prior=BOOK/target.name;reuse=None
    if prior.exists():
        assert digest(prior)==read(WORK/'layout-validation.json')['sha256'], 'MANUAL_EDIT_REQUIRES_MERGE'
        assert read(WORK/'ledger.json')['translatedSourceWords']<=ledger['translatedSourceWords']
        previous=stage/'previous';previous.mkdir();reuse=previous/prior.name
        copy2(prior,reuse)
        for name in ('layout-validation.json','page-index.json'):copy2(WORK/name,previous/name)
    # Keep the source witness's illegible-word brackets as supplied. As in the
    # Locke edition, embed a supported font for signs absent from the body face.
    source_signs=Path(os.environ['WINDIR'])/'Fonts/malgun.ttf' if any('〈' in u['source'] or '〉' in u['source'] for u in compiled) else None
    compose_book(stage/'ledger.json',stage/'snapshot.json',target,reuse=reuse,source_fallback=source_signs)
    proof=read(stage/'layout-validation.json')
    assert proof['allFourColumnsMatchLedger'] and proof['saveReopenIdentical'] and not proof['verticalOverset'] and not proof['missingGlyphs']
    if prior.exists():assert digest(prior)==read(WORK/'layout-validation.json')['sha256']
    for name in ('ledger.json','source-inventory.json','unta-readings.json','dictionary-additions.json','source-validation.json','layout-validation.json','page-index.json','numbering-validation.json','snapshot.json'):
        copy2(stage/name,WORK/(name+'.new'));(WORK/(name+'.new')).replace(WORK/name)
    (WORK/'Proofs').mkdir(exist_ok=True)
    for p in (stage/'Proofs').glob('*.png'):copy2(p,WORK/'Proofs'/p.name)
    copy2(target,BOOK/(target.name+'.new'));(BOOK/(target.name+'.new')).replace(prior)
    print('Installed',proof['pages'],'pages;',proof['sha256'],flush=True)
    return ledger

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--compose',action='store_true');args=cli.parse_args()
    with TemporaryDirectory(dir=ROOT/'.local') as temp:build(Path(temp),args.compose)
