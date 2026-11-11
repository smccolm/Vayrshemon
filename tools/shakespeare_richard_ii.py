"""Names and senses specific to the deposition play on the shared dramatic branch."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "saracen_crusade_people": ("sarakin", "Saracen", "Carlisle's historical designation for a people in his account of Norfolk's crusading. Distinct from Turks and from the broader religious label."),
    "stephen_scroop_given": ("steven", "Stephen", "Given name of the knight who reports the collapse of Richard's support; explicitly supplied in young Percy's report from Flint."),
    "exeter_richard_duke": ("ekseter", "Exeter", "The Duke of Exeter in Northumberland's account of the escape. Distinct from Henry V's uncle."),
    "john_ramston_given": ("jon", "John", "The given name of Sir John Ramston in the returning party."),
    "john_norbery_given": ("jon", "John", "The given name of Sir John Norbery in the returning party."),
    "robert_waterton_given": ("robert", "Robert", "The given name of Sir Robert Waterton in the returning party."),
    "woodstock_duke_byname": ("wudstok", "Woodstock", "Thomas of Woodstock, the dead Duke of Gloucester, called here by his territorial byname."),
    "york_langley_duke": ("york", "York", "Edmund of Langley, Richard's uncle and the father of Aumerle, when named by his dukedom."),
    "percy_hotspur_surname": ("persi", "Percy", "The young Percy, subsequently called Hotspur. His father's surname and their territorial title have separate entries."),
    "percy_northumberland_surname": ("persi", "Percy", "The elder Percy, Earl of Northumberland, when addressed by surname in the final scene."),
    "aumerle_york_son": ("omerl", "Aumerle", "The son of Edmund of Langley. His parents call him Aumerle even when the forfeited title is in question."),
    "rutland_aumerle_title": ("rutland", "Rutland", "Aumerle's remaining title, distinct from the boy Rutland killed by Clifford in a later generation."),
    "bushy_richard_favourite": ("bushi", "Bushy", "Sir John Bushy, a follower of Richard who is condemned with Green."),
    "bagot_richard_favourite": ("bagot", "Bagot", "Sir John Bagot: witness and accuser of Aumerle; distinct from Bushy and Green."),
    "green_richard_favourite": ("grin", "Green", "Sir Henry Green, one of Richard's companions. The surname is distinct from a color word."),
    "ross_bolingbroke_ally": ("ros", "Ross", "Lord Ross, who joins Bolingbroke. A different person from the Scottish thane."),
    "willoughby_bolingbroke_ally": ("wilobi", "Willoughby", "Lord Willoughby, in the party with Ross and Northumberland."),
    "salisbury_richard_ally": ("solzbri", "Salisbury", "The earl in Wales who loses his forces before Richard arrives. Northumberland later reports sending his head to London."),
    "carlisle_bishop_richard": ("karlail", "Carlisle", "The bishop who condemns a subject's judgment of his king, later sentenced by Henry to live in retirement."),
    "scroop_stephen_knight": ("skrup", "Scroop", "Sir Stephen Scroop, who reports the loss of Richard's supporters. Distinct from the archbishop and from the Scroop of the Henry V conspiracy."),
    "berkeley_lord_richard": ("barkli", "Berkeley", "The lord who brings York's enquiry to Bolingbroke, distinct from his castle."),
    "fitzwater_richard_appellant": ("fitswater", "Fitzwater", "The lord who challenges Aumerle and reports two prisoners' heads sent from Oxford."),
    "surrey_richard_duke": ("suri", "Surrey", "The duke who exchanges a challenge with Fitzwater. Other earls of this name have separate identities."),
    "pierce_exton_given": ("pirs", "Pierce", "Given name of Sir Pierce of Exton, later the killer of Richard."),
    "exton_richards_killer": ("ekston", "Exton", "The knight who reads Henry's wish as an order to kill Richard and afterward presents his coffin."),
    "derby_bolingbroke_title": ("darbi", "Derby", "One of the territorial titles Bolingbroke gives in the lists."),
    "lambert_feast_saint": ("lambert", "Lambert", "The saint whose feast Richard assigns for the combat at Coventry."),
    "rainold_cobham_given": ("reinold", "Rainold", "Given name of Lord Cobham in Northumberland's report from Brittany."),
    "cobham_hereford_ally": ("kobam", "Cobham", "Rainold's title in the report of the returning party. This is not the Lancastrian conspirator's wife."),
    "ramston_returning_knight": ("ramston", "Ramston", "Sir John Ramston, one of the knights returning with Hereford."),
    "norbery_returning_knight": ("norberi", "Norbery", "Sir John Norbery, named beside Ramston."),
    "waterton_returning_knight": ("waterton", "Waterton", "Sir Robert Waterton, named among the returning party."),
    "francis_coint_given": ("fransis", "Francis", "Given name of Coint in Northumberland's list."),
    "coint_hereford_ally": ("koint", "Coint", "Surname of Francis Coint in the list from Le Port Blanc."),
    "beaumont_hereford_lord": ("bomon", "Beaumont", "The English lord reported to have joined Hereford, distinct from the French lord in Henry V."),
    "seymour_york_lord": ("seimur", "Seymour", "The lord reported with Berkeley and York."),
    "wiltshire_richard_earl": ("wiltshir", "Wiltshire", "The earl attached to Richard's party, not the earl fighting in the Wars of the Roses."),
    "kent_revolt_earl": ("kent", "Kent", "Kent as named in Northumberland's report of heads sent to London."),
    "oxford_revolt_earl": ("oksford", "Oxford", "The titled man reported dead at the end, distinct from the town where other rebels were taken."),
    "blunt_revolt_knight": ("blunt", "Blunt", "The Blunt named among those whose heads were sent to London. This report does not identify him as Sir Walter Blunt."),
    "brocas_revolt_knight": ("brokas", "Brocas", "One of the two men Fitzwater reports beheaded at Oxford."),
    "bennet_seely_given": ("benet", "Bennet", "Given name of Sir Bennet Seely."),
    "seely_revolt_knight": ("sili", "Seely", "The second of the pair named with Brocas."),
    "barbary_roan_horse": ("barbari", "Barbary", "The roan formerly ridden by Richard and ridden by Bolingbroke in the coronation procession."),
    "plashy_gloucester_house": ("plashi", "Plashy", "The widow's desolate home, to which she both invites York and asks him not to come."),
    "port_blanc_brittany_bay": ("le port blan", "Le Port Blanc", "The bay in Brittany from which Northumberland receives his report. The full place-name stays together."),
    "cotshall_berkeley_route": ("kotsal", "Cotshall", "The place in Northumberland's estimate of the journey from Ravenspurgh. The witness spells it Cotshall."),
    "barkloughly_castle": ("barkloli", "Barkloughly", "The castle near Richard's landing in Wales. The play's name is retained without assigning another site."),
    "flint_richard_castle": ("flint", "Flint", "The castle at which Richard descends to Bolingbroke, distinct from flint as a mineral."),
    "ely_london_house": ("ili", "Ely", "The London house where Gaunt lies ill."),
    "ciceter_gloucestershire_town": ("siseter", "Ciceter", "The Gloucestershire town named in the last scene; local contracted spelling is retained."),
    "caucasus_mountains": ("kaukasus", "Caucasus", "The frozen Caucasus in Bolingbroke's examples of what imagination cannot do to the body."),
}

SENSES = {
    "gardener_richard_household": (["garden","person"], "gardener", "noun", "A person who tends a garden. The gardener directs two servingmen and explains the pruning and rue to the listening Queen."),
    "canterbury_returning_archbishop": (["chief_bishop"], "archbishop", "noun", "The former Archbishop of Canterbury in Northumberland's report. The printed text calls him 'his brother' without naming him."),
    "livery_inherited_lands": (["heir", "possession"], "possession of inheritance", "noun", "Formal delivery of the heir's lands, which the exiled Hereford has authorization to claim by attorney."),
    "duchess_gloucester_widow": (["duchess"], "Duchess", "noun", "Speaker of the marital and fraternal lament for her murdered husband Thomas of Woodstock."),
    "duchess_york_mother": (["duchess"], "Duchess", "noun", "Aumerle's mother and the wife of Edmund of Langley, pleading for her son's life."),
    "appellant_trial_combat": (["accuse","person"], "appellant", "noun", "The party who brings a formal charge and offers to prove it by combat."),
    "appeal_charge_combat": (["accuse","challenge"], "appeal", "verb", "Charge a person with treason under the offer of proof by individual combat."),
}


def lexical_entries(language):
    places = {"plashy_gloucester_house","port_blanc_brittany_bay",
              "cotshall_berkeley_route","barkloughly_castle","flint_richard_castle",
              "ely_london_house","ciceter_gloucestershire_town","caucasus_mountains"}
    entries, glosses = build_entries(language, NAMES, SENSES, places)
    entries["barbary_roan_horse"]["origin"] = "Localized proper name of the groom's former charge, a roan horse."
    entries["saracen_crusade_people"]["origin"] = "Localized historical ethnonym in the bishop's speech."
    return entries, glosses


def prepare():
    add_source_entries("richard-ii", "pericles", lexical_entries,
        "Richard, Gaunt, Bolingbroke, the elder Mowbray and the two Percys retain their established identities. The widowed Duchess of Gloucester and Aumerle's mother the Duchess of York are distinguished by context without supplying unspoken given names.")


if __name__ == "__main__":
    prepare()
