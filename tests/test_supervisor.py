import logging
import time
import pytest
from agents.supervisor import SharedState, Supervisor


class SlowAgent:
    def run(self, value):
        time.sleep(5)
        return {'private': value}


class ErrorAgent:
    def run(self, value):
        raise ValueError('SECRET_HEALTH_DATA')


class FakeSupervisor(Supervisor):
    def __init__(self, responses, **kwargs):
        super().__init__(**kwargs)
        self.responses = responses
        self.visited = []

    def _call(self, state, name, *args):
        if state.calls >= self.max_calls:
            return {'status': 'limit'}
        state.calls += 1
        self.visited.append(name)
        return self.responses.get(name, {'status': 'error'})


def test_risk_runs_rule_before_prediction():
    rules = {'status': 'ok', 'data': {'alerts': [], 'issues': [], 'results': []}}
    agent = FakeSupervisor({'rule': rules, 'prediction': {'status': 'ok', 'data': {'label': 0}}})
    output = agent.run({'intent':'risk', 'measurement': {'test_type':'glucose_meter'}, 'features': {}})
    assert agent.visited == ['rule', 'prediction']
    assert output['safety'] == 'passed_limited' and output['calls'] == 2


@pytest.mark.parametrize('rules', [
    {'status':'ok', 'data': {'alerts':[{'message':'alert'}], 'issues':[], 'results':[]}},
    {'status':'ok', 'data': {'alerts':[], 'issues':[{'code':'missing_field'}], 'results':[]}},
    {'status':'ok', 'data': {}}, {'status':'timeout'},
])
def test_safety_blocks_prediction(rules):
    agent = FakeSupervisor({'rule': rules})
    result = agent.run({'features': {}, 'measurement': {}})
    assert result['safety'] == 'blocked'
    assert result['agents']['prediction']['status'] == 'blocked_by_safety'
    assert agent.visited == ['rule']


def test_missing_measurement_and_intent_validation():
    agent = FakeSupervisor({})
    result = agent.run({'features': {}})
    assert result['safety'] == 'blocked_missing_measurement' and not agent.visited
    with pytest.raises(ValueError): agent.run({'intent':'knowledge', 'question':'q', 'measurement':{}})
    with pytest.raises(ValueError): agent.run({'intent':'risk', 'question':'q', 'features':{}})


def test_hba1c_alone_cannot_clear_glucose_safety_gate():
    rules = {'status': 'ok', 'data': {'alerts': [], 'issues': [], 'results': []}}
    agent = FakeSupervisor({'rule': rules})
    result = agent.run({'features': {}, 'measurement': {'test_type': 'hba1c'}})
    assert result['safety'] == 'blocked_missing_glucose'
    assert result['agents']['prediction']['status'] == 'blocked_by_safety'


def test_knowledge_and_explanation_are_routed_separately():
    agent = FakeSupervisor({'retrieval': {'status':'ok', 'data':{'results':[]}}, 'knowledge': {'status':'ok', 'data':{'mentions':[]}}})
    result = agent.run({'question':'q'})
    assert result['intent'] == 'knowledge' and agent.visited == ['retrieval', 'knowledge']
    other = FakeSupervisor({'rule': {'status':'ok', 'data':{'issues':[], 'alerts':[], 'results':[]}}, 'retrieval': {'status':'ok', 'data':{'results':[]}}, 'knowledge': {'status':'ok', 'data':{'mentions':[]}}})
    assert other.run({'question':'q', 'measurement':{}})['intent'] == 'explanation'
    assert other.visited == ['rule', 'retrieval', 'knowledge']


def test_call_budget_stops_execution():
    agent = FakeSupervisor({'retrieval': {'status':'ok', 'data':{'results':[]}}}, max_calls=1)
    result = agent.run({'question':'q'})
    assert result['calls'] == 1 and result['agents']['knowledge']['status'] == 'limit'


def test_validation_unavailable_abstains():
    a = FakeSupervisor({'retrieval': {'status':'ok', 'data':{'results':[]}}, 'knowledge': {'status':'ok', 'data':{'mentions':[]}}, 'reasoning': {'status':'ok', 'data':{'text':'x', 'status':'draft'}}}, max_calls=3)
    result = a.run({'question':'q', 'generate_answer':True})
    assert not result['answer']['valid'] and result['answer']['issues'] == ['validation_unavailable']


def test_hard_timeout_and_no_sensitive_log(caplog):
    logger = logging.getLogger('supervisor.test')
    caplog.set_level(logging.INFO, logger='supervisor.test')
    supervisor = Supervisor(agents={'rule': SlowAgent()}, timeout_seconds=1, logger=logger)
    state = SharedState(intent='risk', request={'measurement':'SECRET_HEALTH_DATA'})
    start = time.monotonic()
    result = supervisor._call(state, 'rule', 'SECRET_HEALTH_DATA')
    assert result['status'] == 'timeout' and time.monotonic() - start < 4
    assert 'SECRET_HEALTH_DATA' not in caplog.text


def test_exception_redacted(caplog):
    logger = logging.getLogger('supervisor.test')
    caplog.set_level(logging.INFO, logger='supervisor.test')
    supervisor = Supervisor(agents={'rule': ErrorAgent()}, timeout_seconds=5, logger=logger)
    state = SharedState(intent='risk', request={})
    assert supervisor._call(state, 'rule', 'SECRET_HEALTH_DATA') == {'status': 'error'}
    assert 'SECRET_HEALTH_DATA' not in caplog.text
