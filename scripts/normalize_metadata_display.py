"""Balance translated full display strings without closing runtime fragments."""
import argparse
import json
from pathlib import Path

from build_metadata_translation import build_metadata, parse_metadata
from migrate_version_text import same_arguments
from protected_metadata import PROTECTED_METADATA_STRINGS, verify_metadata
from reconcile_pc_english import balance_pc_rich_text


def normalize_display(source, target):
    if source in PROTECTED_METADATA_STRINGS or source == target:
        return source
    if not same_arguments(source, target):
        raise ValueError("Format arguments changed; an explicit review is required")
    if balance_pc_rich_text(source) == source:
        return balance_pc_rich_text(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("official", "source", "output", "report"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    official = args.official.read_bytes()
    raw = args.source.read_bytes()
    originals = parse_metadata(official)[1]
    layout, literals = parse_metadata(raw)
    assert len(originals) == len(literals)
    verify_metadata(official, raw)
    changes, output = [], []
    for index, (original, current) in enumerate(zip(originals, literals)):
        target = normalize_display(original.text, current.text)
        output.append(target.encode("utf8"))
        if target != current.text:
            changes.append({"index": index, "source": original.text,
                            "before": current.text, "target": target})
    result = build_metadata(raw, layout, output)
    assert [x.raw for x in parse_metadata(result)[1]] == output
    protected = verify_metadata(official, result)
    args.output.write_bytes(result)
    args.report.write_text(json.dumps({"changes": changes, "protected": protected},
                                      ensure_ascii=True, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"balanced_display_strings": len(changes)}))


if __name__ == "__main__":
    main()
