"""Compose dictionary readings from attested identities and editable native paraphrases."""
from collections import Counter, defaultdict
from functools import lru_cache
import re

from tools.dictionary_corpus import ROOT, WORK, normalize, read
from tools.dictionary_lexicon import language_set, load_gzip


ROLE = [
 ('city','city|capital'),('town','town|burg'),('village','village|hamlet'),
 ('island','island|isle'),('river','river|brook|stream'),('sea','sea|ocean'),
 ('mountain','mountain|mount'),('hill','hill'),('harbour','harbour|harbor|port'),
 ('bay','bay|gulf'),('valley','valley|vale'),('country','country|province|territory'),
 ('region','district|region|coast'),('ship','ship|vessel'),('book','book|treatise'),
 ('kjv_tribe','tribe'),('people:pl','people|nation'),('house','household|house'),
 ('king','king|monarch'),('queen','queen'),('prince','prince'),('duke','duke'),
 ('priest','priest'),('prophet','prophet'),('judge','judge'),('captain','captain|commander'),
 ('soldier','soldier'),('servant','servant|attendant'),('messenger','messenger'),
 ('writer','writer|author'),('poet','poet'),('merchant','merchant|bookseller'),
 ('father','father'),('mother','mother'),('daughter','daughter'),('son','son'),
 ('brother','brother'),('sister','sister'),('wife','wife'),('husband','husband'),
 ('companion','companion'),('friend','friend'),('child','child'),('spirit','spirit'),
 ('god','god'),('goddess','goddess'),('angel','angel'),('senator_member','senator'),
 ('gentleman','gentleman'),('gentlewoman','gentlewoman'),('courtier','courtier'),
 ('lord','lord|signior'),('princess','princess'),('general_commander','general'),
 ('officer','officer'),('kjv_elder','elder'),('kjv_governor','governor'),
 ('kjv_sailor','sailor|seaman'),('musician_person','musician'),('player','player|actor'),
 ('doctor','doctor|physician'),('bishop_english','bishop'),('knight','knight'),
 ('constable','constable'),('clown','clown|jester'),('counsellor','counsellor|counselor'),
 ('steward','steward'),('scholar','scholar'),('monk_cloister','monk'),
 ('nun','nun'),('friar','friar'),('heir','heir'),('widow','widow'),
 ('kinsman','kinsman'),('lover','lover'),('kjv_ambassador','ambassador|envoy'),
 ('disciple','disciple'),('kjv_apostle','apostle'),('ancestor','ancestor'),
 ('descendant','descendant'),('kjv_family','family|dynasty|clan'),('place','locality|place'),
 ('rock','rock'),('spring','spring'),('forest','forest'),('star','star'),('temple','temple'),
 ('person','person|man|woman|character')
]
KIN = 'father mother son daughter brother sister wife husband widow servant king queen prince duke companion friend captain ruler'.split()
FORMS = dict(noun='thing',verb='action',adjective='quality',modifier='quality',
             adverb='manner',adposition='relation',conjunction='word',pronoun='word',
             interjection='word',quantifier='measure',modal='word')
WORD = re.compile(r"[A-Za-z]+(?:[-’'][A-Za-z]+)*")
META = re.compile(r'(?i)\b(?:No (?:added|invented|modern|automatic)|Supplied local|Preserve(?:s)? (?:the |this )?(?:spelling|source|separate|distinction|local)|Local (?:kinship|relationship|relation)|Native (?:roots?|compound|formation|word)|Author-permitted|Reviewed (?:contextual|native|promotion)|Not automatically|Without invented|No identification|Do not |No external|no claim that)')


