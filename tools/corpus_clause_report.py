"""Publish clause-level evidence and link every editorial change to its English passage."""
from collections import Counter
import gzip
from html import escape
import shutil
from tools.corpus_clause_release import REVIEW, S, read, edited, revised, textpaths, sources, sha, write
from tools.corpus_clause_revision import B, BP, H, HP

def records(path):
    with gzip.open(path,'rt',encoding='utf8') as handle:
        for line in handle:
            yield json.loads(line)

import json

DECISIONS={
    'antony-and-cleopatra/00783a/1':'The three cries of shame reproduce the repeated “fie.”',
    'as-you-like-it/00829a/1':'“Swiftly begin” renders the idiom about starting the song.',
    'coriolanus/01074a/0':'The guard uses the command “stop” for “stay.”',
    'henry-v/00244a/2':'Corrected the question about the fingers.',
    'henry-v/00260a/2':'Corrected the question about the chin.',
    'henry-viii/00392b/1':'The parser separated “ne’er” from its verb. The native clause retains “never dreamed.”',
    'julius-caesar/00575a/2':'The negative belongs to the governing judgment about every small offence receiving blame.',
    'king-lear/00779a/2':'Albany compares the effect of deformity in a fiend and in a woman. The comparison continues beyond this fragment.',
    'measure-for-measure/00010c/5':'The ordinal describes who was mentioned first. Escalus serves under Angelo.',
    'the-merry-wives-of-windsor/00471a/1':'The two oaths and Caius’s expectation are present. The gloss normalizes his accent.',
    'a-midsummer-nights-dream/0662/8':'“Alas” occurs three times for “alack.”',
    'richard-ii/00276b/1':'The target expresses causing misery and marring completely.',
    'richard-ii/00600a/2':'The habit construction renders “as thou art wont to do.”',
    'richard-iii/00244b/1':'The unstable footing of the deck and “it seemed to me” are both present.',
    'romeo-and-juliet/00151c/1':'Corrected the Nurse’s self-interruption from assent to “Nay.”',
    'twelfth-night/00086a/2':'The affirmative statement takes a confirmation-seeking tag.',
}

