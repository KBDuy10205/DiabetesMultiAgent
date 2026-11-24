from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import assertions, build_kb, cypher_export, entities, extract, inventory, neo4j_connection, validate
from .common import ROOT, read_json, read_jsonl


def _config() -> dict:
    return read_json("config/pipeline.json", {})


def _report() -> None:
    validation = read_json("reports/validation_report.json", {})
    extraction_errors = read_jsonl("data/interim/extraction_errors.jsonl")
    manifest = read_json("reports/build_manifest.json", {})
    lines = ["# Báo cáo chất lượng Knowledge Base / Knowledge Graph", "", "## Trạng thái", "", f"- Validation: {'đạt' if validation.get('valid') else 'chưa chạy hoặc có lỗi'}.", f"- Neo4j import: chưa kiểm chứng trong môi trường này.", "", "## Số lượng", ""]
    for key, value in (manifest or validation.get("counts", {})).items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Cần kiểm tra thủ công", ""]
    if extraction_errors:
        for item in extraction_errors:
            lines.append(f"- `{item['source_path']}`: {', '.join(item.get('quality_flags', [])) or item.get('error', 'unknown error')}")
    else:
        lines.append("- Không có lỗi trích xuất được ghi nhận; vẫn cần đối chiếu mẫu với tài liệu gốc trước khi dùng lâm sàng.")
    lines += ["", "## Giới hạn", "", "- Mệnh đề y khoa chỉ được xuất sau khi có quyết định `accepted_for_demo` trong `data/kg/assertions_review.csv`.", "- Pipeline không thay thế việc thẩm định của chuyên gia y tế, không tự hợp nhất nguồn mâu thuẫn."]
    target = ROOT / "reports/quality_report.md"; target.parent.mkdir(parents=True, exist_ok=True); target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an evidence-first local KB/KG.")
    sub = parser.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("inventory"); inv.add_argument("--input", default=_config().get("raw_input_directory", "data/raw"))
    sub.add_parser("extract")
    sub.add_parser("build-kb")
    sub.add_parser("extract-entities")
    proposal = sub.add_parser("propose-assertions"); proposal.add_argument("--mode", choices=["dictionary"], default="dictionary")
    review = sub.add_parser("apply-review"); review.add_argument("--review", default="data/kg/assertions_review.csv")
    sub.add_parser("validate")
    sub.add_parser("export-cypher")
    sub.add_parser("check-neo4j")
    sub.add_parser("all")
    args = parser.parse_args(argv)
    config = _config()
    if args.command == "inventory": inventory.run(args.input)
    elif args.command == "extract": extract.run()
    elif args.command == "build-kb": build_kb.run(config.get("chunk_target_characters", 1200), config.get("chunk_min_characters", 400))
    elif args.command == "extract-entities": entities.run()
    elif args.command == "propose-assertions": assertions.propose()
    elif args.command == "apply-review": assertions.apply_review(args.review)
    elif args.command == "validate":
        result = validate.run(); _report()
        if not result["valid"]:
            print("Validation failed; see reports/validation_report.json", file=sys.stderr); return 1
    elif args.command == "export-cypher":
        result = validate.run()
        if not result["valid"]:
            print("Refusing Cypher export because validation failed.", file=sys.stderr); return 1
        cypher_export.run(); _report()
    elif args.command == "check-neo4j":
        result = neo4j_connection.verify_connection()
        print(f"Connected to {result['database']} at {result['uri']} (nodes: {result['node_count']}, relationships: {result['relationship_count']}).")
    else:
        inventory.run(config.get("raw_input_directory", "data/raw")); extract.run(); build_kb.run(config.get("chunk_target_characters", 1200), config.get("chunk_min_characters", 400)); entities.run(); assertions.propose(); assertions.apply_review("data/kg/assertions_review.csv")
        result = validate.run()
        if not result["valid"]: _report(); return 1
        cypher_export.run(); _report()
    print(f"Completed: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
