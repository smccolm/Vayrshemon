"""The Theban cousins, Athenian court and Chaucerian prologue."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "palamon_theban_cousin": ("palamon", "Palamon", "Arcite's cousin and Creon's nephew. The two prisoners fall in love with Emilia."),
    "arcite_theban_cousin": ("arsit", "Arcite", "Palamon's cousin, the other Theban kinsman. His own name is distinct from the name he uses in Athens."),
    "creon_theban_king": ("kreon", "Creon", "The ruler of Thebes who denies burial to the queens' husbands, and uncle of the two kinsmen."),
    "emilia_hippolyta_sister": ("emilya", "Emilia", "Hippolyta's sister. Palamon and Arcite see her from prison."),
    "pirithous_theseus_friend": ("piritous", "Pirithous", "Friend of Theseus, escorting the bride in the interrupted wedding procession."),
    "artesius_athenian_soldier": ("artesios", "Artesius", "The Athenian officer Theseus dispatches to assemble forces."),
    "capaneus_queen_husband": ("kapaneos", "Capaneus", "The first queen's dead husband. Theseus recalls meeting him at the altar of Mars before his wedding."),
    "chaucer_source_poet": ("choser", "Chaucer", "The poet the prologue names as the source of the story, imagined speaking from his grave."),
    "aulis_muster_place": ("aulis", "Aulis", "The banks where Theseus directs Artesius to muster troops."),
    "valerius_theban_messenger": ("valerius", "Valerius", "The Theban who summons the cousins to Creon and reports Theseus's declaration. Distinct from the forest outlaw in Verona."),
    "flavina_emilia_beloved": ("flavina", "Flavina", "Emilia's childhood companion, who died when they were both eleven. Emilia compares their attachment with that of Pirithous and Theseus."),
    "arcas_may_dancer": ("arkas", "Arcas", "One of the three dancers named by the countrymen before they meet Arcite."),
    "sennois_may_dancer": ("senoi", "Sennois", "The second of the three named dancers, grouped with Arcas and Rycas."),
    "rycas_may_dancer": ("rikas", "Rycas", "The third of the dancers praised in the countrymen's talk of the May festivities."),
    "emily_theseus_address": ("emili", "Emily", "Theseus's shorter form when addressing Emilia after he orders Arcite to attend her. Both forms denote Hippolyta's sister."),
    "gerald_morris_master": ("jerald", "Gerald", "The schoolmaster named by the dancers in their rehearsal."),
    "timothy_morris_drummer": ("timoÕi", "Timothy", "The taborer called in by name. Uses the inherited local form of Timothy for a distinct dramatic person."),
    "fritz_may_dancer": ("frits", "Fritz", "One of the five countrywomen who enter to dance in the local witness."),
    "maudlin_may_dancer": ("maudlin", "Maudlin", "Countrywoman who arrives with Fritz; distinct from the daughter who joins the dance later."),
    "luce_may_dancer": ("lus", "Luce", "The small dancer described as white-legged, distinct from the servant of Adriana."),
    "barbary_may_dancer": ("barbari", "Barbary", "The lively dancer named alongside Luce; distinct from the North African coast in the Daughter's song."),
    "nell_may_dancer": ("nel", "Nell", "The freckled countrywoman who speaks in the dance rehearsal."),
    "cicely_absent_dancer": ("siseli", "Cicely", "The needleworker's daughter who pledged to join the dance and is missing."),
    "meleager_boar_hunter": ("meleager", "Meleager", "The hero named with the boar in Gerald's instructions to the dancers."),
    "george_alow_ballad": ("jorj alou", "George Alow", "Name in the Daughter's seafaring ballad. The song gives no further identity or history."),
    "pallas_schoolmaster_invocation": ("palas", "Pallas", "The goddess invoked by the schoolmaster before he addresses the Duke."),
    "castor_theseus_oath": ("kastor", "Castor", "The divine twin by whom Theseus swears when he interrupts the duel. Uses the inherited form of the name. The ship's figurehead in Acts is a separate reference."),
    "robin_daughter_ballad": ("robin", "Robin", "The named Robin in the song title the Daughter gives her uncle. No identity for him beyond the title is asserted."),
    "ganymede_joves_youth": ("ganimed", "Ganymede", "The youth seized by Jove in Emilia's comparison. The same localized name is used in Rosalind's disguise."),
    "pelops_smooth_shoulder": ("pelops", "Pelops", "The man whose smooth shoulder Emilia compares with Arcite's brow."),
    "geraldo_daughter_name": ("jeraldo", "Geraldo", "The Daughter's form of the schoolmaster's name. She calls him Emilia's schoolmaster; this is her own account."),
    "proserpine_flower_queen": ("proserpin", "Proserpine", "The goddess with whom the Daughter imagines gathering flowers among the blessed."),
}

SENSES = {
    "sedge_lakeshore": (["fen_marsh", "grass"], "sedge", "noun", "The grasslike wetland plant distinguished from reeds along the lake where the Wooer hears the Daughter."),
    "daffodil_trumpet_blossom": (["trumpet", "flower"], "daffodil", "noun", "The trumpet-shaped spring flower in the garlands imagined by the Daughter."),
    "sail_bowline": (["sail", "edge", "string"], "bowline", "noun", "The line at the windward edge of a sail in the family's make-believe voyage. The source calls for the line itself."),
    "foil_contrasting_backing": (["back", "shadow"], "foil", "noun", "A contrasting background that brings another's qualities out, as a backing sets off a jewel. Emilia initially describes Palamon as Arcite's foil."),
    "baldric_sword_belt": (["sword", "belt"], "sword-belt", "noun", "The ornamented baldric suspending a knight's sword at his thigh."),
    "barley_break_game": (["kjv_barley", "tag_game"], "barley-break", "noun", "The chasing game the Daughter imagines playing with the blessed. Retains the grain element of the game's name."),
    "gammon_cured_ham": (["salt_pork", "thigh"], "gammon", "noun", "A cured hind leg of pork, compared with the sufferers endlessly boiling in the Daughter's vision."),
    "heavenly_limiter": (["heavenly", "apportion_allot"], "heavenly-limiter", "noun", "The unnamed heavenly disposer who determines where the cousins' vessels arrive. No additional named god is supplied."),
    "pleurisy_people_image": (["lung_organ", "fever"], "pleurisy", "noun", "The painful chest illness in Arcite's figure of a world overfull of people, cured by Mars through bloodshed. The disease image remains part of his praise of war."),
    "strike_grain_measure": (["grain_kernel", "measure"], "strike", "noun", "The source grain measure in the imagined mare's dowry of oats. The amount is kept in strikes without an inferred conversion."),
    "stool_ball_game": (["stool", "ball"], "stool-ball", "noun", "The ball game named by the Daughter when discussing their visit to the world's end. The dialogue's sexual suggestion remains in the exchange."),
    "fit_recurring_bout": (["return", "disease_ailment"], "fit", "noun", "The bout that the Daughter expects in the man she takes for Palamon. She specifies an hour without describing any symptoms."),
    "philomel_nightingale": (["philomel", "bird"], "Philomel", "noun", "A nightingale called by the mythic name. Theseus hears two rival birds singing."),
    "calkin_horseshoe_heel": (["iron", "heel"], "calkin", "noun", "The projecting iron heel of a horseshoe. The calkins strike the Athenian paving in Pirithous's account."),
    "rowel_spur_wheel": (["spur", "wheel"], "rowel", "noun", "The spur's small sharp wheel, which only agitates the horse further."),
    "jailer_athens_prison": (["jailer_role"], "Jailer", "noun", "The keeper of Theseus's prison and father of the young woman who helps Palamon."),
    "daughter_athens_jailer": (["daughter"], "Daughter", "noun", "The Jailer's unnamed daughter, first seen bringing rushes for the prisoners' room."),
    "wooer_jailer_daughter": (["suitor"], "Wooer", "noun", "The Jailer's daughter's unnamed suitor, who discusses her marriage settlement with her father."),
    "narcissus_garden_flower": (["narcissus", "flower"], "narcissus", "noun", "The garden flower sharing the mythic youth's name. Emilia immediately recalls his love for himself; the biblical namesake is unrelated."),
    "fescue_reading_pointer": (["read", "rod"], "reading-pointer", "noun", "A schoolroom pointer used to follow letters in reading. The countryman's joke retains the suggestive rod in the wife's fist."),
    "plane_spreading_tree": (["broad", "canopy", "tree"], "plane-tree", "noun", "The broad-spreading plane tree against which the quoted cedar's spreading crown is compared."),
    "virginals_keyboard": (["keyboard_jack", "string", "instrument"], "virginals", "noun", "The keyed string instrument named in Palamon's innuendo about what a young woman did in an arbor. Reuses the native term for the wooden jack in Sonnet 128."),
    "beech_smooth_bark": (["smooth", "tree"], "beech", "noun", "The broad beech recalled by Arcite while the cousins tease one another about former encounters."),
    "aglet_plain_tip": (["clothing_lace", "metal"], "aglet", "noun", "A little metal end of a lace, the shape used for the distant stars. Distinct from Grumio's figurative aglet-baby."),
    "bavian_mask_dancer": (["tail", "monkey"], "Bavian", "noun", "The rustic dancer dressed as a baboon, assigned a tail and a tumbling part in the morris."),
    "taborer_morris_musician": (["tabor_small_drum", "man"], "Taborer", "noun", "The performer on the small drum, called Timothy by one of the countrymen."),
    "tediosity_schoolmaster": (["tedious", "weary"], "tediosity", "noun", "Gerald's overgrown term of complaint, formed by adding weary again to the native word for tedious."),
    "disinsanity_schoolmaster": (["not", "healthy", "mind"], "disinsanity", "noun", "Gerald's pompous description of the rustics' confusion, with the negation put before healthy mind."),
    "morr_dance_first_sound": (["morris_dance"], "Morr", "noun", "Gerald's invented beginning of the name of the dance. It joins the following fragment without any intervening sound."),
    "is_dance_last_sound": (["morris_dance"], "is", "noun", "The rest of the dance name as Gerald playfully divides it. The meaning comes only from the two sounds rejoined."),
    "beest_cow_first_milk": (["birth", "milk"], "beestings", "noun", "The rich first milk following calving, eaten by the Clown of the morris."),
    "penner_writing_case": (["pen", "case"], "pen-case", "noun", "The case for pens that Gerald offers at the Duke's feet."),
    "maiden_pink_blossom": (["maiden", "flower"], "maiden-pink", "noun", "The lightly scented wedding flower named by the singing boy; the name designates the flower rather than a color."),
    "larksheel_spurred_blossom": (["lark", "spur", "flower"], "larkspur", "noun", "The spurred flower named lark's-heels in the wedding song."),
    "oxlip_pale_bell": (["pale", "bell", "flower"], "oxlip", "noun", "The pale bell-flowered oxlip in the boy's wedding song, growing in its cradle."),
    "chough_cliff_bird": (["cliff", "crow_bird"], "chough", "noun", "The crow-family cliff bird excluded from the wedding house; hoar is a separate modifier in the song."),
    "cuckoo_nest_intruder": (["other", "nest", "bird"], "cuckoo", "noun", "The bird associated with laying in another bird's nest, called slanderous in the wedding song."),
    "bridal_gown_train": (["gown", "tail"], "gown-train", "noun", "The trailing part of Hippolyta's garment that Emilia lifts during the bridal procession."),
}


def lexical_entries(language):
    entries, glosses = build_entries(language, NAMES, SENSES, {"aulis_muster_place"})
    sound = language.lexicon["morris_dance"]["form"]
    assert sound == "talÃ×m"
    for key, part in [("morr_dance_first_sound", sound[:3]), ("is_dance_last_sound", sound[3:])]:
        entries[key].update(form=part, roman=language.reading(part),
            origin="Schoolmaster's staged division of the native dance name in 3.5.")
    return entries, glosses


def prepare():
    add_source_entries("the-two-noble-kinsmen", "the-two-gentlemen-of-verona", lexical_entries,
        "Retain the wedding procession and sequence of the three petitioning queens. Distinguish the cousins and the two women of the Athenian household; reuse the existing Theseus, Hippolyta and Hymen.",
        inherited_glosses={"kjv_winnow": "winnow", "kjv_thresh": "thresh", "kjv_horseleech": "leech",
                          "kjv_quiver": "quiver", "kjv_file_tool": "file", "kjv_frog": "frog",
                          "kjv_willow": "willow", "kjv_bulrush": "bulrush", "kjv_dawn": "dawn",
                          "kjv_constellation": "constellation", "kjv_square": "square",
                          "kjv_pavement": "paving"})


if __name__ == "__main__":
    prepare()
