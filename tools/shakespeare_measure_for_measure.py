"""Names and native speaking names in the Vienna of Measure for Measure."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "angelo_vienna_deputy": ("anjelo", "Angelo", "The duke's deputy. His angelic name becomes a point of contention in Isabella's accusation."),
    "escalus_vienna_lord": ("eskalus", "Escalus", "The elder Viennese lord given a commission subordinate to Angelo's."),
    "lucio_vienna_gallant": ("lusiyo", "Lucio", "Claudio's acquaintance who petitions Isabella and later slanders the duke to his face."),
    "hungary_realm": ("ungariya", "Hungary", "The kingdom whose possible peace with the dukes sets off the gentlemen's military joke."),
    "bohemia_barnardine_birthplace": ("bohemiya", "Bohemia", "The country of Barnardine's birth. The provost says he was reared in Vienna."),
    "claudio_vienna_prisoner": ("klawdiwo", "Claudio", "Isabella's brother, imprisoned for getting his betrothed Juliet pregnant."),
    "juliet_vienna_betrothed": ("julyet", "Juliet", "Claudio's pregnant betrothed. Julietta is the longer form used of the same woman."),
    "julietta_vienna_betrothed": ("julyeta", "Julietta", "The longer form used of Juliet, Claudio's betrothed."),
    "isabella_vienna_novice": ("izabela", "Isabella", "Claudio's sister, seeking admission to the Poor Clares."),
    "isabel_vienna_short": ("izabel", "Isabel", "Isabella's shorter self-address in the hypothetical exchange of places with Angelo; the same novice is meant."),
    "pompey_vienna_servant": ("pompei", "Pompey", "Mistress Overdone's servant. Later Escalus exploits the echo of Pompey the Great."),
    "thomas_vienna_friar": ("tomas", "Thomas", "The friar whom the duke asks for the habit and instruction needed for his disguise."),
    "thomas_tapster_nickname": ("tomas", "Thomas", "The familiar tapster name used of Pompey by his mistress, distinct from Friar Thomas."),
    "peter_vienna_friar": ("peter", "Peter", "Friar Peter, who assists with the duke's public return."),
    "francisca_vienna_nun": ("fransiska", "Francisca", "The nun who explains the order's restrictions to Isabella."),
    "clare_saint_foundress": ("klara", "Clare", "The saint after whom the sisters of Isabella's intended order are named."),
    "mariana_vienna_betrothed": ("mariyana", "Mariana", "Frederick's sister, formerly contracted to Angelo. She takes Isabella's place at the garden house."),
    "frederick_mariana_brother": ("friderik", "Frederick", "Mariana's brother who drowned with her dowry."),
    "lodowick_dukes_disguise": ("lodowik", "Lodowick", "The name the duke assumes in the friar's habit."),
    "barnardine_vienna_prisoner": ("barnardin", "Barnardine", "The long-imprisoned man who refuses to be executed and is ultimately pardoned."),
    "ragozine_dead_pirate": ("ragozin", "Ragozine", "The pirate whose head is sent in Claudio's place after he dies of fever."),
    "varrius_dukes_friend": ("variyus", "Varrius", "The duke's friend who greets him before the public return."),
    "pygmalion_sculptor": ("pigmaliyon", "Pygmalion", "The sculptor whose statue becomes a woman. Lucio applies the myth to Pompey's trade."),
    "bridget_in_lucios_jest": ("brijet", "Bridget", "The woman after whose face paint Lucio asks Pompey."),
    "kate_keepdown_given": ("kat", "Kate", "The mother of Lucio's child, whom he promised to marry according to the bawd."),
    "jacob_feast_name": ("yakob", "Jacob", "The Jacob named alongside Philip in the calendar feast. The witness's name is retained when other editions gloss it as James."),
    "flavius_vienna_contact": ("flaviyus", "Flavius", "The duke's local contact whom Friar Peter is to send first. Distinct from both Roman men named Flavius."),
    "valencius_vienna_contact": ("valensiyus", "Valencius", "One of the Viennese contacts to be told to bring trumpets to the gate."),
    "rowland_vienna_contact": ("roland", "Rowland", "The duke's local contact, distinct from Sir Rowland de Boys and the ballad figure."),
    "crassus_vienna_contact": ("krasus", "Crassus", "The local man named with Valencius and Rowland, distinct from the Roman general."),
}

SENSES = {
    "duke_vienna_ruler": (["duke"], "Duke", "noun", "The ruler of Vienna. Only the rank prints in the speaker and entrance labels."),
    "provost_vienna_prison": (["prison","steward"], "provost", "noun", "The official in charge of the Viennese prison and its condemned prisoners."),
    "overdone_brothel_keeper": (["excess","do"], "Overdone", "proper", "The bawd's speaking name, formed with native excess and do."),
    "mitigation_bawds_nickname": (["relief_ease"], "Mitigation", "proper", "Lucio's ironic alternative address to Mistress Overdone, a name of easing her clients' troubles."),
    "elbow_vienna_constable": (["elbow"], "Elbow", "proper", "The constable. His bodily name remains available for the joke about leaning on justice."),
    "mistress_elbow_wife": (["mistress","elbow"], "Mistress Elbow", "proper", "The constable's wife whose visit to the house is disputed. Her title accompanies the family's anatomical name."),
    "sitting_flesh_buttocks": (["seat","flesh"], "buttocks", "noun", "Flesh on which a person sits. The native seat-flesh compound supplies Pompey's low-register name and Escalus's reply."),
    "bum_pompey_surname": (["seat","flesh"], "Bum", "proper", "Pompey's surname. Its form matches the native word for buttocks in Escalus's joke about Pompey the Great."),
    "froth_vienna_gentleman": (["foam"], "Froth", "proper", "The gentleman brought in by Elbow. His airy name hints at insubstantiality."),
    "abhorson_executioner": (["abhor","son"], "Abhorson", "proper", "The executioner's speaking name with its native components of abhorrence and sonship. The additional source-language insult echo is not identical."),
    "kersey_workaday_cloth": (["wool_material","cloth"], "kersey", "noun", "The plain woollen cloth the gentleman contrasts with French velvet."),
    "sciatica_hip_pain": (["hip","pain"], "sciatica", "noun", "The deep hip pain the gentleman asks the bawd about."),
    "trout_river_fish": (["spot","stream","fish_creature"], "trout", "noun", "The spotted stream fish in Pompey's sexual image of fishing another person's private water."),
    "star_circle_zodiac": (["star","circle"], "zodiac", "noun", "The solar circuit through the stars that Claudio uses to count the years of the law's disuse."),
    "ticktack_table_game": (["dice","game"], "tick-tack", "noun", "A tables game played with dice. Lucio makes losing a life at a game into a sexual quibble; the English sound of its name has no direct equivalent."),
    "sweat_epidemic": (["sweat","sickness"], "the sweat", "noun", "The sweating sickness in the bawd's list of things that have cost her customers."),
    "prioress_nuns_superior": (["nun","head"], "prioress", "noun", "The superior whose presence is required for a vowed sister to speak to a man."),
    "birch_rod_tree": (["rod","tree"], "birch", "noun", "The tree from which the threatening twigs are cut. The duke compares unused statutes to the display of a rod."),
    "prune_dried_plum": (["dry","plum"], "prune", "noun", "The dried plums Pompey stews; their stones and the price of the dish figure in his account."),
    "china_dish_porcelain": (["fine","clay_material","vessel"], "china dish", "noun", "Fine ceramic tableware beyond the price of the household's ordinary dish. A material designation for the serving vessel."),
    "beheading_block": (["head","wood"], "beheading block", "noun", "The wooden support under a condemned person's head, used in Isabella's image of twenty bloody blocks and in the preparations for execution."),
    "serpigo_skin_affliction": (["skin","sickness"], "serpigo", "noun", "A spreading skin eruption in the disguised duke's list of afflictions; the species of disease is not specified."),
    "prenzie_outward_austerity": (["devout","appearance"], "prenzie", "adjective", "The witness repeats this uncertain adjective for Angelo and for trimmings that disguise a damned body. The native expression reads it as outwardly pious. Priestly and princely are among the alternative editorial readings."),
    "saint_lukes_place": (["saint","kjv_luke_physician_colossians"], "Saint Luke’s", "proper", "The locality the duke names when telling Isabella where to find him. The saint's name identifies the place; the saint does not appear."),
    "keepdown_kate_surname": (["keep","down"], "Keepdown", "proper", "Kate's speaking surname. Mistress Overdone says Kate bore Lucio's child."),
    "picklock_tool": (["lock","open"], "picklock", "noun", "The lock-opening tool found on Pompey and sent to the deputy."),
    "stockfish_dried_fish": (["dry","fish_creature"], "stockfish", "noun", "Dried fish in Lucio's absurd account of Angelo's parentage; distinct from the speaking surname in Love's Labor's Lost."),
    "tundish_liquid_funnel": (["pour","mouth"], "tundish", "noun", "A funnel for filling a bottle, used by Lucio for a sexual insinuation."),
    "clack_dish_alms": (["knock","bowl"], "clack-dish", "noun", "The noisy alms dish into which Lucio says the duke put a ducat."),
    "craft_mystery_trade": (["trade","secret"], "mystery", "noun", "A skilled calling with its own mysteries. Abhorson and Pompey debate whose trade merits the title."),
    "curfew_bell": (["night","bell"], "curfew", "noun", "The evening bell from which the provost reckons the lack of visitors."),
    "rash_prison_customer": (["rash"], "Rash", "proper", "The indebted customer who turned the paper and ginger into very little ready money."),
    "caper_prison_customer": (["gambol"], "Caper", "proper", "The customer sued by the cloth merchant. His speaking name is a playful leap."),
    "pile_mercers_name": (["cloth_nap_surface"], "Pile", "proper", "The cloth-pile element of Master Three-pile. His preceding spoken Unta three is part of the name."),
    "dizzy_prison_customer": (["dizzy"], "Dizzy", "proper", "The young man listed among the bawd's former customers."),
    "deep_vow_prison_customer": (["deep","vow"], "Deep-vow", "proper", "The speaking name joins depth and oath."),
    "copper_spur_customer": (["kjv_copper","spur"], "Copper-spur", "proper", "The speaking name preserves the metal and the rider's spur."),
    "starve_lackey_customer": (["starve","footservant_lackey"], "Starve-lackey", "proper", "The rapier-and-dagger man Pompey names in prison."),
    "drop_heir_customer": (["drop","heir"], "Drop-heir", "proper", "The young customer who killed Pudding."),
    "pudding_slain_man": (["pudding_dish"], "Pudding", "proper", "The man killed by Drop-heir. His speaking name denotes the dish."),
    "forth_light_tilter": (["forth","light"], "Forth-light", "proper", "The jouster in Pompey's list. Preserve the literal components of the supplied name."),
    "shoe_tie_traveler": (["shoe","tie"], "Shoe-tie", "proper", "The well-dressed traveler with a native footwear name."),
    "can_drinkers_name": (["cup"], "Can", "proper", "The drinking vessel in Half-can, the man said to have stabbed Pots. His preceding Unta half is part of the name."),
    "pots_stabbed_man": (["cooking_pot"], "Pots", "proper", "The man stabbed by Half-can. Use native pot with the plural ending in his name."),
    "coin_striking_die": (["coin_currency","impress"], "coin die", "noun", "The device for impressing a coin's image; a figurative forbidden die in Angelo's comparison of procreation with illicit minting."),
    "handle_question_touch": (["hand","try"], "handle", "verb", "Handle a person under examination. Lucio deliberately gives the same expression a sexual reading."),
    "baldpate_friars_nickname": (["bald_bare","head"], "Baldpate", "proper", "Lucio's derisive name for the man in a friar's hood. The speaker does not know he is addressing the duke."),
    "league_road_distance": (["way","measure"], "league", "noun", "The league of distance to the consecrated fountain. A native way-measure designation for the source unit, without a conversion or an inferred length."),
    "hallowmas_feast": (["all","saint","feast"], "Hallowmas", "proper", "The feast of All Saints; Froth distinguishes its eve from the day Pompey first suggests."),
    "bunch_grapes_room": (["bunch","grape"], "Bunch of Grapes", "proper", "The named tavern room where Froth prefers to sit."),
}


def lexical_entries(language):
    return build_entries(language, NAMES, SENSES, {"hungary_realm","bohemia_barnardine_birthplace"})


def prepare():
    add_source_entries("measure-for-measure", "macbeth", lexical_entries,
        "The Duke's office and friar's alias remain distinct. Julietta and Juliet refer to the same woman. The widow's and constable's speaking names use native roots.")


if __name__ == "__main__":
    prepare()
