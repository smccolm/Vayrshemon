"""Build Hobbes's facing-spread edition from authored, source-anchored constructions."""
from collections import Counter
from hashlib import sha256
import argparse
import json
import re
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory

from tools.leviathan_source import BOOK, WORK, ROOT, SOURCE
from tools.editorial_language import EditorialLanguage
from tools.prince_working import PARENT, HEAD, WORK as PRINCE
from tools.locke_working import WORK as LOCKE
from tools.shakespeare_lexicon import lexical_entries
from tools.shakespeare_endin import check_clean
from tools.unta_language import quantity, semantic_key
from vayrshemon.archive_language import base


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=1)+'\n',encoding='utf8')

def roman_value(token):
    weights = dict(I=1, V=5, X=10, L=50, C=100, D=500, M=1000)
    values = [weights[c] for c in token]
    return sum(-v if i+1 < len(values) and v < values[i+1] else v for i,v in enumerate(values))

def number_gloss(n, ordinal, notation):
    if notation == 'digits':
        return str(n) + ('(ord.)' if ordinal else '')
    small = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
    tens = 'zero ten twenty thirty forty fifty sixty seventy eighty ninety'.split()
    def cardinal(v):
        if v < 20:
            return small[v]
        if v < 100:
            return tens[v//10] + ('-'+small[v%10] if v%10 else '')
        for scale, name in ((10**9,'billion'), (10**6,'million'), (1000,'thousand'), (100,'hundred')):
            if v >= scale:
                return cardinal(v//scale) + ' ' + name + (' '+cardinal(v%scale) if v%scale else '')
    word = cardinal(n)
    if not ordinal:
        return word
    endings = {'one':'first','two':'second','three':'third','five':'fifth','eight':'eighth','nine':'ninth','twelve':'twelfth'}
    return re.sub(r'[a-z]+$', lambda m: endings.get(m[0], m[0][:-1]+'ieth' if m[0].endswith('y') else m[0]+'th'), word)


def publish(stage, target):
    files = [('ledger.json', WORK), ('page-index.json', WORK), ('unta-readings.json', WORK),
             ('layout-validation.json', WORK), (target.name, BOOK)]
    with TemporaryDirectory(dir=BOOK) as folder:
        temp = Path(folder)
        for name, parent in files:
            copy2(stage/name, temp/name)
            if (parent/name).is_file():
                copy2(parent/name, temp/('old-'+name))
        installed = []
        try:
            for name, parent in files:
                (temp/name).replace(parent/name)
                installed.append(parent/name)
        except OSError:
            for dest in reversed(installed):
                backup = temp/('old-'+dest.name)
                if backup.is_file():
                    backup.replace(dest)
                else:
                    dest.unlink()
            raise


def build(stage, compose=False):
    rows=read(WORK/'english-blocks.json')['rows']
    language=EditorialLanguage(PARENT/'Language')
    language.resolved_possessor_glosses = True
    extra={}
    for folder in (PRINCE,LOCKE):
        extra.update(read(folder/'dictionary-additions.json')['entries'])
        vocab=read(folder/'vocabulary.json')
        language.glosses.update(vocab.get('constructionLabels',{}))
        language.glosses.update({k:v[1] for group in ('names','senses') for k,v in vocab[group].items()})
        language.glosses.update(vocab.get('biblicalTitles',{}))
    language.lexicon.update(extra)
    for key,entry in language.lexicon.items():
        if key.startswith('kjv_') and key not in language.glosses and '_' not in key[4:]:
            language.glosses[key]=key[4:].capitalize() if entry['pos']=='proper' else key[4:]
    vocab=read(WORK/'vocabulary.json')
    added,glosses=lexical_entries(language,vocab['names'],vocab['senses'],vocab['places'])
    titles_path = ROOT/'Saves/KJV Bible v0.10-kjv.285/section-index.json'
    assert sha256(titles_path.read_bytes()).hexdigest() == '4ee26d924f3946ab0c3be90192e51c02a3bd19b691423b302cf3df3d4f8922a5'
    titles = {t['section']: t for t in read(titles_path)}
    for key, name in vocab.get('biblicalTitles', {}).items():
        t = titles[name]
        # A numeral printed separately in the source takes an explicit Unta token.
        form = t['titleSlots'].split(' ')[0] if name == '2 Kings' else t['titleSlots']
        added[key] = dict(form=form, roman=language.reading(form), pos='proper',
                          meaning='Scripture title, '+name, origin='Sealed KJV book title.')
        glosses[key] = re.sub(r'^[123] ', '', name)
    assert not set(added) & language.lexicon.keys()
    extra.update(added)
    language.lexicon.update(added)
    language.glosses.update(glosses)
    language.glosses.update(vocab.get('constructionLabels', {}))
    authored={}
    for path in sorted((WORK/'Analyses').glob('*.txt')):
        for entry in path.read_text(encoding='utf8').splitlines():
            if entry.strip():
                key,anchor,analysis=entry.split(' | ')
                authored.setdefault(key,[]).append((anchor,analysis))
    headings=(WORK/'chapter-titles.txt').read_text(encoding='utf8').splitlines()
    assert len(headings)==47
    refs=read(ROOT/'Saves/KJV Bible v0.10-kjv.285/complete-translation-ledger.json')
    bible={u['reference']:u for u in refs['units']}
    units=[]
    numbers=[]
    used_rows=set()
    for row in rows:
        key,text=row['id'],row['text']
        parts=authored.get(key)
        if parts is None:
            toc=re.fullmatch(r'Chap\. (\d+)\. .*? Page\. (\d+)', text)
            chap=re.fullmatch(r'Chap\. ([IVXLCDM]+)\. .*',text)
            if toc:
                n,page=toc.groups()
                parts=[('$',f'chapter_book #{n}. {headings[int(n)-1]}. book_leaf #{page}.')]
            elif chap and row['kind']=='heading':
                n=int(row['section'].split()[1])
                if n>1 and not any(r['id'] in authored for r in rows if r['section']==row['section']):
                    break
                parts=[('$',f'chapter_book #{n}. {headings[n-1]}.')]
            else:
                break
        pos=0
        for j,(anchor,analysis) in enumerate(parts,1):
            if anchor == '$':
                end = len(text)
            else:
                start = text.find(anchor, pos)
                if start == -1:
                    raise ValueError(f'{key}.{j}: source anchor not found: {anchor!r}')
                end = start + len(anchor)
            assert end>pos and (end==len(text) or text[end].isspace()),(key,anchor)
            source=text[pos:end]
            uid=f'{key}.{j}'
            # Inherited Bible constructions can already contain keyed numbers.
            # Validate those readings as well as the authored @/# notation.
            for m in re.finditer(r'\bunta_(cardinal|ordinal|times|fold|fraction)_([a-j]+)_over_([a-j]+)(_digits)?\b', analysis):
                decode = lambda word: int(word.translate(str.maketrans('abcdefghij', '0123456789')))
                value, denominator = decode(m[2]), decode(m[3])
                notation = 'digits' if m[4] else 'words'
                q = quantity(value, m[1], denominator, notation=notation)
                assert language.lexicon[m[0]]['form'] == q['form'], m[0]
                numbers.append(dict(unit=uid, value=value if denominator == 1 else q['value'],
                                    kind=m[1], notation=notation, form=q['form'],
                                    gloss=language.glosses.get(m[0], q['value'])))
            def number(m):
                value=int(m[2])
                kind='ordinal' if m[3] else 'cardinal'
                notation='digits' if m[1]=='#' else 'words'
                q=quantity(value,kind,notation=notation)
                k=semantic_key(value,kind,notation=notation)
                if k not in language.lexicon:
                    language.lexicon[k]=extra[k]=dict(form=q['form'],roman=language.reading(q['spokenForm']),
                        pos='numeral',meaning=f'Unta {kind} {value}',origin='Chart 2 Unta number system.')
                language.glosses[k]=number_gloss(value, bool(m[3]), notation)
                assert language.lexicon[k]['form']==q['form']
                numbers.append(dict(unit=uid,value=value,kind=kind,notation=notation,form=q['form'],gloss=language.glosses[k]))
                return k
            analysis=re.sub(r'([#@])(\d+)(o?)',number,analysis)
            analysis=re.sub(r'(?<!:)\b[a-z_]+\b',lambda m: 'drama_native_'+m[0] if 'drama_native_'+m[0] in language.lexicon else m[0],analysis)
            units.append(dict(id=uid,chapter=row['section'],reference=row['section']+' · '+uid,source=source,
                              sourceBlock=key,sourceOffsets=[pos,end],analysis=analysis,continuesParagraph=j>1))
            if 'tableId' in row:
                units[-1].update({k:row[k] for k in ('tableId','parentNode','hierarchyDepth','hierarchyPrefix')})
            pos=end
            while pos<len(text) and text[pos].isspace():pos+=1
        assert pos==len(text),(key,text[pos:])
        used_rows.add(key)
    assert not (authored.keys()-used_rows),authored.keys()-used_rows
    unknown={}
    for u in units:
        for k in re.findall('[a-z_]+',re.sub(':[a-z]+','',u['analysis'])):
            if k not in language.lexicon and k not in language.possessors:
                unknown.setdefault(k,u['id'])
    if unknown:raise ValueError(f'Unknown keys: {unknown}')
    errors=[]
    for u in units:
        try:language.compile(u['analysis'])
        except ValueError as err:errors.append((u['id'],str(err),u['analysis']))
    if errors:raise ValueError('\n'.join(map(str,errors)))
    compiled=language.compile_units(units)
    for u in compiled:
        u['gloss'] = re.sub(r'\b(ourpl|ourone|mypl)-', lambda m: {
            'ourpl':'our(pl.)-', 'ourone':'our(coll.)-', 'mypl':'my(pl.)-'
        }[m[1]], u['gloss'])
        check_clean(u,language)
        figures=Counter(int(v) for v in re.findall(r'\d+',u['source']))
        target=Counter(r['value'] for r in numbers if r['unit']==u['id'] and r['notation']=='digits')
        heading = re.match(r'(?:Part|Chap)\.?\s+([IVXLCDM]+)\.',u['source'])
        if heading:
            figures[roman_value(heading[1])] += 1
        assert figures==target,(u['id'],figures,target)
    by_id={u['id']:u for u in compiled}
    for cite in vocab['sealedReadings']:
        if cite['unit'] in by_id:
            assert cite['native'] in bible[cite['reference']]['text']
            assert cite['native'].casefold() in by_id[cite['unit']]['text'].casefold(),cite
    stage.mkdir(parents=True,exist_ok=True)
    digest=lambda p:sha256(p.read_bytes()).hexdigest()
    prose_complete = len(used_rows) == len(rows)
    ledger=dict(book='Leviathan',languageVersion='0.14',editionLabel='Four-column progressive edition',
                status='complete' if prose_complete else 'incomplete',
                omittedFigures=[], restoredFigures=['knowledge-foldout'],
                sourceLabel='Hobbes · English',sourceSha256=digest(SOURCE),
                readingTextSha256=digest(WORK/'English reading text.txt'),sourceWords=sum(len(r['text'].split()) for r in rows),
                translatedSourceWords=sum(len(u['source'].split()) for u in compiled),units=compiled,
                nextBlock=next((r['id'] for r in rows if r['id'] not in used_rows),None))
    write(stage/'ledger.json',ledger)
    write(stage/'unta-readings.json',numbers)
    print(len(compiled),'units;',ledger['translatedSourceWords'],'words; next:',ledger['nextBlock'],flush=True)
    if not compose:return
    from tools.compose_historical_book import compose as compose_book
    snap=read(PARENT/'current-snapshot.json')
    assert snap['head']==HEAD
    lang=snap['snapshot']['language']
    sid='hobbes.1651.source'
    lang['sources'].append(dict(base(sid,'Leviathan',None,'',status='draft'),kind='other',path=SOURCE.relative_to(ROOT).as_posix(),sha256=digest(SOURCE)))
    keys={k for u in compiled for k in u['keys']}
    for k in sorted(extra.keys() & keys):
        e=extra[k]; eid='hobbes.lex.'+k
        lang['lexicon'].append(dict(base(eid,k,sid,e['origin'],status='draft'),headword=e['form'],orthographyId='thimfora-79',
            pronunciation=e['roman'],ipa='',partOfSpeech=e['pos'],senses=[dict(id=eid+'.sense',definition=e['meaning'],status='draft',
            citations=[dict(sourceId=sid,locator=k)])],variants=[],etymology=e['origin'],exampleIds=[],audioLinks=[]))
    write(stage/'snapshot.json',dict(head='working-language-'+sha256(json.dumps(lang,sort_keys=True).encode()).hexdigest(),snapshot=dict(language=lang)))
    target=stage/(BOOK.name+'.vay')
    prior=BOOK/target.name
    reuse=None
    if prior.is_file():
        previous=stage/'previous'
        previous.mkdir()
        reuse=previous/prior.name
        copy2(prior,reuse)
        for name in ('layout-validation.json','page-index.json'):
            copy2(WORK/name,previous/name)
    compose_book(stage/'ledger.json',stage/'snapshot.json',target,reuse=reuse)
    receipt=read(stage/'layout-validation.json')
    assert receipt['allFourColumnsMatchLedger'] and receipt['saveReopenIdentical'] and not receipt['verticalOverset'] and not receipt['missingGlyphs']
    assert digest(target)==receipt['sha256']
    if prior.exists():
        assert digest(prior)==read(WORK/'layout-validation.json')['sha256']
        assert read(WORK/'ledger.json')['translatedSourceWords'] <= ledger['translatedSourceWords']
    publish(stage,target)
    print('Installed',receipt['pages'],'pages and',receipt['units'],'aligned passages.',flush=True)


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--compose',action='store_true')
    args=cli.parse_args()
    with TemporaryDirectory(dir=ROOT/'.local') as tmp:
        build(Path(tmp),args.compose)
