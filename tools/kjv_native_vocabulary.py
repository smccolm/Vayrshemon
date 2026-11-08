"""Author the historical KJV's native-vocabulary correction on the 284 checkpoint."""
from collections import Counter, defaultdict
from copy import deepcopy
import html
import json
from pathlib import Path
import re
import shutil
import sys

from tools import kjv_unta_chart as prior
from tools.kjv_archive import ROOT, load_register, read, verify_register
from tools.m0.common import file_hash, write_json
from vayrshemon.forge import ForgeProject, digest as snapshot_digest

VERSION='0.10-kjv.285'
PACKAGE=ROOT/'data/language/archaic-kjv-285'
OUT=ROOT/'Saves'/f'KJV Bible v{VERSION}'
COMPACT=ROOT/'Saves'/f'KJV Bible - Compact Letter Edition v{VERSION}'
RECORD=ROOT/'Saves/Maintenance/2026-11-07-native-285'
NOTE="""Ordinary speech in this edition uses Vayrshemon roots. Revelation's Alpha and Omega are the first and last written signs of the source alphabet. The Greek names and the KJV's separate beginning/end and first/last pairs remain visible in the English. The native reading uses the chart word for end, the native adjective ending, and a written mark. The older form endin was an English stem with an added ending.

For people and places we use name forms that a Vayrshemon speaker can inherit, inflect and sometimes shorten. An affiliation takes native morphology. A title, craft, musical instrument or unit of measure has to earn its own native expression. Names are identified by the local verse and a stable dictionary key. A shared pronunciation does not identify two people as one person. These adaptations are editorial decisions, not claims about ancient pronunciations. The author-selected Yeshūa and the 284 chart-based Unta readings are retained."""

