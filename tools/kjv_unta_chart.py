"""Publish the historical Bible's chart transcription from the registered 283 ledger."""
from fractions import Fraction
import html
import shutil

from tools import kjv_unta_correction as parent
from tools.kjv_archive import ROOT, read, digest, verify_register
from vayrshemon.forge import ForgeProject, digest as snapshot_digest

VERSION = '0.10-kjv.284'
PACKAGE = ROOT/'data/language/archaic-kjv-284'
OUT = ROOT/'Saves'/f'KJV Bible v{VERSION}'
COMPACT = ROOT/'Saves'/f'KJV Bible - Compact Letter Edition v{VERSION}'
RECORD = ROOT/'Saves/Maintenance/2026-11-07-unta-284'
CHARTS = ('Origins_2_Thimfora_2.jpg','Origins_3_Unta_2.jpg','Unta - Base 12.jpg')
# Historical font slots. The 1,728 word has the single ėr letter, slot 205.
SPELLINGS = {'ÓÅtus':'ÕÅtus','Çram×n':'Çramen','lans×ro':'lanserß',
             'Óen×um':'Õen×um','nesidÉl':'mesidÉl','Óerid':'ÕÍid'}
DERIVED = {'both','either','double','equivocal','kjv_concubine','kjv_bekah',
           'kjv_doubletongued_timothy','kjv_double_minded_james'}
CHART_NOTE = (
    'The 284 edition uses the native letters in the original Thimfora and Unta charts. '
    'For 2, 48, 84, 108, 120 and 1,728 the readings are ŧhātus, ãramen, lanserō, '
    'ŧhenēum, mesidäl and neksus ŧhėrid. The last word uses the single letter ėr. '
    'The crossed ŧh uses native slot 213 and its Maxima uses slot 212. '
    'The same six spellings recur inside larger counts and exact fractions. '
    'A spoken radix point includes the apostrophe before choi, as in the chart’s yamen’choi yamen. '
    'The inherited Unta values, grammatical categories and KJV verse wording are preserved.')

def corrected_form(form):
    for old,new in SPELLINGS.items():
        form=form.replace(old,new)
    # On chart 2 the apostrophe is a separate, visible triangular glyph.
    return form.replace('’Ñã ', 'Ñã ').replace('Ñã ', '’Ñã ')

def chart_quantity(value,kind,denominator=1,*,notation='words'):
    q=parent.quantity(value,kind,denominator,notation=notation)
    q['spokenForm']=corrected_form(q['spokenForm'])
    if notation=='words':q['form']=q['spokenForm']
    return q

