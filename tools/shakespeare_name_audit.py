"""Verify Yeshūa in the four saved columns of every current Shakespeare edition."""
from collections import Counter
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from tools.compose_historical_book import texts
from tools.shakespeare_project import PROJECT, ROOT, SHAKESPEARE_JESUS, check_shakespeare_name, read, sha, source_units, write, write_working_language, reviewed_bible_names
from vayrshemon.native_storage import unpack


def edition_language(work, project):
    """Reconstruct the language in which the issued passages were actually written."""
    folder = (ROOT/work['output']).parent
    checkpoints = PROJECT/'Checkpoints'
    checkpoint, = [p for p in checkpoints.glob(work['slug']+'*.json')
                   if not p.stem.endswith('-lexical-delta') and read(p).get('head')==work['languageHead']]
    record = read(checkpoint)
    delta = checkpoint.with_name(checkpoint.stem+'-lexical-delta.json')
    if sha(delta)!=record['lexicalDeltaSha256']:
        raise ValueError('Edition dictionary differs from its checkpoint: '+work['slug'])
    with TemporaryDirectory(dir=ROOT/'.local') as scratch:
        dest = Path(scratch)
        language = write_working_language(ROOT/project['base']['package'],read(delta),dest)
        if any(sha(dest/f)!=digest for f,digest in record['languageFiles'].items()):
            raise ValueError('Edition language differs from its checkpoint: '+work['slug'])
    for filename, field in [('name-forms.json','entries'),('endin-correction.json','correctedReadings')]:
        if (folder/filename).exists():
            for key, fields in read(folder/filename)[field].items():
                if language.lexicon[key]['semanticId']!=fields['semanticId']:
                    raise ValueError('Editorial correction changed lexical identity: '+key)
                language.lexicon[key].update(fields)
    if (folder/'display-labels.json').exists():
        language.glosses.update(read(folder/'display-labels.json')['glosses'])
    return language


def audit_book(path, source, expected_hash, ledger=None, language=None, names=()):
    if sha(path) != expected_hash:
        raise ValueError(f'Issued manuscript hash mismatch: {path}')
    pages = unpack(read(path))['state']['pages']
    seen = Counter()
    hits = []
    rejected_stems = []
    rows = iter(ledger['units']) if ledger is not None else None
    biblical = []
    previous = ''
    for left in range(0, len(pages), 2):
        columns = [texts(frame) for page in pages[left:left+2]
                   for frame in sorted(page['frames'], key=lambda frame: int(frame['x']))]
        if len(columns) != 4:
            raise ValueError(f'Expected four parallel columns on spread {left//2+1} in {path}')
        for native, reading, gloss, english in zip(*columns, strict=True):
            if 'endin' in native.casefold():
                rejected_stems.append(dict(pages=[left+1,left+2],occurrences=native.casefold().count('endin')))
            if rows is not None:
                row = next(rows)
                if (native,gloss,english) != (row['text'],row['gloss'],row['source']):
                    raise ValueError(f"Saved text differs from the issued ledger at {path}, {row['id']}")
                used = sorted(set(row['keys']).intersection(names))
                initial = not row.get('continuesParagraph', row.get('part',0)>0) or bool(re.search(r'[.!?]\s*\]?[ ]*$',previous))
                previous = row['analysis']
                if used:
                    translated = language.compile(row['analysis'],initial=initial)
                    for key in used:
                        stored = names[key][0]
                        if stored['form'] not in native and stored['form'] not in native[:1].lower()+native[1:]:
                            # Proper initial capitals use the script's own maxima (not Unicode uppercase).
                            maximum = language.compile(key)['text']
                            if maximum not in native:
                                raise ValueError(f"Missing sealed form for {key} in {path}, {row['id']}")
                        if names[key][1] not in gloss or translated['text'] != native:
                            raise ValueError(f"Biblical reading differs at {path}, {row['id']}, {key}")
                    biblical.append(dict(unit=row['id'],pages=[left+1,left+2],keys=used))
            if native != reading:
                raise ValueError(f'Native and Roman reading blocks differ on page {left+1} in {path}')
            check_shakespeare_name(english, native, gloss)
            occurrences = SHAKESPEARE_JESUS.findall(english)
            seen.update(occurrences)
            if occurrences:
                hits.append(dict(pages=[left+1,left+2],sourceForms=occurrences,
                                 nativeOccurrences=native.count('YeÛça'),glossOccurrences=gloss.count('Yeshūa')))
    expected = Counter(form for unit in source_units(source)['units']
                       for form in SHAKESPEARE_JESUS.findall(unit['source']))
    if seen != expected:
        raise ValueError(f'Source name count mismatch for {path}: {seen} / {expected}')
    if rows is not None and next(rows,None) is not None:
        raise ValueError(f'Unused ledger rows in {path}')
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=expected_hash, pages=len(pages),
                sourceForms=dict(seen), occurrences=sum(seen.values()), passages=hits,
                reviewedBiblicalNamePassages=biblical,rejectedEndin=rejected_stems)


