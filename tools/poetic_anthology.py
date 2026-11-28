"""Compose the complete chronological Poetic Anthology from reviewed source lines."""
import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from html import escape
import json
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from shutil import copy2

from tools.compose_historical_book import compose
from tools.dampier_working import ROOT, WORK as DAMPIER, source_language
from tools.leviathan_working import number_gloss
from tools.paradise_lost_working import read, write, digest
from tools.shakespeare_endin import check_clean
from tools.unta_language import quantity, semantic_key
from vayrshemon.archive_language import base

TITLE = 'Gimōvīv lilangsōlum’na'
BOOK = ROOT / 'Saves/Poetic Anthology - Four-Column Progressive Edition'
WORK = BOOK / 'Working'
TARGET = BOOK / (TITLE + ' - Four-Column Progressive Edition.vay')
SOURCE_FONTS = ROOT / 'data/document-fonts'
TITLE_ANALYSIS = 'anthology_book drama_native_poet:adj'
DATES = {
    'peach':'approx_date #11o to #7o century_period:pl common_era before',
    'psalm':'approx_date #6o century_period common_era before',
    'hate':'#1o century_period common_era before',
    'hearts':'approx_date #1o century_period common_era before to #2o century_period common_era:loc',
    'shine':'#1o to #2o century_period common_era:loc',
    'dawn':'#8o century_period beginning:loc common_era:loc',
    'round':'#13o century_period middle:loc',
}
BREAK = '\u2028'


