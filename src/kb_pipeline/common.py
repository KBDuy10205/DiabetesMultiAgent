from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]


def path_from_root(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def stable_id(namespace: str, *parts: object) -> str:
    payload = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return f"{namespace}_{hashlib.sha256(payload).hexdigest()[:24]}"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def normalise_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value).replace("\u00a0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n[ \t]+", "\n", value)
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def read_json(path: str | Path, default: Any) -> Any:
    file_path = path_from_root(path)
    return default if not file_path.exists() else json.loads(file_path.read_text(encoding="utf-8"))


def write_json(path: str | Path, value: Any) -> None:
    file_path = path_from_root(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    file_path = path_from_root(path)
    if not file_path.exists():
        return []
    return [json.loads(line) for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: str | Path, records: Iterable[dict[str, Any]]) -> None:
    file_path = path_from_root(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
