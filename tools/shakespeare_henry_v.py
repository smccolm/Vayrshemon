"""Dictionary decisions for Henry V on the shared dramatic branch."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


PLACES = {
    "agincourt_field": ("azinkor", "Agincourt", "The field in France whose helmets the Chorus asks the playhouse to contain."),
    "ely_see": ("Ýli", "Ely", "The English episcopal see of the bishop who speaks with Canterbury."),
    "bedford_duchy": ("bedford", "Bedford", "Title of Henry's brother John, formerly named Lancaster. The name of the duchy stands for him in the court scene."),
    "exeter_duchy": ("ekseter", "Exeter", "Title of Henry's uncle, who is present in council and identifies the tennis balls."),
    "salic_land": ("salik", "Salic", "The land whose identification the bishop disputes, and the name of the associated law."),
    "sala_river": ("sala", "Sala", "The river in Canterbury's account of the Salic territory."),
    "elbe_river": ("elb", "Elbe", "The second river bounding the territory in the bishop's account."),
    "meissen_land": ("maisen", "Meissen", "Canterbury's contemporary name for the territory in his argument."),
    "lorraine_duchy": ("loren", "Lorraine", "The duchy of the Charles whose crown Canterbury says Capet usurped."),
    "cambridge_earldom": ("kembrij", "Cambridge", "The earldom held by the Richard named in the Southampton plot."),
    "masham_town": ("masam", "Masham", "The place in the title of Henry, Lord Scroop."),
    "northumberland_county": ("northumberlend", "Northumberland", "The county from which the knight Thomas Grey comes."),
    "southampton_port": ("saÓampton", "Southampton", "The port at which the king is to embark. The inherited Southampton form also occurs as a patron's territorial title."),
    "iceland_island": ("aisland", "Iceland", "The origin of the prick-eared dog in Pistol's insult."),
    "tartarus_depth": ("tartar", "Tartarus", "The infernal place called Tartar to which Henry imagines Scroop's deceiver returning. Distinct from the ethnic name."),
    "staines_town": ("steins", "Staines", "The town to which Quickly offers to accompany Pistol."),
    "berri_duchy": ("beri", "Berri", "The French dukedom of Berri in the king's defense council."),
    "brittany_duchy": ("britani", "Brittany", "The French dukedom of Brittany in the same council."),
    "brabant_duchy": ("brabant", "Brabant", "The dukedom of Brabant, whose forces the king asks to repair the defenses."),
    "cressy_field": ("kresi", "Cressy", "The battlefield in the French king's recollection of Edward the Black Prince."),
    "paris_french_city": ("paris", "Paris", "The city associated with the tennis balls and the Louvre, distinct from the Trojan person."),
    "louvre_palace": ("luvri", "Louvre", "The Paris royal residence that Exeter says Henry will shake."),
    "dover_port": ("dovar", "Dover", "The pier named by the third-act Chorus when asking the audience to imagine the embarkation."),
    "harfleur_town": ("harflër", "Harfleur", "The French port to which the fleet sails and whose walls Henry besieges."),
    "calais_port": ("kale", "Calais", "Port where Nym and Bardolph stole the fire shovel, according to the Boy."),
    "somme_river": ("som", "Somme", "The river the French king says Henry has crossed on the march."),
    "albion_island": ("albion", "Albion", "Brittany's name for the British island with the jutting coast."),
    "bourbon_duchy": ("burbon", "Bourbon", "Dukedom named in the French king's summons to battle."),
    "alencon_duchy": ("alenson", "Alençon", "The French dukedom in the king's summons, printed Alencon in the supplied source."),
    "bar_duchy": ("bar", "Bar", "Dukedom of Bar in the summons."),
    "burgundy_duchy": ("burgundi", "Burgundy", "Dukedom named in the summons. Its duke later appears to argue for peace."),
    "rouen_city": ("ruen", "Rouen", "The city to which the French king wants the captured Henry brought."),
    "russia_bear_country": ("rusia", "Russia", "Country of the bear into whose mouth the English mastiffs rush in Orleans's taunt."),
    "cornwall_country": ("kornwal", "Cornwall", "The region to which Pistol mistakenly assigns the disguised king's supposed surname."),
    "thames_river": ("temz", "Thames", "The English river where Bates imagines himself and the king neck-deep if only they could escape the battle."),
    "suffolk_earldom": ("sufok", "Suffolk", "The earl who dies before York, whose last embrace Exeter describes."),
    "monmouth_town": ("monmeÕ", "Monmouth", "The town of Henry's birth in Fluellen's comparison of Monmouth and Macedon. Uses the established Monmouth form."),
    "macedon_kingdom": ("makedon", "Macedon", "The kingdom in which Fluellen and Gower locate Alexander's birth."),
    "blackheath_common": ("blakheÕ", "Blackheath", "The place outside London where the Chorus imagines the king's lords asking him to display his helmet and sword."),
    "huntington_earldom": ("huntiÙton", "Huntington", "The title of the lord sent to review the treaty, with the witness's spelling."),
    "constantinople_city": ("konstantinopol", "Constantinople", "The city Henry imagines a future child reaching."),
    "salisbury_earldom": ("salzberi", "Salisbury", "The English earl who greets his companions before Agincourt, named by his title."),
    "york_duke_battle": ("york", "York", "The duke who volunteers for the vanguard at Agincourt, distinct from the archbishop and the English city."),
}

PEOPLE = {
    "alice_katherine": ("alis", "Alice", "Katherine's older gentlewoman and teacher in the English lesson. She has lived in England."),
    "pharamond_king": ("faramond", "Pharamond", "The king said by others to have founded the law. Canterbury challenges the attribution."),
    "saxon_people": ("sakson", "Saxon", "The people subdued by Charles in Canterbury's account."),
    "charles_great": ("Ñarlz", "Charles", "Charles the Great as Canterbury names him in the argument over Salic land."),
    "pepin_king": ("pepin", "Pepin", "The king who deposes Childeric and claims through Blithild in Canterbury's account."),
    "childeric_king": ("Ñilderik", "Childeric", "The king deposed by Pepin in Canterbury's account."),
    "blithild_ancestor": ("blithild", "Blithild", "Daughter of Clothair and ancestor through whom Pepin makes his claim."),
    "clothair_king": ("kloter", "Clothair", "The father of Blithild in Canterbury's genealogy."),
    "hugh_capet_king": ("hë", "Hugh", "Capet's given name in the bishop's account of the usurped crown."),
    "capet_dynast": ("kapet", "Capet", "Hugh's surname, also used on its own in the genealogy."),
    "charles_lorraine": ("Ñarlz", "Charles", "Duke of Lorraine. Separate from Charles the Great, whose line he represents."),
    "lingare_ancestor": ("lingar", "Lingare", "Daughter of the Charlemagne whom Canterbury places one generation below Lewis the Emperor."),
    "charlemagne_lingare": ("Ûarlemayn", "Charlemagne", "Lingare's father in the speech. Canterbury assigns him a different generation from Charles the Great."),
    "lewis_emperor": ("luis", "Lewis", "The emperor named as son of Charles the Great and father of Lingare's father."),
    "lewis_tenth": ("luis", "Lewis", "King Lewis the Tenth, distinguished from Lewis the Emperor."),
    "isabel_queen": ("izabel", "Isabel", "Lewis the Tenth's grandmother in the bishop's genealogy."),
    "ermengare_ancestor": ("ermengar", "Ermengare", "The duke of Lorraine's daughter from whom Isabel is said to descend."),
    "edward_black_prince": ("edward", "Edward", "The Black Prince, Henry's great-uncle. Distinct from his father Edward and Henry's later brothers."),
    "richard_cambridge": ("riÑard", "Richard", "Earl of Cambridge, the first of the three conspirators identified by the Chorus."),
    "henry_masham": ("henri", "Henry", "Given name of Lord Scroop of Masham in the Southampton plot."),
    "scroop_masham": ("skrup", "Scroop", "The trusted lord of Masham in the plot, distinguished from the archbishop and the slain Scroop."),
    "thomas_grey_knight": ("tomas", "Thomas", "Given name of the knight Grey in the Southampton plot."),
    "grey_conspirator": ("grei", "Grey", "Surname of Sir Thomas the conspirator."),
    "nell_quickly": ("nel", "Nell", "The hostess Quickly's given name in this play, distinct from Poins's sister Nell."),
    "barbason_spirit": ("barbazon", "Barbason", "The spirit whom Nym denies being when faced with Pistol's conjuring threats."),
    "fluellen_captain": ("fluelin", "Fluellen", "The Welsh captain who drives the tavern soldiers up to the breach and repeatedly invokes Yeshūa."),
    "gower_captain": ("gower", "Gower", "The English captain beside Fluellen. The witness supplies no identification with the messenger in Henry IV, Part 2."),
    "macmorris_captain": ("makmoris", "Macmorris", "The Irish captain supervising the siege excavation."),
    "jamy_captain": ("jemi", "Jamy", "The Scottish captain who joins the discussion about the siege."),
    "james_captain": ("jemz", "James", "The same Scottish captain addressed by Fluellen using the full name James."),
    "montjoy_herald": ("monjoi", "Montjoy", "The French herald, remembered under the same name at Agincourt."),
    "charles_delabreth": ("Ñarlz", "Charles", "Given name of the High Constable of France. Separate from the kings and the duke of Lorraine named Charles."),
    "delabreth_constable": ("delabret", "Delabreth", "Surname of Charles, High Constable of France."),
    "jacques_chatillon": ("jak", "Jacques", "Given name of the Châtillon named in the French summons."),
    "chatillon_lord": ("Ûatilyon", "Chatillon", "Surname paired with Jacques in the list of French lords."),
    "rambures_lord": ("rambër", "Rambures", "French noble named in the summons and subsequently a speaker."),
    "vaudemont_lord": ("vodemon", "Vaudemont", "French lord in the king's summons."),
    "beaumont_lord": ("bomon", "Beaumont", "French lord called to the field after Vaudemont."),
    "grandpre_lord": ("granpre", "Grandpré", "French lord named in the summons and later a speaker. Source label Grandpre."),
    "roussi_lord": ("rusi", "Roussi", "French lord called after Grandpré."),
    "faulconbridge_lord": ("falkonbrij", "Faulconbridge", "French lord named in the summons, distinct from the English family in King John."),
    "foix_lord": ("fwa", "Foix", "French lord named before Lestrale."),
    "lestrale_lord": ("lestral", "Lestrale", "French lord called between Foix and Bouciquault."),
    "bouciquault_lord": ("busiko", "Bouciquault", "French noble named with the witness's spelling Bouciquault."),
    "charolois_lord": ("Ûaroloi", "Charolois", "French lord named at the end of the summons."),
    "hermes_pipe_god": ("hermes", "Hermes", "The god whose pipe is compared with the music of the Dauphin's horse. Distinct from the person addressed in Romans."),
    "perseus_hero": ("perseus", "Perseus", "The mythical hero whom the Dauphin imagines as a worthy rider for his horse."),
    "thomas_erpingham": ("tomas", "Thomas", "The elderly English knight's given name, distinct from Grey and from the duke of Clarence."),
    "erpingham_knight": ("erpingam", "Erpingham", "The old knight whose cloak Henry borrows before visiting his soldiers."),
    "davy_welsh_saint": ("deivi", "Davy", "The Welsh patron saint whose feast and leek Pistol invokes. Distinct from Shallow's servant Davy and the biblical David."),
    "john_bates": ("jon", "John", "The English soldier Bates's given name in the fourth-act night watch."),
    "bates_soldier": ("beits", "Bates", "Soldier who would like the king beside him in the Thames, if both could escape the battle."),
    "alexander_court": ("aleksander", "Alexander", "Given name of the English soldier Court, distinct from the ancient conqueror."),
    "court_soldier": ("kort", "Court", "The soldier who first sees light on the horizon. He is not Williams or Bates."),
    "michael_williams": ("mikel", "Michael", "English soldier who disputes the king's assurance of his cause."),
    "williams_soldier": ("wiliams", "Williams", "The soldier who trades gloves with Henry while Henry is disguised."),
    "talbot_captain": ("talbot", "Talbot", "Named among the English heroes whom Henry imagines being remembered at home."),
    "crispin_saint": ("krispin", "Crispin", "The saint named in the final cry of Henry's speech; the shared feast also honors Crispian."),
    "crispian_saint": ("krispian", "Crispian", "The other saint of the shared feast, called Crispian in Henry's address."),
    "philip_macedon": ("filip", "Philip", "Alexander's father, Philip of Macedon, in Gower's answer."),
    "cleitus_friend": ("kleitos", "Cleitus", "The friend whom Alexander killed while drunk in Fluellen's comparison."),
    "tavy_welsh_saint": ("teivi", "Tavy", "Fluellen's form of the saint's name, repeating Davy with a devoiced initial."),
    "crispianus_saint": ("krispianus", "Crispianus", "The king uses this longer form of Crispian's name when he names the field of Agincourt."),
    "charles_orleans": ("Ñarlz", "Charles", "The French king's nephew, Duke of Orléans, reported captured alive."),
    "john_bourbon": ("jon", "John", "Duke of Bourbon, an imprisoned noble, distinct from John of Alençon."),
    "guichard_dauphin": ("giÛar", "Guichard", "Given name of the Great Master of France in the roll of dead."),
    "dauphin_guichard_family": ("dofin", "Dauphin", "Sir Guichard's surname. The French king's son bears a separate princely title."),
    "john_alencon": ("jon", "John", "Duke of Alençon, listed among the French dead."),
    "anthony_brabant": ("antoni", "Anthony", "Duke of Brabant, named as brother to the Duke of Burgundy."),
    "edward_bar": ("edward", "Edward", "Duke of Bar on the French roll of dead."),
    "marle_lord": ("marl", "Marle", "French earl named between Beaumont and Vaudemont."),
    "edward_york_vanguard": ("edward", "Edward", "Given name of York, the English duke whose death Exeter describes."),
    "richard_ketly": ("riÑard", "Richard", "Given name of the English knight listed after Suffolk."),
    "ketly_knight": ("ketli", "Ketly", "English knight's surname as printed in the witness."),
    "davy_gam": ("deivi", "Davy", "Given name of Gam, the English-side esquire named among the fallen."),
    "gam_esquire": ("gam", "Gam", "The surname of the esquire Davy in the battlefield roll."),
    "parca_fate": ("parka", "Parca", "The Fate whose web of life Pistol threatens to fold up."),
    "cadwallader_welsh": ("kadwalader", "Cadwallader", "Welsh ruler invoked by Pistol when refusing the leek."),
    "isabel_france": ("izabel", "Isabel", "The queen of France in the treaty and marriage scene, distinct from the earlier genealogical Isabel."),
    "kate_france": ("k×t", "Kate", "Henry's familiar name for Katherine of France, distinct from Hotspur's wife Kate."),
    "denis_france_saint": ("deni", "Denis", "French patron saint invoked in the wooing and paired with Saint George."),
    "henry_vi_infant": ("henri", "Henry", "Henry and Katherine's son, the infant king in the Epilogue, distinct from his father."),
}

SENSES = {
    "lesson_article": (["this"], "the (lesson)", "particle", "The native pointing form used before English words quoted in Katherine's lesson. It distinguishes the rehearsed English labels from French words rendered by their native equivalents."),
    "bishop_english": (["kjv_bishop_philippians"], "bishop", "noun", "An English bishop; the inherited oversight root also supplies the institutional dramatic sense."),
    "parliament_bill": (["law", "proposal"], "bill", "noun", "The proposed act for the transfer of church estates. Distinguish it from Falstaff's account of tavern expenses."),
    "cockpit_arena": (["cock_fowl", "pit"], "cockpit", "noun", "A cockfighting pit whose limited size the Chorus compares with the playhouse."),
    "strawberry_fruit": (["red", "berry"], "strawberry", "noun", "The small red berry beneath the nettle in Ely's comparison with Henry's hidden habits of reflection."),
    "alms_house": (["poor", "house"], "almshouse", "noun", "An endowed dwelling for people no longer able to work, in the bill as Canterbury quotes it."),
    "dauphin_heir": (["france", "heir"], "Dauphin", "noun", "The title of the French king's heir. The embassy carrying tennis balls comes from the son."),
    "galliard_dance": (["leap", "dance"], "galliard", "noun", "The lively dance with which the Dauphin says his rival will never win a duchy."),
    "tennis_racket": (["net", "strike"], "racket", "noun", "A strung implement for striking the ball in the Dauphin's tennis challenge."),
    "tennis_hazard": (["danger"], "hazard", "noun", "A winning opening of the tennis court, designated with the native danger root to retain the threat to the crown."),
    "tennis_chase": (["chase"], "chase", "noun", "A chase in court tennis, designated with the pursuit root to retain the military second meaning."),
    "nym_soldier": (["steal"], "Nym", "proper", "The corporal called Nym. A telling-name rendering takes up the old verb for stealing."),
    "nym_humour": (["mood"], "humor", "noun", "Nym's recurring word for a disposition, intention or way of looking at things. Its form recurs when he speaks of the king's humors."),
    "humour_bodily": (["mood"], "bodily humor", "noun", "Nym's word humor carried across to the supposed bodily workings of a sick man. The native form remains the same as the speaker's habitual word."),
    "pudding_dish": (["belly", "food"], "pudding", "noun", "A dish traditionally encased in gut. Quickly makes a grim promise about what the crow will eat."),
    "holdfast_dog": (["hold", "steadfast"], "Holdfast", "proper", "The proverbial dog's telling name in Pistol's advice to his wife."),
    "carnation_colour": (["flesh", "colour"], "carnation", "noun", "The flesh-colored hue that Quickly hears when the Boy says the devils are incarnate. Keep the shared flesh root audible."),
    "france_constable": (["army", "chief"], "High Constable", "noun", "The high military officer of the French crown, distinct from local constables who arrest offenders."),
    "grain_fine_weight": (["seed", "weight"], "grain of weight", "noun", "A minute weight in Exeter's image of Henry weighing time to the utmost grain. The verse gives no count of grains."),
    "linstock_gunner": (["fire", "staff"], "linstock", "noun", "The gunner's staff carrying the lit match to touch off the cannon."),
    "chamber_stage_gun": (["small", "cannon"], "chamber gun", "noun", "A small gun fired to produce the sound of artillery in a stage direction."),
    "yeoman_english": (["land", "man"], "yeoman", "noun", "An English common landholder among the men Henry addresses apart from the nobility."),
    "siege_mine": (["undermine", "way"], "mine", "noun", "An underground approach dug to undermine a fortification at Harfleur."),
    "countermine_passage": (["resist", "dig"], "countermine", "noun", "A counter-tunnel dug in siege warfare. Fluellen says the enemy has got below these countermines."),
    "discipline_military": (["war", "rule"], "military discipline", "noun", "The principles of military practice, repeatedly invoked by Fluellen in his account of the Roman wars."),
    "lavolta_dance": (["turn", "leap"], "lavolta", "noun", "The high turning dance in Brittany's report of the Frenchwomen's taunts."),
    "pax_church": (["peace", "kiss"], "pax", "noun", "A liturgical object kissed as a sign of peace. Pistol says Bardolph is sentenced to hang for stealing one from a church."),
    "execute_judicial": (["law", "kill"], "execute", "verb", "Carry out a sentence of death; Fluellen transfers the act to Bardolph's fiery nose."),
    "pastern_joint": (["foot", "joint"], "pastern", "noun", "The short part of a horse's leg immediately above the hoof."),
    "nutmeg_spice": (["spice", "nut"], "nutmeg", "noun", "The brown aromatic seed used to compare the horse's coloring."),
    "palfrey_mount": (["ride", "horse"], "palfrey", "noun", "A riding horse, here the Dauphin's cherished mount."),
    "hazard_dice": (["risk", "dice"], "hazard", "noun", "A game of dice. The risk root recurs in the Constable's reply that Rambures must go to hazard in battle."),
    "mastiff_dog": (["strong", "dog"], "mastiff", "noun", "The heavy strong dog of England in Rambures's boast and Orleans's retort about bear-baiting."),
    "kern_irish": (["foot", "soldier"], "kern", "noun", "An Irish foot soldier in the Dauphin's mockery of the Constable's style of riding."),
    "leroy_disguise": (["king"], "Le Roy", "proper", "The king is the literal meaning of Henry's French alias. Pistol takes the native royal word as a surname and guesses that it comes from Cornwall."),
    "crown_head_henry": (["crown"], "crown of head", "noun", "The crown of a person's head. Shares the form of the crown coin in Henry's twenty-to-one joke."),
    "chantry_chapel": (["sing", "chapel_worship"], "chantry", "noun", "An endowed chapel where priests sing for a dead person's soul. Henry has built two for Richard."),
    "mace_royal": (["rule", "rod"], "mace", "noun", "The ceremonial mace in Henry's catalogue of the emblems of kingship."),
    "salmon_river_fish": (["silver", "fish_creature"], "salmon", "noun", "The fish that Fluellen says appear in both rivers. Distinguish the fish from the biblical person with the same English spelling."),
    "fer_prisoner": (["iron"], "Fer", "proper", "The French prisoner's iron surname, rendered with the existing native iron root so Pistol can turn his name into verbs."),
    "dew_misheard_name": (["god"], "Dew (misheard name)", "proper", "Pistol hears the French soldier's address to God as the unknown man's surname. Its native form is identical to the god word in the soldier's cry."),
    "fox_blade": (["fox"], "fox blade", "noun", "Pistol's name for the sword on which his captive will die. Preserve the animal name."),
    "fer_threat": (["iron"], "fer", "verb", "Pistol makes an aggressive verb of his captive's native iron surname."),
    "firk_threat": (["iron", "strike"], "firk", "verb", "Pistol's beating threat, with the iron sound picked up from Fer."),
    "ferret_threat": (["iron", "hunt"], "ferret", "verb", "Pistol's hunting-out threat, the third echo of Fer's surname."),
    "mayor_london": (["city", "chief"], "mayor", "noun", "The leading civic officer who comes out with his brethren to welcome the returning king."),
    "darnel_grass": (["false", "grain_kernel"], "darnel", "noun", "A weed resembling cereal grass that takes root in the idle fields."),
    "fumitory_plant": (["smoke", "herb"], "fumitory", "noun", "The smoke herb growing rank among the crops in Burgundy's speech."),
    "burnet_plant": (["red", "herb"], "burnet", "noun", "The red-flowered meadow herb named beside cowslip and clover."),
    "clover_plant": (["meadow", "leaf"], "clover", "noun", "The clover leaf of the earlier sweet meadow, distinct from the flowers listed with it."),
    "dock_weed": (["broad", "leaf"], "dock plant", "noun", "The broad-leaf weed Burgundy calls hateful in the neglected meadow."),
    "kecksy_stalk": (["hollow", "stem"], "kecksy", "noun", "The tall hollow weed stalk named between thistles and burrs."),
}

# These sounds are local to the speaker. Each altered spelling is derived
# from the normal native word rather than the English letters.
LESSON_READINGS = {
    "lesson_le": ("this", "ÑeÕ", "Ñe", "the (French article)", "A clipped native pointing form registers the switch into French le just before a quoted English noun."),
    "lesson_arm_arma": ("arm", "lar", "lara", "arm (slip)", "Katherine adds a final vowel in her first unaided list."),
    "lesson_elbow_bilbow": ("elbow", "larlunor", "bilunor", "elbow (slip)", "Katherine replaces the opening of elbow. Alice corrects her immediately."),
    "lesson_elbow_ilbow": ("elbow", "larlunor", "lirlunor", "elbow (slip)", "In her second unaided list Katherine changes the first vowel. Alice again supplies the ordinary elbow."),
    "lesson_neck_nick": ("neck", "harenklár", "harinklár", "neck (heard)", "Alice gives an accented form of neck, which Katherine repeats without correction."),
    "lesson_chin_sin": ("chin", "melen", "selen", "chin (slip)", "Katherine changes the initial consonant of the chin Alice has just pronounced. The error persists in her final list."),
    "lesson_nails_mailes": ("fingernail_body", "jeljeran", "meljeran", "nail (slip)", "Katherine displaces the initial consonant in her recall of fingernails. Alice supplies the ordinary word."),
}

FLUELLEN_READINGS = {
    "fluellen_pig_slip": ("big", "goren", "koren", "big (Pig slip)", "Fluellen devoices the initial of native big before Gower repeats great. The English animal-name coincidence remains in the source."),
    "fluellen_plood": ("blood", "zár", "sár", "blood (as spoken)", "Fluellen devoices the initial of native blood while speaking of Henry's Welsh blood."),
    "fluellen_pody": ("body", "vor", "for", "body (as spoken)", "Fluellen devoices the initial of native body in the same line as his pronunciation of blood."),
    "fluellen_plows": ("buffet_blow", "sleb", "slep", "blow (as spoken)", "Fluellen devoices the native word for a physical blow when threatening to pay for treason in plows. His meaning is blows."),
    "fluellen_pashful": ("bashful", "vënil", "fënil", "bashful (as spoken)", "As in his pronunciation of body, Fluellen devoices the voiced native initial when asking why Williams is bashful."),
    "fluellen_ploody": ("bloody", "zárplesten", "sárplesten", "bloody (as spoken)", "The same devoicing heard in the captain's plood extends to his description of Pistol's bleeding head."),
}

COURT_READINGS = {
    "court_wat": ("what", "Ñetib", "Ñetip", "what (as spoken)", "Katherine and Alice share a learner pronunciation of the interrogative when switching into English."),
    "court_dat": ("that", "ka", "ga", "that (as spoken)", "Katherine and Alice voice the initial of the native pointing form in their accented English."),
    "court_baiser": ("kiss", "melomi", "melom", "kiss (French citation)", "Alice quotes the French infinitive and asks for its English equivalent. The clipped citation contrasts with Henry's full native verb in reply."),
}


def lexical_entries(language):
    entries, glosses = build_entries(language, PLACES | PEOPLE, SENSES, set(PLACES))
    entries["nell_quickly"]["sameBearerAs"] = "quickly_hostess"
    entries["james_captain"]["sameBearerAs"] = "jamy_captain"
    entries["tavy_welsh_saint"]["sameBearerAs"] = "davy_welsh_saint"
    entries["crispianus_saint"]["sameBearerAs"] = "crispian_saint"
    entries["kate_france"]["sameBearerAs"] = "katherine_france"
    moy_form = language.word("i:a")[0]
    entries["moy_pistol_coin"] = dict(form=moy_form, roman=language.reading(moy_form), pos="noun",
        meaning="Pistol hears French moi as a unit of ransom. The native pseudo-coin repeats the sound of the first-person object pronoun.",
        semanticId="lex.moy_pistol_coin", derivationKeys=["i"], usageScope="editorial-exception",
        status="authored", historicalForms=[], origin="Source-specific reanalysis of the native object form of I in Henry V 4.4.")
    glosses["moy_pistol_coin"] = "moy (imagined coin)"
    for key, (root, expected, slip, label, decision) in (LESSON_READINGS | FLUELLEN_READINGS | COURT_READINGS).items():
        if language.lexicon[root]["form"] != expected or not set(slip) <= language.letters:
            raise ValueError(f"Unrecognized source form for a dramatic pronunciation: {key}")
        part = "particle" if root=="this" else "noun"
        if key in COURT_READINGS:
            part = language.lexicon[root]["pos"]
        if key in FLUELLEN_READINGS:
            part = "adjective" if root in {"big", "bashful", "bloody"} else "noun"
        entries[key] = dict(form=slip, roman=language.reading(slip), pos=part,
                            meaning=decision, semanticId="lex."+key, derivationKeys=[root],
                            usageScope="editorial-exception", status="authored", historicalForms=[],
                            origin=("Source-specific courtship pronunciation or citation in Henry V 5.2." if key in COURT_READINGS
                                    else "Source-specific learner pronunciation in Henry V 3.4." if key in LESSON_READINGS
                                    else "Source-specific Welsh captain's pronunciation in Henry V 5.1."
                                    if key == "fluellen_ploody"
                                    else "Source-specific Welsh captain's pronunciation in Henry V 4.8."
                                    if key in {"fluellen_plows", "fluellen_pashful"}
                                    else "Source-specific Welsh captain's pronunciation in Henry V 4.7."))
        glosses[key] = label
    return entries, glosses


def prepare():
    add_source_entries("henry-v", "henry-iv-part-2", lexical_entries,
                       "Keep the Chorus's imagined battlefield distinct from the playhouse. The bishops' valuation and Canterbury's later genealogy are their spoken claims.")


if __name__ == "__main__":
    prepare()
