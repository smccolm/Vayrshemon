import unittest
from tools.kjv_archive import load_register,read
class PsalmAscentIdentityTests(unittest.TestCase):
 def test_corporate_divine_personal_and_physical_identity(self):
  prior,_=load_register('0.10-kjv.118');lang,manifest=load_register('0.10-kjv.119')
  self.assertEqual(prior.lexicon,{k:lang.lexicon[k] for k in prior.lexicon})
  for attr in ('pairs','suffix','prefix','possessors','roman'):self.assertEqual(getattr(prior,attr),getattr(lang,attr))
  cases={c['id']:c for c in read(lang.folder/'psalms-ascent-corporate-divine-cases.json')};self.assertEqual(len(cases),101)
  for c in cases.values():
   out=lang.compile(c['analysis']);self.assertEqual(c['expectedText'],out['text']);self.assertEqual(c['expectedGloss'],out['gloss']);self.assertNotIn('!',out['text'])
   self.assertFalse({'quick','right','suffer','close','exercise','matter','flourish','mark'}&set(out['keys']))
  for ref,parts in {
   '120-4':['kjv_charcoal:pl of kjv_juniper'],'120-5':['kjv_mesech','kjv_kedar'],
   '121-3':['move:psv:inf allow:neg:fu'],'121-5':['thy/shade','kjv_right_side'],
   '122-1':['wepl','go:opt'],'122-2':['our/foot:pl'],'122-9':['ourone/god','i thy/good:a'],
   '123-2':['our/eye:pl','ourone/god','wesg'],'123-4':['ourone/soul'],
   '124-1':['be:neg:pp'],'124-3':['wepl:a alive','against wesg'],'124-7':['ourone/soul','wesg escape:perf'],
   '125-3':['kjv_lot_portion'],'126-1':['wesg like'],'126-2':['ourone/mouth','for they do:perf'],
   '127-2':['sleep:a give:pr'],'127-5':['kjv_quiver','they shame:psv:neg:fu'],
   '128-6':['thy/child:pl/child:pl:a'],'129-1':['ipl:a','mypl/youth','kjv_israel now say:may'],
   '129-2':['ipl:a','prevail:neg:perf'],'129-3':['mypl/back','kjv_furrow:pl:a'],
   '129-8':['neither','wesg you:pl:a'],'130-3':['record:should'],'130-4':['forgive:ev','fear:psv:may'],
   '131-1':['myself:a in great thing:pl concern:pr'],'131-2':['quiet:caus:perf','kjv_wean:psv:perf'],
   '132-3':['i into tent of my/house'],'132-4':['mine eyelid:pl'],'132-6':['wepl','field:pl of wood'],
   '132-7':['wepl','wesg'],'132-8':['kjv_ark_chest'],'132-9':['kjv_righteousness','clothe:psv:opt'],
   '132-11':['ipl upon thy/throne'],'132-12':['if thy/child:pl','mypl/kjv_covenant:a','ipl they:a teach:fu'],
   '132-13':['he it:a'],'132-14':['mypl/rest','ipl dwell:fu'],'132-16':['salvation clothe:fu'],
   '132-17':['bud:caus:fu','mypl/anoint:psv:adj'],'132-18':['ipl his/enemy:pl:a','himself his/crown thrive:fu'],
   '133-2':['kjv_aaron/beard','kjv_hem:pl'],'134-1':['you:pl','by night'],'134-3':['thee:a','bless:opt'],
  }.items():
   for part in parts:self.assertIn(part,cases['psalms-'+ref]['analysis'],(ref,part))
  self.assertEqual(set(lang.lexicon)-set(prior.lexicon),{'kjv_mesech'})
  self.assertEqual(manifest['baseForgeHead'],read(prior.folder/'manifest.json')['forgeHead'])