def main():
    project = read(PROJECT/'project.json')
    results = []
    witness = project['sealedBible']
    names = reviewed_bible_names(ROOT/witness['package'],witness['manifestSha256'],witness['forgeHead'])
    for work in project['works']:
        if work['status'] == 'verified':
            ledger_path = ROOT/work['currentLedger'] if work.get('currentLedger') else PROJECT/'Ledgers'/(work['slug']+'.json')
            edition = read((ROOT/work['output']).parent/'edition.json')
            if sha(ledger_path) != edition['ledgerSha256']:
                raise ValueError('Published ledger hash mismatch for '+work['slug'])
            results.append(audit_book(ROOT/work['output'], ROOT/work['sourcePath'], work['sha256'],read(ledger_path),edition_language(work,project),names))
    for slug, folder in [('alls-well-that-ends-well', 'Alls Well That Ends Well'),
                         ('a-midsummer-nights-dream', 'A Midsummer Nights Dream')]:
        path, = (ROOT/'Saves'/(folder+' v0.13')).glob('*.vay')
        approved = {'alls-well-that-ends-well': '1d28a11deb0f1462f9ee0205fad20c90b6f12100327978f192e57d67e7ea0d70',
                    'a-midsummer-nights-dream': '292ed08b5781574ef0050abe08dbe2a4d7f20802a404f05201c2bc80dfe5d34b'}
        entry=project.get('existingPlayImpressions',{}).get(slug)
        ledger=None
        if entry:
            if sha(ROOT/entry['priorOutput'])!=approved[slug] or sha(ROOT/entry['currentLedger'])!=entry['ledgerSha256']:
                raise ValueError('Prior 0.13 seal or current impression ledger mismatch: '+slug)
            ledger=read(ROOT/entry['currentLedger'])
        expected=entry['sha256'] if entry else approved[slug]
        results.append(audit_book(path, ROOT/'Inputs/Sources'/(slug+'_TXT_FolgerShakespeare.txt'), expected,ledger))
    result = dict(sealedBible=project['sealedBible'], verifiedEditions=len(results),
                  occurrences=sum(book['occurrences'] for book in results), books=results)
    write(PROJECT/'Reviews/shakespeare-yeshua-saved-books.json', result)
    rejected = {book['path']:book['rejectedEndin'] for book in results if book['rejectedEndin']}
    write(PROJECT/'Reviews/shakespeare-endin-saved-books.json',dict(verifiedEditions=len(results),
          sealedBible=witness,affectedBooks=rejected,occurrences=sum(case['occurrences'] for rows in rejected.values() for case in rows),
          books=[dict(path=book['path'],sha256=book['sha256'],pages=book['pages']) for book in results]))
    if rejected:
        raise ValueError('The rejected endin stem remains in current manuscripts: '+', '.join(rejected))
    print(f"Checked {result['occurrences']} occurrences across {len(results)} saved Shakespeare editions.")


if __name__ == '__main__':
    main()
