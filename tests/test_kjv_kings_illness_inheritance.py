import unittest
from tools.kjv_archive import load_register, read


class KingsIllnessInheritanceTests(unittest.TestCase):
    def test_personal_prayer_plural_self_promises_and_shadow_divisions(self):
        prior, _ = load_register('0.10-kjv.72')
        lang, manifest = load_register('0.10-kjv.73')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings2-illness-inheritance-cases.json')}
        self.assertEqual(47, len(cases))
        for case in cases.values():
            result = lang.compile(case['analysis'])
            self.assertEqual(case['expectedText'], result['text'])
            self.assertEqual(case['expectedGloss'], result['gloss'])
        for ref, parts in {
            '20-1': ['die:fu and live:fu not'],
            '20-3': ['i thou:a beseech:pr', 'perfect heart i walk:perf'],
            '20-5': ['captain of mypl/people', 'ipl heal:fu'],
            '20-6': ['fifteen year:pl:a', 'mypl/servant kjv_david'],
            '20-7': ['kjv_boil_lesion'],
            '20-9': ['ten kjv_shadow_degree:pl go:fu forward', 'or ten kjv_shadow_degree:pl go:fu back'],
            '20-10': ['easy thing'],
            '20-15': ['mypl/house', 'ipl show:perf not'],
            '20-18': ['eunuch:pl'],
            '20-19': ['peace and truth in my/day:pl'],
            '21-5': ['two kjv_court_enclosure:pl'],
            '21-6': ['kjv_observe_times:pa', 'kjv_familiar_spirit:pl and kjv_wizard:pl'],
            '21-8': ['only if', 'mypl/servant kjv_moses'],
            '21-11': ['kjv_judah:a with his/idol:pl sin:caus:perf'],
            '21-13': ['kjv_plummet', 'kjv_dish:a kjv_wipe:pr', 'with its/top down'],
            '21-16': ['from one_num end to another'],
            '21-19': ['kjv_meshullemeth daughter of kjv_haruz of kjv_jotbah'],
            '21-24': ['his/son kjv_josiah_amon:a king'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['2-kings-' + ref]['analysis'])
        self.assertEqual('data/language/archaic-kjv-72', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
