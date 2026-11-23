"""Prepare parallel examples and print definitions from the same lexical articles."""
from collections import Counter
from copy import copy
import re

from tools.dictionary_corpus import ROOT, WORK, normalize, read
from tools.dictionary_definitions import part_of_speech, usage_note
from tools.dictionary_lexicon import load_gzip
from tools.dictionary_sentence_witnesses import CACHE, FINITE, BAD, REMOTE, head_present


def lines(path):
    return [s.split(' | ') for s in path.read_text(encoding='utf-8-sig').splitlines() if s and not s.startswith('#')]


def keyed(path):
    return {k:(a,e) for ks,a,e in lines(path) for k in ks.split('/')}


def label(s):
    return s['label'].partition('{')[0].strip().replace('_',' ')


def end(s):
    return s.rstrip() if s.rstrip().endswith(('.','?','!')) else s.rstrip(' ,:;')+'.'


# A single concrete setting for each category. These are composed illustrations.
SCENES = [
('bird|eagle|heron|hawk|sparrow|fowl|quail|falcon|raven','@ from branch rise:pa.','The {} rose from the branch.'),
('fish|shark|whale|porpoise|dolphin','from ship @ see:pa wepl.','From the ship we saw the {}.'),
('serpent|lizard|snake|viper|adder','under stone @ lie:pa.','The {} lay under a stone.'),
('animal|beast|camel|horse|sheep|ox|cattle|calf|hound|dog|hare|goat','at spring @ drink:pa.','The {} drank at the spring.'),
('gem|stone|crystal|jewel|metal|alloy|ore|mineral','in his/hand @ hold:pa he.','He held the {} in his hand.'),
('tree|fruit|vegetable|shrub|herb|flower|fungus|plant|grain|root','in garden @ grow:pa.','The {} grew in the garden.'),
('vessel|ship|boat|canoe','in harbour @ lie:pa.','The {} lay in the harbour.'),
('cloth|fabric|thread|garment|sleeve|coat|wool|silk','by light @ examine:pa she.','She examined the {} by the light.'),
('book|poem|letter|treatise|verse|prayer|account|song|ballad','before feast @ read:pa he.','He read the {} before the feast.'),
('feast|meal|food|bread|flesh of|meat|wine|spice','on table @ set:pa they.','They set the {} on the table.'),
('person|man who|woman who|servant|official|officer|sailor|priest|spectator|minister|kinsman|artisan|ruler|governor|messenger|soldier','at gate @ wait:pa.','The {} waited at the gate.'),
('tool|instrument|implement|utensil|spoon|cup|knife|blade','on table @ lay:pa she.','She laid the {} on the table.'),
('storm|wind|weather|rain|fire|smoke|cloud','from hill @ see:pa they.','They saw the {} from the hill.'),
('sound|voice|confusion|noise|music|cry','from street @ hear:pa he.','He heard the {} from the street.'),
('shipwreck|fall|exile|expulsion|journey|departure|battle|loss|death','after @ home return:pa they.','They returned home after the {}.'),
('feeling|shame|wonder|awe|fear|anger|grief|sorrow|love|joy','her/voice:n @ reveal:pa.','Her voice revealed her {}.'),
('authority|office|charge of|duty|privilege|right to','who @ hold:pr?','Who holds the {}?'),
('place|building|tower|hill|wall|gate|passage|rock|bridge|island|village|town|harbour','near @ they rest:pa.','They rested near the {}.'),
]
SCENES=[(re.compile(r'\b(?:'+pattern+r')\b',re.I),a,e) for pattern,a,e in SCENES]


