"""Historical register isolation, exact source inventory and anti-migration guards."""
from pathlib import Path
import tempfile
import unittest

from tools.editorial_language import EditorialLanguage
from tools.kjv_archive import (ROOT, PACKAGE, assert_can_consolidate, load_register,
                               parse_source, read, safe_member, seal,
                               verify_seal, write_new, translation_coverage, require_complete_bible)


class WholeBibleCoverageTests(unittest.TestCase):
    def setUp(self):
        self.index = dict(sourceSha256='source', verseCount=2, books=[
            dict(number=1,name='First section',verseCount=1,verses=[dict(id='a',source='First.')]),
            dict(number=2,name='Second section',verseCount=1,verses=[dict(id='b',source='Second.')])])
        self.units = [dict(id=v['id'],source=v['source'],analysis='structural test',text='structural test',
                           gloss='structural test',backReading='structural test',note='Synthetic coverage fixture.')
                      for b in self.index['books'] for v in b['verses']]

    def ledger(self, units):
        return dict(sourceSha256='source',units=units)

    def test_one_complete_section_is_not_the_complete_bible(self):
        ledgers=[self.ledger(self.units[:1])]
        report=translation_coverage(self.index,ledgers)
        self.assertTrue(report['sections'][0]['complete'])
        self.assertFalse(report['complete'])
        self.assertEqual(['b'],report['missingVerseIds'])
        with self.assertRaisesRegex(ValueError,'INCOMPLETE_BIBLE: 1/2'):
            require_complete_bible(self.index,ledgers)

    def test_complete_means_every_source_identity_not_only_a_row_count(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_VERSE'):
            require_complete_bible(self.index,[self.ledger([self.units[0],self.units[0]])])
        self.assertTrue(require_complete_bible(self.index,[self.ledger(self.units)])['complete'])

    def test_source_only_placeholder_and_changed_source_are_rejected(self):
        for key,error in [('text','UNAUTHORED_VERSE'),('analysis','UNAUTHORED_VERSE'),('source','SOURCE_VERSE_CHANGED')]:
            unit=dict(self.units[0]);unit[key]=''
            with self.assertRaisesRegex(ValueError,error):
                translation_coverage(self.index,[self.ledger([unit])])

    def test_wrong_source_hash_and_unknown_identity_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_HASH_MISMATCH'):
            translation_coverage(self.index,[dict(sourceSha256='other',units=self.units)])
        unit=dict(self.units[0]);unit['id']='unknown'
        with self.assertRaisesRegex(ValueError,'UNKNOWN_VERSE'):
            translation_coverage(self.index,[self.ledger([unit])])


class SourceAndFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = ROOT / '.local/test-kjv-archive'
        cls.directory.mkdir(parents=True, exist_ok=True)

    def test_embedded_verse_markers_and_internal_large_gaps_are_not_lost(self):
        with tempfile.TemporaryDirectory(dir=self.directory) as directory:
            source = Path(directory) / 'source.txt'
            source.write_text('First book\n\n1:1 First. 1:2 Second.\n\n\n\n'
                              '2:1 Third.\n\n\n\nOther heading\n\n1:1 Fourth.\n', encoding='utf8')
            result = parse_source(source, ['A', 'B'])
            self.assertEqual(4, result['verseCount'])
            self.assertEqual(['First.', 'Second.', 'Third.'],
                             [v['source'] for v in result['books'][0]['verses']])
            self.assertEqual('Fourth.', result['books'][1]['verses'][0]['source'])
            self.assertIn('Other heading', result['books'][1]['frontmatter'])
            text = source.read_text(encoding='utf8')
            for book in result['books']:
                for verse in book['verses']:
                    self.assertEqual(verse['original'], text[verse['start']:verse['end']])

    def test_missing_or_duplicate_verses_fail_instead_of_becoming_complete(self):
        with tempfile.TemporaryDirectory(dir=self.directory) as directory:
            source = Path(directory) / 'source.txt'
            for content in ['1:1 First. 1:3 Third.', '1:1 First. 1:2 Second. 1:2 Repeated.']:
                source.write_text(content, encoding='utf8')
                with self.assertRaisesRegex(ValueError, 'VERSE_SEQUENCE'):
                    parse_source(source, ['A'])

    def test_frozen_edition_cannot_be_silently_rewritten_or_consolidated(self):
        with tempfile.TemporaryDirectory(dir=self.directory) as directory:
            root = Path(directory)
            file = root / 'book.vay'
            write_new(file, {'text': 'Old form'})
            seal(root, {'book': 'Trial'})
            with self.assertRaises(FileExistsError):
                write_new(file, {'text': 'Modern form'})
            with self.assertRaisesRegex(ValueError, 'NEVER_MODERNIZE'):
                assert_can_consolidate(root)
            file.write_text('Modern form', encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'FROZEN_FILE_CHANGED'):
                verify_seal(root)

    def test_archive_members_cannot_escape_the_edition_folder(self):
        with tempfile.TemporaryDirectory(dir=self.directory) as directory:
            for name in ('../outside', '.', str(Path(directory).parent / 'elsewhere')):
                with self.assertRaisesRegex(ValueError, 'OUTSIDE_ROOT'):
                    safe_member(directory, name)


class HistoricalRegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old, cls.manifest = load_register()
        # These contrasts are against the register's original 0.10 parent.
        base = safe_member(ROOT, cls.manifest['basePackage'])
        cls.modern = EditorialLanguage(base)
        cls.base_manifest = read(base/'manifest.json')

    def test_working_continuation_keeps_parent_and_modern_authorities_separate(self):
        new, manifest = load_register('0.10-kjv.2')
        self.assertIn('INCOMPLETE', manifest['status'])
        self.assertEqual(self.old.lexicon, {k:new.lexicon[k] for k in self.old.lexicon})
        self.assertEqual(self.old.pairs,new.pairs)
        self.assertEqual(self.old.roman,new.roman)
        self.assertEqual(self.old.suffix,new.suffix)
        self.assertNotEqual(new.word('kjv_lot')[0],new.word('kjv_lot_person')[0])
        self.assertEqual(new.word('kjv_havilah')[0],new.word('kjv_havilah_person')[0])
        self.assertNotEqual(new.lexicon['kjv_havilah']['meaning'],new.lexicon['kjv_havilah_person']['meaning'])
        self.assertNotIn('kjv_regret_made',self.modern.lexicon)
        with self.assertRaisesRegex(ValueError,'NOT_UNIQUE'):
            load_register('unregistered-version')

    def test_identity_register_preserves_ancestors_and_distinguishes_perspectives(self):
        parent, _ = load_register('0.10-kjv.2')
        new, manifest = load_register('0.10-kjv.3')
        self.assertIn('INCOMPLETE', manifest['status'])
        self.assertEqual(parent.lexicon, {k:new.lexicon[k] for k in parent.lexicon})
        self.assertEqual(parent.suffix, new.suffix)
        self.assertEqual(parent.pairs, new.pairs)
        self.assertEqual(parent.roman, new.roman)
        self.assertEqual(new.word('ipl')[0], new.word('i:pl')[0])
        self.assertNotEqual(new.word('ipl')[1], new.word('i:pl')[1])
        self.assertEqual('I(pl.self.)', new.word('ipl')[1])
        self.assertEqual('we(sg.whole.)', new.word('wesg')[1])
        self.assertEqual(new.word('we')[0], new.word('wesg')[0])
        self.assertNotEqual(new.word('wesg')[0], new.word('wepl')[0])
        self.assertEqual(new.word('mypl/image')[0], new.word('ipl/image')[0])
        self.assertNotEqual(new.word('mypl/image')[0], new.word('my/image')[0])
        self.assertNotIn('ipl', self.old.lexicon)
        self.assertNotIn('wesg', self.modern.lexicon)
        self.assertNotEqual(new.word('just')[1], new.word('kjv_righteous')[1])

    def test_identity_and_abram_source_bound_fixtures(self):
        new, _ = load_register('0.10-kjv.3')
        for case in read(new.folder/'identity-cases.json'):
            with self.subTest(case=case['id']):
                actual = new.compile(case['analysis'])
                self.assertEqual(case['expectedText'], actual['text'])
                self.assertEqual(case['expectedGloss'], actual['gloss'])
                self.assertNotIn('ipl:pl', case['analysis'])
                self.assertNotIn('ipl:du', case['analysis'])
                self.assertNotIn('wesg:pl', case['analysis'])

    def test_working_continuation_compiler_contrasts(self):
        new, _ = load_register('0.10-kjv.2')
        for name in ['regression-cases.json','historical-cases.json','continuation-cases.json']:
            for case in read(new.folder/name):
                with self.subTest(case=case['id']):
                    if case['expected']=='reject':
                        with self.assertRaises(ValueError):new.compile(case['analysis'])
                    else:
                        actual=new.compile(case['analysis'])
                        self.assertEqual(case['expectedText'],actual['text'])
                        self.assertEqual(case['expectedGloss'],actual['gloss'])

    def test_covenant_continuation_keeps_parent_and_quoted_speakers(self):
        parent, _ = load_register('0.10-kjv.3')
        new, manifest = load_register('0.10-kjv.4')
        self.assertEqual(parent.lexicon, {k:new.lexicon[k] for k in parent.lexicon})
        self.assertEqual(parent.suffix, new.suffix)
        self.assertEqual(parent.pairs, new.pairs)
        self.assertEqual(parent.roman, new.roman)
        cases = {c['id']:c for c in read(new.folder/'covenant-cases.json')}
        self.assertEqual(132, len(cases))
        for case in cases.values():
            with self.subTest(case=case['id']):
                actual = new.compile(case['analysis'])
                self.assertEqual(case['expectedText'], actual['text'])
                self.assertEqual(case['expectedGloss'], actual['gloss'])
                self.assertNotIn('!', actual['text'])
        # Sarah's I remains singular inside the divine speaker's quotation;
        # the following promise resumes the chosen plural-I perspective.
        self.assertNotIn('ipl', cases['genesis-18-13']['analysis'])
        self.assertIn(' i ', cases['genesis-18-13']['analysis'])
        self.assertIn('ipl', cases['genesis-18-14']['analysis'])
        self.assertIn('wepl', cases['genesis-19-2']['analysis'])
        self.assertIn('wesg', cases['genesis-19-13']['analysis'])
        self.assertIn('live:opt:excl', cases['genesis-17-18']['analysis'])
        self.assertIn('escape:opt:excl', cases['genesis-19-20']['analysis'])
        self.assertNotEqual(new.word('kjv_flour')[1], new.word('meal')[1])
        self.assertNotEqual(new.word('kjv_kindness')[1], new.word('kind')[1])
        self.assertNotEqual(new.word('kjv_presence')[1], new.word('before')[1])

    def test_inheritance_register_keeps_quoted_i_and_collective_boundaries(self):
        parent, _ = load_register('0.10-kjv.4')
        new, manifest = load_register('0.10-kjv.5')
        self.assertEqual(parent.lexicon, {k:new.lexicon[k] for k in parent.lexicon})
        self.assertEqual(parent.suffix, new.suffix)
        self.assertEqual(parent.pairs, new.pairs)
        self.assertEqual(parent.roman, new.roman)
        self.assertEqual('data/language/archaic-kjv-4', manifest['basePackage'])
        cases = {c['id']:c for c in read(new.folder/'inheritance-cases.json')}
        self.assertEqual(214, len(cases))
        for case in cases.values():
            with self.subTest(case=case['id']):
                actual = new.compile(case['analysis'])
                self.assertEqual(case['expectedText'], actual['text'])
                self.assertEqual(case['expectedGloss'], actual['gloss'])
                self.assertNotIn('!', actual['text'])
        self.assertIn('iplself:ins ipl swear:perf', cases['genesis-22-16']['analysis'])
        self.assertIn('ipl give:fu', cases['genesis-24-7']['analysis'])
        self.assertIn('i:a take:pa', cases['genesis-24-7']['analysis'])
        self.assertIn('i go:fu', cases['genesis-24-58']['analysis'])
        self.assertNotIn('ipl', cases['genesis-24-58']['analysis'])
        self.assertIn('wesg', cases['genesis-24-57']['analysis'])
        self.assertIn('wepl see:pa', cases['genesis-26-28']['analysis'])
        self.assertIn('wesg say:pa', cases['genesis-26-28']['analysis'])
        self.assertIn('between wepl', cases['genesis-26-28']['analysis'])
        self.assertIn('between wesg and thou', cases['genesis-26-28']['analysis'])
        self.assertIn('wepl find:perf', cases['genesis-26-32']['analysis'])
        self.assertNotEqual(new.word('kjv_envy')[0], new.word('jealousy')[0])
        self.assertNotEqual(new.word('kjv_simpledweller')[0], new.word('kjv_righteous')[0])
        self.assertNotIn('kjv_rightside', new.lexicon)  # Reuse the attested historical direction.
        self.assertIn('kjv_right_side', cases['genesis-24-49']['analysis'])
        self.assertIn('half kjv_shekel', cases['genesis-24-22']['analysis'])
        self.assertIn('thousand:pl of million:pl', cases['genesis-24-60']['analysis'])

    def test_divided_identity_distinguishes_household_i_from_impersonation(self):
        parent, _ = load_register('0.10-kjv.5')
        new, manifest = load_register('0.10-kjv.6')
        self.assertEqual(parent.lexicon, {k:new.lexicon[k] for k in parent.lexicon})
        self.assertEqual(parent.suffix, new.suffix)
        self.assertEqual(parent.pairs, new.pairs)
        self.assertEqual(parent.roman, new.roman)
        self.assertEqual('data/language/archaic-kjv-5', manifest['basePackage'])
        cases = {c['id']:c for c in read(new.folder/'divided-identity-cases.json')}
        self.assertEqual(233, len(cases))
        for case in cases.values():
            with self.subTest(case=case['id']):
                actual = new.compile(case['analysis'])
                self.assertEqual(case['expectedText'], actual['text'])
                self.assertEqual(case['expectedGloss'], actual['gloss'])
                self.assertNotIn('!', actual['text'])
        household = cases['genesis-32-10']['analysis']
        self.assertIn('worthy i be:pr not', household)
        self.assertIn('my/staff', household)
        self.assertIn('i cross:pa', household)
        self.assertIn('two band ipl become:perf', household)
        self.assertIn('kjv_esau i be:pr', cases['genesis-27-19']['analysis'])
        self.assertNotIn('ipl', cases['genesis-27-19']['analysis'])
        self.assertIn('kjv_god ipl be:pr', cases['genesis-31-13']['analysis'])
        self.assertIn('my/kjv_god:pl:a', cases['genesis-31-30']['analysis'])
        self.assertNotIn('ipl', cases['genesis-31-30']['analysis'])
        self.assertIn('wepl make:opt, i and thou', cases['genesis-31-44']['analysis'])
        for ref in ['27-34','27-38','28-17','30-1']:
            self.assertIn(':excl', cases['genesis-'+ref]['analysis'])
        for ref in ['32-26','32-29','32-30']:
            self.assertNotIn('ipl', cases['genesis-'+ref]['analysis'])
        self.assertNotEqual(new.word('kjv_camelcalf')[0], new.word('colt')[0])
        self.assertNotEqual(new.word('kjv_limp')[0], new.word('stop')[0])
        self.assertNotEqual(new.word('kjv_heap')[0], new.word('pile')[0])
        self.assertEqual(4, len({new.word(k)[0] for k in
            ['kjv_speckled','spotted','kjv_ringstraked','kjv_grisled']}))

    def test_corporate_claims_do_not_erase_individual_identity_or_allegations(self):
        parent, _ = load_register('0.10-kjv.6')
        new, manifest = load_register('0.10-kjv.7')
        self.assertEqual(parent.lexicon, {k:new.lexicon[k] for k in parent.lexicon})
        self.assertEqual(parent.suffix, new.suffix)
        self.assertEqual(parent.pairs, new.pairs)
        self.assertEqual(parent.roman, new.roman)
        self.assertEqual('data/language/archaic-kjv-6', manifest['basePackage'])
        cases = {c['id']:c for c in read(new.folder/'corporate-deceit-cases.json')}
        self.assertEqual(189, len(cases))
        for case in cases.values():
            with self.subTest(case=case['id']):
                actual = new.compile(case['analysis'])
                self.assertEqual(case['expectedText'], actual['text'])
                self.assertEqual(case['expectedGloss'], actual['gloss'])
                self.assertNotIn('!', actual['text'])
        self.assertIn('few by kjv_number ipl be:cv', cases['genesis-34-30']['analysis'])
        self.assertIn('i and my/house', cases['genesis-34-30']['analysis'])
        self.assertIn('with deceit', cases['genesis-34-13']['analysis'])
        self.assertIn('one_num people wesg become:fu', cases['genesis-34-16']['analysis'])
        self.assertIn('wesg slay:opt', cases['genesis-37-20']['analysis'])
        self.assertIn('wepl see:fu', cases['genesis-37-20']['analysis'])
        self.assertIn('wepl shame:psv:pr', cases['genesis-38-23']['analysis'])
        self.assertIn('pregnant i be:pr', cases['genesis-38-25']['analysis'])
        self.assertNotIn('ipl', cases['genesis-38-25']['analysis'])
        self.assertIn('kjv_righteous', cases['genesis-38-26']['analysis'])
        self.assertIn('wed:imp', cases['genesis-38-8']['analysis'])
        for ref in ['38-3','38-4','38-5','38-18']:
            self.assertIn('kjv_conceive:pa', cases['genesis-'+ref]['analysis'])
        for ref in ['37-30','38-29']:
            self.assertIn(':excl', cases['genesis-'+ref]['analysis'])
        self.assertNotEqual(new.word('kjv_rend')[0], new.word('tear')[0])
        self.assertNotEqual(new.word('kjv_harlot')[0], new.word('whore')[0])
        self.assertEqual(new.word('kjv_adah')[0], new.word('kjv_adah_esau')[0])
        self.assertNotEqual(new.lexicon['kjv_adah']['meaning'], new.lexicon['kjv_adah_esau']['meaning'])
        self.assertIn('kjv_zibeon daughter', cases['genesis-36-2']['analysis'])
        self.assertIn('his/father', cases['genesis-36-24']['analysis'])
        self.assertIn('mule:pl:a', cases['genesis-36-24']['analysis'])
        self.assertIn('kjv_padanaram:loc', cases['genesis-35-26']['analysis'])
        self.assertIn('kjv_ephrath', cases['genesis-35-19']['analysis'])

    def test_office_self_is_distinct_from_personal_witness_and_collective_liability(self):
        parent, _ = load_register('0.10-kjv.7')
        new, manifest = load_register('0.10-kjv.8')
        self.assertEqual(parent.lexicon, {k:new.lexicon[k] for k in parent.lexicon})
        self.assertEqual(parent.suffix, new.suffix)
        self.assertEqual(parent.pairs, new.pairs)
        self.assertEqual(parent.roman, new.roman)
        self.assertEqual('data/language/archaic-kjv-7', manifest['basePackage'])
        cases = {c['id']:c for c in read(new.folder/'office-self-cases.json')}
        self.assertEqual(209, len(cases))
        for case in cases.values():
            with self.subTest(case=case['id']):
                actual = new.compile(case['analysis'])
                self.assertEqual(case['expectedText'], actual['text'])
                self.assertEqual(case['expectedGloss'], actual['gloss'])
                self.assertNotIn('!', actual['text'])
        self.assertIn('wesg', cases['genesis-39-14']['analysis'])
        self.assertIn(' i cry:pa', cases['genesis-39-14']['analysis'])
        self.assertNotIn('ipl', cases['genesis-41-17']['analysis'])
        self.assertIn('mypl/house', cases['genesis-41-40']['analysis'])
        self.assertIn('kjv_pharaoh ipl be:pr', cases['genesis-41-44']['analysis'])
        self.assertIn('one_num of five equal part:pl', cases['genesis-41-34']['analysis'])
        self.assertIn('thy/head:a of thou', cases['genesis-40-19']['analysis'])
        self.assertIn('restore:fu', cases['genesis-40-13']['analysis'])
        self.assertIn('wesg live:pr:may', cases['genesis-43-8']['analysis'])
        self.assertIn('both wepl and thou', cases['genesis-43-8']['analysis'])
        self.assertIn('five time as much as', cases['genesis-43-34']['analysis'])
        self.assertNotIn('ipl', cases['genesis-44-15']['analysis'])
        self.assertIn('wesg be:pr', cases['genesis-44-16']['analysis'])
        self.assertIn('both wepl and also he', cases['genesis-44-16']['analysis'])
        self.assertIn('in boy/place as slave', cases['genesis-44-33']['analysis'])
        self.assertNotEqual(new.word('kjv_grain_ear')[0], new.word('ear')[0])
        self.assertNotEqual(new.word('kjv_divine')[0], new.word('divine')[0])
        self.assertNotEqual(new.word('kjv_load')[0], new.word('fill')[0])

    def test_descent_self_keeps_biological_persons_and_quoted_roles_distinct(self):
        parent, _ = load_register('0.10-kjv.8')
        new, manifest = load_register('0.10-kjv.9')
        self.assertEqual(parent.lexicon, {k:new.lexicon[k] for k in parent.lexicon})
        self.assertEqual(parent.suffix, new.suffix)
        self.assertEqual(parent.pairs, new.pairs)
        self.assertEqual(parent.roman, new.roman)
        cases = {c['id']:c for c in read(new.folder/'descent-self-cases.json')}
        self.assertEqual(174, len(cases))
        for case in cases.values():
            with self.subTest(case=case['id']):
                actual = new.compile(case['analysis'])
                self.assertEqual(case['expectedText'], actual['text'])
                self.assertEqual(case['expectedGloss'], actual['gloss'])
                self.assertNotIn('!', actual['text'])
        self.assertIn('kjv_joseph i be:pr', cases['genesis-45-3']['analysis'])
        self.assertNotIn('ipl', cases['genesis-45-3']['analysis'])
        self.assertIn('kjv_god ipl be:pr', cases['genesis-46-3']['analysis'])
        self.assertIn('plough:inf', cases['genesis-45-6']['analysis'])
        self.assertIn('both wepl and ourone/land', cases['genesis-47-19']['analysis'])
        self.assertIn('for kjv_pharaoh ipl buy:perf', cases['genesis-47-23']['analysis'])
        self.assertIn('mypl/son:pl', cases['genesis-48-5']['analysis'])
        self.assertIn('my/son:pl', cases['genesis-48-9']['analysis'])
        self.assertIn('kjv_ephraim:a in his/kjv_right_side hand to kjv_israel/left hand', cases['genesis-48-13']['analysis'])
        self.assertIn('his/left hand upon kjv_manasseh/head', cases['genesis-48-14']['analysis'])
        self.assertIn('ipl kjv_divide:fu', cases['genesis-49-7']['analysis'])
        self.assertIn('i wait:perf', cases['genesis-49-18']['analysis'])
        self.assertIn('in kjv_god/place i be:pr?', cases['genesis-50-19']['analysis'])
        self.assertNotIn('ipl', cases['genesis-50-19']['analysis'])
        self.assertIn('kjv_coffin egypt:loc', cases['genesis-50-26']['analysis'])
        self.assertIn('kjv_well', cases['genesis-49-22']['analysis'])
        self.assertEqual(new.word('kjv_hezron')[0], new.word('kjv_hezron_pharez')[0])
        self.assertNotEqual(new.lexicon['kjv_hezron']['meaning'], new.lexicon['kjv_hezron_pharez']['meaning'])
        self.assertNotEqual(new.word('kjv_asscolt')[0], new.word('colt')[0])
        self.assertEqual('data/language/archaic-kjv-8', manifest['basePackage'])

    def test_commission_distinguishes_quoted_name_person_and_collective(self):
        parent, _ = load_register('0.10-kjv.9')
        new, manifest = load_register('0.10-kjv.10')
        self.assertEqual(parent.lexicon, {k:new.lexicon[k] for k in parent.lexicon})
        self.assertEqual(parent.suffix, new.suffix)
        self.assertEqual(parent.possessors, new.possessors)
        self.assertEqual(parent.pairs, new.pairs)
        self.assertEqual(parent.roman, new.roman)
        cases = {c['id']: c for c in read(new.folder/'commission-cases.json')}
        revisions = read(new.folder/'genesis-review-cases.json')
        self.assertEqual(153, len(cases))
        self.assertEqual(51, len(revisions))
        for case in list(cases.values()) + revisions:
            with self.subTest(case=case['id']):
                actual = new.compile(case['analysis'])
                self.assertEqual(case['expectedText'], actual['text'])
                self.assertEqual(case['expectedGloss'], actual['gloss'])
                self.assertNotIn('!', actual['text'])
        self.assertIn('here i be:pr', cases['exodus-3-4']['analysis'])
        self.assertNotIn('ipl', cases['exodus-3-4']['analysis'])
        self.assertIn('ipl be:pr that ipl be:pr', cases['exodus-3-14']['analysis'])
        self.assertIn('kjv_i_am:n i:a', cases['exodus-3-14']['analysis'])
        self.assertEqual(new.word('ipl')[0]+' '+new.word('be:pr')[0], new.lexicon['kjv_i_am']['form'])
        self.assertIn('in place of kjv_god thou be:fu', cases['exodus-4-16']['analysis'])
        self.assertNotIn('ipl', cases['exodus-4-16']['analysis'])
        self.assertIn('his/heart:a hard ipl make:fu', cases['exodus-4-21']['analysis'])
        self.assertIn('mypl/son kjv_israel', cases['exodus-4-22']['analysis'])
        self.assertNotIn('kjv_moses', cases['exodus-4-24']['analysis'])
        self.assertIn('kjv_aaron:n speak:pa', cases['exodus-4-30']['analysis'])
        self.assertIn('hinder:pr', cases['exodus-5-4']['analysis'])
        self.assertIn('kjv_number:ev', cases['exodus-5-8']['analysis'])
        self.assertIn('kjv_jehovah', cases['exodus-6-3']['analysis'])
        self.assertIn('spirit/anguish', cases['exodus-6-9']['analysis'])
        self.assertIn('his/father/sister', cases['exodus-6-20']['analysis'])
        self.assertNotEqual(new.word('kjv_worship')[0], new.word('worship')[0])
        self.assertNotEqual(new.word('kjv_brick_block')[0], new.word('kjv_brick')[0])
        for token,label in [('mypl/son:pl','my(pl.self.)'), ('ourone/kjv_god','our(sg.whole.)')]:
            self.assertEqual(parent.word(token)[0], new.word(token)[0])
            self.assertTrue(new.word(token)[1].startswith(label+'-'))
        for a in read(new.folder/'additions.json'):
            self.assertTrue(set(a['form']) <= new.letters | set('’ -'), a['key'])
            if a['derivationKeys']:
                self.assertEqual(a['form'], ''.join(new.lexicon[k]['form'] for k in a['derivationKeys']))
        self.assertEqual('data/language/archaic-kjv-9', manifest['basePackage'])

    def test_passover_whole_and_plural_self_preserve_parent_register(self):
        parent,_=load_register('0.10-kjv.10')
        new,manifest=load_register('0.10-kjv.11')
        self.assertEqual(parent.lexicon,{k:new.lexicon[k] for k in parent.lexicon})
        self.assertEqual(parent.pairs,new.pairs);self.assertEqual(parent.suffix,new.suffix)
        self.assertEqual(parent.roman,new.roman)
        self.assertEqual('data/language/archaic-kjv-10',manifest['basePackage'])
        cases={c['id']:c for c in read(new.folder/'passover-cases.json')}
        self.assertEqual(len(cases),182)
        for c in cases.values():
            with self.subTest(case=c['id']):
                result=new.compile(c['analysis'])
                self.assertEqual(c['expectedText'],result['text'])
                self.assertEqual(c['expectedGloss'],result['gloss'])
                self.assertNotIn('!',result['text'])
        for field in ('young','old','son:pl','daughter:pl','flock:pl','herd:pl'):
            self.assertIn('ourone/'+field,cases['exodus-10-9']['analysis'])
        self.assertIn('i sin:perf',cases['exodus-10-16']['analysis'])
        self.assertIn('ipl',cases['exodus-12-12']['analysis'])
        self.assertIn('kjv_god:pl',cases['exodus-12-12']['analysis'])
        self.assertIn('ourone/house:pl',cases['exodus-12-27']['analysis'])
        self.assertIn('wepl',cases['exodus-12-33']['analysis'])
        self.assertIn('kjv_three day:pl',cases['exodus-10-22']['analysis'])
        self.assertNotEqual(new.word('kjv_boil_lesion')[1],new.word('boil')[1])
        for a in read(new.folder/'additions.json'):
            self.assertTrue(set(a['form'])<=new.letters|set('’ -'),a['key'])
            if a['derivationKeys']:self.assertEqual(a['form'],''.join(new.lexicon[k]['form'] for k in a['derivationKeys']))

    def test_departure_chorus_pair_and_rations_preserve_historical_state(self):
        parent,_=load_register('0.10-kjv.11')
        new,manifest=load_register('0.10-kjv.12')
        self.assertEqual(parent.lexicon,{k:new.lexicon[k] for k in parent.lexicon})
        for attr in ('pairs','suffix','roman','possessors'):
            self.assertEqual(getattr(parent,attr),getattr(new,attr))
        self.assertEqual('data/language/archaic-kjv-11',manifest['basePackage'])
        cases={c['id']:c for c in read(new.folder/'departure-cases.json')}
        self.assertEqual(159,len(cases))
        for c in cases.values():
            with self.subTest(case=c['id']):
                result=new.compile(c['analysis'])
                self.assertEqual(c['expectedText'],result['text'])
                self.assertEqual(c['expectedGloss'],result['gloss'])
                self.assertNotIn('!',result['text'])
        checks={
            'exodus-13-8':['ipl come:pa'],
            'exodus-13-15':['wesg','i offer:pr','i redeem:pr'],
            'exodus-14-25':['wheel:pl:a take:pa off','wepl'],
            'exodus-15-1':['ipl sing:fu'],
            'exodus-15-9':['enemy:n say:pa: ipl','mypl/lust'],
            'exodus-15-11':['kjv_god:pl','kjv_wonder:pl:a'],
            'exodus-15-18':[':excl'],
            'exodus-16-7':['we:du'],
            'exodus-16-16':['kjv_number:ev','one_num kjv_omer'],
            'exodus-16-22':['two kjv_omer:pl for one_num man'],
            'exodus-16-36':['of kjv_ephah_measure ten:ord part one_num kjv_omer'],
            'exodus-17-9':['for wesg','my/hand i stand:fu'],
            'exodus-18-22':['great kjv_judicial_matter'],
            'exodus-18-23':['kjv_god:n thou:a command:pr'],
            'exodus-18-26':['hard kjv_judicial_matter'],
        }
        for ref,parts in checks.items():
            for part in parts:self.assertIn(part,cases[ref]['analysis'])
        self.assertNotEqual(new.lexicon['kjv_ephah']['pos'],new.lexicon['kjv_ephah_measure']['pos'])
        self.assertEqual(new.word('kjv_eliezer')[0],new.word('kjv_eliezer_moses')[0])
        self.assertNotEqual(new.word('kjv_travail')[0],new.word('kjv_travail_hardship')[0])
        for a in read(new.folder/'additions.json'):
            self.assertTrue(set(a['form'])<=new.letters|set('’ -'),a['key'])
            if a['derivationKeys']:self.assertEqual(a['form'],''.join(new.lexicon[k]['form'] for k in a['derivationKeys']))

    def test_historical_words_do_not_promote_or_replace_modern_words(self):
        self.assertEqual('0.10', self.base_manifest['version'])
        self.assertEqual('venik', self.modern.word('three')[0])
        self.assertEqual('tren', self.old.word('kjv_three')[0])
        self.assertEqual('tatus’t', self.old.word('kjv_second')[0])
        self.assertEqual(self.modern.lexicon, {k: self.old.lexicon[k] for k in self.modern.lexicon})
        self.assertNotIn('kjv_god', self.modern.lexicon)
        self.assertEqual('never-modernize', self.manifest['policy'])

    def test_inherited_and_historical_contrasts(self):
        for filename in ('regression-cases.json', 'historical-cases.json'):
            for case in read(PACKAGE / filename):
                with self.subTest(case=case['id']):
                    if case['expected'] == 'reject':
                        with self.assertRaisesRegex(ValueError, case['error']):
                            self.old.compile(case['analysis'])
                    else:
                        actual = self.old.compile(case['analysis'])
                        self.assertEqual(case['expectedText'], actual['text'])
                        self.assertEqual(case['expectedGloss'], actual['gloss'])

    def test_senses_that_would_mistranslate_jonah_are_separate(self):
        for old, misleading in [('kjv_relent', 'repent'), ('kjv_calamity', 'wickedness'),
                                ('kjv_fast', 'fast'), ('kjv_row', 'row'),
                                ('kjv_right_side', 'right'), ('kjv_fish', 'whale'),
                                ('kjv_god', 'kjv_lord'), ('wepl', 'we')]:
            self.assertNotEqual(self.old.word(old)[0], self.old.word(misleading)[0])
        self.assertEqual(self.old.word('fish')[0], self.old.word('kjv_fish')[0])
        self.assertNotEqual(self.old.lexicon['fish']['pos'], self.old.lexicon['kjv_fish']['pos'])

    def test_no_random_forms_or_unicode_case_conversion(self):
        for addition in read(PACKAGE / 'additions.json'):
            self.assertTrue(set(addition['form']) <= self.old.letters | set('’ -'))
            if addition['derivationKeys']:
                self.assertEqual(addition['form'], ''.join(self.old.lexicon[k]['form']
                                                          for k in addition['derivationKeys']))
        result = self.old.compile('kjv_jonah cry:pr.', initial=False)
        self.assertTrue(result['text'].startswith('Jonah'))
        self.assertEqual('Tren', self.old.compile('kjv_three')['text'])


if __name__ == '__main__':
    unittest.main()
