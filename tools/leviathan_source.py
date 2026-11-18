"""Prepare Hobbes's English for four parallel columns, with marginalia outside the prose."""
from hashlib import sha256
from pathlib import Path
import json
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Inputs/Sources/Thomas Hobbes - Leviathan.txt'
BOOK = ROOT / 'Saves/Leviathan - Four-Column Progressive Edition'
WORK = BOOK / 'Working'
EPUB = ROOT / '.local/leviathan/clarendon.epub'
WITNESS = 'https://oll-resources.s3.us-east-2.amazonaws.com/oll3/store/titles/869/hobbes-leviathan-1909-ed.epub'
SCAN = 'https://oll-resources.s3.us-east-2.amazonaws.com/oll3/store/titles/869/0161_Bk.pdf'

# Readings where the electronic reprint dropped type retained by the supplied witness.
READINGS = {
    1349: (("Levit. 25. 11, 12.", "Levit. 24. 11, 12."),),
    1261: (("δαδονχίαις", "δαδουχίαις"), ("Δαδου̑χοι", "Δαδοῦχοι")),
    1254: (("Exod. 32. 2", "Exod. 32. 4"),),
    1234: (("of whom their can", "of whom there can"),),
    1237: (("δονλεία", "δουλεία"), ("their Service Δονλεία", "their Service Δουλεία"), ("but Δονλεία", "but Δουλεία"), ("Δονλεία because", "Δουλεία because"), ("Δου̑λοι", "Δοῦλοι"), ("Θη̑τεβ", "Θῆτες"), ("Λάτεις", "Λάτρεις")),
    1238: (("Ε῀δω", "Εἴδω"),),
    1228: (("κακοδάιμων", "κακοδαίμων"),),
    1230: (("shewed him them thence", "shewed him thence"),),
    1231: (("hemight", "he might"),),
    1232: (("Enemice", "Enemies"),),
    1214: (("2 Kings, 1. 12.", "2 Sam. 1. 12."),),
    1215: (("Psalme, 37.", "Psalme, 38."),),
    1205: (("2 Kings 8.", "1 Kings 8."),),
    1208: (("Heb. 13. 5.", "Heb. 11. 5."),),
    1201: (("Joash her Son", "Joash her grandson"),),
    1202: (("I Thessal.", "1 Thessal."),),
    147: [('Thirst. nd when', 'Thirst. And when'), ('words Appetite, and we have','words Appetite, and Aversion we have'),
          ('ὁρμὴ and ὀϕορμὴ For','ὁρμὴ, and ἀφορμὴ. For')],
    153: [('and he later,','and the later,')],
    177: [('magination of Pleasure','Imagination of Pleasure')],
    178: [('singularly eloved','singularly beloved')],
    181: [('or magined','or imagined')],
    209: [('πιστέυω are never','πιστεύω εἰς, are never'), ('πιστέυω ἀυτὠ','πιστεύω αὐτῷ')],
    335: [('been steemed','been esteemed')],
    349: [('secure leasure','secure Pleasure')],
    413: [('not Just, Guiltlesse','not Just, but Guiltlesse')],
    416: [('Geometric all', 'Geometricall')],
    429: [('ληρονομία', 'κληρονομία')],
    500: [('nor glorious, not secure', 'nor glorious, nor secure')],
    518: [('because. he hath approved', 'because he hath approved')],
    535: [('to the overaigne','to the Soveraigne'),
          ('(Exod.20. 19)', '(Exod. 20. 19)'), ('(1 Sam, 8. 11', '(1 Sam. 8. 11'),
          ('Lawes; (1 Sam. 24. 9) and therefore', 'Lawes; and therefore'),
          ('David forbad them, saying,', 'David forbad them, saying (1 Sam. 24. 6),'),
          ('(Coll. 3. 20) Servants', '(Col. 3. 22) Servants'), ('(Verse 22) Children', '(Verse 20) Children'),
          ('And St Paul, Warn them', 'And St Paul (Tit. 3. 1), Warn them'),
          ('This obedience (Tit.3.2) is also simple.', 'This obedience is also simple.')],
    521: [('nd this kind','And this kind')],
    523: [('because or the most','because for the most')],
    603: [('of the Soveraign. the Monarch,','of the Soveraign. The Monarch,')],
    645: [('præcribes, and commandeth','præscribes, and commandeth')],
    647: [('3. Then long Use', '3. When long Use')],
    648: [('Obedience to the Civill, Law','Obedience to the Civill Law')],
    650: [('the Common Law. hath','the Common Law, hath')],
    656: [('publique eales','publique Seales')],
    663: [('the entence of','the Sentence of')],
    664: [('that he field for the Felony','that he fled for the Felony')],
    686: [('ἁμάρτημα and ἑγκλημα or ᾀιτία','ἁμάρτημα, and ἔγκλημα, or αἰτία')],
    692: [('Excused from a greate penalty','Excused from a greater penalty')],
    693: [('Law that for-biddeth','Law that forbiddeth')],
    721: [('Crimina lœsœ Majestatis','Crimina læsæ Majestatis')],
    746: [('not contaned in','not contained in')],
    748: [('the Punishment. but where','the Punishment. But where')],
    761: [('distinction f Nocent','distinction of Nocent')],
    769: [('and Cœsar','and Cæsar')],
    773: [('uno bservable','unobservable')],
    785: [('be esembled','be resembled')],
    794: [('toacquiesce','to acquiesce')],
    765: [('Proud.There', 'Proud. There')],
    824: [('Providence.How', 'Providence. How')],
    846: [('Incompre-hensible','Incomprehensible')],
    855: [('it tought also','it ought also')],
    866: [('his Wil immediately','his Will immediately'),('the K. of Israel','the King of Israel'),('God wil not','God will not')],
    867: [('long deferr’ event','long deferred event')],
    805: [('Equall mposition','Equall imposition')],
    806: [('as the necessities of Nature require, by', 'as the necessities of Nature require), by')],
    338: [('Larvœ, Lemures','Larvæ, Lemures')],
    346: [('the Goverment of Religion', 'the Government of Religion'), ('be anable to shew','be unable to shew')],
    354: [('the Sanctify, Wisdome','the Sanctity, Wisdome')],
    375: [('he doth so Renounced,','he doth so Renounce,')],
    397: [('and Prison. with armed men','and Prison, with armed men'),
          ('the onely End of laying down any Right, and therefore', 'the onely End of laying down any Right), and therefore')],
    400: [('condition of ineer Nature', 'condition of meer Nature')],
    820: [('Psalmist. nd','Psalmist. And'), ('moved. hether','moved. Whether')],
    866: [('Christs, nd','Christs, and')],
    873: [('been lost, as long','been lost, was long'), ('And this did Moses','And this also did Moses'), ('and eliver to','and deliver to')],
    874: [('their assage','their passage'), ('signifieth time past','signifieth a time past')],
    876: [('Israelto this day','Israel to this day')],
    877: [('I Kings 9.13','1 Kings 9.13')],
    884: [('If the Prophets, the most ancient','Of the Prophets, the most ancient')],
    887: [('in they Law','in thy Law'), ('Ptolemœus Philadelphus','Ptolemæus Philadelphus')],
    888: [('Testament:Christ','Testament: Christ')],
    892: [('there fore the Scriptures','therefore the Scriptures')],
    900: [('Musick(1 Sam. 19. 20.)','Musick (1 Sam. 19. 23.)')],
    908: [('Luke 24. 3, 7.', 'Luke 24. 37.')],
    914: [('Also (Exod. 14. 9.)', 'Also (Exod. 14. 19.)'),
          ('promised to Moses (Exod. 14. 9.)','promised to Moses (Exod. 23. 20.)')],
    930: [('King dome there','Kingdome there'), ('is a reail,','is a reall,')],
    932: [('Children of God hereafter','Children of God) hereafter')],
    940: [('a Man hath spoken: In', 'a Man hath spoken): In'), ('Also[Mat.', 'Also [Mat.')],
    941: [('is nderstood','is understood'), ('Let their be light','Let there be light')],
    942: [('Son, herefore','Son, therefore'), ('in bloud, faith;', 'in bloud, saith;')],
    944: [('Psalm 36. 31','Psalm 37. 31')],
    945: [('Prœdictor','Prædictor')],
    946: [('future Contigents','future Contingents')],
    948: [('to Jacob [Gen. 18. 12.]','to Jacob [Gen. 28. 12.]')],
    950: [('as A damant', 'as Adamant')],
    955: [('(Josh. 18. 10.]','[Josh. 18. 10.]')],
    957: [('(Deut. 13. 1, &c.]','[Deut. 13. 1, &c.]'), ('[I Kings 12.]','[1 Kings 22.]')],
    958: [('Deut. 13. I.','Deut. 13. 1.'), ('[I Epist. 4. 2,','[1 Epist. 4. 2,'), ('by Baalam','by Balaam')],
    960: [('but two things. which','but two things which')],
    964: [('(verse 41.) that they beleeved him','(verse 31.) that they beleeved him')],
    968: [('on the round became','on the ground became'), ('Ponds, nd','Ponds, and'), ('upon the and,','upon the land,')],
    974: [('(Acts I. II.)','(Acts 1. 11.)')],
    975: [('(except Enos and Elias,)','(except Enoch and Elias,)')],
    976: [('of the Olà,','of the Old,')],
    977: [('and Injeri,','and Inferi,'), ('and Abirom,','and Abiram,')],
    980: [('more Dying. nor','more Dying, nor')],
    982: [('Children of Hinnon','Children of Hinnom'), ('Valley of Hinnon','Valley of Hinnom')],
    983: [('Valley of Hinnon','Valley of Hinnom')],
    986: [('an Everlasting Death yet','an Everlasting Death, yet'), ('one after another for ever;','one after another for ever);')],
    987: [('not ubject','not subject')],
    988: [('2 Sam. 22. 4.', '2 Sam. 22. 3.'), ('the hand of the Assyrians','the hand of the Syrians')],
    995: [('Chap. 65. 20, 21.', 'Chap. 66. 20, 21.')],
    997: [('some other or him','some other for him')],
    998: [('I Cor. 14.','1 Cor. 14.'), ('Κνριακὴ','Κυριακὴ')],
    999: [('Church, έννομος','Church, ἔννομος Ἐκκλησία.'), ('Εκκλησία σνγκεχνμίνη','Ἐκκλησία συγκεχυμένη')],
    1001: [('According o this sense','According to this sense')],
    1004: [('seed of braham','seed of Abraham')],
    1009: [('why lift up your selves','why lift you up your selves')],
    1020: [('tribute to Cæsar; but','tribute to Cæsar); but')],
    1028: [('before, chapt. 13.', 'before, chapt. 16.'), ('(verse II.)', '(verse 11.)'),
           ('He that beleeveth on the Son of man hath', 'He that beleeveth on the Son of God hath')],
    1034: [('and ther the then','and other the then')],
    1045: [('ᾀποσννάγωγον ποιι̑ν', 'ἀποσυνάγωγον ποιεῖν')],
    1050: [('παραιτο:', 'παραιτοῦ:')],
    1054: [('(1 Joh. 4. 1.)', '(1 Joh. 4. 2.)')],
    1064: [('(Deut. 27. 1.)', '(Deut. 27. 2.)')],
    1065: [('(I Kings 14. 26)', '(1 Kings 14. 26)')],
    1074: [('If Ecclesiasticall Officers', 'Of Ecclesiasticall Officers')],
    1081: [('χειροτονήσαντες ᾀντο+̂ις πρεσβντέρονς κατ ἐκκλησίαν', 'χειροτονήσαντες αὐτοῖς πρεσβυτέρους κατ’ ἐκκλησίαν'),
           ('προεστω̑τες', 'προεστῶτες'), ('ίνα καταστήσης κατὰ πόλιν πρεσβντέρονς', 'ἵνα καταστήσῃς κατὰ πόλιν πρεσβυτέρους')],
    1086: [('Κλη̑ρος', 'Κλῆρος')],
    1088: [('If the maintenance', 'Of the maintenance'), ('Preach, e forbad', 'Preach, he forbad')],
    1098: [('principall harge','principall Charge'), ('Crispus, Cajus, and Stephanus', 'Crispus, Gaius, and Stephanas')],
    1103: [('2 Epist. to Tim. ver. 6.', '2 Epist. to Tim. 1. 6.')],
    1113: [('ὀΑντίχριστος', 'ὁ Ἀντίχριστος')],
    1117: [('Subjects For', 'Subjects. For')],
    1118: [('Thummin', 'Thummim'), ('ᾀλήθειαν', 'ἀλήθειαν')],
    1133: [('πακούει', 'ὑπακούει')],
    1156: [('if bee bee', 'if he be')],
    1163: [('Salvatian', 'Salvation')],
    1177: [('διὰπνρὸς', 'διὰ πυρός'), ('Confiagration', 'Conflagration')],
    1187: [('I Tim. 4.', '1 Tim. 4.')],
}


