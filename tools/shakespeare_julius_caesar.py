"""Identity and craft vocabulary for the Julius Caesar witness."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


PEOPLE = {
    "flavius_roman_tribune": ("flavius", "Flavius", "The tribune who disperses the holiday crowd with Marullus, distinct from the soldier of the same name."),
    "marullus_roman_tribune": ("marulus", "Marullus", "The tribune who reminds the commoners of their earlier love for Pompey."),
    "calphurnia_caesar_wife": ("kalfurnia", "Calphurnia", "Caesar's wife, whom he asks Antony to touch during the ritual race. The witness spells the name Calphurnia."),
    "portia_brutus_wife": ("portia", "Portia", "The wife of Marcus Brutus and daughter of Cato."),
    "decius_brutus_conspirator": ("desius", "Decius", "Decius Brutus, the conspirator who interprets Calphurnia's dream. Distinct from the Brutus married to Portia."),
    "brutus_decius_surname": ("brutus", "Brutus", "The Brutus surname when explicitly supplied for Decius, not a reference to Marcus Brutus."),
    "cicero_roman_senator": ("sisero", "Cicero", "The senator seen at the feast, remembered in debate in the Capitol."),
    "casca_roman_conspirator": ("kaska", "Casca", "The man who describes the three offers of a crown and takes part in the attack on Caesar."),
    "titinius_brutus_army": ("titinius", "Titinius", "The Roman whom Cassius remembers Caesar calling for a drink and who later rides out to identify the troops."),
    "cinna_conspirator": ("sina", "Cinna", "Cassius's associate entrusted with the anonymous writings, distinct from Cinna the poet."),
    "metellus_cimber_given": ("metelus", "Metellus", "The given component in the witness's name for the conspirator who asks Caesar to recall his brother."),
    "cimber_conspirator": ("simber", "Cimber", "The surname of the conspirator Metellus Cimber, distinct from the brother on whose behalf he petitions."),
    "trebonius_conspirator": ("trebonius", "Trebonius", "The conspirator who later draws Antony away from Caesar."),
    "lucius_brutus_servant": ("lusius", "Lucius", "The young servant Brutus sends to light a taper and check the calendar. Distinct from the elder Brutus who resisted the Tarquins."),
    "caius_cassius_given": ("kaius", "Caius", "Cassius's given name when Brutus urges him to spare Antony."),
    "caius_ligarius_given": ("kaius", "Caius", "Ligarius's given name, distinct from the Caius addressed in the debate about Antony."),
    "ligarius_roman_conspirator": ("ligarius", "Ligarius", "The Roman reproved by Caesar for praising Pompey, who joins Brutus despite his illness."),
    "cato_portia_father": ("kato", "Cato", "Portia's father, to whose reputation she appeals in the orchard, distinct from the young Cato in the army."),
    "publius_roman_senator": ("publius", "Publius", "The senator who greets Caesar at home and is told after the stabbing that he is safe. Distinct from the banished brother of Metellus Cimber."),
    "artemidorus_warning": ("artemidorus", "Artemidorus", "The man who writes and tries to deliver a warning identifying the conspirators."),
    "popilius_roman_senator": ("popilius", "Popilius", "The senator whose good wishes cause Cassius to fear discovery."),
    "lena_popilius_surname": ("lena", "Lena", "The surname Cassius uses for Popilius as he approaches Caesar."),
    "publius_cimber_exile": ("publius", "Publius", "The given name of Metellus Cimber's banished brother, distinct from the senator who attends Caesar."),
    "cimber_exile_surname": ("simber", "Cimber", "The surname of the banished Publius Cimber whose recall the conspirators request."),
    "cinna_roman_poet": ("sina", "Cinna", "The poet seized by the plebeians because he shares a name with a conspirator. He explicitly distinguishes himself from that man."),
    "marcus_brutus_given": ("markus", "Marcus", "Marcus in the name Marcus Brutus, the first conspirator whose hand Antony takes. Distinct from the given name of Antony."),
    "ate_ruin_goddess": ("ate", "Ate", "The figure of ruin and vengeance whom Antony imagines beside Caesar's spirit when he foretells civil war."),
    "nervii_gaul_people": ("nervii", "Nervii", "The people over whom Caesar won the victory Antony recalls when he identifies Caesar's mantle."),
    "publius_antony_nephew": ("publius", "Publius", "Antony's sister's son, marked for death in the proscription. His kinship distinguishes him from the exiled Cimber; the play does not identify him with the senator who greets Caesar."),
    "lucilius_brutus_officer": ("lusilius", "Lucilius", "Brutus's officer who reports on Cassius's reception and later impersonates Brutus on the battlefield. Distinct from the servant Lucius."),
    "pindarus_cassius_servant": ("pindarus", "Pindarus", "Cassius's servant, whose report from the hill precedes Cassius's request for the sword."),
    "lucius_pella_given": ("lusius", "Lucius", "The given name of Pella, accused of taking bribes at Sardis. Distinct from Brutus's servant."),
    "pella_bribe_accusation": ("pela", "Pella", "The surname of the man censured for taking bribes from the Sardians."),
    "messala_brutus_officer": ("mesala", "Messala", "The officer who reports the proscriptions and Portia's death and later finds the dead Cassius with Titinius."),
    "varro_brutus_guard": ("varo", "Varro", "One of the two men who sleep in Brutus's tent on the night of the apparition."),
    "claudius_brutus_guard": ("klaudius", "Claudius", "Varro's fellow guard in Brutus's tent, distinct from the Danish king and the persons of the biblical witness."),
    "epicurus_philosopher": ("epikurus", "Epicurus", "The philosopher whose views Cassius says he formerly held firmly before giving partial credence to omens."),
    "cato_young_soldier": ("kato", "Cato", "The young soldier who announces his father's name and is killed before Lucilius."),
    "marcus_cato_father_given": ("markus", "Marcus", "The given name in the younger Cato's repeated naming of his father Marcus Cato."),
    "strato_brutus_attendant": ("strato", "Strato", "The man who eventually holds Brutus's sword at his request."),
    "volumnius_brutus_friend": ("volumnius", "Volumnius", "Brutus's old schoolfellow, to whom he describes the two apparitions."),
    "labeo_brutus_officer": ("labeo", "Labeo", "The officer ordered with Flavius to set their army in motion."),
    "flavius_brutus_officer": ("flavius", "Flavius", "The officer appearing with Labeo at Philippi, distinct from the tribune in the first street scene."),
    "dardanus_brutus_attendant": ("dardanus", "Dardanus", "An attendant in Brutus's last scene who refuses his request."),
    "clitus_brutus_attendant": ("klitus", "Clitus", "The attendant who reports Statilius's signal and refuses to kill Brutus."),
    "statilius_torch_bearer": ("statilius", "Statilius", "The man who signaled by torch but did not return. Clitus reports that he was either taken or killed."),
}

PLACES = {
    "thasos_burial_place": ("tasos", "Thasos", "The place to which Brutus orders Cassius's body sent for funeral rites outside the camp."),
}

SENSES = {
    "cobbler_shoe_mender": (["shoe", "repairer"], "cobbler", "noun", "The tradesman who repairs shoes. In his opening self-description he also invites the customary sense of an indifferent workman."),
    "sole_shoe_underpart": (["shoe", "bottom"], "shoe sole", "noun", "The lower working surface of a shoe, in the cobbler's play on the source words soles and souls."),
    "awl_leather_tool": (["leather", "needle"], "awl", "noun", "The pointed tool the cobbler uses to make holes in leather. It draws a source sound-play with all and withal."),
    "lupercal_roman_feast": (["wolf", "festival"], "Lupercal", "proper", "The named Roman festival with a ceremonial race at which Caesar asks Antony to touch Calphurnia."),
    "ides_calendar_day": (["middle", "day"], "ides", "noun", "The named Roman calendar day of the warning, March 15 in this play. The source speaks a calendar name, not a written number."),
    "falling_sickness": (["fall", "sickness"], "falling sickness", "noun", "Brutus's name for Caesar's condition after Casca reports a fall and foaming at the mouth. Cassius immediately applies the same words to their political submission."),
    "greek_speech_language": (["greece", "tongue"], "Greek language", "proper", "Cicero's language as reported by Casca, who distinguishes his own incomprehension from the other listeners' understanding."),
    "praetor_judicial_office": (["city", "judge"], "praetor", "noun", "The Roman magistrate whose chair is to receive one of the anonymous papers where Brutus can find it."),
    "elephant_tusked_animal": (["tusk", "nose", "beast"], "elephant", "noun", "The large tusked animal with a prehensile nose, caught by pitfalls in Decius's account of the practices that please Caesar."),
    "forum_speaking_platform": (["speech", "stand"], "public speaking platform", "noun", "The public speaking stand to which the conspirators direct Brutus and from which Antony will address the plebeians in the Forum."),
    "plebeian_forum_citizen": (["common", "citizen"], "plebeian", "noun", "A common citizen of Rome. In the Forum the local witness differentiates four speakers within the wider group."),
    "audience_hiss": (["breath", "scorn"], "hiss in scorn", "verb", "An audience hisses to reject what it dislikes, paired with applause in Casca's comparison to actors."),
    "bee_wing_buzz": (["wing", "drama_native_sound"], "buzz of wings", "noun", "The sound of the Hybla bees, which Brutus says Antony has stolen along with their honey and their sting."),
    "stake_tether_post": (["ground", "staff"], "tethering stake", "noun", "The anchored wooden post of Octavius's comparison to a captive animal bayed at the stake."),
    "mace_striking_club": (["strike", "staff"], "striking mace", "noun", "The heavy striking implement of personified Sleep, made of lead in Brutus's address to slumber."),
}


def lexical_entries(language):
    return build_entries(language, PEOPLE | PLACES, SENSES, set(PLACES))


def prepare():
    add_source_entries("julius-caesar", "henry-viii", lexical_entries,
                       "The tribunes, the shoemaker's trade and the festival enter the opening scene. The inherited identities of Julius Caesar, Antony, Pompey, Marcus Brutus and Cassius carry forward.")


if __name__ == "__main__":
    prepare()