# Fields are a lexical key, attested component keys, native font slots and the
# semantic decision. An explicit form can be a lexicalized contraction.
ROOT_ROWS="""last|end|hëÕ’na|At the terminal position in a series. Use the end root and its adjectival ending.
drum|skin beat|shalsleb|A struck membrane gives this instrument its native name.
bell|metal beat|zarsleb|Struck resonant metal, distinct from the membrane drum.
trumpet|horn breath|kraneni|The blown horn as a signal instrument.
cornet|horn small|kranvim|The smaller horn instrument. Keep its separate instrument key.
sea|great water|goryems|The great water, including the named sea and the figurative Temple basin.
salt|water stone|yemkwes|The crystalline substance associated with the drying of brine.
iron|bone metal|kranzar|A hard structural metal, named for the support a bone gives.
wake|awaken|ËßÛ|Use the chart-attested awakening verb for coming out of sleep.
moon|night light|ÅÙb×r|A light of the night. This is a celestial body, also used in personification.
sound|hear|jÍen|What can be heard. The nominal form extends the chart hearing root.
debt|owe|lamfëren|The obligation to give what is due, from the established owing construction.
egg|child cover|pelshal|A contained young life, a lexicalized body and cover image.
pig|nose earth|nërjoÙ|The earth-rooting animal. The root names the animal and does not add an action to the verse.
tail|body behind|vorhëÓ|Appendage at the rear of the body.
east|sun rise|bçorvel|Direction of the rising sun. Keep east distinct from the sun itself.
bellows|breath skin|enishal|A skin that drives air into a fire.
sand|stone dust|kwesthren|Small mineral grains underfoot.
ruby|red stone|azkwesil|The red precious stone.
bean|seed food|páwemin|The edible seed kind, distinct from grain.
stool|low seat|grelsilen|A low seat or support.
sneeze|nose breath|nëreni|A sudden expulsion through the nose.
spice|scent plant|nelver|An aromatic plant substance.
frost|cold dew|tézniv|Cold that sets the dew.
lap|leg bend|palklár|The fold made by the seated legs.
bear_animal|beast hair|vorfël|Lexicalized name of the heavy furred beast.
cock|morning bird|venwil|The male fowl known by its morning call.
spider|thread weave|thiravik|The thread-making creature.
beetle|cover wing|shalvÝl|The wing-cased creature named in the dietary list.
worm|small body|vimvor|The small creeping body, including figurative uses.
snail|carry cover|ÛÇdshal|The creature that carries its covering.
leopard|spot beast|pirvor|The spotted beast. Keep the species distinct from its spots.
boar|pig strong|nërjor|The powerful wild swine.
pillow|head rest|hardlen|A rest for the head.
ripe|fruit complete|venagras|Fruit come to completion.
heresy|teaching split|thronstras|A division in teaching or party, according to the source occurrence.
swoon|fall breath|grelëni|Loss of consciousness, distinguished from dying.
gross|thick|gumen|Thickness or coarseness, including a dulled heart or dense darkness.
entangle|thread bind|thirklár|Caught in bindings as in threads.
church|worship house|arvenzál|The place of worship. An assembled congregation has its own key.
dim|light less|b×rvim|Reduced light or sight.
imitate|resemble act|lßnfal|To perform after another's manner.
lurk|hidden remain|ojzhtlen|To remain concealed.
pave|stone way|kwesmar|To lay a stony surface along a way.
casement|open cover|Åelshal|An opening with a movable covering.
lantern|light carry|b×rÛÇd|A light made portable.
crack|split sound|strasjÍ|A split or its audible report.
plaster|wall cover|darshal|A covering spread on a wall.
odious|hate|zethmur|An object of aversion.
lily|flower white|falveÛ|The blossom kind associated with pale petals.
bark|dog cry|bÏebÓÅç|The dog's sharp call.
tree_bark|wood skin|yëlshal|The woody outer covering.
sparrow|small bird|vimwil|The small common bird.
grey|white dust|veÛthren|Ash-pale colour.
purge|clean remove|yatthav|Clear away an impurity.
sweep|dust push|threndar|Move dust or other matter away by repeated strokes.
chide|speak wrong|tonmur|Reprove by speech.
bore|hole cut|duldest|Make an opening by piercing.
carcass|death body|n×nvor|The dead body.
adder|serpent poison|silnam|A venomous serpent.
band|bind|klárin|Binding band or bond.
congeal|cold fixed|tézjem|Become set, as a liquid does.
guest|house other|zálves|A received outsider in the household.
berry|small fruit|vimvenam|The small fleshy fruit.
stem|plant support|verhal|A supporting stalk or shaft, also used for a common stock.
division|split|strasen|The act or result of dividing.
wink|eye shut|omibra|The brief closing of an eye, including a deliberate signal.
rail|insult|marventon|Sustained injurious speech.
roll|turn|elyiÑen|Turn over or around, distinct from simply falling.
thistle|thorn herb|kranyelin|A prickly herb.
fret|heart rub|sevarul|Inward vexation, with the figurative rubbing of a troubled heart.
fist|hand shut|trembra|The hand closed upon itself.
tongs|metal take|zarçzt|The gripping metal implement.
fodder|beast food|vorwem|Food supplied to beasts.
bundle|bind gather|klárgur|Things bound together.
hay|grass dry|yelmayems|Cut grass dried for keeping.
elm|wood branch|yëlhalin|A named branching tree kind, distinct from generic wood.
scalp|head skin|harshal|The skin of the crown of the head.
pair|two group|ÕÅtus gur|Two taken together, using the chart word for two.
shout|call strong|ÓÅçjwën|A forceful projecting call.
claw|nail sharp|jerdest|The sharp nail of a creature.
poet|song make person|lilaÙsßlum|A person who makes verse.
supper|evening meal|venmërwem|The evening meal.
lazy|work without|madÇÓna|Unwilling to work.
choke|breath shut|enibra|Shut off breath or growth.
lime|burn stone|zarkwes|The material obtained by burning, including the image of burned bones.
partition|boundary wall|threndarin|A dividing barrier.
mouse|small tooth|vimker|The small gnawing creature.
fell|skin|shalem|A hide. The source's tree-feller is a cutter, a separate verb.
vanish|see cease|ojzhfçs|Cease to be visible.
glitter|shine turn|bçoreli|Repeated moving points of light.
dainty|fine food|elinwem|A delicately chosen food or quality.
mote|small dust|vimthren|A particle small enough to get into the eye.
leek|leaf onion|yëletrëmen|The long-leaved edible plant.
shear|hair cut|fëldest|Cut away a covering of hair or wool.
howl|cry long|ÓÅçven|A drawn-out cry.
screech|cry sharp|ÓÅçdest|A sharp high cry.
gape|mouth open|tomÅel|Open the mouth wide.
broom|twig gather|yëlgur|Gathered twigs for sweeping.
blot|stain|murden|A blemish or disgracing mark. Erasing writing uses the erasure verb.
mustard|seed sharp|pádest|The sharp seed kind, including the comparison of its size.
kjv_witch|enchant person|fëlmirsßlum|A practitioner of forbidden enchantment under the source designation.
cup|hand vessel|tremborel|A hand-held drinking vessel.
scroll|write roll|Ývely|The writing rolled for keeping.
sail|wind cloth|enifelen|A cloth that catches the wind. It also names travel under sail."""