def build_material():
    lang, inherited, voyage = source_language()
    lang.glosses['kjv_place_site'] = 'place'
    # The latest voyage compiler inherits the accumulated book-specific keys.
    defs = {}
    for line in (WORK/'vocabulary.txt').read_text(encoding='utf8').splitlines():
        if not line.strip():
            continue
        key, roots, label, pos, meaning = line.split(' | ')
        if key in lang.lexicon:
            raise ValueError('Duplicate anthology key: ' + key)
        direct = roots.startswith('=')
        keys = [] if direct else roots.split()
        form = roots[1:] if direct else ''.join(lang.lexicon[k]['form'] for k in keys)
        if not set(form) <= lang.letters | set(' ’'):
            raise ValueError((key, form))
        origin = ('Authored sound or adapted cultural word.' if direct else
                  'Anthology sense formed from ' + ' + '.join(keys) + '.')
        defs[key] = dict(form=form, roman=lang.reading(form), pos=pos, meaning=meaning,
                         origin=origin, derivationKeys=keys, gloss=label)
        lang.lexicon[key] = defs[key]
        lang.glosses[key] = label
    quantities = []
    def analyze(a, uid):
        def make_number(m):
            value, denom = int(m[2]), int(m[3] or 1)
            kind = 'fraction' if m[3] else 'ordinal' if m[4] else 'cardinal'
            notation = 'digits' if m[1]=='#' else 'words'
            q = quantity(value,kind,denom,notation=notation)
            key = semantic_key(value,kind,denom,notation=notation)
            if key not in lang.lexicon:
                defs[key] = dict(form=q['form'], roman=lang.reading(q['spokenForm']), pos='numeral',
                                 meaning=f'Unta {kind} {value}/{denom}',origin='Chart 2 Unta.')
                lang.lexicon[key] = defs[key]
            assert lang.lexicon[key]['form']==q['form']
            lang.glosses[key] = 'one-quarter' if denom==4 else number_gloss(value,kind=='ordinal',notation)
            quantities.append(dict(unit=uid,value=value,denominator=denom,kind=kind,notation=notation,form=q['form']))
            return key
        a = re.sub(r'([@#])(\d+)(?:/(\d+))?(o?)',make_number,a)
        a = re.sub(r'(?<!:)\b[a-z_]+\b',lambda m:'drama_native_'+m[0] if 'drama_native_'+m[0] in lang.lexicon else m[0],a)
        return a
    def unit(uid, section, reference, src, a, **fields):
        a = analyze(a,uid)
        try:
            turns = a.split(' || ')
            parts = [lang.compile(turn, initial=i == 0 or turns[i-1].endswith(('.', '!', '?')))
                     for i, turn in enumerate(turns)]
            c = {field: BREAK.join(p[field] for p in parts) for field in ('text','gloss')}
            c['gloss'] = c['gloss'].replace('ourpl-', 'our(pl.)-')
            c['keys'] = [key for p in parts for key in p['keys']]
        except ValueError as e:
            raise ValueError(f'{uid} {a}: {e}') from e
        return dict(id=uid,chapter=section,reference=reference,source=src,analysis=a,**c,**fields)

    works = read(WORK/'works.json')
    assert [r['sort'] for r in works] == sorted(r['sort'] for r in works)
    constructions = {}
    for line in (WORK/'constructions.txt').read_text(encoding='utf8').splitlines():
        if not line.strip():
            continue
        if line.startswith('['):
            section = line[1:-1]
            assert section not in constructions
            constructions[section]=[]
        else:
            constructions[section].append(line.split(' | '))
    units, contents, sources = [], [], {}
    title = unit('front.title','Title','Poetic Anthology','Poetic Anthology',TITLE_ANALYSIS)
    assert lang.reading(title['text']) == TITLE
    title['gloss'] = 'anthology{many-write} · poet(adj.)'
    sub = unit('front.subtitle','Title','Poems and Songs','Poems and Songs','milton_poem:pl and song:pl')
    toc = unit('contents.title','Contents','Contents','Contents','catalogue')
    for r in works:
        k,t = r['id'],r['title']
        lines = (WORK/'Sources'/f'{k}.txt').read_text(encoding='utf8').splitlines()
        assert lines and all(x.strip() for x in lines)
        sources[k] = dict(lines=len(lines),sha256=digest(WORK/'Sources'/f'{k}.txt'))
        a = r.get('dateAnalysis') or DATES.get(k, '#'+str(r['sort']))
        if 'witness' in r['date'].lower() and 'witness_text' not in a: a += ' witness_text'
        if 'release' in r['date'].lower() and 'publish:psv:pa' not in a: a += ' publish:psv:pa'
        display = t+(BREAK+r['originalTitle'] if r['originalTitle'] else '')
        title_analysis = r['titleAnalysis']
        if k == 'psalm':
            title_analysis += ' || kjv_psalm #137'
        if k == 'hearts':
            title_analysis += ' || short:m anthology_book #40'
        units.append(unit(k+'.title',t,t,display,title_analysis,keepWithOpening=True))
        units.append(unit(k+'.date',t,t+' · '+r['date'],r['date'],a))
        contents.append((r, a))
        used=[]
        inherited_path = WORK/(k+'-inherited.json')
        if inherited_path.exists():
            for row in read(inherited_path):
                start=len(used)+1
                end=len(used)+row['lines']
                used.extend(range(start,end+1))
                source=BREAK.join(lines[start-1:end])
                if 'text' in row:
                    units.append(dict(id=f'{k}.{start}',chapter=t,reference=f'{t} · {start}',source=source,
                                      lines=[start,end],originalSource='\n'.join(lines[start-1:end]),inheritedUnit=row['id'],
                                      **{f:row[f] for f in ('analysis','text','gloss','keys')}))
                else:
                    units.append(unit(f'{k}.{start}',t,f'{t} · {start}',source,row['analysis'],
                                      lines=[start,end],originalSource='\n'.join(lines[start-1:end])))
        else:
            for record in constructions[k]:
                span,analysis,*reading=record
                limits=list(map(int,span.split('-'))); start,end=limits[0],limits[-1]
                assert start==len(used)+1 and start<=end<=len(lines),(k,span)
                used.extend(range(start,end+1))
                original='\n'.join(lines[start-1:end]); source=original.replace('\n',BREAK)
                if reading: source+=BREAK+reading[0]
                units.append(unit(f'{k}.{start}',t,f'{t} · {span}',source,analysis,lines=[start,end],
                                  originalSource=original,englishReading=reading[0] if reading else None))
        assert used == list(range(1,len(lines)+1)),k
        assert '\n'.join(u['originalSource'] for u in units if u['id'].startswith(k+'.') and 'lines' in u)=='\n'.join(lines)
    for u in units:
        if 'inheritedUnit' not in u: check_clean(u,lang)
    def assembled(page_numbers):
        entries=[]
        for r,d in contents:
            k=r['id']; folio=page_numbers.get(k,1)
            # One native paragraph per entry, with the date and Unta folio directly beneath the title.
            head=unit('contents.'+k,'Contents','Contents · '+r['title'],r['title'],r['titleAnalysis'])
            date=unit('contents.'+k+'.date','Contents','Contents',r['date'],d)
            page=unit('contents.'+k+'.folio','Contents','Contents','p. '+str(folio),'book_leaf #'+str(folio))
            for field in ('text','gloss','source'):
                head[field]+=BREAK+date[field]+' · '+page[field]
            head['analysis']+=' || '+date['analysis']+' || '+page['analysis']
            head['keys']+=date['keys']+page['keys']
            entries.append(head)
        return [title,sub,toc,*entries,*units]
    return works, assembled, defs, quantities, sources, lang, inherited | voyage


