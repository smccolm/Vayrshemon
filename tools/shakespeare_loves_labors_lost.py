"""Native dramatic vocabulary and identities for Love's Labor's Lost."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "ferdinand_navarre_king": ("ferdinand", "Ferdinand", "King of Navarre who takes the oath with his three lords. Distinct from Katherine's father in Henry VIII."),
    "navarre_kingdom": ("navar", "Navarre", "The kingdom in which Ferdinand founds his court of study."),
    "berowne_navarre_lord": ("berun", "Berowne", "Ferdinand's companion who questions the terms of the oath before signing."),
    "longaville_navarre_lord": ("longavil", "Longaville", "The lord who devised the threat against a woman approaching the court."),
    "dumaine_navarre_lord": ("dumën", "Dumaine", "Navarre's lord and fellow scholar. His name shares the sound used for the two brothers in All's Well."),
    "aquitaine_french_territory": ("akiten", "Aquitaine", "The territory whose surrender is to be discussed with the French princess."),
    "armado_spanish_traveler": ("armado", "Armado", "The Spanish traveler whose style of speaking delights Ferdinand."),
    "jaquenetta_countrywoman": ("jakuneta", "Jaquenetta", "The woman Costard is accused of meeting in the park."),
    "anthony_dull_given": ("antoni", "Anthony", "The constable's given name in Armado's letter and his own reply."),
    "adriano_armado_given": ("adriano", "Adriano", "Armado's given name in his signature to the king."),
    "armado_interrupted_name": ("ar", "Arm-", "Dull's twice interrupted attempt at Armado's name. This is a fragment of this person's localized name."),
    "boyet_french_courtier": ("boyet", "Boyet", "The princess's envoy and companion, sent to ask for a personal audience."),
    "rosaline_french_lady": ("rozalin", "Rosaline", "The French lady who matches Berowne's wit."),
    "maria_french_lady": ("marya", "Maria", "The French attendant who met Longaville at a wedding in Normandy."),
    "katherine_french_lady": ("kathrin", "Katherine", "The French lady who speaks of Dumaine, distinct from Katherine who married Henry V."),
    "navarre_king_title": ("navar", "Navarre", "The territorial title used personally of Ferdinand, distinguished from the kingdom of Navarre."),
    "perigort_wedding_lord": ("perigor", "Perigort", "The lord whose wedding Maria attended in Normandy."),
    "jaques_wedding_father": ("Ãak", "Jaques", "The given name of the father of Lord Perigort's bride. Distinct from the brothers and the courtier in As You Like It."),
    "falconbridge_wedding_father": ("falkonbrij", "Falconbridge", "Jaques's family name. The bride is his heir."),
    "alanson_wedding_host": ("alenson", "Alanson", "The duke at whose house Katherine met Dumaine. The play supplies no further personal identity."),
    "charles_navarre_father": ("Ãarls", "Charles", "Ferdinand's late father. The princess says his officers issued receipts for the disputed sum."),
    "frances_costard_bride": ("fransis", "Frances", "The imaginary woman Costard thinks Armado might marry him to when told he will be enfranchised."),
    "argus_mythic_watchman": ("argus", "Argus", "The many-eyed watchman whom Berowne imagines guarding his mistress."),
    "joan_berowne_rhyme": ("jon", "Joan", "The generic Joan in Berowne's contrast with his lady at the end of Act 3. No particular woman is identified."),
    "zenelophon_ballad_beggar": ("zenelofon", "Zenelophon", "The beggar loved by King Cophetua in Armado's account of the ballad."),
    "guinover_british_queen": ("gwinovar", "Guinover", "The queen of Britain named in Boyet's jest about the age of the saying."),
    "holofernes_schoolmaster": ("holofernes", "Holofernes", "The schoolmaster who argues about the age and name of the dead deer, distinct from the biblical commander."),
    "nathaniel_curate": ("naÕaniel", "Nathaniel", "The curate at the hunt and later in the Worthies' entertainment."),
    "dictynna_moon_title": ("diktina", "Dictynna", "The lunar goddess-title Holofernes offers twice as the answer to Dull's riddle."),
    "dictima_dull_error": ("diktima", "dictima", "Dull's mispronunciation of Dictynna. The changed medial consonant remains audible."),
    "luna_moon_title": ("luna", "Luna", "The name of the moon invoked along with Phoebe by Nathaniel."),
    "mantuan_school_poet": ("mantuan", "Mantuan", "The poet whose pastoral Holofernes imperfectly recalls. Distinct from Virgil."),
    "venice_lagoon_city": ("venis", "Venice", "The city in the traveler's proverb quoted by Holofernes."),
    "horace_roman_poet": ("horas", "Horace", "The Roman poet whom Holofernes attempts to cite before he notices the verses."),
    "naso_ovid_cognomen": ("naso", "Naso", "Ovid's cognomen, which Holofernes connects with smelling out poetic flowers."),
    "tyburn_gallows_place": ("taiburn", "Tyburn", "The London place of execution whose three-sided gallows Berowne likens to the group of lovers."),
    "timon_misanthrope": ("timon", "Timon", "The severe critic invoked in Berowne's comparison, distinct from the man in Acts."),
    "kate_navarre_beloved": ("k×t", "Kate", "Dumaine's familiar name for Katherine, the French princess's companion."),
    "adramadio_costard_error": ("adramadyo", "Adramadio", "Costard's mangling of Adriano de Armado, repeated while Berowne tears up the paper."),
    "hesperides_garden": ("hesperides", "Hesperides", "The garden of the Hesperides where Berowne pictures Hercules climbing trees."),
    "sphinx_riddle_figure": ("sfinks", "Sphinx", "The riddle-giving creature in Berowne's comparison with love's subtlety."),
    "prometheus_fire_giver": ("prometeus", "Prometheus", "The fire-bringer named in Berowne's praise of women's eyes."),
    "priscian_grammarian": ("priskian", "Priscian", "The grammarian figuratively scratched by Nathaniel's faulty Latin."),
    "mediterranean_sea_name": ("mediteranum", "Mediterraneum", "Armado's learned name for the Mediterranean Sea."),
    "judas_maccabaeus_role": ("judas makabeus", "Judas Maccabaeus", "The Worthy Judas Maccabaeus in the pageant. Distinct from Judas Iscariot and from the schoolmaster playing this role."),
    "muscovy_mask_land": ("moskov", "Muscovy", "The land associated with the costumes in Boyet's guess about the masked men."),
    "pompion_costard_error": ("pompyon", "Pompion", "Costard's distorted name for Pompey the Great in announcing his part. The source's gourd echo is documented in the review."),
    "alisander_pageant_name": ("alisander", "Alisander", "Nathaniel's stage spelling of Alexander the Great. This is the same conqueror, with a different form in the pageant."),
    "judas_maccabaeus_given": ("judas", "Judas", "The given name of the Worthy Judas Maccabaeus, whom the other players confuse with Iscariot."),
    "maccabaeus_pageant_epithet": ("makabeus", "Maccabaeus", "The epithet of the Worthy Holofernes plays, alternately spoken alone and joined with Judas."),
    "jude_stage_fragment": ("jud", "Jude", "A clipped form of the stage Judas's given name in the courtiers' donkey-name joke."),
    "marcade_french_messenger": ("markad", "Marcade", "The messenger who brings news of the French king's death to his daughter."),
    "dick_winter_shepherd": ("dik", "Dick", "The shepherd who warms his fingers in the winter song."),
    "tom_winter_woodbearer": ("tom", "Tom", "The man carrying logs indoors in the winter song."),
    "joan_winter_cook": ("jon", "Joan", "The woman stirring the pot in both winter refrains, distinct from the Joan in Berowne's rhyme."),
    "marian_winter_song": ("maryan", "Marian", "The woman whose nose is red and raw in the winter song."),
}

SENSES = {
    "navarre_academe": (["study","house"], "academe", "noun", "The little house of study Ferdinand intends his court to become."),
    "scholarly_proceed": (["learn","proceed"], "proceed in learning", "verb", "An advance in learning or academic rank. Dumaine follows it with the same native proceed root for progress more broadly."),
    "costard_apple_swain": (["large","apple"], "Costard", "proper", "The rustic's fruit-name, a large apple. It can suggest the rounded head as the comedy develops."),
    "dull_constable": (["dull"], "Dull", "proper", "The constable's speaking name uses the established native word for slow-witted."),
    "christmas_nativity_feast": (["nativity_saviour","birth","feast"], "Christmas", "noun", "The feast of the Saviour's birth that Berowne sets against May's season of flowers."),
    "farborough_dull_office": (["far","village","officer"], "farborough", "noun", "Dull's garbled title for a district peace officer. The native comic form retains the intrusion of far."),
    "bench_form_costard": (["form","seat"], "bench-form", "noun", "Costard hears a seat in the legal word form. The native compound echoes the same word for form in his formula."),
    "sinplicity_costard": (["sin","simplicity"], "sin-simplicity", "noun", "Costard slips sin into simplicity as he speaks of listening after flesh."),
    "mote_armado_page": (["drama_native_mote"], "Mote", "proper", "Armado's young page. The local source names him Mote. His native speck-name anticipates Armado's repeated remarks about his smallness."),
    "deywoman_park": (["milk","woman"], "dairywoman", "noun", "The keeper of dairy produce at the park, the work assigned to Jaquenetta."),
    "passado_fencing": (["step","thrust"], "passing thrust", "noun", "The fencing thrust with an advancing step that Armado says Cupid ignores."),
    "duello_fencing": (["sword","fight"], "formal sword duel", "noun", "The formal practice of single combat whose rules are of no consequence to Cupid."),
    "folio_book_format": (["fold","book"], "folio", "noun", "A book printed on sheets folded once. Armado wants whole volumes in this large format."),
    "french_brawl_dance": (["french","dance"], "French brawl", "noun", "The French dance Mote proposes, heard by Armado as a quarrel in French."),
    "hackney_hired_horse": (["hire_service","horse"], "hired horse", "noun", "A hired-out horse in Mote's aside about Armado's sweetheart."),
    "lenvoi_closing_verse": (["farewell","verse"], "closing verse", "noun", "The short concluding verse illustrated by the exchange about the fox, ape, bee and goose."),
    "plantain_wound_herb": (["broad","leaf","herb"], "plantain", "noun", "The broad-leaved plant Costard wants for his injured shin."),
    "humblebee_verse": (["hair","bee"], "bumblebee", "noun", "The furry bee in Armado's three-animal verse."),
    "remuneration_service_pay": (["service","pay"], "remuneration", "noun", "Armado's learned term for compensation. Costard treats the word as the fixed price of three farthings."),
    "guerdon_honour_gift": (["honour","gift"], "guerdon", "noun", "Berowne's name for his reward, misrepeated by Costard as gardon."),
    "inkle_woven_tape": (["narrow","ribbon"], "inkle", "noun", "The narrow woven tape in Costard's imagined bargaining example."),
    "placket_garment_opening": (["garment","open"], "placket", "noun", "The garment opening in Berowne's sexual mock-title for Cupid."),
    "paritor_summons_officer": (["summon","officer"], "summoning officer", "noun", "An officer serving summonses, one of Cupid's trotting retinue."),
    "spleen_laughter_organ": (["belly","laughter"], "spleen", "noun", "The bodily seat of laughter that Armado says Costard's thought stirs. It receives a distinct native term from spleen as anger or caprice."),
    "monarcho_braggart": (["boast","king"], "Monarcho", "proper", "The self-styled monarch invoked as Boyet's model for the fantastical Armado. The translated royal nickname is separate from the traveler himself."),
    "archery_target_pin": (["target","pin_fastener"], "target pin", "noun", "The pin in the centre of the archery target in the women's banter with Boyet."),
    "archery_white_clout": (["white","cloth"], "target cloth", "noun", "The white target cloth for the archer to hit."),
    "archery_shot": (["arrow","shoot"], "shot", "noun", "A shot with a bow. The forester and princess use it of her chance to shoot and the fairness of her shot."),
    "pricket_spike_buck": (["point","stag_deer"], "spike buck", "noun", "The hunting name for a buck in its second year, with spike antlers. This is Dull's identification of the deer."),
    "sore_fourth_year_buck": (["wound"], "sore buck", "noun", "The fourth-year hunting name, rendered as a deliberate poetic homonym of the native wound root for Holofernes's verse."),
    "roman_angle_letter_l": (["corner","drama_native_alphabet_writing_sign"], "Roman L", "noun", "The corner-shaped source letter L, also the Roman numeral for fifty. The native descriptive name refers to that foreign sign."),
    "pomewater_apple": (["juice","apple"], "pomewater", "noun", "A kind of apple compared to the deer in Holofernes's affected description."),
    "brain_membrane_pia": (["brain","skin"], "brain membrane", "noun", "The pia mater, figured as a womb nurturing Holofernes's flights of invention."),
    "allusion_riddle_turn": (["jest","turn"], "allusion", "noun", "The play or allusive turn in the moon riddle when the teacher substitutes Adam for Cain."),
    "collusion_riddle_turn": (["plot","turn"], "collusion", "noun", "Dull's wrong word for the riddle's allusion, with the same native ending and a conspiratorial first element."),
    "pollution_riddle_turn": (["defile","turn"], "pollution", "noun", "Dull's second mistaken ending to the exchange. The recurring turn now begins with the root for defilement."),
    "birdbolt_blunt_arrow": (["bird","arrow"], "birdbolt", "noun", "The blunt hunting arrow with which Cupid has metaphorically struck the king."),
    "whipping_gig_top": (["turn","game"], "spinning top", "noun", "The child's top which Hercules incongruously whips."),
    "pushpin_game": (["push","pin_fastener"], "pushpin", "noun", "A children's pin game, which Berowne imagines the wise Nestor playing."),
    "warm_caudle_drink": (["warm","drink"], "caudle", "noun", "The restorative warm drink requested for the three lovesick men."),
    "coach_passenger_vehicle": (["traveller","wagon"], "coach", "noun", "The covered passenger vehicle that carries the beloved in the king's comparison with a tear."),
    "even_numerical_parity": (["drama_native_pair","complete"], "even in number", "modifier", "All members can be paired. Dumaine remarks that four lovers now make an even company."),
    "honours_long_word": (["honour","achieve","ability","state"], "honour-attaining capacity", "noun", "An ostentatiously long native word for the state of being able to attain honours in Costard's comparison with the page's height."),
    "vowel_school_sound": (["open","drama_native_sound"], "vowel", "noun", "A vowel in the set recited in the schoolmaster's spelling game. The five in the speech refer to the source exercise."),
    "consonant_school_sound": (["close","drama_native_sound"], "consonant", "noun", "A consonant contrasted with the five cited source vowel letters."),
    "hornbook_primer": (["horn","book"], "hornbook", "noun", "The elementary primer protected by a transparent sheet of horn, taken by Mote as a horn on the teacher's head."),
    "flapdragon_game": (["fire","kjv_raisin"], "flapdragon", "noun", "A burning morsel swallowed for sport. Costard says the tiny page would be easier to swallow."),
    "favour_worn_token": (["love","sign"], "favour token", "noun", "A wearable token of affection. The ladies swap these tokens to misdirect their disguised suitors."),
    "fairing_gift": (["market","gift"], "fairing", "noun", "A present of the sort bought at a fair, used of the suitors' gifts."),
    "pair_taunt_cardhand": (["playing_card","victory"], "winning hand", "noun", "The strong card hand in Rosaline's pair-taunt comparison. Her superiority over Berowne is the point; the text names no precise total of cards."),
    "musician_moor_mask": (["dark","skin","person"], "Moor", "noun", "The people described by the historical source label Blackamoors who enter with music. They are listed separately from the gentlemen in Muscovite disguises."),
    "sycamore_park_tree": (["shade","tree"], "sycamore", "noun", "The tree under whose cool shade Boyet hopes to nap. No identity with the distinct biblical sycomore is imposed."),
    "metheglin_spiced_mead": (["herb","honey","drink"], "spiced mead", "noun", "The spiced honey drink in Berowne's second throw of sweet things."),
    "wort_malt_liquid": (["drama_native_brewing_malt","juice"], "wort", "noun", "The sweet malt liquid before fermentation, included between mead and malmsey."),
    "malmsey_sweet_wine": (["sweet","wine"], "malmsey", "noun", "The rich sweet wine that completes Berowne's throw of three sweets."),
    "novum_dice_game": (["dice","game"], "novum", "noun", "The dice game excepted in Berowne's boast that five such players cannot otherwise be picked. The spoken line gives no score for a throw."),
    "polax_heraldic_weapon": (["staff","blade"], "poleaxe", "noun", "The long-handled bladed weapon carried by the lion in Alexander's painted device."),
    "cittern_instrument": (["string","lute_plucked"], "cittern", "noun", "A plucked stringed instrument whose carved head Boyet compares with the schoolmaster's face."),
    "lemon_citrus_fruit": (["sour","yellow","fruit"], "lemon", "noun", "The lemon that Berowne imagines in Hector's hand."),
    "clove_spice_bud": (["drama_native_spice","bud"], "clove", "noun", "An aromatic dried bud stuck into the lemon. The next speaker hears the participle of cleaving."),
    "calf_leg_muscle": (["leg","brawn_muscle"], "calf", "noun", "The fleshy part of the lower leg mocked in Hector's entrance."),
    "house_for_the_sick": (["sick","house"], "hospital", "noun", "The house where Berowne agrees to try his jokes on the sick."),
    "rook_flock_bird": (["flock","crow_bird"], "rook", "noun", "The flocking crow relative in the spring song, distinct from the smaller daw."),
    "hiems_winter_figure": (["winter"], "Hiems", "proper", "The personification introduced by a Latin name in the source. The native name uses the seasonal root."),
    "ver_spring_figure": (["flower","season"], "Ver", "proper", "The personification introduced by a Latin name in the source. The native name means season of flowers."),
}


def lexical_entries(language):
    entries, glosses = build_entries(language, NAMES, SENSES, {"navarre_kingdom","aquitaine_french_territory","venice_lagoon_city","tyburn_gallows_place","hesperides_garden","mediterranean_sea_name","muscovy_mask_land"})
    for key, original, old, new, gloss in [
        ("egma_costard", "riddle", "bra", "", "garbled riddle"),
        ("gardon_costard", "guerdon_honour_gift", "lam", "", "garbled guerdon"),
        ("dun_costard_mistitle", "lord", "ne", "", "garbled honorific"),
        ("chirrah_armado_greeting", "sirrah", "z", "j", "garbled sirrah"),
        ("pursent_costard_error", "present", "v", "vr", "garbled present"),
        ("parfect_costard_error", "perfect", "na", "", "garbled perfect"),
    ]:
        model = (language.lexicon | entries)[original]
        assert model["form"].count(old) == 1
        form = model["form"].replace(old, new)
        entries[key] = dict(form=form, roman=language.reading(form), pos="verb" if key in {"pursent_costard_error","parfect_costard_error"} else "noun",
            meaning=gloss.capitalize()+" in Costard's mispronunciation.",
            semanticId="lex."+key, derivationKeys=[original],
            origin=("Stage mispronunciation with an added initial consonant." if key=="pursent_costard_error"
                    else "Stage mispronunciation with a changed initial consonant of the native address." if key=="chirrah_armado_greeting"
                    else "Stage mispronunciation with a dropped medial syllable from the native expression."),
            usageScope="later-standard", status="authored", historicalForms=[])
        glosses[key] = gloss
    for symbol, form in {"a":"a","b":"bi","d":"di","e":"e","i":"i","o":"o","t":"ti","u":"u"}.items():
        key = "school_source_letter_" + symbol
        entries[key] = dict(form=form, roman=language.reading(form), pos="noun",
            meaning="Spoken name of the source letter "+symbol.upper()+" in the schoolmaster's spelling lesson.",
            semanticId="lex."+key, origin="Quoted foreign letter-name adapted for the dramatic recitation.",
            usageScope="later-standard", status="authored", historicalForms=[])
        glosses[key] = "letter "+symbol.upper()
    for key, form, gloss, meaning, roots in [
        ("sorel_third_year_buck", language.lexicon["wound"]["form"]+"l", "sorel buck",
         "The third-year buck. The written and pronounced l extends the native homonym for sore in the preceding hunting term. This literary spelling lets the addition work onstage.", ["sore_fourth_year_buck"]),
        ("holofernes_sung_ut", "la", "sung ut", "Native performance syllable for ut in the six-note sequence.", ["song_vocable_li"]),
        ("holofernes_sung_re", "le", "sung re", "Native performance syllable for re in the six-note sequence.", ["song_vocable_li"]),
        ("ba_sheep_sound", "ba", "ba", "The source exercise's reversed B and A pronounced together, also performed as a bleat. This is a quoted sound, not the native name of the animal.", ["school_source_letter_b","school_source_letter_a"]),
        ("winter_owl_call", "wït wç", "owl call", "The two-part sung owl call in both winter refrains, shaped from a short bright note followed by a low hoot.", ["drama_native_owl"]),
    ]:
        entries[key] = dict(form=form, roman=language.reading(form), pos="noun" if key.startswith("sorel_") else "interjection",
            meaning=meaning, semanticId="lex."+key, derivationKeys=roots, origin="Native dramatic spelling for the source's sound play.",
            usageScope="later-standard", status="authored", historicalForms=[])
        glosses[key] = gloss
    return entries, glosses


def prepare():
    add_source_entries("loves-labors-lost", "king-lear", lexical_entries,
        "Ferdinand's three companions and their three years of study are distinct quantities. Dumaine of Navarre has his own identity. Costard and Dull have native speaking names.")


if __name__ == "__main__":
    prepare()