# These occurrences have distinct meanings even though older analyses used the
# same English-facing dictionary key.
CONTEXT={
    'Genesis 31:29':('last night','former night'), 'Genesis 31:42':('last night','former night'),
    'Judges 14:17':('last:pa','continue:pa'),
    'Isaiah 14:8':('fell:ag','cut:ag'),
    'Revelation 22:16':('church:pl','kjv_church_assembly:pl'),
}
for ref in ('Nehemiah 4:5','Psalms 109:13','Psalms 109:14','Isaiah 43:25','Isaiah 44:22','Jeremiah 18:23','Acts 3:19','Revelation 3:5'):
    CONTEXT[ref]=('blot:','erase:')

# Sound adaptations of named bearers. Apply per semantic entry, including
# namesakes, never by substituting a substring across arbitrary headwords.
NAMES={
    'jerusalem':'yerçÛalem','jordan':'yard×n','judah':'yehçdÅ','judea':'yçd×a',
    'israel':'yisrÅl','abraham':'avrÅham','abram':'avrÅm','jakob':'yÅkov','josef':'yßsef',
    'david':'dawÝd','moses':'mßÛe','aaron':'aharßn','saul':'ÛÅul','solomon':'ÛelomÅn',
    'jon':'yßn','peter':'p×tar','paul':'pÅvol','elijah':'eliyÅ','jeremiah':'yiremya',
    'benjamin':'benyamin','reuben':'rçben','satan':'satÅn',
}

EXTRAS="""navigator|sea way person|goryemmar|The person who finds a way across the great water.
near|distance small|thavvim|At a short distance.
approach|near come|thavvimtçl|Come within a short distance.
next|near|thavvimna|The adjoining or next member in order.
young|child|pelna|Of an early age, using the native offspring family.
new|begin become|páf×|Newly come into being.
silk|thread soft|thirmel|The soft fine thread and its cloth.
roar|great sound|gorjÍen|The great carrying sound of a beast or waters.
melt|warm flow|velren|Become flowing under warmth.
door|wall open|darÅel|The opening in a wall, or its closure.
rain|sky water|nabyems|Water that falls from the sky.
owl|night bird|ÅÙwil|The bird of the night.
dale|low land|greljoÙ|A valley, the lower land between heights.
mud|earth water|joÙyem|Earth mixed with water.
kjv_plaster_apply|wall cover|darshal|The act of spreading a covering on a wall.
ship|wood water|yëlyemar|The water-going vessel. Separate from the cloth sail.
voyage|sea way|goryemmarin|Passage across the great water.
wash|water clean|yemyat|To clean with water.
distil|water drop|yemtin|Water falling in small drops.
brine|salt water|yemkwesyems×|Water carrying salt.
mermaid|sea maiden|goryem salin|Legendary sea maiden.
groan|harm sound|murjÍen|A sound of suffering.
pulse|heart sound|sevarjÍen|The beating heard or felt from the heart.
kjv_sea_basin|sea|goryems|Retain the Temple vessel's metaphorical name, Sea.
wane|moon less|ÅÙb×rvim|The visible light of the moon diminishes.
kjv_augustus_luke||augçstos|A transmitted personal designation for this named ruler.
kjv_melzar|keeper|jemoi|Daniel's appointed keeper, addressed by his local role. The KJV designation is preserved in English and the proper-name/office ambiguity is documented.
kjv_hammelech||hameleÕ|The source treats this as a parent's designation. Do not replace it by an assumed royal title.
kjv_jasher|kjv_upright|jeminsevar|The Upright, the title in a book citation. Preserve both citations without supplying a new personal author.
kjv_jachin_pillar|fixed stand|jemkoj|Steadfast-standing, the right pillar's own name. Keep the person named Jachin separate.
kjv_boaz_pillar|power|jwënen|Strength, the left pillar's literary name in this edition. This reading of the name is uncertain. The man in Ruth has his own name.
kjv_alpha_letter_revelation|first write mark|neksus’t Ývden|The first written sign of the named source alphabet.
kjv_omega_letter_revelation|last write mark|hëÕ’na Ývden|The last written sign of that same alphabet."""

