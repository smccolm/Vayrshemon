"""Names and theatrical senses for Henry VI, Part 3 on the shared 0.14 branch."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


PEOPLE = {
    "somerville_warwick_scout": ("somervil", "Somerville", "Warwick's informant who distinguishes the drum from Warwick from Clarence's force at Southam."),
    "aesop_fabulist": ("esop", "Aesop", "The fable-teller whom the captive prince invokes as a taunt to Richard."),
    "daedalus_father": ("dedalos", "Daedalus", "The bereaved father in Henry's comparison of the dead prince to Icarus."),
    "minos_king": ("minos", "Minos", "The king who barred the fliers' course, corresponding in Henry's speech to Richard's father."),
    "ned_lancaster_child": ("ned", "Ned", "Margaret's familiar address to the Lancastrian prince, first as her fellow pilot, then beside his body."),
    "dick_gloucester_brother": ("dik", "Dick", "The captive prince's familiar form for Richard of Gloucester in his defiance of the brothers."),
    "edward_york_infant": ("edward", "Edward", "Infant son of King Edward and Elizabeth whom the nurse carries in the last scene."),
    "ned_york_infant": ("ned", "Ned", "The king's familiar address to his infant son, distinct from Margaret's murdered Ned."),
    "bess_elizabeth_queen": ("bes", "Bess", "Edward's familiar address to his queen before he kisses their child."),
    "john_montgomery": ("jon", "John", "Given name of the Yorkist knight who demands that Edward reclaim his crown at York."),
    "montgomery_yorkist": ("montgomeri", "Montgomery", "Edward's ally who casts down his gauntlet at York."),
    "somerset_warwick_ally": ("somerset", "Somerset", "The living lord who follows Clarence to Warwick. Distinct from Somerset whose head Richard showed at the beginning of the play."),
    "pembroke_edward_ally": ("pembrok", "Pembroke", "The lord whom Edward sends with Stafford to raise men against Warwick."),
    "stafford_edward_ally": ("staford", "Stafford", "Edward's living officer, distinct from the lord reported slain at Saint Albans."),
    "hastings_edward_ally": ("hastiÙz", "Hastings", "Edward's close supporter, who assists in his escape from the bishop's custody."),
    "hungerford_heir_father": ("huÙerford", "Hungerford", "The lord whose heir Clarence says Hastings deserves."),
    "scales_heir_father": ("skeilz", "Scales", "The lord whose daughter and heir has been given to Elizabeth's brother."),
    "bonville_heir_father": ("bonvil", "Bonville", "The lord whose heir Edward has given to his wife's son."),
    "rivers_queen_brother": ("riverz", "Rivers", "Queen Elizabeth's brother, who hears from her that Edward is a prisoner."),
    "rhesus_king": ("resos", "Rhesus", "The prince whose Thracian horses Ulysses and Diomed took in Warwick's comparison."),
    "diomed_greek": ("diomed", "Diomed", "The Greek warrior who raided Rhesus's tents with Ulysses. Distinct from Cleopatra's attendant."),
    "william_stanley_rescuer": ("wiliam", "William", "Given name of the knight who helps Richard and Hastings free Edward."),
    "stanley_edward_rescuer": ("stanli", "Stanley", "The knight in Edward's rescue party, distinct from Duchess Eleanor's custodian."),
    "henry_richmond_child": ("henri", "Henry", "The young Earl of Richmond blessed by Henry VI, distinct from both kings in the current conflict."),
    "richmond_earldom": ("riÑmond", "Richmond", "The young earl's title when Somerset introduces him to King Henry."),
    "oxford_lancaster_earl": ("oksford", "Oxford", "The Lancastrian earl who accompanies Margaret in France and recalls the deaths of his father and brother."),
    "aubrey_vere_brother": ("obrei", "Aubrey", "Oxford's elder brother, named as a victim of Edward's judgment."),
    "vere_oxford_brother": ("ver", "Vere", "The family name used for Oxford's elder brother Aubrey."),
    "bourbon_fleet_admiral": ("burbon", "Bourbon", "Lewis's admiral who is ordered to carry the expedition across the sea."),
    "lady_grey_widow": ("grei", "Grey", "Lady Grey, the widow whose petition Edward hears. She later appears as Queen Elizabeth."),
    "elizabeth_edward_queen": ("elizabet", "Elizabeth", "Queen Elizabeth, the former Lady Grey, Edward's wife and mother of his infant son."),
    "richard_grey_husband": ("riÑard", "Richard", "The given name Edward uses for the widow's dead husband in this witness."),
    "grey_widow_husband": ("grei", "Grey", "Lady Grey's deceased husband, Sir Richard Grey in Edward's account. Distinct from Sir Thomas Grey in Henry V."),
    "proteus_shape_changer": ("proteos", "Proteus", "The shape-changing figure with whom Richard compares his own ability to change for advantage."),
    "bona_french_lady": ("bona", "Bona", "The lady whom Warwick hopes to marry to Edward. Lewis calls her sister in this play."),
    "lewis_french_king": ("luis", "Lewis", "The French king whom Margaret and Warwick petition. Distinct from namesakes in the French genealogy."),
    "harry_henry_sixth": ("hari", "Harry", "Henry's familiar form of his own name as he returns in disguise. Distinct from his father and from Hotspur."),
    "menelaus_spartan": ("menelaos", "Menelaus", "Helen's husband and Agamemnon's brother, named in Edward's taunt to Margaret."),
    "phaeton_sun_driver": ("faeton", "Phaeton", "Clifford compares the fallen York to the youth cast from the sun chariot."),
    "george_york_son": ("jorj", "George", "York's son, named by Margaret beside Edward, Richard and Rutland."),
    "dickie_york_son": ("diki", "Dickie", "Margaret's diminutive for York's son Richard when she mocks his father."),
    "john_mortimer_uncle": ("jon", "John", "York's uncle, Sir John Mortimer, who enters with Hugh and proposes to meet Margaret in the field. Distinct from the dead John whom Cade impersonated."),
    "hugh_mortimer_uncle": ("hyu", "Hugh", "Sir Hugh, brother of Sir John. The two arrive together at York's castle."),
    "mortimer_uncle_family": ("mortimer", "Mortimer", "The surname shared by the two uncles whom York greets at Sandal."),
    "rutland_york_son": ("rutland", "Rutland", "York's young son who flees with his tutor and is killed by Clifford."),
    "edward_lancaster_prince": ("edward", "Edward", "The royal child of Margaret and Henry, displaced by the succession compact. Distinct from York's son Edward."),
    "falconbridge_admiral": ("falkonbrij", "Falconbridge", "The officer whom Margaret names as commander of the Narrow Seas, distinct from the title on Talbot's roll."),
    "cobham_kent_lord": ("kobam", "Cobham", "The Kentish lord to whom York sends his son Edward for support. Distinct from Duchess Eleanor Cobham."),
    "mortimer_roger_march": ("mortimer", "Mortimer", "The family name of Roger, Earl of March, whom Henry names as York's grandfather."),
    "norfolk_york_ally": ("norfolk", "Norfolk", "The lord who helps York take the chair of state. Distinct from the elder Mowbray in the earlier plays."),
    "montague_york_ally": ("montagyu", "Montague", "The ally who shows his sword to York and calls him brother. This preserves his spoken address without supplying a family relationship."),
    "stafford_buckingham_son": ("staford", "Stafford", "Buckingham's son. York reports him killed at the front of the battle."),
    "wiltshire_montague_foe": ("wiltshir", "Wiltshire", "The earl whose blood Montague shows to York."),
    "northumberland_father_albans": ("northumberlend", "Northumberland", "The father killed in the battle York recounts. His son appears alive in the royal party."),
    "northumberland_avenger": ("northumberlend", "Northumberland", "Son of the Northumberland killed at Saint Albans. Henry appeals to his vow of vengeance."),
    "westmorland_henry_ally": ("westmorland", "Westmorland", "The earl who urges Henry to pull York from the throne and leaves when Henry agrees to disinherit the prince."),
    "exeter_henry_ally": ("ekseter", "Exeter", "The duke addressed as cousin by Henry, who changes his judgment upon hearing the argument about Richard's resignation."),
}
SENSES = {
    "magpie_chattering": (["chatter", "bird"], "magpie", "noun", "The chattering pie in Henry's catalogue of birth omens, distinct from the night-crow and the raven."),
    "alderman_york": (["town", "counsel"], "alderman", "noun", "A member of the town government who attends York's mayor on the walls."),
    "gauntlet_challenge": (["armour", "glove"], "gauntlet", "noun", "Montgomery throws this armored glove down in challenge to individual combat."),
    "halberd_watch": (["axe_tool", "staff"], "halberd", "noun", "A pole weapon used by the guards at Edward's tent."),
    "prescription_title": (["time", "right"], "prescriptive right", "noun", "A claim founded on long possession. Warwick disputes that sixty-two years establishes title to a kingdom."),
    "admiral_fleet": (["naval_fleet", "commander"], "admiral", "noun", "Commander of Lewis's fleet."),
    "deformity_on_richards_back": (["deformed", "shape"], "Deformity", "proper", "Richard personifies Deformity as a figure seated on his back mocking his body."),
    "crossbow_hunter": (["cross", "bow_weapon"], "crossbow", "noun", "The hunters' bows with a transverse bow and stock. The sound of the shot may alarm the herd."),
    "gamekeeper_hunter": (["deer", "keeper"], "gamekeeper", "noun", "The keeper of the hunting ground who proposes taking the former king like a deer."),
    "flail_thresher": (["grain_kernel", "beat"], "threshing flail", "noun", "The grain-beating implement of Warwick's idle thresher. His soldiers' weapons fall as feebly."),
    "beaver_helmet_plate": (["chin", "plate"], "helmet faceguard", "noun", "The faceguard on Buckingham's helmet, split by Edward's descending stroke."),
    "broom_shrub_badge": (["twig", "shrub"], "broom sprig", "noun", "The plant in the family name's wordplay. Warwick's native line glosses the localized surname with a sprig, then plants and uproots it."),
}

PLACES = {
    "sicils_reignier_claim": ("sisil", "Sicils", "The Sicilies pledged by Reignier with Jerusalem to obtain Margaret's ransom. The source names the territories in the plural."),
    "dunsmore_heath": ("dunzmor", "Dunsmore", "Oxford's last reported position on the march to Coventry."),
    "daintry_town": ("deintri", "Daintry", "The second messenger locates Montague's troop here."),
    "southam_town": ("suÕam", "Southam", "Where Somerville left Clarence, distinct from the direction of the drum."),
    "warwick_town": ("warik", "Warwick", "The town from which the drum sounds, not Warwick the man on the walls."),
    "barnet_field": ("barnet", "Barnet", "The field where Warwick challenges Edward and is mortally wounded."),
    "hames_castle": ("heimz", "Hames", "Castle to which Edward orders Oxford taken."),
    "belgia_low_countries": ("beljia", "Belgia", "Warwick's name for the continental region from which Edward has sailed."),
    "buckingham_county": ("bukiÙam", "Buckingham", "One of Montague's recruiting grounds, distinct from the dukes."),
    "northampton_county": ("norÕamton", "Northampton", "A place assigned to Montague for the levy."),
    "leicestershire_county": ("lesterÛir", "Leicestershire", "The last recruiting ground assigned to Montague."),
    "oxfordshire_county": ("oksfordÛir", "Oxfordshire", "The earl's recruiting ground, distinct from the man who speaks."),
    "flanders_region": ("flanderz", "Flanders", "Destination overseas after Edward's escape by way of Lynn."),
    "york_bishopric_warwick": ("york", "York", "Warwick's brother's see. He is called Archbishop in the commission and Bishop in later dialogue."),
    "lynn_port": ("lin", "Lynn", "Port from which the party intends to take ship for Flanders."),
    "gloucester_richard_duchy": ("gloster", "Gloucester", "The dukedom Edward assigns to his brother Richard, who asks to exchange it for Clarence."),
    "clarence_george_duchy": ("klarens", "Clarence", "The dukedom Edward assigns to his brother George. Distinct from the earlier holders of this title."),
    "olympia_games_site": ("olimpia", "Olympia", "The place invoked in George's comparison with the victors' rewards at the Olympian Games. Distinct from Mount Olympus."),
    "wakefield_battle": ("weikfeld", "Wakefield", "The battle after which Warwick hears of York's death."),
    "welsh_marches": ("marÑ", "Marches", "The border country where Warwick hears Edward and Richard are raising a fresh force."),
    "york_gate_town": ("york", "York", "Town on whose gates Margaret orders York's head to be set. The spoken name matches his title."),
    "sandal_castle": ("sandal", "Sandal", "York's castle at which his uncles join him before the battle."),
    "essex_county": ("eseks", "Essex", "One of the four counties from which Northumberland says Warwick draws his power."),
    "norfolk_county": ("norfolk", "Norfolk", "The county named in Northumberland's account of the southern force, distinct from the peer."),
    "suffolk_county": ("sufolk", "Suffolk", "County from which Warwick draws forces. This occurrence refers to territory, not the earlier duke."),
}


def lexical_entries(language):
    return build_entries(language, PLACES | PEOPLE, SENSES, set(PLACES))


def prepare():
    add_source_entries("henry-vi-part-3", "henry-vi-part-2", lexical_entries,
                       "York's reported battle losses and the next generation's vows of revenge retain separate identities. Warwick plants the family broom sprig.")


if __name__ == "__main__":
    prepare()
