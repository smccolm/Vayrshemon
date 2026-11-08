"""Record a verified complete native work in the shared, still-incomplete project."""
import argparse,html,re
from urllib.parse import quote
from tools.shakespeare_project import ROOT,PROJECT,VERSION,read,write,sha,materialize

def finish(slug,path,regression_log):
    path=ROOT/path;folder=path.parent
    p=read(PROJECT/'project.json');w=next(w for w in p['works'] if w['slug']==slug)
    ledger_path=PROJECT/'Ledgers'/(slug+'.json');ledger=read(ledger_path);report=read(folder/'layout-validation.json')
    assert ledger['status']=='complete' and ledger['translatedUnits']==w['sourceUnits']
    assert report['allFourColumnsMatchLedger'] and report['saveReopenIdentical']
    assert report['geometryAndPaintPreserved'] and report['numberingCheckedInBothModes']
    assert report['missingGlyphs']==report['verticalOverset']==0
    assert report['sha256']==sha(path)
    assert sha(ROOT/w['sourcePath'])==w['sourceSha256']
    lang=materialize();assert lang.compile_units(ledger['units'])==ledger['units']
    checkpoint=next(c for f in (PROJECT/'Checkpoints').glob(slug+'*.json')
        if not f.name.endswith('-lexical-delta.json') and (c:=read(f))['ledgerSha256']==sha(ledger_path))
    assert checkpoint['head']==p['forgeHead']
    for name,digest in checkpoint['languageFiles'].items():assert sha(PROJECT/'Language'/name)==digest
    regression_log=ROOT/regression_log
    log=regression_log.read_text(encoding='utf-8-sig')
    counts=re.findall(r'Ran (\d+) tests? in ',log)
    assert counts and log.rstrip().endswith('OK'),'A completed passing regression log is required'
    receipt=dict(work=slug,version=VERSION,sourceUnits=w['sourceUnits'],translatedUnits=w['sourceUnits'],
        sourceSha256=w['sourceSha256'],ledgerSha256=sha(ledger_path),nativeSha256=report['sha256'],
        pages=report['pages'],languageHead=checkpoint['head'],checks='All four columns, source identity/order, exact reopening, complete layout, folios in both modes.',
        reviewedProofs=['page-001.png','page-002.png',f'page-{report["pages"]-1:03d}.png',f'page-{report["pages"]:03d}.png','color-1.png','color-2.png'],
        regressionTests=int(counts[-1]),regressionLog=str(regression_log.relative_to(ROOT)),
        regressionLogSha256=sha(regression_log),
        limitations='Authored translation and translator self-review, not independent literary certification. No claim to reproduce English rhyme or metre.')
    for name in receipt['reviewedProofs']:assert (folder/'Proofs'/name).exists()
    write(folder/'edition.json',receipt)
    w.update(status='verified',translatedUnits=w['sourceUnits'],reviewedUnits=w['sourceUnits'],
        output=str(path.relative_to(ROOT)).replace('\\','/'),sha256=report['sha256'],pages=report['pages'],languageHead=checkpoint['head'])
    write(PROJECT/'project.json',p)
    title=html.escape(w['title']);style='<meta charset="utf-8"><style>body{font:18px/1.6 Georgia;max-width:76ch;margin:3em auto}a{color:#17628a}</style>'
    (folder/'Start here.html').write_text(style+'<h1>'+title+'</h1><p>Complete source · working language '+VERSION+' from pinned 0.13 · '+str(report['pages'])+' pages.</p><p><a href="'+quote(path.name)+'">Open complete .vay</a></p><p><a href="../Shakespeare%20Project%200.13/Wiki/'+slug+'.html">Source-linked translation review</a> · <a href="edition.json">Edition receipt</a> · <a href="layout-validation.json">Layout checks</a></p><p>Approved four-column formatting, Maxima, two-page reading mode, black on white and Unta page numbers. The remaining corpus is still in progress.</p>',encoding='utf-8')
    links=''.join('<li><a href="../'+quote(v['output'].removeprefix('Saves/'))+'">'+html.escape(v['title'])+'</a> — '+str(v['pages'])+' pages</li>' for v in p['works'] if v['status']=='verified')
    done=sum(v['status']=='verified' for v in p['works'])
    (PROJECT/'Start here.html').write_text(style+'<h1>Shakespeare from 0.13</h1><p>IN PROGRESS · '+str(done)+' of '+str(len(p['works']))+' new sources delivered.</p><ul>'+links+'</ul><p><a href="Wiki/Index.html">Working wiki</a> · <a href="project.json">Exact coverage and pending works</a> · <a href="Dictionary-delta.json">New dictionary entries</a></p>',encoding='utf-8')
    library=ROOT/'Saves/Start here.html';text=library.read_text(encoding='utf-8')
    marker='<!-- shakespeare-project -->'
    if marker not in text:
        text+=marker+'<p><a href="Shakespeare%20Project%200.13/Start%20here.html">Remaining Shakespeare · new complete works and project progress</a></p>'
        library.write_text(text,encoding='utf-8')
    print(f'{w["title"]}: verified complete native file, {report["pages"]} pages; corpus {done}/{len(p["works"])}.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('work');parser.add_argument('path')
    parser.add_argument('--regression-log',required=True);a=parser.parse_args();finish(a.work,a.path,a.regression_log)