OFFICES={
    'kjv_tartan': ('haren hefak gur', ['chief','army'], 'Military commander, an Assyrian office.'),
    'kjv_rabsaris': ('varßnna zál haren', ['royal','house','chief'], 'Chief of the royal household, an Assyrian court office.'),
    'kjv_rabsaris_babylon': ('varßnna zál haren', ['royal','house','chief'], 'Chief of the royal household at the Babylonian court. This is a separate source identity.'),
    'kjv_rabshakeh': ('tremborel jemãsßlum haren', ['cup','keeper','chief'], 'Chief cupbearer, an office held by the Assyrian spokesman.'),
}
# Source affiliations with English endings other than -ite, and local exceptions.
AFFILIATIONS={
    'kjv_syrian':('kjv_syria','','Association with Syria.'),
    'kjv_sidonian':('kjv_sidon','','Association with Sidon.'),
    'kjv_zidonian':('kjv_zidon','','Association with Zidon, under this distinct source spelling.'),
    'kjv_babylonish':('kjv_babylon','','Style or provenance of the garment in Joshua.'),
    'kjv_chaldean':('kjv_chaldea','','Chaldean affiliation, including court settings.'),
    'kjv_chaldees':('kjv_chaldea','','Collective people designation in the source.'),
    'kjv_lydian':('kjv_lydia','','Affiliation with the land or people named in Ezekiel.'),
    'kjv_parthian_acts':('', 'part', 'A people in the Acts hearing roster.'),
    'kjv_thessalonian_acts':('kjv_thessalonica_acts','','Affiliation with Thessalonica.'),
    'kjv_roman_john':('kjv_rome_acts','','Roman citizenship or imperial affiliation as the passage requires.'),
    'kjv_crete_people_acts':('kjv_crete_island_acts','','A person or people of Crete.'),
    'kjv_shulamite':('', 'Ûulam','Designation of the woman addressed in the Song. Her precise origin is unspecified.'),
    'kjv_korathites':('', 'koraÕ','Family designation in Numbers 26:58. Keep it distinct from Korahites.'),
}

