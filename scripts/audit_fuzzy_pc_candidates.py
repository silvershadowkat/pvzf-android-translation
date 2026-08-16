#!/usr/bin/env python3
"""Rank untranslated Android metadata literals against PC translation sources.

This is a review aid, not an automatic translator.  Android sometimes ships a
shortened or revised copy of a PC gameplay description, so exact matching
cannot find it.  The report keeps the source, PC English target, and similarity
score together so a reviewer can confirm terminology before adding an exact
Android fallback.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path
from typing import Iterable


CJK_RE = re.compile(r"[\u3400-\u9fff]")
STRUCTURED_FILES = ("travel_buffs.json", "tips_fs.json", "tips_iz.json")


def paired_strings(source: object, target: object) -> Iterable[tuple[str, str]]:
    if isinstance(source, str) and isinstance(target, str):
        if CJK_RE.search(source) and target and not CJK_RE.search(target):
            yield source, target
        return
    if isinstance(source, dict) and isinstance(target, dict):
        for key in source.keys() & target.keys():
            yield from paired_strings(source[key], target[key])
        return
    if isinstance(source, list) and isinstance(target, list):
        for source_item, target_item in zip(source, target):
            yield from paired_strings(source_item, target_item)


def normalized(value: str) -> str:
    return re.sub(r"[\s\W_]+", "", value, flags=re.UNICODE)


def similarity(left: str, right: str) -> float:
    left_normalized = normalized(left)
    right_normalized = normalized(right)
    if not left_normalized or not right_normalized:
        return 0.0
    sequence = difflib.SequenceMatcher(None, left_normalized, right_normalized).ratio()
    if left_normalized in right_normalized or right_normalized in left_normalized:
        containment = min(len(left_normalized), len(right_normalized)) / max(
            len(left_normalized), len(right_normalized)
        )
        sequence = max(sequence, 0.65 + 0.35 * containment)
    return sequence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--pc-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--minimum-score", type=float, default=0.36)
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    pc_pairs: list[tuple[str, str, str]] = []
    dump_root = args.pc_root / "Dumps"
    english_root = args.pc_root / "Localization" / "English" / "Strings"
    for filename in STRUCTURED_FILES:
        source = json.loads((dump_root / filename).read_text(encoding="utf-8"))
        target = json.loads((english_root / filename).read_text(encoding="utf-8"))
        for source_text, target_text in paired_strings(source, target):
            pc_pairs.append((source_text, target_text, filename))

    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    literals = audit["metadata"]["strings"]
    report: list[dict[str, object]] = []
    for literal in literals:
        text = literal["text"]
        if len(normalized(text)) < 4:
            continue
        ranked = sorted(
            (
                (similarity(text, source_text), source_text, target_text, filename)
                for source_text, target_text, filename in pc_pairs
            ),
            reverse=True,
        )
        matches = [
            {
                "score": round(score, 4),
                "pc_source": source_text,
                "pc_english": target_text,
                "file": filename,
            }
            for score, source_text, target_text, filename in ranked[: args.limit]
            if score >= args.minimum_score
        ]
        if matches:
            report.append(
                {
                    "android_text": text,
                    "indices": literal["indices"],
                    "matches": matches,
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "format_version": 1,
                "review_only": True,
                "candidate_count": len(report),
                "candidates": report,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(report)} fuzzy review candidates to {args.output}")


if __name__ == "__main__":
    main()
