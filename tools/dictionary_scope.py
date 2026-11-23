"""Select word entries from the concordance, which also records numerical notation."""
import re

from tools.dictionary_lexicon import NUM
from tools.dictionary_corpus import WORK


NUMERAL_TOKEN = re.compile(r"[0-9ÀÁ]+(?::[0-9ÀÁ]+)*(?:[’']t)?")
QUOTATIONS={k for k in (WORK/'nonlexical-quotations.txt').read_text(encoding='utf8').splitlines()
            if k and not k.startswith('#')}

def nonword(sense):
    key = sense['key']
    return (key in QUOTATIONS or key in {'armado_interrupted_name','beat_interrupted_beatrice','dambk_sco','lulla','morr_dance_first_sound','is_dance_last_sound'}
            or key.startswith(('song_vocable_', 'windsor_school_')))

def citation_only(sense):
    """An attribution or a printer's siglum can identify a witness without naming a word."""
    if sense['key'] in {'signature_a_source', 'boyle_jer'}:
        return True
    return (sense['pos'] == 'proper'
            and re.fullmatch(r'[A-Za-z](?:[. ]+[A-Za-z]){0,3}[.]?', sense['form']) is not None
            and re.search(r'\binitials?\b', sense['meaning'], re.I) is not None)


def lexical_form_analysis(form, ids, corpus, senses):
    if not ids or ids[0] not in senses:
        return False
    # A full surname-bearing name is evidence for that person. Its printed
    # first initial alone does not acquire the meaning of the whole name.
    head = corpus['senses'][ids[0]]
    return not (len(form) == 1 and head['pos'] == 'proper'
                and re.match(re.escape(form) + r'\.\s+\S', head['label'], re.I))


def word_senses(corpus):
    # The compiler can give every value, notation and ordinal its own identity.
    # Ordinary vocabulary such as "pair" and the historical counting word
    # "score" has its own lexical evidence, independently of that compiler.
    return {identity: sense for identity, sense in corpus['senses'].items()
            if 'number' not in sense and not NUM.fullmatch(sense['key'])
            and not NUMERAL_TOKEN.fullmatch(sense['form']) and not citation_only(sense) and not nonword(sense)}


def citation_exclusions(corpus, manuscript, omitted):
    identities = {key for key,sense in corpus['senses'].items() if citation_only(sense)}
    forms = set()
    for form in omitted:
        if form in corpus['forms']:
            analyses = [row[1] for row in corpus['forms'][form]]
        else:
            analyses = manuscript.get(form, {}).get('analyses', [])
        if any(keys and (keys[0] in identities or
                         not lexical_form_analysis(form,keys,corpus,corpus['senses'])) for keys in analyses):
            forms.add(form)
    return identities, forms


def word_readings(form, corpus, manuscript, senses):
    """Return eligible ledger analyses and/or a manuscript spelling record."""
    if NUMERAL_TOKEN.fullmatch(form):
        return [], None
    if form in corpus['forms']:
        # The grammar records the head first. "Seven groups" can look up
        # "group", while the possessive in "their 1,000" is not its head.
        analyses = [row for row in corpus['forms'][form] if lexical_form_analysis(form,row[1],corpus,senses)]
        return analyses, None
    record = manuscript[form]
    if 'value' in record or record.get('gloss')=='feigned speech':
        return [], None
    if record.get('analyses'):
        choices = [keys for keys in record['analyses'] if lexical_form_analysis(form,keys,corpus,senses)]
        return [], dict(record, analyses=choices) if choices else None
    return [], record

def nonword_exclusions(corpus, manuscript, omitted):
    identities={i for i,s in corpus['senses'].items() if nonword(s)}
    forms=set()
    for form in omitted:
        m=manuscript.get(form,{})
        keys=[r[1] for r in corpus['forms'].get(form,[])] or m.get('analyses',[])
        if m.get('gloss')=='feigned speech' or any(x and x[0] in identities for x in keys):forms.add(form)
    return identities,forms