def vocabulary(language):
    old=language.lexicon
    out=deepcopy(old)
    decisions={}
    def revise(key,form,parts,reason,kind):
        assert key in old and set(parts)<=old.keys(),key
        assert set(form)<=language.letters|{' ','’','-'},(key,form)
        before=old[key]
        if form==before['form']:return
        decisions[key]=dict(kind=kind,before=before['form'],after=form,components=parts,reason=reason)
        e=out[key]=deepcopy(before)
        e.setdefault('historicalForms',[]).append(dict(version=prior.VERSION,form=before['form'],roman=language.reading(before['form'])))
        e.update(form=form,roman=language.reading(form),derivationKeys=parts,register=VERSION,
                 origin='285 editorial vocabulary review. '+reason,
                 note=reason,evidence='Authored historical-register revision. Original source references and lexical identity are retained.')
    for row in (ROOT_ROWS+'\n'+EXTRAS).splitlines():
        key,parts,form,reason=row.split('|')
        revise(key,form,parts.split(),reason,'ordinary vocabulary' if key not in ('kjv_augustus_luke','kjv_hammelech') else 'localized name')
    for key,(form,parts,reason) in OFFICES.items():
        revise(key,form,parts,reason,'native office')
    for key,(base,stem,reason) in AFFILIATIONS.items():
        parts=[base] if base else []
        stem=language.maxima(old[base]['form'] if base else stem)
        form=stem+'’na'
        if key=='kjv_shulamite':
            form+=' '+old['female']['form']
            parts.append('female')
        revise(key,form,parts,reason+' The affiliation uses the native relational adjective.','native affiliation')
    for book in ('job','isaiah','ezekiel','joel'):
        revise('kjv_sabeans_'+book,'SÅba '+old['group']['form'],['group'],
               'A transmitted collective name with the native word for group. Preserve this passage’s separate identity.','native affiliation')
    for key,e in old.items():
        if key not in decisions and e['pos']=='proper' and e['form'] in NAMES:
            revise(key,NAMES[e['form']],e.get('derivationKeys',[]),'Adapt the transmitted name to this register. Preserve this bearer and the KJV spelling in the source column.','localized name')
    # The affiliation ending does not itself establish whether its stem is a
    # place, ancestor, people or office. Preserve that uncertainty in the gloss.
    for key,e in old.items():
        label=key.removeprefix('kjv_').split('_')[0]
        if key in decisions or not key.startswith('kjv_') or not re.search(r'(?:ite|ites|itess)$',label) or not e['form'].endswith('it'):continue
        stem=e['form'][:-2]
        if key=='kjv_ammonitess':stem=old['kjv_ammon']['form']
        if key=='kjv_areopagite_acts':stem=old['kjv_areopagus_acts']['form']
        stem=NAMES.get(stem,stem)
        feminine=label.endswith('itess')
        if feminine and stem.startswith(old['woman']['form']):stem=stem[len(old['woman']['form']):]
        form=language.maxima(stem)+'’na'+(' '+old['female']['form'] if feminine else '')
        revise(key,form,['female'] if feminine else [],
               'Local affiliation stem with the native relational adjective.'+(' Retain the explicit feminine designation.' if feminine else '')+
               ' The expression does not choose between descent, residence and allegiance without evidence in the verse.',
               'native affiliation')
    for key,e in old.items():
        if key in decisions or not key.startswith('kjv_') or e['pos']!='proper' or e.get('derivationKeys'):continue
        if not re.search(r'\b(?:proper (?:form|name)|source name|named|son|daughter|father|mother|town|city|place|king|priest|prophet|river|wife|brother|sister)\b',e['meaning'],re.I):continue
        form=e['form']
        if ' ' in form or form.endswith('’na'):continue
        if form.startswith('j'):form='y'+form[1:]
        if form.endswith('iah'):form=form[:-3]+'ya'
        if form!=e['form']:
            revise(key,form,[],'A transmitted name in this register uses the y onset or final -ya. This is an editorial naming convention, not a reconstructed sound law. Keep the specific source bearer.','localized name')
    # Carry corrections only along declared semantic edges. Match complete
    # constituent spans in the old compound, never free substrings in a verse.
    explicit=set(decisions)
    for _ in range(15):
        updates=0
        for key,e in old.items():
            if key in explicit or key.startswith('unta_'):continue
            deps=e.get('derivationKeys',[])
            if not any(d in decisions for d in deps) or not all(d in old for d in deps):continue
            form=e['form'];revised=form;changed=[]
            # Use the longest constituent first when one is nested in another.
            parts=[]
            for d in sorted(set(deps),key=lambda d:-len(old[d]['form'])):
                if d not in decisions:continue
                a,b=old[d]['form'],out[d]['form']
                for source,target in dict([(a,b),(language.maxima(a),language.maxima(b))]).items():
                    for m in re.finditer(re.escape(source),form):
                        if not any(m.start()<right and m.end()>left for left,right,_ in parts):
                            parts.append((m.start(),m.end(),target))
                            changed.append(d)
            for left,right,target in sorted(parts,reverse=True):revised=revised[:left]+target+revised[right:]
            if revised!=out[key]['form']:
                revise(key,revised,deps,'Retain the corrected native constituent in this established word ('+', '.join(dict.fromkeys(changed))+').','dependent vocabulary')
                updates+=1
        if not updates:break
    else:raise ValueError('Unresolved lexical dependencies')
    assert out['last']['form']==language.word('end:adj')[0]
    assert out['kjv_omega_letter_revelation']['form']==out['last']['form']+' '+out['write']['form']+out['mark']['form']
    assert out['kjv_alpha_letter_revelation']['form']==out['first']['form']+' '+out['write']['form']+out['mark']['form']
    assert not any('endin' in e['form'].casefold() for e in out.values())
    return out,decisions

def inspect():
    lang,_=load_register(prior.VERSION)
    entries,decisions=vocabulary(lang)
    units=read(prior.OUT/'complete-translation-ledger.json')['units']
    count=Counter(k for u in units for k in u['keys'])
    print(Counter(d['kind'] for d in decisions.values()))
    print('Active lexical keys',sum(count[k]>0 for k in decisions),'affected verses',sum(bool(set(u['keys'])&decisions.keys()) or u['reference'] in CONTEXT for u in units))
    for k in decisions:
        if decisions[k]['kind']=='ordinary vocabulary' and not count[k]:print('Dictionary only',k)
    return entries,decisions

