"""Create the native four-column key to volume numbers, relationships and source citations."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from PySide6.QtWidgets import QApplication
from tools.dictionary_layout import DictionaryLayout
from tools.dictionary_lexicon import load_gzip
from tools.reciprocal_publication import FOLDER,STAGE,WORK,ROOT,sha,digit
from tools.semantic_expansion import prepare_lang,adapted
from tools.reciprocal_verify import stamp
from vayrshemon.file_api import FileSession

NAME='Volume 00 - How to Use the Expanded Edition.vay'
COLS=('Vayrshemon','Transliteration 7','Construction gloss','English explanation and alphabetical ranges')
def main():
    lang=prepare_lang();cat=json.loads((WORK/'volumes.json').read_text('utf8'))
    ns=load_gzip(WORK/'reciprocal-lexicon.json.gz')['nodes'];byroman={n['roman']:n for n in ns}
    rows=[]
    def write(key,native,gloss,english,section='guide'):
        rows.append(dict(id=key,reference='Using the thesaurus' if section=='guide' else 'Alphabetical volumes',section=section,text=native,gloss=gloss,source=english))
    paras=[
      ('book of word:pl and near:m meaning:pl. each word by each written:m mark seek:imp.', 'Dictionary and thesaurus. Look up a word in Thimfora order, comparing each letter through the whole word.'),
      ('after example near:m word:pl see:imp. first number book show:pr. then word in that book seek:imp.', 'After an example come the related words. The numeral before a cross-reference identifies the volume. Find the word under its own spelling there.'),
      ('from first word to second go:can:pr. from second word to first again return:can:pr. both meaning:pl by their/example:pl compare:imp.', 'Each reference has a return reference. Read both examples to see which word fits the occasion.'),
      ('old:m word in old:m book find:can:psv:pr. from it new:m word here make:psv:pr. old:m book first word show:pr. new:m use its/own:m example here have:pr.', 'For a newly coined word, the historical references identify the older source reading. The new example illustrates the later word.'),
      ('from name new:m word for deed or way of deed come:can:pr. after name to new:m work its/image carry:psv:pr.', 'A name can yield a word for an action, a quality, a manner of acting, or an ordinary thing. The transfer into a new field is an allusion.'),
    ]
    for i,(analysis,english) in enumerate(paras):
        c=lang.compile(adapted(analysis.replace('number','mark of count'),lang));write('guide-'+str(i),c['text'],c['gloss'],english)
    sign=digit(12);count=lang.compile('mark of count in native:m word:pl and in other word:pl same:m book show:pr.'.replace('native:m','our/own:m'))
    write('numbering',count['text']+' '+sign+'.',count['gloss']+' Twelve.', 'Unta numerals in the native columns use base twelve. The English column and filenames use decimal. The native digits for one dozen name Volume 12.')
    for roman in ('renūl','jōrek','klēmun','shalōvek','shalōrin'):
        n=byroman[roman];r=n['reads'][0]
        write('choice-'+str(n['id']),n['form']+': '+r['definition']+' '+r['example'],n['label']+'. '+r['gloss']+' '+r['exampleGloss'],
              n['label']+'. '+r['meaning']+' '+r['exampleEnglish'],'examples')
    for m in cat:
        num=m['number'];a,b=m['rangeNative'];word=lang.compile('book',initial=True)
        write('volume-'+str(num),word['text'].rstrip('.')+' '+digit(num)+'. '+a+' – '+b+'.',
              'Volume '+str(num)+'. '+m['first']+' – '+m['last']+'.',
              'Volume '+f'{num:02d}'+'. '+m['first']+' – '+m['last']+'. '+format(m['heads'],',')+' headwords.','volumes')
    app=QApplication.instance() or QApplication([]);output=FOLDER['progressive']/NAME;stage=STAGE/'guide';stage.mkdir(exist_ok=True)
    layout=DictionaryLayout(title='Using the expanded Vayrshemon dictionary and thesaurus',document_id='document.reciprocal.guide',id_prefix='reciprocal.guide',column_names=COLS,cache_root=stage)
    try:report,_=layout.build(rows,stage/NAME,stamp(rows))
    finally:layout.session.finish()
    session=FileSession(ROOT,source_fonts=False,recovery=False);session.remember=lambda *a,**kw:None;session.log.emit=lambda *a,**kw:None
    try:
        session.open(stage/NAME,advance_revision=False);assert len(session.state['pages'])==report['pages'] and session.saved_page_mode=='two'
    finally:session.finish()
    (stage/NAME).replace(output)
    report.update(file=NAME,nativeReopened=True,ranges=len(cat),sha256=sha(output))
    (WORK/'guide.json').write_text(json.dumps(report,indent=1),encoding='utf8');print(report)
if __name__=='__main__':main()
