"""The friends of Verona, their servants and the court at Milan."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "valentine_verona_friend": ("valentin", "Valentine", "The friend who goes first to Milan and falls in love with Sylvia."),
    "valentinus_antonio_form": ("valentinus", "Valentinus", "Antonio's alternate form of Valentine's name when he gives his son instructions."),
    "proteus_verona_friend": ("proteos", "Proteus", "Antonio's son and Valentine's friend. His own changes of allegiance echo the name of the mythic shape-changer."),
    "julia_verona_beloved": ("yulia", "Julia", "Proteus's beloved in Verona. She later travels dressed as the page Sebastian."),
    "lucetta_julia_attendant": ("luseta", "Lucetta", "Julia's waiting-gentlewoman and counsellor about suitors."),
    "sylvia_milan_daughter": ("silvya", "Sylvia", "The Duke's daughter. The local witness spells the name Sylvia."),
    "thurio_milan_suitor": ("turio", "Thurio", "The suitor favored by Sylvia's father."),
    "eglamour_sylvia_escort": ("eglamor", "Eglamour", "The knight named in the opening discussion of suitors and called upon to help Sylvia leave Milan."),
    "antonio_proteus_father": ("antonyo", "Antonio", "Proteus's father in Verona."),
    "pantino_antonio_attendant": ("pantino", "Pantino", "Antonio's attendant, who recommends sending Proteus to court."),
    "mercatio_julia_suitor": ("merkatsio", "Mercatio", "The rich man discussed by Julia and Lucetta, distinct from Mercutio."),
    "alphonso_court_traveller": ("alfonso", "Alphonso", "The gentleman whose party travels to greet the emperor."),
    "sebastian_julia_disguise": ("sebastyan", "Sebastian", "The page identity taken by Julia. References to the page keep this name while stage directions identify Julia."),
    "nan_lance_housemaid": ("nan", "Nan", "Lance's family maid, represented by his hat in the mock farewell."),
    "merops_phaeton_father": ("merops", "Merops", "The father the Duke assigns to Phaeton in his rebuke to Valentine about driving the heavenly chariot."),
    "gregory_well_saint": ("gregori", "Gregory", "Saint Gregory in the name of the well where Proteus says he will meet Thurio."),
    "patrick_sylvia_confessor": ("patrik", "Patrick", "The friar at whose cell Sylvia proposes to make confession. Distinct from Saint Patrick."),
    "lawrence_forest_friar": ("lawrens", "Lawrence", "The friar who recognizes Eglamour and tentatively identifies his masked companion, according to the Duke's report."),
    "ursula_sylvia_attendant": ("ursula", "Ursula", "Sylvia calls on her to bring the portrait. Distinct from the attendant in Messina."),
    "moyses_forest_outlaw": ("moyses", "Moyses", "Member of the forest band pursuing Eglamour. This is a separate person from the biblical Moses."),
    "valerius_forest_outlaw": ("valerius", "Valerius", "Moyses's companion in the pursuit of Eglamour, distinct from the Roman Valerius."),
}

SENSES = {
    "speed_valentine_servant": (["speed"], "Speed", "proper", "Valentine's quick-witted servant. His name is rendered by the native word for speed."),
    "lance_proteus_servant": (["lance"], "Lance", "proper", "Proteus's servant and Crab's keeper. The familiar name shares its form with the native weapon word."),
    "crab_lance_hound": (["sour", "apple"], "Crab", "proper", "Lance's dog. The crabapple reading carries Lance's joke about the dog's sour nature."),
    "duke_sylvia_father": (["duke"], "Duke", "proper", "Sylvia's father, the unnamed ruler at Milan."),
    "emperor_milan_court": (["imperial", "lord"], "Emperor", "noun", "Title for the ruler of the court to which the young gentlemen travel. The local cast list also designates him Duke."),
    "beadsman_prayer_intercessor": (["prayer", "servant"], "beadsman", "noun", "A person who undertakes to pray for another, as Proteus promises to do for Valentine."),
    "mutton_sheep_jest": (["sheep", "flesh"], "mutton", "noun", "Sheep or its flesh, reused in Speed's matched jests about himself and the woman receiving the letter."),
    "lace_dress_mutton": (["garment_lacing"], "laced", "adjective", "Lacing of a woman's fashionable clothing in the disparaging laced-mutton jest."),
    "nod_yes_fool": (["nod", "yes"], "noddy-fool", "noun", "Proteus's teasing name for a fool, built in this exchange by putting the native nod and assent together."),
    "descant_upper_voice": (["high", "musical_part"], "descant", "noun", "The contrasting upper part improvised against a melody in Lucetta's musical retort."),
    "mean_middle_voice": (["middle", "musical_part"], "mean", "noun", "The middle vocal part, contrasted with the unruly bass."),
    "knit_yarn_stitches": (["yarn", "weave"], "knit", "verb", "Interlink successive loops of yarn to make cloth, as in Lance's example of making a stocking."),
    "brew_ale": (["ale", "make"], "brew", "verb", "Brew a drink from malt. One of the household arts listed in Lance's paper."),
    "outlaw_forest_band": (["outside", "law", "man"], "outlaw", "noun", "A member of the exiled band that intercepts Valentine and Speed. The three numbered speakers retain their individual ordinals."),
    "allycholly_host_error": (["melancholy"], "melancholy (clipped)", "adjective", "The Host's garbled word for melancholy when he addresses Julia in disguise. The native word loses its opening syllable."),
    "pillory_neck_wood": (["neck", "wood"], "pillory", "noun", "The public wooden restraint in which Lance stands for the dog's killing of geese; distinct from the stocks in which he sits."),
    "periwig_false_hair": (["false", "hair"], "wig", "noun", "Artificial hair worn on the head; Julia considers matching Sylvia's auburn hair with a wig."),
}


def lexical_entries(language):
    entries, glosses = build_entries(language, NAMES, SENSES)
    base = language.lexicon["melancholy"]["form"]
    assert base.startswith("wé")
    clipped = base[2:]
    entries["allycholly_host_error"].update(form=clipped, roman=language.reading(clipped),
        origin="Host's comic clipping of the inherited melancholy form in 4.2.")
    return entries, glosses


def prepare():
    add_source_entries("the-two-gentlemen-of-verona", "the-tempest", lexical_entries,
        "Keep the Verona friends and their two servants distinct. Follow the local witness's personal names, its alternation of ducal and imperial titles, and Julia's identity beneath the page's disguise.",
        inherited_glosses={"kjv_spokesman": "spokesman", "kjv_cord": "cord",
                          "kjv_zeal": "zeal", "kjv_parable_teaching": "parable",
                          "kjv_breeches": "breeches", "kjv_drink_substance": "drink",
                          "kjv_urinate": "urinate", "kjv_stocks_feet": "foot-stocks",
                          "kjv_force_assault": "force-sexually"})


if __name__ == "__main__":
    prepare()
