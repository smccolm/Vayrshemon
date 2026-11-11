from html import escape
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.kjv_native_vocabulary import OUT,PACKAGE,VERSION,load_register,read

def main():
    assert not (OUT/'FROZEN.json').exists()
    lang,_=load_register(VERSION)
    review=read(PACKAGE/'vocabulary-review.json')['entries']
    units={u['reference']:u for u in read(OUT/'complete-translation-ledger.json')['units']}
    verse=units['Revelation 22:13']
    proof=''
    if (OUT/'page-index.json').exists():
        spread=next(s for s in read(OUT/'page-index.json')['spreads'] if verse['reference'] in s['references'])
        proof='<p><a href="Proofs/page-'+format(spread['leftPage'],'05d')+'.png">See the printed reading on page '+str(spread['leftPage'])+'</a></p>'
    entries=[]
    for key in sorted(review):
        row=review[key]
        parts=' + '.join(row['components'])
        refs=row['verses']
        # A verse reference appears once per dictionary entry and can be found
        # without knowing the key or the book's native page number.
        cells=[key,row['beforeRoman'],row['afterRoman'],parts,row['reason']]
        citations='<details><summary>'+str(len(refs))+' verse'+('' if len(refs)==1 else 's')+'</summary>'+escape(', '.join(refs))+'</details>' if refs else 'Dictionary only'
        entries.append('<tr>'+''.join('<td>'+escape(c)+'</td>' for c in cells)+'<td>'+citations+'</td></tr>')
    out='''<!doctype html><meta charset="utf-8"><title>Native vocabulary in the two KJV editions</title>
<style>body{font:18px/1.55 Georgia,serif;max-width:90em;margin:2rem auto;padding:0 1rem;color:#222}p,blockquote{max-width:55em}table{border-collapse:collapse;width:100%;font-size:16px}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #ddd;padding:.5em}h2{margin-top:2em}a{color:#155b79}</style>
<h1>Native vocabulary in the two KJV editions</h1>
<h2>Alpha and Omega</h2><p>The earlier <i>endin jelam</i> used English <i>end</i> for the adjective “last.” The chart already gives <i>hüŧh</i> for “end.” Its adjective is <i>hüŧh’na</i>. Writing and a mark supply <i>īvden</i>. The speaker calls himself the first and last written signs of the Greek alphabet. The edition also keeps the two further pairs in Revelation 22:13.</p>
'''
    out+='<blockquote lang="en">'+escape(verse['source'])+'</blockquote><blockquote>'+escape(lang.reading(verse['text']))+'</blockquote>'+proof
    out+='''<h2>Ordinary words and names</h2><p><i>Omibra</i>, “wink,” joins eye and shut. <i>Trembra</i>, “fist,” names the closed hand. In Judges 14:17 the feast <em>lasted</em>, so the translation uses the verb for continuing. In Isaiah 14:8 the trees rejoice that the woodcutter has ceased coming up against them.</p>
<p><i>Yardēn</i> names the Jordan and <i>Dawīd</i> names David. <i>Roma’na</i> expresses Roman affiliation or citizenship as the passage requires. The English source identifies the historical people, places and offices. Stable dictionary keys distinguish people who share a spoken name.</p>
<h2>Dictionary decisions</h2><p>“Components” gives dictionary lookup keys. Readings use the native register’s Roman transcription. The verse column expands to show every reference for the revised key.</p><table><thead><tr>
<th>Dictionary key</th><th>Earlier reading</th><th>Current reading</th><th>Components</th><th>Reason</th><th>References</th></tr></thead><tbody>
'''
    (OUT/'Vocabulary review.html').write_text(out+''.join(entries)+'</tbody></table>',encoding='utf8')

if __name__=='__main__':main()
