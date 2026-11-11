"""The induction company, the two Paduan sisters and the disguised suitors."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "christopher_sly_given": ("kristofor", "Christopher", "The tinker's given name in the induction."),
    "christophero_sly_claim": ("kristoforo", "Christophero", "Sly's expanded form of his own given name when he wakes."),
    "richard_sly_conqueror": ("ritchard", "Richard", "Sly names Richard as the Conqueror in his claim of descent."),
    "jeronimy_sly_saint": ("jeronimi", "Jeronimy", "Sly invokes Saint Jeronimy in a phrase recalling Hieronimo in The Spanish Tragedy."),
    "clowder_sly_hound": ("klauder", "Clowder", "The hound to be coupled with the deep-voiced female hound."),
    "soto_player_part": ("soto", "Soto", "The name offered by the second player in recollection of the farmer's eldest son."),
    "bartholomew_induction_page": ("bartolomeu", "Bartholomew", "The lord's page, who performs the part of Sly's wife."),
    "burton_heath_sly_home": ("burton", "Burton", "Burton Heath, home of old Sly."),
    "wincot_sly_village": ("winkot", "Wincot", "Home of Marian Hacket, the alewife who knows Sly's debt."),
    "marian_hacket_alewife": ("maryan", "Marian", "The alewife whom Sly calls to witness his identity."),
    "hacket_wincot_name": ("haket", "Hacket", "Surname shared by Marian and Cicely in the induction."),
    "cicely_hacket_servant": ("siseli", "Cicely", "The maid Sly identifies in the induction. Distinct from Marian the alewife."),
    "stephen_sly_acquaintance": ("stefen", "Stephen", "Stephen Sly among the names the servant tries to discredit."),
    "john_naps_greete": ("jon", "John", "Old John Naps of Greete in the servant's list."),
    "naps_greete_surname": ("naps", "Naps", "Surname of old John, associated with Greete."),
    "greete_naps_village": ("grit", "Greete", "Place associated with John Naps."),
    "peter_turph_acquaintance": ("peter", "Peter", "Given name of Peter Turph in the servant's list."),
    "turph_peter_surname": ("turf", "Turph", "Surname of Peter in the list of supposed acquaintances."),
    "henry_pimpernell_acquaintance": ("henri", "Henry", "The Henry of Sly's acquaintance named beside Peter Turph."),
    "pimpernell_henry_surname": ("pimpernel", "Pimpernell", "Surname of Henry in the induction."),
    "semiramis_assyrian_queen": ("semiramis", "Semiramis", "The queen whose luxurious bed the lord invokes to tempt Sly."),
    "io_painted_maiden": ("iyo", "Io", "The mythological maiden in the painting offered to Sly."),
    "baptista_minola_father": ("baptista", "Baptista", "Paduan father of Katherine and Bianca."),
    "minola_paduan_family": ("minola", "Minola", "Surname of the Paduan household."),
    "katherine_minola_daughter": ("katerin", "Katherine", "Baptista's elder daughter."),
    "kate_minola_familiar": ("ket", "Kate", "The short form of Katherine's name in Petruchio's courtship."),
    "bianca_minola_daughter": ("byanka", "Bianca", "Baptista's younger daughter, distinct from Cassio's companion."),
    "petruchio_verona_suitor": ("petrutcho", "Petruchio", "Veronese suitor and then husband of Katherine."),
    "gremio_bianca_suitor": ("gremyo", "Gremio", "The older suitor for Bianca. Not Petruchio's servant Grumio."),
    "grumio_petruchio_servant": ("grumyo", "Grumio", "Petruchio's servant. Distinct from Gremio."),
    "hortensio_bianca_suitor": ("ortensyo", "Hortensio", "The suitor who adopts a music teacher's identity."),
    "litio_hortensio_alias": ("lityo", "Litio", "Hortensio's assumed name as a music teacher."),
    "lucentio_bianca_suitor": ("luchentyo", "Lucentio", "Bianca's suitor from Pisa who exchanges roles with his servant."),
    "cambio_lucentio_alias": ("kambyo", "Cambio", "Lucentio's assumed identity as a tutor."),
    "vincentio_lucentio_father": ("vinchentyo", "Vincentio", "Lucentio's father, later impersonated by a merchant."),
    "tranio_lucentio_servant": ("tranyo", "Tranio", "Lucentio's servant, who impersonates his master."),
    "biondello_lucentio_servant": ("byondelo", "Biondello", "Lucentio's other servant."),
    "alice_sly_example": ("alis", "Alice", "Sly guesses that Madam might need a given name, first trying Alice."),
    "joan_sly_example": ("jon", "Joan", "Sly's second proposed name to put before Madam."),
    "pisa_lucentio_birthplace": ("piza", "Pisa", "Lucentio's birthplace, distinct from Florence where he grew up."),
    "lombardy_lucentio_destination": ("lombardi", "Lombardy", "Lucentio calls the region the garden of Italy."),
    "bentivolii_vincentio_family": ("bentivolyi", "Bentivolii", "The family from which Vincentio descends."),
    "aristotle_philosopher": ("aristotel", "Aristotle", "Philosopher whose counsels of moderation Tranio contrasts with Ovid."),
    "anna_dido_sister": ("ana", "Anna", "Dido's sister, cited as a trusted confidante in Lucentio's appeal to Tranio."),
    "agenor_europa_father": ("agenor", "Agenor", "Father of Europa in Lucentio's comparison with Bianca."),
    "anne_sly_invoked_saint": ("an", "Anne", "Saint Anne, invoked by Sly when he is caught nodding during the play."),
    "antonio_petruchio_father": ("antonyo", "Antonio", "Petruchio's deceased father in Verona."),
    "florentius_gower_knight": ("florentsyo", "Florentius", "The knight whose bride Petruchio invokes in describing his willingness to marry."),
    "socrates_athenian": ("sokrates", "Socrates", "Philosopher named in Petruchio's comparison of ill-tempered wives."),
    "xanthippe_socrates_wife": ("ksantipe", "Xanthippe", "The wife whom Petruchio names with Socrates."),
    "adriatic_sea": ("adriyatik", "Adriatic", "The sea in Petruchio's image of an unruly bride."),
    "katherina_minola_form": ("katerina", "Katherina", "The longer form of Katherine used by Hortensio and several others."),
    "grissel_patient_wife": ("grisel", "Grissel", "Patient Grissel, the exemplary wife with whom Petruchio compares Katherine."),
    "sigeian_trojan_land": ("sigeya", "Sigeian", "The Trojan land named in the Latin lines Lucentio reads with Bianca."),
    "aeacides_ajax_patronymic": ("eyakides", "Aeacides", "Name derived from Aeacus, explicitly attributed to Ajax by Lucentio."),
    "jamy_biondello_saint": ("jami", "Jamy", "Saint Jamy in Biondello's wager. This speech supplies no biographical identification."),
    "curtis_petruchio_servant": ("kurtis", "Curtis", "The servant sent to ready the household and the fire."),
    "nathaniel_petruchio_servant": ("naÕaniel", "Nathaniel", "Servant called to greet Grumio and the wedding couple."),
    "joseph_petruchio_servant": ("yßsef", "Joseph", "Servant named and speaking in Petruchio's household."),
    "nicholas_petruchio_servant": ("nikolas", "Nicholas", "Servant who hails his fellow Grumio."),
    "phillip_petruchio_servant": ("filip", "Phillip", "Petruchio's servant, whose name the local witness spells with double l."),
    "walter_petruchio_servant": ("wolter", "Walter", "Servant whose dagger is being fitted for a sheath."),
    "gregory_petruchio_servant": ("gregori", "Gregory", "Servant Petruchio calls by name at the door."),
    "gabriel_petruchio_servant": ("gabriel", "Gabriel", "Servant whose pumps lack the expected ornament."),
    "peter_petruchio_servant": ("peter", "Peter", "Petruchio's servant, who identifies himself as the one who brought the meal."),
    "adam_petruchio_servant": ("adam", "Adam", "One of the servants whom Grumio declares adequately dressed."),
    "rafe_petruchio_servant": ("reif", "Rafe", "A well-dressed servant included with Adam and Gregory."),
    "troilus_petruchio_spaniel": ("troilus", "Troilus", "Petruchio's spaniel, distinguished from the Trojan man for whom he is named."),
    "ferdinand_petruchio_cousin": ("ferdinand", "Ferdinand", "Petruchio's cousin, whom a servant is sent to summon."),
    "tripoli_merchant_destination": ("tripoli", "Tripoli", "Destination after Rome in the merchant's proposed journey. The source does not identify a modern port."),
    "marcellus_gremio_anchorage": ("marselus", "Marcellus", "The name in Gremio's Marcellus' road, where his argosy lies at anchor. The local source spelling is retained."),
}

SENSES = {
    "sly_tinker_family": (["cunning"], "Sly", "proper", "The tinker's speaking surname is the native word for cunning."),
    "merriman_sly_hound": (["merry", "man"], "Merriman", "proper", "The exhausted hunting dog's name."),
    "silver_sly_hound": (["silver"], "Silver", "proper", "The hound who recovers the scent at the hedge corner."),
    "bellman_sly_hound": (["bell", "man"], "Bellman", "proper", "The huntsman's favourite dog in the comparison with Silver."),
    "echo_sly_hound": (["echo"], "Echo", "proper", "A hound praised for all but his speed. Distinct from the nymph."),
    "borough_sly_jurisdiction": (["town"], "borough", "noun", "Unit of local authority in Sly's string of mock offices."),
    "rosewater_hand_wash": (["rose", "water"], "rosewater", "noun", "Perfumed water offered to the supposed nobleman."),
    "ewer_hand_wash": (["water", "pour", "vessel"], "ewer", "noun", "A pouring vessel used with a washbasin."),
    "diaper_hand_towel": (["linen", "hand"], "linen towel", "noun", "The patterned towel brought by the third attendant to dry hands."),
    "quart_sealed_vessel": (["gallon_wine", "quarter"], "quart", "noun", "A vessel of a quarter gallon. Sly wants the tavern measure certified; no modern volume conversion is assumed."),
    "sly_headborough_officer": (["town", "guard"], "headborough", "noun", "The local officer whom the hostess goes to fetch. Shares the office word used for Verges."),
    "pantaloon_comic_elder": (["old", "actor"], "pantaloon", "noun", "Gremio is marked as a stock comic elderly man at his entrance."),
    "mathematics_number_study": (["number_abstract", "study"], "mathematics", "noun", "The numerical discipline named in Tranio's advice on studies."),
    "metaphysics_first_causes": (["cause", "nature", "study"], "metaphysics", "noun", "Study of fundamental causes and the nature of things."),
    "logic_argument_study": (["reason", "study"], "logic", "noun", "The discipline of reasoning and argument that Tranio recommends practising with acquaintances."),
    "pip_card_mark": (["playing_card", "mark"], "card pip", "noun", "A single card mark above the game total in Grumio's two-and-thirty joke."),
    "aglet_baby_lace_figure": (["clothing_lace", "image"], "lace-tip figure", "noun", "A small figure fashioned at the tip of a lace, paired with a puppet in Grumio's mock list."),
    "chestnut_edible_nut": (["kjv_chestnut", "seed"], "chestnut", "noun", "The nut which bursts in a farmer's fire in Petruchio's comparison."),
    "galleass_oared_warship": (["war", "galley_ship"], "galleass", "noun", "A large armed oared ship listed separately from a galley and an argosy."),
    "cape_bed_valance": (["bed", "curtain"], "valance", "noun", "A short ornamental hanging among Gremio's furnishings."),
    "hazelnut_hazel_seed": (["kjv_hazel", "seed"], "hazelnut", "noun", "The nuts whose brown hue and kernels Petruchio compares with Katherine."),
    "fowl_comb_crest": (["cock_fowl", "crest"], "cock's comb", "noun", "The comb on a fowl's head, at once an imagined crest and an allusion to the fool's cap."),
    "gamut_music_scale": (["music", "step"], "gamut", "noun", "The ordered musical scale Hortensio turns into an amorous lesson."),
    "clef_pitch_sign": (["music", "mark"], "clef", "noun", "A sign used to identify a musical pitch in the written lesson."),
    "sounded_musical_note": (["music", "sound"], "note", "noun", "An individual musical sound, as distinct from a written memorandum."),
    "bass_music_part": (["low", "sound"], "bass", "noun", "The low musical part that Lucentio says is out of tune."),
    "glanders_horse": (["nostril", "sickness"], "glanders", "noun", "The first named equine malady in Biondello's account, affecting the nose and jaws."),
    "lampass_horse": (["palate", "swelling_body"], "lampass", "noun", "The swelling of the horse's palate in Biondello's catalogue."),
    "farcy_horse_fashions": (["sore_wound", "swell"], "fashions", "noun", "The horse disease called fashions or farcy in Biondello's report."),
    "windgall_horse": (["leg", "swelling_body"], "windgall", "noun", "The soft swelling of a horse's leg in this catalogue, distinguished from the spavin."),
    "yellows_horse": (["yellow", "sickness"], "yellows", "noun", "The yellows, a jaundice which discolours the horse."),
    "fives_horse": (["jaw", "swelling_body"], "fives", "noun", "The fives or strangles affecting glands near the horse's jaws. The name carries no numerical assertion."),
    "bots_horse": (["stomach", "worm"], "bots", "noun", "The horse's internal parasites in Biondello's catalogue."),
    "muscatel_wedding_wine": (["sweet", "grape", "wine"], "muscatel", "noun", "The sweet wine Petruchio drinks at the wedding."),
    "sugarsop_petruchio_servant": (["sugar_native", "soak"], "Sugarsop", "proper", "The servant's food-name in Grumio's summons, formed from sugar and soak."),
    "fustian_household_cloth": (["rough", "weave", "cloth"], "fustian", "noun", "Coarse woven cloth worn by the household's servingmen."),
    "haberdasher_cap_seller": (["hat", "trader"], "haberdasher", "noun", "The tradesman who brings the commissioned cap."),
    "tripe_stomach_meat": (["stomach", "meat"], "tripe", "noun", "Edible stomach lining, which Grumio offers to broil."),
    "porringer_food_bowl": (["porridge", "vessel"], "porringer", "noun", "A small dish for food whose shape Petruchio sees in the cap."),
    "walnut_nut": (["shell", "nut"], "walnut", "noun", "The hard-shelled nut in Petruchio's taunt about the cap. The shell root already carries the hard exterior sense."),
    "cockle_sea_shell": (["sea", "shell"], "cockle", "noun", "A small ribbed shellfish, distinct from the weed."),
    "cape_garment_collar": (["shoulder", "cloth"], "cape", "noun", "The small cape or collar listed in the tailor's note."),
    "long_lane_road": (["long", "way"], "Long-lane", "proper", "The named lane at whose end the party intends to mount."),
    "pegasus_genoa_inn": (["pegasus_steed", "house"], "Pegasus", "proper", "The inn of the Pegasus in Genoa, named by the visiting merchant."),
    "parsley_kitchen_herb": (["cut", "leaf", "herb"], "parsley", "noun", "Culinary parsley for stuffing a rabbit, named for its divided leaf."),
}


def lexical_entries(language):
    entries, glosses = build_entries(language, NAMES, SENSES, {"burton_heath_sly_home", "greete_naps_village", "wincot_sly_village",
        "pisa_lucentio_birthplace", "lombardy_lucentio_destination"})
    if language.lexicon["comedy"]["form"] != "pifaln":
        raise ValueError("Unrecognized native base for Sly's comonty")
    key = "comonty_sly_error"
    entries[key] = dict(form="piflan", roman=language.reading("piflan"), pos="noun",
        meaning="Sly mispronounces comedy. The native form transposes two sounds in the play word.",
        semanticId="lex." + key, derivationKeys=["comedy"], historicalForms=[],
        usageScope="editorial-exception", status="authored", origin="Sly's question to the page in induction scene 2")
    glosses[key] = "comedy (as spoken)"
    if language.lexicon["abuse"]["form"] != "murlametåv":
        raise ValueError("Unrecognized base for Grumio's rebused")
    key = "rebused_grumio_slip"
    entries[key] = dict(form="murmaletåv", roman=language.reading("murmaletåv"), pos="verb",
        meaning="Grumio mispronounces the ordinary verb for abusing someone.",
        semanticId="lex." + key, derivationKeys=["abuse"], historicalForms=[],
        usageScope="editorial-exception", status="authored", origin="Grumio's question about a supposed insult")
    glosses[key] = "abuse (as spoken)"
    if language.lexicon["merchant"]["form"] != "kamizãÑtsßlum":
        raise ValueError("Unrecognized native base for Biondello's marcantant")
    key = "marcantant_biondello_error"
    entries[key] = dict(form="kamizãÑzãÑtsßlum", roman=language.reading("kamizãÑzãÑtsßlum"), pos="noun",
        meaning="Biondello repeats a syllable in the ordinary merchant word while guessing what the newcomer does.",
        semanticId="lex." + key, derivationKeys=["merchant"], historicalForms=[],
        usageScope="editorial-exception", status="authored", origin="Biondello's distortion of the occupational term")
    glosses[key] = "merchant (as spoken)"
    key = "sol_solmization_syllable"
    entries[key] = dict(form="sßl", roman=language.reading("sßl"), pos="citation",
        meaning="The sung syllable sol in Petruchio's threat and Hortensio's lesson.",
        semanticId="lex." + key, historicalForms=[], status="authored",
        usageScope="editorial-exception", origin="Source-specific musical syllable paired with the established fa.")
    glosses[key] = "sol"
    for key, form, label in (("mi_solmization_syllable", "mi", "mi"), ("ut_solmization_syllable", "ut", "ut"),
                             ("la_solmization_syllable", "lÅ", "la"), ("school_source_letter_c", "si", "letter C")):
        entries[key] = dict(form=form, roman=language.reading(form), pos="citation",
            meaning=f"The source's {label} in Hortensio's alphabetic music lesson.",
            semanticId="lex." + key, status="authored", usageScope="editorial-exception", historicalForms=[],
            origin="A named letter or sung syllable under discussion in The Taming of the Shrew 3.1.")
        glosses[key] = label
    return entries, glosses


def prepare():
    add_source_entries("the-taming-of-the-shrew", "the-merry-wives-of-windsor", lexical_entries,
        "Keep the lord's induction company distinct from the players and their Paduan roles. Retain both of Sly's given-name forms, his Richard and the identities assumed by the disguised suitors.",
        inherited_glosses={"kjv_basin": "basin", "kjv_husbandman": "farmer", "kjv_pitcher": "pitcher",
                           "apollo": "Apollo", "florence": "Florence", "italy": "Italy", "kjv_pool": "pool",
                           "kjv_moth_job": "moth", "kjv_sop_john": "sop", "kjv_bolster": "bolster",
                           "kjv_censer": "censer", "kjv_gutter": "gutter", "kjv_luke_physician_colossians": "Luke",
                           "native_place_bergamo": "Bergamo"})


if __name__ == "__main__":
    prepare()
