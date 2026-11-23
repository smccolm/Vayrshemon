"""Short examples reconstructed from explicit grammatical relations in attested wording."""
import re
from tools.dictionary_sentence_witnesses import BAD,REMOTE,FINITE,anchors,head_present

NAME=r"[A-Z][A-Za-z’'\-]+"
KIN='son|daughter|wife|father|mother|sister|brother|servant|captain|king|prince|duke'
def witness_name(s,source):
    label=s['label'].split('{')[0].strip()
    words=[label,label.replace('-',' '),re.split('[- ]',label)[0]]
    words+=re.findall(NAME,s.get('meaning','')[:38])+[s.get('key','').removeprefix('kjv_').split('_')[0]]
    for w in words:
        if len(w)<2 or w.lower() in ('source','native','the','role','name','earlier'):continue
        m=re.search(r'(?<![\w-])'+re.escape(w)+r'(?![\w-])',source,re.I)
        if m:return m[0]
    return label

def local_example(editor,s,ctx):
    source=' '.join(ctx['source'].split()).replace('ſ','s')
    if BAD.search(source) or REMOTE.search(source):return
    key=s['key'];name=witness_name(s,source);esc=re.escape(name)
    native=ctx['text'].strip()
    syntax=ctx['analysis'].strip()
    gloss=ctx['gloss'].strip()
    proper=s['pos']=='proper'
    def make(a,e):return editor.compile(a,e,'source construction')
    def alias(value):
        for k in dict.fromkeys(re.findall(r'[a-zA-Z][a-zA-Z_0-9]*',syntax)):
            recs=editor.d.keyrefs.get(k)
            if k!=key and recs and recs[0]['pos']=='proper' and k in editor.lang.lexicon and witness_name(recs[0],source).casefold()==value.casefold():
                return k
    if proper:
        for m in re.finditer(rf'\b({NAME}),? (?:the )?({KIN}) of ({NAME})\b',source):
            a,rel,b=m.groups()
            if a==b:continue
            if a.casefold()==name.casefold() and (other:=alias(b)):
                return make(f'@ {rel} of {other} be:pa.',f'{a} was the {rel} of {b}.')
            if b.casefold()==name.casefold() and (other:=alias(a)):
                return make(f'{other} {rel} of @ be:pa.',f'{a} was the {rel} of {b}.')
        relatives=re.findall(rf'\b({NAME}) his son\b',source)
        for a,b in zip(relatives,relatives[1:]):
            if b==name and (other:=alias(a)):return make(f'@ son of {other} be:pa.',f'{b} was the son of {a}.')
            if a==name and (other:=alias(b)):return make(f'{other} son of @ be:pa.',f'{b} was the son of {a}.')
        for m in re.finditer(rf'\b({NAME}) (?:the|an?) ({NAME}(?:ite|ean|ian))\b',source):
            a,b=m.groups()
            if a==name and (other:=alias(b)):return make(f'@ {other} be:pa.',f'{a} was a {b}.')
            if b==name and (other:=alias(a)):return make(f'{other} @ be:pa.',f'{a} was a {b}.')
    # Restore full predicate-bearing sentences from a paragraph, including
    # independent clauses ending with the colon of the early printed source.
    if ': ' in syntax and re.match(r'^\w+(?::[a-z]+)*:',syntax) and ': ' in native and ': · ' in gloss:
        cue,rest=syntax.split(': ',1)
        speaker=re.match(r"^([A-Z][A-Z ’'\-,]*(?= [A-Z][a-z]| [Ii]\b| [Aa]\b))\s+",source)
        if speaker:
            source=source[speaker.end():]
            syntax=rest; native=native.split(': ',1)[1];gloss=gloss.split(': · ',1)[1]
            if key==cue:
                sel=re.split(r'(?<=[.!?])\s+',source)[0]
                a=re.split(r'(?<=[.!?])\s+',syntax)[0]
                n=re.split(r'(?<=[.!?])\s+',native)[0]
                g=re.split(r'(?<=[.!?])\s+·\s+',gloss)[0]
                if FINITE.search(a) and 1<=len(sel.split())<=22 and 1<=len(n.split())<=19 and sel[-1:] in '!?.' and n[-1:] in '!?.' and ':' not in n:
                    return said(editor,s,speaker[1].strip().title(),n,g,sel)
    gs=re.split(r'(?<=[.!?;:])\s+·\s+',gloss)
    ns=re.split(r'(?<=[.!?;:])\s+',native)
    ans=re.split(r'(?<=[.!?;:])\s+',syntax)
    es=re.split(r'(?<=[.!?;:])\s+',source)
    options=[]
    if len(ns)==len(ans)==len(gs):
        for n,a,g in zip(ns,ans,gs):
            if not FINITE.search(a) or not head_present(n,s['form']):continue
            if not re.search(r'(?<![a-zA-Z_0-9])'+re.escape(key)+r'(?![a-zA-Z_0-9])',a):continue
            for e in es:
                if proper and not re.search(r'\b'+esc+r'\b',e,re.I):continue
                ga=anchors(g,True);ea=anchors(e)
                overlap=len(ga & ea)
                if overlap>=2 and overlap/max(len(ga),len(ea),1)>=.63:options.append((n,a,g,e))
    if len(es)==len(ns)==1 and FINITE.search(syntax):options.append((native,syntax,gloss,source))
    for n,a,g,e in sorted(options,key=lambda it:len(it[0].split())):
        if not 2<=len(n.split())<=41 or not 3<=len(e.split())<=58 or not head_present(n,s['form']):continue
        if BAD.search(n+' '+e) or ':' in n[:-1] or re.match(r'^(?:who|whose|which|when|if|because|whereas|until|though|as though|after that|forasmuch)\b',e,re.I):continue
        if re.match(r'^[A-Z][A-Z ]{3,}\s',e):continue
        if n[-1:] not in '.?!;:,' or e[-1:] not in '.?!;:,':continue
        n=n.rstrip(',;:');g=g.rstrip(',;:');e=e.rstrip(',;:')
        if not n.endswith(('.','?','!')):n+='.'
        if not e.endswith(('.','?','!')):e+='.'
        return dict(native=editor.lang.maxima(n),gloss=g,english=e[:1].upper()+e[1:],book=ctx['book'],ref=ctx['reference'],method='attested clause')

