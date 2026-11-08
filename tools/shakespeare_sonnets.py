"""Authored lexical decisions for the complete Sonnets source; no automatic translation."""
from copy import deepcopy
from tools.shakespeare_project import PROJECT, read, write, materialize
from tools.unta_language import quantity

CONTEXTS = {
    'passionate_affect': ('passion', 'passionate', 'modifier', 'Moved by strong emotion, the title of The Passionate Pilgrim; native passion-family adjective, not a phonetic rendering of a common English word.'),
    'version_text': ('form', 'version', 'noun', 'A particular textual form of a poem, distinguishing early printed versions of Sonnets 138 and 144 from the main sequence.'),
    'habit_garb': ('habit_guise', 'habit', 'noun', 'Habit as manner or figurative clothing in the early Sonnet 138, where the best habit is a soothing tongue rather than the later seeming trust.'),
    'smother_conceal': ('smother', 'smother', 'verb', 'Stifle or cover from exposure, the mutual faults smothered by love in early Sonnet 138; no literal killing is added.'),
    'water_well': ('kjv_well', 'well', 'noun', 'A well used to obtain water in the love-god story of Sonnet 154; no Biblical actors, promises or historical capacity measure are imported.'),
    'refuse_waste': ('waste', 'refuse', 'noun', 'Discarded or worthless matter, metaphorically the lowest deeds in Sonnet 150; not the verb to decline.'),
    'brightness_light': ('shine', 'brightness', 'noun', 'Luminous brightness making the day fair in Sonnet 150, a nominal quality rather than divine favour.'),
    'blindness_sight': ('blind', 'blindness', 'noun', 'Lack of sight personified in Sonnet 152’s praise that denies what the eyes see; not an added medical diagnosis.'),
    'command_order': ('command', 'command', 'verb', 'Give an authoritative order, the beloved’s eyes commanding the speaker’s best qualities in Sonnet 149.'),
    'ground_basis': ('ground', 'ground', 'noun', 'The basis of an attitude or claim, Sonnet 142’s hate grounded on sinful loving; nominal metaphor, not a geological assertion.'),
    'duration_term': ('time', 'term', 'noun', 'An allotted duration or tenure, the divine terms exchanged for mortal hours in Sonnet 146; no exact number of years is supplied.'),
    'outer_surface': ('outside', 'outer', 'modifier', 'On the exterior, the bodily walls painted bright in Sonnet 146; not a change to the underlying body metaphor.'),
    'pleasure_delight': ('delight', 'delight', 'verb', 'Give pleasure, or be pleased in passive voice; the ears denying pleasure in the beloved’s tune in Sonnet 141.'),
    'ending_added': ('end', 'ending', 'noun', 'An appended completion of an utterance, the not-you ending in Sonnet 145; not a death.'),
    'income_return': ('yield', 'revenue', 'noun', 'Income or return from a holding, metaphorically the revenues of other beds in Sonnet 142; no tax or particular amount is introduced.'),
    'wit_faculty': ('wit', 'wit-faculty', 'noun', 'An inward mental faculty, the source’s five wits in Sonnet 141. Keeps the conventional count without inventing a particular historical list or narrowing wit to verbal cleverness.'),
    'sensual_sense': ('sense', 'sensual', 'modifier', 'Pertaining to bodily sensation and sensual enjoyment, Sonnet 141’s feast of the senses; not a diagnosis or a moral doctrine.'),
    'pine_languish': ('languish', 'pine', 'verb', 'Waste or suffer inwardly, the soul and body’s opposed resources in Sonnet 146; not the tree.'),
    'dearth_scarcity': ('lack', 'dearth', 'noun', 'Want or scarcity, the soul’s deprivation despite the body’s costly decoration in Sonnet 146.'),
    'charge_expense': ('spend', 'expense', 'noun', 'Expenditure laid out on the body, eaten by worms in Sonnet 146; not a command, accusation or electric charge.'),
    'dross_material': ('kjv_dross', 'dross', 'noun', 'Unwanted metalworking residue, the low-value hours sold for divine terms in Sonnet 146. The material category is retained without importing a Biblical accusation or verse participants.'),
    'death_sonnet': ('death_personified', 'Death', 'proper', 'Personified Death feeding on humans and being overcome in Sonnet 146; no additional named character or inherited Venus narrative is introduced.'),
    'bodily_feeling': ('touch', 'feeling', 'noun', 'The bodily faculty of touch in Sonnet 141, distinguished from emotional sentiment and named beside the other senses.'),
    'careful_concern': ('care', 'concerned', 'modifier', 'Anxious attention to a loose domestic bird in Sonnet 143; careful does not simply praise technical precision.'),
    'kindness_conduct': ('goodwill', 'kindness', 'noun', 'Benevolent or affectionate conduct, the alleged deep kindness of Sonnet 152; not kinship or a kind/species.'),
    'partial_bias': ('favour', 'partial', 'modifier', 'Biased by favour for one object, the eyes’ overpartial looking in Sonnet 137; not incomplete or a numerical fraction.'),
    'hook_mooring': ('hook_trap', 'hook', 'noun', 'A curved fastening or catching hook, forged from visual falsehood to bind judgment in Sonnet 137. The source supplies no fishing bait or suspension mechanism.'),
    'habit_guise': ('clothing', 'guise', 'noun', 'Outward dress or appearance, love’s best habit in Sonnet 138; not merely a repeated behaviour.'),
    'cunning_subtlety': ('cunning', 'subtlety', 'noun', 'A deceptive fine distinction or artifice, the world’s false subtleties in Sonnet 138; not the subject’s supposed lack of artistic skill.'),
    'number_aggregate': ('number_abstract', 'number', 'noun', 'A numerical total or counted company, Sonnet 136’s number among which the speaker asks to pass uncounted. No fixed cardinal value is invented.'),
    'lending_gain': ('gain', 'profit', 'noun', 'Gain sought by lending, the usury metaphor in Sonnet 134; nominal use of the native gain root, with no asserted interest rate.'),
    'will_desire': ('will', 'will/desire', 'noun', 'Volition, appetite and sexual desire in the repeated will wordplay of Sonnets 135–136. Uses the native desire root. Bodily sexual metonymy is licensed by this context, not forced into every occurrence; the sound pun with the personal name Will cannot be reproduced exactly.'),
    'statute_security': ('bond', 'statute-bond', 'noun', 'A formally binding debt obligation invoked through beauty in Sonnet 134; not merely any written public law. The exact historical legal procedure remains a source note, not newly invented Vayrshemon law.'),
    'detain': ('hold', 'detain', 'verb', 'Keep back for a time, Nature holding her treasure in Sonnet 126; distinguished by context from keeping it forever.'),
    'play_music': ('play', 'play-music', 'verb', 'Perform on a musical instrument in Sonnet 128; a musical extension of the native play root rather than a game or theatrical role.'),
    'harvest_crop': ('harvest', 'harvest', 'noun', 'The yield to be reaped, kisses figured as the lips’ due harvest in Sonnet 128; nominal result of harvesting.'),
    'musical_sound': ('sound', 'sound', 'noun', 'Audible musical sound in Sonnet 130; nominal sense, neither health nor a narrow body of water.'),
    'fickle': ('change', 'fickle', 'modifier', 'Unsteady and liable to change, Time’s glass in Sonnet 126; a dispositional use, not a completed act of changing.'),
    'dun_colour': ('brown', 'dun', 'modifier', 'Dull greyish brown in Sonnet 130’s comparison with snow. A colour description, not a claim of ugliness or a racial identification.'),
    'damasked_colour': ('mix', 'damasked', 'modifier', 'Intermingled colouring, specifically red and white roses in Sonnet 130. Not patterned cloth or an asserted botanical species.'),
    'perfume_scent': ('fragrance', 'perfume', 'noun', 'A pleasing scent used in the comparison with ordinary human breath in Sonnet 130; not an invented ingredient or cosmetic recipe.'),
    'exhale_breath': ('breathe', 'exhale', 'verb', 'Send breath out; source reeks in Sonnet 130 need not assert putrid smell. Retains the native breathing form in a specifically outward sense.'),
    'artifice': ('art', 'artifice', 'noun', 'Skilled artificial contrivance, including cosmetic alteration in Sonnet 127, not specifically medical practice. Whether deceptive is supplied by the verse.'),
    'rare_excellence': ('precious', 'rare', 'modifier', 'Exceptional in worth or loveliness, Sonnet 130’s rare beloved; not merely statistically infrequent.'),
    'distraction_frenzy': ('frantic', 'distraction', 'noun', 'The mind’s agitated scattering in Sonnet 119’s maddening fever; nominal use of the native mind-release formation, not the English-like frenzy stem or an imposed modern diagnosis.'),
    'unkindness': ('unkind', 'unkindness', 'noun', 'Unkind conduct or lack of affection in Sonnet 120, nominal use of the later dramatic unkind term; the reciprocal injuries are distinct from number, species or kinship classification.'),
    'sickle': ('kjv_sickle', 'sickle', 'noun', 'The curved harvesting blade wielded by personified Time in Sonnet 116; retains the native harvest-knife category, distinct from a long-handled scythe.'),
    'nerve_sinew': ('sinew', 'sinew', 'noun', 'The resilient bodily sinews called nerves in Sonnet 120; the comparison to brass and hammered steel does not refer narrowly to modern neurological tissue.'),
    'payment': ('pay', 'payment', 'noun', 'Something given as a fee or recompense, including the reciprocal pardon metaphor in Sonnet 120; no unprinted price or currency is supplied.'),
    'oblation': ('offer', 'offering', 'noun', 'A freely offered gift of self, with ritual resonance in Sonnet 125; not automatically a slaughtered sacrifice, bribe or demanded payment.'),
    'foundation_base': ('foundation', 'foundation', 'noun', 'A supporting base for a grand construction imagined to endure in Sonnet 125; carries the native foundation form without importing Lucrece’s underground-wind account.'),
    'cherub_likeness': ('kjv_cherub', 'cherub', 'noun', 'The beautiful heavenly creature used as a comparison in Sonnet 114. Keeps the native source-category name, without equating every angel with a cherub or adding a winged infant’s anatomy.'),
    'chance_event': ('happen', 'chance-event', 'noun', 'An occurrence or contingency, Time’s millioned accidents in Sonnet 115; not restricted to a collision, injury or mishap. Nominal sense of the native happen root.'),
    'eclipse_event': ('eclipse', 'eclipse', 'noun', 'An obscuration endured by the mortal moon in Sonnet 107. Nominal event sense; the lunar/political image is retained without identifying a particular ruler, date or astronomical event.'),
    'olive_tree': ('kjv_olive', 'olive', 'noun', 'Olive as the tree or its branches, Peace’s emblem in Sonnet 107. Retains the native botanical form without importing the Genesis dove narrative.'),
    'grind_edge': ('kjv_grind', 'whet', 'verb', 'Grind to sharpen an edge, figuratively whet appetite upon fresh experiments in Sonnet 110; not pulverize appetite into meal. Native contextual extension of the grinding root.'),
    'eve_source': ('kjv_eve', 'Eve', 'proper', 'Eve, the named figure evoked by the apple comparison in Sonnet 93. Retains the historical proper-name form; the apple is Shakespeare’s allusion, not an alteration of Genesis or an ordinary borrowed noun.'),
    'patent_right': ('charter', 'patent', 'noun', 'A granted title or right of possession in Sonnet 87; the love relationship is treated as a revocable legal grant, not an invention patent.'),
    'lameness': ('lame', 'lameness', 'noun', 'Impairment in walking, offered hypothetically as a reproach in Sonnet 89; no autobiographical diagnosis is asserted.'),
    'prize': ('reward', 'prize', 'noun', 'The precious object sought by the rival poet’s figurative voyage in Sonnet 86; the beloved as desired reward, not an asserted competition payment.'),
    'dedicate': ('offer', 'dedicate', 'verb', 'Address or offer a work to its honoured subject in Sonnet 82; literary dedication, without requiring a sacred consecration ceremony.'),
    'virtue_power': ('power', 'virtue', 'noun', 'Effective potency attributed to the pen in Sonnet 81; distinct from moral excellence or religious merit.'),
    'boat': ('kjv_ship_boat_acts', 'boat', 'noun', 'A small vessel, the poet’s modest craft in Sonnet 80; no inherited shipwreck participants or subsidiary-boat story are introduced.'),
    'stealth': ('secret', 'stealth', 'noun', 'Unnoticed movement, the sundial shadow’s stealth in Sonnet 77; does not imply that the shadow has a private factual secret.'),
    'sundial': ('dial', 'sundial', 'noun', 'The shadow-measuring time dial in Sonnet 77; no mechanical hands, battery or digital display are inferred.'),
    'water_depth': ('deep', 'depth', 'noun', 'Distance below a water surface, metaphorically the patron’s inexhaustible worth in Sonnet 80; nominal depth rather than silent sound.'),
    'conquest': ('conquer', 'conquest', 'noun', 'A taking by force, the body imagined as the knife’s cowardly conquest in Sonnet 74; nominal result rather than a new historical campaign.'),
    'twilight': ('kjv_twilight', 'twilight', 'noun', 'Dim transitional light, specifically after sunset in Sonnet 73; the time is fixed by the clause, not by a new astronomical measurement.'),
    'nourish': ('kjv_nourish', 'nourish', 'verb', 'Sustain life or a flame, the nourishment consumed into ashes in Sonnet 73; native feed-life development without inherited Biblical agency.'),
    'suspicion': ('suspect', 'suspicion', 'noun', 'An adverse possibility entertained without proof, the suspect of Sonnets 70 and following; nominal suspicion, not a demonstrated fault.'),
    'counterfeit_bastard': ('false', 'counterfeit', 'modifier', 'Illegitimate or counterfeit signs of beauty in Sonnet 68; source bastard attacks the artifice, not the family status of a newly invented child.'),
    'rank_odour': ('foul', 'rank', 'modifier', 'Offensively strong smell attributed by observers in Sonnet 69; distinct from social rank.'),
    'firm_ground': ('strong', 'firm', 'modifier', 'Firmness of solid ground contrasted with the sea in Sonnet 64; physical resistance, not a moral promise or commercial company.'),
    'brass': ('kjv_brass', 'brass', 'noun', 'The durable copper-alloy monumental metal in Sonnets 64–65; the source label is retained without asserting a precise modern alloy composition.'),
    'fullness': ('full', 'fullness', 'noun', 'Satiation of the hungry eyes in Sonnet 56, nominal fullness, not a supplied numerical capacity.'),
    'adult_maturity': ('ripe', 'maturity', 'noun', 'Full development reached by a growing human life in Sonnet 60; nominal ripeness, without a stipulated age.'),
    'bodily_flourish': ('ornament', 'flourish', 'noun', 'Youthful visible splendour pierced by Time in Sonnet 60; not the existing musical fanfare sense.'),
    'blunt': ('dull', 'blunt', 'verb', 'Dull a sharp edge, the metaphorical point of rare pleasure in Sonnet 52; a physical-edge sense distinct from slow apprehension.'),
    'robe': ('kjv_robe', 'robe', 'noun', 'A long outer garment whose splendour is reserved for an occasion in Sonnet 52; no priestly office is inferred.'),
    'steadfast': ('kjv_steadfast', 'constant', 'modifier', 'Unchanging in loyalty or affection, the constant heart in Sonnet 53; no inherited Biblical participant is imported.'),
    'festival': ('kjv_feast_appointed', 'festival', 'noun', 'An infrequent celebratory observance in Sonnet 52; no particular religion or calendar day is imposed.'),
    'wardrobe': ('kjv_wardrobe_store', 'wardrobe', 'noun', 'The clothing repository hiding a splendid robe in Sonnet 52; not the private chamber of the heart in Sonnet 46.'),
    'fragrance': ('scent', 'fragrance', 'noun', 'A pleasing odour, the rose quality distinguished from visual colour in Sonnet 54; nominal olfactory sense rather than the action of tracking.'),
    'display_splendour': ('pride', 'splendour', 'noun', 'Visible magnificence of the robe kept out of sight in Sonnet 52; not necessarily arrogance.'),
    'verdict': ('judgment', 'verdict', 'noun', 'The jury’s determination of the eye/heart claim in Sonnet 46, rather than a general opinion about beauty.'),
    'liberty': ('free', 'liberty', 'noun', 'Freedom to act, shading into licence in Sonnet 41; not a constitutional guarantee added to the scene.'),
    'temptation': ('tempt', 'temptation', 'noun', 'Attraction toward a tempting act, personified as following the beautiful addressee in Sonnet 41.'),
    'flattery': ('flatter', 'flattery', 'noun', 'Coaxing praise or pleasing self-persuasion, the speaker’s openly named consolation in Sonnet 42.'),
    'grace_elegance': ('grace', 'grace', 'noun', 'Attractive bearing or elegance in the oxymoron lascivious grace, Sonnet 40; not divine forgiveness or an honorific title.'),
    'poverty': ('poor', 'poverty', 'noun', 'Having very little, the speaker’s paradoxical remaining possessions stolen in Sonnet 40; no quantitative income is inferred.'),
    'robbery': ('rob', 'robbery', 'noun', 'The act of taking what belongs to another, used for the beloved’s appropriation of love in Sonnet 40.'),
    'poetic_theme': ('subject', 'theme', 'noun', 'The subject supplied to poetic invention, source subject and argument in Sonnet 38; distinct from a subject under a sovereign or a quarrel.'),
    'borne_cross': ('kjv_cross_instrument', 'cross', 'noun', 'The carried wooden cross used as an image of suffering in Sonnet 34; not the verb cross or oppose. The Christian allusion belongs to the source, without an added named participant.'),
    'legal_advocate': ('kjv_advocate_john_epistle', 'advocate', 'noun', 'One speaking on another’s behalf in a legal case; the wronged speaker defending the beloved in Sonnet 35. Native inherited behalf-speaker form, with no divine identity carried into the new sense.'),
    'grievance': ('grieve', 'grievance', 'noun', 'A remembered sorrow or injury returned to in Sonnet 30; nominal sorrow, not a newly asserted formal complaint.'),
    'furrow': ('kjv_furrow', 'furrow', 'noun', 'A ploughed groove, transferred to Time’s wrinkles in Sonnet 22; preserves the field/face image.'),
    'pictorial_perspective': ('perspective', 'perspective', 'noun', 'The painter’s way of seeing through or rendering apparent depth in Sonnet 24; the source’s disputed optical metaphor is not restricted to one specific device.'),
    'poetic_frenzy': ('frenzy_native', 'frenzy', 'noun', 'Inspired or excessive poetic excitement attributed by future readers in Sonnet 17; not simply violent anger.'),
    'poetic_grace': ('merit', 'grace', 'noun', 'An admired quality of the beloved, enumerated in verse; not divine favour or a noble form of address.'),
    'portrait': ('image', 'portrait', 'noun', 'A painted representation of a person, source counterfeit in Sonnet 16; the word does not assert fraudulent intent.'),
    'appearance_hue': ('hue', 'hue', 'noun', 'Colour, complexion and visible form together in Sonnet 20; no biographical proper name is inferred from the word.'),
    'poetic_line': ('line', 'line', 'noun', 'A line of verse, with drawn line and lineage resonances available where the source invokes them; not an invented number of lines.'),
    'prediction': ('foretell', 'prediction', 'noun', 'A prognostic or forecast, the celestial signs the poet disclaims reading; nominal use of foretell.'),
    'sheaf': ('kjv_sheaf', 'sheaf', 'noun', 'A tied bundle of harvested stalks, the summer crop imagined on a funeral bier; not an individual grain.'),
    'bier': ('kjv_bier', 'bier', 'noun', 'A carrying frame for the dead; the harvested crop is personified, with no invented wheels.'),
    'lease_tenure': ('kjv_lease_property', 'lease', 'noun', 'Temporary holding of property rather than outright ownership; beauty’s lease and its ending in Sonnets 13 and 18.'),
    'breeding_stock': ('breed', 'stock', 'noun', 'Procreative continuance or stock in the source’s selective argument, not a shop or stored inventory.'),
    'household_management': ('manage', 'husbandry', 'noun', 'Prudent upkeep of an estate or house, also carrying the procreative husbandry metaphor; not exclusively ploughing.'),
    'poetic_conceit': ('thought', 'conceit', 'noun', 'A mental conception of transient life in Sonnet 15; no conceited vanity is implied.'),
    'temperate_mild': ('moderate', 'temperate', 'modifier', 'Mild and well-tempered, with both climate and character available in the summer comparison.'),
    'loan': ('lend', 'loan', 'noun', 'Something lent for later return, the willingly paid procreative loan of Sonnet 6; no rate is implied.'),
    'distillate': ('distil', 'distillate', 'noun', 'The liquid essence left by distillation; nominal result, the prisoner in glass in Sonnet 5.'),
    'bareness': ('bare', 'bareness', 'noun', 'The condition of being stripped of covering or growth; the winter landscape in Sonnet 5.'),
    'fuel': ('kjv_fuel', 'fuel', 'noun', 'Material sustaining a fire; the self-consuming flame of Sonnet 1, without adding a literal diet.'),
    'famine': ('kjv_famine', 'famine', 'noun', 'A severe lack of food amid abundance in Sonnet 1; contrasted with the self-fed flame.'),
    'bequest': ('bequeath', 'bequest', 'noun', 'Something left to another; nominal use in Nature’s paradoxical loan rather than outright gift.'),
    'reckoning': ('reckon', 'account', 'noun', 'An accounting of what has been received and returned; not the homonymous noble rank.'),
    'gain_profit': ('gain', 'profit', 'noun', 'A beneficial return, including the procreative financial metaphor; no numerical rate is invented.'),
    'tillage': ('kjv_husbandry_corinthians', 'tillage', 'noun', 'Cultivation of a field, retaining the sexual agricultural metaphor without turning it into a spouse noun.'),
    'vial_small': ('kjv_vial', 'vial', 'noun', 'A small liquid vessel in the distillation metaphor; not the bowls of Revelation or a modern medical container.'),
    'usury_interest': ('kjv_usury', 'interest', 'noun', 'A lending charge or return; source usury, with its forbidden/permitted contrast supplied by the clause.'),
    'steep_slope': ('kjv_steep_slope', 'steep', 'modifier', 'Sharply sloping, the sun’s climb; not the verb meaning soak.'),
    'musical_string': ('string', 'string', 'noun', 'A vibrating string on a musical instrument, participating in sympathetic resonance.'),
    'musical_part': ('part', 'part', 'noun', 'A component voice or role in a musical harmony, with the family-role metaphor retained.'),
    'height_pitch': ('height', 'height', 'noun', 'Highest elevation in the sun’s apparent course; not sticky pitch or a musical note.'),
}

