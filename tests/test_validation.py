from kb_pipeline import validate


def test_validation_reports_missing_outputs_as_valid_empty_structure(tmp_path, monkeypatch):
    monkeypatch.setattr(validate, "read_jsonl", lambda _: [])
    monkeypatch.setattr(validate, "write_json", lambda *_: None)
    result = validate.run()
    assert result["valid"] is True
    assert result["counts"]["sources"] == 0
