"""Issue only the word correction authorized for previously published Shakespeare books."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse

from tools.shakespeare_project import PROJECT, ROOT, SEALED_BIBLE, read, write, sha, write_working_language, inherit_sealed_reading_slots
from tools.editorial_language import EditorialLanguage
from tools.shakespeare_endin import check_clean, correction, correct_forge_headwords, install_endin_readings
from tools.compose_historical_book import compose
from vayrshemon.forge import ForgeProject

LEGACY = {'allswell':'Alls Well That Ends Well','midsummer':'A Midsummer Nights Dream'}

def prepare(slug):
    project=read(PROJECT/'project.json')
    development=(ROOT/project['base']['forgeProject']).parent
    if slug in LEGACY:
        name=LEGACY[slug]
        native=ROOT/'Saves'/(name+' v0.13')/(name+' - 0.13.vay')
        edition=read(native.parent/'edition.json')
        assert sha(native)==edition['sha256']==read(development/(slug+'-book-validation.json'))['sha256']
        parent=project['base']['forgeHead']
        ledger_path=development/(slug+'-ledger.json')
        cp=None
    else:
        w=next(w for w in project['works'] if w['slug']==slug)
        assert w['status']=='verified'
        native=ROOT/w['output']
        edition=read(native.parent/'edition.json')
        assert sha(native)==w['sha256']==edition['nativeSha256']
        parent=w['languageHead']
        ledger_path=ROOT/w['currentLedger'] if w.get('currentLedger') else PROJECT/'Ledgers'/(slug+'.json')
        assert sha(ledger_path)==edition['ledgerSha256']
        cp,=[f for f in (PROJECT/'Checkpoints').glob(slug+'*.json') if not f.name.endswith('-lexical-delta.json') and read(f)['head']==parent]
    if edition.get('endinCorrection'):
        raise ValueError('Already issued')
    revised_number=edition.get('editorialRevision',1)+1
    folder=native.parent/('Editorial revision '+str(revised_number))
    original=read(ledger_path)
    revised=deepcopy(original)
    with TemporaryDirectory(dir=ROOT/'.local',prefix='endin-'+slug+'-') as temp:
        temp=Path(temp)
        if cp is not None:
            delta_path=cp.with_name(cp.stem+'-lexical-delta.json')
            assert sha(delta_path)==read(cp)['lexicalDeltaSha256']
            lang=write_working_language(ROOT/project['base']['package'],read(delta_path),temp)
            assert all(sha(temp/k)==v for k,v in read(cp)['languageFiles'].items())
        else:
            lang=EditorialLanguage(ROOT/project['base']['package'])
        labels=native.parent/'display-labels.json'
        if labels.is_file():
            lang.glosses.update(read(labels)['glosses'])
        previous_forms=native.parent/'name-forms.json'
        if previous_forms.is_file():
            for key,fields in read(previous_forms)['entries'].items():
                assert lang.lexicon[key]['semanticId']==fields['semanticId']
                lang.lexicon[key].update(fields)
        baseline=lang.compile_units(original['units'])
        assert all((a['text'],a['gloss'])==(b['text'],b['gloss']) for a,b in zip(baseline,original['units'],strict=True))
        forms=install_endin_readings(lang)
        inherit_sealed_reading_slots(lang.roman,SEALED_BIBLE)
        changed={}
        for r in revised['units']:
            if 'endin' in r['text'].casefold():
                r['analysis'],sense=correction(slug,r)
                changed[r['id']]=sense
        if not changed:
            raise ValueError('No rejected form in '+slug)
        revised['units']=lang.compile_units(revised['units'])
        for old,new in zip(original['units'],revised['units'],strict=True):
            assert all(old.get(k)==new.get(k) for k in ('id','rawSource','source','sourceId','lineNumbers','startLine','endLine','sourceOffsets'))
            assert 'endin' not in new['text'].casefold(),new['id']
            if old['id'] not in changed:
                assert old==new,(slug,old['id'])
            else:
                assert old['text']!=new['text'], old['id']
                check_clean(new,lang)
        if cp is not None:
            revised['editionLabel']=original['book']+' · 0.14 · editorial impression '+str(revised_number)
        target_ledger=folder/'corrected-ledger.json'
        write(target_ledger,revised)
        stamp=dict(previousNativeSha256=sha(native),previousLedgerSha256=sha(ledger_path),
                   correctedLedgerSha256=sha(target_ledger),correctedReadings=forms,
                   senses=changed,senseCounts=dict(Counter(changed.values())),languageHead=parent,
                   sealedBible=SEALED_BIBLE,revision=revised_number)
        for source in (previous_forms,labels):
            if source.is_file():
                write(folder/source.name,read(source))
        write(folder/'endin-correction.json',stamp)
        if cp is None:
            return folder,stamp
        if (folder/native.name).exists():
            report=read(folder/'layout-validation.json')
            assert sha(folder/native.name)==report['sha256']
        else:
            forge=ForgeProject(ROOT/project['base']['forgeProject'])
            snapshot=forge.read(parent)['snapshot']
            correct_forge_headwords(snapshot,forms)
            snapshot_path=temp/'snapshot.json'
            write(snapshot_path,dict(head=parent,snapshot=snapshot))
            report=compose(target_ledger,snapshot_path,folder/native.name,reuse=native)
        assert all(report[k] for k in ('saveReopenIdentical','geometryAndPaintPreserved','allFourColumnsMatchLedger','numberingCheckedInBothModes'))
        assert report['verticalOverset']==report['missingGlyphs']==0
        index=read(folder/'page-index.json')['spreads']
        pages=sorted({n for sp in index if changed.keys()&set(sp['unitIds']) for n in (sp['leftPage'],sp['rightPage'])})
        e=dict(edition,editorialRevision=revised_number,priorNativeSha256=sha(native),priorLedgerSha256=sha(ledger_path),
               nativeSha256=report['sha256'],ledgerSha256=sha(target_ledger),pages=report['pages'],spreads=len(index),
               correctedUnits=list(changed),selectedProofPages=pages,reviewedProofs=[],endinCorrection=dict(
                   receiptSha256=sha(folder/'endin-correction.json'),senseCounts=stamp['senseCounts'],
                   spreadsReused=report['reusedMeasuredSpreads'],recomposedSpreads=len(index)-report['reusedMeasuredSpreads'],
                   originalPages=edition['pages'],regressionSha256=sha(ROOT/'.local/shakespeare-endin-regressions.log')))
        write(folder/'revision-validation.json',e)
        print(slug,len(changed),report['pages'],pages,flush=True)
        return folder,stamp

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('slug')
    prepare(parser.parse_args().slug)