DERIVATIONS = {
    'print_text': (['ink', 'press'], 'verb', 'print', 'Produce writing by an inked impression, the appendix’s first printed versions. Native ink-press; no particular press mechanism is invented.'),
    'gathering_signature': (['book', 'mark'], 'noun', 'signature', 'A printed gathering or leaf-reference mark, the source colophons sig. A 3 and sig. A 4; not an author’s handwritten name.'),
    'soothe_gently': (['gentle', 'quiet'], 'verb', 'soothe', 'Quiet or reassure gently, the soothing tongue in early Sonnet 138; can carry flattery in context without asserting truth.'),
    'bathing_pool': (['wash', 'hollow'], 'noun', 'bath', 'A hollow or basin of water for bathing, the curative fountain of Sonnets 153 and 154; native wash-hollow, distinct from the Biblical bath volume.'),
    'vowed_devotee': (['vow'], 'agent', 'votary', 'One bound by a sacred vow, a maiden who vowed chastity in Sonnet 154; a native vow-agent rather than a sound adaptation of votary.'),
    'disarm_weapons': (['weapon', 'remove'], 'verb', 'disarm', 'Deprive of a weapon, here the love-god’s torch in Sonnet 154; native weapon-remove.'),
    'invite_kindly': (['goodwill', 'summon'], 'verb', 'invite', 'Call another to join or partake, the sensual feast in Sonnet 141; native goodwill-summon, without the compulsion of an authoritative summons.'),
    'exclude_bar': (['outside', 'hold'], 'verb', 'exclude', 'Keep outside the allowed range, the desire excluded by physic in the chosen reading of Sonnet 147.'),
    'bay_sea': (['sea', 'bend'], 'noun', 'bay', 'An inlet of the sea where ships ride, the sexual metaphor of Sonnet 137; distinct from the reddish-brown horse colour.'),
    'moor_vessel': (['ship', 'tie'], 'verb', 'anchor', 'Secure at a mooring, the eyes anchored in Sonnet 137’s bay; no particular anchor design or extra rope is asserted.'),
    'ride_vessel': (['ship', 'rest'], 'verb', 'ride-at-anchor', 'Remain as a vessel on the water, Sonnet 137’s nautical ride; preserves the sexual suggestion without turning the bay into a horse pasture.'),
    'ground_plot': (['ground', 'piece'], 'noun', 'plot-of-land', 'A bounded parcel of ground, Sonnet 137’s several plot contrasted with a common place; not a secret scheme.'),
    'misconstrue': (['false', 'understand'], 'verb', 'misconstrue', 'Twist or misread another’s meaning, the ill-wresting world of Sonnet 140; no physical wrestling match is introduced.'),
    'mortgage_pledge': (['debt', 'pledge'], 'verb', 'mortgage', 'Pledge as security for debt, the speaker mortgaged to the beloved’s will in Sonnet 134; no invented interest rate or foreclosure term.'),
    'sue_debt': (['law', 'seek'], 'verb', 'sue', 'Pursue a claim through legal process, the creditor pursuing the friend’s debt in Sonnet 134; not ordinary romantic wooing.'),
    'debtor_person': (['debt'], 'agent', 'debtor', 'A person owing an obligation, the friend made liable for the speaker in Sonnet 134.'),
    'bail_release': (['pledge', 'release'], 'verb', 'bail', 'Obtain another’s release by standing as security, the speaker’s heart offered for his friend in Sonnet 133; distinct from simply escaping a prison.'),
    'wire_metal': (['metal', 'thread'], 'noun', 'wire', 'A thin strand of metal, the conventional hair comparison in Sonnet 130; native metal-thread without an unprinted golden colour.'),
    'misrepresent': (['false', 'show'], 'verb', 'misrepresent', 'Represent inaccurately, the flattering false comparisons applied to women in Sonnet 130; does not accuse the represented women of lying.'),
    'favoured_minion': (['favour', 'child'], 'noun', 'favourite', 'A cherished favourite or dependent of personified Nature in Sonnet 126, native favour-child; does not assert biological descent.'),
    'debt_discharge': (['debt', 'release'], 'noun', 'discharge', 'Release from an outstanding obligation, the quietus obtained when Nature hands over her treasure in Sonnet 126. Financial metaphor, not a named death certificate.'),
    'keyboard_jack': (['wood', 'leap'], 'noun', 'keyboard-jack', 'The moving wooden jack of a plucked keyboard instrument in Sonnet 128, imaginatively conflated with the keys touched by the hand. Not the personal name Jack or a modern piano mechanism.'),
    'wood_chip': (['wood', 'piece'], 'noun', 'wood-piece', 'A small piece of wood; the dancing chips of the keyboard in Sonnet 128. Does not turn the intact instrument into discarded splinters.'),
    'vital_spirit': (['life', 'breath'], 'noun', 'vital-spirit', 'Life force expended in Sonnet 129, retaining the sexual expenditure implication in context. Distinct from a ghost, personal soul, or a claim about modern bodily physiology.'),
    'suborn': (['fraud', 'induce'], 'verb', 'suborn', 'Induce to deceptive or corrupt testimony, the unknown informer addressed in Sonnet 125. Native fraud-induce; no actual monetary bribe or named historical conspirator is supplied.'),
    'weed_plant': (['wild', 'plant'], 'noun', 'weed', 'An unwanted or unvalued growing plant contrasted with prized flowers in Sonnet 124; native wild-plant lexicalization, not a claim that every wild flower is a weed.'),
    'cloy': (['full', 'weary'], 'verb', 'cloy', 'Weary through excess or satiation, explicitly denied of the beloved’s sweetness in Sonnet 118. Native full-weary, not simply fill or nourish.'),
    'sauce': (['taste', 'liquid'], 'noun', 'sauce', 'A flavouring accompaniment to food, the bitter sauces of Sonnet 118; native taste-liquid, distinct from a medical potion although the poem links the metaphors.'),
    'siren_creature': (['charm', 'sing'], 'agent', 'siren', 'A dangerously enchanting song-creature in Sonnet 119, native charm-sing agent. The tears are metaphorical seduction; no mermaid anatomy or named individual is supplied.'),
    'pyramid_monument': (['narrow', 'high', 'form'], 'noun', 'pyramid', 'A tapering high monument, the pyramids raised by Time in Sonnet 123. Native narrow-high-form; retains the historical pyramid/obelisk breadth without naming an Egyptian site or specifying an unprinted number of faces.'),
    'faith_breaker': (['faith', 'break'], 'agent', 'heretic', 'A breaker from an allegiance or professed faith, personified Policy opposed to constant love in Sonnet 124; native faith-break agent, without assigning a historical denomination or legal punishment.'),
    'ceremonial_canopy': (['honour', 'cloth'], 'noun', 'canopy', 'The overhead cloth borne in a ceremony of honour in Sonnet 125, native honour-cloth. Does not assume a particular royal procession or identify the poet as a historical participant.'),
    'rent_use': (['use', 'pay'], 'noun', 'rent', 'Payment for use or occupancy, the costly dwelling in outward form and favour in Sonnet 125. Native use-pay; not the source word rent meaning torn.'),
    'transmutation_art': (['change', 'art'], 'noun', 'alchemy', 'The figurative art of transforming unformed or monstrous sights into beauty in Sonnet 114. Native change-art, distinct from Sonnet 33’s specifically golden transmutation.'),
    'palate': (['mouth', 'taste'], 'noun', 'palate', 'The tasting capacity or organ metaphorically attributed to the mind as monarch in Sonnet 114; native mouth-taste, not a painter’s palette or a gust of wind.'),
    'askance_look': (['side', 'look'], 'verb', 'look-askance', 'Look obliquely or with averted regard, the speaker’s treatment of truth in Sonnet 110. Native side-look; distinct from an actor’s aside and not a claim about a permanent ocular condition.'),
    'augur': (['omen', 'read'], 'agent', 'augur', 'An interpreter of omens, the gloomy prognosticator in Sonnet 107; native omen-read agent. No specific religious office, bird species or historical person is inserted.'),
    'love_lease': (['time', 'grant'], 'noun', 'lease', 'A grant of tenure for a term, metaphorically the duration allotted to true love in Sonnet 107. Native time-grant, distinct from a permanent gift or a particular monetary rent.'),
    'strangle': (['neck', 'choke'], 'verb', 'strangle', 'Choke by constricting the neck, metaphorically kill acquaintance in Sonnet 89; preserves the violent self-denial without introducing an actual victim.'),
    'rhetoric': (['speech', 'art'], 'noun', 'rhetoric', 'Crafted persuasive or ornamental expression, whose strained touches are challenged in Sonnet 82; native speech-art, not a foreign ordinary loan.'),
    'quill_pen': (['feather', 'pen'], 'noun', 'quill', 'A feather writing pen, explicitly writing verse in Sonnets 83 and 85; distinct from an uncut bird feather.'),
    'shallow_water': (['small', 'water_depth'], 'modifier', 'shallow', 'Limited water depth supporting a small boat in Sonnet 80; native small-depth, not the inherited small-knowledge term for intellectual shallowness.'),
    'book_leaf': (['book', 'leaf'], 'noun', 'page', 'A leaf or page of a book, the empty writing surface in Sonnet 77; distinct from a household page and from foliage.'),
    'choir_space': (['sing', 'place'], 'noun', 'choir', 'A place for choral singing, the ruined architectural space imagined in bare branches in Sonnet 73; distinct from a group of singers.'),
    'sunset': (['sun', 'sink'], 'noun', 'sunset', 'The sun’s apparent setting, native sun-sink; no claim that the celestial body physically submerges in water.'),
    'interest_share': (['part', 'right'], 'noun', 'interest', 'A retained share or right in a work, the life invested in verse in Sonnet 74; not a lending rate or merely curiosity.'),
    'dregs': (['sink', 'remain'], 'noun', 'dregs', 'Settled unwanted residue, metaphorically the least valuable bodily remainder in Sonnet 74; the speaker’s valuation does not assert that bodies are objectively worthless.'),
    'miser': (['miserly', 'person'], 'noun', 'miser', 'One guarding possessions with reluctance to part, the troubled owner in Sonnet 75; distinct from simply being poor.'),
    'learned_doctor': (['knowledge'], 'agent', 'scholar', 'A learned authority invoked by folly’s doctor-like pretence in Sonnet 66; not a physician or a new named university degree.'),
    'mow': (['grass', 'cut'], 'verb', 'mow', 'Cut standing growth down with a blade, Time’s scythe in Sonnet 60; distinct from threshing harvested grain.'),
    'parallel_lines': (['same', 'line'], 'modifier', 'parallel', 'Lines running alongside one another, the wrinkles ploughed in beauty’s brow in Sonnet 60; a visible relation rather than an assertion of a measured spacing.'),
    'sparse': (['few', 'space'], 'modifier', 'sparse', 'Thinly distributed with intervals, the placement of festival-jewels in Sonnet 52; not an exact density.'),
    'necklace': (['neck', 'jewel'], 'noun', 'necklace', 'Jewellery worn around the neck, the carcanet in Sonnet 52; native neck-jewel, with no invented number of stones.'),
    'wild_rose': (['wild', 'rose_flower'], 'noun', 'wild-rose', 'The canker bloom or dog rose contrasted with the fragrant cultivated rose in Sonnet 54; distinct from the rose-damaging worm called canker in Sonnet 35.'),
    'masonry': (['stone', 'build'], 'noun', 'masonry', 'Building work in stone, exposed to war in Sonnet 55; not a guild or an imported architectural style.'),
    'jury': (['judge', 'group'], 'noun', 'jury', 'A group charged to settle the contested claim, the quest of thoughts in Sonnet 46; no unstated number of jurors is supplied.'),
    'defendant': (['defend'], 'agent', 'defendant', 'The party answering the claim, the eye in Sonnet 46; a contextual legal role, not a newly introduced physical guard.'),
    'instinct': (['nature', 'know'], 'noun', 'instinct', 'Innate apprehension attributed hypothetically to the riding animal in Sonnet 50; not an assertion that it understands human speech.'),
    'classical_element': (['world', 'matter'], 'noun', 'element', 'One of the source cosmology’s earth, water, air and fire constituents in Sonnets 44–45; native world-matter, not a chemical element or a new Vayrshemon scientific assertion.'),
    'gold_transmutation': (['gold', 'change'], 'noun', 'alchemy', 'Transmutation into gold, the heavenly alchemy of sunrise on streams; native gold-change, not a borrowed ordinary word.'),
    'literary_style': (['verse', 'manner'], 'noun', 'style', 'A writer’s manner of expression, distinguished from personal love in Sonnet 32; not a stylus or clothing fashion.'),
    'judicial_session': (['judge', 'sit'], 'noun', 'session', 'A sitting of a tribunal, the sessions to which memories are summoned in Sonnet 30; native judge-sit and not a royal household.'),
    'picture_frame': (['hold', 'boundary'], 'noun', 'frame', 'A supporting border holding a picture, with the body as frame in Sonnet 24; not the act of deceitful framing.'),
    'workshop': (['labour', 'house'], 'noun', 'workshop', 'A place where an artisan works and displays the picture; the heart’s figurative painter shop.'),
    'poetic_spirit': (['verse', 'spirit'], 'noun', 'verse-spirit', 'Poetic inspiration personified in the rival muse of Sonnet 21; no named Greek goddess is specified by this masculine source figure.'),
    'paw': (['beast', 'foot'], 'noun', 'paw', 'An animal foot including its claws in the lion image; native beast-foot, not a human hand.'),
    'astral_art': (['star', 'knowledge'], 'noun', 'star-lore', 'The art of reading celestial signs to predict earthly events, source astronomy in Sonnet 14; native star-knowledge, not a claim about modern scientific astronomy.'),
    'ill_shaped': (['bad', 'shape'], 'modifier', 'ill-shaped', 'Lacking the beauty of form the speaker prizes; featureless in Sonnet 11, not literally without facial anatomy.'),
    'pupil_student': (['learn'], 'agent', 'pupil', 'A learner or novice, the self-deprecating poet’s pen; distinct from the eye’s pupil.'),
    'verse_metre': (['verse', 'measure'], 'noun', 'metre', 'Measured verse pattern, including a poem’s strained or exaggerated measure; not a metric unit of length.'),
    'painting_brush': (['paint', 'instrument'], 'noun', 'brush', 'A painter’s brush, source pencil in Sonnet 16; not an asserted modern graphite pencil.'),
    'audit_accounts': (['reckon', 'judge'], 'noun', 'audit', 'Assessment of an account rendered, Nature’s closing reckoning in Sonnet 4.'),
    'testament_executor': (['bequeath', 'manage'], 'agent', 'executor', 'One administering a bequest; beauty continued in descendants, not an executioner.'),
    'usurer_lender': (['lend', 'gain'], 'agent', 'usurer', 'One lending for a return, the paradoxical profitless lender in Sonnet 4.'),
    'homage_service': (['honour', 'serve'], 'noun', 'homage', 'Acknowledged service to a superior; eyes figuratively honour the rising sun.'),
    'unprovided': (['prepare', 'without'], 'modifier', 'unprovided', 'Failing to provide for the future; the reproach of Sonnet 10, not mere present poverty.'),
}

