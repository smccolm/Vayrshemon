"""Compile hand-authored Boyle analyses against corrected source paragraphs."""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
from shutil import copy2
from tempfile import TemporaryDirectory

from tools.paradise_lost_working import ROOT, PARENT, HEAD, read, write, digest, load_language
from tools.shakespeare_lexicon import lexical_entries
from tools.shakespeare_endin import check_clean
from tools.unta_language import quantity, semantic_key
from tools.leviathan_working import number_gloss
from vayrshemon.archive_language import base

TITLE = 'The Sceptical Chymist'
BOOK = ROOT/'Saves'/(TITLE+' - Four-Column Progressive Edition')
WORK = BOOK/'Working'
SOURCE = ROOT/'Inputs/Sources'/('Robert Boyle - '+TITLE+'.txt')
HASH = '1eb152f3470b2f45b0d187d5d1100263caba69156453422ac903129f8d33dab0'
SECTIONS = {1:'Title',4:'Preface',24:'First dialogue',64:'Second title',
            70:'Part I',162:'Part II',238:'Part III',280:'Part IV',346:'Part V',
            438:'Part VI',560:'Conclusion',602:'Publisher’s notice'}


def inventory():
    assert digest(SOURCE)==HASH, 'Source file changed'
    lines=SOURCE.read_text(encoding='utf-8-sig').replace('ſ','s').splitlines()
    original_nonblank={n for n,t in enumerate(lines,1) if t.strip()}
    grouped=defaultdict(list)
    for change in read(WORK/'corrections.json'):
        grouped[change['line']].append(change)
    for n,changes in grouped.items():
        limit=len(lines[n-1])
        for c in sorted(changes,key=lambda c:-c['start']):
            a,b=c['start'],c['end']
            assert b<=limit and lines[n-1][a:b]==c['before'], c
            lines[n-1]=lines[n-1][:a]+c['after']+lines[n-1][b:]
            limit=a
    order=[n for n,t in enumerate(lines,1) if t.strip() and n not in (594,596,598,600,508)]
    assert lines[271].endswith('imitate Nature.') and lines[273].startswith('But,')
    order.insert(order.index(274),596)
    lines[505]+=' '+lines[507]
    section=None; rows=[]
    for n in order:
        section=SECTIONS.get(n,section)
        rows.append(dict(line=n,section=section,text=' '.join(lines[n-1].split()).replace('VV','W')))
    assert set(order)|{508,594,598,600}==original_nonblank
    assert len(order)==len(set(order)) and not any('〈' in r['text'] for r in rows)
    assert order[order.index(596)-1:order.index(596)+2]==[272,596,274]
    return rows


