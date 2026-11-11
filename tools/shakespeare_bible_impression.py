"""Compose a biblical-name correction using the issued book's own language checkpoint."""
import argparse
from copy import deepcopy
from tempfile import TemporaryDirectory
from pathlib import Path

from tools.compose_historical_book import compose
from tools.shakespeare_project import (
    ROOT, PROJECT, read, write, sha, reviewed_bible_names,
    inherit_reviewed_bible_names, inherit_sealed_reading_slots, write_working_language,
)
from vayrshemon.forge import ForgeProject


def build(slug):
    project = read(PROJECT/'project.json')
    work = next(w for w in project['works'] if w['slug'] == slug)
    current = ROOT/work['output']
    edition = read(current.parent/'edition.json')
    if work['status'] != 'verified' or sha(current) != edition['nativeSha256'] or sha(current) != work['sha256']:
        raise ValueError('Current native edition does not match its receipt')
    if edition.get('biblicalNameImpression'):
        raise ValueError('This impression already incorporates the sealed names')
    checkpoints = PROJECT/'Checkpoints'
    cp_path, = [f for f in checkpoints.glob(slug+'*.json') if not f.name.endswith('-lexical-delta.json')
                and read(f)['head'] == work['languageHead']]
    cp = read(cp_path)
    delta_path = cp_path.with_name(cp_path.stem+'-lexical-delta.json')
    assert sha(delta_path) == cp['lexicalDeltaSha256']
    ledger_path = ROOT/work['currentLedger'] if work.get('currentLedger') else PROJECT/'Ledgers'/(slug+'.json')
    assert sha(ledger_path) == edition['ledgerSha256']
    assert sha(ROOT/work['sourcePath']) == edition['sourceSha256']
    original = read(ledger_path)
    witness = project['sealedBible']
    names = reviewed_bible_names(ROOT/witness['package'], witness['manifestSha256'], witness['forgeHead'])
    revision = edition.get('editorialRevision',1) + 1
    folder = current.parent/('Editorial revision '+str(revision))
    target = folder/current.name
    target_ledger = folder/'corrected-ledger.json'
    with TemporaryDirectory(dir=ROOT/'.local', prefix=slug+'-names-') as tmp:
        tmp = Path(tmp)
        language = write_working_language(ROOT/project['base']['package'], read(delta_path), tmp)
        assert all(sha(tmp/f) == h for f,h in cp['languageFiles'].items())
        previous_labels = current.parent/'display-labels.json'
        if previous_labels.exists():
            language.glosses.update(read(previous_labels)['glosses'])
        baseline = language.compile_units(original['units'])
        for old, same in zip(original['units'], baseline, strict=True):
            assert (old['text'],old['gloss']) == (same['text'],same['gloss']), (slug,old['id'])
        inherit_reviewed_bible_names(language.lexicon, language.glosses, witness)
        inherit_sealed_reading_slots(language.roman,witness)
        revised = deepcopy(original)
        revised['units'] = language.compile_units(original['units'])
        changed = {}
        for old,new in zip(original['units'], revised['units'], strict=True):
            assert all(old[k] == new[k] for k in ('id','analysis','source','rawSource','sourceId','keys'))
            if (old['text'],old['gloss']) != (new['text'],new['gloss']):
                affected = sorted(set(new['keys']) & names.keys())
                assert affected, (slug,new['id'])
                changed[new['id']] = affected
                new['review'] += ' Sealed Bible name reading: '+', '.join(names[k][0]['roman'] for k in affected)+'.'
        if not changed:
            return None
        revised['editionLabel'] = original['book']+' · '+edition['version']+' · editorial impression '+str(revision)
        if target.exists():
            assert sha(target_ledger) == read(folder/'revision-validation.json')['ledgerSha256']
            report = read(folder/'layout-validation.json')
            assert report['sha256'] == sha(target)
        else:
            write(target_ledger,revised)
            forge = ForgeProject(ROOT/project['base']['forgeProject'])
            snapshot = tmp/'snapshot.json'
            write(snapshot, dict(head=cp['head'],snapshot=forge.read(cp['head'])['snapshot']))
            report = compose(target_ledger,snapshot,target,reuse=current)
        assert all(report[k] for k in ('allFourColumnsMatchLedger','saveReopenIdentical',
                   'geometryAndPaintPreserved','numberingCheckedInBothModes'))
        assert report['missingGlyphs'] == report['verticalOverset'] == 0
        index = read(folder/'page-index.json')['spreads']
        affected_pages = sorted({p for spread in index if set(spread['unitIds']) & changed.keys()
                                 for p in (spread['leftPage'],spread['rightPage'])})
        old_labels = read(previous_labels)['glosses'] if previous_labels.exists() else {}
        used = {k for ks in changed.values() for k in ks}
        write(folder/'name-forms.json',dict(sealedBible=witness,
              entries={k:{field:names[k][0][field] for field in ('form','roman','semanticId','pos')} for k in sorted(used)}))
        write(folder/'display-labels.json', dict(sealedBible=witness,
              glosses={**old_labels, **{k:names[k][1] for k in sorted(used)}}))
        e = dict(edition,editorialRevision=revision,priorNativeSha256=sha(current),
                 nativeSha256=report['sha256'],priorLedgerSha256=sha(ledger_path),ledgerSha256=sha(target_ledger),
                 pages=report['pages'],spreads=len(index),correctedUnits=sorted(changed),
                 selectedProofPages=affected_pages,reviewedProofs=[],sealedBible=witness,
                 biblicalNameImpression=dict(formsByUnit=changed,
                     readings={k:names[k][0]['roman'] for k in sorted(used)},
                     spreadsReused=report['reusedMeasuredSpreads'],recomposedSpreads=len(index)-report['reusedMeasuredSpreads'],
                     predecessorPages=edition['pages'],sourceLinesPreserved=True,languageHead=cp['head'],
                     nameFormsSha256=sha(folder/'name-forms.json'),
                     regressionSha256=sha(ROOT/'.local/sealed-biblical-readings-regressions.log')))
        write(folder/'revision-validation.json',e)
        print(slug,report['pages'],changed,affected_pages,flush=True)
        return e


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('slug')
    build(parser.parse_args().slug)
