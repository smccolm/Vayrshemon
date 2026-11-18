"""The original colour-mask key order, bound to the current chart's slots."""
from dataclasses import dataclass
import json


@dataclass(frozen=True)
class Key:
    name: str
    lower: str
    upper: str
    command: bool = False


# In the original bitmap the first region is RGB(252,252,252). Each
# successive region is three shades darker. Letters follow chart order
# between Unta, punctuation and editing keys.
DIGITS = (0, 3, 7, 11, 16, 21, 43, 49, 54, 59, 63, 67)
SPECIAL = {
    37: ('Space', ' ', ' '),
    44: ('Comma', ',', '<'), 50: ('Period', '.', '>'),
    55: ('Antagonistic clitic', '?', '('), 60: ('Cooperative clitic', ':', ')'),
    64: ('Clitic', '’', '['), 68: ('Dual clitic', '"', ']'),
}
COMMANDS = {62: 'Backspace', 65: 'Caps', 66: 'Delete', 69: 'Enter'}


def native_keys(root):
    chart = json.loads((root / 'data/orthography/chart-transcription.json').read_text(encoding='utf-8'))
    keys = {i: Key(*spec) for i, spec in SPECIAL.items()}
    keys.update({i: Key(name, name, name, True) for i, name in COMMANDS.items()})
    for i, (_, scalar, name), shifted in zip(DIGITS, chart['numerals'], '{}%|_~=+-*/\\', strict=True):
        keys[i] = Key(name, chr(scalar), shifted)
    for i, (_, upper, lower, name, _, _) in zip(
            (j for j in range(70) if j not in keys), chart['letters'], strict=True):
        keys[i] = Key(name, chr(lower), chr(upper))
    return tuple(keys[i] for i in range(70))


ENGLISH_ROWS = (
    ('`1234567890-=', '~!@#$%^&*()_+'),
    ('qwertyuiop[]\\', 'QWERTYUIOP{}|'),
    ("asdfghjkl;'", 'ASDFGHJKL:"'),
    ('zxcvbnm,./', 'ZXCVBNM<>?'),
)


def english_character(lower, upper, caps, shift):
    return upper if (shift ^ (caps and lower.isalpha())) else lower
