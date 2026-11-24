"""Make the four-column reader's guide and alphabetical volume key for each book."""
import argparse
import json

from PySide6.QtWidgets import QApplication
from tools.conventional_reference import SOURCE,edition,part,write_json
from tools.dictionary_corpus import ROOT,sha
from tools.dictionary_layout import DictionaryLayout
from tools.dictionary_lexicon import load_gzip
from tools.reciprocal_publication import digit
from tools.reciprocal_verify import stamp
from tools.semantic_expansion import prepare_lang
from vayrshemon.file_api import FileSession


def make(kind):
    book=edition(kind)
    lang=prepare_lang()
    cat=json.loads((book.work/'volumes.json').read_text('utf8'))
    nodes=load_gzip(SOURCE/'reciprocal-lexicon.json.gz')['nodes']
    title='Reader’s guide to the '+book.title
    rows=[]
    def add(key,section,native,gloss,english):
        rows.append(part(key,section,section.title(),native,gloss,english))
    def explain(key,analysis,english):
        c=lang.compile(analysis)
        add(key,'guide',c['text'],c['gloss'],english)
    explain('title','book of word:pl' if kind=='dictionary' else 'book of near:m meaning:pl',book.title+'.')
    explain('order','each word by each written:m mark seek:imp.',
            'Find the word in Thimfora order. Compare successive letters through the whole spelling.')
    if kind=='dictionary':
        explain('senses','each meaning and its/example read:imp.',
                'Each numbered sense has its own definition and example. Read the sentence to see which sense applies.')
        explain('witness','old:m word in old:m book find:can:psv:pr. from it new:m word here make:psv:pr.',
                'For a new formation, the historical citation identifies the older word or sense. The example illustrates the new use.')
    else:
        explain('group','near:m word:pl together read:imp. by example which word fit:pr see:imp.',
                'Read the choices together. Compare the examples for scope, register, and the circumstances in which each word fits.')
        explain('pointer','first mark of count book show:pr. second mark of count near:m word:pl together show:pr.',
                'An alphabetical pointer names the headword where the comparison appears. The first number gives its volume, the second its group.')
    count=lang.compile('mark of count in our/own:m word:pl and in other word:pl same:m book show:pr.')
    add('digits','guide',count['text']+' '+digit(12)+'.',count['gloss']+' Twelve.',
        'Native numbers use base twelve. The English column and file names use decimal. The numeral opposite names Volume 12.')
    forms=('renūl','vālem') if kind=='thesaurus' else ('gonzūm',)
    for form in forms:
        w=next(n for n in nodes if n['roman']==form);r=w['reads'][0]
        add('reading-'+str(w['id']),'examples',w['form']+': '+r['definition']+' '+r['example'],
            r.get('construction') or r['gloss']+' '+r['exampleGloss'],form+'. '+r['meaning']+' '+r['exampleEnglish'])
    prefix=lang.compile('book')['text'].rstrip('.')
    for m in cat:
        first,last=(nodes[i]['form'] for i in (m['headIDs'][0],m['headIDs'][-1]))
        n=m['number'];label=m['first']+' – '+m['last']
        add('range-'+str(n),'volumes',prefix+' '+digit(n)+'. '+first+' – '+last+'.',
            'Volume '+str(n)+'. '+label+'.',m['name']+'. '+label+'. '+format(m['heads'],',')+' headwords.')
    app=QApplication.instance() or QApplication([])
    stage=book.stage/'guide';stage.mkdir(exist_ok=True)
    name="Volume 00 - Reader's Guide.vay"
    layout=DictionaryLayout(title=title,document_id='document.'+book.key+'.guide',id_prefix=book.key+'.guide',
          column_names=('Vayrshemon','Transliteration 7','Construction gloss','English explanation and alphabetical ranges'),cache_root=stage)
    try:report,_=layout.build(rows,stage/name,stamp(rows))
    finally:layout.session.finish()
    session=FileSession(ROOT,source_fonts=False,recovery=False)
    session.remember=lambda *args,**kw:None
    session.log.emit=lambda *args,**kw:None
    try:
        session.open(stage/name,advance_revision=False)
        assert len(session.state['pages'])==report['pages'] and session.saved_page_mode=='two'
    finally:session.finish()
    target=book.folders['progressive']/name
    target.parent.mkdir(parents=True,exist_ok=True)
    (stage/name).replace(target)
    report.update(file=name,sha256=sha(target),ranges=len(cat),nativeReopened=True)
    write_json(book.work/'guide.json',report)
    print(book.title,'guide',report['pages'],'pages',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('kind',choices=['dictionary','thesaurus'])
    make(p.parse_args().kind)
