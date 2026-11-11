"""The Athenian household, creditors and artists in Timon of Athens."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "byzantium_ancient_city": ("bizantion", "Byzantium", "The city where Alcibiades says the condemned soldier served."),
    "hostilius_second_stranger": ("ostilius", "Hostilius", "The second Stranger, addressed by name after witnessing Lucius refuse Timon's request."),
    "lacedaemon_spartan_land": ("lakedemon", "Lacedaemon", "The Spartan territory to which Timon says his lands once extended."),
    "apemantus_athenian_critic": ("apemantos", "Apemantus", "The abrasive Athenian who challenges the praise of Timon's guests and later visits him outside the city."),
    "lucilius_timon_servant": ("lusilius", "Lucilius", "Timon's servant, who loves the old Athenian's daughter. The Roman officer of Brutus is another person."),
    "ventidius_timon_friend": ("ventidius", "Ventidius", "The friend whose debt Timon pays. Distinct from Antony's commander."),
    "alcibiades_athenian_captain": ("alkibiades", "Alcibiades", "The Athenian commander who visits Timon, pleads for a soldier before the Senate, and later returns in arms."),
    "flavius_timon_steward": ("flavius", "Flavius", "The steward responsible for Timon's accounts."),
    "flaminius_timon_servant": ("flaminius", "Flaminius", "Timon's servant who asks Lucullus for help."),
    "servilius_timon_servant": ("servilius", "Servilius", "Timon's servant sent to Lucius."),
    "lucullus_timon_guest": ("lukulos", "Lucullus", "The lord who refuses Flaminius's request for help on Timon's behalf."),
    "lucius_timon_guest": ("lusius", "Lucius", "The Athenian approached by Servilius for Timon. Distinguish references to Lucius's man from Lucius's own speeches."),
    "sempronius_timon_guest": ("sempronius", "Sempronius", "A lord who resents being asked for aid after the other guests."),
    "caphis_athenian_agent": ("kafis", "Caphis", "A senator's servant sent to collect from Timon."),
    "varro_athenian_creditor": ("varo", "Varro", "A creditor represented by his men; separate from Brutus's guard."),
    "isidore_athenian_creditor": ("isidor", "Isidore", "The creditor whose man attends to seek payment."),
    "hortensius_athenian_agent": ("ortensius", "Hortensius", "The man attending with other creditors' servants to collect a debt."),
    "titus_athenian_agent": ("titus", "Titus", "The man who comes with Hortensius for payment; distinct from Titus Lartius and the Biblical Titus."),
    "philotus_athenian_agent": ("filotos", "Philotus", "One of the men demanding money from Timon's household."),
    "phrynia_alcibiades_companion": ("friniya", "Phrynia", "One of the two women with Alcibiades when he meets Timon outside Athens."),
    "timandra_alcibiades_companion": ("timandra", "Timandra", "The other woman accompanying Alcibiades. She speaks to Timon by name in the scene."),
}

SENSES = {
    "bandit_road_robber": (["way", "thief"], "bandit", "noun", "A robber of travelers. The three numbered bandits in the woods initially present themselves as soldiers."),
    "bathing_tub_vessel": (["bath_washing", "vessel"], "bathing tub", "noun", "The treatment tub in Timon's address to Timandra, a vessel distinct from the act of bathing."),
    "misanthropos_timon_byname": (["human", "hate"], "Man-hater", "proper", "The name Timon gives himself in the woods, translated by its Greek sense. It is a self-description of the Athenian Timon."),
    "solidare_athenian_coin": (["coin_currency", "piece"], "solidare", "noun", "The coin Lucullus offers Flaminius for concealing their encounter. No exchange rate or metal is asserted."),
    "brothel_customer": (["harlot_person", "visit"], "brothel customer", "noun", "The whoremaster in the Fool's exchange with Varro's man. The Fool finds him among all professions and stations."),
    "gull_seabird": (["shore", "bird"], "gull", "noun", "The stripped seabird opposed to the brilliant phoenix. The Senator's image also suggests a man made a dupe."),
    "windpipe_throat_passage": (["breath", "passage"], "windpipe", "noun", "The airway that Apemantus imagines exposed when a great man drinks at dinner."),
    "gem_water_lustre": (["gem", "light"], "gem lustre", "noun", "The water of the jeweler's stone: its transparent brilliance."),
}


def lexical_entries(language):
    return build_entries(language, NAMES, SENSES, {"lacedaemon_spartan_land", "byzantium_ancient_city"})


def prepare():
    add_source_entries("timon-of-athens", "the-winters-tale", lexical_entries,
        "Use the Athenian Timon already invoked by Berowne. His indebted friend Ventidius and his servant Lucilius are separate from their Roman namesakes. The talent is a monetary unit.",
        inherited_glosses={"kjv_talent_money": "talent", "kjv_debt_bill": "debt bill",
                          "kjv_diligent": "diligent", "kjv_swallow_bird": "swallow",
                          "kjv_uncover": "uncover", "kjv_diamond": "diamond",
                          "kjv_sprinkle": "sprinkle", "kjv_nakedness": "nakedness",
                          "kjv_consumption_illness": "wasting sickness"})


if __name__ == "__main__":
    prepare()
