from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .benchmark import METHODS


def summarize(rows, local_rows=None):
    summary = []
    for method in METHODS:
        items = [r for r in rows if r['method'] == method]
        answers = [r for r in items if r['answer'] is not None]
        pairs = []
        for case in sorted({r['case_id'] for r in items}):
            valid = [r['answer'] for r in items if r['case_id'] == case and r['answer'] is not None]
            if len(valid) == 2:
                pairs.append(valid[0] == valid[1])
        retrieved = [r for r in items if r['hit_at_5'] is not None and
                     (r['retrieved_chunk_ids'] or r['status'].startswith('http_') or r['status'] in {'ok', 'draft', 'insufficient_evidence'} or r.get('agent_statuses', {}).get('retrieval') == 'ok')]
        usable = [r for r in answers if 'citation_valid' in r]
        usage = [r['usage'] for r in items if isinstance(r.get('usage'), dict)]
        def total_if_complete(key):
            return sum(u[key] for u in usage) if usage and all(type(u.get(key)) is int for u in usage) else None
        local = [r for r in (local_rows or []) if r['method'] == method and r['status'] == 'ok' and r.get('hit_at_5') is not None]
        summary.append({'method':method, 'attempts':len(items), 'status_counts':dict(Counter(r['status'] for r in items)),
                        'answers_parsed':len(answers), 'accuracy_correct':sum(r['correct'] for r in answers),
                        'accuracy_denominator':len(answers), 'consistency_same':sum(pairs), 'consistency_pairs':len(pairs),
                        'retrieval_hits':sum(r['hit_at_5'] for r in retrieved), 'retrieval_denominator':len(retrieved),
                        'valid_citations':sum(r.get('citation_valid', False) for r in usable),
                        'gold_cited':sum(r.get('gold_chunk_cited', False) for r in usable), 'citation_denominator':len(usable),
                        'mean_seconds_all_attempts':mean(r['seconds'] for r in items) if items else None,
                        'mean_peak_rss_mib_all_attempts':mean(r['peak_rss_mib'] for r in items) if items else None,
                        'usage_responses':len(usage), 'prompt_tokens':total_if_complete('prompt_tokens'),
                        'completion_tokens':total_if_complete('completion_tokens'), 'total_tokens':total_if_complete('total_tokens'),
                        'local_retrieval_hits':sum(r['hit_at_5'] for r in local), 'local_retrieval_denominator':len(local),
                        'local_mean_seconds':mean(r['seconds'] for r in local) if local else None,
                        'local_mean_peak_rss_mib':mean(r['peak_rss_mib'] for r in local) if local else None,
                        'prediction_ran_count':sum(r.get('prediction_ran') is True for r in items),
                        'prediction_blocked_count':sum(r.get('safety') in {'blocked','blocked_missing_measurement','blocked_missing_glucose'} for r in items)})
    return summary


def chart(summary, path):
    labels = ['LLM', 'Vector', 'KG + Vector', 'Single-Agent', 'Multi-Agent']
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    times = [s['mean_seconds_all_attempts'] if s['mean_seconds_all_attempts'] is not None else 0 for s in summary]
    axes[0].bar(labels, times, color='#438c78')
    axes[0].set_ylabel('Giây / lượt đã thử')
    axes[0].set_title('Thời gian trung bình (kể cả lượt lỗi)')
    for i, s in enumerate(summary):
        axes[0].text(i, times[i], f"n={s['attempts']}", ha='center', va='bottom', fontsize=8)
    values = [(s['local_retrieval_hits'] / s['local_retrieval_denominator'] * 100) if s['local_retrieval_denominator'] else 0 for s in summary]
    bars = axes[1].bar(labels, values, color='#729bc2')
    axes[1].set_ylim(0, 110)
    axes[1].set_ylabel('% lượt truy xuất đã hoàn tất')
    axes[1].set_title('Truy xuất cục bộ: Hit@5 đúng chunk chuẩn')
    for i, s in enumerate(summary):
        label = f"{s['local_retrieval_hits']}/{s['local_retrieval_denominator']}" if s['local_retrieval_denominator'] else 'N/A'
        axes[1].text(i, values[i] + 2, label, ha='center', va='bottom', fontsize=8)
    for axis in axes:
        axis.tick_params(axis='x', labelrotation=20, labelsize=8)
        axis.spines[['top','right']].set_visible(False)
    fig.suptitle('Thử nghiệm thăm dò: mẫu nhỏ, không xếp hạng chất lượng y khoa', fontsize=12)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('--local')
    parser.add_argument('--summary', required=True)
    parser.add_argument('--chart', required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.input).read_text(encoding='utf-8').splitlines() if line.strip()]
    local_rows = [json.loads(line) for line in Path(args.local).read_text(encoding='utf-8').splitlines() if line.strip()] if args.local else []
    summary = summarize(rows, local_rows)
    path = Path(args.summary)
    with path.open('x', encoding='utf-8') as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)
    if Path(args.chart).exists():
        raise FileExistsError('Refusing to overwrite chart')
    chart(summary, Path(args.chart))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
