"""Exact Unta quantity readings for authored language, derived from chart 2.

Numbers are semantic quantities, not English-word replacements. In particular
score-as-twenty differs from score-as-tally, and third-order from one-third.
Published language packages are untouched; users of this helper pin its digest.
"""
from fractions import Fraction
import re

DIGITS=('fßlem','neksus','ÓÅtus','venik','bÅrum','jensis','ßd×um','pÉrsus','krizum','deksin','eÛnÉ','yamen')
DOZENS=('', 'Ém×nß','sid×um','salisiks','Çram×n','riv×um','vÅkus','lans×ro','Énimus','Óen×um','nesidÉl','onez')
POWERS=((12**4,'nekra'),(12**3,'Óerid'),(12**2,'nßrum'))
REVIEW_WORDS=re.compile(
    r"\b(?:\d+(?:st|nd|rd|th)?|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"(?:thir|four|fif|six|seven|eigh|nine)teen(?:th)?|"
    r"(?:twent|thirt|fort|fift|sixt|sevent|eight|ninet)(?:y|ieth)|"
    r"(?:hundred|thousand|million|billion)(?:s|th|ed)?|(?:[a-z]+)?scores?|"
    r"first|seconds?|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|"
    r"once|twice|thrice|doubl(?:e[sd]?|ing)|trebl(?:e[sd]?|ing)|tripl(?:e[sd]?|ing)|twain|dozens?|gross|half|halves|quarters?|demi(?=-[a-z])|"
    r"(?:\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"(?:thir|four|fif|six|seven|eigh|nine)teen|"
    r"(?:twent|thirt|fort|fift|sixt|sevent|eight|ninet)y|hundred|thousand|million|billion)fold)\b",re.I)

def digits(value):
    if not isinstance(value,int) or isinstance(value,bool) or value<0:raise ValueError('Nonnegative integer required')
    result=''
    while value:value,r=divmod(value,12);result='0123456789AB'[r]+result
    return result or '0'

def cardinal(value):
    if not isinstance(value,int) or isinstance(value,bool) or value<0:raise ValueError('Nonnegative integer required')
    # High chart entries have an unresolved last exponent. Stay within the
    # directly checked short scales; larger exact source values need review.
    if value>=12**8:raise ValueError('Quantity beyond verified spoken scale; author an exact reviewed product')
    if value<12:return DIGITS[value]
    words=[]
    for scale,name in POWERS:
        coefficient,value=divmod(value,scale)
        if coefficient:words.extend((cardinal(coefficient),name))
    coefficient,value=divmod(value,12)
    if coefficient:words.append(DOZENS[coefficient])
    if value:words.append(DIGITS[value])
    return ' '.join(words)

def spoken_quantity(value,kind='cardinal',denominator=1):
    number=Fraction(value,denominator)
    if number<0:raise ValueError('Negative quantity needs an authored signed construction')
    if kind in {'cardinal','ordinal','times','fold'}:
        if number.denominator!=1:raise ValueError('Integral construction needs an integer')
        n=number.numerator;form=cardinal(n)
        if kind=='ordinal':
            if n<1:raise ValueError('Ordinal must be positive')
            form+='’t'
        if kind=='times':form+=' venor'
        if kind=='fold':form+=' mem' # N measures: authored multiplicative construction
        return dict(value=str(n),kind=kind,base12=digits(n),form=form,
                    evidence='Chart-2 cardinal; productive ordinal/multiple morphology where marked')
    if kind!='fraction':raise ValueError('Unknown numerical construction')
    integer,remainder=divmod(number.numerator,number.denominator);den=number.denominator
    residual=den
    for factor in (2,3):
        while residual%factor==0:residual//=factor
    if residual==1:
        parts=[]
        while remainder:
            digit,remainder=divmod(remainder*12,den);parts.append(digit)
        form=cardinal(integer)+(('Ñã '+' '.join(DIGITS[d] for d in parts)) if parts else '')
        shown=digits(integer)+(('.'+''.join('0123456789AB'[d] for d in parts)) if parts else '')
        evidence='Chart-2 choi separator extended to exact terminating fractions; never rounded'
    else:
        # Explicit authored ratio convention: N parts out of D equal parts.
        # It is not claimed to be an attested chart reading or a finite radix.
        form=cardinal(number.numerator)+' threnin tha '+cardinal(number.denominator)+' ilmem threnin'
        shown=digits(number.numerator)+'/'+digits(number.denominator)
        evidence='Authored exact parts-out-of-equal-parts construction; nonterminating fraction, no approximation'
    return dict(value=str(number),kind=kind,base12=shown,form=form,evidence=evidence)


def quantity(value,kind='cardinal',denominator=1,*,notation='words'):
    """Match source notation; semantic value and grammatical kind stay exact.

    Unta glyph slots are 0..9, À (ten), Á (eleven). The chart's paired
    triangle radix separator is the font's colon, not its sentence period.
    The ordinary source word 'third' therefore remains venik’t; source '3rd'
    uses digit 3 with the same native ordinal ending.
    """
    if notation not in {'words','digits'}:raise ValueError('Choose source words or digits')
    q=spoken_quantity(value,kind,denominator)
    q.update(notation=notation,spokenForm=q['form'])
    if notation=='words':return q
    glyphs=lambda s:s.translate(str.maketrans({'A':'À','B':'Á','.':':'}))
    if kind=='fraction' and '/' in q['base12']:
        n,d=q['base12'].split('/')
        # Exact nonterminating fractions retain the native ratio construction;
        # both quantities are written as digits, never silently rounded.
        q['form']=glyphs(n)+' threnin tha '+glyphs(d)+' ilmem threnin'
    else:
        q['form']=glyphs(q['base12'])+{'ordinal':'’t','times':' venor','fold':' mem'}.get(kind,'')
    q['evidence']+='; source uses numerals: chart glyph slots and productive grammatical ending'
    return q

def candidates(source):
    return [dict(text=m.group(),start=m.start(),end=m.end()) for m in REVIEW_WORDS.finditer(source)]

def semantic_key(value,kind='cardinal',denominator=1,*,notation='words'):
    # Compiler keys contain letters only. Decimal values are machine metadata,
    # never an instruction to print English decimal spellings in the text.
    encode=lambda n:''.join('abcdefghij'[int(c)] for c in str(n))
    q=Fraction(value,denominator)
    if q<0:raise ValueError('Negative quantity requires review')
    if notation not in {'words','digits'}:raise ValueError('Choose source words or digits')
    return 'unta_'+kind+'_'+encode(q.numerator)+'_over_'+encode(q.denominator)+('_digits' if notation=='digits' else '')
