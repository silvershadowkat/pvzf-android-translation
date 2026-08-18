#!/usr/bin/env python3
"""Inventory CJK-bearing serialized UI strings with their Unity hierarchy."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path

import UnityPy

from polish_android_ui import CJK_RE, hierarchy_for_component, make_generator, object_map


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def collect(value, path=()):
    matches = []
    if isinstance(value, str) and CJK_RE.search(value):
        matches.append({"field_path": list(path), "text": value})
    elif isinstance(value, dict):
        for key, item in value.items():
            matches.extend(collect(item, path + (key,)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            matches.extend(collect(item, path + (index,)))
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--dummy-dll-dir", required=True, type=Path)
    parser.add_argument("--unity-version", default="2022.3.62f1")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    env = UnityPy.load(str(args.bundle))
    env.typetree_generator = make_generator(args.unity_version, args.dummy_dll_dir)
    objects = object_map(env)
    records = []
    failures = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            tree = obj.read_typetree(check_read=False)
        except Exception as exc:
            failures.append({"file": obj.assets_file.name, "path_id": obj.path_id, "error": str(exc)})
            continue
        matches = collect(tree)
        if matches:
            records.append(
                {
                    "file": obj.assets_file.name,
                    "path_id": obj.path_id,
                    "hierarchy": list(hierarchy_for_component(objects, obj)),
                    "matches": matches,
                }
            )

    report = {
        "format_version": 1,
        "bundle": {"path": str(args.bundle.resolve()), "sha256": sha256_file(args.bundle)},
        "object_count": len(records),
        "string_field_count": sum(len(record["matches"]) for record in records),
        "records": records,
        "typetree_failure_count": len(failures),
        "typetree_failures": failures,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("bundle", "object_count", "string_field_count", "typetree_failure_count")}, ensure_ascii=False, indent=2))
    del env, objects
    gc.collect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