def update_forge_lexicon(snapshot,lex,decisions):
    entries=snapshot['language']['lexicon']
    seen=set();updated=[]
    for entry in entries:
        keys=entry['label'].split(' / ')
        if not decisions.keys() & set(keys):
            updated.append(entry);continue
        assert all(k in lex for k in keys)
        if len(keys)==1:
            key=keys[0];source=lex[key]
            entry.update(headword=source['form'],pronunciation=source['roman'],etymology=source['origin'],notes=source['note'])
            entry['senses'][0]['definition']=source['meaning']
            updated.append(entry);seen.add(key);continue
        # The early drama Forge grouped unrelated homophones and ordinary
        # derivations under one printed headword. Split only affected groups.
        groups=defaultdict(list)
        for key in keys:groups[lex[key]['form']].append(key)
        first=next((v for v in groups if v==entry['headword']),next(iter(groups)))
        for form,members in groups.items():
            record=deepcopy(entry)
            if form!=first:record['id']='kjv285.lex.'+members[0]
            record.update(label=' / '.join(members),headword=form,pronunciation=lex[members[0]]['roman'],
                etymology=lex[members[0]]['origin'],notes='\n'.join(k+' — '+lex[k]['origin'] for k in members))
            record['senses']=[deepcopy(s) for s in entry['senses'] if s['id'].split('.')[-1] in members or s['definition'].split(':')[0] in members]
            assert len(record['senses'])==len(members),(members,record['senses'])
            for sense in record['senses']:
                k=sense['definition'].split(':')[0]
                if k not in members:k=sense['id'].split('.')[-1]
                sense['definition']=k+': '+lex[k]['meaning']
                if form!=first:
                    assert not any(sense['id'] in t['senseIds'] for row in snapshot['language']['corpus'] for t in row['tokens'])
            updated.append(record)
            seen.update(set(members)&decisions.keys())
    for key in sorted(decisions.keys()-seen):
        source=lex[key]
        new=deepcopy(next(r for r in updated if r['label']=='kjv_omega_letter_revelation'))
        new.update(id='kjv285.lex.'+key,label=key,headword=source['form'],pronunciation=source['roman'],
            partOfSpeech=source['pos'],etymology=source['origin'],notes=source['note'],citations=[],variants=[],
            senses=[dict(id='kjv285.sense.'+key,definition=source['meaning'],status='draft',citations=[])])
        updated.append(new)
    snapshot['language']['lexicon']=updated

def write_dictionary(language):
    if (OUT/'FROZEN.json').exists():
        raise FileExistsError('The edition is sealed')
    style='<meta charset="utf-8"><style>body{max-width:70em;margin:3em auto;font:18px/1.6 Georgia}td,th{padding:.4em;text-align:left}</style>'
    glossary=read(PACKAGE/'morphology.json')['glosses']
    rows=''.join('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in
        (k,language.reading(e['form']),glossary.get(k,''),e['meaning']))+'</tr>'
        for k,e in sorted(language.lexicon.items()))
    (OUT/'Dictionary.html').write_text(style+'<h1>KJV 285 historical dictionary</h1><table><tr><th>Key</th><th>Reading</th><th>Gloss</th><th>Meaning</th></tr>'+rows+'</table>',encoding='utf8')

