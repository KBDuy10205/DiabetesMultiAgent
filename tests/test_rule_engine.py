import math
import pytest
from rule_engine.engine import evaluate, load_rules


def measurement(test, value, **changes):
    defaults = {
        'hba1c': {'unit': '%', 'pregnant': False, 'lab_certified': True, 'a1c_interference': False},
        'fpg': {'unit': 'mg/dL', 'pregnant': False, 'sample': 'plasma', 'fasting_hours': 8},
        'ogtt_2h': {'unit': 'mg/dL', 'pregnant': False, 'sample': 'plasma', 'glucose_load_g': 75, 'elapsed_minutes': 120},
        'glucose_meter': {'unit': 'mg/dL'},
    }
    return {'test_type': test, 'value': value, **defaults[test], **changes}


@pytest.mark.parametrize('test,value,expected', [
    ('hba1c', 5.69, 'a1c_below_5_7'), ('hba1c', 5.7, 'a1c_5_7_to_below_6_5'),
    ('hba1c', 6.49, 'a1c_5_7_to_below_6_5'), ('hba1c', 6.5, 'a1c_at_least_6_5'),
    ('fpg', 99.9, 'fpg_below_100'), ('fpg', 100, 'fpg_100_to_below_126'),
    ('fpg', 125.9, 'fpg_100_to_below_126'), ('fpg', 126, 'fpg_at_least_126'),
    ('ogtt_2h', 139.9, 'ogtt_below_140'), ('ogtt_2h', 140, 'ogtt_140_to_below_200'),
    ('ogtt_2h', 199.9, 'ogtt_140_to_below_200'), ('ogtt_2h', 200, 'ogtt_at_least_200'),
])
def test_interpretation_boundaries(test, value, expected):
    result = evaluate(measurement(test, value))
    assert [r['rule_id'] for r in result['results']] == [expected]
    assert not result['issues']
    assert result['results'][0]['source']['url'].startswith('https://')


@pytest.mark.parametrize('value,expected', [(53.99, ['glucose_below_54']), (54, ['glucose_54_to_below_70']), (69.99, ['glucose_54_to_below_70']), (70, [])])
def test_safety_boundaries(value, expected):
    result = evaluate(measurement('glucose_meter', value))
    assert [r['rule_id'] for r in result['alerts']] == expected
    assert not result['results']


@pytest.mark.parametrize('test,changes,field', [
    ('hba1c', {'pregnant': True}, 'pregnant'), ('hba1c', {'lab_certified': False}, 'lab_certified'),
    ('hba1c', {'a1c_interference': True}, 'a1c_interference'), ('fpg', {'sample': 'capillary'}, 'sample'),
    ('fpg', {'fasting_hours': 7.99}, 'fasting_hours'), ('ogtt_2h', {'glucose_load_g': 74}, 'glucose_load_g'),
    ('ogtt_2h', {'elapsed_minutes': 119}, 'elapsed_minutes'), ('ogtt_2h', {'sample': 'serum'}, 'sample'),
])
def test_excludes_inapplicable_context(test, changes, field):
    result = evaluate(measurement(test, 100, **changes))
    assert not result['results']
    assert {'code': 'not_applicable', 'field': field} in result['issues']


@pytest.mark.parametrize('changes,code', [({'value': None}, 'missing_field'), ({'value': 0}, 'invalid_value'), ({'value': -1}, 'invalid_value'), ({'value': True}, 'invalid_value'), ({'value': math.nan}, 'invalid_value'), ({'value': '100'}, 'invalid_value'), ({'unit': 'mmol/L'}, 'invalid_unit'), ({'pregnant': None}, 'missing_field'), ({'fasting_hours': '8'}, 'invalid_field')])
def test_missing_or_invalid(changes, code):
    result = evaluate({**measurement('fpg', 100), **changes})
    assert not result['results']
    assert code in [i['code'] for i in result['issues']]


def test_safety_alert_survives_missing_applicability():
    result = evaluate(measurement('fpg', 53, pregnant=None))
    assert [a['rule_id'] for a in result['alerts']] == ['glucose_below_54']
    assert not result['results']
    assert {'code': 'missing_field', 'field': 'pregnant'} in result['issues']


def test_missing_test_and_unknown_test():
    assert evaluate({})['issues']
    result = evaluate({'test_type': 'unknown', 'value': 100, 'unit': 'mg/dL'})
    assert result['issues'][0]['code'] == 'unsupported_test'


def test_all_rule_ids_are_exercised_and_have_source():
    covered = {'a1c_below_5_7', 'a1c_5_7_to_below_6_5', 'a1c_at_least_6_5', 'fpg_below_100', 'fpg_100_to_below_126', 'fpg_at_least_126', 'ogtt_below_140', 'ogtt_140_to_below_200', 'ogtt_at_least_200', 'glucose_below_54', 'glucose_54_to_below_70'}
    assert {r['id'] for r in load_rules()['rules']} == covered
