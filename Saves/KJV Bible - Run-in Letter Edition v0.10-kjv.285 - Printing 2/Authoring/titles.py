"""Short historical-register titles for the 66 opening banners."""
from copy import copy
from functools import lru_cache

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainterPath
from compose import BOOKS,Proof,digits,pe
from tools.kjv_native_vocabulary import VERSION,load_register

# These are title readings. Keys always identify the same bearer; the body
# lexicon and translations remain the sealed 285 register.
NAME_FORMS={
    'kjv_samuel':'Ûemçel', 'kjv_ezra_scribe':'ezrÅ', 'kjv_ezekiel':'yehezkel',
    'kjv_daniel_captive':'dÅniyel', 'kjv_amos_prophet':'Åmos', 'kjv_nahum_prophet':'nahçm',
    'kjv_habakkuk_prophet':'habakçk', 'kjv_haggai_prophet':'hÅgay',
    'kjv_matthew_disciple':'mattay', 'kjv_mark_surname_acts':'markus',
    'kjv_titus_second_corinthians':'tÝtos', 'kjv_james_epistle':'yÅkov',
}
# Use the dative for letter destinations. Following volume signs count works
# in a named series. Chapter one is understood at each book opening.
TITLE_ROWS=[
    ('beginning','Beginning'),
    ('departure','Departure'),
    ('kjv_levite:pl','Levites'),
    ('kjv_number:ev','The numbering'),
    ('law again','The law again'),
    ('kjv_joshua','Joshua'),
    ('judge:pl','Judges'),
    ('kjv_ruth','Ruth'),
    ('kjv_samuel','Samuel'),
    ('kjv_samuel','Samuel'),
    ('king:pl','Kings'),
    ('king:pl','Kings'),
    ('chronicle:pl','Chronicles'),
    ('chronicle:pl','Chronicles'),
    ('kjv_ezra_scribe','Ezra'),
    ('kjv_nehemiah_hachaliah','Nehemiah'),
    ('kjv_esther','Esther'),
    ('kjv_job_sufferer','Job'),
    ('kjv_psalm:pl','Sacred songs'),
    ('wise word:pl','Wise words'),
    ('kjv_preacher','The assembly teacher'),
    ('kjv_solomon/song','Solomon’s song'),
    ('kjv_isaiah','Isaiah'),
    ('kjv_jeremiah_prophet','Jeremiah'),
    ('lamentation:pl','Laments'),
    ('kjv_ezekiel','Ezekiel'),
    ('kjv_daniel_captive','Daniel'),
    ('kjv_hosea_prophet','Hosea'),
    ('kjv_joel_prophet','Joel'),
    ('kjv_amos_prophet','Amos'),
    ('kjv_obadiah_prophet','Obadiah'),
    ('kjv_jonah','Jonah'),
    ('kjv_micah_morasthite','Micah'),
    ('kjv_nahum_prophet','Nahum'),
    ('kjv_habakkuk_prophet','Habakkuk'),
    ('kjv_zephaniah_prophet','Zephaniah'),
    ('kjv_haggai_prophet','Haggai'),
    ('kjv_zechariah_prophet','Zechariah'),
    ('kjv_malachi_prophet','Malachi'),
    ('kjv_matthew_disciple','Matthew'),
    ('kjv_mark_surname_acts','Mark'),
    ('kjv_luke_physician_colossians','Luke'),
    ('kjv_john_zebedee','John'),
    ('deed:pl','Deeds'),
    ('kjv_rome_acts:d','To Rome'),
    ('kjv_corinth_acts:d','To Corinth'),
    ('kjv_corinth_acts:d','To Corinth'),
    ('kjv_galatia_acts:d','To Galatia'),
    ('kjv_ephesus_acts:d','To Ephesus'),
    ('kjv_philippi_acts:d','To Philippi'),
    ('kjv_colosse_colossians:d','To Colosse'),
    ('kjv_thessalonica_acts:d','To Thessalonica'),
    ('kjv_thessalonica_acts:d','To Thessalonica'),
    ('kjv_timothy_second_corinthians:d','To Timothy'),
    ('kjv_timothy_second_corinthians:d','To Timothy'),
    ('kjv_titus_second_corinthians:d','To Titus'),
    ('kjv_philemon_letter:d','To Philemon'),
    ('kjv_hebrew:pl:d','To the Hebrews'),
    ('kjv_james_epistle','James'),
    ('kjv_peter_disciple','Peter'),
    ('kjv_peter_disciple','Peter'),
    ('kjv_john_zebedee/letter','John’s letter'),
    ('kjv_john_zebedee/letter','John’s letter'),
    ('kjv_john_zebedee/letter','John’s letter'),
    ('kjv_jude_epistle','Jude'),
    ('reveal:ev','The unveiling'),
]