def prepare():
    prior_manifest=verify_register(parent.VERSION)
    if (PACKAGE/'manifest.json').exists() or (OUT/'KJV 284.vayforge').exists():
        raise FileExistsError('284 already registered or in progress')
    for folder in (PACKAGE, OUT, COMPACT, RECORD):
        folder.mkdir(parents=True,exist_ok=True)
    write=parent.write
    for name in prior_manifest['files']:
        shutil.copyfile(parent.PACKAGE/name,PACKAGE/name)
    note_path=PACKAGE/'unta.md'
    note_path.write_text(note_path.read_text(encoding='utf8')+'\n'+CHART_NOTE+'\n',encoding='utf8')
    orth=read(PACKAGE/'orthography.json')
    orth['romanBySlot'].update({'Õ':'ŧh','Ô':'Ŧh'})
    write(PACKAGE/'orthography.json',orth)
    lang=parent.compiler(PACKAGE)
    quantities=read(parent.PACKAGE/'quantities.json')
    for q in quantities.values():
        v=Fraction(q['value'])
        update=chart_quantity(v.numerator,q['kind'],v.denominator,notation=q['notation'])
        assert q['base12']==update['base12']
        q.update(update)
    write(PACKAGE/'quantities.json',quantities)
    lex=read(PACKAGE/'lexicon.json')
    lex['version']=VERSION
    numerals=set(quantities)|parent.KEYS.keys()|parent.ORDINAL.keys()|parent.DENOM.keys()|DERIVED|{'twenty_four','twice','thrice'}
    changed={}
    for key,entry in lex['entries'].items():
        old=entry['form']
        form=corrected_form(old)
        if old==form:continue
        assert key in numerals,key
        entry.setdefault('historicalForms',[]).append(dict(version=parent.VERSION,form=old,roman=entry['roman']))
        entry.update(form=form,roman=lang.reading(form),register=VERSION)
        changed[key]=(old,form)
    for k,q in quantities.items():assert lex['entries'][k]['form']==q['form']
    write(PACKAGE/'lexicon.json',lex)
    lang=parent.compiler(PACKAGE)
    old=read(parent.OUT/'complete-translation-ledger.json')
    changes=[]
    for u in old['units']:
        revised=lang.compile(u['analysis'])
        assert revised['keys']==u['keys'] and revised['gloss']==u['gloss']
        if revised['text']!=u['text']:
            assert set(changed).intersection(u['keys']),u['reference']
            changes.append(dict(id=u['id'],reference=u['reference'],keys=sorted(set(changed).intersection(u['keys'])),
                                parentText=u['text'],text=revised['text']))
            u.update(revised)
    assert len(old['units'])==31102 and changes
    old.update(version=VERSION,correctionOf=parent.VERSION)
    write(OUT/'complete-translation-ledger.json',old)
    write(OUT/'correction-ledger.json',changes)
    summary=dict(version=VERSION,parent=parent.VERSION,verses=31102,sections=66,
                 changedLexicalForms=len(changed),revisedVerses=len(changes),
                 parentLedgerSha256=digest(parent.OUT/'complete-translation-ledger.json'),
                 distinctQuantityReadings=len(quantities),sourceDigitVerses=0,sourcePreserved=True,
                 chartSha256={n:digest(ROOT/'Inputs'/n) for n in CHARTS},spellings=SPELLINGS)
    write(OUT/'language-delta.json',summary)
    write(PACKAGE/'coverage-summary.json',summary)
    prior=read(parent.OUT/'current-snapshot.json')
    assert prior['head']==prior_manifest['forgeHead']
    path=OUT/'KJV 284.vayforge'
    forge=ForgeProject.create(path,'KJV 284 · chart transcription',snapshot=prior['snapshot'])
    write(OUT/'forge-import.json',dict(originalHead=prior['head'],localImportHead=forge.status()['head'],
          importedSnapshotSha256=snapshot_digest(prior['snapshot']),parentProject=parent.OUT.name+'/KJV 283.vayforge'))
    snap=prior['snapshot']
    for entry in snap['language']['lexicon']:
        key=entry['label']
        if key in changed:
            updated=lex['entries'][key]
            entry.update(headword=updated['form'],pronunciation=updated['roman'])
    by_id={u['id']:u for u in old['units']}
    fixtures=0
    for test in snap['tests']:
        if test['id'].startswith('kjv283.verse.'):
            uid=test['id'].removeprefix('kjv283.verse.')
            test.update(id='kjv284.verse.'+uid,title='KJV 284 · '+by_id[uid]['reference'])
            test['paragraphs'][0]['text']=by_id[uid]['text']
            fixtures+=1
    assert fixtures==31102
    snap['wiki'].insert(0,dict(id='kjv284-chart',title='Original Unta spellings',body=CHART_NOTE,ruleIds=[]))
    snap['research']['kjv284Unta']=summary
    st=forge.replace_draft(snap,forge.status()['generation'])
    head=forge.commit('KJV 284 · restore six chart spellings in both Bibles',st['generation'])['head']
    write(OUT/'current-snapshot.json',dict(head=head,snapshot=snap))
    for folder in (OUT,COMPACT):
        write(folder/'forge-reference.json',dict(project=str(path),branch='main',head=head,parentHead=prior['head']))
    manifest=dict(version=VERSION,policy='never-modernize',basePackage=parent.PACKAGE.relative_to(ROOT).as_posix(),
        baseManifestSha256=digest(parent.PACKAGE/'manifest.json'),baseForgeHead=prior['head'],forgeHead=head,
        compilerPath=(PACKAGE/'compiler.py').relative_to(ROOT).as_posix(),compilerSha256=digest(PACKAGE/'compiler.py'),
        files={n:digest(PACKAGE/n) for n in prior_manifest['files']})
    write(PACKAGE/'manifest.json',manifest)
    registry=read(ROOT/'data/language/historical.json')
    assert not any(row['version']==VERSION for row in registry['registers'])
    registry['registers'].append(dict(version=VERSION,package=PACKAGE.relative_to(ROOT).as_posix(),
        manifestSha256=digest(PACKAGE/'manifest.json'),forgeHead=head,policy='never-modernize',guide='docs/KJV_ARCHIVE.md'))
    write(ROOT/'data/language/historical.json',registry)
    verify_register(VERSION)
    style='<meta charset="utf-8"><style>body{max-width:70em;margin:3em auto;font:18px/1.6 Georgia}td,th{padding:.4em;text-align:left}pre{white-space:pre-wrap}</style>'
    glossary=read(PACKAGE/'morphology.json')['glosses']
    rows=''.join('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in (k,e['roman'],glossary.get(k,''),e['meaning']))+'</tr>' for k,e in sorted(lex['entries'].items()))
    (OUT/'Dictionary.html').write_text(style+'<h1>KJV 284 historical dictionary</h1><table><tr><th>Key</th><th>Reading</th><th>Gloss</th><th>Meaning</th></tr>'+rows+'</table>',encoding='utf8')
    wiki=CHART_NOTE+'\n\n'+(parent.OUT/'Wiki.md').read_text(encoding='utf8')
    (OUT/'Wiki.md').write_text(wiki,encoding='utf8')
    (OUT/'Wiki.html').write_text(style+'<h1>KJV 284 grammar and Unta</h1><pre>'+html.escape(wiki)+'</pre>',encoding='utf8')
    print('Registered',head,summary,flush=True)

if __name__=='__main__':
    prepare()
