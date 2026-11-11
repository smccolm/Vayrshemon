"""Court and family identities in the King John source."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries
from tools.unta_language import quantity


PEOPLE = {
    "john_plantagenet_king": ("jon", "John", "The English king who receives Philip's challenge on behalf of the young Arthur."),
    "eleanor_john_mother": ("elenor", "Eleanor", "Mother of John and Richard, widow of Henry II. She acknowledges the newly knighted Bastard as her grandson."),
    "pembroke_john_earl": ("pembrok", "Pembroke", "The earl at John's court directed to escort the French ambassador."),
    "essex_john_earl": ("eseks", "Essex", "The noble who brings the Faulconbridges' inheritance dispute before John."),
    "salisbury_john_earl": ("salzberi", "Salisbury", "The English noble who serves John and later judges the evidence of Arthur's death."),
    "chatillion_french_envoy": ("Ûatilyon", "Chatillion", "The envoy of Philip of France. Distinct from the soldier Jacques Chatillon named in Henry V."),
    "philip_france_king_john": ("filip", "Philip", "King of France, who lays claim to John's territories for Arthur. Distinct from the Bastard's given name."),
    "geoffrey_arthur_father": ("jefri", "Geoffrey", "John's deceased brother, Constance's husband and Arthur's father."),
    "arthur_brittany_heir": ("arÕur", "Arthur", "Son of Geoffrey and Constance. The French king advances the boy's claim against his uncle John."),
    "constance_arthur_mother": ("konstans", "Constance", "Widow of Geoffrey who seeks her son Arthur's inheritance."),
    "philip_faulconbridge_bastard": ("filip", "Philip", "The older Faulconbridge brother, who relinquishes the estate, is knighted Richard, and acknowledges Coeur de Lion as his father."),
    "faulconbridge_bastard_surname": ("falkonbrij", "Faulconbridge", "The family name as borne by Philip before he forgoes it. The same sound is heard in his brother's and mother's surname."),
    "robert_faulconbridge_son": ("robert", "Robert", "The younger brother who pursues the Faulconbridge inheritance, distinct from old Sir Robert."),
    "faulconbridge_younger_surname": ("falkonbrij", "Faulconbridge", "The surname when designating Robert the younger in the inheritance hearing."),
    "robert_faulconbridge_elder": ("robert", "Robert", "Old Sir Robert, the late husband of Lady Faulconbridge and legal father at issue in John's ruling."),
    "faulconbridge_elder_surname": ("falkonbrij", "Faulconbridge", "The surname of the knight employed by Coeur de Lion on an embassy to Germany."),
    "faulconbridge_mother_lady": ("falkonbrij", "Faulconbridge", "The Lady Faulconbridge who acknowledges Richard as Philip's father."),
    "faulconbridge_john_family": ("falkonbrij", "Faulconbridge", "The family name as an inherited identity or estate, without identifying one particular member."),
    "richard_lionheart_given": ("riÑard", "Richard", "Richard Coeur de Lion, John's brother, distinct from the son named Richard in his likeness."),
    "richard_bastard_knighted": ("riÑard", "Richard", "The new personal name King John confers on Philip at his knighting."),
    "nob_mock_knight": ("nob", "Nob", "The mock knight's name in Philip's rejection of his brother's looks and estate."),
    "joan_imagined_bride": ("jon", "Joan", "The hypothetical female name in the new knight's jest about making any Joan a lady."),
    "george_imagined_traveler": ("jorj", "George", "The name of a hypothetical person whom the newly knighted Richard proposes to call Peter."),
    "peter_wrong_name": ("peter", "Peter", "The wrong name which the newly knighted Bastard proposes to give a hypothetical George."),
    "james_gurney_servant": ("jemz", "James", "Given name of Lady Faulconbridge's servant who calls the Bastard Philip."),
    "gurney_servant_surname": ("gerni", "Gurney", "Surname of the servant dismissed before the Bastard questions his mother."),
    "basilisco_bragging_knight": ("basilisko", "Basilisco", "The boastful knight to whom Philip compares himself when he insists on his new knighthood."),
    "philip_sparrow_name": ("filip", "Philip", "Conventional bird name in Philip Sparrow, by which the new knight diverts his abandoned name. Distinct from both living men called Philip."),
    "louis_john_dauphin": ("lui", "Louis", "Philip of France's son and heir who speaks for Arthur before Angiers. Distinct from the Dauphins in other plays."),
    "austria_lion_duke": ("ostria", "Austria", "The duke who wears a lion's skin and whose deed the Dauphin blames for Richard's early death. Austria used as the man's title; separate from the place."),
    "blanche_john_niece": ("blanÛ", "Blanche", "John's niece, the Lady Blanche of Spain who arrives with Eleanor and is proposed as the Dauphin's bride."),
    "limoges_austria_title": ("limoj", "Limoges", "Another address to the same lion-clad duke called Austria. Constance uses both names in one speech."),
    "pandulph_legate_john": ("pandulf", "Pandulph", "Cardinal of Milan and papal legate who challenges John and later receives his crown."),
    "innocent_pope_john": ("inosent", "Innocent", "The pope in whose name Pandulph makes his demand. The witness gives his name without a regnal figure."),
    "stephen_archbishop_john": ("steven", "Stephen", "Given name of the chosen Archbishop of Canterbury whom John keeps from his see."),
    "langton_archbishop_john": ("langton", "Langton", "The surname of Stephen Langton in the legate's demand."),
    "hubert_arthur_keeper": ("hubert", "Hubert", "The man to whom John entrusts Arthur. He agrees to the king's request and later spares the boy."),
    "peter_pomfret_prophet": ("peter", "Peter", "The prophetic speaker from Pomfret whose words about John's crown lead to his arrest. Distinct from the jesting Peter in the opening scene."),
    "bigot_john_lord": ("bigot", "Bigot", "The noble who goes with Salisbury to seek Arthur and later joins the returning English lords."),
    "melun_french_count": ("melun", "Melun", "The French count who brings the cardinal's letter and later warns the English lords as he is dying."),
    "henry_son_king_john": ("henri", "Henry", "John's son who comes to Swinstead with the returning lords and receives their allegiance. No regnal numeral occurs in the source."),
}

PLACES = {
    "northamptonshire_birthplace": ("norÕamtonÛir", "Northamptonshire", "The county in which Philip says he was born."),
    "apennines_mountains": ("apeninz", "Apennines", "Mountains named by the Bastard in his parody of conversation with a traveler."),
    "pyrenees_mountains": ("pirenez", "Pyrenean", "The Pyrenean mountains named in the same exchange with an imagined traveler."),
    "po_italian_river": ("po", "Po", "The river in Philip's mock display of travel conversation."),
    "angiers_john_city": ("anjër", "Angiers", "The enclosed town before which the two royal hosts meet. Retains the spelling Angiers in the source column."),
    "volquessen_dowry": ("volkesen", "Volquessen", "The first territory named in John's grant of five provinces with Blanche."),
    "milan_legate_city": ("milan", "Milan", "The city attached to Pandulph's title as cardinal."),
    "pomfret_prophet_town": ("pomfret", "Pomfret", "The place whose streets Peter addresses. The prophet comes from the town, not the castle as a building."),
    "edmundsbury_town": ("edmundzberi", "Edmundsbury", "The town named Saint Edmundsbury where the English lords plan to meet Louis."),
    "bury_town_short": ("beri", "Bury", "The shorter name of the same Saint Edmundsbury in Bigot's direction to join the Dauphin."),
    "swinstead_abbey_place": ("swinsted", "Swinstead", "The settlement and abbey named in the witness. John seeks shelter there during his fever."),
    "goodwin_sands_name": ("gudwin", "Goodwin", "The name in Goodwin Sands, where the Dauphin's reinforcements are wrecked. Distinct from the Lincoln Washes."),
    "lincoln_washes_place": ("linkon", "Lincoln", "The geographic name modifying the tidal Washes where soldiers of the Bastard are lost."),
}

SENSES = {
    "abbey_religious_house": (["cloister", "house"], "abbey", "noun", "A religious house under an abbot. John intends to charge these houses with the cost of the expedition."),
    "abbot_religious_head": (["monk_cloister", "head"], "abbot", "noun", "The head of a monastic community. John orders money taken from the abbots' hoards."),
    "priory_religious_house": (["under", "cloister"], "priory", "noun", "A religious house under a prior, named alongside the abbeys in John's order."),
    "alphabet_writing_sign": (["sound", "mark"], "letter of the alphabet", "noun", "A written sign representing a speech sound. The alphabet in the absey-book differs from a letter sent to another person."),
    "primer_letters_book": (["sound", "mark", "book"], "letter primer", "noun", "An alphabet primer. The Bastard mocks a stock answer learnt as if from a beginner's book."),
    "empire_sovereign": (["empire", "lord"], "emperor", "noun", "The sovereign to whom old Sir Robert is sent in Germany. The title denotes a ruling monarch here."),
    "good_friday_observance": (["holy", "friday_source"], "Good Friday", "noun", "The Christian fast day evoked in the Bastard's flesh-eating joke, named by sacredness and the established native designation for the source weekday."),
    "landed_squire": (["land", "nobleman"], "landed squire", "noun", "Robert becomes a landholding gentleman when his brother becomes a landless knight."),
    "commodity_self_interest": (["own", "advantage"], "self-interest", "noun", "Commodity personified in the Bastard's soliloquy is the advantage one seeks for oneself. He ends by worshipping Gain."),
    "bowls_turning_bias": (["weight", "turn"], "bias", "noun", "The unequal weight that turns a rolling bowl aside, applied to the world's deviation from impartiality. Distinct from a bowl used as a vessel."),
    "alchemist_transmuter": (["gold", "make", "person"], "alchemist", "noun", "The sun as an alchemist gilding the clods of earth on the marriage day."),
    "excommunicate_judgment": (["church", "banish"], "excommunicate", "verb", "Exclude from the communion of the Church in Pandulph's sentence against John."),
    "heretic_dissenter": (["heresy", "person"], "heretic", "noun", "The ecclesiastical designation Pandulph applies to John when releasing his subjects from allegiance."),
    "iron_age_cruelty": (["iron", "age"], "Iron Age", "noun", "The cruel Iron Age Arthur invokes as he pleads against the use of hot irons. The repetition of iron joins the mythic age to the metal."),
    "binding_rope": (["twist", "thread"], "rope", "noun", "The executioners carry ropes for binding Arthur to a chair. No noose or ship's mooring is implied."),
    "brazier_coals": (["coal", "vessel"], "brazier", "noun", "The vessel of burning coals used to heat the irons. The stage direction does not describe a sanctuary implement."),
    "ascension_feast": (["rise", "heaven", "day"], "Ascension Day", "noun", "The Christian feast named in Peter's prediction about the king's crown. The text specifies noon on the next feast."),
    "shears_blades": (["join", "blade"], "shears", "noun", "A cutting instrument with joined blades, figuratively in destiny's hand and literally in the tailor's hand."),
    "washes_tidal_flats": (["sea_tide", "kjv_plain_land"], "tidal flats", "noun", "The Washes, the tidal flats named for Lincoln and then referred to briefly in the death scene. Distinct from the Goodwin Sands."),
    "sewing_thimble": (["needle", "shield"], "thimble", "noun", "The protective implement for a sewing finger that the Bastard contrasts with the armed gauntlet."),
}


def lexical_entries(language):
    entries, glosses = build_entries(language, PEOPLE | PLACES, SENSES, set(PLACES))
    quarter = quantity(1, "fraction", 4)["form"]
    form = quarter + " " + language.lexicon["penny"]["form"]
    entries["farthing_english_coin"] = dict(
        form=form, roman=language.reading(form), pos="noun", meaning="The English quarter-penny unit in Philip's three-farthing coin image. Distinct from the biblical monetary sense.",
        semanticId="lex.farthing_english_coin", origin="Spoken Unta quarter and native penny, retaining the source denomination.",
        usageScope="later-standard", status="authored", historicalForms=[])
    glosses["farthing_english_coin"] = "farthing"
    return entries, glosses


def prepare():
    add_source_entries("king-john", "julius-caesar", lexical_entries,
                       "The rival claims to England and the Faulconbridge estate introduce distinct royal and family identities. The play's source denominations and the inherited native Lionheart byname are preserved.")


if __name__ == "__main__":
    prepare()
