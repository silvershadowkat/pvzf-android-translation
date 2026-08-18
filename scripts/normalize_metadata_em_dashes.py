#!/usr/bin/env python3
"""Replace em dashes in IL2CPP string literals without changing other text."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_metadata_translation import build_metadata, parse_metadata


EM_DASH = "\u2014"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    base = args.base.read_bytes()
    layout, literals = parse_metadata(base)
    translated: list[bytes] = []
    changes: list[dict[str, object]] = []
    for index, literal in enumerate(literals):
        count = literal.text.count(EM_DASH)
        normalized = literal.text.replace(EM_DASH, "-")
        translated.append(normalized.encode("utf-8"))
        if count:
            changes.append(
                {
                    "index": index,
                    "replacement_count": count,
                    "source": literal.text,
                    "translation": normalized,
                }
            )

    output = build_metadata(base, layout, translated)
    output_layout, output_literals = parse_metadata(output)
    if [literal.raw for literal in output_literals] != translated:
        raise RuntimeError("self-validation failed: rebuilt literals differ")
    remaining = sum(literal.text.count(EM_DASH) for literal in output_literals)
    if remaining:
        raise RuntimeError(f"validation found {remaining} remaining em dashes")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    report = {
        "format_version": 1,
        "base": {
            "path": str(args.base.resolve()),
            "size": len(base),
            "sha256": sha256(base),
            "literal_count": len(literals),
            "literal_data_offset": layout.data_offset,
            "literal_data_size": layout.data_size,
        },
        "output": {
            "path": str(args.output.resolve()),
            "size": len(output),
            "sha256": sha256(output),
            "literal_count": len(output_literals),
            "literal_data_offset": output_layout.data_offset,
            "literal_data_size": output_layout.data_size,
        },
        "changed_literal_occurrences": len(changes),
        "replacement_count": sum(int(item["replacement_count"]) for item in changes),
        "remaining_em_dashes": remaining,
        "changes": changes,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": report["output"],
                "changed_literal_occurrences": report["changed_literal_occurrences"],
                "replacement_count": report["replacement_count"],
                "remaining_em_dashes": remaining,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
