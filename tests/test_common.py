from kb_pipeline.common import normalise_text, stable_id
from kb_pipeline.cypher_export import _literal


def test_stable_id_is_repeatable():
    assert stable_id("chunk", "a", 2) == stable_id("chunk", "a", 2)
    assert stable_id("chunk", "a", 2) != stable_id("chunk", "a", 3)


def test_normalise_text_keeps_meaningful_symbols():
    assert normalise_text(" HbA1c  ≥  6,5%\n\n\nKhông bỏ ") == "HbA1c ≥ 6,5%\n\nKhông bỏ"


def test_cypher_map_keys_are_not_json_quoted():
    assert _literal({"id": "source_1", "demo": False}) == '{id: "source_1", demo: false}'
