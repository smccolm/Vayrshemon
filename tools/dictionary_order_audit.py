"""Read the printed native column and walk adjacent spellings in chart order."""
from itertools import zip_longest

from tools.compose_historical_book import texts


# Transcribed from the maxima and minima columns of Origins_2_Thimfora_2.jpg.
# Keep this reference independent of the sorter and its JSON inventory.
MINIMA='jÃkaÅÇÉhËrÍÏbcÑdgptÓÕvze'+'×flmnÙsÛxiÝoßáãåqwuçéëy'
MAXIMA='JÂKAÄÆÈHÊRÌÎBCÐDGPTÒÔVZE'+'ÖFLMNØSÚXIÜOÞàâäQWUæèêY'
CASE=dict(zip(MAXIMA,MINIMA,strict=True))
LITERAL={'ā':'Å','ē':'×','ī':'Ý','ō':'ß','ô':'á','ū':'ç','ü':'ë','č':'Ñ',
         'š':'Û','ŧ':'Õ','ñ':'n','í':'i','ï':'i','ó':'o'}
DIGITS='0123456789ÀÁ'
ALPHABET=' '+DIGITS+MINIMA


def reference_word(spelling):
    normalized=[]
    letters=[]
    for char in spelling:
        if char in CASE:
            char=CASE[char]
        elif char not in ALPHABET:
            char='’' if char=="'" else char.lower()
        normalized.append(char)
        if char in ('’','-',','):
            continue
        slot=LITERAL.get(char,char)
        if slot not in ALPHABET:
            raise ValueError(f'No Thimfora filing rule for {char!r} in {spelling!r}')
        letters.append(slot)
    return ''.join(letters),''.join(normalized)


def check_native_order(pages,index,by_id):
    sections=('directory','headwords','manuscript','forms')
    counts={s:dict(entries=0,distinctSpellings=0,adjacentDistinctPairs=0,
                   decidedAtSecondLetterOrLater=0,decidedAtThirdLetterOrLater=0,
                   shorterPrefixFirst=0,spellingTies=0,acrossSpreads=0) for s in sections}
    seen={s:set() for s in sections}
    previous={}
    for page,content in enumerate(pages,1):
        if page%2==0:
            continue
        ids=index[page//2]['ids']
        native=min(content['frames'],key=lambda frame:int(frame['x']))
        for uid,line in zip(ids,texts(native),strict=True):
            section,_,initial=by_id[uid]['section'].partition('-')
            if section=='opening':
                continue
            words=line.split(', ') if section=='forms' else [line.partition('. ')[0]]
            for spelling in words:
                letters,normalized=reference_word(spelling)
                if initial and initial!=letters[0]:
                    raise ValueError(f'{spelling!r} filed under {initial!r} on page {page}')
                record=counts[section]
                record['entries']+=1
                if section in previous:
                    old_letters,old_word,old_page=previous[section]
                    if old_word!=normalized:
                        record['adjacentDistinctPairs']+=1
                        if page!=old_page:
                            record['acrossSpreads']+=1
                        for pos,(a,b) in enumerate(zip_longest(old_letters,letters)):
                            if a==b:
                                continue
                            if b is None or (a is not None and ALPHABET.index(a)>ALPHABET.index(b)):
                                raise ValueError(f'{old_word!r} (p. {old_page}) before {spelling!r} '
                                                 f'(p. {page}), first difference at position {pos+1}')
                            if a is None:
                                record['shorterPrefixFirst']+=1
                            elif a!=' ' and b!=' ':
                                depth=sum(c in MINIMA for c in letters[:pos])
                                record['decidedAtSecondLetterOrLater']+=int(depth>=1)
                                record['decidedAtThirdLetterOrLater']+=int(depth>=2)
                            break
                        else:
                            record['spellingTies']+=1
                            if (old_word!=old_letters,old_word)>(normalized!=letters,normalized):
                                raise ValueError(f'Wrong spelling tie on page {page}: {old_word!r}, {spelling!r}')
                if normalized in seen[section]:
                    if section!='headwords' or previous[section][1]!=normalized:
                        raise ValueError(f'Repeated or separated entry {spelling!r} on page {page}')
                else:
                    seen[section].add(normalized)
                    record['distinctSpellings']+=1
                previous[section]=letters,normalized,page
    return counts
