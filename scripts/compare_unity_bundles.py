#!/usr/bin/env python3
"""Compare Unity serialized objects in two bundles by path ID and raw payload hash."""

from __future__ import annotations

import argparse
import collections
import gc
import hashlib
import json
from pathlib import Path

import UnityPy


def build_index(path: Path) -> dict[tuple[str, int], dict[str, object]]:
    env = UnityPy.load(str(path))
    result: dict[tuple[str, int], dict[str, object]] = {}
    for obj in env.objects:
        raw = obj.get_raw_data()
        try:
            name = obj.peek_name()
        except Exception:
            name = ""
        key = (obj.assets_file.name, obj.path_id)
        result[key] = {
            "file": obj.assets_file.name,
            "type": obj.type.name,
            "name": name,
            "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    del env
    gc.collect()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("modified", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    base = build_index(args.base)
    modified = build_index(args.modified)
    changes: list[dict[str, object]] = []
    counts: collections.Counter[str] = collections.Counter()
    type_counts: collections.Counter[str] = collections.Counter()

    for key in sorted(base.keys() | modified.keys()):
        left = base.get(key)
        right = modified.get(key)
        if left is None:
            kind = "added"
            type_name = str(right["type"])
        elif right is None:
            kind = "removed"
            type_name = str(left["type"])
        elif left["type"] != right["type"]:
            kind = "type_changed"
            type_name = f"{left['type']}->{right['type']}"
        elif left["sha256"] != right["sha256"]:
            kind = "modified"
            type_name = str(left["type"])
        else:
            continue

        counts[kind] += 1
        type_counts[f"{kind}:{type_name}"] += 1
        changes.append({"file": key[0], "path_id": key[1], "kind": kind, "base": left, "modified": right})

    report = {
        "unitypy_version": UnityPy.__version__,
        "base": str(args.base.resolve()),
        "modified": str(args.modified.resolve()),
        "base_object_count": len(base),
        "modified_object_count": len(modified),
        "change_counts": dict(sorted(counts.items())),
        "change_type_counts": dict(sorted(type_counts.items())),
        "changes": changes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "base_object_count", "modified_object_count", "change_counts", "change_type_counts"
    )}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
