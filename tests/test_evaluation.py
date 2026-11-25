import pytest
from evaluation.benchmark import citation_scores, load_cases, parse_answer


def test_question_dataset_is_traceable():
    cases = load_cases()
    assert len(cases) == 3
    assert {item['gold'] for item in cases} == {'A', 'B', 'C'}


@pytest.mark.parametrize('answer,expected', [('A [S1]','A'), ('**B** [S2]', 'B'), ('C. Đúng', 'C'), ('Không đủ thông tin', None), ('AB', None)])
def test_parse_answer(answer, expected):
    assert parse_answer(answer) == expected


def test_citation_and_source_agreement_are_separate():
    evidence = [{'chunk_id':'other', 'source_id':'s'}, {'chunk_id':'gold', 'source_id':'s2'}]
    assert citation_scores('A [S1]', evidence, 'gold') == {'citation_valid':True, 'gold_chunk_cited':False}
    assert citation_scores('A [S2]', evidence, 'gold') == {'citation_valid':True, 'gold_chunk_cited':True}
    assert not citation_scores('A [S3]', evidence, 'gold')['citation_valid']


def test_summary_does_not_treat_failed_calls_as_incorrect_or_zero_tokens():
    from evaluation.report import summarize
    rows = [{'method':'llm', 'case_id':'q', 'status':'http_503', 'answer':None, 'correct':None,
             'hit_at_5':None, 'retrieved_chunk_ids':[], 'seconds':1.0, 'peak_rss_mib':10.0, 'usage':None}]
    result = summarize(rows)[0]
    assert result['attempts'] == 1 and result['accuracy_denominator'] == 0
    assert result['consistency_pairs'] == 0 and result['prompt_tokens'] is None
