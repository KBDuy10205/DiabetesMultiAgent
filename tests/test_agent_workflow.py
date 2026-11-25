from agents.workflow import AgentWorkflow


class Stub:
    def __init__(self, result=None, error=None): self.result, self.error = result, error
    def run(self, *args):
        if self.error: raise self.error
        return self.result


def test_workflow_combines_results_and_preserves_alerts():
    chunk = {'chunk_id': 'c', 'source_id': 's', 'text': 'evidence'}
    rule = {'alerts': [{'rule_id': 'glucose_below_54', 'message': 'Cảnh báo an toàn'}], 'results': [], 'issues': [{'code': 'missing_field'}]}
    flow = AgentWorkflow(rule=Stub(rule), retrieval=Stub({'results': [chunk]}), knowledge=Stub({'mentions': [chunk]}), reasoning=Stub({'text': 'Cảnh báo an toàn. Nội dung [S1]', 'status': 'draft'}))
    result = flow.run({'question': 'q', 'measurement': {}, 'generate_answer': True})
    assert result['agents']['rule']['data'] == rule
    assert result['evidence'][0]['channels'] == ['vector', 'kg']
    assert result['answer']['valid'] is True


def test_partial_failure_does_not_erase_alert():
    flow = AgentWorkflow(rule=Stub({'alerts': [{'rule_id': 'glucose_below_54'}]}), prediction=Stub(error=RuntimeError('private data')))
    result = flow.run({'measurement': {}, 'features': {}})
    assert result['agents']['rule']['data']['alerts']
    assert result['agents']['prediction'] == {'status': 'error', 'error_type': 'RuntimeError'}


def test_rule_prediction_difference_not_automatically_diagnosis():
    from agents.validation import ValidationAgent
    result = ValidationAgent().run({'text': 'Kết quả [S1]'}, [{'source_id':'s', 'chunk_id':'c', 'text':'x'}], {'label': 0}, {'results':[{'rule_id': 'fpg_at_least_126'}]})
    assert result['warnings'] == ['ml_label_and_lab_threshold_differ_do_not_infer_diagnosis']


def test_missing_safety_alert_rejects_draft():
    from agents.validation import ValidationAgent
    result = ValidationAgent().run({'text': 'Kết quả [S1]'}, [{'source_id':'s', 'chunk_id':'c', 'text':'x'}], rule={'alerts': [{'message': 'Cảnh báo an toàn'}]})
    assert not result['valid']
    assert 'safety_alert_missing_or_modified' in result['issues']