def clean(text):
    text = ' '.join(text.replace(' | ', ' ').split())
    text = text.replace('VainGlory','Vain-glory').replace('DÆ','Dæ')
    text = re.sub(r'(?<=[a-z])(?=[A-Z])',' ',text)
    text = re.sub(r'\[(same|s|ni|n|h|of|one)\]', r'\1', text)
    text = re.sub(r'(?<=[A-Za-z]),(?=[A-Za-z])', ', ',text)
    def cap(match):
        word = match[0]
        if re.fullmatch(r'M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})', word):
            return word
        return word.capitalize()
    text = re.sub(r'\b[A-Z]{2,}\b', cap, text)
    text = re.sub(r'\b([A-Z])([A-Z]+)([a-z]+)', lambda m: m[1]+m[2].lower()+m[3], text)
    text = re.sub(r'(?<=\w)\((?=[a-zA-Z])',' (',text)
    return text.replace('.:', '.').replace(' ,', ',').replace("Honor'D","Honor'd").strip()


def inner(el, notes, *, skip_lists=False):
    if el.get('class') == 'entity uivrgr':
        return 'ῦ'  # Oxford p. 323, λόγος θεοῦ.
    if el.get('class') == 'pb' or el.get('class') == 'footnote-link type-footnote':
        return ''
    if skip_lists and el.tag == 'ul':
        return ''
    if el.get('class') == 'type-margin':
        note = clean(''.join(inner(c, []) + (c.tail or '') for c in el))
        notes.append(note)
        return ''
    return (el.text or '') + ''.join(inner(c, notes, skip_lists=skip_lists) + (c.tail or '') for c in el)


