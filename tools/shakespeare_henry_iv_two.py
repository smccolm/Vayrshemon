"""Source-specific names and senses for Henry IV, Part 2."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries


NAMES = {
    "bardolph_lord": ("bardolf", "Bardolph", "The rebel lord who brings Northumberland secondhand news, distinct from Falstaff's companion Bardolph."),
    "blunt_family": ("blunt", "Blunt", "The surname used in the plural in Lord Bardolph's false report that Douglas killed both Blunts."),
    "travers_retainer": ("traverz", "Travers", "Northumberland's servant sent out for news."),
    "morton_retainer": ("morton", "Morton", "Northumberland's retainer who saw the fall of Hotspur at Shrewsbury."),
    "john_umfrevile": ("jon", "John", "Sir John Umfrevile's given name in Travers's account."),
    "umfrevile_knight": ("umfrevil", "Umfrevile", "Sir John who first gave Travers glad news. The unidentified later horseman brings contrary news."),
    "chester_city": ("Ñester", "Chester", "City for which the unknown rider asks the way."),
    "pomfret_castle": ("pomfret", "Pomfret", "Castle where the deposed Richard's blood is figuratively scraped from the stones."),
}
SENSES = {
    "rumour_player": (["rumour"], "Rumor", "proper", "The personification of rumor who wears a costume painted with tongues. Uses the ordinary native word for rumor."),
    "induction_play": (["begin", "speech"], "Induction", "noun", "The opening presentation before the acts of the play."),
}


def lexical_entries(language):
    return build_entries(language, NAMES, SENSES, {"chester_city", "pomfret_castle"})


def prepare():
    add_source_entries("henry-iv-part-2", "henry-iv-part-1", lexical_entries,
                       "Keep Rumor's knowingly false dispatch distinct from the actual outcome and from Morton's eyewitness account. Lord Bardolph is not Falstaff's companion.")


if __name__ == "__main__":
    prepare()
