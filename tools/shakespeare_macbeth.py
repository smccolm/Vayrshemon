"""Names, ranks and source-specific dramatic senses for Macbeth."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "macbeth_scottish_thane": ("makbeÕ", "Macbeth", "The Thane of Glamis to whom the sisters also promise Cawdor and the crown."),
    "duncan_scottish_king": ("dunkan", "Duncan", "The king who names his son Malcolm heir and invests Macbeth with Cawdor."),
    "malcolm_duncan_son": ("malkom", "Malcolm", "Duncan's elder son, later named Prince of Cumberland."),
    "donalbain_duncan_son": ("donalbën", "Donalbain", "Duncan's younger son, who follows a separate route into exile."),
    "banquo_scottish_captain": ("bankwo", "Banquo", "Macbeth's fellow captain, to whom the sisters promise royal descendants."),
    "lennox_scottish_lord": ("lenoks", "Lennox", "The Scottish lord present when the wounded captain and Ross report."),
    "ross_scottish_thane": ("ros", "Ross", "The Scottish lord who reports the Norwegian conflict and carries Duncan's greeting."),
    "ross_scottish_district": ("ros", "Ross", "The district in the Thane of Ross's title."),
    "angus_scottish_thane": ("angus", "Angus", "The lord accompanying Ross. His person is distinct from the district of Angus."),
    "macdonwald_rebel": ("makdonwald", "Macdonwald", "The rebel Macbeth kills in the captain's report, distinct from the Thane of Cawdor."),
    "sweno_norwegian_king": ("sveno", "Sweno", "The Norwegian king who sues for terms after the fighting."),
    "bellona_war_goddess": ("belona", "Bellona", "War goddess whose figurative bridegroom is Macbeth in Ross's report."),
    "colme_island_saint": ("kolm", "Colme", "The saint in the island name at which the Norwegian king pays for his men's burial."),
    "glamis_scottish_district": ("glamis", "Glamis", "Macbeth's inherited thanedom, distinct from the subsequent grant of Cawdor."),
    "cawdor_scottish_district": ("kador", "Cawdor", "The thanedom transferred from the condemned lord to Macbeth."),
    "fife_scottish_district": ("faif", "Fife", "The Scottish district named by Ross and associated with Macduff."),
    "forres_scottish_town": ("fores", "Forres", "The destination Banquo asks about when he sees the sisters."),
    "aleppo_syrian_city": ("alepo", "Aleppo", "The city to which the master of the Tiger has sailed."),
    "sinel_macbeth_father": ("sinel", "Sinel", "Macbeth's late father, through whom he inherited Glamis."),
    "cumberland_princely_title": ("kumberland", "Cumberland", "Malcolm's territorial title as designated heir to Duncan."),
    "inverness_macbeth_castle": ("invernes", "Inverness", "The place where Duncan will visit Macbeth and his wife."),
    "macduff_fife_thane": ("makduf", "Macduff", "The Thane of Fife who discovers Duncan's murder."),
    "fleance_banquo_son": ("fleans", "Fleance", "Banquo's son, who escapes from his father's murderers."),
    "duff_macduff_short": ("duf", "Duff", "Banquo's familiar short address to Macduff after the discovery of Duncan."),
    "scone_investiture_place": ("skçn", "Scone", "The place to which Macbeth goes for investiture as king."),
    "colmekill_royal_burial": ("kolmekil", "Colmekill", "The sacred burial place of Duncan and the kings before him, distinct from Saint Colme's Inch."),
    "siward_english_commander": ("siward", "Siward", "The English commander whose support Macduff seeks for Malcolm."),
    "harpier_witch_familiar": ("harpyer", "Harpier", "The familiar whom the third witch hears announcing the time; the source does not specify an animal."),
    "menteith_scottish_thane": ("menteith", "Menteith", "The lord who marches with Caithness and joins Malcolm. Distinct from his territorial name."),
    "caithness_scottish_thane": ("kaiÕnes", "Caithness", "The lord who reports that Macbeth is fortifying Dunsinane."),
    "seyton_macbeth_follower": ("seton", "Seyton", "Macbeth's attendant, who brings word of the queen's death."),
    "siward_younger_son": ("siward", "Siward", "The younger Siward killed onstage by Macbeth. His given role title includes the explicit young."),
    "birnam_forest_place": ("birnam", "Birnam", "The forest from which Malcolm's soldiers will cut boughs."),
    "dunsinane_hill_place": ("dunsinën", "Dunsinane", "The hill and stronghold named in the third apparition's condition."),
}

PLACES = {"ross_scottish_district", "glamis_scottish_district", "cawdor_scottish_district",
          "fife_scottish_district", "forres_scottish_town", "aleppo_syrian_city",
          "cumberland_princely_title", "inverness_macbeth_castle", "scone_investiture_place", "colmekill_royal_burial",
          "birnam_forest_place", "dunsinane_hill_place"}

SENSES = {
    "lady_macbeth_spouse": (["lady", "macbeth_scottish_thane"], "Lady Macbeth", "proper",
        "Macbeth's wife. Her own role has a separate identity and uses the native honorific and localized family name."),
    "lady_macduff_spouse": (["lady", "macduff_fife_thane"], "Lady Macduff", "proper",
        "Macduff's wife, who is attacked at her house. Distinct from Lady Macbeth."),
    "graymalkin_witch_familiar": (["drama_native_grey", "cat"], "Graymalkin", "proper",
        "The first witch's named grey cat. Its speaking name is made of the native colour and animal."),
    "paddock_witch_familiar": (["toad"], "Paddock", "proper",
        "The second witch's named toad. The common animal name serves as a proper call."),
    "thane_scottish_rank": (["land", "lord"], "thane", "noun",
        "The Scottish territorial rank shared by Glamis, Cawdor, Ross and Fife."),
    "dollar_northern_coin": (["silver", "coin_currency"], "dollar", "noun",
        "The silver coin demanded in the Scottish settlement with Norway. No conversion into another currency is specified."),
    "tiger_merchant_ship": (["tiger"], "Tiger", "proper",
        "The named ship whose master the First Witch means to torment. Its native name is the animal."),
    "weird_sisters_fate": (["fate", "sister"], "Weird Sister", "proper",
        "A sister of fate. The witches use the name of themselves during their winding charm."),
    "martlet_temple_swallow": (["temple", "swallow_nesting_bird"], "martlet", "noun",
        "The swallow-like bird that nests on buildings, here Duncan's summer guest."),
    "sewer_table_steward": (["table_meal", "steward"], "table steward", "noun",
        "The officer overseeing dishes at the feast. The word denotes an office in the household."),
    "goose_tailors_iron": (["goose"], "goose iron", "noun",
        "A tailor's smoothing iron called a goose. Its native form matches the bird, so the Porter's talk of roasting it has both readings."),
    "rhinoceros_horned_beast": (["horn", "nose", "beast"], "rhinoceros", "noun",
        "The horn-nosed beast Macbeth says he could face more readily than the ghost."),
    "witches_cauldron": (["large", "cooking_pot"], "cauldron", "noun",
        "The large pot around which the witches circle and sing."),
    "yew_bow_tree": (["bow_weapon", "tree"], "yew", "noun",
        "The poisonous bow-wood tree whose shoots the witches cut at the eclipse."),
    "shark_sea_predator": (["sea", "hunt", "fish"], "shark", "noun",
        "The predatory saltwater fish whose stomach and gullet are added to the cauldron."),
    "conjured_apparition": (["spirit", "shape"], "apparition", "noun",
        "One of the spirits appearing in a distinct form and speaking to Macbeth at the cauldron."),
    "blindworm_legless_lizard": (["without", "leg", "kjv_lizard"], "blindworm", "noun",
        "The legless lizard to which the witch attributes a sting. The native form describes its body."),
    "doctor_edward_court": (["doctor"], "doctor", "noun",
        "The unnamed English doctor who reports patients awaiting Edward. Only his office prints."),
    "doctor_dunsinane_court": (["doctor"], "doctor", "noun",
        "The Scottish physician who witnesses Lady Macbeth sleepwalking. His native role label matches that of the distinct English doctor."),
    "evil_royal_touch_disease": (["evil"], "the evil", "noun",
        "The disease historically called the king's evil, scrofula. The healing claim is the belief expressed by this play's speakers."),
    "rhubarb_purging_root": (["purge", "root"], "rhubarb", "noun",
        "The purging root invoked in Macbeth's question to the doctor about driving out the English."),
    "senna_purging_leaf": (["purge", "leaf"], "senna", "noun",
        "The purging leaf paired with rhubarb in Macbeth's metaphor for his country."),
}


def lexical_entries(language):
    return build_entries(language, NAMES, SENSES, PLACES)


def prepare():
    add_source_entries("macbeth", "loves-labors-lost", lexical_entries,
        "The witches' speaking names use native animal roots. Glamis is inherited, Cawdor transferred and kingship predicted. Macdonwald and the condemned Thane of Cawdor are separate rebels.")


if __name__ == "__main__":
    prepare()
