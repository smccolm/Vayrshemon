"""Source identities and native dramatic senses for King Lear."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


PEOPLE = {
    "lear_british_king": ("lir", "Lear", "The father of Goneril, Regan and Cordelia who divides his kingdom while reserving the name of king."),
    "kent_lear_earl": ("kent", "Kent", "The earl who challenges Lear's division and is banished. Distinct from the county."),
    "gloucester_lear_earl": ("gloster", "Gloucester", "The father of Edgar and Edmund. Distinct from the other dukes and earls called Gloucester."),
    "edmund_gloucester_son": ("edmund", "Edmund", "Gloucester's younger son, acknowledged publicly despite his birth outside marriage."),
    "edgar_gloucester_son": ("edgar", "Edgar", "Gloucester's elder son by order of law, distinct from Edmund."),
    "albany_goneril_husband": ("albani", "Albany", "The duke married to Goneril. His intended share is compared with Cornwall's at the opening."),
    "cornwall_regan_husband": ("kornwal", "Cornwall", "The duke married to Regan. Distinct from the geographic name Cornwall."),
    "goneril_lear_daughter": ("goneril", "Goneril", "Lear's eldest daughter and Albany's wife."),
    "regan_lear_daughter": ("regan", "Regan", "Lear's second daughter, Cornwall's wife."),
    "cordelia_lear_daughter": ("kordelya", "Cordelia", "Lear's youngest daughter, who refuses to measure love in a declaration for a dower."),
    "france_cordelia_suitor": ("frans", "France", "The king who courts Cordelia and accepts her without a dowry. Distinct from France as a country and from Philip in King John."),
    "burgundy_cordelia_suitor": ("burgundi", "Burgundy", "The duke who seeks Cordelia with a dower. This entry is the suitor, not the territory."),
    "scythian_lear_people": ("siÕian", "Scythian", "The people named in Lear's hostile comparison. The following figure who eats his own offspring is a second comparison."),
    "tom_bedlam_figure": ("tom", "Tom", "The conventional Tom of Bedlam whom Edmund invokes as a model for feigned melancholy. Edgar later takes a Poor Tom disguise."),
    "oswald_goneril_steward": ("oswald", "Oswald", "Goneril's steward. She tells him to provoke a quarrel with Lear by giving him poor service."),
    "jug_song_nickname": ("jug", "Jug", "The woman addressed by a familiar name in the Fool's snatch of song. She has no entrance or assigned speech."),
    "gloucester_lear_destination": ("gloster", "Gloucester", "Named destination of Kent's ride with Lear's letter. The source does not give a more precise address."),
    "curan_household": ("kuran", "Curan", "The member of Gloucester's household who tells Edmund of the duke's coming and of a whispered dispute between the two dukes."),
    "lipsbury_pinfold_place": ("lipsberi", "Lipsbury", "The name Kent gives to the pound in which he would trap Oswald. Its real-world location is unspecified."),
    "sarum_lear_plain": ("sarum", "Sarum", "The plain on which Kent imagines driving Oswald as a goose."),
    "camelot_lear_place": ("kamelot", "Camelot", "The legendary destination to which Kent would drive Oswald cackling from Sarum."),
    "poor_tom_edgar_alias": ("tom", "Tom", "The Poor Tom persona adopted by Edgar to evade the hunt. He borrows a beggar's name which Edmund had invoked earlier."),
    "turlygod_edgar_alias": ("turligod", "Turlygod", "Edgar's second beggar appellation, paired with Poor Tom. No derivation from the English religious noun is asserted."),
    "dolphin_ballad_address": ("dolfin", "Dolphin", "An address in Edgar's song. The local spelling allows a Dauphin echo without identifying any particular prince."),
    "flibbertigibbet_fiend": ("flibertijibet", "Flibbertigibbet", "The fiend Edgar says walks from curfew to the first cock and spoils eyes and wheat."),
    "swithold_charm": ("swiÕold", "Swithold", "The figure crossing the upland in Edgar's sung charm against the nightmare."),
    "smulkin_fiend": ("smulkin", "Smulkin", "The fiend Poor Tom bids be quiet."),
    "modo_fiend": ("modo", "Modo", "One of the two names Edgar gives the Prince of Darkness."),
    "mahu_fiend": ("mahu", "Mahu", "The second name Edgar gives the Prince of Darkness."),
    "rowland_ballad_knight": ("roland", "Rowland", "The knight in Edgar's dark tower song. Distinct from Sir Rowland de Boys."),
    "gloucester_lear_earldom": ("gloster", "Gloucester", "The earldom Cornwall grants Edmund, whose father is still alive."),
    "edmund_as_gloucester": ("gloster", "Gloucester", "Edmund addressed by his new earldom. The elder Gloucester retains his own name and identity."),
    "caius_kent_disguise": ("kaius", "Caius", "Kent's name in disguise as Lear's servant. Kent reveals explicitly that he and Caius are the same man."),
    "frateretto_fiend": ("fratereto", "Frateretto", "The fiend Edgar says tells him about Nero fishing in the lake of darkness."),
    "bessy_song": ("besi", "Bessy", "The woman called across the stream in Edgar's song, answered by the Fool."),
    "tray_lear_hound": ("trei", "Tray", "The first of the little dogs Lear imagines barking at him."),
    "obidicut_fiend": ("obidikut", "Obidicut", "The fiend of lust in Poor Tom's list of five."),
    "hobbididance_fiend": ("hobidivalen", "Hobbididance", "The prince of dumbness in Tom's list. The local name differs from Hoppedance and retains the native dance ending."),
    "la_far_french_marshal": ("la far", "La Far", "The marshal left in command after Cordelia's husband returns to France."),
}

SENSES = {
    "conceive_comprehend": (["receive", "thought"], "conceive mentally", "verb", "Kent's inability to conceive what Gloucester means. The paired bodily sense answers his phrase."),
    "conceive_in_womb": (["receive", "child"], "conceive a child", "verb", "Gloucester applies the shared native receive construction to Edmund's mother's pregnancy."),
    "dragons_tail_astrology": (["dragon", "tail"], "Dragon's Tail", "proper", "The astrological Dragon's Tail invoked in Edmund's mock account of his parents' coupling."),
    "great_bear_constellation": (["great", "bear_animal"], "Great Bear", "proper", "Ursa Major, the constellation Edmund says presided over his birth. The native name translates Great Bear."),
    "lawful_birth_status": (["law", "birth"], "lawfully born", "modifier", "A child born within recognized marriage. Edmund repeats the term legitimate while planning to displace Edgar."),
    "moiety_allotment": (["give", "part"], "allotted share", "noun", "Either duke's allotted share of Lear's kingdom. Its extent is compared with the other duke's but is not given as half the whole realm."),
    "lear_fool_companion": (["fool"], "Fool", "noun", "Lear's professional Fool. Goneril's later description of old fools is an insult, not this role."),
    "fools_cap_coxcomb": (["fool", "cap_bonnet"], "fool's cap", "noun", "The cap the Fool offers Kent. Its name transfers the office and the charge of folly to whoever wears it."),
    "football_game": (["foot", "ball"], "football", "noun", "The rough ball game alluded to when Kent trips Goneril's steward."),
    "numeral_sign": (["write", "count"], "written numeral", "noun", "A written sign that represents a number. The Fool pictures Lear as a solitary round zero without another digit beside it."),
    "parent_slayer": (["parent", "killer"], "parent-killer", "noun", "The parricides Edmund claims to have warned Edgar about. In his fabricated account the threatened parent is their father."),
    "godson_sponsored_child": (["sponsor", "son"], "godson", "noun", "Edgar is Gloucester's son and Lear's godson. The relationship records Lear's sponsorship and naming of Edgar."),
    "pinfold_enclosure": (["herd_livestock", "fence"], "cattle pound", "noun", "A fenced pound for stray animals. Kent imagines penning Oswald where he cannot run away."),
    "zed_last_source_sign": (["drama_native_last", "drama_native_alphabet_writing_sign"], "zed", "noun", "The last letter in the source alphabet. Kent calls it superfluous. The reference is to the English letter and its position in that alphabet."),
    "mother_rising_fit": (["rise", "grief"], "rising fit", "noun", "Lear calls the mounting distress in his body the mother. It rises toward his heart and he commands it down."),
    "hysterica_passio_lear": (["womb", "disease_ailment"], "womb-affliction", "noun", "Learned native rendering of the Latin tag Hysterica passio beside Lear's plain expression for his rising distress."),
    "weathercock_roof": (["wind", "cock_fowl"], "weathercock", "noun", "The bird-shaped vane above the steeple which Lear dares the storm to submerge."),
    "codpiece_garment": (["groin", "cover"], "codpiece", "noun", "The garment covering the male genitals. The Fool pairs it with the headpiece and later identifies himself with it."),
    "hovel_shelter": (["poor", "house"], "hovel", "noun", "The rough shelter Kent offers Lear during the storm."),
    "brewing_malt": (["sprout_grow", "grain_kernel"], "malt", "noun", "Sprouted grain for brewing. The Fool's brewers adulterate their malt with water."),
    "pillicock_ballad": (["little", "cock_fowl"], "Pillicock", "proper", "An affectionate and bawdy name from Edgar's song. Repeat the same native name for the hill."),
    "tithing_district": (["village", "boundary"], "tithing district", "noun", "The local jurisdiction through which Tom is whipped. No tax or exact count of households is asserted."),
    "theban_inhabitant": (["thebes", "person"], "Theban", "noun", "A person of Thebes. Lear calls Edgar a Theban and later an Athenian."),
    "hoppedance_fiend": (["hop_step", "dance"], "Hoppedance", "proper", "The named fiend Edgar hears crying in Tom's hungry belly. The native name retains both movements."),
    "blanch_lear_hound": (["white"], "Blanch", "proper", "The white-named dog in Lear's list. Distinct from the Lady Blanche of King John."),
    "sweetheart_lear_hound": (["sweet", "heart"], "Sweetheart", "proper", "The last dog Lear names in the mock trial."),
    "eye_jelly_lear": (["soft", "eye"], "eye jelly", "noun", "Cornwall calls Gloucester's remaining eye a soft jelly as he destroys it."),
    "cuckooflower_plant": (["cuckoo", "flower"], "cuckooflower", "noun", "One of the flowers in Lear's wild crown, listed by Cordelia."),
    "samphire_cliff_herb": (["cliff", "herb"], "samphire", "noun", "The coastal plant gathered by the man in Edgar's description of the imaginary drop."),
    "cockboat_tender": (["ship", "boat"], "ship's boat", "noun", "The small tender of the larger vessel in Edgar's account of the supposed cliff."),
    "buoy_seamark": (["float", "sign"], "buoy", "noun", "A small floating mark to which the supposed height reduces a ship's boat."),
    "press_money_soldier": (["soldier", "pay"], "recruit's pay", "noun", "Pay for an impressed soldier. Lear imagines recruiting, then turns to archery."),
    "handy_dandy_game": (["hand", "choose"], "choose-a-hand", "noun", "A guessing game invoked when Lear interchanges the places of judge and thief."),
    "captain_prison_order": (["captain"], "captain", "noun", "The captain entrusted with Edmund's note to follow the prisoners. Edmund later sends him a reprieve token."),
    "captain_trumpet_signal": (["captain"], "captain", "noun", "The captain in Albany's company who orders the trumpet to sound. The source introduces a captain after the recipient of Edmund's note has exited."),
}


def lexical_entries(language):
    entries, glosses = build_entries(language, PEOPLE, SENSES, places={
        "gloucester_lear_destination", "gloucester_lear_earldom", "lipsbury_pinfold_place", "sarum_lear_plain", "camelot_lear_place"
    })
    # Edmund sings the written notes in order. The syllables draw on the existing
    # lila, lulo and lilin refrains; the source notes remain visible in the gloss.
    for note, form in [("fa", "li"), ("sol", "lu"), ("la", "lo"), ("mi", "lin")]:
        key = "lear_sung_" + note
        entries[key] = dict(form=form, roman=language.reading(form), pos="interjection",
            meaning=f"Singable native syllable for Edmund's source {note} in the four-note passage.",
            semanticId="lex." + key, origin="Literary performance adaptation from the dramatic song vocables.",
            usageScope="later-standard", status="authored", historicalForms=[])
        glosses[key] = f"sung {note}"
    key = "edgar_rustic_address"
    full = language.lexicon["sir"]["form"]
    assert full == "arzi"
    form = full[:-2]
    entries[key] = dict(form=form, roman=language.reading(form), pos="noun",
        meaning="Clipped form of the respectful address in Edgar's peasant voice to Oswald.",
        semanticId="lex." + key, origin="Literary stage contraction of arzi to its respect root ar.",
        derivationKeys=["sir"], usageScope="later-standard", status="authored", historicalForms=[])
    glosses[key] = "sir (rustic)"
    return entries, glosses


def prepare():
    add_source_entries("king-lear", "king-john", lexical_entries,
        "Kent weighs the two dukes' allotments. Lear's thirds are exact shares. The two native constructions for conceive share a root and distinguish Kent's meaning from Gloucester's sexual pun.")


if __name__ == "__main__":
    prepare()
