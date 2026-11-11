"""Venetian household identities, Belmont disguises and the merchant's accounts."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "antonio_venice_merchant": ("antoniyo", "Antonio", "The Venetian merchant and Bassanio's friend, who enters the bond with Shylock."),
    "salarino_antonio_friend": ("salarino", "Salarino", "Antonio's interlocutor at the opening. Distinct from Solanio and from the messenger Salerio."),
    "solanio_antonio_friend": ("solanyo", "Solanio", "Antonio's interlocutor who conjures up the wind and maps. Distinct from Salarino and Salerio."),
    "salerio_venice_messenger": ("saleryo", "Salerio", "The messenger from Venice who brings Antonio's letter to Belmont."),
    "bassanio_portia_suitor": ("basanyo", "Bassanio", "Antonio's kinsman and friend who seeks Portia at Belmont."),
    "gratiano_bassanio_friend": ("gratsiyano", "Gratiano", "Bassanio's companion who marries Nerissa. Distinct from Brabantio's brother."),
    "lorenzo_jessica_husband": ("lorentso", "Lorenzo", "Friend of Bassanio and husband of Jessica."),
    "portia_belmont_heiress": ("portia", "Portia", "The heiress of Belmont who argues the bond case. Bassanio compares her with Cato's daughter; they are separate women."),
    "nerissa_portia_companion": ("nerisa", "Nerissa", "Portia's companion who marries Gratiano and appears as the lawyer's clerk."),
    "shylock_venice_lender": ("Ûaylok", "Shylock", "The Venetian Jewish lender, father of Jessica. His trial turns on the flesh penalty of his bond."),
    "jessica_shylock_daughter": ("jesika", "Jessica", "Shylock's daughter, who leaves his house and marries Lorenzo."),
    "tubal_shylock_friend": ("tubal", "Tubal", "Shylock's fellow lender in Venice, distinct from the persons or peoples of the biblical name."),
    "leah_shylock_ring": ("leya", "Leah", "The woman who gave the unmarried Shylock a turquoise ring. Distinct from Jacob's wife in the biblical narrative."),
    "lancelet_gobbo_servant": ("lanselet", "Lancelet", "The younger Gobbo, servant to Shylock and then to Bassanio. Keep the local spelling Lancelet."),
    "gobbo_family_name": ("gobo", "Gobbo", "The surname shared by Lancelet and his father. Distinguish their personal and elder designations in the directions."),
    "gobbo_lancelet_father": ("gobo", "Gobbo", "Lancelet's nearly blind father, called Gobbo in the speech headings. He brings a basket and offers Bassanio a dish of doves."),
    "margery_gobbo_mother": ("marjeri", "Margery", "Old Gobbo's wife and Lancelet's mother, named when the father doubts his son's identity."),
    "dobbin_gobbo_horse": ("dobin", "Dobbin", "Gobbo's shaft horse, whose tail serves as a measure of Lancelet's supposed beard."),
    "leonardo_bassanio_servant": ("leonardo", "Leonardo", "Bassanio's servant in the preparations for Belmont."),
    "balthazar_portia_servant": ("baltazar", "Balthazar", "Portia's servant sent to fetch the notes and clothes from Padua."),
    "balthazar_portia_alias": ("baltazar", "Balthazar", "Portia's assumed name as the lawyer. Same spoken name as her servant and a separate identity."),
    "stephano_belmont_servant": ("stefano", "Stephano", "Portia's servant who announces her approach to Belmont."),
    "bellario_paduan_doctor": ("belaryo", "Bellario", "Portia's learned cousin at Padua, whose letter introduces the young doctor at the trial."),
    "belmont_portia_estate": ("belmont", "Belmont", "Portia's home and the place of the casket test and final reunion."),
    "rialto_exchange_place": ("ryalto", "Rialto", "The Venetian place of trade and reports on the fortunes of ships."),
    "morocco_suitor_country": ("moroko", "Morocco", "The country named in the first royal suitor's title."),
    "colchos_fleece_shore": ("kolkos", "Colchos", "The shore of the Golden Fleece compared to Belmont. Retains the geographical form in this source."),
    "jason_fleece_seeker": ("yason", "Jason", "The seeker of the Golden Fleece, extended in the plural to Portia's suitors. Distinct from either New Testament Jason."),
    "andrew_merchant_vessel": ("andru", "Andrew", "Salarino's imagined richly laden ship. The name denotes a vessel, independently of the biblical apostle."),
    "palatine_belmont_suitor": ("palatin", "Palatine", "The count palatine described by Portia, who makes his frown the mark of his courtship."),
    "le_bon_belmont_suitor": ("lebon", "Le Bon", "The French lord in Portia's catalogue of suitors."),
    "falconbridge_belmont_baron": ("falkonbrij", "Falconbridge", "The English baron whom Portia cannot converse with. Distinct from the English historical figures."),
    "saxony_suitor_duchy": ("saksonya", "Saxony", "The duchy of the uncle of Portia's German suitor."),
    "montferrat_marquess_estate": ("montferat", "Montferrat", "The territory in the marquess's title in Nerissa's memory of Bassanio's visit."),
    "tripolis_merchant_port": ("tripolis", "Tripolis", "The port named as a destination of Antonio's ship. The witness supplies no more precise modern location."),
    "mexico_merchant_destination": ("meksiko", "Mexico", "Place where Shylock has heard that Antonio has a third trading ship."),
    "solyman_morocco_battles": ("soliman", "Solyman", "The sultan whom Morocco boasts he defeated in three battles. The speech makes no independent historical claim."),
    "genoa_tubal_search": ("jenova", "Genoa", "The city where Tubal sought Jessica and heard news of both her purchases and Antonio's losses."),
    "frankfurt_diamond_market": ("frankfurt", "Frankfurt", "Where Shylock says he paid two thousand ducats for a diamond."),
    "midas_gold_touch": ("midas", "Midas", "The king whose golden touch makes gold hard food in Bassanio's deliberation."),
    "chus_shylock_countryman": ("kus", "Chus", "The man Jessica names with Tubal as a witness to Shylock's oath. Distinct from the biblical Cush."),
    "lisbon_antonio_route": ("lisbon", "Lisbon", "One of the ports Bassanio lists when he asks whether any of Antonio's ships survived."),
    "scylla_lancelet_hazard": ("skila", "Scylla", "One of the paired perils Lancelet uses in his joke about Jessica's father and mother."),
    "charybdis_lancelet_hazard": ("karibdis", "Charybdis", "The other peril in Lancelet's pairing of Jessica's parents."),
    "aeson_medea_restored": ("eson", "Aeson", "The old man whom Medea's enchanted herbs renewed, in Jessica's series of night comparisons."),
    "endymion_moon_beloved": ("endimyon", "Endymion", "Beloved of the moon in Portia's request for silence."),
}

SENSES = {
    "argosy_large_merchantman": (["great", "trade", "ship"], "argosy", "noun", "A grand merchant vessel, personified above smaller traders in Salarino's comparison."),
    "merchant_venture_cargo": (["risk", "trade"], "venture", "noun", "The commercial stake exposed to sea travel. The play distinguishes Antonio's several ships and destinations."),
    "gudgeon_fish_bait": (["small", "fish"], "gudgeon", "noun", "A small easily caught fish, applied by Gratiano to the reputation for wisdom for which a silent man angles."),
    "casket_choice_box": (["choose", "box"], "casket", "noun", "One of the gold, silver and lead boxes in the condition imposed by Portia's father."),
    "sophy_persian_title": (["kjv_persia", "king"], "Sophy", "noun", "The Persian ruler's title in Morocco's claim about his scimitar. A different Persian prince is mentioned immediately after."),
    "turquoise_leah_gem": (["blue", "green", "gem"], "turquoise", "noun", "The stone in the ring Leah gave Shylock before his marriage. He distinguishes its personal value from a price in animals."),
    "magnifico_venetian_noble": (["noble", "lord"], "magnifico", "noun", "A Venetian grandee named with the Duke, distinct from the twenty merchants who also interceded."),
    "clerk_nerissa_disguise": (["law", "writer"], "clerk", "noun", "The lawyer's clerk played by the disguised Nerissa. The office appears in the stage directions and as a form of address."),
    "shylock_gift_deed": (["gift", "writing"], "deed of gift", "noun", "The instrument Shylock is ordered to sign, settling his possessions at death on Lorenzo and Jessica. It is first drafted, then sent for signature and later delivered at Belmont."),
}


def lexical_entries(language):
    return build_entries(language, NAMES, SENSES, {"belmont_portia_estate", "rialto_exchange_place",
        "morocco_suitor_country", "colchos_fleece_shore", "saxony_suitor_duchy",
        "montferrat_marquess_estate", "tripolis_merchant_port", "mexico_merchant_destination",
        "genoa_tubal_search", "frankfurt_diamond_market", "lisbon_antonio_route"})


def prepare():
    add_source_entries("the-merchant-of-venice", "the-comedy-of-errors", lexical_entries,
        "Keep the three similarly named Venetians separate, distinguish the two Portias and the two Balthazar roles, and distinguish named ships from biblical people.",
        inherited_glosses={"kjv_broth": "broth", "kjv_anchor_acts": "anchor",
            "kjv_bushel": "bushel", "kjv_temple_head": "temple of head", "kjv_jew": "Jew",
            "kjv_nazarene": "Nazarene", "kjv_publican": "tax collector", "kjv_laban": "Laban",
            "kjv_ram": "ram", "kjv_tribe": "tribe", "kjv_gravel": "gravel", "kjv_palm_hand": "palm",
            "kjv_ashes": "ashes", "kjv_hagar": "Hagar", "kjv_arabia": "Arabia",
            "kjv_synagogue": "synagogue", "kjv_ferryboat": "ferryboat", "kjv_sabbath": "Sabbath",
            "kjv_bleat": "bleat", "kjv_principal_amount": "principal",
            "kjv_daniel_captive": "Daniel", "kjv_barabbas": "Barabbas",
            "kjv_cherub": "cherub", "kjv_manna": "manna"})


if __name__ == "__main__":
    prepare()
