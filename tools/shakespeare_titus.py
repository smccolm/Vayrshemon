"""The Andronici and the competing Roman and Gothic households."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "procne_philomels_sister": ("prokne", "Procne", "Philomela’s sister, invoked by Titus as the precedent for his revenge on the mother of Lavinia’s attackers."),
    "virginius_roman_father": ("virginiyus", "Virginius", "Roman father invoked by Titus in asking Saturninus to judge a father’s killing of his daughter. Retains the account given by this play."),
    "jubiter_countryman_misnaming": ("jubiter", "Jubiter", "The country fellow’s mispronunciation of Jupiter, whom he takes for someone he might have met. Preserve the distinction from the deity’s name."),
    "cornelia_roman_midwife": ("korneliya", "Cornelia", "The midwife who witnesses the birth of Tamora’s son. Distinct from the Roman mother in Titus’s reading analogy."),
    "muliteus_aaron_countryman": ("muliteus", "Muliteus", "Aaron’s countryman whose wife has just given birth. Aaron proposes exchanging their child for his own."),
    "enceladus_giant": ("enkeladus", "Enceladus", "The giant named by Aaron as an imagined challenger to his defence of his infant son."),
    "typhon_giant": ("tifon", "Typhon", "Mythic figure whose brood Aaron invokes together with Enceladus."),
    "cornelia_mother_of_gracchi": ("korneliya", "Cornelia", "The Roman mother invoked by Titus when he recalls Lavinia reading to young Lucius."),
    "cocytus_underworld_river": ("kokitus", "Cocytus", "The underworld river whose misty mouth Martius compares with the pit where Bassianus lies dead."),
    "cimmerian_darkness_ethnonym": ("kimeriya", "Cimmerian", "Bassianus compares Aaron to the people of the land of darkness in classical poetry. The comparison belongs to Bassianus."),
    "styx_underworld_river": ("stiks", "Styx", "The river of the dead, on whose shore Titus imagines his unburied sons waiting."),
    "solon_athenian_lawgiver": ("solon", "Solon", "The Athenian lawgiver invoked by Marcus while contrasting living success with honor secure at death."),
    "laertes_ithacan_father": ("laertes", "Laertes", "Father of Ulysses in Marcus's account of the burial of Ajax, distinct from the son of Polonius."),
    "caesar_titus_imperial_title": ("sëzar", "Caesar", "The imperial designation used by Bassianus for his late father; it does not identify Julius Caesar."),
    "scythia_ancient_country": ("skitiya", "Scythia", "The country Chiron and Demetrius invoke in their comparison with Rome."),
    "titus_andronici_father": ("titus", "Titus", "The Roman general and father of Lavinia, Lucius, Martius, Quintus and Mutius."),
    "andronicus_roman_family": ("andronikus", "Andronicus", "The family name shared by the general Titus and his brother Marcus. Used alone for Titus in the opening election."),
    "marcus_andronici_tribune": ("markus", "Marcus", "Titus's brother, the tribune who announces the people's choice for emperor."),
    "saturninus_roman_emperor": ("saturninus", "Saturninus", "The late emperor's firstborn son and Bassianus's elder brother."),
    "saturnine_emperor_short": ("saturnin", "Saturnine", "The shorter address for the same emperor Saturninus."),
    "bassianus_roman_prince": ("basianus", "Bassianus", "Younger son of the dead emperor, rival of Saturninus, betrothed to Lavinia."),
    "lavinia_titus_daughter": ("laviniya", "Lavinia", "Daughter of Titus Andronicus and beloved of Bassianus."),
    "lucius_titus_son": ("lusius", "Lucius", "Titus's surviving son and father of young Lucius. Distinct from the child and earlier dramatic namesakes."),
    "lucius_titus_grandson": ("lusius", "Lucius", "Young Lucius, the general's grandson. The source's description 'young' is expressed separately."),
    "mutius_titus_son": ("mutius", "Mutius", "Titus's son who bars his father's way to protect Lavinia's departure."),
    "martius_titus_son": ("martius", "Martius", "Son of Titus, accused with his brother Quintus; distinct from Coriolanus and his child."),
    "quintus_titus_son": ("kwintus", "Quintus", "Son of Titus, accused with his brother Martius. His personal name is distinct from an ordinal."),
    "tamora_goth_queen": ("tamora", "Tamora", "Queen of the Goths, captive mother of Alarbus, Chiron and Demetrius, later empress."),
    "alarbus_tamora_son": ("alarbus", "Alarbus", "Tamora's eldest surviving son at the Roman triumph, selected for sacrifice."),
    "chiron_tamora_son": ("kiron", "Chiron", "Tamora's son and brother of Demetrius, not the mythical centaur."),
    "demetrius_tamora_son": ("demetriw", "Demetrius", "Tamora's son, distinct from the Athenian lover and Antony's Roman follower."),
    "aaron_tamora_companion": ("aharßn", "Aaron", "Tamora's companion and the father of her infant. The name follows the inherited Biblical reading while the person is distinct."),
    "publius_marcus_son": ("publius", "Publius", "Marcus's son who joins the archers and later assists Titus."),
    "caius_andronici_kinsman": ("kaius", "Caius", "A gentleman with the Andronici in the archery scene and at Titus's house."),
    "sempronius_andronici_kinsman": ("sempronius", "Sempronius", "A gentleman named among the archers, distinct from Timon's guest."),
    "valentine_andronici_kinsman": ("valentin", "Valentine", "The man summoned with Caius and Publius at Titus's house."),
    "aemilius_imperial_messenger": ("emilius", "Aemilius", "Messenger for the Roman emperor who approaches Lucius and accompanies the imperial party."),
}

SENSES = {
    "revenge_tamora_disguise": (["revenge"], "Revenge", "proper", "The personified role assumed by Tamora before Titus."),
    "rape_chiron_disguise": (["rape"], "Rape", "proper", "Rape or Rapine, the personified role assumed by Chiron in the visit to Titus."),
    "murder_demetrius_disguise": (["murder"], "Murder", "proper", "The personified role assumed by Demetrius in Tamora’s visit to Titus."),
    "virgo_maiden_stars": (["maiden", "star"], "Virgo", "proper", "The Maiden of the zodiac, in whose lap Titus imagines young Lucius’s shot."),
    "aries_ram_stars": (["ram_sheep", "star"], "Aries", "proper", "The Ram of the zodiac, imagined in Marcus’s story about Taurus."),
    "emperal_countryman_error": (["emperor_roman_throne", "royal"], "emperal", "noun", "The countryman’s mixed form for emperor. His native form combines the imperial title with royal."),
    "tadpole_frog_young": (["kjv_frog", "drama_native_young"], "tadpole", "noun", "A frog’s young, used by Demetrius as an insult for the infant."),
    "ovid_changes_title": (["change", "form"], "Metamorphosis", "proper", "Ovid’s poem, named in the singular in the supplied play. Its native title describes changes of form."),
    "orator_cicero_title": (["orator"], "The Orator", "proper", "The rhetorical work by Tully that Lavinia read to her nephew."),
    "elder_berry_tree": (["drama_native_berry", "tree"], "elder tree", "noun", "The elder whose shadow falls on the pit in the forged letter. The tree is distinct from an older person."),
    "panther_hunted_cat": (["drama_native_leopard"], "panther", "noun", "The large spotted cat named as quarry by Titus and Marcus."),
    "mistletoe_tree_plant": (["tree", "drama_native_berry"], "mistletoe", "noun", "The berry-bearing plant growing on the trees in Tamora’s invented account of the valley."),
    "emperor_roman_throne": (["emperor_dynastic_ruler"], "emperor", "noun", "The Roman imperial office for which the brothers compete and which Saturninus receives."),
    "empress_roman_throne": (["empress_sovereign"], "empress", "noun", "The Roman imperial dignity proposed for Lavinia and then conferred on Tamora."),
    "pantheon_roman_temple": (["all", "god", "temple"], "All-Gods Temple", "proper", "The Roman Pantheon where Saturninus proposes to marry Lavinia. Its title is translated by meaning."),
    "pius_titus_epithet": (["devout"], "Pious", "proper", "The honorific Pius accorded to Titus for services to Rome, rendered by the native word for devotion."),
}


def lexical_entries(language):
    return build_entries(language, NAMES, SENSES, {"styx_underworld_river", "scythia_ancient_country", "cocytus_underworld_river"})


def prepare():
    add_source_entries("titus-andronicus", "timon-of-athens", lexical_entries,
        "Distinguish the two generations named Lucius. Aaron has the inherited name reading and a separate dramatic identity. Translate Pius as an honorific and retain the family name for both brothers.",
        inherited_glosses={"kjv_wool": "wool", "kjv_kinswoman": "kinswoman",
                          "kjv_stump": "stump", "kjv_mourning": "mourning", "kjv_archer": "archer",
                          "kjv_stephen_acts": "Stephen", "kjv_unholy_profane": "unholy"})


if __name__ == "__main__":
    prepare()
