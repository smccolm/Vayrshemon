"""The island household, the Neapolitan passengers and their ship's crew."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "prospero_milan_duke": ("prospero", "Prospero", "The former duke of Milan, Miranda's father and Ariel's master."),
    "miranda_prospero_daughter": ("miranda", "Miranda", "Prospero's daughter, raised on the island."),
    "ariel_island_spirit": ("ariyel", "Ariel", "Spirit serving Prospero, distinct from biblical people and places with the same written name."),
    "caliban_sycorax_son": ("kaliban", "Caliban", "Sycorax's son, who claims the island through his mother."),
    "alonso_naples_king": ("alonso", "Alonso", "King of Naples, father of Ferdinand and Claribel."),
    "ferdinand_naples_prince": ("ferdinand", "Ferdinand", "The king's son, first seen among the people caught in the tempest."),
    "sebastian_alonso_brother": ("sebastyan", "Sebastian", "Alonso's brother. He is not Antonio, the brother who supplanted Prospero."),
    "antonio_prospero_brother": ("antonyo", "Antonio", "Prospero's brother, who has taken his Milanese office."),
    "gonzalo_naples_councillor": ("gonzalo", "Gonzalo", "Councillor who secretly supplied Prospero and Miranda before they were set adrift."),
    "adrian_alonso_courtier": ("adriyan", "Adrian", "Courtier travelling with Alonso."),
    "francisco_alonso_courtier": ("fransisko", "Francisco", "Courtier of Naples, distinct from the sentinel in Hamlet."),
    "trinculo_alonso_jester": ("trinkulo", "Trinculo", "The jester from the royal company."),
    "stephano_alonso_butler": ("stefano", "Stephano", "Alonso's butler, distinct from the servant in Belmont."),
    "sycorax_caliban_mother": ("sikoraks", "Sycorax", "Caliban's mother, expelled from Argier before the arrival of Prospero."),
    "setebos_sycorax_god": ("setebos", "Setebos", "The god whom Caliban calls his mother's."),
    "bermoothes_islands": ("bermudes", "Bermoothes", "The islands named when Ariel reports fetching dew for Prospero."),
    "argier_sycorax_city": ("arjir", "Argier", "The city of Sycorax's banishment, named by Ariel and Prospero."),
    "claribel_alonso_daughter": ("klaribel", "Claribel", "Alonso's daughter, whose marriage is the occasion for the voyage."),
    "tunis_claribel_kingdom": ("tunis", "Tunis", "Tunis, where Claribel is queen."),
    "prosper_caliban_short": ("prosper", "Prosper", "The shortened form of Prospero's name used by Caliban and later by Alonso when he hears it in the thunder."),
    "mall_sailors_song": ("mal", "Mall", "One of the women named in Stephano's sailors' song."),
    "meg_sailors_song": ("meg", "Meg", "The Meg named by the singers, distinct from the women called Meg in other plays."),
    "marian_sailors_song": ("maryan", "Marian", "The Marian named in the sailors' song."),
    "margery_sailors_song": ("marjeri", "Margery", "The Margery named in the sailors' song."),
    "kate_sailors_song": ("ket", "Kate", "The woman with the sharp tongue in the sailors' song."),
    "ban_caliban_song": ("ban", "’Ban", "Caliban sings the final part of his own name before repeating its opening."),
    "ca_caliban_song": ("ka", "Ca-", "The opening of Caliban's name as he repeats it in the song."),
    "dis_underworld_name": ("dis", "Dis", "The underworld ruler who carried off Ceres's daughter. The masque uses his name Dis."),
}

SENSES = {
    "boatswain_ship_officer": (["sail", "keeper"], "boatswain", "noun", "The working officer who gives sail-handling orders and calls on the passengers to keep clear."),
    "topsail_upper_sail": (["high", "sail"], "topsail", "noun", "Sail above a lower sail, ordered taken in during the storm."),
    "topmast_upper_spar": (["high", "kjv_mast"], "topmast", "noun", "The upper spar ordered lowered, distinguished from the sail it carries."),
    "course_lower_sail": (["low", "sail"], "course", "noun", "A large lower sail. The boatswain distinguishes the main course from the pair of courses."),
    "yard_sail_spar": (["sail", "beam"], "yard", "noun", "A transverse spar carrying a sail. Ariel names these spars among the places where he appeared as flame."),
    "bowsprit_forward_spar": (["ship_prow", "beam"], "bowsprit", "noun", "The spar projecting forward from the ship's bow."),
    "ship_deck_hatch": (["deck_surface", "door"], "hatch", "noun", "The covered access through the deck above the sleeping mariners."),
    "trident_neptune_spear": (["kjv_fork_tool", "spear"], "trident", "noun", "Neptune's three-pointed spear. Ariel imagines it shaking in the storm."),
    "island_mild_temperance": (["temperate_mild"], "mildness", "noun", "The mild quality of the island climate in Adrian's description."),
    "temperance_imagined_wench": (["temperate_mild"], "Temperance", "proper", "Antonio takes the preceding word for mild climate as a woman's name. Both senses deliberately have the same native form."),
    "mooncalf_island_insult": (["drama_native_moon", "birth"], "mooncalf", "noun", "The newcomers' insult for Caliban, invoking a monstrous birth attributed to the moon."),
    "swabber_ship_worker": (["wash", "deck_surface"], "swabber", "noun", "The sailor responsible for washing the deck in Stephano's song."),
    "pignut_edible_root": (["earth", "nut"], "pignut", "noun", "An edible underground tuber which Caliban offers to dig with his nails."),
    "marmoset_small_monkey": (["small", "ape_native"], "marmoset", "noun", "The nimble little monkey Caliban offers to show Stephano how to trap."),
    "scamel_island_creature": (["rock", "creature"], "scamel", "noun", "Young creatures gathered from the rock. The identity of the Shakespearean animal is uncertain."),
    "fish_dam_weir": (["water", "fence"], "weir", "noun", "A barrier that traps fish, which Caliban says he will no longer build for Prospero."),
    "timber_log": (["wood", "piece"], "log", "noun", "A length of cut timber. Ferdinand carries and piles these for Prospero."),
    "flesh_fly_breeder": (["flesh", "fly_insect"], "flesh-fly", "noun", "The fly that deposits its young on flesh in Ferdinand's image of intolerable degradation."),
    "catch_musical_round": (["return", "song"], "round", "noun", "A song with successive entries of the same tune. Caliban asks Stephano and Trinculo to sing it."),
    "organ_pipe_music": (["music", "pipe"], "organ pipe", "noun", "The deep sounding pipe of a musical organ. Alonso hears a bass accusation in the thunder."),
    "vetch_fodder_pulse": (["fodder", "bean"], "vetch", "noun", "The fodder legume in Iris's catalogue of Ceres's crops."),
    "oat_nodding_grain": (["hang", "grain_kernel"], "oat", "noun", "The cereal with nodding grain heads, distinguished from wheat, barley and rye in Ceres's fields."),
    "naiad_brook_nymph": (["brook", "nymph"], "naiad", "noun", "One of the water nymphs summoned from the brooks to join the dance."),
    "line_linden_tree": (["thread", "tree"], "linden", "noun", "The fibre-yielding linden from which the garments hang. The stage direction specifies a tree."),
    "equatorial_line": (["middle", "line"], "equator", "noun", "The earth's middle line in the jerkin joke. The word also calls back to the tree carrying the clothes."),
    "barnacle_water_goose": (["sea", "wild_goose_native"], "barnacle goose", "noun", "The goose associated in folklore with sea barnacles. Caliban pairs the imagined transformation with becoming apes."),
    "mountain_tempest_hound": (["mountain"], "Mountain", "proper", "A spirit that hunts the conspirators in hound shape, addressed by Prospero."),
    "silver_tempest_hound": (["silver"], "Silver", "proper", "The spirit hound called by Ariel, distinct from the actual hunting dog named Silver in the Shrew induction."),
    "fury_tempest_hound": (["fury"], "Fury", "proper", "A pursuing spirit hound called twice by Prospero."),
    "tyrant_tempest_hound": (["tyrant"], "Tyrant", "proper", "A hunting spirit in dog shape addressed by Prospero during the pursuit."),
    "mushroom_ground_cap": (["earth", "cap"], "mushroom", "noun", "The mushrooms that Prospero attributes to the elves' midnight work."),
    "chess_kings_game": (["king", "game"], "chess", "noun", "The game at which Prospero reveals the lovers to the assembled party."),
    "pickle_salt_brine": (["drama_native_salt", "water"], "pickle", "noun", "Preserving brine, with a secondary sense of a sorry predicament. Trinculo follows this joke by speaking of his bones and flesh-flies."),
    "furze_thorn_shrub": (["thorn", "bush"], "furze", "noun", "Spiny scrub with which Gonzalo would be content if only he were on land."),
    "cell_prospero_dwelling": (["small", "dwelling"], "cell", "noun", "Prospero's small dwelling on the island, where he has raised Miranda."),
}


def lexical_entries(language):
    return build_entries(language, NAMES, SENSES, {"bermoothes_islands", "argier_sycorax_city", "tunis_claribel_kingdom"})


def prepare():
    add_source_entries("the-tempest", "the-taming-of-the-shrew", lexical_entries,
        "Distinguish the master from the boatswain, the royal passengers from the crew, and the two pairs of brothers. Preserve Prospero's distinction between the spectacle of wreck and the actual safety of the company.",
        inherited_glosses={
            "kjv_heath_shrub": "heath", "kjv_furlong_source": "furlong",
            "kjv_curious_magic_acts": "magic", "kjv_compassion": "compassion",
            "kjv_tumult": "tumult", "kjv_murmur": "grumble", "kjv_grudge": "grudge",
            "kjv_honeycomb": "honeycomb", "kjv_husk": "husk", "kjv_mallows": "mallows",
            "kjv_vineyard": "vineyard", "kjv_razor": "razor", "kjv_cubit": "cubit",
            "kjv_lap_drink": "lap-up",
            "kjv_fruit_cluster": "cluster",
            "kjv_refresh": "refresh", "kjv_multiply": "multiply", "kjv_standard_bearer": "standard-bearer",
            "kjv_belch": "belch", "kjv_plummet": "plummet",
            "iris": "Iris", "juno": "Juno", "venus": "Venus",
            "kjv_oracle_reply": "oracle", "kjv_barley": "barley",
            "kjv_low_cattle": "low", "kjv_lake": "lake",
            "kjv_pillar": "pillar",
        })


if __name__ == "__main__":
    prepare()
