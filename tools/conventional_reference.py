"""Build independent dictionary articles and thesaurus usage groups from the issued lexicon."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json

from tools.dictionary_corpus import ROOT
from tools.dictionary_lexicon import load_gzip, save_gzip
from tools.dictionary_rows import filing_initial
from tools.reciprocal_publication import ReferenceEdition, digit, volume
from tools.semantic_expansion import WORK as SOURCE, prepare_lang


def edition(kind):
    title='Vayrshemon '+kind.title()
    root=ROOT/'Saves'/title
    return ReferenceEdition(title,'conventional'+kind,root/'Working',ROOT/'.local/conventional-reference'/kind,
        {'print':root/'Letter Print Edition','progressive':root/'Four-Column Progressive Edition'},
        'English definitions, examples and sources' if kind=='dictionary' else 'English meanings, usage distinctions and examples')


def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=1),encoding='utf8')


def part(record_id,section,roman,text,gloss,english):
    return dict(id=record_id,section=section,reference=roman,text=text,gloss=gloss,source=english)


def print_part(record_id,head,kind,text):
    return dict(id=record_id,head=head,kind=kind,text=text)


def prepare(kind):
    book=edition(kind)
    book.work.mkdir(exist_ok=True,parents=True)
    (book.stage/'volumes').mkdir(exist_ok=True,parents=True)
    nodes=load_gzip(SOURCE/'reciprocal-lexicon.json.gz')['nodes']
    lang=prepare_lang()
    if kind=='dictionary':
        articles=dictionary_articles(nodes)
        title,guide='book of word:pl','each word seek:imp. each meaning and its/example read:imp.'
        intro='Look up the headword in Thimfora order. Each numbered sense has its own example.'
    else:
        from tools.conventional_synonyms import thesaurus_articles
        articles=thesaurus_articles(nodes,lang,book.work)
        title,guide='book of near:m meaning:pl','near:m word:pl together read:imp. by example which word fit:pr see:imp.'
        intro='Compare the words in a sense group. Each has a usage example. The alphabetical pointers also lead from each alternative to the group.'
    native_title=lang.compile(title)['text'].rstrip('.')
    native_guide=lang.compile(guide)['text']
    catalogue=[]
    for batch,group in enumerate(articles,1):
        section='opening'; heads=[a[0] for a in group]
        rows=[part('title',section,book.title,native_title+' '+digit(batch)+'. '+native_guide,
                   book.title+'. '+str(batch)+'. '+lang.compile(guide)['gloss'],book.title+', volume '+str(batch)+'. '+intro)]
        printed=[];head_rows=[]
        for _,body,pr in group:
            head_rows.append(body[0]['id'])
            rows.extend(body);printed.extend(pr)
        meta=dict(number=batch,name=f'Volume {batch:02d}',title=native_title,guide=native_guide,heads=len(heads),
                  first=nodes[heads[0]]['roman'],last=nodes[heads[-1]]['roman'],headIDs=heads,headRows=head_rows,
                  rows=len(rows),printParagraphs=len(printed))
        save_gzip(book.stage/'volumes'/f'{batch:02d}.json.gz',dict(rows=rows,print=printed,meta=meta))
        catalogue.append(meta)
    write_json(book.work/'volumes.json',catalogue)
    print(book.title,len(catalogue),'volumes',sum(m['heads'] for m in catalogue),'alphabetical entries',flush=True)


def dictionary_articles(nodes):
    batch=[]
    for n in nodes:
        head=n['form'];roman=n['roman'];section='letter-'+str(ord(filing_initial(head)))
        rows=[];printed=[]
        for i,s in enumerate(n['reads']):
            key=f"w{n['id']}.{i}"
            prefix=(head+': ' if i==0 else '')+(digit(i+1)+' ' if len(n['reads'])>1 else '')
            glossnum=(str(i+1)+'. ' if len(n['reads'])>1 else '')
            definition=prefix+s['definition']
            english=glossnum+s['meaning']
            refs=' '.join(s['references'])
            if s.get('construction'):
                rows.append(part(key,section,roman,definition+' '+s['example'],glossnum+s['construction'],
                                 english+' Example: '+s['exampleEnglish']+' '+refs))
            else:
                rows.extend([part(key,section,roman,definition,glossnum+s['gloss'],english+' '+refs),
                             part(key+'x',section,roman,s['example'],s['exampleGloss'],s['exampleEnglish'])])
            printed.extend([print_part(key,head,'definition',definition),print_part(key+'x',head,'example',s['example'])])
        batch.append((n['id'],rows,printed))
        if len(batch)==1600:
            yield batch
            batch=[]
    if batch:yield batch


def build(kind,formats,workers,numbers):
    book=edition(kind)
    catalogue=json.loads((book.work/'volumes.json').read_text('utf8'))
    jobs=[(fmt,n) for n in (numbers or range(1,len(catalogue)+1)) for fmt in formats]
    with ProcessPoolExecutor(max_workers=workers,max_tasks_per_child=1) as pool:
        tasks=[pool.submit(volume,f,n,book) for f,n in jobs]
        for task in as_completed(tasks):
            print(task.result(),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('book',choices=['dictionary','thesaurus'])
    p.add_argument('action',choices=['prepare','print','progressive','both','bind'])
    p.add_argument('--workers',type=int,default=6)
    p.add_argument('--volumes',nargs='*',type=int)
    a=p.parse_args()
    if a.action=='prepare':
        prepare(a.book)
    elif a.action=='bind':
        from tools.dictionary_continuous_print import bind
        from tools.conventional_reference_proof import verify
        bind(edition(a.book))
        verify(a.book)
    else:
        build(a.book,['print','progressive'] if a.action=='both' else [a.action],a.workers,a.volumes)
