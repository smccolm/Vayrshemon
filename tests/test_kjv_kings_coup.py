import unittest
from tools.kjv_archive import load_register, read


class KingsCoupTests(unittest.TestCase):
    def test_quoted_identity_selective_reporting_and_distinct_kings(self):
        prior, _ = load_register('0.10-kjv.66')
        lang, manifest = load_register('0.10-kjv.67')
        self.assertEqual(prior.lexicon, {k: lang.lexicon[k] for k in prior.lexicon})
        for field in ('pairs', 'suffix', 'prefix', 'possessors', 'roman'):
            self.assertEqual(getattr(prior, field), getattr(lang, field))
        cases = {c['id']: c for c in read(lang.folder / 'kings2-coup-cases.json')}
        self.assertEqual(66, len(cases))
        for c in cases.values():
            result = lang.compile(c['analysis'])
            self.assertEqual(c['expectedText'], result['text'])
            self.assertEqual(c['expectedGloss'], result['gloss'])
        for ref, parts in {
            '8-10': ['certainly thou recover:pr:may', 'surely he die:fu'],
            '8-14': ['surely thou recover:pr:should'],
            '8-15': ['thick cloth:a kjv_hazael take:pa', 'king die:pa'],
            '8-16': ['kjv_jehoshaphat_asa then king', 'kjv_jehoram_jehoshaphat'],
            '8-25': ['twelve:ord year', 'kjv_ahaziah_jehoram'],
            '8-26': ['kjv_athaliah daughter of kjv_omri'],
            '9-5': ['kjv_errand:a i have:pr', 'which of all wepl'],
            '9-6': ['oil:a on his/head messenger pour:pa', 'ipl anoint:perf'],
            '9-12': ['now to wesg tell:imp', 'to i he speak:pa', 'ipl anoint:perf'],
            '9-19': ['two:ord messenger:a on horse'],
            '9-21': ['each in his/chariot', 'they:du go:pa out'],
            '9-25': ['i and thou together'],
            '9-26': ['of his/son:pl blood:a ipl see:perf', 'ipl repay:fu'],
            '9-29': ['ten and one_num:ord year'],
            '9-30': ['her/face:a paint:pa', 'her/head:a adorn:pa'],
            '9-32': ['who on mypl/side', 'two or kjv_three eunuch:pl'],
            '9-35': ['kjv_skull and foot:pl and kjv_palm_hand:pl'],
        }.items():
            for part in parts:
                self.assertIn(part, cases['2-kings-' + ref]['analysis'])
        self.assertNotIn('die', cases['2-kings-8-14']['analysis'])
        self.assertEqual('data/language/archaic-kjv-66', manifest['basePackage'])


if __name__ == '__main__':
    unittest.main()
