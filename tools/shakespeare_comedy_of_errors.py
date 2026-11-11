"""Twin households and the ports, offices and currencies of The Comedy of Errors."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "solinus_ephesus_duke": ("solinus", "Solinus", "Duke of Ephesus, who sentences Egeon and later witnesses the reunion."),
    "egeon_syracuse_father": ("ejeon", "Egeon", "Merchant of Syracuse, husband of Emilia and father of the two men named Antipholus."),
    "emilia_ephesus_abbess": ("emilya", "Emilia", "Egeon's wife, revealed as the abbess. Distinct from Emilia in Othello."),
    "antipholus_syracuse_twin": ("antifolus", "Antipholus", "Egeon's son travelling from Syracuse in search of his brother. The twins share this spoken name."),
    "antipholus_ephesus_twin": ("antifolus", "Antipholus", "The son raised in Ephesus and married to Adriana. He shares his brother's spoken name."),
    "dromio_syracuse_twin": ("dromyo", "Dromio", "The servant who travels with the Syracusan Antipholus. Same spoken name as his twin."),
    "dromio_ephesus_twin": ("dromyo", "Dromio", "The Ephesian servant sent to fetch his master for dinner. Same spoken name as his twin."),
    "adriana_ephesus_wife": ("adryana", "Adriana", "Wife of the Ephesian Antipholus and sister of Luciana."),
    "luciana_adriana_sister": ("lusyana", "Luciana", "Adriana's sister, pursued by the visiting Antipholus."),
    "angelo_ephesus_goldsmith": ("anjelo", "Angelo", "The Ephesian goldsmith who delivers the chain to the visiting twin. Distinct from the deputy in Vienna."),
    "balthasar_ephesus_merchant": ("baltasar", "Balthasar", "The merchant who dines with the Ephesian Antipholus. Distinct from Romeo's servant."),
    "luce_adriana_household": ("lus", "Luce", "The household speaker called Luce at the barred door. The later cook is called Nell in the dialogue."),
    "nell_comedy_kitchen": ("nel", "Nell", "The kitchen woman's name in Dromio's geographic description and his pun on the cloth ell. Keep the source's separate use of Luce."),
    "epidamium_trade_city": ("epidamium", "Epidamium", "The trading city where the twins were born. Keep the local spelling and distinguish Epidaurus, named separately in the rescue account."),
    "epidaurus_rescue_port": ("epidårus", "Epidaurus", "The port named for one approaching ship in Egeon's account. The abbess later speaks of men from Epidamium."),
    "menaphon_dukes_uncle": ("menafon", "Menaphon", "The duke's uncle, said by the Ephesian Antipholus to have brought him to the town."),
    "maud_ephesus_household": ("måd", "Maud", "The first household name Dromio calls outside the barred door."),
    "bridget_ephesus_household": ("brijet", "Bridget", "Called by the Ephesian Dromio, distinct from the woman in Lucio's jest."),
    "marian_ephesus_household": ("marian", "Marian", "One of the household names in the call at the door."),
    "ciceley_ephesus_household": ("siseli", "Ciceley", "One of the names Dromio calls from the street."),
    "gillian_ephesus_household": ("jilyan", "Gillian", "The penultimate household name in Dromio's list."),
    "ginn_ephesus_household": ("jin", "Ginn", "The last household name Dromio calls. Distinct from Gillian."),
    "america_dromio_world": ("amerika", "America", "America in Dromio's imagined map of the kitchen woman's body."),
    "indies_dromio_america": ("indiz", "Indies", "The Indies as explicitly paired with America in Dromio's map."),
    "dowsabel_kitchen_byname": ("dåsabel", "Dowsabel", "Dromio's playful name for the kitchen woman who claimed him. He previously called her Nell; the two are not new characters."),
    "lapland_dromio_place": ("laplant", "Lapland", "The region from which the visiting Antipholus imagines the local sorcerers came."),
    "pinch_ephesus_schoolmaster": ("pinÛ", "Pinch", "The schoolmaster called Doctor Pinch who claims to exorcise the Ephesian master and servant."),
}

SENSES = {
    "syracusan_dramatic_citizen": (["kjv_syracuse_acts", "person"], "Syracusan", "noun", "A native of Syracuse in the play's reciprocal ban on trade. Reuses the sealed place name."),
    "guilder_source_coin": (["gold", "coin_currency"], "guilder", "noun", "The named currency the detained merchants lacked. The speech supplies no exchange rate into marks."),
    "mark_ephesus_account": (["account", "silver"], "mark", "noun", "The play's mark of account for the ransom and Egeon's assets. It expresses no conversion into guilders, ducats or historical Ephesian coinage."),
    "jailer_ephesus_office": (["prison", "guard"], "jailer", "noun", "The keeper ordered to take Egeon into custody."),
    "trade_factor_comedy": (["trade", "act", "person"], "factor", "noun", "The merchant's representative who looked after his trading goods at Epidamium."),
    "goldsmith_ephesus_trade": (["gold", "work", "person"], "goldsmith", "noun", "The craft practised by Angelo, maker of the chain."),
    "centaur_inn_ephesus": (["centaur"], "Centaur", "proper", "The sign of the inn at which the visitors have deposited the money. Distinguish Adriana's home, the Phoenix."),
    "phoenix_ephesus_house": (["phoenix"], "Phoenix", "proper", "The mythical bird is the house sign to which Adriana sends for her Ephesian husband."),
    "crupper_saddle_strap": (["tail", "strap"], "crupper", "noun", "The strap that passes under the tail to secure the saddle. Sixpence was paid to the saddler."),
    "baste_meat_and_beat": (["wet", "beat"], "basting", "noun", "Dromio links wetting roast meat with having received a beating. The same theatrical compound returns with dry in his next joke."),
    "tiger_ephesus_inn": (["tiger"], "Tiger", "proper", "The inn where Balthasar proposes that the excluded party dine."),
    "porpentine_ephesus_house": (["porcupine_quilled"], "Porpentine", "proper", "The house where the Ephesian Antipholus knows the hostess and plans to give the chain."),
    "market_fair_assembly": (["market", "gather"], "fair", "noun", "A gathering for trade. In the Duke's decree marts and fairs are places Syracusan and Ephesian merchants frequent."),
    "carat_goldsmith_weight": (["gold", "weight", "part"], "carat", "noun", "A fine unit of weight used on the goldsmith's note. The dialogue gives neither a number of carats nor a modern gram equivalent."),
    "courtesan_porpentine_house": (["payment", "companion"], "courtesan", "noun", "The hostess at the Porpentine who seeks the ring lent to the Ephesian Antipholus and expects his chain."),
    "sergeant_debt_arrest": (["debt", "officer"], "sergeant", "noun", "The civil officer who serves an arrest for debt. Dromio plays on his uniform, hunting and soldiering."),
    "expedition_comedy_ship": (["hurry"], "Expedition", "proper", "The departing bark given the speaking name Expedition in contrast with the hoy Delay."),
    "delay_comedy_hoy": (["delay"], "Delay", "proper", "Dromio calls the enforced wait a hoy named Delay, in opposition to the departing Expedition."),
    "limbo_infernal_confinement": (["prison", "spirit"], "limbo", "noun", "The place of confinement for souls with which Dromio compares his master's arrest."),
    "bass_viol_comedy": (["low", "string", "music"], "bass viol", "noun", "The low string instrument in a leather case to which the officer is compared."),
    "durance_prison_cloth": (["endure", "cloth"], "durance", "noun", "Durable cloth in Dromio's suits of durance. The accompanying captivity phrase gives the punishment sense of the pun."),
    "abbess_religious_head": (["holy", "mother", "head"], "abbess", "noun", "Head of the priory who offers the visitors sanctuary. The stage uses her office before revealing that she is Emilia."),
    "gossip_birth_sponsor": (["birth", "witness"], "birth sponsor", "noun", "A sponsor or companion at a birth celebration. The abbess invites the household to a gossips' feast and the Duke accepts that role."),
}


def lexical_entries(language):
    return build_entries(language, NAMES, SENSES, {"epidamium_trade_city", "epidaurus_rescue_port",
        "america_dromio_world", "indies_dromio_america", "lapland_dromio_place"})


def prepare():
    add_source_entries("the-comedy-of-errors", "romeo-and-juliet", lexical_entries,
        "Give the pairs of twins distinct identities and shared spoken names. Use the established biblical place names and keep the two rescue ports distinct.",
        inherited_glosses={
            "kjv_syracuse_acts": "Syracuse", "kjv_ephesus_acts": "Ephesus", "kjv_corinth_acts": "Corinth",
            "kjv_bay_water": "bay", "kjv_goods": "goods", "kjv_sailor": "sailor",
            "kjv_shipwreck_corinthians": "shipwreck", "kjv_greece_zechariah": "Greece", "kjv_asia_acts": "Asia",
            "kjv_inn": "inn", "kjv_christian_name_acts": "Christian", "kjv_sorcerer": "sorcerer", "kjv_witch": "witch",
            "kjv_noah": "Noah", "kjv_spain_romans": "Spain", "kjv_sapphire": "sapphire",
            "kjv_persia": "Persia", "kjv_chalkstone": "chalk", "kjv_tapestry": "tapestry",
            "kjv_binding_band": "binding band",
            "kjv_wizard": "wizard", "kjv_creditor": "creditor", "kjv_bucket": "bucket",
            "kjv_lot": "lot",
        })


if __name__ == "__main__":
    prepare()
