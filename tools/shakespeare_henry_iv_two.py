"""Source-specific names and senses for Henry IV, Part 2."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "bardolph_lord": ("bardolf", "Bardolph", "The rebel lord who brings Northumberland secondhand news, distinct from Falstaff's companion Bardolph."),
    "blunt_family": ("blunt", "Blunt", "The surname used in the plural in Lord Bardolph's false report that Douglas killed both Blunts."),
    "travers_retainer": ("traverz", "Travers", "Northumberland's servant sent out for news."),
    "morton_retainer": ("morton", "Morton", "Northumberland's retainer who saw the fall of Hotspur at Shrewsbury."),
    "john_umfrevile": ("jon", "John", "Sir John Umfrevile's given name in Travers's account."),
    "umfrevile_knight": ("umfrevil", "Umfrevile", "Sir John who first gave Travers glad news. The unidentified later horseman brings contrary news."),
    "chester_city": ("Ñester", "Chester", "City for which the unknown rider asks the way."),
    "pomfret_castle": ("pomfret", "Pomfret", "Castle where the deposed Richard's blood is figuratively scraped from the stones."),
    "dommelton_merchant": ("domelton", "Dommelton", "The merchant who refuses Falstaff and his companion Bardolph credit for satin."),
    "smithfield_market": ("smithfÝld", "Smithfield", "The London horse market to which the companion Bardolph goes."),
    "ursula_mistress": ("ursula", "Ursula", "The older woman to whom Falstaff sends a letter after making repeated promises of marriage."),
    "job_sufferer_falstaff": ("yob", "Yob", "The biblical sufferer whom Falstaff names when claiming poverty. The form follows the historical 285 witness for kjv_job_sufferer."),
    "thomas_mowbray": ("tomas", "Thomas", "The Earl Marshal's given name in the York council."),
    "mowbray_marshal": ("moubrei", "Mowbray", "The younger Mowbray, rebel Earl Marshal in York."),
    "hastings_rebel": ("heistingz", "Hastings", "The lord at York who assesses the rebel levies and the king's divided forces."),
    "gower_messenger": ("gauer", "Gower", "The messenger to the chief justice. A personal name distinct from the poet of Pericles."),
    "basingstoke_town": ("beizingstok", "Basingstoke", "The town where the messenger says the king lodged."),
    "keech_goodwife": ("kÝÑ", "Keech", "The butcher's wife named in Quickly's recollection of the marriage promise."),
    "lumbert_street": ("lumbert", "Lumbert", "Quickly's own form of the London street name. Her pronunciation is retained."),
    "doll_given": ("dol", "Doll", "Doll in the given name Doll Tearsheet."),
    "althea_page_story": ("althea", "Althea", "The mother the page credits with dreaming of a firebrand. Preserve his mistaken attribution."),
    "nell_poins": ("nel", "Nell", "Poins's sister in the marriage story told in Falstaff's letter."),
    "holland_region": ("holand", "Holland", "The place name heard in holland linen, following the prince's reference to the low countries."),
    "japheth_ancestor": ("yafeÓ", "Yapheth", "Noah's son invoked as a remote ancestor by the prince. Uses the historical 285 spelling."),
    "sneak_musician": ("snik", "Sneak", "The musician whose band the drawers seek for Doll."),
    "will_drawer": ("wil", "Will", "The tavern servant who brings advance word of the prince's disguise."),
    "arthur_song_king": ("arthur", "Arthur", "The king in Falstaff's interrupted song."),
    "canary_islands_wine": ("kanari", "Canary", "The islands furnishing the wine Quickly thinks Doll has drunk. Distinct from the canary dance."),
    "bordeaux_wine_place": ("bordo", "Bordeaux", "The place of origin of the stuff Doll compares to Falstaff's cargo."),
    "tisick_deputy": ("tizik", "Tisick", "The deputy quoted at length by Quickly."),
    "dorothy_doll": ("dorothi", "Dorothy", "Pistol's fuller form of Doll's given name. Distinct from Dorothy, Imogen's attendant."),
    "erebus_dark": ("erebus", "Erebus", "The underworld darkness invoked in Pistol's theatrical threats."),
    "hiren_sword": ("hairen", "Hiren", "Invoked when Pistol draws his sword; Quickly hears him as asking for a woman."),
    "cerberus_hound": ("kerberus", "Cerberus", "The infernal hound grandiosely called King Cerberus by Pistol."),
    "calipolis_stage": ("kalipolis", "Calipolis", "The theatrical name in Pistol's quotation about feeding and growing fat."),
    "galloway_region": ("galowei", "Galloway", "Region invoked through the Galloway nags in Pistol's retort."),
    "atropos_fate": ("atropos", "Atropos", "The Fate invoked by Pistol after naming the Sisters Three."),
    "agamemnon_greek": ("agamemnon", "Agamemnon", "Greek commander in Doll's comparison of Falstaff to the heroes of Troy."),
    "tewkesbury_town": ("tiuksberi", "Tewkesbury", "Town whose thick mustard Falstaff compares to Poins's wit."),
    "westminster_seat": ("westminster", "Westminster", "Seat where Peto reports the king is staying."),
    "peesell_quickly": ("tremzel", "Peesell", "Quickly's shortened, mispronounced form of Pistol's native name, preserving its opening sounds."),
    "surrey_earl": ("suri", "Surrey", "The earl summoned with Warwick to attend King Henry at night."),
    "warwick_earl": ("warik", "Warwick", "The king's adviser who discusses the rebel numbers and encourages him to rest."),
    "nevil_warwick": ("nevil", "Nevil", "Warwick as addressed by the king in the scene of Richard's prediction."),
    "john_blunt": ("jon", "John", "Sir John Blunt, who attends the king at night in Part 2. Distinct from Sir Walter Blunt, slain in Part I."),
    "blunt_john_knight": ("blunt", "Blunt", "Surname of Sir John Blunt who enters with Warwick and Surrey."),
}
SENSES = {
    "rumour_player": (["rumour"], "Rumor", "proper", "The personification of rumor who wears a costume painted with tongues. Uses the ordinary native word for rumor."),
    "induction_play": (["begin", "speech"], "Induction", "noun", "The opening presentation before the acts of the play."),
    "chief_justice_lord": (["chief", "magistrate_official"], "chief justice", "noun", "The senior judge who questioned Falstaff about the Gad's Hill robbery."),
    "satin_cloth": (["smooth", "silk"], "satin", "noun", "The smooth silk ordered on credit by Falstaff."),
    "slops_breeches": (["loose", "kjv_hosen"], "loose breeches", "noun", "The loose breeches for which Falstaff wants satin."),
    "gravy_sauce": (["meat", "juice"], "gravy", "noun", "Meat juices in Falstaff's repeated substitution of gravy for gravity."),
    "gooseberry_fruit": (["sour", "berry"], "gooseberry", "noun", "The single small fruit by which Falstaff measures the market's esteem for men's gifts."),
    "angel_gold_coin": (["angel", "gold"], "gold angel", "noun", "The angel coin, whose defective weight Falstaff contrasts with his own as he answers the judge's evil angel."),
    "service_pension": (["soldier", "pay"], "pension", "noun", "The military pension for which Falstaff expects his limp to furnish a good excuse."),
    "fang_officer": (["tooth"], "Fang", "proper", "The arresting officer's predatory name is rendered with the native tooth root."),
    "snare_officer": (["snare"], "Snare", "proper", "Fang's assistant. His telling name uses the native word for a trap."),
    "pie_corner_place": (["pie", "corner"], "Pie Corner", "proper", "The place where Quickly says Falstaff buys a saddle."),
    "lubbers_head_inn": (["lout_insult", "head"], "Lubber's Head", "proper", "Quickly's bungled name for the tavern sign. Keep the lout in her version."),
    "smooth_silkman": (["smooth"], "Smooth", "proper", "The silk dealer with the telling surname Smooth. Distinct from Dommelton."),
    "tearsheet_surname": (["rend_apart", "sheet_bed"], "Tearsheet", "proper", "Doll's bawdy surname rendered as the rending of a bedsheet."),
    "whitsun_feast": (["spirit", "feast"], "Whitsun", "proper", "The Pentecost feast in Quickly's phrase Wheeson week. Carries the religious reference through native vocabulary."),
    "prawn_crustacean": (["small", "sea", "claw"], "prawn", "noun", "The small crustaceans in the butcher's wife's dish, named for their small sea-claws."),
    "noble_gold_coin": (["noble", "gold"], "noble coin", "noun", "The gold coin in Quickly's offer of twenty nobles. Distinct from social rank."),
    "peach_fruit": (["soft", "stone", "fruit"], "peach", "noun", "The soft stone fruit whose color the prince remembers in Poins's stockings."),
    "martinmas_cattle": (["ox", "feast"], "Martinmas beef", "noun", "The seasonal feast associated with slaughtered, well-fed cattle. Poins uses Martlemas as a name for Falstaff."),
    "pistol_ensign": (["pistol_sidearm"], "Pistol", "proper", "The ensign bears the same native name as the handgun in Falstaff's extended gun jokes."),
    "ensign_rank": (["banner", "carry"], "ensign", "noun", "The military rank of standard-bearer, called ancient in the source. Distinct from elderly."),
    "dumb_minister": (["silent"], "Dumb", "proper", "The minister named Dumb by Quickly, rendered with the native root for silent."),
    "conger_fish": (["long", "sea", "fish_creature"], "conger eel", "noun", "The marine eel in Doll's insult and in Falstaff's account of Poins's tastes."),
    "aspen_tree": (["tremble", "tree"], "aspen", "noun", "The tree whose trembling leaf Quickly likens to her own shaking."),
    "quickly_pulsidge": (["pulse", "rank"], "pulsidge", "noun", "Quickly adorns pulse with a misplaced status ending as she takes Doll's pulse."),
    "quickly_confirmities": (["confirm", "weakness"], "confirmities", "noun", "Quickly blends confirmation into infirmities while asking her guests to bear each other's faults."),
    "occupy_euphemism": (["use"], "occupy", "verb", "The common verb use made objectionable by a sexual use in Doll's comparison. Both senses are assigned to the same native word here."),
    "corporal_rank": (["lower", "officer"], "corporal", "noun", "Bardolph's subordinate military rank in Pistol's address."),
    "venus_planet": (["venus"], "Venus", "proper", "The planet paired with Saturn, with an allusion to the goddess of love. Hal applies the conjunction to Doll and Falstaff."),
    "quoits_game": (["ring", "throw", "sport"], "quoits", "noun", "The ring-throwing game at which Falstaff says Poins excels."),
    "kirtle_garment": (["kjv_skirt_garment"], "kirtle", "noun", "The skirted garment for which Falstaff offers Doll a choice of fabric."),
}


def lexical_entries(language):
    places = {"chester_city", "pomfret_castle", "smithfield_market", "basingstoke_town", "lumbert_street",
              "holland_region", "canary_islands_wine", "bordeaux_wine_place", "galloway_region",
              "tewkesbury_town", "westminster_seat"}
    entries, glosses = build_entries(language, NAMES, SENSES, places)
    entries["job_sufferer_falstaff"]["sameBearerAs"] = "kjv_job_sufferer"
    entries["japheth_ancestor"]["sameBearerAs"] = "kjv_japheth"
    entries["dorothy_doll"]["sameBearerAs"] = "doll_given"
    entries["peesell_quickly"]["sameBearerAs"] = "pistol_ensign"
    entries["nevil_warwick"]["sameBearerAs"] = "warwick_earl"
    suit = language.lexicon["legal_process"]["form"]
    assert suit.startswith("lam")
    slip = "lem" + suit[3:]
    entries["quickly_exion"] = dict(form=slip, roman=language.reading(slip), pos="noun",
        meaning="Quickly's slip for her legal action, with the opening vowel of the native legal-process term displaced.",
        semanticId="lex.quickly_exion", derivationKeys=["legal_process"], usageScope="editorial-exception",
        status="authored", historicalForms=[], origin="Source-specific Vayrshemon malapropism for Quickly's exion in 2.1.")
    glosses["quickly_exion"] = "suit (slip)"
    return entries, glosses


def prepare():
    add_source_entries("henry-iv-part-2", "henry-iv-part-1", lexical_entries,
                       "Keep Rumor's knowingly false dispatch distinct from the actual outcome and from Morton's eyewitness account. Lord Bardolph is not Falstaff's companion.")


if __name__ == "__main__":
    prepare()
