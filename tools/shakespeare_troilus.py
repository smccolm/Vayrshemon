"""Source-specific names and readings for Troilus and Cressida."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "terence_comic_writer": ("terens", "Terence", "Roman comic author paired with Plautus in the quarto address."),
    "cressid_short_name": ("kresid", "Cressid", "Short form of Cressida, the daughter of Calchas."),
    "pandar_short_name": ("pandar", "Pandar", "Short form of Pandarus, Cressida's uncle. The play turns his name into a word for a go-between."),
    "tenedos_island": ("tenedos", "Tenedos", "Island where the Greek ships unload before approaching Troy."),
    "dardan_trojan_gate": ("dardan", "Dardan", "First of the six gates of Troy named in the Prologue, distinct from the Dardan plain."),
    "timbria_trojan_gate": ("timbriya", "Timbria", "Second gate in the Prologue's list."),
    "helias_trojan_gate": ("heliyas", "Helias", "Third gate in the Prologue's list."),
    "chetas_trojan_gate": ("ketas", "Chetas", "Fourth gate in the Prologue's list."),
    "troien_trojan_gate": ("troyen", "Troien", "Fifth gate in the Prologue's list."),
    "antenorides_trojan_gate": ("antenorides", "Antenorides", "Sixth gate in the Prologue's list, distinct from the Trojan leader Antenor."),
    "antenor_trojan_leader": ("antenor", "Antenor", "Trojan warrior for whose return Calchas seeks the surrender of his daughter."),
    "alexander_cressida_servant": ("aleksander", "Alexander", "Cressida's servant who reports on the Trojan and Greek warriors."),
    "cassandra_priam_daughter": ("kasandra", "Cassandra", "Prophetic daughter of Priam and sister of Hector and Troilus."),
    "calchas_cressida_father": ("kalkas", "Calchas", "Cressida's father, the Trojan diviner who joined the Greeks."),
    "deiphobus_priam_son": ("deifobus", "Deiphobus", "One of Priam's sons in the Trojan procession."),
    "helenus_priam_son": ("helenus", "Helenus", "Priam's son and brother to Hector and Troilus, distinct from Helen."),
    "helenas_priam_son_variant": ("helenas", "Helenas", "Entrance spelling for Helenus in the supplied Trojan council scene."),
    "priamus_trojan_king_variant": ("priyamus", "Priamus", "Extended name of Priam in Hector's address to his brothers."),
    "andromache_hector_wife": ("andromake", "Andromache", "Hector's wife, who begs him to stay home from battle."),
    "briareus_many_handed": ("briyareus", "Briareus", "Many-handed figure invoked to mock an Ajax who cannot make use of his gifts."),
    "patroclus_achilles_companion": ("patroklus", "Patroclus", "Achilles's companion in the Greek camp."),
    "boreas_north_wind": ("boreyas", "Boreas", "Personified north wind that rouses Thetis in Nestor's sea image."),
    "myrmidon_achilles_company": ("mirmidon", "Myrmidon", "Achilles is called the great Myrmidon. The plural names his fighting company."),
    "sol_planetary_sun": ("sol", "Sol", "The sun named in Ulysses's comparison between planetary and political rank."),
    "polyxena_priam_daughter": ("poliksena", "Polyxena", "Trojan princess whose claim on Achilles's affection is set against military renown."),
    "cancer_zodiac_crab": ("karkinos", "Cancer", "The celestial Crab receiving the sun in Ulysses's flattery of Ajax."),
    "milo_bull_bearing_athlete": ("milon", "Milo", "Bull-bearing athlete whose title Ulysses would award to Ajax."),
    "nell_helen_of_troy": ("nel", "Nell", "Paris's familiar name for Helen in the music scene."),
    "charon_underworld_ferryman": ("kharon", "Charon", "Ferryman whom Troilus asks Pandarus to impersonate at Cressida's door."),
    "diomedes_greek_full_name": ("diomedes", "Diomedes", "Full name of the Greek warrior also called Diomed, distinct from Cleopatra's attendant."),
    "aquilon_north_wind": ("akwilon", "Aquilon", "North wind personified in Ajax's challenge to the trumpeter."),
    "neoptolemus_trojan_comparison": ("neoptolemos", "Neoptolemus", "Warrior named in Hector's comparison of a champion's reputation and his hopes of taking honor from Hector; the speech supplies no genealogy."),
    "brabbler_hound": ("brabler", "Brabbler", "Named hound whose noisy promises Thersites compares to Diomed's."),
    "ariachne_weaver": ("ariakhne", "Ariachne", "The weaver invoked for her broken thread in Troilus's paradox; preserves the spelling of the local witness."),
    "polydamas_trojan": ("polidamas", "Polydamas", "Warrior reported to have beaten down Menon."),
    "menon_combatant": ("menon", "Menon", "Warrior beaten down by Polydamas in Agamemnon's report."),
    "margareton_priam_son": ("margareton", "Margareton", "Warrior called bastard Margareton in the battle report."),
    "doreus_captive": ("doreus", "Doreus", "Prisoner of Margareton."),
    "epistrophus_fallen_king": ("epistrofos", "Epistrophus", "Fallen king named with Cedius."),
    "cedius_fallen_king": ("sediyus", "Cedius", "Fallen king named with Epistrophus."),
    "polyxenes_fallen_warrior": ("poliksenes", "Polyxenes", "Warrior reported slain, distinct from Polyxena and from the king Polixenes of Bohemia."),
    "amphimachus_warrior": ("amfimakos", "Amphimachus", "Reported mortally wounded with Thoas."),
    "thoas_warrior": ("toas", "Thoas", "Reported mortally wounded with Amphimachus."),
    "palamedes_wounded_warrior": ("palamedes", "Palamedes", "Warrior reported sorely hurt and bruised."),
    "sagittary_trojan_fighter": ("sagitari", "Sagittary", "Dreaded figure who terrifies the Greek forces; distinct from the Venetian location."),
    "galathe_hector_horse": ("galate", "Galathe", "Hector's horse, named by Nestor in the battle report."),
}
PLACES = {k for k in NAMES if k.endswith(("_trojan_gate", "_island"))}


def lexical_entries(language):
    senses = {
        "pandar_eponym_go_between": (["pandar_short_name"], "pander (go-between)", "noun",
            "Pandarus asks that go-betweens be called by his own name. The ordinary noun in this particular vow echoes his localized short name."),
        "tick_sheep_parasite": (["cling", "blood", "suck"], "tick", "noun",
            "The small blood-feeding creature clinging to a sheep in Thersites's comparison."),
    }
    return build_entries(language, NAMES, senses, PLACES)


def prepare():
    add_source_entries("troilus-and-cressida", "titus-andronicus", lexical_entries,
        "Keep the quarto reader's address ahead of the armored Prologue. Distinguish the six named gates from people and places of the same name. Keep the Greeks, Trojans and shortened personal names connected to their earlier dramatic readings.",
        inherited_glosses={"kjv_tree_sap": "sap", "kjv_winnowing_fan": "winnowing fan",
                           "kjv_axletree": "axle", "kjv_millstone": "millstone", "kjv_knead": "knead",
                           "kjv_bolt_door": "door bolt", "kjv_wedge": "wedge", "kjv_copper": "copper",
                           "kjv_sponge": "sponge", "kjv_wine_lees": "wine lees",
                           "kjv_lizard": "lizard", "kjv_latrine_house": "privy",
                           "kjv_almond": "almond"})


if __name__ == "__main__":
    prepare()