def said(editor,s,name,n,g,e):
    prefix=editor.compile('@ say:pa.','')
    return dict(native=prefix['native'][:-1]+': '+editor.lang.maxima(n),gloss=prefix['gloss'][:-1]+': '+g,english=name+' said, “'+e+'”',method='attributed speech')

def named_context(editor,s,ctx,name,role):
    """Use the actual kind of record when a roll, an allotment or a title is the sole witness."""
    key=s['key']
    desc=s['meaning'].lower()
    ref=str(ctx['reference']);src=ctx['source']
    def make(a,e):return editor.compile(a,e,'contextual use')
    m=re.match(r'Nehemiah 10:(\d+)$',ref)
    if m and int(m[1])<=27 and (('sign' in key or 'seal' in desc) or re.fullmatch(r"[A-Za-z’, ;.\-]+",src) and len(src.split())<12):
        return make('@ among they who kjv_covenant:a seal:pa be:pa.',f'{name} was among those who sealed the covenant.')
    if role in ('ship',) or re.search(r'\b(?:named ship|ship named|ship commanded|ship on which)\b',desc):
        return make('from shore @:a see:pr thou?',f'Can you see {name} from the shore?')
    if key.startswith(('locke_first_','locke_second_','hobbes_book_')) or 'scripture title' in desc or role=='book':
        return make('at end of @ this passage:a find:pa i.',f'I found this passage at the end of {name}.')
    if re.search(r'itinerary|encampment|journey station',desc) and 'camp' in src.lower() or re.search(r'\bpitched in '+re.escape(name)+r'\b',src,re.I):
        return make('at @ they camp:pa.',f'They camped at {name}.')
    if 'genealog' in desc or 'family line' in desc or 'ancestry' in desc or 'sons list' in desc:
        return make('in account of kin @:a wepl find:pr.',f'We find {name} in the family genealogy.')
    if re.search(r'\b(?:signer|seal-list|seal list)\b',desc):
        return make('on roll his/name as @ write:psv:perf.',f'On the roll his name is written as {name}.')
    if role in ('city','town','village','island','river','harbour','bay','country','valley','hill','mountain','region','sea','place'):
        frames={
         'river':('where @ sea:a reach:pr?',f'Where does {name} reach the sea?'),
         'island':('at kjv_dawn towards @ sail:pa wepl.',f'At dawn we sailed toward {name}.'),
         'harbour':('in @ ship:pl how many be:pr?',f'How many ships are in {name}?'),
         'bay':('across @ one ship sail:pa.',f'A ship sailed across {name}.'),
         'mountain':('from valley @:a see:pr wepl.',f'We can see {name} from the valley.'),
         'hill':('from here @:a see:pr thou?',f'Can you see {name} from here?'),
         'country':('of @ people what tongue speak:pr?',f'What language do the people of {name} speak?'),
         'sea':('across @ how long sail:pa you?',f'How long did you sail across {name}?'),
         'town':('to @ which way lead:pr?',f'Which way leads to {name}?'),
         'city':('at gate of @ wepl wait:pa.',f'We waited at the gate of {name}.')}
        a,e=frames.get(role,('from here to @ how far be:pr?',f'How far is it from here to {name}?'))
        return make(a,e)
    if re.search(r'\b(?:epithet|surname|byname|nickname|family name)\b',desc):
        return make('by name @ his/companion:pl he:a know:pa.',f'His companions knew him by the name {name}.')
    if 'saint' in desc and 'invok' in desc:
        return make('in oath he saint @:a call:pa.',f'In his oath he called upon Saint {name}.')
    if role in ('author','writer','poet'):
        return make('what @ of this write:pa?',f'What did {name} write about this?')
    if role in ('king','queen','prince','duke','ruler','governor','lord'):
        return make('who before @ counsel:a give:pa?',f'Who offered counsel before {name}?')
    if role in ('priest','prophet','bishop','friar'):
        return make('to word:pl of @ listen:imp.',f'Listen to the words of {name}.')
    if role in ('captain','general_commander','soldier','officer'):
        return make('under whose command @ serve:pa?',f'Under whose command did {name} serve?')
