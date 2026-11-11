"""Personal names, ports and speaking names in the Pericles witness."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "pericles_tyrian_prince": ("perikles", "Pericles", "The prince of Tyre, husband of Thaisa and father of Marina."),
    "gower_chorus_poet": ("gauer", "Gower", "The old poet who returns to tell and stage this story. The earlier messenger and captain of this name are distinct people."),
    "antiochus_riddle_king": ("antiokus", "Antiochus", "The king whose incest with his daughter is the answer to his deadly riddle."),
    "thaliard_antiochus_agent": ("thaliard", "Thaliard", "The chamber attendant whom Antiochus supplies with poison and gold to kill Pericles."),
    "helicanus_tyrian_regent": ("helikanus", "Helicanus", "Pericles's trusted lord in Tyre. He declines a crown during the prince's absence."),
    "helicane_short_form": ("helikan", "Helicane", "The contracted name for Helicanus, used by Gower and by the Tyrian lords."),
    "escanes_tyrian_lord": ("eskanes", "Escanes", "The lord of Tyre who confers with Helicanus."),
    "cleon_tarsus_governor": ("kleon", "Cleon", "The governor of famine-stricken Tarsus and husband of Dionyza."),
    "dionyza_tarsus_wife": ("diyoniza", "Dionyza", "Cleon's wife, mother of Philoten and foster guardian of Marina."),
    "simonides_pentapolis_king": ("simonides", "Simonides", "The king at Pentapolis who welcomes the knights, father of Thaisa."),
    "thaisa_simonides_daughter": ("taisa", "Thaisa", "Simonides's daughter, wife of Pericles, mother of Marina. Her apparent death at sea is followed by revival at Ephesus."),
    "lychorida_family_nurse": ("likorida", "Lychorida", "The nurse who tends the family and tells Marina of her birth at sea."),
    "cerimon_ephesian_healer": ("serimon", "Cerimon", "The lord at Ephesus who revives the woman taken for dead."),
    "philemon_cerimon_attendant": ("filemon", "Philemon", "Cerimon's attendant. Distinct from the earlier householder of myth and the biblical addressee."),
    "nicander_ship_attendant": ("nikander", "Nicander", "The person asked to bring the satin coffin during the storm."),
    "nestor_ship_attendant": ("nestor", "Nestor", "Pericles asks Lychorida to have this attendant fetch spices, ink, paper, casket and jewels. He is distinct from the ancient Greek counselor."),
    "philoten_dionyzas_daughter": ("filoten", "Philoten", "Cleon and Dionyza's daughter. Her mother compares her accomplishments with Marina's."),
    "leonine_tarsus_servant": ("leonin", "Leonine", "The servant whom Dionyza orders to kill Marina. Pirates take her before he can do so."),
    "valdes_pirate_captain": ("valdes", "Valdes", "The pirate captain whose men Leonine identifies."),
    "lysimachus_mytilene_governor": ("lisimakus", "Lysimachus", "Governor of Mytilene, who visits Marina in the brothel and later brings her to her father's ship."),
    "bolt_brothel_servant": ("bolto", "Bolt", "The named brothel servant whom Marina persuades to find her work teaching."),
    "tib_brothel_nickname": ("tib", "Tib", "A familiar woman's name used generically of the woman asked for by a brothel customer. No specific participant is identified."),
    "aesculapius_healing_god": ("eskulapius", "Aesculapius", "The god of healing to whom Cerimon appeals."),
    "priapus_fertility_god": ("priyapus", "Priapus", "The fertility deity the Bawd says Marina could freeze."),
    "tyre_princes_city": ("tyr", "Tyre", "The prince's home city. Shares the inherited permitted place form for Tyre."),
    "tyrus_same_city": ("tirus", "Tyrus", "The longer name for the same Tyre used by Gower and Pericles."),
    "antioch_riddle_city": ("antiok", "Antioch", "Antiochus's city in Syria, where he challenges his daughter's suitors."),
    "tarsus_famine_city": ("tarsus", "Tarsus", "The city relieved by Pericles's grain ships and the later foster home of Marina."),
    "ephesus_temple_city": ("efesus", "Ephesus", "The city of Cerimon and Diana's temple."),
    "pentapolis_tourney_city": ("pentapolis", "Pentapolis", "The place ruled by Simonides, where the castaway Pericles enters the tournament."),
    "mytilene_harbour_city": ("mitilene", "Mytilene", "The place where the pirates sell Marina and where her father later anchors."),
    "transylvania_travellers_land": ("transilvaniya", "Transylvania", "The land within the Bawd's designation of the dead traveler."),
}

SENSES = {
    "marina_sea_child": (["drama_native_sea","child"], "Marina", "proper", "Sea-child. Her father named her for her birth at sea, the explanation she gives him during the recognition scene."),
    "pilch_fishermans_nickname": (["skin","coat"], "Pilch", "proper", "Fur-coat, the name the First Fisherman calls out before the Second Fisherman answers."),
    "patchbreech_fishermans_nickname": (["patch","leg"], "Patchbreech", "proper", "Patch-leg. The patch on a trouser leg gives the Third Fisherman's clothing nickname."),
    "verolles_french_customer": (["drama_native_pox"], "Verolles", "proper", "The French knight whose disease the Bawd comments on. His speaking surname evokes the pox."),
    "ember_eve_fast": (["fast_abstain","evening"], "Ember eve", "noun", "The eve of a seasonal religious fast, among the occasions Gower says the old tale has been sung."),
    "fisherman_net_worker": (["fish","person"], "fisherman", "noun", "A person fishing for a living. The three fishermen have separate ordinal speech labels."),
    "porpoise_round_snout": (["short","beak","dolphin"], "porpoise", "noun", "The short-snouted sea mammal the fisherman saw rolling in the water; he reports the half-fish, half-flesh belief."),
    "armour_skirt_bases": (["knight","kjv_skirt_garment"], "bases", "noun", "A knight's tournament skirts, to be made from the fisherman's gown. A pair describes the outfit."),
    "condolement_fishermans_fee": (["grief","pay"], "condolement", "noun", "Grief-pay, a comic word for the fisherman's expected recompense. It mixes a word of mourning into his demand for a tip."),
    "perch_survey_length": (["measure","rod"], "perch", "noun", "A surveyor's rod as a unit of length, eleven halves of a yard. Gower says many a perch without giving the total distance."),
    "chequin_gold_coin": (["gold","coin_currency"], "chequin", "noun", "The gold coin, or sequin, in which the Pander reckons the savings that would let him give up the trade."),
    "seafarers_omen_belief": (["omen","belief"], "superstition", "noun", "Pericles's description of the crew's belief that a dead body causes the storm to continue."),
    "knights_shield_emblem": (["shield_target","mark"], "shield device", "noun", "The pictorial emblem presented on a tournament shield at Pentapolis; the motto voices its meaning."),
    "melancholy_guest": (["melancholy"], "Melancholy", "proper", "Pericles's sad and dull-eyed companion, described as a habitual visitor."),
    "plenty_cup_giver": (["abundance"], "Plenty", "proper", "Plenty holds a full hand over Tarsus and offers her cup to wealthy cities."),
    "riches_in_streets": (["wealth"], "Riches", "proper", "Riches strews herself through Tarsus before the famine."),
    "fates_thread_cutters": (["fate"], "Fate", "proper", "The Destinies that cut a thread of life. Also the Fates invoked by Dionyza."),
    "patience_at_graves": (["patience"], "Patience", "proper", "Pericles imagines personified Patience smiling at kings' graves. Distinct from the historical queen's attendant."),
    "extremity_at_graves": (["extremity"], "Extremity", "proper", "In the imagined encounter Patience's smile puts Extremity out of action."),
    "graces_divine_attendants": (["grace","goddess"], "Grace", "proper", "One of the divine Graces. Pericles imagines them attending the princess as subjects."),
    "tyrian_citizen": (["tyre_princes_city","person"], "Tyrian", "noun", "A person from the prince's city."),
    "woman_priest_diana": (["woman","priest"], "priestess", "noun", "A woman who serves in Diana's temple, including Thaisa in the final scene."),
    "transylvanian_customer": (["transylvania_travellers_land","person"], "Transylvanian", "noun", "The dead customer mentioned by the Bawd."),
}


def lexical_entries(language):
    places = {"tyre_princes_city", "tyrus_same_city", "antioch_riddle_city", "tarsus_famine_city",
              "ephesus_temple_city", "pentapolis_tourney_city", "mytilene_harbour_city",
              "transylvania_travellers_land"}
    return build_entries(language, NAMES, SENSES, places)


def prepare():
    add_source_entries("pericles", "othello", lexical_entries,
        "Gower the poet narrates. Marina's speaking name uses the native sea and child roots. Her birth, the false report of her death and the staged recognition are distinguished.")


if __name__ == "__main__":
    prepare()
