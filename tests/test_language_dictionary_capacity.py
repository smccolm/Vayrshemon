"""A second play must survive Forge and native language serialization intact."""
import uuid
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator,ValidationError
from vayrshemon import language
from vayrshemon.language_contracts import DATA,REVISION,COLLECTION_LIMITS
from vayrshemon.forge import ForgeProject,empty_snapshot

def entry(i):
    return dict(id=f'entry.{i}',label=f'Word {i}',status='draft',citations=[],notes='',headword=f'word{i}',orthographyId=None,pronunciation='',ipa='',partOfSpeech='noun',senses=[dict(id=f'sense.{i}',definition=f'Meaning {i}',status='draft',citations=[])],variants=[],etymology='',exampleIds=[],audioLinks=[])

class DictionaryCapacityTests(unittest.TestCase):
    def test_large_dictionary_survives_revision_and_forge_restore(self):
        snapshot=empty_snapshot();snapshot['language']['lexicon']=sorted([entry(i) for i in range(2655)],key=lambda e:e['id'])
        state=language.initial();language.append_revision(state,snapshot['language'],'Second play')
        language.validate_state(state)
        self.assertEqual(language.dataset(state),snapshot['language'])
        root=Path(__file__).resolve().parents[1]/'.local/test-dictionary-capacity'/uuid.uuid4().hex
        root.mkdir(parents=True)
        project=ForgeProject.create(root/'source.vayforge','Capacity')
        project.replace_draft(snapshot,project.status()['generation']);project.commit('Second play',project.status()['generation'])
        project.export(root/'edition.json');restored=ForgeProject.restore(root/'edition.json',root/'copy.vayforge')
        self.assertEqual(restored.read()['snapshot'],snapshot)
        self.assertEqual(restored.status()['head'],project.status()['head'])

    def test_capacity_is_bounded_in_data_and_revision_references(self):
        limit=COLLECTION_LIMITS['lexicon'];schema=DATA['properties']['lexicon']
        self.assertEqual(REVISION['properties']['collections']['properties']['lexicon']['maxItems'],limit)
        with self.assertRaises(ValidationError):Draft202012Validator(schema).validate([entry(0)]*(limit+1))
        self.assertEqual(DATA['properties']['morphology']['maxItems'],2000)

if __name__=='__main__':unittest.main()
