"""Exact source coverage: prologues and dedications are not metadata."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tools import shakespeare_project as project

class ShakespeareSourceTests(unittest.TestCase):
    def test_dramatic_spellings_and_repeated_invocations(self):
        source = 'Jesu, Jesus, Jeshu, Cheshu!'
        project.check_shakespeare_name(source, 'YeÛça ' * 4, 'Yeshūa ' * 4)
        for native, gloss in [('YeÛça ' * 3, 'Yeshūa ' * 4), ('Jesus', 'Yeshūa'), ('YeÛça', 'Jesu')]:
            with self.assertRaises(ValueError):
                project.check_shakespeare_name(source, native, gloss)

    def test_sealed_names_reach_all_bearers_without_merging_them(self):
        base = project.ROOT / 'data/language/later-dramatic-0.13'
        delta = dict(entries={}, glosses={}, decisions=[])
        with tempfile.TemporaryDirectory(dir=project.ROOT/'.local') as tmp:
            target = Path(tmp)
            old = project.write_working_language(base, delta, target)
            self.assertEqual(old.lexicon['kjv_jesus_matthew']['form'], 'jesus')
            current = project.write_working_language(base, dict(delta, sealedBible=project.SEALED_BIBLE), target)
            witness = project.read(project.ROOT/project.SEALED_BIBLE['package']/'name-forms.json')
            self.assertEqual(len({current.lexicon[k]['semanticId'] for k in witness}), 5)
            self.assertEqual(current.compile('kjv_mary_jesus')['gloss'], 'Mary')
            self.assertEqual(current.compile('kjv_joses_jesus_brother')['gloss'], 'Joses')
            for key, record in witness.items():
                with self.subTest(key=key):
                    self.assertEqual(current.lexicon[key]['semanticId'], record['semanticId'])
                    self.assertEqual(current.lexicon[key]['form'], record['after'])
                    self.assertEqual(current.lexicon[key]['roman'], record['afterRoman'])
                    expected = 'Baryeshūa' if key == 'kjv_barjesus_acts' else 'Yeshūa'
                    result = current.compile(key)
                    self.assertEqual(current.reading(result['text']), expected)
                    self.assertEqual(result['gloss'], expected)

    def test_reviewed_bible_names_follow_referents_across_registers(self):
        base = project.ROOT / 'data/language/later-dramatic-0.13'
        delta = dict(entries={}, glosses={}, decisions=[], sealedBible=project.SEALED_BIBLE, inheritReviewedBibleNames=True)
        with tempfile.TemporaryDirectory(dir=project.ROOT/'.local') as tmp:
            lang = project.write_working_language(base, delta, Path(tmp))
            for key, reading in [('kjv_paul_acts', 'Pāvol'), ('kjv_abraham', 'Avrāham'), ('kjv_peter_disciple', 'Pētar'), ('kjv_jephthah', 'Yefŧhah')]:
                self.assertEqual(lang.reading(lang.compile(key)['text']), reading)
            self.assertEqual(lang.compile('kjv_paul_acts')['gloss'], 'Paul')
            self.assertEqual(lang.lexicon['peter']['meaning'], "Peter, Quince's given name")
            self.assertEqual(lang.lexicon['peter']['form'], 'peter')

    def test_inherited_vocabulary_corrects_omega_and_preserves_later_native_developments(self):
        base = project.ROOT/'data/language/later-dramatic-0.13'
        delta = dict(entries={},glosses={},decisions=[],sealedBible=project.SEALED_BIBLE,
                     inheritReviewedBibleNames=True,inheritReviewedBibleVocabulary=True,normalizeStoredRomanSlots=True)
        with tempfile.TemporaryDirectory(dir=project.ROOT/'.local') as tmp:
            lang = project.write_working_language(base,delta,Path(tmp))
            self.assertEqual(lang.lexicon['kjv_omega_letter_revelation']['roman'], 'hüŧh’na īvden')
            self.assertEqual(lang.lexicon['last']['roman'], 'hüŧh’na')
            self.assertEqual(lang.lexicon['ghost']['form'], project.read(base/'lexicon.json')['entries']['ghost']['form'])

    def test_endin_guard_catches_inflections_and_preserves_distinct_senses(self):
        from tools.shakespeare_endin import check_clean,correction
        from types import SimpleNamespace
        old=SimpleNamespace(lexicon={'last':dict(pos='adjective',form='endin')})
        with self.assertRaises(ValueError):
            check_clean(dict(keys=['last'],analysis='last:m',text='Zem’endinmū'),old)
        clean=SimpleNamespace(lexicon={})
        for analysis,text in [('{{endinmu}}','Endinmu'),('drama_native_last:neg:prog','native')]:
            with self.subTest(analysis=analysis), self.assertRaises(ValueError):
                check_clean(dict(keys=[],analysis=analysis,text=text),clean)
        for slug,uid,analysis,expected in [('hamlet','00147a','last:pr:neg','endure:pr:neg'),
                ('allswell','0617','last+night','former+night'),('lucrece','00193','at last thus','finally thus'),
                ('cymbeline','00407a','to last end','to last end')]:
            self.assertEqual(correction(slug,dict(id=uid,analysis=analysis))[0],expected)

    def parse(self,slug,body):
        sandbox=project.ROOT/'.local/test-shakespeare-sources';sandbox.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=sandbox) as tmp:
            assert Path(tmp).resolve().is_relative_to(sandbox.resolve())
            root=Path(tmp);p=root/(slug+'_TXT_FolgerShakespeare.txt')
            p.write_text('Test work\nCreated on today\n\n'+body,encoding='utf-8')
            with patch.object(project,'ROOT',root):return project.source_units(p)

    def test_prologue_is_retained_and_decorative_rules_are_excluded(self):
        parsed=self.parse('test-play','Characters in the Play\nA\nB\n\n\nPROLOGUE\nSpeech.\n\n=====\nACT 1\nScene 1\n[Enter A.]\n\nA First speech.\n')
        text='\n'.join(u['rawSource'] for u in parsed['units'])
        self.assertTrue(text.startswith('PROLOGUE\nSpeech.'))
        self.assertIn('[Enter A.]',text);self.assertNotIn('=====',text)
        nums=[n for u in parsed['units'] for n in u['lineNumbers']]
        self.assertEqual(len(nums),len(set(nums)))
        self.assertTrue(set(nums).isdisjoint(parsed['excludedLineNumbers']))

    def test_poetry_dedication_epigraph_and_signature_are_retained(self):
        parsed=self.parse('lucrece','To the patron\n\nAuthorial dedication.\n\nLatin epigraph.\n\nArgument\nArgument body.\n\nPoem stanza.\n\nWilliam Shakespeare\n')
        self.assertEqual('To the patron',parsed['units'][0]['source'])
        self.assertEqual('William Shakespeare',parsed['units'][-1]['source'])
        self.assertEqual(7,parsed['sourceBodyNonblankLines'])

    def test_troilus_quarto_address_precedes_armored_prologue(self):
        address = 'A never writer to an ever reader: news.'
        parsed = self.parse('troilus-and-cressida', 'Characters in the Play\nTROILUS\n\n'
                            + address + '\n\nEternal reader. Vale.\n\n\n[Enter the Prologue in armor.]\n')
        self.assertEqual([unit['source'] for unit in parsed['units']],
                         [address, 'Eternal reader. Vale.', '[Enter the Prologue in armor.]'])

    def test_authored_split_requires_exact_nondoubled_source_coverage(self):
        source={'units':[dict(id='00001',lineNumbers=[10,11,12],rawSource='First\nSecond\nThird',source='First Second Third')]}
        a=[dict(id='00001a',sourceId='00001',sourceLines=[10,11])]
        rows,complete,lines=project.authored_source_rows(source,a)
        self.assertEqual((0,2),(complete,lines));self.assertEqual('First Second',rows[0][0]['source'])
        b=dict(id='00001b',sourceId='00001',sourceLines=[12])
        self.assertEqual((1,3),project.authored_source_rows(source,a+[b])[1:])
        for numbers in ([11,12],[10],[10,12]):
            with self.assertRaises(AssertionError):
                project.authored_source_rows(source,a+[dict(b,sourceLines=numbers)])

    def test_numeric_review_rejects_twenty_silently_becoming_two_dozens(self):
        row=dict(id='quantity-test',analysis='unta_amount',numericReview=[dict(
            text='score',key='unta_amount',value='20',decision='A score of soldiers is exactly twenty.')])
        project.validate_numeric_review('a score of soldiers',row,{'unta_amount':{'numericValue':'20'}})
        with self.assertRaises(AssertionError):
            project.validate_numeric_review('a score of soldiers',row,{'unta_amount':{'numericValue':'24'}})
        # Same spelling can instead be an account/debt, with an explicit contextual decision.
        project.validate_numeric_review('pay the score',dict(id='debt-test',analysis='debt',
            numericReview=[dict(text='score',decision='This score is a debt, not twenty.')]),{})

    def test_sentence_slices_cover_original_prose_even_inside_one_source_line(self):
        raw='First sentence. Second\nsentence. Third sentence.'
        source={'units':[dict(id='00001',lineNumbers=[10,11],rawSource=raw,source=raw.replace('\n',' '))]}
        a=dict(id='a',sourceId='00001',sourceOffsets=[0,16])
        b=dict(id='b',sourceId='00001',sourceOffsets=[16,len(raw)])
        rows,complete,lines=project.authored_source_rows(source,[a,b])
        self.assertEqual(raw,''.join(u['rawSource'] for u,_ in rows))
        self.assertEqual((1,2),(complete,lines))
        self.assertEqual((0,0),project.authored_source_rows(source,[a])[1:])
        for span in ([15,len(raw)],[17,len(raw)],[0,len(raw)]):
            with self.assertRaises(AssertionError):project.authored_source_rows(source,[a,dict(b,sourceOffsets=span)])
        with self.assertRaisesRegex(AssertionError,'SOURCE_TOKEN_SPLIT'):
            project.authored_source_rows(source,[dict(a,sourceOffsets=[0,3])])

    def test_source_digits_and_words_require_matching_unta_notation(self):
        for text,notation in [('third','words'),('3rd','digits')]:
            row=dict(id='notation',analysis='quantity',numericReview=[dict(text=text,key='quantity',
                value='3',decision='Third in order, preserving the source notation.')])
            project.validate_numeric_review(text,row,{'quantity':dict(numericValue='3',numericNotation=notation)})
            opposite='digits' if notation=='words' else 'words'
            with self.assertRaisesRegex(AssertionError,'SOURCE_NUMBER_NOTATION_MISMATCH'):
                project.validate_numeric_review(text,row,{'quantity':dict(numericValue='3',numericNotation=opposite)})

    def test_reject_historical_three_and_a_digit_key_disguised_as_a_word(self):
        word = project.semantic_key(3, 'ordinal')
        digits = project.semantic_key(3, 'ordinal', notation='digits')
        note = dict(text='third', key=word, value='3', decision='Written ordinal.')
        row = dict(id='night-watch', analysis=word, numericReview=[note])
        lexicon = {word: dict(numericValue='3', numericNotation='words')}
        project.validate_numeric_review('the third night', row, lexicon)
        with self.assertRaisesRegex(AssertionError, 'UNUSED_QUANTITY_KEY'):
            project.validate_numeric_review('the third night', dict(row, analysis=digits), lexicon)
        with self.assertRaisesRegex(ValueError, 'Unta form for three'):
            project.validate_numeric_review('the third night', dict(row, analysis='kjv_three:ord'), lexicon)

    def test_large_forge_reviews_preserve_all_records_in_bounded_sections(self):
        from tools.shakespeare_checkpoint import review_sections
        units=[dict(id=str(i),source='source '*100,backTranslation='translation '*100,
                    review='review '*100,numericReview=[dict(text='third',value='3')],
                    semanticQuantityReview=[dict(text='moiety',value='1/2')],
                    research=['https://example.org/source']) for i in range(30)]
        sections=review_sections(units)
        self.assertGreater(len(sections),1)
        self.assertEqual([u['id'] for u in units],[uid for section in sections for uid,_ in section])
        for section in sections:
            self.assertLessEqual(len('\n\n'.join(text for _,text in section)),18000)
            for _,text in section:
                self.assertIn('Numeric decisions:',text);self.assertIn('https://example.org/source',text)
                self.assertIn('Additional quantitative senses:',text);self.assertIn('moiety',text)
        with self.assertRaisesRegex(ValueError,'REVIEW_UNIT_TOO_LONG'):
            review_sections([dict(units[0],review='x'*18001)])

    def test_additional_quantity_senses_preserve_value_and_source_notation(self):
        row=dict(id='moiety',analysis='unta_half',semanticQuantityReview=[dict(
            text='moiety',key='unta_half',value='1/2',decision='Half the world, expressed in source-matching Unta words.')])
        entry=dict(numericValue='1/2',numericNotation='words')
        project.validate_numeric_review('A moiety of the world.',row,{'unta_half':entry})
        for wrong,code in [(dict(entry,numericValue='1/3'),'QUANTITY_VALUE_MISMATCH'),
                           (dict(entry,numericNotation='digits'),'SOURCE_NUMBER_NOTATION_MISMATCH')]:
            with self.assertRaisesRegex(AssertionError,code):
                project.validate_numeric_review('A moiety of the world.',row,{'unta_half':wrong})
        with self.assertRaisesRegex(AssertionError,'SEMANTIC_QUANTITY_NOT_IN_SOURCE'):
            project.validate_numeric_review('A share of the world.',row,{'unta_half':entry})

    def test_reviewed_regnal_figure_uses_digits_without_reinterpreting_pronouns(self):
        note=dict(text='Henry V',sourceNotation='roman-regnal',key='unta_five',value='5',
                  decision='The printed stage designation gives his regnal number.')
        row=dict(id='new-king',analysis='unta_five',semanticQuantityReview=[note])
        lex={'unta_five':dict(numericValue='5',numericNotation='digits')}
        project.validate_numeric_review('[Enter the Prince, as Henry V, and Blunt.]',row,lex)
        with self.assertRaisesRegex(AssertionError,'SOURCE_NUMBER_NOTATION_MISMATCH'):
            project.validate_numeric_review('Henry V',row,{'unta_five':dict(lex['unta_five'],numericNotation='words')})
        with self.assertRaisesRegex(AssertionError,'REGNAL_FIGURE_VALUE_MISMATCH'):
            project.source_number_notation('Henry IV',dict(note,text='Henry IV'))
        with self.assertRaisesRegex(AssertionError,'INVALID_REGNAL_FIGURE'):
            project.source_number_notation('I am here.',dict(note,text='I',value='1'))
        self.assertEqual(project.source_number_notation('Henry the Fifth',dict(text='Fifth')),'words')

if __name__=='__main__':unittest.main()
