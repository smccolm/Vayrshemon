"""Names, ranks and Venetian references in the supplied Othello."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "othello_venetian_general": ("otelo", "Othello", "Venice's general and Desdemona's husband."),
    "iago_venetian_ensign": ("yago", "Iago", "The ensign in Othello's service who wanted Cassio's lieutenancy."),
    "roderigo_venetian_suitor": ("roderigo", "Roderigo", "The suitor of Desdemona whose purse Iago controls."),
    "brabantio_venetian_senator": ("brabansiyo", "Brabantio", "Desdemona's father and a senator of Venice."),
    "desdemona_general_wife": ("dezdemona", "Desdemona", "Brabantio's daughter, married to Othello."),
    "desdemon_familiar_short": ("dezdemon", "Desdemon", "The shorter form of Desdemona used by Cassio and Othello. The same person as Desdemona."),
    "naples_musicians_city": ("napoli", "Naples", "The city in the Clown's jest about instruments speaking through the nose. It shares the permitted place form of the earlier kingdom."),
    "cassio_florentine_officer": ("kasiyo", "Cassio", "The Florentine officer Othello chose as his lieutenant."),
    "michael_cassio_given": ("maikel", "Michael", "Cassio's given name, distinct from all the earlier Michaels."),
    "emilia_iago_wife": ("emiliya", "Emilia", "Iago's wife and Desdemona's attendant."),
    "bianca_cassio_companion": ("biyanka", "Bianca", "The woman attached to Cassio in Cyprus."),
    "montano_cyprus_governor": ("montano", "Montano", "The official in Cyprus whom Cassio wounds in the night brawl."),
    "lodovico_venetian_envoy": ("lodoviko", "Lodovico", "The Venetian relative of Brabantio who delivers a dispatch to Othello."),
    "gratiano_brabantio_brother": ("gratsiyano", "Gratiano", "Brabantio's brother, distinct from the man of the same name in The Merchant of Venice."),
    "janus_roman_deity": ("yanus", "Janus", "The Roman god named in Iago's oath when he sees the approaching lights."),
    "mauritania_iago_destination": ("mauritaniya", "Mauritania", "The destination Iago tells Roderigo the couple will visit. It conflicts with the recall to Venice."),
    "barbary_willow_singer": ("barbari", "Barbary", "The maid in Desdemona's mother's household who died singing the willow song. Distinct from the region that qualified Iago's horse insult."),
    "palestine_pilgrimage_land": ("palestin", "Palestine", "The distant destination in Emilia's exaggeration about walking barefoot for a touch of Lodovico's lip."),
    "pontic_sea_water": ("pontik", "Pontic", "The Pontic Sea, the first water in Othello's comparison of his thoughts to an unreturning current."),
    "propontic_sea_water": ("propontik", "Propontic", "The water Othello names between the Pontic and the Hellespont."),
    "stephen_english_ballad_king": ("steven", "Stephen", "The thrifty king in the old-cloak ballad, distinct from the archbishop or the biblical martyr."),
    "almain_german_demonym": ("aleman", "Almain", "The second name Iago uses for a German drinker in his boast about English drinking."),
    "veronesa_ship_designation": ("veroneza", "Veronesa", "The designation the Third Gentleman gives the Venetian ship. The wording leaves its precise significance open."),
    "rhodes_eastern_island": ("rodes", "Rhodes", "The island where Iago says his commander saw him in action. The localized place form also occurs in Acts."),
    "moor_source_ethnonym": ("maur", "Moor", "The historical ethnonym speakers apply to Othello. Its use here identifies neither his precise birthplace nor his faith."),
    "angelo_venetian_reporter": ("anjelo", "Angelo", "The signior who sends the sailor's report of a course to Rhodes. Distinct from the deputy in Vienna."),
    "marcus_luccicos_given": ("markus", "Marcus", "The given name of the Venetian sought by the Duke while the fleet reports are discussed."),
    "luccicos_venetian_absentee": ("lukikos", "Luccicos", "Marcus's family name. The senator reports that he is in Florence."),
    "ottoman_dynastic_name": ("otoman", "Ottoman", "The dynastic name in the messenger's designation of the Ottomites and later references to the fleet."),
}

SENSES = {
    "purgatory_souls_cleansing": (["soul","purify"], "purgatory", "noun", "The state of purification after death which Emilia says she would risk in her hypothetical bargain."),
    "fitchew_polecat": (["stink","weasel"], "polecat", "noun", "The strong-smelling mustelid Cassio calls Bianca as she approaches. Perfuming the animal caps his insult."),
    "crusado_portuguese_coin": (["cross_mark","coin_currency"], "crusado", "noun", "The cross-marked Portuguese coin in Desdemona's imagined full purse. Its number and exchange value are unspecified."),
    "mummy_preserved_substance": (["kjv_embalm","flesh"], "mummy", "noun", "Preserved bodily material used as dye in Othello's story about maidens' hearts. The statement is his account of the cloth's origins."),
    "poppy_sleep_flower": (["sleep","flower"], "poppy", "noun", "The poppy in Iago's list of things that will never restore Othello's sleep."),
    "leet_local_court": (["town","judgment"], "leet", "noun", "The local court invoked alongside law days in Iago's image of improper thoughts sitting in judgment."),
    "jess_falcons_strap": (["hawk","strap"], "jess", "noun", "The strap restraining a hawk's leg. Othello imagines his heartstrings as jesses."),
    "hollander_demonym": (["holland_region","person"], "Hollander", "noun", "A person of Holland in Iago's brag about rival drinkers."),
    "equinox_equal_night": (["equal","night"], "equinox", "noun", "The balancing of night and day used by Iago to claim Cassio's vice equals his virtue."),
    "peg_string_tuning": (["musical_string","pin_fastener"], "tuning peg", "noun", "The peg Iago threatens to turn down to spoil the couple's musical accord."),
    "cod_bearded_fish": (["beard","fish"], "cod", "noun", "The cod with its chin barbel. Iago compares the head of this fish and a salmon's tail."),
    "frieze_rough_wool": (["rough","wool_material"], "frieze", "noun", "A coarse woolen cloth. Iago likens extracting an invention from his head to pulling birdlime from its fibers."),
    "clyster_pipe": (["kjv_bowels","pipe"], "clyster pipe", "noun", "A tube for administering an enema, Iago's malicious wish as Cassio repeatedly kisses his fingers."),
    "bear_star_group": (["drama_native_bear_animal","star"], "Bear", "proper", "The stellar Bear in the storm scene. The name follows the speaker, who does not specify Great or Little."),
    "mortise_timber_socket": (["wood","kjv_socket"], "mortise", "noun", "The socket joining the ship's oak timbers, imagined under the weight of mountainous water."),
    "guinea_hen_insult": (["spotted","hen"], "guinea hen", "noun", "The speckled fowl in Iago's insult about living or dying for a woman. His sexual slur belongs to him."),
    "lettuce_garden_leaf": (["milk","leaf"], "lettuce", "noun", "The garden plant with milky sap. Iago sets sowing it beside planting nettles."),
    "thyme_garden_herb": (["low","fragrant","herb"], "thyme", "noun", "The low, fragrant herb Iago would pull out of his garden. The supplied line reads thyme."),
    "carob_sweet_pod": (["sweet","pod_shell"], "carob pod", "noun", "Sweet carob pods in the locusts comparison, a botanical reading beside the bitter gourd. The edible insect is an alternate interpretation."),
    "colocynth_bitter_gourd": (["bitter","kjv_gourd"], "colocynth", "noun", "The bitter gourd tasted in Iago's forecast of Othello's desires."),
    "snipe_marsh_bird": (["fen_marsh","beak","bird"], "snipe", "noun", "The long-billed marsh bird as Iago's dismissive characterization of Roderigo."),
    "anthropophagi_travellers_tale": (["person","flesh","eat"], "Anthropophagi", "proper", "The man-eaters in Othello's account of his travels. The descriptive people-name renders the Greek name with the same meaning."),
    "countercaster_reckoning": (["reckoning_counter","reckon"], "countercaster", "noun", "A reckoner using counting tokens. Iago sneers at the officer he sees as a book-trained calculator."),
    "sagittary_venice_place": (["kjv_archer"], "Sagittary", "proper", "The Archer, the named place in Venice to which Iago directs Brabantio's party. No building type is specified."),
    "venetian_citizen": (["venice_lagoon_city","person"], "Venetian", "noun", "A Venetian, named with the localized city and the native person word."),
    "gondolier_venice_boatman": (["gondola_boat","person"], "gondolier", "noun", "The boatman Roderigo alleges conducted Desdemona across Venice."),
    "carrack_trading_ship": (["trade","ship"], "carrack", "noun", "A large merchant sailing ship. Iago likens Othello's new marriage to the taking of such a prize on land."),
    "signiory_venetian_council": (["venice_lagoon_city","council"], "signiory", "noun", "The ruling Venetian body to which Othello has given military service."),
    "ottomite_dynastic_demonym": (["ottoman_dynastic_name","person"], "Ottomite", "noun", "A member of the Ottoman force named by the messenger, without declaring an individual's ancestry."),
}


def lexical_entries(language):
    places = {"rhodes_eastern_island", "naples_musicians_city", "pontic_sea_water", "propontic_sea_water",
              "palestine_pilgrimage_land", "mauritania_iago_destination"}
    entries, glosses = build_entries(language, NAMES, SENSES, places)
    entries["moor_source_ethnonym"]["origin"] = "Localized historical people-name. Othello's birthplace remains unspecified."
    entries["ottoman_dynastic_name"]["origin"] = "Localized historical dynasty name used in the fleet reports."
    return entries, glosses


def prepare():
    add_source_entries("othello", "much-ado-about-nothing", lexical_entries,
        "The ensign, lieutenant and general have distinct titles. Iago's allegations and his animal insults remain attributed to their speakers. The Moor is an ethnonym; the Sagittary is a named meeting place.")


if __name__ == "__main__":
    prepare()
