"""Saved Unta settings, including an opt-in minimum document page count."""
from copy import deepcopy
from .api import obj

POSITION=obj(dict(visible={'type':'boolean'},vertical={'enum':['top','bottom']},
                  horizontal={'enum':['left','right']}),('visible','vertical','horizontal'))
FIELDS=dict(enabled={'type':'boolean'},sizePt={'type':'number','minimum':8,'maximum':150},
            edgeInsetPt={'type':'number','minimum':2,'maximum':144},
            single=POSITION,left=deepcopy(POSITION),right=deepcopy(POSITION))
SETTINGS=obj(dict(version={'const':1},**FIELDS),('version',*FIELDS))
PATCH=obj(deepcopy(FIELDS))
SETTINGS['properties']['minimumPages']={'type':'integer','enum':[1,2]}
PATCH['properties']['minimumPages']={'type':'integer','enum':[1,2]}
for key in ('single','left','right'):PATCH['properties'][key]['required']=[]


def defaults():
    return dict(version=1,enabled=False,sizePt=50,edgeInsetPt=28,
                single=dict(visible=True,vertical='bottom',horizontal='right'),
                left=dict(visible=True,vertical='bottom',horizontal='left'),
                right=dict(visible=True,vertical='bottom',horizontal='right'))


def new_document_defaults():
    return dict(defaults(),enabled=True,minimumPages=2)