ROOTS = {
    'scythe': ('thorden', 'scythe', 'noun', 'A long-handled harvesting blade, personified Time’s implement; authored native harvest/cut-family form, distinct from a short sickle.'),
    'churl_native': ('krathlen', 'churl', 'noun', 'An ungenerous, rough-mannered person; native rough-family formation, preserving the tender/churl contrast without the old ungrounded karlën lookalike.'),
    'tattered': ('desfil', 'tattered', 'modifier', 'Torn and frayed in strips, a native cut/cloth-family formation; source weed here is clothing, not a plant.'),
    'reel_stagger': ('rilyan', 'reel', 'verb', 'Move unsteadily from side to side; authored turn/motion-family formation, the aged sun’s departure.'),
}

PROPER_IDENTIFIERS = {
    'london_source': ('london', 'London', 'The named place London in the supplied 1599 publication imprint.'),
    'iaggard_source': ('yagard', 'Iaggard', 'The named publisher printed W. Iaggard in the supplied imprint; native phonetic adaptation of the surname, retaining the printed identity.'),
    'initial_w_source': ('w', 'W.', 'The printed W. name-initial in the Shakespeare and Iaggard imprint. Not expanded to an unprinted given name.'),
    'signature_a_source': ('a', 'A', 'The letter A identifying the printed gathering in the supplied bibliographic signatures. It is a letter label, not a quantity ten or an ordinal.'),
}


