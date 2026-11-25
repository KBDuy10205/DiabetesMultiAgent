"""Complete a retrieval-only comparison without contacting the LLM."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from agents.coordinator import CoordinatorAgent
from agents.prediction import PredictionAgent
from agents.rule import RuleAgent
from rag.core import embedder
from .benchmark import INSTRUCTION, MemorySampler, get_pima_row, load_cases, retrieve


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    features, measurement = get_pima_row()
    cases = load_cases()
    with path.open('x', encoding='utf-8') as file:
        model = embedder()
        for case in cases:
            question = case['question'] + INSTRUCTION
            for method in ('vector_rag', 'kg_vector_rag', 'single_agent', 'multi_agent'):
                row = {'method':method, 'case_id':case['id'], 'status':'error', 'hit_at_5':None,
                       'retrieved_chunk_ids':[], 'prediction_ran':None, 'safety':None}
                start = time.perf_counter()
                with MemorySampler() as memory:
                    try:
                        if method == 'multi_agent':
                            result = CoordinatorAgent().supervise({'intent':'explanation', 'question':question, 'features':features,
                                                                   'measurement':measurement, 'generate_answer':False})
                            evidence = result['evidence']
                            row['safety'] = result['safety']
                            row['prediction_ran'] = result['agents'].get('prediction', {}).get('status') == 'ok'
                            row['agent_statuses'] = {key:value['status'] for key, value in result['agents'].items()}
                            row['status'] = 'ok' if all(result['agents'].get(k, {}).get('status') == 'ok' for k in ('rule', 'retrieval', 'knowledge')) else 'error'
                        else:
                            if method == 'single_agent':
                                PredictionAgent().run(features)
                                rule = RuleAgent().run(measurement)
                                row['prediction_ran'] = True
                                row['rule_issue_codes'] = [issue['code'] for issue in rule['issues']]
                            evidence = retrieve(question, method, model)
                            row['status'] = 'ok'
                        row['retrieved_chunk_ids'] = [x['chunk_id'] for x in evidence]
                        row['hit_at_5'] = case['gold_chunk_id'] in row['retrieved_chunk_ids']
                    except Exception as error:
                        row['status'] = 'error_' + type(error).__name__
                row['seconds'] = time.perf_counter() - start
                row['peak_rss_mib'] = memory.peak / (1024 * 1024)
                file.write(json.dumps(row, ensure_ascii=False) + '\n')
                file.flush()
                print(f"{case['id']} {method} status={row['status']} hit={row['hit_at_5']}", flush=True)


if __name__ == '__main__':
    main()
