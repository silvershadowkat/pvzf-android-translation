#!/usr/bin/env python3
"""Overlay TextAssets from one same-version bundle onto another by stable ID."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import re
from pathlib import Path

import UnityPy


SIZE_TAG_RE = re.compile(r"</?size(?:=[^>]*)?>", re.IGNORECASE)
ANDROID_ALMANAC_ASSETS = {"LawnStrings", "ZombieStrings"}
EM_DASH = "\u2014"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def text_assets(env) -> dict[tuple[str, int], tuple[str, str]]:
    records = {}
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.parse_as_object()
        records[(obj.assets_file.name, obj.path_id)] = (data.m_Name, data.m_Script)
    return records


def normalize_android_almanac_text_asset(name: str, script: str) -> tuple[str, int]:
    """Remove PC-only TMP size overrides from Android entity Almanacs."""
    if name not in ANDROID_ALMANAC_ASSETS:
        return script, 0
    normalized, count = SIZE_TAG_RE.subn("", script)
    # Fail before writing if normalization exposed malformed JSON.
    json.loads(normalized.lstrip("\ufeff"))
    return normalized, count


def normalize_overlay_text_asset(name: str, script: str) -> tuple[str, int, int]:
    script, size_tag_count = normalize_android_almanac_text_asset(name, script)
    em_dash_count = script.count(EM_DASH)
    if em_dash_count:
        script = script.replace(EM_DASH, "-")
    return script, size_tag_count, em_dash_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--source-bundle", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    source_env = UnityPy.load(str(args.source_bundle))
    source = text_assets(source_env)
    del source_env
    gc.collect()

    normalized_source = {}
    almanac_size_tags_removed = {}
    em_dashes_replaced = {}
    for key, (name, script) in source.items():
        script, removed, dash_count = normalize_overlay_text_asset(name, script)
        if dash_count:
            em_dashes_replaced[name] = dash_count
        normalized_source[key] = (name, script)
        if removed:
            almanac_size_tags_removed[name] = removed
    source = normalized_source

    env = UnityPy.load(str(args.base_bundle))
    base = text_assets(env)
    if set(base) != set(source):
        raise RuntimeError(
            "TextAsset inventory mismatch: "
            f"base_only={sorted(set(base) - set(source))}, "
            f"source_only={sorted(set(source) - set(base))}"
        )

    changed = []
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        key = (obj.assets_file.name, obj.path_id)
        current = base[key]
        replacement = source[key]
        if current == replacement:
            continue
        data = obj.parse_as_object()
        data.m_Name, data.m_Script = replacement
        obj.save_typetree(data)
        changed.append(
            {
                "file": key[0],
                "path_id": key[1],
                "name": replacement[0],
                "name_changed": current[0] != replacement[0],
                "script_changed": current[1] != replacement[1],
            }
        )

    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    del output_bytes, env
    gc.collect()

    check_env = UnityPy.load(str(args.output))
    reopened = text_assets(check_env)
    del check_env
    if reopened != source:
        mismatches = sorted(key for key in source if reopened.get(key) != source[key])
        raise RuntimeError(f"reopened TextAsset validation failed: {mismatches}")
    remaining_size_tags = {
        name: len(SIZE_TAG_RE.findall(script))
        for name, script in reopened.values()
        if name in ANDROID_ALMANAC_ASSETS and SIZE_TAG_RE.search(script)
    }
    if remaining_size_tags:
        raise RuntimeError(f"Android Almanac size tags remain: {remaining_size_tags}")

    report = {
        "format_version": 1,
        "base": {"path": str(args.base_bundle.resolve()), "sha256": sha256_file(args.base_bundle)},
        "source": {"path": str(args.source_bundle.resolve()), "sha256": sha256_file(args.source_bundle)},
        "output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
        },
        "validated_text_assets": len(source),
        "changed_text_assets": len(changed),
        "almanac_size_tags_removed": almanac_size_tags_removed,
        "remaining_almanac_size_tags": 0,
        "text_asset_em_dashes_replaced": em_dashes_replaced,
        "remaining_text_asset_em_dashes": 0,
        "changes": changed,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": report["output"],
                "validated_text_assets": report["validated_text_assets"],
                "changed_text_assets": report["changed_text_assets"],
                "almanac_size_tags_removed": report["almanac_size_tags_removed"],
                "remaining_almanac_size_tags": report["remaining_almanac_size_tags"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