def prepare():
    lang = materialize()
    delta = read(PROJECT / 'lexical-delta.json')
    added = []
    def add(key, entry, label):
        if key in delta['entries']:
            return
        assert key not in lang.lexicon, key
        entry.update(semanticId='lex.' + key, usageScope='later-standard',
                     status='authored', historicalForms=[])
        delta['entries'][key] = entry
        delta['glosses'][key] = label
        added.append(key)
    for key, (parent, label, pos, meaning) in CONTEXTS.items():
        entry = deepcopy(lang.lexicon[parent])
        entry.update(pos=pos, meaning=meaning, origin='Reviewed contextual sense of ' + parent)
        add(key, entry, label)
    available = {**lang.lexicon, **delta['entries']}
    for key, (parents, pos, label, meaning) in DERIVATIONS.items():
        form = ''.join(available[p]['form'] for p in parents)
        if pos == 'agent':
            form += lang.suffix['ag'][0]
            pos = 'noun'
        add(key, dict(form=form, roman=lang.reading(form), pos=pos, meaning=meaning,
                     derivationKeys=parents, origin='Authored native lexical derivation: ' + ' + '.join(parents)), label)
    for key, (form, label, pos, meaning) in ROOTS.items():
        if key not in delta['entries']:
            assert not any(e['form'] == form for e in available.values()), ('Review root homonym', key)
        add(key, dict(form=form, roman=lang.reading(form), pos=pos, meaning=meaning,
                     origin='Authored native formation; motivation in definition, not claimed historical attestation.'), label)
    for key, (form, label, meaning) in PROPER_IDENTIFIERS.items():
        add(key, dict(form=form, roman=lang.reading(form), pos='proper', meaning=meaning,
            origin='Source-specific proper name or bibliographic identifier adaptation; not an ordinary vocabulary loan.'), label)
    may = quantity(5, 'ordinal')['form'] + ' ' + lang.lexicon['month']['form']
    add('may_source', dict(form=may, roman=lang.reading(may), pos='noun',
        meaning='May, the fifth month of the source poet’s English calendar; native Unta ordinal plus month, not an invented Vayrshemon calendar equivalence.',
        origin='Source-calendar reference expressed with the exact Unta ordinal five and the native month term.'), 'May')
    second_material = quantity(2, 'ordinal')['form'] + ' ' + lang.lexicon['matter']['form']
    add('second_grade_material', dict(form=second_material, roman=lang.reading(second_material), pos='noun',
        meaning='Inferior second-grade material mixed into an offering, source seconds in Sonnet 125. Retains the Unta ordinal word two in the quality-ranking metaphor; neither a duration in seconds nor two items. The source permits a flour-quality allusion without requiring added flour in the translation.',
        origin='Authored Unta second-ordinal word plus native material; contextual quality grade.',
        numericValue='2',numericKind='ordinal-grade',numericNotation='words',base12='2'), 'second-grade-material')
    december = quantity(12, 'ordinal')['form'] + ' ' + lang.lexicon['month']['form']
    add('december_source', dict(form=december, roman=lang.reading(december), pos='noun',
        meaning='December, the twelfth month of the source English calendar, personified as old in Sonnet 97. Uses the Unta word ordinal for twelve plus month, without inventing a Vayrshemon calendar equivalence.',
        origin='Source-calendar name expressed as native Unta ordinal twelve plus month.'), 'December')
    june = quantity(6, 'ordinal')['form'] + ' ' + lang.lexicon['month']['form']
    add('june_source', dict(form=june, roman=lang.reading(june), pos='noun',
        meaning='June, the sixth month in the source English calendar; the repeated Junes of Sonnet 104 remain three occurrences of that month, not three months invented for a native calendar.',
        origin='Source-calendar name expressed as native Unta ordinal six plus month.'), 'June')
    add('saturn_source', dict(form='saturn', roman=lang.reading('saturn'), pos='proper',
        meaning='Saturn, the named heavy and slow planetary/deity figure made to laugh and leap by April in Sonnet 98; retains the source personification and does not become an ordinary word for heaviness.',
        origin='Author-permitted phonetic proper-name adaptation, distinct from native common vocabulary.'), 'Saturn')
    add('will_source', dict(form='wil', roman=lang.reading('wil'), pos='proper',
        meaning='Will, the personal name explicitly identified by the speaker in Sonnet 136. The native word for desire is different; this adaptation preserves the name without borrowing English will as common vocabulary or falsely claiming an identical sound pun.',
        origin='Author-permitted phonetic personal-name adaptation. The source pun and its sound loss are documented in the verse review.'), 'Will')
    if added:
        delta['decisions'].append(dict(work='shakespeares-sonnets', decision=
            'Preserve each sonnet and exact source lines. Headings printed as digits use Unta figures; numerical words use Unta words. Keep the poet’s persuasion, contradictory metaphors and ambiguities distinct from narrator endorsement.'))
    write(PROJECT / 'lexical-delta.json', delta)
    materialize()
    print('Sonnets lexical additions:', len(added))

if __name__ == '__main__':
    prepare()