class Articles:
    def __init__(self,c,d):
        self.c,self.d=c,d
        self.lang=copy(d.lang)
        self.lang.lexicon=dict(d.lang.lexicon)
        self.lang.glosses=dict(d.lang.glosses)
        self.witness=load_gzip(CACHE)
        self.facts=load_gzip(CACHE.with_name('dictionary-relations.json.gz'))
        self.approved={}
        sample=WORK/'opening-illustrations.json'
        for item in read(sample):
            for i in item['readings']:
                s=c['senses'][i]
                self.lang.lexicon[s['key']]=dict(self.lang.lexicon[s['key']],form=s['form'])
                self.approved[i]=item
        self.auth=keyed(WORK/'lexical-examples.txt')
        self.ms=keyed(WORK/'manuscript-examples.txt')
        self.sub={(r[0],r[3]):a for r,a in zip(lines(WORK/'sense-divisions.txt'),lines(WORK/'sense-examples.txt'),strict=True)}
        self.stats=Counter()

    def compile(self,a,e,method='composed',ref=''):
        p=self.lang.compile(a.replace('@','exampletarget'))
        return dict(native=p['text'],gloss=p['gloss'],english=e,method=method,ref=ref)

    def subject(self,s):
        self.lang.lexicon['exampletarget']=dict(form=s['form'],pos=s['pos'])
        self.lang.glosses['exampletarget']=label(s)

    def definition(self,s,ctx,n,g,method):
        if method=='identified by source':
            title,eng=self.d.source_title(ctx)
            if title:
                marker=' '+self.d.phrase('in')[0]+' '+title
                if marker in n:
                    n=n.split(marker)[0];g=g.split(' · in · '+eng)[0]
                    if n==self.d.phrase('name')[0]:
                        # The headword is a named referent. Preserve local identifying
                        # information when a roster or list is all the witness supplies.
                        nearby=self.neighbour(s,ctx)
                        if nearby:
                            tail=self.d.phrase('name which with')
                            final=self.d.phrase('write:psv:perf')
                            n=tail[0]+' '+self.lang.maxima(nearby['form'])+' '+final[0]
                            g=tail[1]+' · '+label(nearby)+' · '+final[1]
            return n,g
        if method=='cited terminology':
            title,eng=self.d.source_title(ctx)
            if title and ' '+title+' ' in n:
                return n.split(' '+self.d.phrase('which in')[0]+' ')[0],g.split(' · which · in · ')[0]
        return n,g

    def neighbour(self,s,ctx):
        words=re.findall(r'[a-zA-Z][a-zA-Z_0-9]*',ctx['analysis'])
        if s['key'] not in words:return None
        p=words.index(s['key'])
        for i in sorted(range(len(words)),key=lambda x:abs(x-p)):
            other=self.d.keyrefs.get(words[i])
            if other and other[0]['pos']=='proper' and normalize(other[0]['form'])!=normalize(s['form']) and label(other[0]).casefold() in ctx['source'].casefold():
                return other[0]

    def example(self,ident,s,ctx,place=None):
        self.subject(s)
        k=s.get('key','')
        text=label(s)
        if place:
            return self.compile('in kjv_basket @ stone'+('' if place.value==1 else ':pl')+' be:pa.',
                f'There {"was one stone" if place.value==1 else f"were {place.value:,} stones"} in the basket.')
        if k in self.auth:return self.compile(*self.auth[k])
        if ident in self.witness:
            item=dict(self.witness[ident])
            name=re.match(r"^([A-Z][A-Z ’',-]+?)(?:,? +)(?=[A-Z][a-z]|I\b)",item['english'])
            if not name:return item
            if ': ' in item['native'] and ': · ' in item['gloss']:
                body=item['native'].split(': ',1)[1]
                gloss=item['gloss'].split(': · ',1)[1]
                if head_present(body,s['form']):
                    item.update(native=self.lang.maxima(body),gloss=gloss,english=item['english'][name.end():])
                    return item
                if s['pos']=='proper' and head_present(item['native'].split(': ',1)[0],s['form']):
                    from tools.dictionary_source_examples import said
                    item.update(said(self,s,name[1].strip(' ,').title(),body,gloss,item['english'][name.end():]))
                    return item
            elif head_present(item['native'],s['form']) and not re.match(r'^\S+[:,] ',item['native']):
                item['english']=item['english'][name.end():]
                return item
        from tools.dictionary_source_examples import local_example,witness_name
        if item:=local_example(self,s,ctx):return item
        if s['pos']=='proper':text=witness_name(s,ctx['source'])
        fact=self.facts.get(k)
        if fact:
            for a,rel,b,book,ref in fact:
                other=b if k==a else a
                if other not in self.lang.lexicon or other not in self.d.keyrefs:continue
                original=self.d.keyrefs[other][0]
                othername=witness_name(original,self.c['contexts'][original['citations'][0]]['source'])
                an,en=('@',text) if a==k else (a,othername)
                bn,ben=('@',text) if b==k else (b,othername)
                return self.compile(f'{an} {rel} of {bn} be:pa.',f'{en} was the {rel} of {ben}.','source relationship',book+', '+ref)
        # If an economical paragraph is itself a complete sentence it can
        # still serve where the short-witness selector rejected a long clause.
        native=ctx['text'].strip();en=' '.join(ctx['source'].split())
        if (head_present(native,s['form']) and 2<=len(native.split())<=45 and len(en.split())<=66
            and len(en.split())>=3 and FINITE.search(ctx['analysis']) and not re.search(r':|\[|\]|^\s*(And (?:the )?sons of|Which|Whose|Because)\b',en)
            and not BAD.search(native+' '+en) and not REMOTE.search(en) and native[-1:] in '.?!' and en[-1:] in '.?!'
            and ':' not in native and not re.search(r'^[A-Z ]{3,}\s',en)):
            return dict(native=native,english=en,gloss=ctx['gloss'],book=ctx['book'],ref=ctx['reference'],method='attested unit')
        pos=part_of_speech(s['pos'])
        if pos=='proper':
            from tools.dictionary_source_examples import named_context
            if item:=named_context(self,s,ctx,text,self.d.role(usage_note(s))):return item
            other=self.neighbour(s,ctx)
            if other:
                self.lang.lexicon['exampleneighbour']=dict(form=other['form'],pos='proper')
                self.lang.glosses['exampleneighbour']=label(other)
                return self.compile('writer:n @ and exampleneighbour:a name:pr.',
                              f'The writer names {text} and {witness_name(other,ctx["source"])}.','contextual pairing')
            role=self.d.role(usage_note(s)) or ''
            if role in ('city','town','village','island','river','valley','country','region','harbour','bay','hill','sea','mountain','place','forest'):
                return self.compile('from here to @ how far be:pr?',f'How far is it from here to {text}?')
            if role in ('book','ship'):
                return self.compile('who @:a name:pa?',f'Who gave {text} its name?')
            return self.compile('in whose account @:a wepl find:pr?',f'In whose account do we find {text}?')
        if pos in ('adjective','modifier'):
            # Seek the actual modified noun in the keyed construction.
            found=re.findall(r'(?<!\w)'+re.escape(k)+r':m\s+([a-zA-Z_][a-zA-Z_0-9]*)',ctx['analysis'])
            noun=next((t for t in found if t in self.lang.lexicon and t in self.d.keyrefs and part_of_speech(self.d.keyrefs[t][0]['pos']) in ('noun','proper','root')),'thing')
            name=label(self.d.keyrefs[noun][0]) if noun!='thing' else 'thing'
            return self.compile(f'this {noun} @:m be:pa.',f'This {name} was {text}.')
        if pos=='verb':
            return self.compile('when they @:pa?',f'When did they {text}?')
        if pos=='adverb':
            return self.compile('he @ speak:pa.',f'He spoke {text}.')
        desc=usage_note(s).split(';')[0]
        for pattern,a,e in SCENES:
            if pattern.search(text) or pattern.search(desc[:110]):
                return self.compile(a,e.format(text))
        return self.compile('of @ on that day they speak:pa.',f'That day they spoke about {text}.')

    def approved_item(self,item):
        if 'definitionNative' in item:
            return (item['definitionNative'],item['definitionGloss'],item['english'],
                    dict(native=item['exampleNative'],gloss=item['exampleGloss'],english=item['translation'],method=item['method']))
        d=self.lang.compile(item['definition'],initial=False)
        if 'sentence' in item: ex=self.compile(item['sentence'],item['translation'])
        else:
            ctx=self.c['contexts'][item['witness']]
            g=' · '.join(ctx['gloss'].split(' · ')[-6:])
            # The quotation stops at Rugby, regardless of subsequent dialogue.
            tokens=ctx['gloss'].split(' · ')
            ix=next(i for i,t in enumerate(tokens) if t.lower().startswith('behind'))
            g=' · '.join(tokens[ix:ix+len(item['example'].split())])
            ex=dict(native=item['example'],gloss=g,english=item['translation'],book=ctx['book'],ref=ctx['reference'],method='attested')
        return d['text'],d['gloss'],item['english'],ex

    def manuscript(self,f,lab):
        self.subject(dict(form=f,label=lab,pos='noun'))
        a,e=self.ms[f]
        name={'Åmos':'Amos','habakçk':'Habakkuk','hÅgay':'Haggai','nahçm':'Nahum'}.get(f,lab)
        return self.compile(a,e.replace('{name}',name))

    def add(self,row,n,g,meaning,example,refs,readings=()):
        from tools.dictionary_rows import citation
        n=end(n);g=end(g)
        if example.get('book'):
            exref=citation({},dict(book=example['book'],reference=example['ref']))
        else:exref=example.get('ref','')
        refs=list(dict.fromkeys(x.strip(' .') for x in [*refs,exref] if x))
        head=row['text'].partition('. ')[0]
        revision=self.revision
        n=revision.case(n,g,False)
        example=dict(example,native=revision.case(example['native'],example['gloss'],True))
        from tools.dictionary_sense_revision import significant,skeleton
        revision.seen[normalize(head)].append((skeleton(example['english']),significant(example['english'])))
        if not head_present(example['native'],head):
            raise ValueError((row['id'],head,example))
        if any(q in n+example['native'] for q in '[]'):raise ValueError(('brackets',row['id'],n,example))
        row['article']=dict(definition=n,example=example['native'],exampleMethod=example['method'],exampleEnglish=example['english'],readingIds=list(readings),references=refs)
        initial=row['gloss'].partition('. ')[0]
        row.update(text=head+'. '+n+' '+example['native'],gloss=initial+'. '+g+' '+example['gloss'],
                   source=end(meaning)+' Example: '+end(example['english'])+' '+'. '.join(refs)+('.' if refs else ''))
        self.stats[example['method']]+=1
