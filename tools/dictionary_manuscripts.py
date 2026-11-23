"""Recover independent readings for words known only from the printed columns."""
import re
from collections import defaultdict

from tools.dictionary_corpus import WORK, normalize

def manuscript_notes():
    out={}
    for line in (WORK/'manuscript-notes.txt').read_text(encoding='utf8').splitlines():
        if not line or line.startswith('#'):continue
        forms,label,analysis=line.split(' | ')
        for form in forms.split('/'):
            form=normalize(form)
            if form in out:raise ValueError(f'Duplicate manuscript note for {form}')
            out[form]=(label,analysis)
    return out


def lemma(label):
    return re.sub(r'\([^)]*\)|\{[^}]*\}|:pl\b', '', label).strip(' .,:;?!').lower().replace('_','-')


class ManuscriptReadings:
    def __init__(self, corpus, definer):
        self.d=definer
        self.senses=corpus['senses']
        self.by_word=defaultdict(set)
        for identity,s in self.senses.items():
            for label in (s['label'].split('{')[0],s['key'],s['key'].removeprefix('kjv_')):
                self.by_word[lemma(label)].add(identity)
        # Attested construction glosses know nicknames and compound senses that
        # differ from the modern dictionary's citation spelling.
        for analyses in corpus['forms'].values():
            for gloss,ids,*_ in analyses:
                if len(ids)==1:self.by_word[lemma(gloss)].add(ids[0])
        self.notes=manuscript_notes()
        self.c=corpus

    def find(self,label,form):
        options=self.by_word.get(label,set())
        if not options:return None
        def rank(identity):
            s=self.senses[identity]
            v=normalize(s['form'])
            return (v in form,len(v) if v in form else 0,lemma(s['label'])==label,
                    s['key']==label,bool(s['contemporary']),s['contemporary']+s['historical'])
        best=max(sorted(options),key=rank)
        if len(options)>1 and not rank(best)[0]:
            # Distinct manuscript spellings can express exactly the same inherited
            # identity. Different identities with the same gloss need other evidence.
            if len({self.senses[x]['key'] for x in options})>1:
                exact=[x for x in options if self.senses[x]['key']==label.replace('-','_')]
                if len(exact)!=1:return None
                best=exact[0]
        return best

    def components(self,label,form):
        text=lemma(label)
        if ident:=self.find(text,form):return [ident]
        words=text.split('-')
        found=[]
        while words:
            for end in range(len(words),0,-1):
                if ident:=self.find('-'.join(words[:end]),form):
                    found.append(ident);del words[:end]
                    break
            else:
                return []
        return found

    def read(self, form, record):
        if form in self.notes:
            label,analysis=self.notes[form]
            n,g=self.d.phrase(analysis)
            return n,g,label
        if 'value' in record:
            from tools.unta_language import quantity
            q=quantity(record['value'])
            return q['form'],str(record['value']),f"Unta numeral for {record['value']:,}."
        label=record['gloss']
        if label=='feigned speech':
            n,g=self.d.phrase('sound which soldier:pl as other tongue in play speak:pr')
            return n,g,'Feigned speech in the capture of Parolles.'
        prefix,_,rest=label.partition('-')
        possessive=self.d.lang.possessors.get(prefix) if rest else None
        parts=self.components(rest if possessive else label,form)
        if not parts:return None
        if len(parts)==1:
            s=self.senses[parts[0]]
            n,g,e,_=self.d.define(s,self.c['contexts'][s['citations'][0]])
            e=label+'. '+e
        else:
            ss=[self.senses[i] for i in parts]
            n,g,e=' '.join(s['form'] for s in ss),' · '.join(s['label'].split('{')[0] for s in ss),label
        if possessive:
            who,wg=self.d.phrase(possessive)
            n=who+' '+n;g=wg+' · '+g
        return n,g,e
