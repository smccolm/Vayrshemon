"""Authored lexical decisions for Phoenix; no generated English substitution."""
from copy import deepcopy
from tools.shakespeare_project import PROJECT,read,write,materialize

PROMOTIONS={
 'tree':('kjv_tree','tree','Woody plant with trunk and branches. Generic tree; the Arabian tree is not silently identified as a palm.'),
 'arabia':('kjv_arabia','Arabia','Arabia as the poetic location; place-name sounds are permitted, with no modern national boundaries supplied.'),
 'turtledove':('kjv_turtledove','turtledove','The dove bird called turtle in the poem; never a shelled reptile.'),
 'eagle':('kjv_eagle','eagle','Eagle, the expressly exempted feathered king. Bird category, not a new named human sovereign.'),
 'swan':('kjv_swan','swan','The poem’s white swan and death-song image. Literary bird identity is explicit here; no claim resolves the old Biblical zoological uncertainty.'),
 'fever':('kjv_fever','fever','Bodily fever, whose end is ominously foretold; do not assert recovery when death may be meant.'),
 'strict':('kjv_strict','strict','Close observance of a rule or ritual; not narrow spatial width.'),
 'posterity':('kjv_posterity','posterity','Continuing descendants; not fame or memory after death.'),
 'ashes':('kjv_ashes','burnt-residue','Ashes/cinders, residue of burning. Keeps the lovers’ fire and urn connected without adding resurrection.'),
}
COMPOUNDS={
 'dirge':(['mourn','song'],'mourning-song','A funeral lament, including the threne/Threnos. Native vocabulary, not a respelled Greek heading.'),
 'requiem':(['dead','hymn'],'dead-hymn','Hymn for the dead in the specified rite; not a generic concert or an assertion of a particular later musical setting.'),
 'funerary_urn':(['ashes','vessel'],'ashes-vessel','Vessel holding funerary burnt remains in this poem; does not imply an unspecified exact shape.'),
 'number_abstract':(['reckon','essence'],'number','Number as numerical distinction, personified in love’s abolition of counting; distinct from noble Count.'),
 'forecomer':(['before','come'],'forecomer','One arriving ahead, an ominous precursor here. Native compositional agent stem; the modifier and fiend remain explicit.'),
 'treble_lived':(['three','life'],'three-lived','Having a threefold life-span in the crow address. No numeral is changed and no zoological mechanism or comparison species is inserted.'),
 'self_distinction':(['self','property'],'self-property','Property personified: defining individuality with a possessive resonance. Not merely real estate or a moral prohibition on ownership.'),
}

def prepare():
    lang=materialize();delta=read(PROJECT/'lexical-delta.json')
    assert not any(k in delta['entries'] for k in PROMOTIONS|COMPOUNDS)
    def add(key,entry,gloss,note):
        entry.update(semanticId='lex.shakespeare.'+key,usageScope='later-literary',development='reviewed-0.13-expansion',
            origin='The Phoenix and Turtle: '+note,historicalForms=[],historicalWitness=None)
        delta['entries'][key]=entry;delta['glosses'][key]=gloss
        delta['decisions'].append(dict(key=key,work='the-phoenix-and-turtle',decision=note))
        lang.lexicon[key]=entry
    for key,(base,gloss,meaning) in PROMOTIONS.items():
        e=deepcopy(lang.lexicon[base]);e['meaning']=meaning
        add(key,e,gloss,'Explicit literary promotion of '+base+'; same native form, reviewed meaning, older entry untouched.')
    for key,(parts,gloss,meaning) in COMPOUNDS.items():
        form=''.join(lang.lexicon[k]['form'] for k in parts)
        e=dict(form=form,roman=lang.reading(form),pos='noun',meaning=meaning,derivationKeys=parts)
        if key=='treble_lived':e['pos']='adjective'
        if key=='self_distinction':e['pos']='proper'
        add(key,e,gloss,'Native compound of '+', '.join(parts)+'. '+meaning)
    for key,base,meaning in [
        ('phoenix_symbol','phoenix','The personified Phoenix of this poem, without identifying a historical human allegorical referent.'),
        ('turtle_symbol','turtledove','The poem’s personified Turtle; male dove paired with his queen, not a reptile.'),
        ('reason_personified','reason','Reason as a reasoning persona; distinct from the rationality that Love is said to possess.')]:
        e=deepcopy(lang.lexicon[base]);e.update(pos='proper',meaning=meaning)
        add(key,e,{'phoenix_symbol':'Phoenix','turtle_symbol':'Turtle','reason_personified':'Reason'}[key],meaning+' Native base '+base+' retained.')
    for key,form,label in [('william','wilyam','William'),('shakespeare','Ûekspir','Shakespeare')]:
        add(key,dict(form=form,roman=lang.reading(form),pos='proper',meaning=label+', the supplied author’s personal name.'),label,'Permitted approximate personal-name sound; not ordinary vocabulary.')
    write(PROJECT/'lexical-delta.json',delta);materialize()
    print('Phoenix: 9 reviewed historical promotions, 7 native compounds, 3 distinct personifications, 2 personal names.')

def refine():
    """Review ordinary terms that the inherited bank wrongly borrowed."""
    lang=materialize();delta=read(PROJECT/'lexical-delta.json')
    for key,parts,pos,gloss,meaning in [
        ('crow_bird',['black','bird'],'noun','crow','Crow: lexicalized native black-bird compound identifying the crow species category in this poem; not every black bird.'),
        ('choral_song',['gather','song'],'noun','choral-song','Collective anthem or choral response, including the chorus framing this funeral; not an imported Greek sound.'),
        ('appall_native',['fear','astonish'],'verb','appall','Astound with horror, in the poem the reaction of personified Property to the loss of self-distinction.')]:
        if key in delta['entries']:continue
        assert key not in lang.lexicon
        form=''.join(lang.lexicon[k]['form'] for k in parts)
        delta['entries'][key]=dict(form=form,roman=lang.reading(form),pos=pos,meaning=meaning,
            semanticId='lex.shakespeare.'+key,usageScope='later-literary',development='reviewed-0.13-expansion',
            origin='Native compound of '+', '.join(parts),historicalForms=[],derivationKeys=parts)
        delta['glosses'][key]=gloss
        delta['decisions'].append(dict(key=key,work='the-phoenix-and-turtle',decision=meaning))
    write(PROJECT/'lexical-delta.json',delta);materialize()

if __name__=='__main__':
    import sys
    if '--refine' in sys.argv:refine()
    else:prepare()
