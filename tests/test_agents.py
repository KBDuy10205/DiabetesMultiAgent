import pytest
from agents.coordinator import CoordinatorAgent
from agents.knowledge import KnowledgeAgent
from agents.prediction import FEATURES, PredictionAgent
from agents.reasoning import ReasoningAgent
from agents.retrieval import RetrievalAgent
from agents.rule import RuleAgent
from agents.validation import ValidationAgent
from rag.core import ABSTAIN


def test_coordinator_routes_without_guessing():
    agent = CoordinatorAgent()
    assert agent.run({'question': 'abc'})['tasks'] == ['retrieval', 'knowledge']
    assert agent.run({'features': {}, 'measurement': {}})['tasks'] == ['prediction', 'rule']
    with pytest.raises(ValueError): agent.run({'tasks': ['prediction']})
    with pytest.raises(ValueError): agent.run({'question': 'abc', 'generate_answer': True, 'tasks': ['knowledge']})


def test_prediction_agent_independent():
    class Model:
        classes_ = [0, 1]
        def predict_proba(self, frame): return [[0.7, 0.3]]
        def predict(self, frame): return [0]
    agent = PredictionAgent(loader=lambda _: Model())
    assert agent.run({feature: 1 for feature in FEATURES})['probability'] == 0.3
    with pytest.raises(ValueError): agent.run({'Age': 10})
    with pytest.raises(ValueError): agent.run({**{f: 1 for f in FEATURES}, 'Age': True})


def test_rule_agent_preserves_alerts_and_missing():
    result = RuleAgent().run({'test_type': 'fpg', 'unit': 'mg/dL', 'value': 53})
    assert result['alerts'][0]['rule_id'] == 'glucose_below_54'
    assert result['issues'] and not result['results']


class Driver:
    def __init__(self): self.closed = False
    def close(self): self.closed = True


def test_retrieval_agent_and_cleanup():
    driver = Driver()
    agent = RetrievalAgent(search=lambda d, db, m, q, k: [{'chunk_id': 'x'}], model_factory=lambda: 'model', connection_factory=lambda: (driver, 'db'))
    assert agent.run('test')['results'][0]['chunk_id'] == 'x'
    assert driver.closed
    with pytest.raises(ValueError): agent.run(' ')


def test_knowledge_agent_independent():
    driver = Driver()
    agent = KnowledgeAgent(connection_factory=lambda: (driver, 'db'), entity_loader=lambda: [{'id': 'x', 'aliases': ['insulin']}], mention_search=lambda *a: [{'chunk_id': 'c'}], assertion_search=lambda *a: [])
    result = agent.run('Insulin')
    assert result['entity_ids'] == ['x'] and result['mentions'][0]['chunk_id'] == 'c'
    assert driver.closed
    assert agent.run('no match')['entity_ids'] == []


def test_reasoning_agent_absence_and_configured():
    assert ReasoningAgent().run('q', [])['status'] == 'insufficient_evidence'
    agent = ReasoningAgent(endpoint='http://example.test', model='fake', answer_fn=lambda *a: 'Thông tin [S1]')
    assert agent.run('q', [{'text': 'source'}])['text'] == 'Thông tin [S1]'


def test_validation_agent_checks_citations_and_definitive_claim():
    agent = ValidationAgent()
    evidence = [{'chunk_id': 'c', 'source_id': 's', 'text': 'evidence'}]
    assert agent.run({'text': 'Dữ liệu [S1]'}, evidence)['valid']
    assert agent.run({'text': 'Dữ liệu [S2]'}, evidence)['text'] == ABSTAIN
    assert not agent.run({'text': 'Chắc chắn mắc bệnh [S1]'}, evidence)['valid']
    assert agent.run({'text': ABSTAIN}, [])['valid']
