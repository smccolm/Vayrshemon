"""Twelfth Night personal names, assumed identities and speaking surnames."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "viola_messaline_twin": ("viyola", "Viola", "The shipwrecked twin who takes service with Orsino."),
    "cesario_viola_disguise": ("sesariyo", "Cesario", "The public identity Viola assumes in Illyria."),
    "olivia_illyrian_countess": ("oliviya", "Olivia", "The countess whom Orsino courts through Viola."),
    "orsino_illyrian_duke": ("orsino", "Orsino", "Ruler of Illyria, addressed by the source as duke and count."),
    "curio_orsino_gentleman": ("kuriyo", "Curio", "Orsino's attendant who proposes the hart hunt."),
    "valentine_orsino_gentleman": ("valentin", "Valentine", "Orsino's gentleman who reports Olivia's refusal to meet him."),
    "maria_olivia_attendant": ("marya", "Maria", "Olivia's attendant who writes the counterfeit letter."),
    "mary_maria_familiar": ("meri", "Mary", "Familiar name used for Maria within Olivia's household."),
    "marian_toby_call": ("mariyan", "Marian", "Name Toby calls while asking for wine in Olivia's house."),
    "toby_olivia_kinsman": ("tobi", "Toby", "Olivia's kinsman, the knight who encourages Andrew's courtship."),
    "andrew_illyrian_suitor": ("andru", "Andrew", "The visiting knight whom Sir Toby lives upon."),
    "malvolio_olivia_steward": ("malvoliyo", "Malvolio", "Olivia's steward, tricked into mistaking Maria's letter for hers."),
    "feste_olivia_jester": ("feste", "Feste", "The singer and jester addressed as Fool in the dialogue."),
    "fabian_olivia_gentleman": ("fabiyan", "Fabian", "Gentleman in Olivia's service who witnesses the letter trick."),
    "sebastian_viola_twin": ("sebastyan", "Sebastian", "Viola's twin, rescued by Antonio."),
    "sebastian_messaline_father": ("sebastyan", "Sebastian", "The dead father of the twins, named for their recognition."),
    "roderigo_sebastian_alias": ("roderigo", "Roderigo", "The name Sebastian had given Antonio before telling his own."),
    "antonio_sebastian_friend": ("antoniyo", "Antonio", "Seafarer who rescues Sebastian and mistakes Viola for him."),
    "messaline_twins_home": ("mesalin", "Messaline", "Place of origin given by both twins."),
    "arion_dolphin_rider": ("ariyon", "Arion", "Musician on a dolphin invoked by the ship's captain."),
    "mall_picture_subject": ("mal", "Mall", "Woman in the picture which Toby says takes dust behind a curtain."),
    "castile_toby_formula": ("kastilya", "Castile", "Place behind the deliberately obscure Castiliano vulgo in Toby's interruption."),
    "quinapalus_fools_authority": ("kwinapalus", "Quinapalus", "Authority cited by Feste to license his witticism."),
    "pigrogromitus_jesters_tale": ("pigrogromitus", "Pigrogromitus", "Extravagant name in Andrew's recollection of Feste's patter."),
    "vapians_jesters_people": ("vapiyan", "Vapian", "Invented people in the same recollection."),
    "queubus_jesters_equator": ("kwebus", "Queubus", "Invented name attached to the equinoctial line."),
    "peg_ramsey_song": ("peg ramzi", "Peg-a-Ramsey", "Name taken from a tune in Toby's teasing of Malvolio."),
    "penthesilea_amazon": ("pentesileya", "Penthesilea", "Amazon queen invoked in Toby's teasing farewell to Maria."),
    "strachy_malvolio_story": ("straki", "Strachy", "Malvolio's example of a lady who married beneath her rank. The original title is obscure."),
    "sowter_letter_hound": ("sauter", "Sowter", "Name Fabian gives the hound following the counterfeit letter's scent."),
    "capilet_andrew_horse": ("kapilet", "Capilet", "Andrew's gray horse offered to avert the duel."),
    "topas_feste_disguise": ("topas", "Topas", "Clerical identity assumed by Feste when speaking to the imprisoned steward."),
    "prague_hermit_city": ("prag", "Prague", "City in Feste's tale of a hermit."),
    "gorboduc_legendary_king": ("gorboduk", "Gorboduc", "King named in the supposed hermit's address to a niece."),
    "bennet_bell_saint": ("benet", "Bennet", "Saint whose bells Feste evokes when counting coins."),
    "candy_cretan_port": ("kandi", "Candy", "The Cretan place named as the point of origin of the Phoenix's freight."),
    "titus_orsino_nephew": ("titus", "Titus", "Orsino's young nephew who lost a leg in a sea fight."),
    "dick_illyrian_surgeon": ("dik", "Dick", "Surgeon Toby asks for after the fight."),
    "ware_great_bed_town": ("wer", "Ware", "English town whose famously large bed Toby compares to a sheet of writing paper."),
    "browne_separatist_name": ("braun", "Browne", "Name underlying Andrew's reference to a Brownist."),
}


def lexical_entries(language):
    senses = {
        "belch_toby_surname": (["mouth", "wind"], "Belch", "proper", "Toby's comic surname, given a native mouth-wind image."),
        "aguecheek_andrew_surname": (["fever", "cheek"], "Aguecheek", "proper", "Andrew's speaking surname, carried through the native words for fever and cheek."),
        "agueface_toby_misnaming": (["fever", "face"], "Agueface", "proper", "Toby changes cheek to face in Andrew's surname."),
        "accost_andrew_misnaming": (["approach"], "Accost", "proper", "Andrew hears Toby's command to approach as Maria's name."),
        "catch_voices_song": (["catch", "song"], "catch (round)", "noun", "A part-song whose voices enter by turns. The same native catch root is heard in the dog joke."),
        "opal_changing_gem": (["change", "light", "gem"], "opal", "noun", "Gem whose changing color figures Orsino's changing mind."),
        "patience_monument_figure": (["patience"], "Patience", "proper", "The personification carved on a monument in Viola's account of her father's daughter."),
        "elephant_illyrian_inn": (["drama_native_elephant_tusked_animal"], "Elephant (inn)", "proper", "Illyrian inn in the south suburbs at which Antonio arranges the travelers' board."),
        "phoenix_illyrian_ship": (["phoenix"], "Phoenix (ship)", "proper", "Ship Antonio captured with its cargo from Candy."),
        "tiger_illyrian_ship": (["tiger"], "Tiger (ship)", "proper", "Ship boarded in the action in which Orsino's nephew lost his leg."),
    }
    entries, glosses = build_entries(language, NAMES, senses, {"messaline_twins_home", "prague_hermit_city", "candy_cretan_port", "ware_great_bed_town"})
    for symbol, form in {"m": "em", "p": "pi"}.items():
        key = "school_source_letter_" + symbol
        entries[key] = dict(form=form, roman=language.reading(form), pos="noun",
            meaning="Spoken name of the source letter " + symbol.upper() + " in Malvolio's reading of the forged letter.",
            semanticId="lex." + key, origin="Quoted foreign letter-name adapted for the dramatic recitation.",
            usageScope="later-standard", status="authored", historicalForms=[])
        glosses[key] = "letter " + symbol.upper()
    return entries, glosses


def prepare():
    add_source_entries("twelfth-night", "troilus-and-cressida", lexical_entries,
        "Preserve the names of the twins and their father, Viola's Cesario, Sebastian's Roderigo and Feste's clerical disguise. Translate the meanings of the speaking surnames and the mistaken name Accost.",
        inherited_glosses={"kjv_box_tree": "box tree", "kjv_brimstone": "brimstone", "kjv_badger": "badger",
                          "kjv_legion_named": "Legion", "kjv_beelzebub": "Beelzebub"})


if __name__ == "__main__":
    prepare()
