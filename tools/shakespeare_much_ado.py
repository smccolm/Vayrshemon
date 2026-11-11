"""Localized names and native wordplay in the Messina play."""
from tools.shakespeare_lexicon import add_source_entries, lexical_entries as build_entries
from tools.unta_language import quantity


NAMES = {
    "europa_joves_beloved": ("europa", "Europa", "The woman approached by Jove in bull form. Claudio plays her name against the continent in the preceding line."),
    "beat_interrupted_beatrice": ("beat", "Beat–", "Benedick's interrupted beginning of Beatrice's name after she calls Hero undone. Not a new person."),
    "john_legendary_priest": ("jon", "John", "Prester John, the legendary priest-ruler whose foot Benedick offers to measure. The priestly title is spoken separately."),
    "philemon_host_of_jove": ("filemon", "Philemon", "The poor householder who received Jove in the story of Baucis and Philemon, distinct from the Pauline correspondent."),
    "adam_ballad_archer": ("adam", "Adam", "The accomplished archer in Benedick's bottle-and-cat boast, traditionally identified as Adam Bell. Only Adam is spoken here."),
    "leonato_messina_governor": ("leonato", "Leonato", "Governor of Messina, Hero's father and Beatrice's uncle."),
    "messina_sicilian_city": ("mesina", "Messina", "The city governed by Leonato, host to the returning soldiers."),
    "hero_leonato_daughter": ("hero", "Hero", "Leonato's daughter. Distinct from the lover of Leander and from the common noun for a brave person."),
    "beatrice_leonato_niece": ("beatris", "Beatrice", "Leonato's niece, Hero's cousin and Benedick's verbal opponent."),
    "pedro_aragon_prince": ("pedro", "Pedro", "The prince returning from war, half-brother to John and patron of Claudio."),
    "aragon_princes_region": ("aragon", "Aragon", "The territory of Don Pedro's princely title."),
    "claudio_messina_soldier": ("klawdiwo", "Claudio", "The Florentine soldier honored by Pedro and suitor to Hero. Distinct from Isabella's imprisoned brother in Vienna."),
    "padua_benedicks_city": ("paduwa", "Padua", "Benedick's city of origin."),
    "balthasar_messina_singer": ("baltasar", "Balthasar", "The member of Pedro's company who sings during the staged conversation for Benedick."),
    "john_pedros_halfbrother": ("jon", "John", "Don Pedro's illegitimate half-brother; he later directs the plot against Hero."),
    "antonio_leonato_brother": ("antoniyo", "Antonio", "Father named in the Act 1 direction introducing Antonio's son after Leonato asks his brother about his son. Keep the unexpanded brother label in his speeches. The masked Antonio is a separate stage role in the supplied arrangement."),
    "antonio_ursulas_dance_partner": ("antoniyo", "Antonio", "The masked Signior Antonio who enters with Pedro after Leonato and his brother step aside. Ursula identifies him by his nod and dry hand. Distinct stage role from the elder brother, whom other editions sometimes call Antonio."),
    "anthony_leonato_brother": ("antoni", "Anthony", "Leonato explicitly addresses his elder brother as Anthony in Act 5. Keeps the witnessed spelling separate from the Antonio who dances with Ursula."),
    "conrade_john_follower": ("konrad", "Conrade", "Don John's companion, eventually arrested with Borachio."),
    "margaret_hero_attendant": ("margaret", "Margaret", "Hero's attendant. Borachio's scheme uses her presence at the window."),
    "meg_margaret_familiar": ("meg", "Meg", "Hero's affectionate shortened address for Margaret as she dresses for the wedding."),
    "ursula_hero_attendant": ("ursula", "Ursula", "Hero's gentlewoman, who helps stage the conversation meant for Beatrice."),
    "francis_messina_friar": ("fransis", "Francis", "The friar at Hero's wedding. Distinct from Francis Seacoal."),
    "hugh_watchman_given": ("hyu", "Hugh", "Hugh Oatcake, a watchman commended for his literacy."),
    "george_watchman_given": ("jorj", "George", "George Seacoal, proposed with Hugh Oatcake for the office of constable on the watch."),
    "francis_seacoal_given": ("fransis", "Francis", "The given name spoken in Dogberry's later request for Francis Seacoal. Preserve the witnessed difference from George Seacoal without assuming identity."),
}

