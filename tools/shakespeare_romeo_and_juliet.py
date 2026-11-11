"""Veronese households, speakers and readings in Romeo and Juliet."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "romeo_montague_son": ("rom×o", "Romeo", "Montague's son, who marries Juliet."),
    "juliet_capulet_daughter": ("julyet", "Juliet", "Capulet's daughter. Distinct from Claudio's betrothed in Vienna."),
    "jule_nurse_pet_name": ("jul", "Jule", "The Nurse's familiar short name for Juliet."),
    "montague_verona_house": ("montagyu", "Montague", "Romeo's father and his family name. Distinct from the Yorkist lord."),
    "capulet_verona_house": ("kapulet", "Capulet", "Juliet's father and the family name in Verona. Distinct from Diana's name Capilet."),
    "capel_family_short": ("kapel", "Capel", "Short form of the same Capulet family name in the name of the tomb."),
    "verona_city": ("verßna", "Verona", "The city of the two feuding households."),
    "mantua_exile_city": ("mantwa", "Mantua", "The city of Romeo's exile, to which the Friar's letter fails to travel."),
    "sampson_capulet_man": ("samson", "Sampson", "Capulet's sword-bearing servant who bites his thumb."),
    "gregory_capulet_man": ("gregori", "Gregory", "Sampson's companion in the opening street encounter."),
    "abram_montague_man": ("abram", "Abram", "Montague's servant in the street quarrel. Distinct from the biblical Abram."),
    "balthasar_romeo_man": ("baltasar", "Balthasar", "Romeo's servant, who saw Juliet buried and brings the report."),
    "benvolio_verona_kinsman": ("benvolyo", "Benvolio", "Montague's kinsman, who draws to separate the fighters."),
    "tybalt_capulet_kinsman": ("tibalt", "Tybalt", "The Capulet kinsman who kills Mercutio and is slain by Romeo."),
    "petruchio_tybalt_companion": ("petruÑyo", "Petruchio", "Tybalt's companion in Verona. Distinct from the suitor in The Taming of the Shrew."),
    "escalus_verona_prince": ("eskalus", "Escalus", "Prince of Verona, who judges the quarrel. Distinct from the Viennese lord."),
    "paris_juliet_suitor": ("paris", "Paris", "The prince's kinsman who seeks Juliet's hand. Distinct from the Trojan and the city."),
    "mercutio_romeo_friend": ("merkutyo", "Mercutio", "The prince's kinsman and Romeo's friend."),
    "rosaline_verona_beloved": ("rozalin", "Rosaline", "The woman Romeo loves before meeting Juliet. Distinct from the French courtier."),
    "lawrence_verona_friar": ("lorens", "Lawrence", "The friar who marries Juliet and Romeo, gives her the vial, and testifies to the Prince."),
    "john_verona_friar": ("jon", "John", "The friar whose journey is stopped by quarantine."),
    "peter_juliet_household": ("peter", "Peter", "Servant in Juliet's household and companion to the Nurse."),
    "susan_nurse_child": ("suzan", "Susan", "The Nurse's deceased child who was the same age as Juliet."),
    "mab_fairy_queen": ("mab", "Mab", "The fairy queen and midwife of Mercutio's account of dreams."),
    "martino_verona_guest": ("martino", "Martino", "Named with his wife and daughters on the feast list."),
    "anselme_verona_guest": ("anselm", "Anselme", "The count named with his sisters on the feast list."),
    "vitruvio_widow_husband": ("vitruvyo", "Vitruvio", "His widow is named on the invitation list."),
    "placentio_verona_guest": ("plasentyo", "Placentio", "Named with his nieces on the invitation list."),
    "valentine_mercutio_brother": ("valentin", "Valentine", "Mercutio's brother, named on the invitation list."),
    "livia_verona_guest": ("livya", "Livia", "Named after Rosaline among the invited guests."),
    "valentio_verona_guest": ("valentyo", "Valentio", "The guest identified as Tybalt's cousin."),
    "lucio_verona_guest": ("lusyo", "Lucio", "Named with Helena on the list. Distinct from Vienna's Lucio."),
    "helena_verona_guest": ("helena", "Helena", "The guest called lively, distinct from the Helena of Athens."),
    "lucentio_verona_wedding": ("lusentyo", "Lucentio", "The past wedding by which Capulet dates his last appearance in a mask."),
    "tiberio_verona_father": ("tiberyo", "Tiberio", "Old Tiberio, whose son the Nurse identifies to Juliet at the feast."),
    "susan_grindstone_guest": ("suzan", "Susan", "Susan Grindstone, to be admitted with Nell. Distinct from the Nurse's dead child."),
    "nell_verona_guest": ("nel", "Nell", "The woman to be admitted with Susan Grindstone."),
    "anthony_feast_man": ("antoni", "Anthony", "Called with Potpan while the feast is being prepared."),
    "abraham_cupid_nickname": ("avrÅham", "Abraham", "Mercutio's nickname for Cupid in the transmitted reading Young Abraham Cupid. It echoes the inherited name without identifying Cupid with the biblical patriarch."),
    "popering_pear_name": ("popering", "pop’rin", "Name of the pear in Mercutio's obscene comparison with the medlar."),
    "francis_friars_saint": ("fransis", "Francis", "The saint invoked by Friar Lawrence, distinct from the Friar Francis of Messina."),
    "petrarch_love_poet": ("petrark", "Petrarch", "The poet whose measures Mercutio says will suit Romeo, and Laura's poet."),
    "laura_petrarch_beloved": ("låra", "Laura", "Petrarch's beloved in Mercutio's list of comparisons."),
    "angelica_household_address": ("anjelika", "Angelica", "Capulet's address while Lady Capulet and the Nurse are both present. The line does not identify which woman he addresses."),
    "simon_verona_musician": ("simon", "Simon", "The first musician addressed as Simon Catling. Distinct from the biblical Simon and the earlier dramatic Simons."),
    "hugh_verona_musician": ("hyu", "Hugh", "The second musician addressed as Hugh Rebeck."),
    "james_verona_musician": ("jemz", "James", "The third musician addressed as James Soundpost, whom Peter identifies as the singer."),
    "jack_musicians_address": ("jak", "Jack", "The second musician's familiar address in the exit exchange. It need not displace the name Simon used earlier."),
    "re_solmization_syllable": ("r×", "re", "The foreign sung syllable re in Peter's threat to re the musicians. Localized as a named musical syllable, without assigning an absolute pitch."),
    "fa_solmization_syllable": ("fÅ", "fa", "The foreign sung syllable fa in Peter's parallel threat. The musician answers by turning the two syllables back into notes."),
}

SENSES = {
    "freetown_verona_court": (["free", "town"], "Free-town", "proper", "The translated place-name of the Prince's ordinary judgment seat."),
    "coal_bearing_insult": (["carry", "coal"], "bear insults", "verb", "An ignominious coal porter's burden used to signify submitting to insults. The literal coals are repeated in the reply."),
    "coal_carrier_worker": (["coal", "carry", "person"], "collier", "noun", "The person who bears or deals in coals in Gregory's literal retort."),
    "dried_fish_poor_john": (["dry", "fish"], "dried fish", "noun", "Poor-john, the cheap dried fish Gregory opposes to Sampson's boast about flesh."),
    "maiden_head_wordplay": (["maid", "head"], "maidenhead", "noun", "The maid's head in Sampson's verbal threat and, through his pun, virginity. The second sense is supplied in the same line."),
    "lammas_loaf_feast": (["bread", "feast"], "Lammas", "proper", "The loaf feast whose eve the Nurse identifies as Juliet's birthday."),
    "shoe_last_form": (["shoe", "form"], "shoe last", "noun", "The model on which a shoemaker shapes a shoe. The servant mistakenly assigns the last to a tailor."),
    "yardstick_cloth_worker": (["cloth", "measure", "staff"], "yardstick", "noun", "The tailor's measuring rod, mistakenly assigned to the shoemaker."),
    "shoemaker_craft": (["shoe", "make", "person"], "shoemaker", "noun", "The maker of shoes in the servant's mixed-up list of trades."),
    "potpan_feast_man": (["cooking_pot", "kjv_pan_cooking"], "Potpan", "proper", "The servingman's kitchen nickname, rendered with the two vessel words."),
    "grindstone_guest_name": (["grind_crush", "stone"], "Grindstone", "proper", "The descriptive surname of the Susan admitted to the feast."),
    "marchpane_almond_sweet": (["kjv_almond", "sweetmeat"], "marchpane", "noun", "The almond sweet a servingman wants saved for him."),
    "echo_nymph_cave": (["echo"], "Echo", "proper", "The personified Echo whose cave and airy tongue Juliet imagines. Her name uses the native echo root."),
    "slip_false_coin": (["false", "coin_currency"], "false coin", "noun", "The slip as a counterfeit coin. Mercutio also uses it for Romeo slipping away."),
    "roe_fish_eggs": (["fish", "egg"], "roe", "noun", "Fish eggs, which music and verse cannot restore to the dried herring in Mercutio's taunt."),
    "pink_courtesy_flower": (["flower"], "pink", "noun", "The flower called a pink serves as Mercutio's flower of courtesy. Romeo turns to the flower pattern of his shoe."),
    "minim_music_rest": (["music", "rest"], "minim rest", "noun", "A written rest in Mercutio's parody of Tybalt keeping musical time as he fences."),
    "back_thrust_fencing": (["reverse", "thrust"], "reverse thrust", "noun", "The punto reverso of Mercutio's catalogue of fencing terms."),
    "foreign_r_letter": (["staff", "kjv_loop", "leg"], "letter R", "noun", "The foreign written R, described by its upright, upper loop and leg. The Nurse associates its sound with a dog's growl when she asks about the original names Romeo and rosemary."),
    "catling_musician_byname": (["gut_music_string"], "Catling", "proper", "The musical surname means an instrument string of gut."),
    "rebeck_musician_byname": (["fiddle_bowed"], "Rebeck", "proper", "The second musician's surname names a bowed string instrument."),
    "soundpost_musician_byname": (["sound", "staff"], "Soundpost", "proper", "The musician's surname names the internal upright support used to transmit the sound of a bowed instrument."),
    "quince_fruit_kitchen": (["gold", "scent", "fruit"], "quince", "noun", "The fragrant fruit requested for cooking with dates. Distinct from Peter Quince's surname."),
    "mantua_apothecary": (["medicine", "mix", "person"], "apothecary", "noun", "The poor compounder of medicines in Mantua who sells Romeo the poison."),
    "alligator_shop_specimen": (["broad", "jaw", "crocodile_creature"], "alligator", "noun", "The broad-jawed crocodilian displayed as a stuffed specimen in the apothecary's shop."),
    "iron_crow_prybar": (["iron", "lift", "bar"], "crowbar", "noun", "The iron prying tool used at the Capulet tomb. Distinct from the crow bird and the crowing cock."),
}


def lexical_entries(language):
    return build_entries(language, NAMES, SENSES, {"verona_city", "mantua_exile_city"})


def prepare():
    add_source_entries("romeo-and-juliet", "richard-iii", lexical_entries,
                       "Localize the Veronese households and use readable English glosses for the inherited terms in the play.",
                       inherited_glosses={
                           "kjv_garment_collar": "collar", "kjv_tool": "tool", "kjv_wean": "wean",
                           "kjv_teat": "teat", "kjv_testicle": "testicle", "kjv_midwife": "midwife",
                           "kjv_grasshopper": "grasshopper", "kjv_driver": "driver", "kjv_hazel": "hazel",
                           "kjv_scrape": "scrape", "kjv_pentecost_acts": "Pentecost", "kjv_trespass": "trespass",
                           "kjv_baptize": "baptize", "kjv_stumble": "stumble", "kjv_depth": "depth",
                           "kjv_mast": "mast", "kjv_poultice": "poultice", "kjv_message": "message",
                           "kjv_easter_acts": "Easter", "kjv_well": "water-well", "kjv_disobedient": "disobedient",
                           "kjv_dish": "dish", "kjv_rattle": "rattle", "kjv_provisions": "provisions",
                           "kjv_cock_crow": "crow", "kjv_martyr_acts": "martyr", "kjv_tortoise": "tortoise",
                           "kjv_mattock": "mattock", "kjv_righteous": "righteous",
                       })


if __name__ == "__main__":
    prepare()
