from pathlib import Path
from copy import deepcopy
import json,re,hashlib,sys
from tools.shakespeare_collected import sources,saved_source,PROJECT,ROOT
from tools.editorial_language import EditorialLanguage
from tools.kjv_historical_flow import compiler
def read(p): return json.loads(Path(p).read_bytes())
def write(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.writing')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf8');tmp.replace(p)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
S=ROOT/'.local'/'corpus-clause-review'
SV=ROOT/'Saves'
B=next(SV.glob('KJV Bible v*'))
BP=next(SV.glob('KJV Bible - Run*'))
H=next(SV.glob('The Collected Works of William Shakespeare v*'))
HP=next(SV.glob('The Collected*Progressive*'))
def ledger(w):
    return saved_source(w['currentLedger']) if w.get('currentLedger') else PROJECT/'Ledgers'/(w['slug']+'.json')
def textpaths():
    yield 'bible',B/'complete-translation-ledger.json'
    for w in sources():yield w['slug'],ledger(w)
def revised(path):return S/'files'/path.relative_to(ROOT)
def edited(path):
    p=revised(path)
    return p if p.exists() else path
def plan():
    changes={}; hist=compiler(ROOT/'data/language/archaic-kjv-285'); lang=EditorialLanguage(PROJECT/'Language')
    transcriptions=read(ROOT/'data/language/archaic-kjv-278/lexicon.json')['entries']
    quoted=('kjv_eli_quoted','kjv_eloi_quoted','kjv_lama_quoted','kjv_sabachthani_quoted','kjv_talitha_quoted','kjv_cumi_quoted','kjv_ephphatha_quoted')
    transcript=compiler(ROOT/'data/language/archaic-kjv-285')
    for key in quoted:
        for field in ('form','roman'):
            transcript.lexicon[key][field]=transcriptions[key][field]
    write(S/'quoted-readings.json',{k:{f:transcript.lexicon[k][f] for f in ('form','roman','meaning')} for k in quoted})
    review=read(PROJECT/'Reviews/marriage-verb-check.json')
    matrimony={w['work']:{u['id'] for u in w['passages']} for w in review['examples']}
    for slug,path in textpaths():
        doc=read(path); changed={};prev=''
        for u in doc['units']:
            old=u['analysis'];new=old;note=''
            if slug=='bible' and re.search(r'\bLot\b',u['source']) and re.search(r'\bkjv_lot\b',old):
                new=re.sub(r'\bkjv_lot\b','kjv_lot_person',old)
                note='Lot is the man named in the English.'
            if slug=='hamlet' and u['id']=='00064a':
                new=old.replace('marcellus_sentinel: ','marcellus_sentinel: when cock_fowl cry:pa it vanish:pa. ',1)
                u['backTranslation']='It faded when the cock crowed. '+u['backTranslation']
                note='Restored Marcellus’s observation before the reported belief.'
            if u['id'] in matrimony.get(slug,set()):
                new=re.sub(r'\bmarry(?=:(?!excl\b))','wed',old)
                note='The verb denotes entering marriage, including metaphorical and elliptical uses.'
            if (slug,u['id']) in additional:
                search,replace,note=additional[slug,u['id']]
                assert search in new,(slug,u['id'],search)
                new=new.replace(search,replace,1)
            if slug=='bible':
                for a,b in medial_questions.get(u['id'],()):
                    assert a in new
                    new=new.replace(a,b,1)
                    note='Restore the boundaries of the questions in the English.'
            back=u.get('backTranslation',u.get('backReading','')).rstrip()
            individually_reviewed=(u['id'] in extra_questions.get(slug,set()) or (slug=='bible' and u['id'] in jeremiah_questions))
            question=(u['source'].rstrip().endswith('?') and (back.endswith('?') or individually_reviewed) and new.rstrip().endswith('.')
                      and ':q' not in new.rstrip()[:-1].rsplit('.',1)[-1])
            if question:
                new=new.rstrip()[:-1]+'?'
                note=(note+' ' if note else '')+('Restore the question after checking the supplied English against the native clause.' if individually_reviewed else 'Restore the final question confirmed by both the supplied source and the passage back-reading.')
            quoted_row=slug=='bible' and u['id'] in ('40.027.046','41.015.034','41.005.041','41.007.034')
            if quoted_row:note='Preserve the foreign utterance in its attested 278 phonographic spelling before the separate English interpretation.'
            if new!=old or quoted_row:
                initial=not u.get('continuesParagraph',u.get('part',0)>0) or bool(re.search(r'[.!?]\s*\]?[ ]*$',prev))
                language=hist if slug=='bible' else EditorialLanguage(ROOT/'data/language/later-dramatic-0.13') if slug=='alls-well-that-ends-well' else lang
                def comp(a):return language.compile(a) if slug=='bible' else language.compile(a,initial=initial)
                if question and old.rstrip()[:-1]+'?'==new:
                    assert u['text'].endswith('.') and u['gloss'].endswith('.'),(slug,u['id'])
                    before={k:u[k] for k in ('text','gloss','keys')}
                    after=dict(text=u['text'][:-1]+'?',gloss=u['gloss'][:-1]+'?',keys=u['keys'])
                else:
                    before,after=comp(old),transcript.compile(new) if quoted_row else comp(new)
                change={'source':u['source'],'oldAnalysis':old,'analysis':new,'oldText':u['text'],'oldGloss':u['gloss'],'note':note}
                # Isolate the edited tokens, keeping the precise readings of each issued work.
                from difflib import SequenceMatcher
                for key,sep in [('text',' '),('gloss',' · '),('keys',None)]:
                    parts=lambda x:x.split(sep) if sep else x[:]
                    a,b,actual=map(parts,(before[key],after[key],u[key]))
                    if a==actual: value=b
                    else:
                        if len(a)!=len(actual):raise ValueError((slug,u['id'],key,len(a),len(actual)))
                        value=actual[:]
                        for tag,i,j,k,l in reversed(SequenceMatcher(None,a,b,autojunk=False).get_opcodes()):
                            if tag!='equal':
                                assert actual[i:j]==a[i:j],(slug,u['id'],key,actual[i:j],a[i:j])
                                value[i:j]=b[k:l]
                    u[key]=sep.join(value) if sep else value
                u['analysis']=new
                u['note' if slug=='bible' else 'review']=u.get('note' if slug=='bible' else 'review','').rstrip()+' '+note
                change.update({key:u[key] for key in ('text','gloss')})
                changed[u['id']]=change
            prev=old
        if changed:
            changes[slug]=changed;write(revised(path),doc)
    assert sum('Lot is the man' in u['note'] for u in changes['bible'].values())==16
    write(S/'changes.json',changes)
    print({k:len(v) for k,v in changes.items()},flush=True)