def usage_note(s):
    meaning=s['meaning'].strip()
    meaning=re.sub(r'(?<=[A-Za-z])(?=\d+[:–])',' ',meaning)
    meaning=re.sub(r'(?<=\d)(?=(?:John|Peter|Kings|Chronicles|Timothy|Corinthians|Samuel|Thessalonians)\b)',' ',meaning)
    meaning=re.sub(r'\b(in|beside|of|from|to)(?=[A-Z][a-z])',r'\1 ',meaning)
    meaning=re.sub(r'(?<=[,;])(?=[A-Za-z])',' ',meaning)
    meaning=re.sub(r'^[Ss]ource (?:proper (?:name|form)|personal name|name|geographical name)\s*','',meaning)
    meaning=re.sub(r'(?i)\s*;?\s*declared derivation from .*$','',meaning)
    meaning=re.sub(r'\s*<[^>]*>','',meaning)
    meaning=META.split(meaning,1)[0].strip(' .;,')
    meaning=re.split(r'(?i)(?:[.;]\s*|,\s*)(?=authored (?:formation|borrowing|compound|adaptation)|the distinction is retained|without (?:an? )?(?:invented|unprinted)|an? (?:explicit |historical )?source-label)',meaning,1)[0]
    meaning=re.sub(r'\s*\((?:v\*?|adj|n(?:, ?(?:m|cnt|cl))?)\)$','',meaning,flags=re.I)
    return meaning or s['label']


def part_of_speech(pos):
    p=pos.strip().lower()
    if p in {'v','v*'}:return 'verb'
    if p.startswith('n,'):return 'noun'
    if p=='adj':return 'adjective'
    return p


