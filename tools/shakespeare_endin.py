"""Correct the rejected last/final stem without flattening duration or relative time."""
import re

from tools.shakespeare_project import ROOT, SEALED_BIBLE, reviewed_bible_vocabulary


LAST_LEMMA = re.compile(r'(?<![A-Za-z_])(?:last|final)(?![A-Za-z_])')
FINITE_LAST = re.compile(r'(?<![A-Za-z_])(?:drama_native_)?last(?=(?::[a-z_]+)*?:(?:pr|pa|fu|perf|pp|fp|prog|pprog|gn|inf|cv|imp|opt|can|may)(?![A-Za-z_]))')

# The time is relative to the speaker's present point of reference.
PREVIOUS = {
    'antony-and-cleopatra': {'01016a'},
    'as-you-like-it': {'00532a'},
    'coriolanus': {'00946c','01113a','01215a'},
    'cymbeline': {'00123a','00328b','00489a','00697a'},
    'hamlet': {'00031a','00052a','00104a','01017a','01076a'},
    'henry-iv-part-1': {'00003d','00004a','00050a','00161a','00506b','00554a'},
    'henry-iv-part-2': {'00020a','00325a','00860a'},
    'henry-v': {'00006a','00638a'},
    'henry-vi-part-1': {'00027a'},
    'allswell': {'0617','1031','1061'},
}
PREVIOUS_OCCASION = {
    'antony-and-cleopatra': {'00431a'}, 'as-you-like-it': {'00715a'},
    'coriolanus': {'00844a'}, 'hamlet': {'00458a'}, 'henry-iv-part-1': {'00311a'},
    'allswell': {'1090'}, 'midsummer': {'0624'},
}
ENDURE = {
    'cymbeline': {'00658a'},'hamlet': {'00147a','00575a','00596b'},
    'henry-iv-part-2': {'00109b'},'venus-and-adonis': {'00081','00091'},
}

def install_endin_readings(language):
    w=SEALED_BIBLE
    entries=reviewed_bible_vocabulary(ROOT/w['package'],w['manifestSha256'],w['forgeHead'])
    changed={}
    for key in ('last','final','kjv_omega_letter_revelation'):
        old=language.lexicon[key]
        review,bible=entries[key]
        if old['semanticId']!=bible['semanticId'] or old['form'] not in (review['before'],review['after']):
            raise ValueError('Unexpected form or identity for '+key)
        changed[key]={k:bible[k] for k in ('form','roman','semanticId','pos')}
        old.update(changed[key])
    return changed

def correction(slug,row):
    uid=row['id']
    analysis=row['analysis']
    if uid in ENDURE.get(slug,()):
        if not FINITE_LAST.search(analysis):
            raise ValueError('Expected a duration verb at '+slug+' '+uid)
        return LAST_LEMMA.sub('endure',analysis),'duration'
    if uid in PREVIOUS_OCCASION.get(slug,()):
        return LAST_LEMMA.sub('preceding time',analysis),'preceding occasion'
    if uid in PREVIOUS.get(slug,()):
        return LAST_LEMMA.sub('former',analysis),'preceding time or most recent member of a sequence'
    if 'at last' in analysis:
        return re.sub(r'(?<![A-Za-z_])at last(?![A-Za-z_])','finally',analysis),'eventual outcome'
    if not LAST_LEMMA.search(analysis):
        raise ValueError('Rejected form has no reviewed semantic lemma at '+slug+' '+uid)
    return analysis,'terminal position or final item'

def check_clean(unit,language):
    keys = [key for key in unit['keys'] if language.lexicon[key]['pos']!='proper'
            and 'endin' in language.lexicon[key]['form'].casefold()]
    if keys or 'endin' in unit['text'].casefold():
        raise ValueError('Rejected endin stem in '+str(unit.get('id','passage'))+' '+','.join(keys))
    if FINITE_LAST.search(unit['analysis']):
        raise ValueError('Choose the native verb for enduring or continuing: '+str(unit.get('id','passage')))

def correct_forge_headwords(snapshot,forms):
    for entry in snapshot['language']['lexicon']:
        headword = entry.get('headword','').casefold()
        if headword not in ('endin','endin jelam'):
            continue
        form = forms['kjv_omega_letter_revelation' if ' ' in headword else 'last']
        entry.update(headword=form['form'], pronunciation=form['roman'])
