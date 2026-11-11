"""Households, aliases, disputed offices and heraldic language in Windsor."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "leda_jupiters_beloved": ("leda", "Leda", "The woman in Falstaff's recollection of Jupiter in the form of a swan."),
    "eton_windsor_town": ("eton", "Eton", "The town of Slender's intended wedding and the point beyond which Bardolph is thrown off a horse."),
    "reading_berkshire_town": ("reding", "Readings", "The first of the towns Evans names when warning the Host about horse thieves. Source label preserves Readings."),
    "maidenhead_berkshire_town": ("medenhed", "Maidenhead", "The second town whose hosts Evans says lost horses and money."),
    "colnbrook_berkshire_town": ("kolnbruk", "Colnbrook", "The third town named in Evans's warning."),
    "faustus_stage_doctor": ("faustus", "Faustus", "The stage doctor in Bardolph's comparison to three Doctor Faustuses."),
    "brentford_windsor_disguise": ("brentford", "Brentford", "Place associated with the maid's aunt whose clothes disguise Falstaff."),
    "pratt_maid_aunt": ("prat", "Pratt", "The maid's aunt called Mother Pratt; Falstaff wears her clothes when the wives give him her name."),
    "herne_windsor_hunter": ("hern", "Herne", "The hunter in the Windsor oak legend, later impersonated by Falstaff."),
    "ginny_quickly_mishearing": ("jini", "Ginny", "The woman Quickly imagines when she mishears genitive case."),
    "datchet_meadow_place": ("datchet", "Datchet", "The place in the Thames-side meadow name; the basket is ordered to the laundry workers there."),
    "bucklersbury_herb_street": ("buklersberi", "Bucklersbury", "The London street whose druggists' herbs are evoked by Falstaff's comparison."),
    "john_mock_address": ("jon", "John", "Generic personal name in the taunt John ape applied to Evans. Distinct from Rugby, Falstaff and Ford's servant."),
    "hippocrates_physician": ("hipokrates", "Hippocrates", "The medical authority whom Evans calls Hibbocrates alongside Galen."),
    "gallia_host_name": ("galya", "Gallia", "The Host's old name for France, used as a direct address to Caius."),
    "gaul_host_epithet": ("gol", "Gaul", "The Host's jokingly paired address to Evans after Gallia, followed explicitly by French and Welsh. It does not relocate Evans."),
    "castalion_host_epithet": ("kastalyon", "Castalion", "The Host's extravagant title for Caius. Its reference is uncertain between Castile and Castalia."),
    "bridget_windsor_fan_owner": ("brijet", "Bridget", "Mistress Bridget, whose fan handle was lost. Distinct from the other dramatic Bridgets."),
    "acteon_hunted_stag": ("akteon", "Acteon", "The hunter turned into a stag and pursued by his hounds in Pistol's warning to Ford."),
    "cathay_page_insult": ("katay", "Cathay", "Invoked in Page's Cataian insult for Nym, a term of distrust, not an established birthplace for him."),
    "nan_anne_page": ("nan", "Nan", "Quickly's familiar form of Anne Page's name, also used in the choice of a husband."),
    "anne_page_windsor": ("an", "Anne", "The Pages' daughter. Slender, Caius and Fenton seek her hand."),
    "william_page_son": ("wilyam", "William", "The Pages' school-age son, whom Sir Hugh examines."),
    "thomas_page_given": ("tomas", "Thomas", "Sir Hugh calls Anne's father Thomas in the opening scene. Keep this local form alongside the later George."),
    "george_page_given": ("jorj", "George", "Given name used of Master Page later in the play; do not harmonize the opening Thomas."),
    "margaret_page_wife": ("margaret", "Margaret", "Mistress Page's personal name, with Meg as a familiar form."),
    "meg_page_familiar": ("meg", "Meg", "Familiar address to Margaret Page."),
    "alice_ford_wife": ("alis", "Alice", "Mistress Ford, recipient of one of Falstaff's matching letters."),
    "frank_ford_given": ("frank", "Frank", "Familiar given name for Master Ford."),
    "abraham_slender_given": ("abram", "Abraham", "Shallow's young kinsman, addressed by Sir Hugh. Distinct from the biblical patriarch."),
    "hugh_evans_parson": ("hyu", "Hugh", "Given name of the Welsh parson and teacher Sir Hugh Evans."),
    "evans_parson_surname": ("evans", "Evans", "Surname of the Windsor parson."),
    "caius_windsor_doctor": ("kayos", "Caius", "The French doctor who courts Anne Page, distinct from Kent's borrowed name."),
    "quickly_windsor_housekeeper": ("kwikli", "Quickly", "The doctor's housekeeper. Uses the established dramatic pronunciation; the Windsor speeches identify her by her employment here."),
    "fenton_anne_suitor": ("fenton", "Fenton", "The young gentleman loved by Anne Page."),
    "robin_falstaff_page": ("robin", "Robin", "Falstaff's page in Windsor. Distinct from Robin Goodfellow."),
    "rugby_caius_servant": ("rugbi", "Rugby", "Doctor Caius's servant, called both John and Jack."),
    "john_rugby_given": ("jon", "John", "Rugby's given name. Distinct from Master Ford's servant John."),
    "jack_rugby_familiar": ("jak", "Jack", "Caius's familiar name for John Rugby."),
    "john_ford_servant": ("jon", "John", "One of the two servants called to carry the basket in Ford's household."),
    "robert_ford_servant": ("robert", "Robert", "The other servant who carries the basket with John."),
    "peter_simple_given": ("peter", "Peter", "Slender's servant's given name, distinct from the apostle and from Juliet's servant."),
    "cotsall_course": ("kotsal", "Cotsall", "The grounds on which Page's greyhound is said to have been outrun."),
    "banbury_cheese_town": ("banberi", "Banbury", "The town whose thin cheese Bardolph invokes in ridiculing Slender."),
    "mephostophilus_fiend": ("mefostofilus", "Mephostophilus", "The stage devil whose name Pistol throws at Slender. Keeps the supplied form of the name."),
    "edward_shuffle_coin_king": ("edward", "Edward", "The king named on the silver coins used for shovel-board. The passage supplies no regnal number."),
    "yed_miller_coin_seller": ("yed", "Yed", "The man from whom Slender says he bought his two shovel-board pieces."),
    "alice_shortcake_given": ("alis", "Alice", "The woman who borrowed Slender's book, distinct from Mistress Ford."),
    "sackerson_bear": ("sakerson", "Sackerson", "The named bear whom Slender boasts of seeing loose twenty times."),
    "pandarus_trojan_go_between": ("pandarus", "Pandarus", "The Trojan go-between invoked when Pistol refuses to deliver Falstaff's love letters."),
    "guiana_gold_region": ("guyana", "Guiana", "The region Falstaff invokes in his fantasy of drawing gold from Mistress Page."),
}

SENSES = {
    "odd_numerical_parity": (["pair", "remain"], "odd in number", "modifier", "Counting in pairs leaves a single unpaired member. Falstaff twice attributes luck or divine force to this numerical property."),
    "bead_fairy_player": (["bead"], "Bead", "proper", "A fairy-play name called by Evans. The human actor is not identified."),
    "cricket_fairy_player": (["cricket_singer"], "Cricket", "proper", "The named fairy ordered to inspect the chimneys, distinct from the literal singing insect."),
    "pistol_hobgoblin_role": (["hobgoblin"], "Hobgoblin", "proper", "Pistol's assumed part as the fairy crier in the Windsor forest play."),
    "eryngo_candied_root": (["sea", "sweet", "root"], "eryngo root", "noun", "Candied sea-holly root. Falstaff imagines a snow of these supposed aphrodisiacs."),
    "potato_sweet_root": (["sweet", "earth", "root"], "sweet potato", "noun", "The sweet potato in Falstaff's wish for a rain of provoking foods."),
    "windsor_deanery": (["chief", "priest", "house"], "deanery", "noun", "The dean's residence at which Mrs Page intends Caius to marry Anne."),
    "mussel_shellfish": (["dark", "shell"], "mussel", "noun", "The dark-shelled edible mollusc in Falstaff's mussel-shell insult to Simple."),
    "school_case_inflection": (["word", "form"], "grammatical case", "noun", "A word's inflection for case in the Latin exercise, distinct from Quickly's bawdy use of case."),
    "school_pronoun": (["name", "represent"], "pronoun", "noun", "A word standing in place of a name. The exercise borrows its articles from a demonstrative pronoun."),
    "school_nominative": (["name", "form"], "nominative", "noun", "The case named first in William's demonstrative paradigm."),
    "school_accusative": (["object", "form"], "accusative", "noun", "The case taught by the hunc, hanc, hoc series as mangled in Evans's speech."),
    "school_genitive": (["owner", "form"], "genitive", "noun", "The possessive case. Keep the singular huius and plural citation separate from Quickly's misheard name."),
    "school_vocative": (["call", "form"], "vocative", "noun", "Case of direct address. This demonstrative has no separate vocative form in the exercise."),
    "school_word_gender": (["word", "kind"], "grammatical gender", "noun", "The grammatical gender of a Latin word, distinguished from grammatical number."),
    "pepper_spice": (["sharp", "berry"], "pepper", "noun", "Peppercorn spice in the little box where Ford imagines Falstaff could not possibly hide."),
    "turnip_root": (["round", "root"], "turnip", "noun", "Round root vegetable hurled like a bowls ball in Anne's imagined death."),
    "bilbo_flexible_sword": (["bend", "blade"], "bilbo blade", "noun", "A flexible sword that can be bent hilt to point, unlike the restraint called bilboes."),
    "peck_dry_vessel": (["dry", "measure", "vessel"], "peck vessel", "noun", "A peck-capacity vessel, two dry gallons. Falstaff compares his cramped circumference with its rim. Its precise physical diameter is not given."),
    "pumpion_round_gourd": (["round", "kjv_melon"], "pumpkin", "noun", "The large, watery garden fruit in Mistress Ford's insult for Falstaff; distinct from Costard's mangling of Pompey's name."),
    "buck_basket_laundry": (["wash", "kjv_basket"], "buck-basket", "noun", "Laundry basket into which Falstaff climbs. The audible buck/deer pun belongs to the subsequent exchange with Ford."),
    "jack_lent_effigy": (["lenten_fast", "figure_sign"], "Jack-a-Lent", "noun", "A Lenten effigy used as a target. Mistress Page applies the little figure's name to Robin."),
    "hooped_farthingale": (["hoop_binding", "kjv_skirt_garment"], "farthingale", "noun", "The hooped petticoat that Falstaff pictures framing Mistress Ford's gait."),
    "counter_debtors_prison": (["debt", "prison"], "Counter", "proper", "The London prison for debtors whose gate Falstaff detests."),
    "pettyward_windsor": (["little", "region"], "Petty-ward", "proper", "The lesser ward named among the areas searched by Simple."),
    "parkward_windsor": (["park", "region"], "Park-ward", "proper", "The park ward among the areas searched by Simple."),
    "madrigal_part_song": (["voice", "harmony", "song"], "madrigal", "noun", "The birds' part-song in the pastoral refrain Evans repeatedly sings."),
    "frogmore_windsor_fields": (["kjv_frog", "bog"], "Frogmore", "proper", "The wet ground near Windsor where the duellists are brought together. The source name is rendered with the native frog and bog roots."),
    "mockwater_physician_taunt": (["mock", "water"], "mockwater", "noun", "The Host's mocking name for a doctor inspecting urine, which he falsely glosses as valour to Caius."),
    "clapperclaw_beat": (["beat", "claw"], "clapper-claw", "verb", "The Host threatens a drubbing, then tells Caius that the word means to make amends. Its meaning stays constant through the false gloss."),
    "wittol_assenting_husband": (["consent", "cuckold"], "wittol", "noun", "A husband who knowingly accepts his wife's infidelity. Contrasts with the surrounding repetitions of cuckold."),
    "pickt_hatch_district": (["point", "gate"], "Pickt-hatch", "proper", "The London district in Falstaff's dismissive send-off to Pistol; rendered as a pointed gate."),
    "canaries_quickly_error": (["canary_dance"], "canaries", "noun", "Quickly uses canary and canaries for the fluster Falstaff has caused. The mistaken noun preserves the possible dance association, without making the wife actually dance."),
    "alligant_quickly_error": (["all", "grace_elegance"], "all-elegant", "modifier", "Quickly's grand-sounding mistake for elegant or eloquent in her description of courtiers."),
    "greensleeves_tune": (["green", "sleeve"], "Greensleeves", "proper", "The secular melody set against the Hundredth Psalm; translated as a title from its colour and garment."),
    "ringwood_hunting_hound": (["sound", "wood"], "Ringwood", "proper", "The named hound at the heels of the horned hunter in Pistol's warning to Ford. The native name evokes a ringing wood."),
    "posset_hot_milk": (["warm", "milk", "drink"], "posset", "noun", "A warm milk-and-liquor drink promised by the fire. The source specifies no recipe."),
    "seacoal_fire_fuel": (["sea", "coal"], "sea coal", "noun", "Coal brought by sea to fuel the household fire, distinct from a glowing ember or the watchman's surname."),
    "phlegmatic_quickly_error": (["cold", "dull"], "phlegmatic", "modifier", "Quickly misnames the doctor's heated temper with the cold, slow humour. She wants him to calm down."),
    "allicholy_quickly_error": (["all", "sorrow"], "allicholy", "noun", "Quickly's blunder for melancholy, rendered as all-sorrow. Here she means Anne's fits of brooding."),
    "slender_shallow_kinsman": (["thin"], "Slender", "proper", "The telling surname of Shallow's young kinsman."),
    "simple_slender_servant": (["simple"], "Simple", "proper", "The telling surname of Slender's servant Peter."),
    "page_windsor_family": (["page"], "Page", "proper", "The family surname. Speech headings and titles distinguish the father, mother and children from a page serving a gentleman."),
    "ford_windsor_family": (["ford"], "Ford", "proper", "The family name formed from a water crossing; helps maintain the stream-name jokes about Ford's assumed name."),
    "brook_ford_alias": (["brook"], "Brook", "proper", "Ford's assumed name when he approaches Falstaff. Retains the stream image."),
    "garter_windsor_inn": (["garter"], "Garter", "proper", "The inn whose host takes part in the Windsor intrigues. Named for its sign."),
    "star_chamber_tribunal": (["star", "room"], "Star Chamber", "proper", "Royal tribunal to which Shallow threatens to take his complaint."),
    "windsor_quorum_blunder": (["gather", "enough"], "Coram", "noun", "Slender's mangled quorum, referring to qualifications of a justice. The native builds a mock title from enough for a gathering."),
    "windsor_rollkeeper_blunder": (["guard", "scroll"], "Custalorum", "noun", "Shallow's abbreviated keeper-of-the-rolls style, echoed and mangled by Slender."),
    "windsor_rolls_blunder": (["scroll", "roll"], "Ratolorum", "noun", "Slender's comic echo of the roll word as a separate office. The paired native titles repeat the scroll root."),
    "armigero_esquire_style": (["shield", "carry"], "Armigero", "noun", "The Latin legal style of an armiger. Rendered as the mock grand style shield-bearer in Slender's twofold utterance."),
    "miller_yed_surname": (["mill_grinding", "keeper"], "Miller", "proper", "Yed's occupational surname for the seller of Slender's game coins."),
    "cabbage_leaf_head": (["leaf", "head"], "cabbage", "noun", "The headed vegetable Falstaff understands when Evans says worts for words."),
    "shovelboard_game_coin": (["plank_board", "silver_coin"], "shovel-board piece", "noun", "A silver piece slid across a board in the game. Slender describes two Edward pieces he bought above their face value."),
    "shortcake_book_borrower": (["break", "cake"], "Shortcake", "proper", "Alice's edible surname, a cake which breaks easily. Distinct from the Messina watchman's Oatcake."),
    "michaelmas_feast": (["kjv_michael_jude_archangel", "feast"], "Michaelmas", "noun", "Feast of the archangel Michael. Simple confuses its place in the calendar relative to Allhallowmas."),
    "pippin_dessert_apple": (["seed", "apple"], "pippin", "noun", "An eating apple served with cheese at the end of dinner. Distinct from King Pippin."),
    "pheazar_host_title": (["great", "imperial"], "Pheazar", "noun", "The Host's playful third title for Falstaff. The etymology is uncertain; the native enlarges the imperial title rather than assigning a specific foreign office."),
    "spigot_cask_plug": (["wood", "stop"], "spigot", "noun", "The wooden plug for drawing a drink from a cask. Pistol mocks Bardolph for agreeing to handle it."),
    "burning_glass_lens": (["sun", "glass"], "burning glass", "noun", "A glass focusing the sunlight to scorch a surface. Falstaff compares a woman's gaze to it."),
    "gourd_false_die": (["hollow", "dice"], "gourd die", "noun", "A false die called a gourd, distinguished from the fullam in Pistol's boast. The hollow image does not specify a weight or outcome."),
    "fullam_false_die": (["weight", "dice"], "fullam die", "noun", "A die loaded to cheat, paired with the gourd and with the high and low throws."),
}


# Latin forms are themselves the objects of the lesson. The surrounding
# dialogue and grammatical descriptions use native dramatic vocabulary.
SCHOOL_CITATIONS = {
    "pulcher": ("pulker", "pulcher", "Latin for fair. Quickly hears polecats."),
    "lapis": ("lapis", "lapis", "Latin for stone, rehearsed by teacher and pupil."),
    "hic": ("hik", "hic", "Masculine nominative singular of the demonstrative."),
    "haec": ("haek", "haec", "Feminine nominative singular of the demonstrative."),
    "hoc": ("hok", "hoc", "Neuter nominative singular of the demonstrative."),
    "hig": ("hig", "hig", "Evans's voiced rendition of hic."),
    "haeg": ("haeg", "haeg", "Evans's voiced rendition of haec."),
    "hog": ("hog", "hog (slip)", "Evans's voiced rendition of hoc, misheard as a pig."),
    "huius": ("huyus", "huius", "Genitive singular supplied by Evans."),
    "hinc": ("hink", "hinc (pupil)", "William's answer, where hunc would be expected."),
    "hung": ("hung", "hung (slip)", "Evans's classroom pronunciation of hunc."),
    "hang": ("hang", "hang (slip)", "Evans's classroom hanc, misheard as the verb hang."),
    "caret": ("karet", "caret", "Latin for it lacks. Quickly hears an edible root."),
    "horum": ("horum", "horum", "Masculine or neuter genitive plural, repeated around harum."),
    "harum": ("harum", "harum", "Feminine genitive plural, between the two horum forms."),
    "whorum": ("worum", "whorum (misheard)", "Quickly's bawdy version of the sound she hears."),
    "qui": ("kwi", "qui", "Masculine nominative singular of the relative pronoun."),
    "quae": ("kwae", "quae", "Feminine nominative singular of the relative pronoun."),
    "quod": ("kwod", "quod", "Neuter nominative singular of the relative pronoun."),
}


def lexical_entries(language):
    entries, glosses = build_entries(language, NAMES, SENSES, {
        "cotsall_course", "banbury_cheese_town", "guiana_gold_region", "cathay_page_insult",
        "gallia_host_name", "datchet_meadow_place", "bucklersbury_herb_street", "brentford_windsor_disguise",
        "eton_windsor_town", "reading_berkshire_town", "maidenhead_berkshire_town", "colnbrook_berkshire_town"})
    for term, (form, label, meaning) in SCHOOL_CITATIONS.items():
        key = "windsor_school_" + term
        entries[key] = dict(form=form, roman=language.reading(form), pos="citation", meaning=meaning,
            semanticId="lex." + key, origin="Source-language citation in William's Latin lesson",
            usageScope="editorial-exception", status="authored", historicalForms=[])
        glosses[key] = label
    for root, expected, slip in (("cheese", "melkor", "nelkor"), ("butter", "melam", "nelam")):
        if language.lexicon[root]["form"] != expected or not set(slip) <= language.letters:
            raise ValueError(f"Unexpected form for Evans's pronunciation of {root}")
        key = "evans_windsor_" + root
        entries[key] = dict(form=slip, roman=language.reading(slip), pos="noun",
            meaning=f"Evans's pronunciation of {root}, echoed by Falstaff.",
            derivationKeys=[root], semanticId="lex." + key, status="authored", historicalForms=[],
            origin="Native m/n substitution in the closing Windsor taunt.",
            usageScope="editorial-exception")
        glosses[key] = root + " (as spoken)"
    return entries, glosses


def prepare():
    add_source_entries("the-merry-wives-of-windsor", "the-merchant-of-venice", lexical_entries,
        "Reuse Falstaff, Shallow and their returning companions. Give the two households, their servants, and Ford's Brook alias separate identifiable roles. Preserve malapropisms and track the source's own name variations.",
        inherited_glosses={"kjv_legal_case": "legal case", "kjv_skirt_garment": "skirt", "kjv_resurrection": "resurrection",
                           "kjv_pot_scum": "scum", "kjv_godly": "godly", "native_place_england": "England",
                           "native_place_germany": "Germany", "kjv_treasury": "treasury", "caesar": "Caesar",
                           "troy": "Troy", "english": "English", "kjv_scour": "scour", "kjv_psalm": "psalm",
                           "kjv_coffer": "coffer", "galen": "Galen", "ethiop": "Ethiopian", "greece": "Greece",
                           "kjv_babylon": "Babylon", "kjv_eve": "Eve", "kjv_napkin_cloth": "napkin",
                           "native_place_netherlands": "Netherlands", "kjv_goliath": "Goliath",
                           "kjv_shuttle_weaving": "weaving shuttle", "jove": "Jove",
                           "kjv_emerald": "emerald", "kjv_sapphire": "sapphire",
                           "kjv_satan_job": "Satan", "kjv_job_sufferer": "Job",
                           "kjv_fornication": "fornication", "kjv_plumbline": "plumb line"})


if __name__ == "__main__":
    prepare()
