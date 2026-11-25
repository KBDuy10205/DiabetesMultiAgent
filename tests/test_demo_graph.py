import pytest
from kb_pipeline.demo_graph import validate


def test_demo_records_are_traceable():
    row = {'id': 'x', 'disease_id': 'd', 'concept_id': 'c', 'concept_name': 'real', 'relation': 'HAS_POSSIBLE_SYMPTOM', 'chunk_id': 'ch', 'source_id': 's', 'evidence_quote': 'real quote', 'review_status': 'demo_unreviewed', 'demo': True}
    chunk = {'id': 'ch', 'source_id': 's', 'text': 'a real quote here'}
    entities = [{'id': 'd', 'label': 'Disease'}]
    validate([row], [chunk], entities)
    with pytest.raises(ValueError):
        validate([{**row, 'evidence_quote': 'invented'}], [chunk], entities)
    with pytest.raises(ValueError):
        validate([{**row, 'review_status': 'accepted_for_demo'}], [chunk], entities)
    with pytest.raises(ValueError):
        validate([row, row], [chunk], entities)
