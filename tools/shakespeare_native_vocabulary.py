"""Apply reviewed native vocabulary to new dramatic manuscripts on their own checkpoint."""
from copy import deepcopy
import re

from tools.editorial_language import WORD, TOKEN
from tools.kjv_native_vocabulary import ROOT_ROWS, EXTRAS
from tools.shakespeare_project import PROJECT, materialize, read, write

PREFIX = "drama_native_"


def native_entries(language):
    """Index new readings by their inherited key. Follow only documented lexical derivations."""
    lex = language.lexicon
    changes = {}
    for row in (ROOT_ROWS + "\n" + EXTRAS).splitlines():
        key, roots, form, reason = row.split("|")
        if key in lex and lex[key]["pos"] != "proper" and roots and lex[key]["form"] != form:
            changes[key] = (form, roots.split(), reason)
    for key, equivalent in {"hop": "hop_step", "gun": "gun_weapon", "cradle": "cradle_native",
                            "crest": "war_crest"}.items():
        existing = lex[equivalent]
        changes[key] = (existing["form"], [equivalent], existing["meaning"])
    for key, roots, reason in [
        ("glance", ["quick", "look"], "A brief look, from the native words for quick and look."),
        ("hemp", ["kjv_cord", "plant"], "The cordage plant in Cade's threat of a hanging."),
        ("wren", ["small", "song", "bird"], "The small songbird in the comparison."),
        ("pox", ["spot", "sickness"], "An eruptive disease invoked in a curse, from the native words for a spot and an illness."),
    ]:
        changes[key] = ("".join(lex[r]["form"] for r in roots), roots, reason)
    if "last" in changes and lex["final"]["form"] == lex["last"]["form"]:
        changes["final"] = changes["last"]
    seeds = set(changes)
    for _ in range(16):
        updated = False
        for key, entry in lex.items():
            if (key in seeds or key.startswith((PREFIX, "unta_")) or entry["pos"] == "proper"
                    or "numericValue" in entry):
                continue
            roots = entry.get("derivationKeys", [])
            if not any(root in changes for root in roots):
                continue
            original = entry["form"]
            spans = []
            for root in sorted(set(roots) & changes.keys(), key=lambda r: -len(lex[r]["form"])):
                old, new = lex[root]["form"], changes[root][0]
                for a, b in {(old, new), (language.maxima(old), language.maxima(new))}:
                    for m in re.finditer(re.escape(a), original):
                        if not any(m.start() < stop and start < m.end() for start, stop, _ in spans):
                            spans.append((m.start(), m.end(), b))
            form = original
            for start, stop, text in sorted(spans, reverse=True):
                form = form[:start] + text + form[stop:]
            if form != original and (key not in changes or changes[key][0] != form):
                changes[key] = (form, roots, "Preserve the native constituents in this dramatic sense.")
                updated = True
        if not updated:
            return changes
    raise ValueError("Native lexical derivations did not stabilize")


def prepare_manuscript_readings(slug, language):
    project = read(PROJECT / "project.json")
    work = next(w for w in project["works"] if w["slug"] == slug)
    if work["status"] == "verified":
        raise ValueError("An issued play must retain its own checkpoint")
    changes = native_entries(language)
    source = PROJECT / "Analyses" / (slug + ".json")
    analyses = read(source)
    needed = set()
    changed_rows = []

    def replace_word(match):
        token = match.group()
        if not WORD.fullmatch(token):
            return token
        def replace_lemma(m):
            key = m.group()
            if key not in changes:
                return key
            needed.add(key)
            return PREFIX + key
        # Suffixes retain their morphology. Compound and possessive members
        # are separate lemmas. Literal {{...}} text is a single non-word token.
        return re.sub(r"(?<![A-Za-z_:])[A-Za-z_]+", replace_lemma, token)

    for row in analyses:
        before = row["analysis"]
        after = TOKEN.sub(replace_word, before)
        if before != after:
            row["analysis"] = after
            changed_rows.append(row["id"])
    if not needed:
        return language
    delta_path = PROJECT / "lexical-delta.json"
    delta = read(delta_path)
    pending = sorted(needed)
    done = set()
    new = []
    while pending:
        key = pending.pop()
        if key in done:
            continue
        done.add(key)
        form, roots, reason = changes[key]
        alias = PREFIX + key
        entry = deepcopy(language.lexicon[key])
        dependencies = [PREFIX + r if r in changes and r != key else r for r in roots]
        entry.update(form=form, roman=language.reading(form), semanticId="lex." + alias,
                     derivationKeys=dependencies, historicalForms=[], meaning=entry["meaning"],
                     origin="Dramatic native reading. " + reason, status="authored")
        gloss = language.glosses.get(key, key.replace("_", "-"))
        if alias in delta["entries"]:
            assert language.lexicon[alias] == entry and delta["glosses"][alias] == gloss, alias
        else:
            delta["entries"][alias] = entry
            delta["glosses"][alias] = gloss
            new.append(alias)
        pending.extend(r for r in roots if r in changes and r not in done)
    if new:
        delta["decisions"].append(dict(work=slug, entries=sorted(new),
            decision="Attested native roots replace inherited English-shaped forms in new dramatic sources. Older issued language checkpoints retain their readings."))
        write(delta_path, delta)
    language = materialize()
    for row in analyses:
        language.compile(row["analysis"])
    write(source, analyses)
    print(f"{slug}: {len(changed_rows)} rows revised, {len(new)} native readings registered.")
    return language