SENSES = {
    "buckler_fastening_screw": (["turn","fasten"], "fastening screw", "noun", "The turning fastener that fits a spike into a buckler. Margaret and Benedick play on the weapons' sexual implications."),
    "worm_conscience_name": (["drama_native_worm"], "Worm", "proper", "Benedick gives the gnawing conscience the title Don Worm."),
    "plaintiff_court_claimant": (["claim","person"], "plaintiff", "noun", "The party bringing a claim. Dogberry twice applies the title to prisoners who are accused."),
    "lackbeard_claudio_nickname": (["without","beard"], "Lackbeard", "proper", "Benedick's taunting nickname for Claudio after issuing the challenge."),
    "dissembly_dogberry_error": (["apart","assemble"], "dissembly", "noun", "Dogberry breaks his assembly apart while asking whether the whole company has assembled."),
    "burglary_housebreaking": (["house","theft"], "burglary", "noun", "House theft, the erroneous charge Dogberry calls the report of Hero's false accusation."),
    "comfect_confection_nickname": (["sweetmeat"], "Comfect", "proper", "The mocking sweetmeat title Beatrice gives Claudio in her fury at the denunciation."),
    "watch_examination_record": (["question","record"], "examination", "noun", "The formal questioning and its written record. Dogberry later forces the noun into a verb in his instructions."),
    "headborough_messina_watch": (["town","guard"], "headborough", "noun", "Verges's local watch office in the entrance before Leonato, distinct from Dogberry's constable title."),
    "noncome_dogberry_error": (["no","mind"], "noncome", "noun", "Dogberry's mangling of the legal phrase for being of unsound mind. His native no-mind is an improvised expression, not a judicial finding."),
    "benedick_paduan_soldier": (["blessed"], "Benedick", "proper", "Pedro's Paduan soldier. His name is rendered with the native root for blessed so the sound of the blessed thistle in Margaret's teasing prescription recalls his name throughout the play."),
    "benedictus_herb_epithet": (["blessed"], "benedictus", "adjective", "The blessed in blessed thistle. The same native root names Benedick. Beatrice isolates this epithet three times, sensing that Margaret is teasing her."),
    "rebato_wired_collar": (["neck","ruff"], "rebato", "noun", "The raised collar Margaret compares while Hero chooses what to wear."),
    "light_o_love_song": (["light_weight","love"], "Light o' love", "proper", "The song Margaret proposes, whose lightness leads to the joke about a burden and sexual levity."),
    "desartless_watch_error": (["merit","without"], "desartless", "adjective", "Dogberry asks who is most without merit when choosing a worthy constable. Keeps the negative in his wrong word."),
    "watch_bill_hooked_weapon": (["kjv_hook","blade","staff"], "watch bill", "noun", "The watchman's hooked pole weapon. Borachio also hears a merchant's bill in the joke about being taken up on credit."),
    "deformed_imaginary_thief": (["deformed"], "Deformed", "proper", "The watchman mistakes the repeated adjective describing fashion for a thief's name. The native adjective supplies the identical spoken name."),
    "spaniard_clothing_style": (["spaniard_guest"], "Spaniard", "noun", "A person in Spanish dress in Pedro's imagined costume. The native Spanish demonym is shared with the unnamed guest in Cymbeline."),
    "bell_sounding_tongue": (["drama_native_bell","tongue"], "clapper", "noun", "The tongue that strikes a bell, compared with the tongue that voices Benedick's thoughts."),
    "haggard_wild_hawk": (["wild","hawk"], "haggard hawk", "noun", "The untamed hawks from the crags to which Hero compares Beatrice's spirits."),
    "vane_turning_wind": (["wind","turn"], "weather vane", "noun", "The vane that turns with every wind in Hero's description of Beatrice's mockery."),
    "sheet_paper_and_bed": (["sheet_linen"], "sheet", "noun", "A single flat sheet of writing material, extended from the native linen-sheet word. The two names on the paper are also imagined together in bed."),
    "orthography_precise_spelling": (["exact","writing"], "orthography", "noun", "Correct spelling personified, Benedick's caricature of Claudio's newly elaborate speech."),
    "love_claudio_mock_title": (["love"], "Love", "proper", "The mock personification Monsieur Love, here directed at Claudio in the prince's company."),
    "lady_fame_messenger": (["lady","rumour"], "Lady Fame", "proper", "The personification who carries news. Benedick casts himself in her part."),
    "lady_tongue_beatrice": (["lady","tongue"], "Lady Tongue", "proper", "Benedick's mock name for Beatrice, paired with his earlier Lady Disdain."),
    "cham_legendary_ruler": (["king"], "Cham", "noun", "The title of the Great Khan in Benedick's imaginary errand for a hair from his beard."),
    "pygmies_legendary_people": (["kjv_cubit","people"], "Pygmies", "proper", "The small people of classical legend. The native cubit-and-people name reflects the forearm measure in the traditional name."),
    "harpy_winged_woman": (["wing","claw","woman"], "harpy", "noun", "The winged, taloned female creature invoked as an insult against Beatrice. Distinct from Macbeth's Harpier."),
    "roasting_spit_rod": (["roast","rod"], "roasting spit", "noun", "The roasting spit Benedick imagines Hercules turning for Beatrice."),
    "count_messina_rank": (["earl_rank"], "count", "noun", "The rank of a count in Claudio's and John's titles. It shares the established native rank form with earl."),
    "repentance_after_wedding": (["heart","repent"], "repentance", "noun", "Regret for getting married, personified as the limping dancer in Beatrice's comparison."),
    "jig_quick_dance": (["quick","dance"], "jig", "noun", "A quick lively dance. Beatrice runs its speed into her image of hasty wooing."),
    "parish_clerk_responses": (["church_building_native","answer"], "parish clerk", "noun", "The clerk who gives the congregation's liturgical responses, Margaret's teasing role for Balthasar."),
    "hunting_horn_signal": (["hunt","horn"], "bugle", "noun", "The horn sounded by a huntsman. Benedick invokes the cuckold's horns."),
    "recheat_return_call": (["return","horn","call"], "recheat", "noun", "The hunting call sounded on the horn to bring the hounds back."),
    "baldric_horn_strap": (["shoulder","belt"], "baldrick", "noun", "The belt across the shoulder from which a hunter's horn can hang."),
    "key_music_pitch": (["song","sound"], "musical key", "noun", "The pitch or key in which to join the song, used figuratively to ask in what tone to answer Claudio."),
    "don_aragon_honorific": (["lord"], "Don", "noun", "The Iberian honorific of Pedro and John, rendered as a native title."),
    "signior_messina_address": (["sir"], "Signior", "noun", "The Italian courtesy title rendered with the native respectful male address. Distinguished from Don."),
    "mountanto_benedick_nickname": (["up","thrust"], "Mountanto", "proper", "Beatrice's name for Benedick, from the upward fencing thrust."),
    "flight_archery_shot": (["long","arrow"], "flight", "noun", "Long-distance archery with a flight arrow; contrasts with the blunt bird-bolt in Beatrice's story."),
    "trencherman_hearty_eater": (["trencher_plate","eat"], "trencherman", "noun", "A vigorous eater at table. Beatrice gives eating the language of soldierly valor."),
    "hat_forming_block": (["hat","shape"], "hat block", "noun", "The mould giving a hat its fashionable shape; Beatrice compares Benedick's fidelity to the newest hat style."),
    "turncoat_changing_side": (["turn","coat"], "turncoat", "noun", "Someone changing sides as though turning a coat, here Courtesy personified in Benedick's reply."),
    "borachio_john_follower": (["wine","skin"], "Borachio", "proper", "Don John's follower. The native wineskin speaking name carries the wine-vessel association and prepares his talk of drinking during the watch scene."),
    "lady_disdain_beatrice": (["lady","scorn"], "Lady Disdain", "proper", "Benedick's mock title for Beatrice. The native word for scorn also answers him in her next line."),
    "dogberry_messina_constable": (["dog","bush","fruit"], "Dogberry", "proper", "The constable's speaking name expressed with dog, bush and fruit."),
    "verges_dogberry_partner": (["staff"], "Verges", "proper", "The partner constable's name read as an officer's verge or staff. A competing reading hears verjuice, the sour juice of unripe fruit."),
    "oatcake_watch_surname": (["horse","grain_kernel","cake"], "Oatcake", "proper", "The watchman's oat-and-cake surname. A native horse-grain expression specifies oats, a familiar feed grain."),
    "seacoal_watch_surname": (["sea","coal"], "Seacoal", "proper", "The coal-by-sea surname borne in George Seacoal and the later Francis Seacoal address."),
}