class Definer:
    def __init__(self,corpus):
        self.corpus=corpus
        self.lang,historical=language_set()
        self.lang.lexicon={**historical.lexicon,**self.lang.lexicon}
        self.defs={}
        for line in (WORK/'authored-definitions.txt').read_text(encoding='utf8').splitlines():
            if not line or line.startswith('#'):continue
            key,analysis,english=line.split(' | ')
            if key in self.defs:raise ValueError(key)
            self.defs[key]=analysis,english
        for line in (WORK/'native-readings.txt').read_text(encoding='utf8').splitlines():
            if not line or line.startswith('#'):continue
            keys,analysis=line.split(' | ')
            for key in keys.split('/'):
                if key in self.defs:raise ValueError(key)
                self.defs[key]=analysis,None
        self.by_name=defaultdict(set)
        self.by_label=defaultdict(list)
        self.keyrefs=defaultdict(list)
        for s in corpus['senses'].values():
            self.keyrefs[s['key']].append(s)
            label=s['label'].split('{')[0].strip().casefold()
            if s['pos']=='proper':
                if re.fullmatch(r"[a-z][a-z'-]{2,}",label):
                    self.by_name[label].add(s['form'])
            else:
                for word in {label,s['key'].removeprefix('drama_native_').removeprefix('kjv_').replace('_',' ')}:
                    self.by_label[word].append(s)
        self.bible_titles={}
        for p in read(ROOT/'Saves/KJV Bible v0.10-kjv.285/section-index.json'):
            self.bible_titles[p['section']]=p['titleSlots']
        self.title_texts={'A New Voyage Round the World': 'drama_native_new:m drama_native_voyage world around',
            'The Sceptical Chymist': 'boyle_sceptical:m boyle_chymist', 'Leviathan':'leviathan',
            'Paradise Lost':'paradise lose:psv:perf','The Prince':'prince'}

    @lru_cache(maxsize=50000)
    def phrase(self,analysis):
        if any(ord(c)>127 for c in analysis) and all(w.split(':')[0] in self.lang.lexicon for w in analysis.split()):
            parts=[self.lang.word(w) for w in analysis.split()]
            return ' '.join(p[0] for p in parts),' · '.join(p[1] for p in parts)
        result=self.lang.compile(analysis,initial=False)
        return result['text'],result['gloss']

    def name(self,english,context):
        key=english.casefold().strip(',')
        options=self.by_name.get(key,set())
        if len(options)==1:return self.lang.maxima(next(iter(options)))
        present=[v for v in options if normalize(v) in {normalize(w.strip('.,:;?!')) for w in context['text'].split()}]
        return self.lang.maxima(present[0]) if len(present)==1 else None

    def role(self,meaning):
        # Only the beginning identifies the referent. Later names and comparisons
        # frequently describe a relative, a speaker or a different location.
        lead=re.split(r'[.;]|,\s*(?:not|without)|\b(?:who|whose|whom|where|given by|named by|mentioned by|identified through|identified by|addressed by|not|distinct from|rather than|instead of|beside|alongside)\b',meaning,1,flags=re.I)[0][:135]
        matches=[]
        for key,terms in ROLE:
            for m in re.finditer(rf'\b(?:{terms})\b',lead,re.I):
                if re.search(r"(?i)\b(?:(?:of|to|from|by|beside|with|against)\s+(?:the |his |her |a |an )?|(?:his|her|their)\s+)$",lead[:m.start()]):
                    continue
                if re.match(r"['’]s\b",lead[m.end():]):
                    continue
                matches.append((m.start(),key))
        return min(matches)[1] if matches else None

    def source_title(self,context):
        book=context['book']
        if book=='King James Bible' or re.search(r'\d+:\d+',str(context['reference'])):
            ref=re.match(r'(.+?)\s+(\d+):(\d+)',context['reference'])
            if ref and ref[1] in self.bible_titles:
                from tools.unta_language import quantity
                num=lambda a:quantity(int(a),notation='digits')['form']
                return self.bible_titles[ref[1]]+' '+num(ref[2])+', '+num(ref[3]),ref[0]
        # In the plays, the title often is the principal character's name.
        title=re.sub(r'^(The |King |Prince )','',book)
        form=self.name(title,context)
        if form:return form,book
        if book in self.title_texts:
            try:return self.phrase(self.title_texts[book])[0],book
            except ValueError:pass
        return None,book

    def proper(self,s,context):
        meaning=usage_note(s)
        lead=re.split(r'[.;]|,\s*(?:not|without)|\b(?:distinct from|rather than|instead of|beside|alongside)\b',meaning,1,flags=re.I)[0]
        for role in KIN:
            # Name + kinship + of + related name, or the possessive order.
            patterns=(rf"\b{role} of (?:the )?([A-Z][a-zA-Z'-]+)",rf"\b([A-Z][a-zA-Z'-]+)[’']s {role}\b")
            for pat in patterns:
                m=re.search(pat,lead)
                if m and not re.search(r'\b(?:son|daughter|wife|husband|mother|father|brother|sister) of\b',lead[:m.start()],re.I) and (related:=self.name(m[1],context)) and normalize(related)!=normalize(s['form']):
                    a,g=self.phrase(role+' of')
                    return a+' '+related,g+' · '+m[1],meaning,'kinship or office'
        descriptor=meaning.lower()
        patterns=[
            (r'itinerary|encampment|journey station','place where people on journey rest:perf'),
            (r'genealogy|genealogical|migration list|in .{0,28}family line','person whose name in account of kin write:psv:perf'),
            (r'latin (?:or greek )?(?:expression|word|phrase|quotation)|greek (?:or latin )?(?:word|phrase|expression)','word of other tongue which writer repeat:pr'),
            (r'alias|assumed name|assumed by|disguise|disguised as','name which person in other acting_role bear:pr'),
            (r'mispronounc|mishear|mangled name','name whose sound in speech change:psv:perf'),
            (r'angel sent to counsel','messenger of god who counsel give:pr'),
        ]
        role=next((k for pat,k in patterns if re.search(pat,descriptor)),None) or self.role(meaning)
        if not role:
            role='place' if 'geographic' in s['origin'].lower() else 'name'
        a,g=self.phrase(role)
        native_book,eng_book=self.source_title(context)
        if native_book:
            v,vg=self.phrase('in')
            p,pg=self.phrase('name:psv:perf')
            out=a+' '+v+' '+native_book+' '+p if role!='name' else a+' '+v+' '+native_book
            gloss=g+' · '+vg+' · '+eng_book+(' · '+pg if role!='name' else '')
            return out,gloss,meaning,'identified by source'
        # The cited wording after the colon is a genuine identifying description
        # even where an early text supplies no recoverable biography.
        phrase='name which in this passage write:psv:perf' if role=='name' else role+' which in this passage name:psv:perf'
        a,g=self.phrase(phrase)
        return a,g,meaning,'identified by citation'

    def concept(self,word,s):
        low=word.lower()
        aliases={'human':'person','human being':'person','human beings':'people:pl','mankind':'people:pl',
            'male':'kjv_male','toward':'towards','body of water':'water','territory':'region',
            'geographical region':'region','quantity':'measure','household':'kjv_family',
            'family':'kjv_family','appointed ruler':'ruler','absolute authority':'great:m authority',
            'worshipper':'worship:ag','occupation':'work','beginning':'beginning','leader':'ruler',
            'instrument':'instrument','tool':'instrument','implement':'instrument','garment':'garment',
            'speech act':'speech','dwelling place':'dwelling','vessel':'vessel','ownership':'possession',
            'magnitude':'measure','intellect':'mind','adult':'adult_maturity','offspring':'child',
            'plant':'drama_native_plant','fish':'fish','bird':'bird','house':'house','action':'action'}
        if low in aliases:
            k=aliases[low]
            if all(w.split(':')[0] in self.lang.lexicon for w in k.split()):return k
        candidates=self.by_label.get(low,[])
        for x in sorted(candidates,key=lambda x:(x['key']!=low,not x['contemporary'],-x['contemporary'])):
            if x['key']!=s['key'] and normalize(x['form'])!=normalize(s['form']) and x['key'] in self.lang.lexicon:
                return x['key']
        return None

    def semantic_phrase(self,s):
        meaning=usage_note(s)
        # Require a whole licensed nominal construction for this definition.
        for phrase in re.split(r';|, |\. | or ',meaning)[:4]:
            phrase=re.sub(r'^(?:to |the |a |an )','',phrase.strip(),flags=re.I)
            phrase=re.sub(r'\s*\([^()]*\)\s*$','',phrase).strip(' .')
            if not phrase or len(phrase)>65:continue
            for separator,rel in [(' of ','of'),(' for ','for'),(' with ','with'),(' without ','without'),(' between ','between')]:
                if separator in phrase.lower():
                    a,b=re.split(re.escape(separator),phrase,maxsplit=1,flags=re.I)
                    x=self.concept(a,s);y=self.concept(re.sub(r'^(?:a |the |an )','',b),s)
                    if x and y:return x+' '+rel+' '+y
            ws=phrase.split()
            if len(ws)==2:
                x=self.concept(ws[0],s); y=self.concept(ws[1],s)
                if x and y and ' ' not in x and ':' not in x and part_of_speech(self.lang.lexicon[x].get('pos','')) in ('modifier','adjective'):
                    return x+':m '+y
            if re.fullmatch('[a-z]+',phrase.lower()) and (x:=self.concept(phrase,s)):
                if x.split(':')[0]!=s['key'] and normalize(self.phrase(x)[0])!=normalize(s['form']):return x
        return None

    def cited_term(self,s,context):
        from tools.unta_language import quantity
        key,meaning=s['key'],s['meaning']
        # Earlier packages encoded these as words before the numerical compiler
        # assigned a separate keyed entry for each value and notation.
        old_numbers=dict(two=2,three=3,kjv_three=3,four=4,five=5,six=6,seven=7,
                         eight=8,nine=9,ten=10,eleven=11,twelve=12,twenty_four=24,
                         hundred=100,thousand=1000,million=1000000,kjv_second=2)
        if key in old_numbers:
            kind='ordinal' if key=='kjv_second' else 'cardinal'
            value=old_numbers[key]
            n,g=self.phrase('place in order' if kind=='ordinal' else 'count')
            return quantity(value,kind,notation='digits')['form']+' '+n,str(value)+' · '+g
        month=next((i for i,name in enumerate('January February March April May June July August September October November December'.split(),1)
                    if re.match(name+r'\b',meaning,re.I) and 'month' in meaning.lower()),None)
        if month:
            form=quantity(month,'ordinal')['form']
            a,g=self.phrase('month of year')
            return form+' '+a,str(month)+'(ord.) · '+g
        if key.startswith('school_source_letter_'):
            sign=key.rsplit('_',1)[1].upper()
            a,g=self.phrase('name of written:m sign in lesson')
            return a+' '+sign,g+' · '+sign
        if 'solmization' in key or key.startswith('lear_sung_'):
            return self.phrase('voice:g sign by which song:g sound distinguish:psv:pr')
        if key.startswith('song_vocable_') or 'nonlexical' in meaning.lower():
            return self.phrase('sound which in song repeat:psv:pr')
        if 'intended native expression is ' in meaning:
            roman=meaning.split('intended native expression is ')[1].strip().rstrip('.')
            words=[v for v in self.lang.lexicon.values() if self.lang.reading(v['form']).casefold()==roman.casefold()]
            if words:
                a,g=self.phrase('wrong:m sound of word')
                return a+' '+words[0]['form'],g+' · '+roman
        if key.startswith('kjv_') and re.search(r'(?i)dietary list|source (?:tree|stone|gem|bird) (?:name|label)|tree called|grain called|historical (?:grain|gem|stone|tree) (?:label|name)|source plant whose|exact modern species',meaning):
            groups={'tree':'tree','stone':'stone','gem':'jewel','bird':'bird','grain':'corn','plant':'kjv_plant_growth'}
            typ=next((k for w,k in groups.items() if re.search(r'\b'+w+r'\b',meaning,re.I)),'animal')
            cited,ref=self.source_title(context)
            if cited:
                n,g=self.phrase(typ+' which in')
                a,b=self.phrase('name:psv:perf')
                return n+' '+cited+' '+a,g+' · '+ref+' · '+b
        return None

    def define(self,s,context):
        key=s['key']
        if key in self.defs:
            a,meaning=self.defs[key]
            return *self.phrase(a),meaning or usage_note(s),'authored paraphrase'
        if s.get('number'):
            q=s['number']
            from fractions import Fraction
            z=Fraction(q['value'])
            from tools.unta_language import quantity
            number=quantity(z.numerator,'fraction' if z.denominator!=1 else 'cardinal',z.denominator,notation='digits')
            ending={'cardinal':'count','ordinal':'place in order','fraction':'part of whole','times':'time:pl','fold':'measure'}[q['kind']]
            f,g=self.phrase(ending)
            form=q.get('spokenForm',q['form']) if q.get('notation')=='digits' else number['form']
            return form+' '+f,q['value']+' · '+g,usage_note(s),'number'
        if s['pos']=='proper':
            return self.proper(s,context)
        cited=self.cited_term(s,context)
        if cited:
            return *cited,usage_note(s),'cited terminology'
        phrase=self.semantic_phrase(s)
        needs_roots=[k for k in s['roots'] if k in self.lang.lexicon]
        if phrase:
            f,g=self.phrase(phrase)
            if normalize(f)!=normalize(s['form']):
                return f,g,usage_note(s),'semantic paraphrase'
        if needs_roots:
            if len(needs_roots)==1 and needs_roots[0] in self.defs:
                a,_=self.defs[needs_roots[0]]
                f,g=self.phrase(a)
                return f,g,usage_note(s),'defined root'
            roots=' '.join(needs_roots)
            if len(needs_roots)==1:
                p=part_of_speech(s['pos'])
                if p=='noun':roots='thing of '+roots
                elif p=='verb':roots=roots+':inf'
                elif p in ('modifier','adjective'):roots='like '+roots
            f,g=self.phrase(roots)
            return f,g,usage_note(s),'analytic reading'
        return '', '',usage_note(s),'requires paraphrase'
