#!/usr/bin/env python3
"""Replace em dashes in player-facing Unity strings with ASCII hyphens."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
from typing import Any

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator


EM_DASH = "\u2014"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_tree(value: Any) -> tuple[Any, int]:
    if isinstance(value, str):
        count = value.count(EM_DASH)
        return value.replace(EM_DASH, "-"), count
    if isinstance(value, list):
        result = []
        count = 0
        for item in value:
            normalized, item_count = normalize_tree(item)
            result.append(normalized)
            count += item_count
        return result, count
    if isinstance(value, dict):
        result = {}
        count = 0
        for key, item in value.items():
            normalized, item_count = normalize_tree(item)
            result[key] = normalized
            count += item_count
        return result, count
    return value, 0


def make_generator(unity_version: str, dummy_dll_dir: Path) -> TypeTreeGenerator:
    generator = TypeTreeGenerator(unity_version)
    generator.load_local_dll_folder(str(dummy_dll_dir))
    return generator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--dummy-dll-dir", required=True, type=Path)
    parser.add_argument("--unity-version", default="2022.3.62f1")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    generator = make_generator(args.unity_version, args.dummy_dll_dir)
    env = UnityPy.load(str(args.base_bundle))
    env.typetree_generator = generator
    changes = []
    skipped_monobehaviours = 0
    skipped_with_raw_em_dashes = []

    for obj in env.objects:
        if obj.type.name == "TextAsset":
            data = obj.parse_as_object()
            count = data.m_Script.count(EM_DASH)
            if count:
                data.m_Script = data.m_Script.replace(EM_DASH, "-")
                obj.save_typetree(data)
                changes.append(
                    {
                        "file": obj.assets_file.name,
                        "path_id": obj.path_id,
                        "type": obj.type.name,
                        "name": data.m_Name,
                        "replacement_count": count,
                    }
                )
        elif obj.type.name == "MonoBehaviour":
            try:
                tree = obj.read_typetree(check_read=False)
            except Exception:
                skipped_monobehaviours += 1
                raw_count = bytes(obj.get_raw_data()).count(EM_DASH.encode("utf-8"))
                if raw_count:
                    skipped_with_raw_em_dashes.append(
                        {
                            "file": obj.assets_file.name,
                            "path_id": obj.path_id,
                            "replacement_count": raw_count,
                        }
                    )
                continue
            normalized, count = normalize_tree(tree)
            if count:
                obj.save_typetree(normalized)
                changes.append(
                    {
                        "file": obj.assets_file.name,
                        "path_id": obj.path_id,
                        "type": obj.type.name,
                        "replacement_count": count,
                    }
                )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.write_bytes(output_bytes)
    del output_bytes, env
    gc.collect()

    check_generator = make_generator(args.unity_version, args.dummy_dll_dir)
    check = UnityPy.load(str(args.output))
    check.typetree_generator = check_generator
    remaining = 0
    for obj in check.objects:
        if obj.type.name == "TextAsset":
            remaining += obj.parse_as_object().m_Script.count(EM_DASH)
        elif obj.type.name == "MonoBehaviour":
            try:
                tree = obj.read_typetree(check_read=False)
            except Exception:
                continue
            _, count = normalize_tree(tree)
            remaining += count
    del check
    gc.collect()
    if remaining:
        raise RuntimeError(f"validation found {remaining} remaining player-facing em dashes")
    if skipped_with_raw_em_dashes:
        raise RuntimeError(
            "unreadable MonoBehaviours still contain em dashes: "
            f"{skipped_with_raw_em_dashes}"
        )

    report = {
        "format_version": 1,
        "base": {"path": str(args.base_bundle.resolve()), "sha256": sha256_file(args.base_bundle)},
        "output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
        },
        "changed_objects": len(changes),
        "replacement_count": sum(item["replacement_count"] for item in changes),
        "skipped_monobehaviours": skipped_monobehaviours,
        "skipped_monobehaviours_with_raw_em_dashes": skipped_with_raw_em_dashes,
        "remaining_player_facing_em_dashes": remaining,
        "changes": changes,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "output",
        "changed_objects",
        "replacement_count",
        "skipped_monobehaviours",
        "remaining_player_facing_em_dashes",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