def retain_edition_lexicon(package, needed, definitions):
    """Keep the readings used in a book, their derivations and the language's linked examples."""
    required = set(needed)
    pending = list(required)
    while pending:
        for root in definitions.get(pending.pop(), {}).get('derivationKeys', ()):
            if root not in required:
                required.add(root)
                pending.append(root)
    linked = {eid for rule in package['morphology'] for eid in rule['entryIds']}
    linked.update(eid for item in package['corpus'] for token in item['tokens'] for eid in token['entryIds'])
    original = package['lexicon']
    package['lexicon'] = [e for e in original if e['label'] in required or e['id'] in linked]
    assert {e['label'] for e in original if e['label'] in needed} <= {e['label'] for e in package['lexicon']}


def build(publish, initial_folios=None, edition_lexicon=False, additional_source_fonts=(), measured_edition=None,
          folio_workers=1, catalogue_path=None):
    works, assemble, defs, quantities, sources, lang, inherited=build_material()
    initial=assemble({})
    print(TITLE, len(works),'works;',sum(v['lines'] for v in sources.values()),'source lines;',len(initial),'aligned units',flush=True)
    if not publish:return
    prior_digest = digest(TARGET) if TARGET.is_file() else None
    if prior_digest and read(WORK/'source-validation.json')['sha256'] != prior_digest:
        raise ValueError('The existing manuscript has edits. Reconcile them before rebuilding.')
    snapshot=read(DAMPIER/'snapshot.json')
    language=deepcopy(snapshot['snapshot']['language'])
    sid='anthology.poetic.source'
    language['sources'].append(dict(base(sid,'Poetic Anthology',None,'',status='draft'),kind='other',
                                    path=(catalogue_path or WORK/'works.json').relative_to(ROOT).as_posix(),sha256=digest(WORK/'works.json')))
    def snapshot_for(material):
        package = deepcopy(language)
        existing = {e['label'] for e in package['lexicon']}
        needed = {k for u in material for k in u['keys']}
        for key, entry in sorted((inherited | defs).items()):
            if key in existing or key not in needed:
                continue
            eid = 'anthology.lex.' + key
            package['lexicon'].append(dict(base(eid,key,sid,entry['origin'],status='draft'),
                headword=entry['form'],orthographyId='thimfora-79',pronunciation=entry['roman'],
                ipa='',partOfSpeech=entry['pos'],senses=[dict(id=eid+'.sense',definition=entry['meaning'],
                status='draft',citations=[dict(sourceId=sid,locator=key)])],variants=[],
                etymology=entry['origin'],exampleIds=[],audioLinks=[]))
        if edition_lexicon:
            retain_edition_lexicon(package, needed, inherited | defs)
        return dict(head='poetic-anthology-'+sha256(json.dumps(package,sort_keys=True).encode()).hexdigest(),
                    snapshot=dict(language=package))
    with TemporaryDirectory(dir=ROOT/'.local') as temp:
        stage=Path(temp)
        write(stage/'snapshot.json',snapshot_for(initial))
        pass_cache={'directory': ROOT/'.local/anthology-expansion/measured'}
        def measure(material,preflight):
            write(stage/'ledger.json',dict(book=TITLE,languageVersion='0.14',editionLabel='Four-column progressive edition',status='complete',sourceLabel='Source text',wrapLongWords=True,pairedPersianReading=True,units=material))
            return compose(stage/'ledger.json',stage/'snapshot.json',stage/TARGET.name,preflight=preflight,
                           source_fallback=SOURCE_FONTS/'NotoSerifTC-Anthology.ttf',
                           other_source_fonts=[SOURCE_FONTS/'NotoSansTamil-Regular.ttf',
                                               Path(os.environ['WINDIR'])/'Fonts/malgun.ttf', *additional_source_fonts],
                           reuse=measured_edition if 'signature' not in pass_cache else None,pass_cache=pass_cache,
                           folio_workers=folio_workers)
        folios=read(WORK/'source-validation.json').get('entryOpenings',{}) if prior_digest else (initial_folios or {})
        def positions(index):
            return {r['id']:next(s['leftPage'] for s in index if r['id']+'.title' in s['unitIds']) for r in works}
        for _ in range(4):
            receipts=measure(assemble(folios),True)
            targets=positions(receipts['index'])
            for spread in receipts['index']:
                for uid in spread['unitIds']:
                    if uid.endswith('.title') and uid.split('.')[0] in targets:
                        assert any(x.startswith(uid[:-5]) and x.rsplit('.',1)[-1].isdigit() for x in spread['unitIds']),uid+' separated from opening'
            if targets==folios:break
            folios=targets
        else:raise ValueError('Contents pagination did not settle')
        material=assemble(folios)
        write(stage/'snapshot.json',snapshot_for(material))
        proof=measure(material,False)
        index=read(stage/'page-index.json')['spreads']
        assert positions(index)==folios
        assert all(any(r['id']+'.title' in s['unitIds'] and any(re.match(rf"{r['id']}\.\d",u) for u in s['unitIds']) for s in index) for r in works),'title separated from opening'
        if (digest(TARGET) if TARGET.is_file() else None) != prior_digest:
            raise ValueError('The manuscript changed during composition.')
        write(stage/'source-validation.json',dict(works=len(works),sourceLines=sum(x['lines'] for x in sources.values()),sources=sources,
            reconstructedAllSourceLines=True,contentsPagesVerified=True,entryOpenings=folios,sha256=proof['sha256']))
        for n in ('ledger.json','page-index.json','layout-validation.json','numbering-validation.json','source-validation.json','snapshot.json'):
            copy2(stage/n,WORK/n)
        used_keys={key for u in material for key in u['keys']}
        write(WORK/'dictionary-additions.json',dict(entries={k:e for k,e in defs.items() if k in used_keys}))
        write(WORK/'unta-readings.json',[dict(zip(('unit','value','denominator','kind','notation','form'),k)) for k in dict.fromkeys(tuple(z.values()) for z in quantities) if not k[0].startswith('contents.') or not k[0].endswith('.folio') or folios[k[0].split('.')[1]]==k[1]])
        (WORK/'Proofs').mkdir(exist_ok=True)
        for p in (stage/'Proofs').glob('*.png'):copy2(p,WORK/'Proofs'/p.name)
        (stage/TARGET.name).replace(TARGET)
        assert digest(TARGET)==proof['sha256']
        print(proof['pages'],'pages. Verified',TARGET,flush=True)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--compose',action='store_true')
    build(cli.parse_args().compose)