@lru_cache(maxsize=1)
def catalog():
    original,_=load_register(VERSION)
    register=copy(original)
    register.lexicon=dict(original.lexicon)
    for key,form in NAME_FORMS.items():
        assert set(form)<=original.letters and original.lexicon[key]['pos']=='proper'
        register.lexicon[key]=dict(original.lexicon[key],form=form)
    rows=[]
    for n,(book,(analysis,gloss)) in enumerate(zip(BOOKS,TITLE_ROWS,strict=True),1):
        parts=[register.word(token) for token in analysis.split()]
        text=register.maxima(' '.join(form for form,_,_ in parts))
        series=int(book[0]) if book[:1] in '123' else None
        if series and series>1:
            text+=' '+digits(series)
            gloss+=' '+str(series)
        keys=[k for _,_,used in parts for k in used]
        rows.append(dict(number=n,book=book,analysis=analysis,meaning=gloss,slots=text,
            roman=register.reading(text),series=series,semanticKeys=keys,
            titleNameAdaptations={k:dict(bodyRoman=original.reading(original.word(k)[0]),
                titleRoman=register.reading(register.word(k)[0])) for k in keys if k in NAME_FORMS}))
    assert len({r['slots'] for r in rows})==len(rows)==66
    assert rows[0]['slots']=='Pá' and rows[0]['roman']=='Pô'
    return rows


def shape_title(proof,text,spec):
    # The same engraved rectangle and mirrored ornaments bound every opening.
    left,right=(QRectF(*im['rect']) for im in spec['images'])
    frame=pe.decode_path(spec['paths'][0]).boundingRect()
    cx=frame.center().x()
    cy=frame.center().y()
    half=min(cx-left.right(),right.left()-cx)-7
    width=2*half
    height=frame.height()-18
    words=text.split()
    options=[[text]]
    for i in range(1,len(words)):
        if all(ch in '0123456789ÀÁ' for ch in words[i]):continue
        options.append([' '.join(words[:i]),' '.join(words[i:])])
    for size in range(84,31,-1):
        # Keep Genesis's short, well-known mark at the proof's original size.
        em=100 if text=='Pá' else size
        for lines in options:
            paths=[proof.word(line,em) for line in lines]
            boxes=[p.boundingRect() for p in paths]
            h=sum(b.height() for b in boxes)+6*(len(lines)-1)
            if h>height or max(b.width() for b in boxes)>width:continue
            y=cy-h/2
            full=QPainterPath()
            for p,b in zip(paths,boxes):
                full.addPath(p.translated(cx-b.center().x(),y-b.top()))
                y+=b.height()+6
            return pe.encode_path(full,'book-title'),dict(fontSizePt=em,lines=lines,
                inkWidthPt=full.boundingRect().width(),inkHeightPt=h)
    raise ValueError('Banner title does not fit: '+text)


def apply_titles(state):
    proof=Proof()
    edition=state['printEdition']
    result=[]
    for section,row in zip(edition['sections'],catalog(),strict=True):
        assert (section['number'],section['name'])==(row['number'],row['book'])
        spec=edition['pages'][section['pageId']]
        assert sum(p['role']=='chapter-number' for p in spec['paths']) in (0,1)
        assert sum(p['role']=='book-title' for p in spec['paths'])==1
        title,fit=shape_title(proof,row['slots'],spec)
        spec['paths']=[title if p['role']=='book-title' else p for p in spec['paths'] if p['role']!='chapter-number']
        result.append(dict(row,**fit))
    return result


def check_titles(state):
    proof=Proof()
    edition=state['printEdition']
    for section,row in zip(edition['sections'],catalog(),strict=True):
        spec=edition['pages'][section['pageId']]
        actual,=[p for p in spec['paths'] if p['role']=='book-title']
        assert section['name']==row['book'] and not any(p['role']=='chapter-number' for p in spec['paths'])
        expected,_=shape_title(proof,row['slots'],spec)
        assert actual==expected,(section['name'],row['roman'])
        box=QRectF(*actual['bounds'])
        assert all(not box.intersects(QRectF(*im['rect'])) for im in spec['images'])