def build():
    src = SOURCE.read_bytes()
    assert sha256(src).hexdigest() == '26a264e01de726e5a561b6ada00354ecca8e8b5ad4f23f865c4213719b197f71'
    assert sha256(EPUB.read_bytes()).hexdigest() == 'b0bc0495d95eaae0bd2db01dc1fc9032a2b17c8c9586b074cdb7a76f07420f2e'
    with ZipFile(EPUB) as z:
        root = ET.fromstring(z.read('Hobbes_0161.html'))
    for el in root.iter():
        el.tag = el.tag.split('}')[-1]
    rows = []
    def add(section, key, kind, text):
        value = clean(text)
        if key == 'lf0161_label_993':
            assert 'Achristian Common-Wealth' in value
            value = value.replace('Achristian Common-Wealth','a Christian Common-Wealth')
        source_id = re.fullmatch(r'Hobbes_0161_(\d+)',key)
        if source_id:
            for before, after in READINGS.get(int(source_id[1]), ()):
                assert value.count(before) == 1, (key,before)
                value = value.replace(before,after)
        if value:
            rows.append(dict(id=key, section=section, kind=kind, text=value))
    lines = src.decode('utf8').splitlines()
    add('Title', 'title', 'heading', 'Leviathan, or the Matter, Forme and Power of a Commonwealth Ecclesiasticall and Civil.')
    add('Title', 'author', 'byline', lines[2])
    add('Dedication', 'dedication', 'heading', "To my most honor'd friend Mr Francis Godolphin of Godolphin.")
    add('Dedication', 'salute', 'prose', lines[7])
    def emit(section, el):
        key = el.get('id')
        notes = []
        text = inner(el, notes)
        if '*' in text or any(note.startswith('*') for note in notes):
            references = [n[1:].strip().rstrip('.') for n in notes if n.startswith('*')]
            assert len(references) == text.count('*'), (key, references)
            refs = iter(references)
            text = re.sub(r'\s*\*\s*', lambda m: ' ('+next(refs)+') ', text)
            text = re.sub(r'\)\s+([,.;:!?])', r')\1', text)
            notes = [n for n in notes if not n.startswith('*')]
        if key == 'Hobbes_0161_80':
            assert 'past, it is called.' in text
            text = text.replace('past, it is called.','past, it is called Memory.')
        if key == 'Hobbes_0161_92':
            assert 'Latines call it, as it were' in text
            text = text.replace('Latines call it, as it were','Latines call it Reminiscentia, as it were')
        if key == 'Hobbes_0161_82':
            assert 'are those we call.' in text
            text = text.replace('are those we call.','are those we call Dreams.')
        if key == 'Hobbes_0161_112':
            assert 'the befinitions of former Authors' in text
            text = text.replace('the befinitions of former Authors','the Definitions of former Authors')
        if key == 'Hobbes_0161_1327':
            assert 'Eoclesiastiques' in text
            text = text.replace('Eoclesiastiques','Ecclesiastiques')
        if key == 'Hobbes_0161_903':
            assert '(Ezek. 2. 30.) the Spirit entred into me' in text
            text = text.replace('Ezek. 2. 30.', 'Ezek. 2. 2.')
            text = text.replace('entred into; and possessed his body','entred into, and possessed his body')
        if key == 'Hobbes_0161_1129':
            assert 'Timothy 3. 2.' in text
            text = text.replace('Timothy 3. 2.', '1 Timothy 3. 2.')
        if key == 'Hobbes_0161_133':
            assert not notes
            notes.append('2.')
        if key == 'Hobbes_0161_534':
            notes.remove('The Rights of Monarchy from Scripture.')
        elif key == 'Hobbes_0161_535':
            notes.insert(0, 'The Rights of Monarchy from Scripture.')
        if key == 'Hobbes_0161_965':
            notes.insert(0, 'The definition of a Miracle.')
        if key == 'Hobbes_0161_966':
            notes.remove('The definition of a Miracle')
        for preceding, following, heading in (
                ('Hobbes_0161_177','Hobbes_0161_178','The Passion of Love.'),
                ('Hobbes_0161_180','Hobbes_0161_181','Religion.')):
            if key == preceding:
                notes.remove(heading)
            elif key == following:
                notes.insert(0,heading)
        repairs = {
            'Hobbes_0161_147': ('being he generall name', 'being the generall name'),
            'Hobbes_0161_153': ('And hose are', 'And those are'),
            'Hobbes_0161_188': ('passion that auseth', 'passion that causeth'),
            'Hobbes_0161_254': ('a promise of Good. it', 'a promise of Good, it'),
        }
        if key in repairs:
            before, after = repairs[key]
            assert before in text
            text = text.replace(before, after)
        if key == 'Hobbes_0161_236':
            assert 'hang’ themselves' in text and 'extraordinory' in text
            text = text.replace('hang’ themselves', 'hang’d themselves').replace('extraordinory', 'extraordinary')
        if key == 'Hobbes_0161_238':
            assert 'Transub-stantiation' in text and 'Lucide Intervals And' in text
            text = text.replace('Transub-stantiation', 'Transubstantiation').replace('Lucide Intervals And', 'Lucide Intervals. And')
        for i, note in enumerate(notes, 1):
            if key == 'Hobbes_0161_721' and note == 'Lœsœ Majestas.':
                note = 'Læsa Majestas.'
            if key == 'Hobbes_0161_751':
                note = note.replace('Revolled Subjects','Revolted Subjects')
            if key == 'Hobbes_0161_766':
                note = note.replace('Imperject Institution','Imperfect Institution')
            if key == 'Hobbes_0161_878':
                note = note.replace('Erra and Nehemiah','Ezra and Nehemiah')
            if key == 'Hobbes_0161_986' and note.startswith('Apol.'):
                note = note.replace('Apol.', 'Rev.', 1)
            if key == 'Hobbes_0161_989':
                note = note.replace('Eternail Salvation','Eternall Salvation')
            # Use the numbering of the KJV witness for Hobbes's Psalm quotations.
            psalm_readings = {'Psal. 96.1.': 'Psal. 97. 1.', 'Psal. 98.1.': 'Psal. 99. 1.',
                              'Psal. 72. ver. 1,2,3.': 'Psal. 73. ver. 1, 2, 3.'}
            if key in ('Hobbes_0161_820', 'Hobbes_0161_824'):
                note = psalm_readings.get(note, note)
            if note == 'Gen.17.10.':
                note = 'Gen. 17. 10.'
            if key == 'Hobbes_0161_523':
                note = note.replace('attained./Not', 'attained. Not')
            if key == 'Hobbes_0161_447' and i == 2:
                assert note.strip(',. ') == 'Actor'
                note = 'Author.'
            if key == 'Hobbes_0161_458':
                note = re.sub(r'Plur-\s+ality', 'Plurality', note)
            if key == 'Hobbes_0161_499' and note.startswith('Subordinute '):
                note = note.replace('Subordinute', 'Subordinate', 1)
            note = note.replace('After the Captivit,', 'After the Captivity,')
            note = note.replace('power to tonch.', 'power to teach.')
            if key == 'Hobbes_0161_1070':
                note = note.replace('./John ', '. John ')
            if key == 'Hobbes_0161_1090':
                note = note.replace('./1 Cor.', '. 1 Cor.')
            if note == 'Resaon defined.':
                note = 'Reason defined.'
            if note == 'First, from his desíre of knowing Causes.':
                note = 'First, from his desire of knowing Causes.'
            if note == 'Causes of absurditie I.':
                note = 'Causes of absurditie. 1.'
            if note == 'An Image what. Phantasmes.':
                note = 'What is an image? Phantasms.'
            add(section, f'{key}-margin-{i}', 'marginal heading', note)
        add(section, key, 'heading' if el.tag=='h2' else 'prose', text)
    emit('Dedication', root.find(".//p[@id='Hobbes_0161_62']"))
    add('Dedication','signature','prose', 'Sir, '+lines[13].rstrip(',')+'.')
    # Retain the supplied witness's TOC and its word/figure distinction. The
    # original locators name the 1651 folios, not native facing-spread numbers.
    add('Contents','contents','heading',lines[15])
    chapter = ''
    for i, line in enumerate(lines[17:218],18):
        if not line.strip():
            continue
        if line.startswith('Chap.'):
            chapter = '' if line == 'Chap.' else line + ' '
            continue
        add('Contents',f'toc-{i}', 'contents',chapter+line)
        chapter = ''
    sections = {e.get('id'): e for e in root.iter('div') if e.get('id')}
    chapter_counter = 0
    part_counter = 0
    for key in range(10,63):
        el = sections[f'lf0161_div_{key:03}']
        role = el.get('class')
        if role == 'type-chapter':
            chapter_counter += 1
            section = f'Chapter {chapter_counter}'
        elif role == 'type-introduction':
            section = 'Introduction'
        elif role == 'type-part':
            part_counter += 1
            section = f'Part {part_counter}'
        else:
            assert key == 62
            section = 'Review and conclusion'
        def walk(parent):
            for c in parent:
                if c.tag in ('p','h2','li'):
                    emit(section,c)
                elif c.get('class') == 'figure':
                    assert section == 'Chapter 9'
                    table = json.loads((WORK/'knowledge-foldout.json').read_text(encoding='utf8'))
                    for node in table['rows']:
                        add(section, node['id'], 'table branch', node['text'])
                        rows[-1].update(tableId='knowledge-foldout', parentNode=node['parent'],
                                        hierarchyDepth=node['depth'], hierarchyPrefix=node['prefix'])
                elif c.get('class') not in ('type-chapter','pb'):
                    walk(c)
        walk(el)
    assert (chapter_counter,part_counter) == (47,4)
    if rows[-1]['text'].rstrip('.').lower() != 'finis':
        add('Review and conclusion','finis','prose','Finis.')
    assert len({r['id'] for r in rows}) == len(rows) and all(r['id'] for r in rows)
    text = '\n\n'.join(r['text'] for r in rows)+'\n'
    assert not any(s in text for s in ('〈','◊','•…','[Note:', 'uivrgr', 'Edition: current', 'Edition: Hobbes','non-Latin alphabet'))
    assert 'Answer to the Argument from the Cherubins, and Brazen Serpent.' in text
    assert 'What is an image? Phantasms.' in text
    WORK.mkdir(parents=True,exist_ok=True)
    (WORK/'English reading text.txt').write_text(text,encoding='utf8')
    data=dict(sourceSha256=sha256(src).hexdigest(),witness=WITNESS,facsimile=SCAN,
              witnessSha256=sha256(EPUB.read_bytes()).hexdigest(),
              pendingFigures=[], restoredFigures=[dict(id='knowledge-foldout',facsimilePage=97,
              sourceLines=[600,704],transcription='knowledge-foldout.json')], rows=rows)
    (WORK/'english-blocks.json').write_text(json.dumps(data,ensure_ascii=False,indent=1), encoding='utf8')
    return rows


if __name__=='__main__':
    rows=build()
    print(len(rows),'English blocks,',sum(len(r['text'].split()) for r in rows),'words')
