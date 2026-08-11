#!/usr/bin/env python3
"""Replace target Unity Font payloads with donor font data while preserving object IDs."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path

import UnityPy


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def font_objects(env):
    result = {}
    for obj in env.objects:
        if obj.type.name != "Font":
            continue
        data = obj.read()
        result[data.m_Name] = (obj, data)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--donor-bundle", required=True, type=Path)
    parser.add_argument("--map", action="append", required=True, metavar="TARGET=DONOR")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    mappings = []
    for value in args.map:
        if "=" not in value:
            parser.error(f"invalid --map value: {value}")
        mappings.append(tuple(value.split("=", 1)))

    env = UnityPy.load(str(args.base_bundle))
    donor_env = UnityPy.load(str(args.donor_bundle))
    targets = font_objects(env)
    donors = font_objects(donor_env)
    expected = {}
    changes = []

    for target_name, donor_name in mappings:
        if target_name not in targets:
            raise KeyError(f"target Font not found: {target_name}")
        if donor_name not in donors:
            raise KeyError(f"donor Font not found: {donor_name}")
        target_obj, target_data = targets[target_name]
        _donor_obj, donor_data = donors[donor_name]
        old_data = bytes(target_data.m_FontData)
        new_data = bytes(donor_data.m_FontData)
        target_data.m_FontData = new_data
        target_obj.save_typetree(target_data)
        key = (target_obj.assets_file.name, target_obj.path_id)
        expected[key] = (target_name, sha256(new_data))
        changes.append({
            "file": key[0],
            "path_id": key[1],
            "target_font": target_name,
            "donor_font": donor_name,
            "old_font_data_size": len(old_data),
            "new_font_data_size": len(new_data),
            "old_font_data_sha256": sha256(old_data),
            "new_font_data_sha256": sha256(new_data),
        })

    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    del output_bytes, env, donor_env
    gc.collect()

    check_env = UnityPy.load(str(args.output))
    validated = 0
    for obj in check_env.objects:
        key = (obj.assets_file.name, obj.path_id)
        if key not in expected:
            continue
        name, expected_hash = expected[key]
        data = obj.read()
        if data.m_Name != name or sha256(bytes(data.m_FontData)) != expected_hash:
            raise RuntimeError(f"Font validation failed for {key}")
        validated += 1
    if validated != len(expected):
        raise RuntimeError(f"validated {validated} of {len(expected)} Font objects")
    del check_env
    gc.collect()

    report = {
        "format_version": 1,
        "base": {"path": str(args.base_bundle.resolve()), "sha256": sha256_file(args.base_bundle)},
        "donor": {"path": str(args.donor_bundle.resolve()), "sha256": sha256_file(args.donor_bundle)},
        "output": {"path": str(args.output.resolve()), "size": args.output.stat().st_size, "sha256": sha256_file(args.output)},
        "validated_fonts": validated,
        "changes": changes,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("output", "validated_fonts", "changes")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