def prepare(amend=False):
    if any((p/'FROZEN.json').exists() for p in (OUT,COMPACT)) or (OUT/'KJV Bible.vay').exists():
        raise FileExistsError('The historical publication already exists')
    if amend != (PACKAGE/'manifest.json').exists():
        raise FileExistsError('Draft amendment requires the existing unpublished checkpoint')
    draft_head=verify_register(VERSION)['forgeHead'] if amend else None
    lang,manifest=load_register(prior.VERSION)
    lex,decisions=vocabulary(lang)
    for d in (PACKAGE,OUT,COMPACT,RECORD):d.mkdir(parents=True,exist_ok=True)
    for name in manifest['files']:shutil.copyfile(prior.PACKAGE/name,PACKAGE/name)
    inherited=read(PACKAGE/'lexicon.json')
    inherited.update(version=VERSION,entries=lex)
    # Preserve lexical nuance while removing superseded borrowing directions from
    # the active entries. Earlier definitions remain in the parent register.
    for k,r in decisions.items():
        if r['kind']=='native affiliation':
            lex[k]['meaning']=re.sub(r' retained as an authored borrowing[^.]*',' rendered by a native affiliation form',lex[k]['meaning'])
        if k=='kjv_melzar':lex[k]['meaning']='Daniel’s appointed keeper. Melzar is the source designation. Its name or office status is uncertain.'
        if k in OFFICES:lex[k]['meaning']=OFFICES[k][2]
    write_json(PACKAGE/'lexicon.json',inherited)
    current=prior.parent.compiler(PACKAGE)
    ledger=read(prior.OUT/'complete-translation-ledger.json')
    changes=[]; references=defaultdict(list)
    for u in ledger['units']:
        a=u['analysis'];ref=u['reference']
        if ref in CONTEXT:
            orig,new=CONTEXT[ref]
            assert a.count(orig)==1,(ref,orig,a)
            a=a.replace(orig,new)
        output=current.compile(a)
        if a!=u['analysis'] or output['text']!=u['text'] or output['gloss']!=u['gloss']:
            keys=sorted(set(u['keys'])&decisions.keys())
            assert keys or ref in CONTEXT,ref
            changes.append(dict(id=u['id'],reference=ref,parentText=u['text'],text=output['text'],keys=keys,
                                beforeAnalysis=u['analysis'],afterAnalysis=a))
            u.update(analysis=a,**output)
        for k in set(u['keys']):references[k].append(ref)
        if 'kjv_omega_letter_revelation' in u['keys']:
            u['note']+=' The alphabetic pair uses first/last writing-marks in 285. The separate sequence terms in the speech retain their own wording.'
    assert len(ledger['units'])==31102 and len(references['kjv_omega_letter_revelation'])==4
    ledger.update(version=VERSION,correctionOf=prior.VERSION)
    write_json(OUT/'complete-translation-ledger.json',ledger)
    write_json(OUT/'correction-ledger.json',changes)
    index={u['id']:u for u in ledger['units']}
    write_json(PACKAGE/'flow-cases.json',[index[f['id']] for f in read(prior.PACKAGE/'flow-cases.json')])
    for k,r in decisions.items():
        r.update(beforeRoman=lang.reading(r['before']),afterRoman=current.reading(r['after']),verses=references[k])
    write_json(PACKAGE/'vocabulary-review.json',dict(parent=prior.VERSION,entries=decisions,contextualAnalyses=CONTEXT,
        sourceNotes={'Jasher':'https://classic.net.bible.org/passage.php?passage=Jos+10%3A13',
                     'Assyrian offices':'https://bible.usccb.org/bible/2kings/18',
                     'Jachin and Boaz':'https://classic.net.bible.org/verse.php?book=1Ki&chapter=7&theme=false&verse=21'}))
    (PACKAGE/'vocabulary.md').write_text(NOTE+'\n',encoding='utf8')
    summary=dict(version=VERSION,parent=prior.VERSION,verses=31102,sections=66,revisedVerses=len(changes),
                 dictionaryEntries=len(lex),usedKeys=len([k for k in references if references[k]]),
                 changedLexicalForms=len(decisions),changedUsedKeys=sum(bool(references[k]) for k in decisions),
                 categories=dict(Counter(r['kind'] for r in decisions.values())),contextualAnalyses=len(CONTEXT),
                 parentLedgerSha256=file_hash(prior.OUT/'complete-translation-ledger.json'),
                 chartQuantitiesSha256=file_hash(PACKAGE/'quantities.json'),sourcePreserved=True)
    assert summary['chartQuantitiesSha256']==file_hash(prior.PACKAGE/'quantities.json')
    write_json(OUT/'language-delta.json',summary)
    write_json(PACKAGE/'coverage-summary.json',summary)
    # Read-only, source-linked review inventory. It distinguishes unchanged
    # inherited entries from entries for which this impression makes a decision.
    write_json(RECORD/'lexical-inventory.json',{k:dict(roman=current.reading(e['form']),role=e['pos'],
        basis=e['origin'],decision=decisions[k]['kind'] if k in decisions else 'retained from 284',
        verses=references[k]) for k,e in lex.items()})
    previous=read(prior.OUT/'current-snapshot.json');assert previous['head']==manifest['forgeHead']
    path=OUT/'KJV 285.vayforge'
    if path.exists():
        forge=ForgeProject(path);imp=read(OUT/'forge-import.json')
        assert imp['originalHead']==previous['head'] and (draft_head or imp['localImportHead'])==forge.status()['head']
    else:
        forge=ForgeProject.create(path,'KJV 285 · native vocabulary and transmitted names',snapshot=previous['snapshot'])
        write_json(OUT/'forge-import.json',dict(originalHead=previous['head'],localImportHead=forge.status()['head'],
            importedSnapshotSha256=snapshot_digest(previous['snapshot']),parentProject=prior.OUT.name+'/KJV 284.vayforge'))
    snap=previous['snapshot'];update_forge_lexicon(snap,lex,decisions)
    rows={u['id']:u for u in ledger['units']};fixtures=0
    for t in snap['tests']:
        if t['id'].startswith('kjv284.verse.'):
            uid=t['id'].removeprefix('kjv284.verse.');u=rows[uid]
            t.update(id='kjv285.verse.'+uid,title='KJV 285 · '+u['reference'])
            t['paragraphs'][0].update(text=u['text'],translation=u['source'],
                    analysis=u['gloss']+'\nAnalysis: '+u['analysis']+'\n'+u['note'])
            fixtures+=1
    assert fixtures==31102
    snap['wiki'].insert(0,dict(id='kjv285-vocabulary',title='Native words and transmitted names',body=NOTE,ruleIds=[]))
    snap['research']['kjv285Vocabulary']=summary
    st=forge.replace_draft(snap,forge.status()['generation'])
    head=forge.commit('KJV 285 · native vocabulary and transmitted names',st['generation'])['head']
    write_json(OUT/'current-snapshot.json',dict(head=head,snapshot=snap))
    for folder in (OUT,COMPACT):write_json(folder/'forge-reference.json',dict(project=str(path),branch='main',head=head,parentHead=previous['head']))
    names=[*manifest['files'],'vocabulary-review.json','vocabulary.md']
    pkg=dict(version=VERSION,policy='never-modernize',basePackage=prior.PACKAGE.relative_to(ROOT).as_posix(),
        baseManifestSha256=file_hash(prior.PACKAGE/'manifest.json'),baseForgeHead=previous['head'],forgeHead=head,
        compilerPath=(PACKAGE/'compiler.py').relative_to(ROOT).as_posix(),compilerSha256=file_hash(PACKAGE/'compiler.py'),
        files={n:file_hash(PACKAGE/n) for n in names})
    write_json(PACKAGE/'manifest.json',pkg)
    registry=read(ROOT/'data/language/historical.json')
    if amend:
        assert [r['forgeHead'] for r in registry['registers'] if r['version']==VERSION]==[draft_head]
        registry['registers']=[r for r in registry['registers'] if r['version']!=VERSION]
        write_json(RECORD/'draft-checkpoint.json',dict(unpublishedDraftHead=draft_head,finalHead=head))
    else:assert not any(row['version']==VERSION for row in registry['registers'])
    registry['registers'].append(dict(version=VERSION,package=PACKAGE.relative_to(ROOT).as_posix(),
        manifestSha256=file_hash(PACKAGE/'manifest.json'),forgeHead=head,policy='never-modernize',guide='docs/KJV_ARCHIVE.md'))
    write_json(ROOT/'data/language/historical.json',registry);verify_register(VERSION)
    style='<meta charset="utf-8"><style>body{max-width:70em;margin:3em auto;font:18px/1.6 Georgia}td,th{padding:.4em;text-align:left}pre{white-space:pre-wrap}</style>'
    write_dictionary(current)
    wiki=NOTE+'\n\n'+(prior.OUT/'Wiki.md').read_text(encoding='utf8')
    (OUT/'Wiki.md').write_text(wiki,encoding='utf8')
    (OUT/'Wiki.html').write_text(style+'<h1>KJV 285 grammar and vocabulary</h1><pre>'+html.escape(wiki)+'</pre>',encoding='utf8')
    print(head,summary,flush=True)

if __name__=='__main__':
    prepare(amend='--amend' in sys.argv)
