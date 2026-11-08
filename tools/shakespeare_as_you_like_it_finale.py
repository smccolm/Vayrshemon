"""Authored native senses for As You Like It's closing scenes; no translation automation."""
from tools.shakespeare_project import PROJECT, read, write, materialize

# Each item is an explicit semantic extension or a native derivation, not an
# English sound replacement. No historical edition or published pin is changed.
SENSES = {
    'salutation_formal': (['greet', 'speech'], 'salutation', 'noun', 'A formal spoken greeting, paired with ordinary greeting in Touchstone’s affected entrance.'),
    'ally_person': (['friend'], 'ally', 'noun', 'A person or relation allied through shared interests, including the marriage connections promised to Oliver; not a claim of an actual military treaty.'),
    'party_disputant': (['quarrel', 'person'], 'party', 'noun', 'A party to a quarrel in the etiquette anecdote, not a political faction or festive gathering.'),
    'heap_pile': (['heap_mound'], 'heap', 'verb', 'Gather into a heap, used figuratively of overflowing joy at the final dance.'),
    'supply_food': (['food', 'give'], 'victual', 'verb', 'Provision with food for a journey, Jaques’s metaphor for a short-lived marriage.'),
    'lie_challenge': (['false', 'accuse'], 'lie-charge', 'noun', 'Giving someone the lie: an accusation that they speak falsely. This is not a lie told by the accuser; qualified/direct are stages in Touchstone’s quarrel parody.'),
    'oyster_native': (['pearl', 'cover'], 'oyster', 'noun', 'A pearl-bearing bivalve, lexicalized native pearl-cover, in the fair-pearl/foul-oyster contrast. Not every protective shell or a claim that every oyster contains a pearl.'),
    'religious_turn': (['faith', 'turn'], 'convert', 'verb', 'Adopt a religious life and turn away from a former enterprise; Frederick’s reported conversion, without specifying an unprinted denomination.'),
    'bequeath_assign': (['leave'], 'bequeath', 'verb', 'Assign or leave a possession/status to someone, here a living duke renouncing power and Jaques assigning futures. Does not assert either speaker’s death.'),
    'hawk_throat': (['throat', 'cough'], 'hawk', 'verb', 'Clear the throat noisily before singing; not hunt with a falcon.'),
    'rye_grain': (['winter', 'corn'], 'rye', 'noun', 'Rye as the cereal in the lovers’ field. Authored winter-grain lexical category, not an assertion that all winter grain is rye.'),
    'acre_plot': (['field', 'part'], 'acre', 'noun', 'A field strip or cultivated plot in the song. No exact acreage is stated; not a forced modern area conversion.'),
    'romani_source_people': (['wander', 'people'], 'Romani-person', 'noun', 'The people called gypsies in the source comparison. Authored native ethnonym wander-people for this source-cultural referent, not a claim that all Romani travel or that every traveller is Romani. Source ethnonym and its outsider stereotype remain documented.'),
    'flood_ark_vessel': (['kjv_flood_ark'], 'ark', 'noun', 'The Noah flood vessel in Jaques’s mock paired-animals allusion; not the covenant chest.'),
    'reckon_as': (['reckon'], 'reckon', 'verb', 'Account or judge something to be so, including reckoning the song wasted time. Not a noble count.'),
    'favoured_features': (['face', 'shape'], 'features', 'noun', 'Facial appearance, source favor, by which Duke Senior recognizes his daughter; not kindness.'),
    'rudiments_learning': (['learn', 'origin'], 'rudiments', 'noun', 'First principles of a discipline, not an asserted Unta ordinal in the source.'),
    'purgation_defence': (['innocent', 'proof'], 'purgation', 'noun', 'A defence establishing innocence or truth of a claim, Touchstone’s demand to prove courtier status. Not a medical purge.'),
    'measure_dance': (['measure'], 'measure', 'noun', 'A measured court dance; explicit metrical/dance extension of native measure retains the later measures/measure echo.'),
    'sententious_speech': (['proverb', 'speech'], 'sententious', 'modifier', 'Full of pointed maxims or wise-seeming sayings; the Duke’s assessment of Touchstone.'),
    'fool_bolt': (['short', 'arrow'], 'bolt', 'noun', 'The blunt short arrow of the fool’s-bolt proverb, not a door fastener.'),
    'disease_ailment': (['illness'], 'disease', 'noun', 'An ailment in the source deliberately odd dulcet diseases phrase; do not silently emend to phrases.'),
    'retort_answer': (['back', 'answer'], 'retort', 'noun', 'An answering turn in the parody of quarrel etiquette.'),
    'quip_taunt': (['small', 'taunt'], 'quip', 'noun', 'A pointed mocking reply in Touchstone’s named ladder of quarrels.'),
    'reproof_rebuke': (['blame', 'speech'], 'reproof', 'noun', 'An explicit rebuke within the escalating quarrel.'),
    'countercheck_rebuke': (['back', 'rebuke'], 'countercheck', 'noun', 'A countering rebuke, distinct in the named ladder from the preceding reproof.'),
    'peacemaker_person': (['peace', 'make', 'person'], 'peacemaker', 'noun', 'An agent of reconciliation, here the quoted conditional if personified.'),
    'stalking_horse_decoy': (['hide', 'horse'], 'stalking-horse', 'noun', 'A horse or horse-shaped cover used to approach quarry unseen; the Duke’s metaphor for wit concealed by folly.'),
    'dining_board': (['food', 'wood'], 'board', 'noun', 'A dining board, hence shared sustenance in board and bed; not a writing tablet.'),
    'populate_town': (['people'], 'people', 'verb', 'Fill a place with inhabitants, the song’s claim that marriage populates towns.'),
    'niece_kin': (['brother', 'daughter'], 'niece', 'noun', 'A brother’s daughter, here Duke Senior’s niece Celia; not his literal daughter or a claim that sister’s daughters are excluded from the broader kinship category.'),
    'bush_wine_sign': (['bush'], 'bush', 'noun', 'The branch or bush displayed to advertise wine, the epilogue’s proverbial sign; not an unspecified plant growing in the wine.'),
    'simper_smile': (['small', 'smile'], 'simper', 'verb', 'Smile in a self-conscious or affected manner in the epilogue’s audience teasing.'),
    'curtsy_gesture': (['knee', 'bow'], 'curtsy', 'verb', 'A bending-knee gesture of courtesy closing the epilogue; not an archery bow.'),
}