def lexical_entries(language):
    entries, glosses = build_entries(language, NAMES, SENSES, {"messina_sicilian_city","aragon_princes_region","padua_benedicks_city"})
    refrain = language.lexicon["song_vocable_lilin"]
    _, syllable, _ = refrain["form"].split()
    entries["much_ado_nonny"] = dict(refrain, form=syllable, roman=language.reading(syllable),
        semanticId="lex.much_ado_nonny", meaning="The medial performance syllables in the established native hey-nonny-no refrain, sung twice here in each stanza.",
        origin="Selected from the existing native performance refrain to preserve the two nonnys of Balthasar's song.")
    glosses["much_ado_nonny"] = "nonny"
    laugh = language.lexicon["laugh"]["form"]
    assert laugh == "haha"
    for key, form, label in [("laughter_open_syllable", laugh[:2], "ha"),
                             ("laughter_high_syllable", "hÝ", "he")]:
        entries[key] = dict(form=form, roman=language.reading(form), pos="interjection",
            semanticId="lex."+key, usageScope="literary-exception", status="authored",
            meaning="A performed laugh in Benedick's examples of interjections at the wedding.",
            origin="A single beat of the native laughter word, with an open or a higher vowel.", historicalForms=[])
        glosses[key] = label
    for key, intended, before, after, label in [
        ("vagrom_watch_error", "wanderer", "maser", "samer", "vagrom"),
        ("vigitant_watch_error", "vigilant_watchful", "jem", "tem", "vigitant"),
        ("decerns_dogberry_error", "concern", "v×d", "d×v", "decerns"),
        ("aspicious_dogberry_error", "suspicion", "lamves", "farves", "aspicious"),
        ("suffigance_dogberry_error", "suffice", "mr×", "ml×m", "suffigance"),
        ("eftest_dogberry_error", "quick", "sßr", "sër", "eftest"),
    ]:
        base = language.lexicon[intended]
        assert base["form"].count(before) == 1
        form = base["form"].replace(before, after)
        entries[key] = dict(form=form, roman=language.reading(form), pos=base["pos"],
            semanticId="lex."+key, intendedKey=intended, usageScope="literary-exception", status="authored",
            meaning=f"Dogberry's malformed {label}. The intended native expression is {base['roman']}.",
            origin=("A deliberately altered native pronunciation confined to Dogberry's watch instructions."
                    if key in {"vagrom_watch_error","vigitant_watch_error"} else
                    ("A deliberate alteration of a native word during Dogberry's hearing." if key == "eftest_dogberry_error"
                     else "A deliberate alteration of a native word in Dogberry's report to Leonato.")),
            historicalForms=[])
        glosses[key] = label
    january = quantity(1, "ordinal")["form"] + " " + language.lexicon["month"]["form"]
    entries["january_source_month"] = dict(language.lexicon["may_source"], form=january,
        roman=language.reading(january), semanticId="lex.january_source_month", sourceCalendarMonth=1,
        meaning="January, first month of the source calendar. A hot January is Beatrice's deliberately unlikely condition.",
        origin="Source-calendar name using the first spoken Unta ordinal and the native month word.")
    glosses["january_source_month"] = "January"
    february = quantity(2, "ordinal")["form"] + " " + language.lexicon["month"]["form"]
    entries["february_source_month"] = dict(language.lexicon["may_source"], form=february,
        roman=language.reading(february), semanticId="lex.february_source_month", sourceCalendarMonth=2,
        meaning="February, second month of the source calendar. Pedro likens Benedick's face to its stormy weather.",
        origin="Source-calendar name using the second spoken Unta ordinal and the native month word.")
    glosses["february_source_month"] = "February"
    return entries, glosses


def prepare():
    add_source_entries("much-ado-about-nothing","measure-for-measure",lexical_entries,
        "Claudio of Florence, Hero of Messina and Don Pedro have their own identities. Beatrice names Benedick with a native fencing thrust; the constables' and watchmen's names use native words.")


if __name__ == "__main__":
    prepare()
