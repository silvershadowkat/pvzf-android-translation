"""Track the 117 provisional Release 9 strings against a reviewed PC snapshot.

Read-only comparison: reports complete PC candidates without rewriting payloads.
"""
import argparse
import json
from pathlib import Path

from build_metadata_translation import load_pc_translations, translate_complete_pc_literal
from reviewed_generic_text import GENERIC_TEXT, PC_NAME_REQUIREMENTS
from reviewed_release9_text import GENERIC_RELEASE9


def release9_entries():
    entries = dict(GENERIC_RELEASE9)
    source = "命运无常：获得了{0}幸运"
    entries[source] = GENERIC_TEXT[source]
    return entries


def audit(strings_dir):
    exact, _, regex, _ = load_pc_translations(strings_dir, include_android_fallbacks=False)
    rows = []
    for source, fallback in release9_entries().items():
        pc, method = translate_complete_pc_literal(source, exact, regex)
        rows.append({
            "source": source,
            "provisional_english": fallback,
            "status": "pc_candidate_available" if method else "awaiting_pc_translation",
            "pc_english": pc if method else None,
            "pc_match_method": method,
            "pc_name_requirement": PC_NAME_REQUIREMENTS.get(source),
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strings-dir", type=Path, required=True)
    parser.add_argument("--pc-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = audit(args.strings_dir)
    available = sum(row["status"] == "pc_candidate_available" for row in rows)
    report = {"pc_commit": args.pc_commit, "tracked": len(rows),
              "pc_candidates": available, "entries": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Tracked {len(rows)} provisional strings; {available} complete PC candidates.")


if __name__ == "__main__":
    main()