def build(stage, publish):
    rows=inventory()
    language,inherited=load_language()
    v=read(WORK/'vocabulary.json')
    added,labels=lexical_entries(language,v['names'],v['senses'])
    assert not added.keys() & language.lexicon.keys()
    language.lexicon.update(added);language.glosses.update(labels)
    extra=inherited|added
    cursor=0;offset=0;units=[];used_numbers=[];counts=Counter()
    def number(match):
        value=int(match[2]);denominator=int(match[3] or 1)
        kind='fraction' if match[3] else ('ordinal' if match[4] else 'cardinal')
        notation='digits' if match[1]=='#' else 'words'
        k=semantic_key(value,kind,denominator,notation=notation)
        q=quantity(value,kind,denominator,notation=notation)
        if k not in language.lexicon:
            extra[k]=language.lexicon[k]=dict(form=q['form'],roman=language.reading(q['spokenForm']),pos='numeral',meaning=f'Unta {kind} {value}',origin='Chart 2 Unta.')
        assert q['form']==language.lexicon[k]['form']
        if kind=='fraction':
            fraction_names={(1,2):'half',(1,3):'one-third',(1,4):'one-quarter'}
            language.glosses[k]=fraction_names.get((value,denominator),f'{value}/{denominator}')
        else:
            language.glosses[k]=number_gloss(value,kind=='ordinal',notation)
        used_numbers.append(dict(unit=uid,value=value,denominator=denominator,kind=kind,notation=notation,key=k))
        return k
    for path in sorted((WORK/'Analyses').glob('*.txt')):
        for record in path.read_text(encoding='utf-8-sig').splitlines():
            if not record.strip():continue
            pos,anchor,analysis=record.split(' | ')
            n=int(pos);r=rows[cursor];txt=r['text']
            assert n==r['line'],(pos,r['line'])
            end=len(txt) if anchor=='$' else txt.index(anchor,offset)+len(anchor)
            assert end>offset and (end==len(txt) or txt[end].isspace()),(n,anchor)
            counts[n]+=1;uid=f'boyle.{n:03d}.{counts[n]:03d}'
            analysis=re.sub(r'([@#])(\d+)(?:/(\d+))?(o?)',number,analysis)
            analysis=re.sub(r'(?<!:)\b[a-z_]+\b',lambda m:'drama_native_'+m[0] if 'drama_native_'+m[0] in language.lexicon else m[0],analysis)
            units.append(dict(id=uid,chapter=r['section'],reference=f'{r["section"]} · {n}.{counts[n]}',source=txt[offset:end],analysis=analysis,sourceLine=n,sourceOffsets=[offset,end],continuesParagraph=bool(offset)))
            if end==len(txt):cursor+=1;offset=0
            else:offset=end+1
    compiled=language.compile_units(units)
    for u in compiled:check_clean(u,language)
    full='\n\n'.join(r['text'] for r in rows)
    consumed=' '.join(u['source'] for u in units)
    expected=' '.join([r['text'] for r in rows[:cursor]]+([rows[cursor]['text'][:offset].strip()] if offset else []))
    assert consumed==expected
    ledger=dict(book=TITLE,languageVersion='0.14',editionLabel='Four-column progressive edition',status='complete' if cursor==len(rows) else 'incomplete',sourceLabel='Boyle · corrected 1661 text',sourceSha256=HASH,sourceWords=len(full.split()),translatedSourceWords=len(consumed.split()),units=compiled,nextSourceLine=rows[cursor]['line'] if cursor<len(rows) else None,nextSourceOffset=offset)
    write(stage/'ledger.json',ledger);write(stage/'unta-readings.json',used_numbers)
    write(stage/'dictionary-additions.json',dict(parentHead=HEAD,entries=added))
    write(stage/'source-inventory.json',dict(sourceSha256=HASH,rows=rows))
    write(stage/'source-validation.json',dict(
        status=ledger['status'],totalCorrectedWords=ledger['sourceWords'],
        translatedWords=ledger['translatedSourceWords'],remainingWords=ledger['sourceWords']-ledger['translatedSourceWords'],
        consecutiveSourcePrefix=True,nextSourceLine=ledger['nextSourceLine'],nextSourceOffset=offset,
        relocatedSheet=dict(sourceLine=596,after=272,before=274),
        joinedParagraphs=[506,508],printerInstructionsExcluded=[594,598,600],
        suppliedSourceSha256=HASH,correctedTextSha256=sha256((full+'\n').encode()).hexdigest()))
    (stage/'corrected-source.txt').write_text(full+'\n',encoding='utf8',newline='\n')
    print(f'{len(units)} units, {ledger["translatedSourceWords"]} / {ledger["sourceWords"]} words',flush=True)
    if not publish:return
    from tools.compose_historical_book import compose
    snapshot=read(PARENT/'current-snapshot.json')
    assert snapshot['head']==HEAD
    lang=deepcopy(snapshot['snapshot']['language']);sid='boyle.sceptical-chymist.source'
    lang['sources'].append(dict(base(sid,TITLE,None,'',status='draft'),kind='other',path=SOURCE.relative_to(ROOT).as_posix(),sha256=HASH))
    keys={k for u in compiled for k in u['keys']}
    for k in sorted(keys & extra.keys()):
        e=extra[k];eid='boyle.lex.'+k
        lang['lexicon'].append(dict(base(eid,k,sid,e['origin'],status='draft'),headword=e['form'],orthographyId='thimfora-79',pronunciation=e['roman'],ipa='',partOfSpeech=e['pos'],senses=[dict(id=eid+'.sense',definition=e['meaning'],status='draft',citations=[dict(sourceId=sid,locator=k)])],variants=[],etymology=e['origin'],exampleIds=[],audioLinks=[]))
    write(stage/'snapshot.json',dict(head='working-language-'+sha256(json.dumps(lang,sort_keys=True).encode()).hexdigest(),snapshot=dict(language=lang)))
    name=BOOK.name+'.vay';prior=BOOK/name;reuse=None
    previous_hash=digest(prior) if prior.exists() else None
    if previous_hash:
        assert previous_hash==read(WORK/'layout-validation.json')['sha256']
        assert read(WORK/'ledger.json')['translatedSourceWords']<=ledger['translatedSourceWords']
        previous=stage/'previous';previous.mkdir();reuse=previous/name;copy2(prior,reuse)
        for f in ('layout-validation.json','page-index.json'):copy2(WORK/f,previous/f)
    proof=compose(stage/'ledger.json',stage/'snapshot.json',stage/name,reuse=reuse)
    assert proof['allFourColumnsMatchLedger'] and proof['saveReopenIdentical'] and not proof['missingGlyphs'] and not proof['verticalOverset']
    assert (digest(prior) if prior.exists() else None)==previous_hash
    for p in sorted(stage.glob('*')):
        if p.is_file() and p.name!=name:
            temp=WORK/(p.name+'.new');copy2(p,temp);temp.replace(WORK/p.name)
    proofs = WORK/'Proofs'
    proofs.mkdir(exist_ok=True)
    staged_proofs = {p.name: p for p in (stage/'Proofs').glob('page-*.png')}
    for name_, path in staged_proofs.items():
        copy2(path, proofs/name_)
    for path in proofs.iterdir():
        if re.fullmatch(r'page-\d+\.png', path.name) and path.name not in staged_proofs:
            path.unlink()
    temp=BOOK/(name+'.new');copy2(stage/name,temp);temp.replace(prior)
    print('Installed',proof['pages'],'pages',flush=True)


if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('--compose',action='store_true')
    with TemporaryDirectory(dir=ROOT/'.local') as folder:build(Path(folder),cli.parse_args().compose)
