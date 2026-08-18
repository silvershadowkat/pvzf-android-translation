#!/usr/bin/env python3
"""Find untranslated IL2CPP literals embedded inside translated PC strings.

Fusion's Android UI sometimes stores only the suffix of a sentence and adds a
plant name or another value at runtime. A conventional exact-string audit
misses those literals because the PC community project translates the complete
rendered sentence. This report identifies proper prefix, suffix, and inner
matches for manual review. It never edits metadata automatically.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_metadata_translation import load_pc_translations, parse_metadata  # noqa: E402


CJK_RE = re.compile(r"[\u3400-\u9fff]")


def load_pc_exact(strings_dir: Path) -> dict[str, str]:
    exact, _, _, _ = load_pc_translations(strings_dir)
    return exact


def relation(fragment: str, source: str) -> str | None:
    if fragment == source or fragment not in source:
        return None
    if source.endswith(fragment):
        return "suffix"
    if source.startswith(fragment):
        return "prefix"
    return "inner"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--pc-strings-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--minimum-cjk",
        default=3,
        type=int,
        help="minimum number of CJK characters in a candidate fragment",
    )
    parser.add_argument(
        "--context-radius",
        default=2,
        type=int,
        help="number of neighboring literal-table entries to include for review",
    )
    args = parser.parse_args()

    _, literals = parse_metadata(args.metadata.read_bytes())
    fragments: dict[str, list[int]] = {}
    for index, literal in enumerate(literals):
        cjk_count = len(CJK_RE.findall(literal.text))
        if cjk_count >= args.minimum_cjk:
            fragments.setdefault(literal.text, []).append(index)

    exact = load_pc_exact(args.pc_strings_dir)
    matches = []
    for fragment, indices in sorted(fragments.items()):
        candidates = []
        for source, target in exact.items():
            match_relation = relation(fragment, source)
            if match_relation is None:
                continue
            candidates.append(
                {
                    "relation": match_relation,
                    "pc_source": source,
                    "pc_target": target,
                    "removed_source_text": source.replace(fragment, "<FRAGMENT>", 1),
                }
            )
        if candidates:
            contexts = []
            for index in indices:
                first = max(0, index - args.context_radius)
                last = min(len(literals), index + args.context_radius + 1)
                contexts.append(
                    {
                        "metadata_index": index,
                        "neighbors": [
                            {
                                "metadata_index": neighbor_index,
                                "text": literals[neighbor_index].text,
                            }
                            for neighbor_index in range(first, last)
                        ],
                    }
                )
            matches.append(
                {
                    "fragment": fragment,
                    "metadata_indices": indices,
                    "candidate_count": len(candidates),
                    "candidates": candidates,
                    "contexts": contexts,
                }
            )

    report = {
        "format_version": 2,
        "review_note": (
            "Candidates require manual context review. Do not automatically replace "
            "fragments because omitted prefixes can determine the English subject or target."
        ),
        "metadata": str(args.metadata.resolve()),
        "pc_strings_dir": str(args.pc_strings_dir.resolve()),
        "remaining_cjk_literals": len(fragments),
        "matched_fragments": len(matches),
        "matches": matches,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "remaining_cjk_literals": len(fragments),
                "matched_fragments": len(matches),
                "output": str(args.output),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
