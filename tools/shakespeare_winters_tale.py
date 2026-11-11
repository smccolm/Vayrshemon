"""The Sicilian and Bohemian courts in The Winter's Tale."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "smalus_libyan_king": ("ismalos", "Smalus", "The ruler of Libya whom Leontes names. Florizell pretends that he is Perdita's father."),
    "rogero_sicilian_gentleman": ("rozero", "Rogero", "The second Gentleman, called by name by the first during the recognition reports."),
    "julio_romano_artist": ("zhuliyo romano", "Julio Romano", "The Italian artist credited by the third Gentleman with making the likeness of Hermione. The witness names him Julio Romano."),
    "mopsa_bohemian_shepherdess": ("mopsa", "Mopsa", "The young woman courted by the Shepherd's Son at the sheep-shearing."),
    "dorcas_bohemian_shepherdess": ("dorkas", "Dorcas", "Mopsa's companion at the sheep-shearing; a different person from the woman in Acts."),
    "doricles_florizell_disguise": ("dorikles", "Doricles", "The name under which Florizell visits the Shepherd's household, and the name Perdita uses when speaking in company."),
    "flora_spring_goddess": ("filora", "Flora", "The Roman flower goddess to whom Florizell likens Perdita in her feast clothes."),
    "perdita_foundling": ("perdita", "Perdita", "The name given to the Sicilian infant in Antigonus's dream because she is counted lost. The Shepherd raises her in Bohemia."),
    "florizell_bohemian_prince": ("florizel", "Florizell", "Polixenes's son, called Florizell in this witness. Time introduces his name to the spectators."),
    "autolycus_itinerant_thief": ("autolikos", "Autolycus", "The Bohemian singer, thief and traveling seller who identifies himself by his father's naming and the sign of Mercury."),
    "autolycus_mythic_namesake": ("autolikos", "Autolycus", "The legendary thief invoked through the singer's name and association with Mercury. The naming in the dialogue does not give the singer's father a separate personal name."),
    "archidamus_bohemian_courtier": ("arkidamos", "Archidamus", "Polixenes's courtier who discusses hospitality with Camillo in the opening scene."),
    "camillo_sicilian_counsellor": ("kamilo", "Camillo", "The Sicilian counsellor who welcomes Archidamus. His later service in Bohemia does not change his identity."),
    "leontes_sicilian_king": ("leontes", "Leontes", "King of Sicilia, husband of Hermione and childhood friend of Polixenes."),
    "hermione_sicilian_queen": ("hermioni", "Hermione", "Queen of Sicilia and mother of Mamillius. Distinguish her words from Leontes's accusations."),
    "mamillius_sicilian_prince": ("mamilius", "Mamillius", "The young prince of Sicilia praised by Archidamus and Camillo."),
    "polixenes_bohemian_king": ("poliksenes", "Polixenes", "King of Bohemia, visiting the Sicilian court of his childhood friend."),
    "antigonus_sicilian_lord": ("antigonos", "Antigonus", "The Sicilian lord attending Leontes and husband of Paulina."),
    "paulina_sicilian_lady": ("paulina", "Paulina", "Antigonus's wife, who defends Hermione and the newborn child."),
    "cleomenes_oracle_envoy": ("kleomenes", "Cleomenes", "One of the two Sicilian envoys sent to Apollo's oracle."),
    "dion_oracle_envoy": ("dion", "Dion", "The envoy named alongside Cleomenes, returning with Apollo's sealed answer."),
    "emilia_hermione_attendant": ("emilya", "Emilia", "Hermione's attendant who tells Paulina of the baby's birth in confinement. A different person from Hippolyta's sister."),
    "margery_paulina_taunt": ("marjeri", "Margery", "The King's mocking midwife name for Paulina. Lady Margery is not an additional woman onstage."),
    "delphos_oracle_place": ("delfos", "Delphos", "The sacred place named Delphos in the local witness. The envoys later describe it as an island."),
    "sicilia_winters_kingdom": ("sisiliya", "Sicilia", "The kingdom named Sicilia in this witness; the shared dictionary also has the island name Sicily."),
    "sicilia_style_leontes": ("sisiliya", "Sicilia", "Sicilia when the name of the realm stands for its king, Leontes."),
    "bohemia_style_polixenes": ("bohemiya", "Bohemia", "Bohemia when the name of the realm stands for its king, Polixenes. Shares the inherited name of the country."),
}


SENSES = {
    "pheasant_game_bird": (["tail", "bird"], "pheasant", "noun", "The long-tailed game bird the Shepherd's Son imagines is the meaning of advocate. Retains the mistake and the distinction between cock and hen."),
    "honesty_vendor_personification": (["honesty"], "Honesty", "proper", "The virtue imagined as a fool by Autolycus after cheating the feastgoers."),
    "trust_vendor_personification": (["trust"], "Trust", "proper", "Honesty's sworn brother in the thief's personification of the virtues."),
    "pomander_fragrant_ball": (["perfume_scent", "ball"], "pomander", "noun", "The ball of perfume in the list of the peddler's sold wares."),
    "saultier_rustic_dancer": (["leap", "dance"], "leap-dancer", "noun", "The Servant's rustic saultiers, distinct from the stage direction's satyrs. The native phrase plays on the dancers' jumping; the original sound resemblance is not reproduced."),
    "taleporter_ballad_midwife": (["tale", "carry"], "Taleporter", "proper", "The ballad's alleged witness has a speaking surname, literally one who carries tales. No actual witness confirms the peddler's story."),
    "cypress_gauze": (["thin", "silk"], "cypress gauze", "noun", "The fine black cloth in Autolycus's sales song, distinct from the tree."),
    "ruff_shaping_iron": (["steel", "rod"], "ruff iron", "noun", "The heated steel poking-stick used to shape folds in a ruff."),
    "peddler_traveling_seller": (["travel", "sell"], "peddler", "noun", "The itinerant seller who brings goods and ballads to the sheep-shearing."),
    "milliner_small_wares": (["glove", "sell"], "milliner", "noun", "A dealer in fine small wares. The Servant compares the fit of songs with the fit of this dealer's gloves."),
    "carnation_garden_blossom": (["fringe_clothing", "flower"], "carnation", "noun", "The garden blossom, distinguished from the established flesh-color sense. The native description follows the fringed petals."),
    "gillyvor_streaked_blossom": (["streak", "blossom"], "gillyflower", "noun", "The streaked cultivated flower in Perdita and Polixenes's argument about art and nature."),
    "dibble_planting_peg": (["plant", "rod"], "planting peg", "noun", "A pointed implement used to make a hole in the earth for a cutting."),
    "lavender_fragrant_herb": (["purple", "herb"], "lavender", "noun", "The fragrant herb described as hot among the midsummer gifts."),
    "savory_kitchen_herb": (["spice", "herb"], "savory", "noun", "The culinary herb listed between mints and marjoram."),
    "crown_imperial_flower": (["crown", "bell"], "crown imperial", "noun", "The flowering plant with a crown of hanging bells in the spring garland speech."),
    "flower_de_luce_iris": (["sword", "blossom"], "flower-de-luce", "noun", "The iris of the spring garland speech, described there among lilies. The native plant name refers to its blade-like leaf."),
    "milk_curd_food": (["milk", "curdle"], "curds", "noun", "The milk curds in Camillo's title for Perdita, queen of curds and cream."),
    "tod_wool_unit": (["wool_material", "weight"], "tod of wool", "noun", "The woolman's unit used in the Shepherd's Son's calculation. The dialogue does not state its weight in pounds."),
    "rice_food_grain": (["water", "seed"], "rice", "noun", "The edible grain on the feast shopping list. A native compound referring to the crop."),
    "currant_dried_grape": (["small", "grape"], "currant", "noun", "Small dried grapes used in cookery, distinguished here from the larger sun raisins."),
    "mace_nutmeg_spice": (["nutmeg_spice", "skin"], "mace", "noun", "The spice from the covering of the nutmeg seed; distinct from mace as weapon or insignia."),
    "warden_baking_pear": (["cook", "pear"], "baking pear", "noun", "The firm culinary pear used in a warden pie."),
    "date_palm_fruit": (["palm_tree_native", "fruit"], "date fruit", "noun", "The palm fruit considered and crossed off the shopping list."),
    "hornpipe_dance_tune": (["horn", "dance"], "hornpipe", "noun", "The secular dance tune to which one of the singers incongruously sings psalms."),
    "troll_my_dames_game": (["ball", "arch"], "ball-and-arches", "noun", "A portable game in which balls are rolled through arches. One of the enterprises Autolycus ascribes to his supposed assailant."),
    "stile_fence_step": (["fence", "step"], "stile", "noun", "A crossing of a fence by steps, taken merrily in Autolycus's road song."),
    "superstitious_dream_observance": (["dream", "fear"], "superstitious awe", "noun", "The fearful reverence that leads Antigonus to obey a dream despite calling dreams trifles. Distinct from Festus's description of a religious dispute."),
    "emperor_dynastic_ruler": (["king", "king"], "emperor", "noun", "The dynastic sovereign of Russia whom Hermione names as her father. Separate from Roman imperator as a military address."),
    "time_winters_chorus": (["time"], "Time", "proper", "Time as the speaking Chorus who turns his glass and carries the audience sixteen years forward."),
    "infant_bearing_cloth": (["infant", "cloth"], "bearing-cloth", "noun", "The fine carrying or ceremonial cloth that suggests the exposed infant belongs to a family of rank."),
    "morsel_swallow_game": (["swallow"], "gulp", "verb", "Gulp down as in the flapdragon game. The Shepherd's Son imagines the sea playing the game with the ship."),
    "neat_bovine_collective": (["ox", "herd"], "cattle", "noun", "Cattle as the collective name for the steer, heifer and calf. The English sound-link with neat meaning clean is documented separately."),
    "grace_elder_deed": (["grace"], "Grace", "proper", "Hermione imagines Grace as the name of her earlier good deed, figured as an elder sister. Uses the native word for favor."),
    "pin_web_eyesight": (["eye", "web"], "pin-and-web", "noun", "The obstruction to sight in Leontes's accusation. No more precise diagnosis is asserted."),
    "medal_neck_piece": (["neck", "image"], "medal", "noun", "The medal hung at the neck in Leontes's claim that Polixenes wears Hermione like her medal."),
    "best_betrayal_epithet": (["best"], "the Best", "proper", "Polixenes's allusive title for Yeshūa in his oath about the betrayer. The speaker uses the title and does not utter the personal name."),
    "land_damn_oath": (["earth", "curse"], "land-damn", "verb", "Antigonus's opaque threat against an imagined instigator. The native compound preserves the land and curse without supplying an unspoken punishment."),
    "geld_make_barren": (["cut", "barren"], "geld", "verb", "Antigonus's violent, conditional threat to deprive his daughters or himself of the ability to have children. The verb renders both geld and glib in his speech."),
}


def lexical_entries(language):
    return build_entries(language, NAMES, SENSES, {"sicilia_winters_kingdom", "delphos_oracle_place"})


def prepare():
    add_source_entries("the-winters-tale", "the-two-noble-kinsmen", lexical_entries,
        "Distinguish the two countries from their names used as royal styles. Archidamus speaks for the visiting Bohemian party; Camillo speaks for the Sicilian hosts.",
        inherited_glosses={"kjv_cupbearer": "cupbearer", "kjv_justify_judicial": "justify",
                           "kjv_heifer": "heifer", "kjv_muzzle": "muzzle", "kjv_goad": "goad",
                           "kjv_adulteress": "adulteress", "kjv_shoulder_blade": "shoulder blade",
                           "kjv_plant_cutting": "cutting", "kjv_mint_herb": "mint",
                           "kjv_ethiopian": "Ethiopian", "kjv_brick_block": "brick",
                           "kjv_mole_animal": "mole", "kjv_sect_acts": "sect",
                           "kjv_gallery": "gallery"})


if __name__ == "__main__":
    prepare()