def main():
    output=revised(REVIEW);output.mkdir(parents=True,exist_ok=True)
    decisions={**DECISIONS,**read(S/'context-adjudications.json')}
    context={}
    for first,second in zip(*(records(S/('context-'+m+'-scores.jsonl.gz')) for m in ('reading','gloss')),strict=True):
        assert first[0]==second[0]
        context[first[0]]=[first[1:],second[1:]]
    persistent={k for k,(a,b) in context.items() if min(a[0],b[0])>=.98}
    changes=read(S/'changes.json'); summaries=read(S/'audit-totals.json')
    write(output/'corrections.json',changes)
    checked=read(S/'verified-publications.json')
    for folder in (B,BP,H,HP):
        checked[folder.name]['nativeFile']=next(folder.glob('*.vay')).name
        if folder in (BP,H):
            receipt=read(S/('bible-pdf.json' if folder==BP else 'shakespeare-pdf.json'))
            pdf=next(folder.glob('*.pdf'))
            assert sha(edited(pdf))==receipt['sha256']
            checked[folder.name].update(pdfFile=pdf.name,pdfSha256=receipt['sha256'],physicalPages=receipt['pages'])
    write(output/'verified-publications.json',checked)
    totals=Counter(); ranking=[]
    labels={w['slug']:w['title'] for w in sources()};labels['bible']='King James Bible'
    def row_inputs():
        for slug,path in textpaths():
            for u in read(edited(path))['units']:yield slug,u
    audit=records(S/'clause-audit.jsonl.gz')
    scores=[records(S/(mode+'-scores.jsonl.gz')) for mode in ('reading','gloss')]
    with gzip.open(output/'clause-comparison.jsonl.gz','wt',encoding='utf8',compresslevel=5) as dest:
        for (slug,unit),entry in zip(row_inputs(),audit,strict=True):
            assert (slug,unit['id'],unit['analysis'])==(entry['work'],entry['id'],entry['analysis'])
            entry.update(native=unit['text'],constructionGloss=unit['gloss'],backReading=unit.get('backTranslation',unit.get('backReading','')))
            for i,c in enumerate(entry['clauses']):
                key=f"{slug}/{unit['id']}/{i}"
                a,b=[next(it) for it in scores];assert key==a[0]==b[0]
                c.update(backReadingAndGlossScores=a[1:],glossScores=b[1:])
                totals[c['status']]+=1;totals['clauses']+=1
                if key in context:c['sourceContextScores']=context[key]
                if key in decisions:c['editorialReading']=decisions[key]
                if min(a[1],b[1])>=.98:
                    ranking.append((key,unit.get('reference',unit['id']),labels[slug],c['english'],entry['source'],unit['gloss'],entry['backReading'],a[1],b[1],decisions.get(key,'')))
            totals['passages']+=1
            dest.write(json.dumps(entry,ensure_ascii=False,separators=(',',':'))+'\n')
    assert all(next(it,None) is None for it in scores)
    assert totals['clauses']==sum(t['clauses'] for t in summaries.values())==312463 and totals['passages']==70877
    def put(name,body):
        (output/name).write_text(body,encoding='utf8')
    def item(title,elements):
        return '<details><summary>'+escape(title)+'</summary>'+''.join('<p><b>'+escape(k)+'</b> '+escape(str(v))+'</p>' for k,v in elements)+'</details>'
    def html(title,body):
        return '<!doctype html><html lang="en"><meta charset="utf-8"><title>'+escape(title)+'</title><style>body{font:17px Georgia,serif;max-width:62em;margin:3em auto;line-height:1.45;padding:0 1.5em}h1,h2,summary,b{font-family:system-ui,sans-serif}details{padding:.5em 0;border-top:1px solid #ddd}summary{cursor:pointer}p{overflow-wrap:anywhere}b{font-size:.88em}</style><h1>'+escape(title)+'</h1>'+body+'</html>'
    retained=sum(not r[-1] for r in ranking)
    put('Priority readings.html',html('Priority readings',
        f'<p>Both comparison views flagged {len(ranking):,} clauses. A second pass supplied the surrounding English passage or sentence. {len(persistent):,} still crossed the same 0.98 threshold in both views. {len(persistent-set(decisions)):,} of those lack an individual disposition. {retained:,} initial flags have no individual disposition. Expand a reading to inspect its full context.</p>'+
        ''.join(item(f'{label} · {ref} · {en[:100]}', [('Identifier',k),('English passage',src),('English clause',en),('Construction gloss',gl),('Back-reading',br),('Initial comparison scores',f'{a}, {b}'),('Scores with full source context',', '.join(str(v[0]) for v in context[k])),('Disposition',decision or 'Below threshold in context; individually unadjudicated' if k not in persistent else decision or 'Open')]) for k,ref,label,en,src,gl,br,a,b,decision in sorted(ranking,key=lambda r:(r[0] not in persistent,-min(r[7],r[8]),r[0])))))
    put('Corrected passages.html',html('Corrected passages',''.join('<h2>'+escape(labels[slug])+'</h2>'+''.join(item(k+' · '+v['source'][:100],[('English',v['source']),('Reason',v['note']),('Previous native',v['oldText']),('Corrected native',v['text']),('Previous construction gloss',v['oldGloss']),('Corrected construction gloss',v['gloss'])]) for k,v in rows.items()) for slug,rows in changes.items())))
    allcounts={slug:len(rows) for slug,rows in changes.items()}
    write(output/'audit-counts.json',dict(**totals,byWork=summaries,changedPassages=allcounts,bothScoresAtLeast98=len(ranking),contextPersistent=len(persistent),persistentIndividuallyOpen=sorted(persistent-set(decisions)),initialFlagsIndividuallyOpen=retained,individualReadings=decisions))
    rows=''.join(f"<li>{escape(n)} — {v['nativePages']:,} native pages, {v['passages']:,} passages</li>" for n,v in checked.items())
    body=f"""<p>The English body of all 66 Bible books and all 42 supplied Shakespeare works was compared against the issued translations. The comparison covers 31,102 KJV verses and 39,775 Shakespeare passages. The Shakespeare sources comprise 38 plays and four poetry publications. The scope follows the bodies of the supplied editions, including their stage directions. Publisher preliminaries and cast catalogues outside those bodies are excluded.</p>
<h2>Corrections</h2><p>{allcounts['bible']:,} Bible verses and {sum(allcounts.values())-allcounts['bible']:,} Shakespeare passages changed. All 16 misreadings of Lot now identify the person. Hamlet 1.1 restores Marcellus’s sentence “It faded on the crowing of the cock.” Other corrections include Jehoiada’s name, Yeshūa and the title Christ, the quotations in Mark and Matthew, Deuteronomy 32:6, omitted stage directions and addresses, and 204 passages that used the oath for the verb “marry.” Most remaining changes restore question punctuation. <a href="Corrected passages.html">Read all corrections side by side</a> or download the <a href="corrections.json">change ledger</a>.</p>
<h2>Method and limits</h2><p>The comparison reconstructed the supplied English in order. An English dependency parser divided it into 113,510 Bible and 198,953 Shakespeare clauses and fragments. For each clause the audit matched English words to the passage’s native morphological analysis, with each occurrence assigned at most once. {totals['lexical evidence']:,} segments had at least one lexical match, {totals['no lexical anchor']:,} had content words without a match, and {totals['function words or punctuation']:,} had only material such as function words or punctuation.</p>
<p>A local English-language inference model also compared every clause twice, once with the construction gloss, once with the passage back-reading and gloss together. Both views share the same gloss and model. The written back-readings vary in detail. The model operates on English proxies, truncates long premise text, and cannot certify Vayrshemon meaning, style, or wordplay. Each result stores the full native passage, gloss and English, plus both score triples in contradiction, entailment, neutral order. <a href="clause-comparison.jsonl.gz">Complete clause comparisons</a>.</p>
<p>The targeted editorial checks covered proper names, stage directions, the oath and marriage distinction, negative questions, and high-risk comparisons. When both clause-level views scored at least 0.98 for contradiction, the model ran again using the surrounding English. Of {len(ranking):,} initial flags, {len(persistent):,} persisted in context and {len(persistent-set(decisions)):,} of those await individual review. The separate editorial readings include the correction to Lafew’s assurance about Bertram in <i>All’s Well That Ends Well</i>. Full mechanical coverage does not establish that every literary reading has been individually checked. {retained:,} of the initial flags lack an individual disposition. <a href="Priority readings.html">Inspect flagged readings</a> · <a href="audit-counts.json">Counts and individual readings</a>.</p>
<h2>Publications verified</h2><ul>{rows}</ul><p>Reconstructed all passages from the saved print pages, checked all four columns in both progressive editions and compared the individual Shakespeare books against their revised ledgers. Both duplex PDFs keep the preceding print masters’ physical page counts, page pairing and navigation. <a href="verified-publications.json">Publication hashes</a>.</p>"""
    put('Audit.html',html('Bible and Shakespeare clause review',body))
    print(totals, len(ranking),retained,flush=True)

if __name__=='__main__':main()