def prepare():
    lang = materialize()
    delta = read(PROJECT / 'lexical-delta.json')
    added = []
    for key, (parts, gloss, pos, meaning) in SENSES.items():
        if key in delta['entries']:
            continue
        assert key not in lang.lexicon, key
        form = ''.join(lang.lexicon[p]['form'] for p in parts)
        delta['entries'][key] = dict(form=form, roman=lang.reading(form), pos=pos,
            meaning=meaning, derivationKeys=parts, semanticId='lex.'+key,
            origin='Authored native derivation/sense: '+' + '.join(parts),
            usageScope='later-standard', status='authored', historicalForms=[])
        delta['glosses'][key] = gloss
        added.append(key)
    for key, form, gloss, meaning in [
        ('hymen_deity', 'himen', 'Hymen', 'The personified classical wedding god in the final masque, not an anatomical noun.'),
        ('jaques_de_boys_name', 'Ãak de bois', 'Jaques-de-Boys', 'Full source personal name of the second brother, distinct from the melancholy courtier. No identity suffix is printed.'),
        ('song_vocable_li', 'lila', 'vocable', 'Authored native performance syllables for the song’s hey refrain; not a lexical translation or historical attestation.'),
        ('song_vocable_lu', 'lulo', 'vocable', 'Authored contrasting native performance syllables for ho; not an ordinary borrowed English word.'),
        ('song_vocable_lilin', 'lila lilin lu', 'vocable', 'Authored expanded native refrain corresponding to hey-nonny-no.'),
        ('song_vocable_tiril', 'lila tiril a tiril tiril', 'vocable', 'Authored ringing performance refrain corresponding to the bird-song line; no claim of identical English metre.'),
    ]:
        if key in delta['entries']:
            continue
        assert key not in lang.lexicon
        is_name = key in {'hymen_deity', 'jaques_de_boys_name'}
        delta['entries'][key] = dict(form=form, roman=lang.reading(form),
            pos='proper' if is_name else 'interjection', meaning=meaning,
            semanticId='lex.'+key, usageScope='later-standard' if is_name else 'editorial-exception',
            status='authored', historicalForms=[],
            origin='Permitted phonetic personal-name adaptation' if is_name else 'Declared native literary performance adaptation')
        delta['glosses'][key] = gloss
        added.append(key)
    if added:
        delta['decisions'].append(dict(work='as-you-like-it', decision=
            'Final scenes preserve source numeral-versus-word notation, exact ordinal ladders, deliberate song refrains, distinct Jaques identities and native ordinary vocabulary. Song vocables are authored performance adaptations, not historical attestations.'))
    write(PROJECT/'lexical-delta.json', delta)
    materialize()
    print('Finale semantic additions:', len(added))

if __name__ == '__main__':
    prepare()
