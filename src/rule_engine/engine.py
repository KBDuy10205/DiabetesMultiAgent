from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

RULES_PATH = Path(__file__).resolve().parents[2] / 'config' / 'medical_rules.json'
INTERPRETATION_TESTS = {'hba1c', 'fpg', 'ogtt_2h'}
GLUCOSE_TESTS = {'fpg', 'ogtt_2h', 'glucose_random', 'glucose_meter'}
UNITS = {'hba1c': '%', **{name: 'mg/dL' for name in GLUCOSE_TESTS}}
DISCLAIMER = 'Chỉ hỗ trợ học tập và tham khảo; không chẩn đoán, không thay thế bác sĩ.'


def load_rules(path: Path = RULES_PATH) -> dict[str, Any]:
    with path.open(encoding='utf-8') as file:
        data = json.load(file, parse_float=Decimal)
    ids = set()
    for rule in data['rules']:
        if (rule['id'] in ids or rule['category'] not in {'interpretation', 'safety'}
                or not rule['source'].get('url') or not rule['source'].get('title')
                or not rule['if'] or not set(rule['if']) <= {'gte', 'lt'}):
            raise ValueError('Invalid rule configuration')
        ids.add(rule['id'])
    return data


def number(value: Any) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except InvalidOperation:
        return None


def matches(value: Decimal, conditions: dict) -> bool:
    return all(value >= Decimal(str(limit)) if op == 'gte' else value < Decimal(str(limit)) for op, limit in conditions.items())


def evaluate(measurement: dict, rules: dict | None = None) -> dict:
    """Evaluate one result. Missing applicability never implies normality."""
    if not isinstance(measurement, dict):
        raise ValueError('measurement must be an object')
    rules = rules if rules is not None else load_rules()
    issues, results, alerts = [], [], []
    output = {'rule_version': rules['version'], 'disclaimer': DISCLAIMER, 'issues': issues, 'results': results, 'alerts': alerts}
    for field in ('test_type', 'value', 'unit'):
        if field not in measurement or measurement[field] is None:
            issues.append({'code': 'missing_field', 'field': field})
    test = measurement.get('test_type')
    if not isinstance(test, str) or test not in UNITS:
        if test is not None:
            issues.append({'code': 'unsupported_test', 'field': 'test_type'})
        return output
    unit = measurement.get('unit')
    if unit is not None and unit != UNITS[test]:
        issues.append({'code': 'invalid_unit', 'field': 'unit', 'expected': UNITS[test]})
    value = number(measurement.get('value'))
    if measurement.get('value') is not None and (value is None or value <= 0):
        issues.append({'code': 'invalid_value', 'field': 'value'})
    if value is None or value <= 0 or unit != UNITS[test]:
        return output

    def run(category, test_type, destination):
        for rule in rules['rules']:
            if rule['category'] == category and rule['test_type'] == test_type and rule['unit'] == unit and matches(value, rule['if']):
                destination.append({'rule_id': rule['id'], 'message': rule['then'], 'source': rule['source']})

    if test in GLUCOSE_TESTS:
        run('safety', 'glucose', alerts)
    if test not in INTERPRETATION_TESTS:
        issues.append({'code': 'interpretation_not_supported', 'field': 'test_type'})
        return output

    required = {'pregnant': bool}
    if test == 'hba1c':
        required.update({'lab_certified': bool, 'a1c_interference': bool})
    elif test == 'fpg':
        required.update({'sample': str, 'fasting_hours': 'number'})
    else:
        required.update({'sample': str, 'glucose_load_g': 'number', 'elapsed_minutes': 'number'})
    valid = True
    for field, expected in required.items():
        item = measurement.get(field)
        if item is None:
            issues.append({'code': 'missing_field', 'field': field}); valid = False
        elif expected == 'number' and (number(item) is None or number(item) < 0):
            issues.append({'code': 'invalid_field', 'field': field}); valid = False
        elif expected != 'number' and type(item) is not expected:
            issues.append({'code': 'invalid_field', 'field': field}); valid = False
    if not valid:
        return output
    constraints = [('pregnant', measurement['pregnant'] is False)]
    if test == 'hba1c':
        constraints += [('lab_certified', measurement['lab_certified'] is True), ('a1c_interference', measurement['a1c_interference'] is False)]
    elif test == 'fpg':
        constraints += [('sample', measurement['sample'] == 'plasma'), ('fasting_hours', number(measurement['fasting_hours']) >= 8)]
    else:
        constraints += [('sample', measurement['sample'] == 'plasma'), ('glucose_load_g', number(measurement['glucose_load_g']) == 75), ('elapsed_minutes', number(measurement['elapsed_minutes']) == 120)]
    for field, ok in constraints:
        if not ok:
            issues.append({'code': 'not_applicable', 'field': field})
    if all(ok for _, ok in constraints):
        run('interpretation', test, results)
    return output
