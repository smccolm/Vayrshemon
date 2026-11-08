"""Build source-specific dictionary additions on the shared dramatic lexicon."""
from tools.shakespeare_project import PROJECT, materialize, read, write


def lexical_entries(language, names, senses, places=()):
    entries, glosses = {}, {}
    for key, (form, gloss, meaning) in names.items():
        origin = ("Author-permitted geographic-name adaptation" if key in places
                  else "Author-permitted phonetic personal-name adaptation")
        entries[key] = dict(form=form, roman=language.reading(form), pos="proper",
            meaning=meaning, semanticId="lex."+key, origin=origin,
            usageScope="later-standard", status="authored", historicalForms=[])
        glosses[key] = gloss
    roots_available = language.lexicon | entries
    for key, (roots, gloss, part, meaning) in senses.items():
        form = "".join(roots_available[root]["form"] for root in roots)
        entries[key] = dict(form=form, roman=language.reading(form), pos=part,
            meaning=meaning, semanticId="lex."+key, derivationKeys=roots,
            origin="Authored native derivation or sense: "+" + ".join(roots),
            usageScope="later-standard", status="authored", historicalForms=[])
        glosses[key] = gloss
    return entries, glosses


def add_source_entries(work, predecessor, build_entries, decision, *, inherited_glosses=None):
    works = {w["slug"]: w for w in read(PROJECT/"project.json")["works"]}
    if works[predecessor]["status"] != "verified" or works[work]["status"] == "verified":
        raise ValueError(f"Cannot extend {work} from {predecessor} at these project statuses.")
    language = materialize()
    delta_path = PROJECT/"lexical-delta.json"
    delta = read(delta_path)
    entries, glosses = build_entries(language)
    new_keys = []
    for key, entry in entries.items():
        if key in delta["entries"]:
            assert delta["entries"][key] == entry and delta["glosses"][key] == glosses[key], key
        else:
            assert key not in language.lexicon, key
            new_keys.append(key)
    new_glosses = {}
    for key, label in (inherited_glosses or {}).items():
        if key not in language.lexicon:
            raise ValueError(f"Unknown inherited dictionary entry: {key}")
        previous = language.glosses.get(key)
        if previous is None:
            new_glosses[key] = label
        elif previous != label:
            raise ValueError(f"Conflicting gloss for {key}: {previous!r} / {label!r}")
    if new_keys or new_glosses:
        delta["entries"].update({key: entries[key] for key in new_keys})
        delta["glosses"].update({key: glosses[key] for key in new_keys})
        delta["glosses"].update(new_glosses)
        record = dict(work=work, entries=new_keys, decision=decision)
        if new_glosses:
            record["inheritedReadingGlosses"] = new_glosses
        delta["decisions"].append(record)
        write(delta_path, delta)
        materialize()
    print(work, "additions:", len(new_keys))
