"""The three Unta places admitted to the word dictionary, in native font slots."""
from collections import defaultdict
from dataclasses import dataclass

from tools.dictionary_corpus import normalize
from tools.unta_language import semantic_key


# Transcribed from the native glyph column of Inputs/Origins_3_Unta_2.jpg.
# Some translated books use different spellings for the same quantities.
UNITS = ('fßlem','neksus','ÕÅtus','venik','bÅrum','jensis','ßd×um','pÉrsus','krizum','deksin','eÛnÉ','yamen')
DOZENS = ('','Ém×nß','sid×um','salisiks','Çramen','riv×um','vÅkus','lanserß','Énimés','Õen×um','mesidÉl','onez')
NAMES = ('zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven')


def chart_reading(form, language):
    # Native slot 0233 is ūvēel. Transliteration 7 prints u with one dot
    # above. Use the same letter in Unicode search labels and cross-references.
    return ''.join('u\u0307' if char=='é' else language.reading(char) for char in form)


@dataclass(frozen=True)
class PlaceWord:
    form: str
    places: tuple
    label: str
    variants: tuple

    @property
    def value(self):
        coefficient, exponent = self.places[0]
        return coefficient * 12**exponent

    def definition(self, definer):
        coefficient, exponent = self.places[0]
        if not coefficient:
            return definer.phrase('nothing to reckon:inf')
        if exponent == 0:
            key = 'one_num' if coefficient == 1 else NAMES[coefficient]
            analysis, _ = definer.defs[key]
            return definer.phrase(analysis)
        groups = 'group' if coefficient == 1 else 'group:pl'
        tail = groups+' of twelve' if exponent == 1 else groups+' of twelve group:pl of twelve'
        native, gloss = definer.phrase(tail)
        return UNITS[coefficient]+' '+native, NAMES[coefficient]+' · '+gloss

    def description(self):
        coefficient, exponent = self.places[0]
        if not coefficient:
            return 'Zero units, zero dozen, or zero gross. Each has the same written name.'
        unit = ('unit' if coefficient == 1 else 'units', 'dozen', 'gross')[exponent]
        return f'{NAMES[coefficient].capitalize()} {unit} ({self.value:,} in decimal).'


def place_words(corpus, ordinary):
    """Merge a chart meaning with its existing lexical sense whenever possible."""
    positions = defaultdict(list)
    for exponent in range(3):
        for coefficient in range(12):
            value = coefficient * 12**exponent
            positions[value].append((coefficient, exponent))
    variants = defaultdict(set)
    for s in corpus['senses'].values():
        q = s.get('number', {})
        if q.get('kind') == 'cardinal' and q.get('notation') == 'words':
            variants[int(q['value'])].add(normalize(s['form']))
    result = {}
    for value, places in positions.items():
        coefficient, exponent = places[0]
        if exponent == 0:
            form = UNITS[coefficient]
        elif exponent == 1:
            form = DOZENS[coefficient]
        else:
            form = UNITS[coefficient]+' nßrum'
        identity = semantic_key(value)+'@'+form
        if value <= 12:
            key = ('zero','one_num',*NAMES[2:],'twelve')[value]
            if key+'@'+form in ordinary:
                identity = key+'@'+form
        label = NAMES[coefficient] if exponent == 0 else NAMES[coefficient]+' '+('dozen' if exponent == 1 else 'gross')
        result[identity] = PlaceWord(form,tuple(places),label,tuple(sorted(variants[value]-{form})))
    return result


def index_place_words(finder, places, language):
    indexed = {f:(gloss,label) for f,gloss,label in finder}
    for word in places.values():
        destination = chart_reading(word.form,language)+' — '+word.label
        for spelling in (word.form,*word.variants):
            gloss,label = indexed.get(spelling, ('',''))
            readings = gloss.split(' / ') if gloss else []
            if word.label not in readings:
                readings.append(word.label)
            if destination not in label.split(' / '):
                label = (label+' / ' if label else '')+destination
            indexed[spelling] = (' / '.join(readings),label)
    return [(form,*entry) for form,entry in indexed.items()]