additional={
    ('alls-well-that-ends-well','0030'):('love:a to i he give:pr, so best:a rel he:a attend:fu he not can lack:fu.', 'best:a rel his/love:a attend:fu he not can lack:pr.', 'Retain “his love” and the present assurance. Remove the unsupported assertion that he gives his love to Lafew.'),
    ('bible','05.032.006'):('he make:perf and thou:a kjv_establish:perf.', 'he make:perf and thou:a kjv_establish:perf not?', 'Restore the negative question governing both made and established.'),
    ('bible','11.002.035'):('kjv_benaiah:a','kjv_benaiah:a of kjv_jehoiada son','Restore the father named in Benaiah’s apposition.'),
    ('bible','43.008.020'):('in kjv_treasury speak:pa','in kjv_treasury kjv_jesus_matthew speak:pa','Restore Yeshūa as the named speaker.'),
    ('bible','45.001.006'):('of kjv_jesus_matthew','of kjv_jesus_matthew kjv_christ_title','Restore the title Christ after Yeshūa.'),
    ('bible','52.002.019'):('kjv_jesus_matthew presence','kjv_jesus_matthew kjv_christ_title presence','Restore the title Christ after Yeshūa.'),
    ('bible','40.027.046'):('mypl/god mypl/god why thou ipl:a forsake:perf:q?', 'kjv_eli_quoted, kjv_eli_quoted, kjv_lama_quoted kjv_sabachthani_quoted?', 'Restore the quoted cry.'),
    ('bible','41.015.034'):('mypl/god mypl/god why thou ipl:a forsake:perf:q','kjv_eloi_quoted, kjv_eloi_quoted, kjv_lama_quoted kjv_sabachthani_quoted?', 'Restore the quoted cry.'),
    ('henry-iv-part-1','00387a'):('thy/age be:pa i','thy/age be:pa i, hal_prince_wales:excl,','Restore Falstaff’s direct address to Hal.'),
    ('henry-iv-part-1','00768a'):('in henry_bolingbroke/tooth:pl','in king henry_bolingbroke/tooth:pl','Retain the royal title in Douglas’s challenge.'),
    ('henry-vi-part-3','00195a'):('on small:m rise he:a place:pr they','on small:m rise richard_plantagenet:a place:pr they','Restore York’s identity in the stage direction.'),
    ('henry-vi-part-3','00345a'):('our/royal:m father mean:pr i','our/royal:m father, duke of york_plantagenet_title, mean:pr i','Restore the Duke of York’s title and territorial name.'),
    ('henry-vi-part-3','00635a'):('brother of clarence_george_duchy:excl thou here also be:pr. then see:pr i edward_york_son fall:must:pr. yet despite','yes brother of clarence_george_duchy:excl thou here also be:pr? no, then see:pr i edward_york_son fall:must:pr. yet warwick_neville_son:excl despite','Restore the opening assent, the question, the responding nay, and the address to Warwick.'),
    ('richard-iii','00924a'):('as for my/daughter:pl nun:pl','as for my/daughter:pl, richard_york_son:excl, nun:pl','Restore Elizabeth’s direct address to Richard.'),
    ('king-lear','01094a'):('albany_goneril_husband: thy/very','albany_goneril_husband: [ to edgar_gloucester_son ] thy/very','Restore the direction identifying Edgar as Albany’s addressee.'),
    ('king-lear','00443a'):('other offence than say:pr thou do:pa thou.','no other offence than that of which speak:pr thou do:pa thou?','Restore the gentleman’s negative question and its exception.'),
    ('henry-v','00103a'):('pistol_ensign:', 'pistol_ensign: [ to nym_soldier ]', 'Restore the direction identifying Nym as the addressee.'),
    ('henry-viii','00108a'):('henry_eighth_king:', 'henry_eighth_king: [ to surveyor_estate ]', 'Restore the address to the Surveyor.'),
    ('king-john','00279a'):('queen eleanor_john_mother:', 'queen eleanor_john_mother: [ to arthur_brittany_heir ]', 'Restore the Queen’s address to Arthur.'),
    ('romeo-and-juliet','00151c'):('yes by holy:m cross','nay, by holy:m cross','Restore the Nurse’s self-correction before the oath.'),
    ('henry-v','00265a'):('already forget:perf you','already forget:neg:perf you','Restore the negative question in Alice’s French.'),
}
extra_questions={k:set(v.split()) for k,v in {
    'bible':'40.019.005 40.022.044 41.002.026 41.012.011 42.011.006 45.009.024 51.002.022 52.003.010 58.002.004',
    'hamlet':'00502d',
    'henry-iv-part-1':'00229a 00375a 00394a 00415b',
    'henry-iv-part-2':'00392a 00452c 00645b',
    'henry-v':'00158a 00661a',
    'henry-vi-part-1':'00129a 00243a 00443a 00585b',
    'henry-vi-part-2':'00101a 00449b 00454b 00537a',
    'henry-vi-part-3':'00117a 00248c 00819d',
    'henry-viii':'00076a 00334b 00350a 00450a 00760a',
    'king-john':'00063a 00149a',
    'king-lear':'00578a',
    'loves-labors-lost':'00040b 00566a 00578a 00817a',
    'the-merchant-of-venice':'00006b 00102c',
    'richard-iii':'00663a 01177b',
    'the-two-noble-kinsmen':'00685a',
}.items()}
jeremiah_questions={'24.'+k for k in '''002.005 002.006 002.014 002.017 002.018 002.021 002.031 003.004
004.014 004.021 005.009 005.022 005.029 005.031 007.010 007.017 007.019 008.004
008.009 008.019 008.022 009.007 009.009 009.012 012.001 012.005'''.split()}
medial_questions={
    '24.002.014':[('servant be:pr he','servant be:pr? he'),('slave be:pr why','slave be:pr? why')],
    '24.002.018':[('drink:inf or','drink:inf? or')],
    '24.002.031':[('land of darkness why','land of darkness? why')],
    '24.004.014':[('save:psv:may how','save:psv:may. how')],
    '24.005.009':[('visit:neg:fu kjv_lord','visit:neg:fu? kjv_lord')],
    '24.005.022':[('fear:neg:pr kjv_lord','fear:neg:pr? kjv_lord')],
    '24.005.029':[('visit:neg:fu kjv_lord','visit:neg:fu? kjv_lord')],
    '24.007.019':[('kjv_provoke:pr kjv_lord','kjv_provoke:pr? kjv_lord')],
    '24.008.004':[('rise:neg:fu he','rise:neg:fu? he')],
    '24.008.019':[('kjv_zion be:neg:pr her','kjv_zion be:neg:pr? her'),('in she be:neg:pr why','in she be:neg:pr? why')],
    '24.008.022':[('kjv_gilead be:pr no','kjv_gilead be:pr? no'),('there be:pr why','there be:pr? why')],
    '24.009.009':[('visit:neg:fu kjv_lord','visit:neg:fu? kjv_lord')],
    '24.009.012':[('declare:may for what','declare:may? for what')],
    '24.012.001':[('prosper:pr why','prosper:pr? why')],
    '24.012.005':[('contend:can and if','contend:can? and if')],
}
if __name__=='__main__': plan()

