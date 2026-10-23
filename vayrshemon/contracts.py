"""M1 file wrapper and lab settings; embedded documents use the M0 contract."""
from .api import obj, BOOL

FEATURES = obj(dict(kern=BOOL, liga=BOOL), ('kern','liga'))
VIEW = obj(dict(mode={'enum':['mono','color']}, baselines=BOOL, origins=BOOL, bounds=BOOL,
                zoom={'type':'number','minimum':.1,'maximum':3}), ('mode','baselines','origins','bounds','zoom'))
LAYER = obj(dict(fontId={'type':'string'}, color={'type':'string','pattern':'^#[0-9a-fA-F]{6}$'},
                 enabled=BOOL, glyphMap={'type':'array','items':{'type':'integer','minimum':0},'maxItems':65536}),
            ('fontId','color','enabled','glyphMap'))
RECIPE = obj(dict(recipeId={'const':'recipe.thimfora.flat-lab'}, revision={'const':'0.1.0'}, master={'type':'string'},
                  layers={'type':'array','items':LAYER,'minItems':3,'maxItems':3}), ('recipeId','revision','master','layers'))
FONT_SOURCE = obj(dict(fontId={'type':'string'}, sha256={'type':'string','pattern':'^[0-9a-f]{64}$'}, path={'type':'string'}),
                  ('fontId','sha256','path'))
LAB = obj(dict(features=FEATURES, styleFeatures={'type':'object','additionalProperties':FEATURES,'maxProperties':2000},
               view=VIEW, recipe={'anyOf':[{'type':'null'},RECIPE]},
               fontSources={'type':'array','items':FONT_SOURCE,'maxItems':128}),
          ('features','styleFeatures','view','recipe','fontSources'))
LAB_DOCUMENT = obj(dict(format={'const':'vayrshemon.lab'},formatVersion={'const':'0.1.0'},
                        document={'type':'object'},lab=LAB,engine={'type':'object'}),
                   ('format','formatVersion','document','lab','engine'))
LAB_DOCUMENT.update({'$schema':'https://json-schema.org/draft/2020-12/schema',
                     '$id':'urn:vayrshemon:schema:lab-document:0.1.0',
                     'description':'The document property is additionally validated against document.schema.json and M1 semantic constraints.'})
