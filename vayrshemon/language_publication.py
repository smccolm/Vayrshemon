"""Searchable, printable publications from the exact selected language revision."""
from html import escape
import json
from .language import dataset, revision


def html_book(state, kind):
    rev = revision(state); data = dataset(state)
    title = {'dictionary':'Dictionary', 'grammar':'Grammar book', 'corpus':'Interlinear corpus'}[kind]
    def e(value): return escape(str(value))
    def citations(items):
        return '<ul class="citations">'+''.join('<li>'+e(c['sourceId'])+' · '+e(c['locator'])+'</li>' for c in items)+'</ul>' if items else ''
    def details(r):
        return '<p class="meta">'+e(r['id'])+' · '+e(r['status'])+'</p>'+('<p>'+e(r.get('notes',''))+'</p>' if r.get('notes') else '')+citations(r['citations'])
    sections = []
    if kind=='dictionary':
        for r in sorted(data['lexicon'], key=lambda r:(r['label'].casefold(),r['id'])):
            body = '<h2>'+e(r['label'])+'</h2>'+details(r)
            body += '<dl>'+''.join('<dt>'+e(k)+'</dt><dd>'+e(r[k])+'</dd>' for k in ('headword','pronunciation','ipa','partOfSpeech','etymology'))+'</dl>'
            body += '<ol>'+''.join('<li>'+e(s['definition'])+' <small>'+e(s['id'])+' · '+e(s['status'])+'</small>'+citations(s['citations'])+'</li>' for s in r['senses'])+'</ol>'
            body += '<ul>'+''.join('<li>'+e(v['script'])+': <span class="source">'+e(v['text'])+'</span> · '+e(', '.join(v['sourceFonts']))+' · '+e(v['note'])+'</li>' for v in r['variants'])+'</ul>'
            body += '<p>Examples: '+e(', '.join(r['exampleIds']))+'</p><p>Audio: '+e(', '.join(r['audioLinks']))+'</p>'
            sections.append('<article>'+body+'</article>')
    if kind=='grammar':
        for r in data['grammar']:
            body = '<h2>'+e(r['label'])+'</h2>'+details(r)+'<p class="source">'+e(r['statement'])+'</p>'
            body += ''.join('<aside>'+e(a['status'])+': '+e(a['statement'])+citations(a['citations'])+'</aside>' for a in r['alternatives'])
            body += '<p>Morphology: '+e(', '.join(r['morphologyIds']))+'<br>Examples: '+e(', '.join(r['exampleIds']))+'</p>'
            sections.append('<article>'+body+'</article>')
        for r in data['morphology']:
            body = '<h2>'+e(r['label'])+'</h2>'+details(r)+'<p>'+e(r['kind'])+' · '+e(r['form'])+'</p><p>'+e(json.dumps(r['features'],ensure_ascii=False))+'</p>'
            body += '<table><tr><th>Cell</th><th>Form</th><th>Features</th><th>Status</th></tr>'+''.join('<tr><td>'+e(c['label'])+'</td><td>'+e(c['form'])+'</td><td>'+e(json.dumps(c['features'],ensure_ascii=False))+'</td><td>'+e(c['status'])+citations(c['citations'])+'</td></tr>' for c in r['cells'])+'</table>'
            sections.append('<article>'+body+'</article>')
    if kind in ('grammar','corpus'):
        for r in data['corpus']:
            body = '<h2>'+e(r['label'])+'</h2>'+details(r)+'<p class="source">'+e(r['text'])+'</p><p>'+e(r['translation'])+'</p><p class="source">'+e(r['rawGloss'])+'</p>'
            body += '<table><tr><th>Source token</th><th>Segments</th><th>Glosses</th><th>Analysis</th></tr>'+''.join('<tr><td>'+e(t['surface'])+'</td><td>'+e(' · '.join(t['morphemes']))+'</td><td>'+e(' · '.join(t['glosses']))+'</td><td>'+e(t['status'])+' '+e(', '.join(t['entryIds']+t['morphologyIds']))+'</td></tr>' for t in r['tokens'])+'</table>'
            sections.append('<article>'+body+'</article>')
    sources = '<h2>Sources</h2>'+''.join('<article><h3>'+e(s['id'])+'</h3><p>'+e(s['path'])+'</p><code>'+e(s['sha256'])+'</code></article>' for s in data['sources'])
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><title>'+title+'</title><style>'
        'body{max-width:980px;margin:48px auto;padding:0 24px;color:#172134;background:#fff;font:16px/1.6 system-ui,sans-serif}'
        'h1{font-size:38px}h2{margin-top:0}article{padding:20px 0;border-top:1px solid #ccd7e6;break-inside:avoid}'
        '.meta,.citations,small{color:#52647c;font-size:13px}dt{font-weight:600}dd{margin:0 0 8px}table{border-collapse:collapse;width:100%}'
        'td,th{text-align:left;vertical-align:top;padding:7px;border:1px solid #d8e1ee}aside{background:#fff2c9;padding:14px}'
        '.source{white-space:pre-wrap}code{overflow-wrap:anywhere}@page{size:A4;margin:20mm}@media print{body{margin:0;padding:0;font-size:11pt}}'
        '</style><h1>'+title+'</h1><p>'+e(rev['label'])+'</p><p class="meta">Revision '+e(rev['id'])+'<br>SHA-256 '+e(rev['sha256'])+'</p>'
        '<p>Historical script and transliteration slots are preserved verbatim. Font-family hints do not establish a verified Unicode orthography. Uncertain analyses and competing revisions are retained; this publication does not promote them to canonical rules.</p>'
        +''.join(sections)+sources+'</html>')
