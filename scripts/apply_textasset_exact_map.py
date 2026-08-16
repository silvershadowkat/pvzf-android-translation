#!/usr/bin/env python3
"""Apply a reviewed exact-string map to TextAssets in a Unity bundle."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
from typing import Any

import UnityPy


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def replace_tree(value: Any, exact: dict[str, str], used: set[str]) -> tuple[Any, int]:
    if isinstance(value, str):
        replacement = exact.get(value)
        if replacement is not None:
            used.add(value)
            return replacement, 1
        return value, 0
    if isinstance(value, list):
        result: list[Any] = []
        count = 0
        for item in value:
            replaced, item_count = replace_tree(item, exact, used)
            result.append(replaced)
            count += item_count
        return result, count
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        count = 0
        for key, item in value.items():
            replaced, item_count = replace_tree(item, exact, used)
            result[key] = replaced
            count += item_count
        return result, count
    return value, 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--exact-map", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "none"), default="original")
    args = parser.parse_args()

    map_payload = json.loads(args.exact_map.read_text(encoding="utf-8-sig"))
    exact = map_payload.get("exact", map_payload)
    if not isinstance(exact, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in exact.items()
    ):
        raise TypeError("exact map must contain a string-to-string 'exact' object")

    env = UnityPy.load(str(args.base_bundle))
    expected: dict[tuple[str, int], str] = {}
    changes: list[dict[str, object]] = []
    used: set[str] = set()
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.parse_as_object()
        original = data.m_Script
        try:
            tree = json.loads(original.lstrip("\ufeff"))
        except (json.JSONDecodeError, TypeError):
            replacement = exact.get(original)
            if replacement is None:
                continue
            updated = replacement
            replacement_count = 1
            used.add(original)
        else:
            updated_tree, replacement_count = replace_tree(tree, exact, used)
            if replacement_count == 0:
                continue
            updated = json.dumps(updated_tree, ensure_ascii=False, indent=4)
        data.m_Script = updated
        obj.save_typetree(data)
        key = (obj.assets_file.name, obj.path_id)
        expected[key] = updated
        changes.append(
            {
                "file": key[0],
                "path_id": key[1],
                "name": data.m_Name,
                "replacement_count": replacement_count,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.write_bytes(output_bytes)
    del output_bytes, env
    gc.collect()

    validated = 0
    check = UnityPy.load(str(args.output))
    for obj in check.objects:
        key = (obj.assets_file.name, obj.path_id)
        if key not in expected:
            continue
        if obj.type.name != "TextAsset" or obj.parse_as_object().m_Script != expected[key]:
            raise RuntimeError(f"TextAsset validation failed for {key}")
        validated += 1
    if validated != len(expected):
        raise RuntimeError(f"validated {validated} of {len(expected)} changed TextAssets")
    del check
    gc.collect()

    unused = sorted(set(exact) - used)
    report = {
        "format_version": 1,
        "base": {"path": str(args.base_bundle.resolve()), "sha256": sha256_file(args.base_bundle)},
        "exact_map": {"path": str(args.exact_map.resolve()), "entry_count": len(exact)},
        "output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
        },
        "changed_text_assets": len(changes),
        "validated_text_assets": validated,
        "changes": changes,
        "unused_exact_entries": unused,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("output", "changed_text_assets", "validated_text_assets")}, indent=2))
    if unused:
        raise RuntimeError(f"{len(unused)} exact-map entries were not applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
