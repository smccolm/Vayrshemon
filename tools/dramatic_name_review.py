"""Explicit 0.13 corrections to the two plays; Bible files are never inputs/outputs."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import argparse, hashlib, html, json, re, shutil, sqlite3
from tools.editorial_language import ROOT, EditorialLanguage, load_current

VERSION = '0.13'
PACKAGE = ROOT / 'data/language/later-dramatic-0.13'
DEST = ROOT / 'Saves/Language Development 0.13'
PARENT = ROOT / 'Saves/Language Development 0.12'
NAMES = {'bottom_name':'Bottom', 'flute_name':'Flute', 'snout_name':'Snout',
         'cobweb_name':'Cobweb', 'mote_name':'Mote'}
LABELS = dict(NAMES, bear_animal='bear', odour_stage='odour', amen='so-be(opt.)')
NATIVE = {
    'puritan': (['pure','faith','person'], '', 'noun', 'purity-faith-adherent',
        'Puritan: adherent of the source culture’s reforming religious-purity movement; not merely a clean person.'),
    'papist': (['chief','priest','follower'], ' ', 'noun', 'pope-adherent',
        'Papist: source speaker’s polemical designation for allegiance to the pope; a lexicalized chief-priest-follower phrase, not a personal name.'),
    'shrove_tuesday': (['confess','feast','day'], ' ', 'noun', 'pre-Lenten-confession-feast-day',
        'Shrove Tuesday, the source culture’s specific pre-Lenten confession and feasting day; the native phrase is a calendar label, not a claim about an Unta weekday.'),
    'centaur': (['horse','human'], '', 'noun', 'horse-human',
        'Centaur: the horse-bodied human creature of the source mythology; a class of beings, not an individual named Centaur.'),
    'bacchanal': (['wine','god','follower'], ' ', 'noun', 'wine-god-adherent',
        'Bacchanal: a worshipper of Bacchus, the wine deity; here the frenzied women who kill the Thracian singer, not simply any drunk person.'),
    'legrand': (['great'], '', 'adjective', 'Great',
        'The Great, translated epithet in Saint Jaques le Grand; not an additional personal name.'),
}
REFERENTS = {
    'francis_flute': ('francis', 'Francis', 'Francis, the given name of Flute in Midsummer; distinct from the saint and inn-sign referent in All’s Well.'),
    'helen_troy': ('helen', 'Helen', 'Helen of Troy, the mythic beauty invoked in Midsummer; distinct from both plays’ Helen/Helena characters.'),
}
UNIT_KEYS = {'0027':('diana','dian'), '0097':('francis','francis_flute'),
             '0611':('helen','helen_troy'), '0672':('helen','helen_troy')}
NOTE = '''# Later dramatic Vayrshemon 0.13 — names without lookup labels

This is a targeted audit of both complete plays against the pinned 0.12 language.
The completed historical Bibles are untouched. No biblical text is recompiled.

## Printed words and dictionary identities

Bottom, Flute, Snout, Cobweb and Mote are printed without the internal “-name”
qualifier. Bear and odour lose the “-animal” and “-stage” lookup qualifiers.
Explicit resolved labels also apply inside possessive chains: Bottom’s name
must not become “bottom-name” again when used before another noun. Pronominal
possessives retain my/your/our and their existing number distinctions. This is
a construction-gloss correction; it never substitutes English into native text.

## Separate referents, including homonymous names

Diana’s altar in Midsummer belongs to Dian the goddess, not to the Widow’s
daughter in All’s Well. The two Helen allusions in Midsummer refer to Helen of
Troy, not Helen of All’s Well or Helena of Athens. Francis Flute receives his
own identity, distinct from the Saint Francis inn-sign. Equal name sounds do
not establish equal people. The two new semantic entries preserve existing
name forms; Diana’s altar uses the established native goddess-name Dian.

## Native ordinary vocabulary

Puritan, Papist, Shrove Tuesday, centaur, Bacchanal and the epithet le Grand
were wrongly excused as names. Their new forms use existing native roots,
with precise source-specific meanings retained in the dictionary. Papist keeps
the source speaker’s polemical context; it is not a neutral label imposed on
modern people. The Shrove Tuesday phrase retains that exact calendar referent.
No Unta weekday correspondence is invented. Centaur describes a creature class;
Bacchanal denotes the wine deity’s adherent, not generic drunkenness.

“Amen, amen” already has native **kom rē’ne** twice. Preserve both ratifications
and their optative force; display the construction as **so-be(opt.)** rather
than hiding it behind the foreign formula. Neither play uses a Jesus entry.
The author’s Yeshūa spelling remains the choice for future occurrences.

## Deliberate forms retained

Bottom’s Ercles, Phibbus and Thisne, and the play-within-the-play’s Limander,
Shafalus and Procrus, are source-grounded theatrical distortions. Do not silently
normalize them. Genuine names such as Mile End and the literal fairy names
retain their referents. Limbo is a named otherworld region; the Muses and Furies
are named mythic collectives in these passages. Low Dutch is a named language
with an inherited geographic form; this audit does not invent a more precise
modern dialect identity. Regional affiliation terms are retained as documented
name-derived forms, not treated as unrelated ordinary lexical loans.

All four first-person perspectives, inherited clause variation, deliberate
repetitions, source order and English are preserved. Maxima follows names and
actual sentence boundaries. The source-linked audit is not independent literary
certification or an assertion that no other translation issue can exist.
'''

def read(p): return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,v):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def refresh_copied_fixtures(lang):
    # Old fixtures stay immutable in 0.10–0.12; only this new package adopts
    # its resolved display labels. Source analyses and rejection cases persist.
    for name in ['regression-cases.json','flow-cases.json']:
        rows=read(PACKAGE/name)
        for row in rows:
            if row.get('expected')=='reject':continue
            c=lang.compile(row['analysis'],initial=row.get('initial',True))
            row['expectedText']=c['text'];row['expectedGloss']=c['gloss']
            if 'expectedReading' in row:row['expectedReading']=lang.reading(c['text'])
        write(PACKAGE/name,rows)

def prepare():
    old,pin=load_current();assert pin['version']=='0.12'
    assert not PACKAGE.exists() and not DEST.exists(), 'Use a new version, never overwrite a publication'
    PACKAGE.mkdir();DEST.mkdir();write(DEST/'parent.json',pin);write(PACKAGE/'parent.json',pin)
    for name in ['lexicon.json','morphology.json','orthography.json','regression-cases.json','flow-cases.json']:
        shutil.copyfile(old.folder/name,PACKAGE/name)
    lex=read(PACKAGE/'lexicon.json');morph=read(PACKAGE/'morphology.json')
    morph['possessorGlossPolicy']='resolved-labels';morph['glosses'].update(LABELS)
    changes=[]
    for key,(parts,separator,pos,gloss,meaning) in NATIVE.items():
        entry=lex['entries'][key];before=deepcopy(entry)
        entry['historicalForms'].append(dict(version='0.12',form=entry['form'],roman=entry['roman'],status='superseded editorial borrowing, not fictional sound change'))
        form=separator.join(old.lexicon[k]['form'] for k in parts)
        entry.update(form=form,roman=old.reading(form),meaning=meaning,pos=pos,derivationKeys=parts,
            derivationSeparator=separator,usageScope='later-literary',development='native-source-term-correction',
            origin='0.13 explicit native construction from '+', '.join(parts)+'; source-cultural meaning retained.')
        morph['glosses'][key]=gloss
        changes.append(dict(key=key,before=before,after=deepcopy(entry)))
    for key,(base,label,meaning) in REFERENTS.items():
        assert key not in lex['entries']
        entry=deepcopy(lex['entries'][base]);entry.update(meaning=meaning,semanticId='lex.'+key,
            historicalForms=[],historicalWitness=None,development='referent-disambiguation',
            origin='0.13 source-linked identity separation; inherited personal-name form preserved.')
        lex['entries'][key]=entry;morph['glosses'][key]=label
    lex['version']=VERSION;write(PACKAGE/'lexicon.json',lex);write(PACKAGE/'morphology.json',morph)
    lang=EditorialLanguage(PACKAGE);refresh_copied_fixtures(lang)
    allchanges=[];books={};inventory={};cases=[]
    for slug in ['allswell','midsummer']:
        prior=read(PARENT/(slug+'-ledger.json'));units=prior['units'];newer=deepcopy(units)
        assert old.compile_units(units)==units, 'Parent ledger does not compile exactly'
        for u in newer:
            if slug=='midsummer' and u['id'] in UNIT_KEYS:
                a,b=UNIT_KEYS[u['id']];pattern=r'(?<![A-Za-z_])'+a+r'(?![A-Za-z_])'
                assert len(re.findall(pattern,u['analysis']))==1
                u['analysis']=re.sub(pattern,b,u['analysis'])
        compiled=lang.compile_units(newer);edits=[]
        for before,after in zip(units,compiled):
            assert {k:v for k,v in before.items() if k not in {'analysis','text','gloss','keys'}}=={k:v for k,v in after.items() if k not in {'analysis','text','gloss','keys'}}
            if before!=after:
                row=dict(play=slug,unitId=after['id'],source=after['source'],beforeAnalysis=before['analysis'],afterAnalysis=after['analysis'],beforeText=before['text'],afterText=after['text'],beforeGloss=before['gloss'],afterGloss=after['gloss'])
                edits.append(row);allchanges.append(row)
        used={k for u in units for k in u['keys']}
        assert not any('jesus' in k or 'barjesus' in k for k in used)
        inventory[slug]=[dict(key=k,form=old.lexicon[k]['form'],roman=old.lexicon[k]['roman'],meaning=old.lexicon[k]['meaning'],gloss=old.glosses.get(k,k.replace('_','-')),units=[u['id'] for u in units if k in u['keys']]) for k in sorted(used) if old.lexicon[k]['pos']=='proper' or '_' in k or k in NATIVE or k=='amen']
        books[slug]=dict(units=len(units),changedUnits=len(edits),nativeTextUnits=sum(r['beforeText']!=r['afterText'] for r in edits),glossUnits=sum(r['beforeGloss']!=r['afterGloss'] for r in edits),analysisUnits=sum(r['beforeAnalysis']!=r['afterAnalysis'] for r in edits),sourceSha256=prior['sourceSha256'])
        prior.update(languageVersion=VERSION,parentVersion='0.12',units=compiled);write(DEST/(slug+'-ledger.json'),prior)
    write(DEST/'name-audit.json',dict(scope='Every used proper-name entry, internal compound key and source occurrence in both complete plays',books=inventory,jesusOccurrences=0,reviewedNameLabels=LABELS,nativeTerms=list(NATIVE),referentRepairs=UNIT_KEYS,retained=['intentional theatrical name distortions','Mile End','Limbo','Muses','Furies','Low Dutch','regional affiliations'],limitations='Targeted name/label/native-term review, not independent certification of every literary choice.'))
    write(DEST/'editorial-revisions.json',allchanges)
    write(PACKAGE/'name-decisions.json',dict(labels=LABELS,nativeEntries=changes,referents=REFERENTS,sourceUnitRepairs=UNIT_KEYS,books=books,jesusOccurrences=0,newLexicalRoots=0))
    for analysis in ['bottom_name/head:n.','my/bottom_name/head:n.','bottom_name+flute_name/name:n.','bear_animal:a.','odour_stage, odour_stage:excl.','amen, amen.','dian/altar.','francis_flute flute_name.','helen_troy/beauty.','papist puritan shrove_tuesday centaur bacchanal legrand.']:
        cases.append(dict(analysis=analysis,**lang.compile(analysis)))
    write(PACKAGE/'name-cases.json',cases)
    write(PACKAGE/'decisions.json',dict(parent=pin,books=books,sourceUnitRepairs=UNIT_KEYS,newSemanticEntries=list(REFERENTS),newLexicalRoots=0,grammarChanges=0,glossPolicy='resolved-labels'))
    (PACKAGE/'development.md').write_text(NOTE,encoding='utf8')
    (PACKAGE/'grammar.md').write_text(NOTE+'\n\n# Inherited 0.12 grammar\n\n'+(old.folder/'grammar.md').read_text(encoding='utf8'),encoding='utf8')
    write(DEST/'language-delta.json',dict(version=VERSION,parentVersion='0.12',parentHead=pin['forgeHead'],books=books,newLexicalRoots=0,newSemanticEntries=len(REFERENTS),nativeTermsCorrected=len(NATIVE),displayLabelsCorrected=len(LABELS),referentCorrections=len(UNIT_KEYS),grammarChanges=0,semanticKeys=len(lex['entries']),BibleUnchanged=True))
    print(json.dumps(books,indent=2),flush=True)

def publish():
    from vayrshemon.forge import ForgeProject,validate
    from vayrshemon.archive_language import base
    assert not (PACKAGE/'manifest.json').exists()
    pin=read(DEST/'parent.json');prior=read(PARENT/'current-snapshot.json');assert prior['head']==pin['forgeHead']
    s=deepcopy(prior['snapshot']);lang=EditorialLanguage(PACKAGE);delta=read(DEST/'language-delta.json')
    sid='later013.source';rid='later013.names'
    s['language']['sources'].append(dict(base(sid,'0.13 name and native-term audit',None,'',status='draft'),kind='other',path='Saves/Language Development 0.13/editorial-revisions.json',sha256=sha(DEST/'editorial-revisions.json')))
    s['language']['grammar'].append(dict(base(rid,'Names, homonyms and construction labels',sid,'Explicit source review',status='draft'),topic='construction',statement=NOTE,morphologyIds=[],exampleIds=[],alternatives=[]))
    found=set()
    for entry in s['language']['lexicon']:
        key=entry['label']
        if key in NATIVE:
            new=lang.lexicon[key];entry.update(headword=new['form'],pronunciation=new['roman'],partOfSpeech=new['pos'],etymology=new['origin']);entry['senses'][0]['definition']=new['meaning'];found.add(key)
    assert found==set(NATIVE),found
    for key in REFERENTS:
        e=lang.lexicon[key]
        s['language']['lexicon'].append(dict(base('later013.lex.'+key,key,sid,'Distinct named referent',status='draft'),headword=e['form'],orthographyId='thimfora-79',pronunciation=e['roman'],ipa='',partOfSpeech='proper',senses=[dict(id='later013.sense.'+key,definition=e['meaning'],status='draft',citations=[dict(sourceId=sid,locator='Midsummer source-linked audit')])],variants=[],etymology=e['origin'],exampleIds=[],audioLinks=[]))
    s['wiki'].insert(0,dict(id='later013-current',title='START HERE · later dramatic 0.13',body=(PACKAGE/'grammar.md').read_text(encoding='utf8'),ruleIds=[rid]))
    s['wiki'].insert(1,dict(id='later013-audit',title='0.13 · Source-linked name and vocabulary audit',body=json.dumps(read(DEST/'name-audit.json'),ensure_ascii=False,indent=2),ruleIds=[rid]))
    for slug in ['allswell','midsummer']:
        units=read(DEST/(slug+'-ledger.json'))['units']
        for offset in range(0,len(units),10):
            group=units[offset:offset+10]
            s['tests'].append(dict(id=f'later013.{slug}.{offset}',title=f'0.13 · {slug} · {group[0]["id"]}–{group[-1]["id"]}',ruleIds=[rid],paragraphs=[dict(text=u['text'],translation=u['source'],analysis=u['gloss']+'\nAuthored analysis: '+u['analysis']) for u in group]))
    s['decisions'].append(dict(id='later013-names',status='proposed',choice=NOTE,evidence='Explicit user request to recheck both plays after the Bible name correction; all 1,970 source units audited.'))
    s['research']['laterDramatic013']=delta;validate(s)
    path=DEST/'Vayrshemon 0.13.vayforge';assert not path.exists()
    with sqlite3.connect('file:'+str(ROOT/pin['forgeProject']).replace('\\','/')+'?mode=ro',uri=True) as source,sqlite3.connect(path) as destination:source.backup(destination)
    project=ForgeProject(path);status=project.status();status=project.branch('later-dramatic-0.13',status['generation'],version=pin['forgeHead'])
    status=project.replace_draft(s,status['generation']);status=project.commit('0.13 · printed name labels, distinct referents and native cultural terms',status['generation'])
    head=status['head'];write(DEST/'current-snapshot.json',dict(head=head,snapshot=s));delta.update(forgeHead=head,newWikiArticles=2,newForgeFixtures=len(s['tests'])-len(prior['snapshot']['tests']));write(DEST/'language-delta.json',delta)
    for slug in ['allswell','midsummer']:
        p=DEST/(slug+'-ledger.json');d=read(p);d['languageHead']=head;write(p,d)
    write(PACKAGE/'manifest.json',dict(format='vayrshemon.editorial-language',formatVersion='1.0.0',version=VERSION,status='authored later dramatic baseline; edition validation separate',forgeHead=head,parentHead=pin['forgeHead'],compilerPath='tools/editorial_language.py',compilerSha256=sha(ROOT/'tools/editorial_language.py'),files={p.name:sha(p) for p in sorted(PACKAGE.iterdir()) if p.is_file() and p.name!='manifest.json'}))
    style='<meta charset="utf-8"><style>body{font:18px/1.6 Georgia;max-width:1200px;margin:3em auto;padding:1em}td,th{padding:.5em;text-align:left;border-bottom:1px solid #ccc}pre{white-space:pre-wrap}</style>'
    grammar=(PACKAGE/'grammar.md').read_text(encoding='utf8');(DEST/'Wiki.md').write_text(grammar,encoding='utf8');(DEST/'Wiki.html').write_text(style+'<h1>Later dramatic 0.13</h1><pre>'+html.escape(grammar)+'</pre>',encoding='utf8')
    rows=''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in [k,e['roman'],lang.glosses.get(k,k.replace('_','-')),e['meaning'],e['usageScope']])+'</tr>' for k,e in sorted(lang.lexicon.items()))
    (DEST/'Dictionary.html').write_text(style+'<h1>Vayrshemon 0.13 dictionary</h1><p>Stable identities are distinct from printed names. Historical-reference entries require review before reuse.</p><table><tr><th>ID</th><th>Roman</th><th>Gloss</th><th>Meaning</th><th>Scope</th></tr>'+rows+'</table>',encoding='utf8')
    rows=''.join('<h2>'+html.escape(r['play']+' '+r['unitId'])+'</h2><p>'+html.escape(r['source'])+'</p><pre>'+html.escape(lang.reading(r['beforeText'])+'\n→ '+lang.reading(r['afterText'])+'\n'+r['beforeGloss']+'\n→ '+r['afterGloss'])+'</pre>' for r in read(DEST/'editorial-revisions.json'))
    (DEST/'Changes.html').write_text(style+'<h1>0.13 · Exact changes</h1>'+rows,encoding='utf8')
    write(DEST/'forge-reference.json',dict(project=str(path),head=head,branch='later-dramatic-0.13',parentHead=pin['forgeHead']))
    print('Forge/package ready; current pin intentionally not yet promoted:',head,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','publish']);args=parser.parse_args()
    {'prepare':prepare,'publish':publish}[args.command]()
