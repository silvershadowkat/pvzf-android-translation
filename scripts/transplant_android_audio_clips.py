#!/usr/bin/env python3
"""Transplant Android-encoded AudioClips into a same-version Unity bundle."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import ntpath
import shutil
from pathlib import Path

import UnityPy
from UnityPy.helpers.ResourceReader import get_resource_data


AUDIO_METADATA_FIELDS = (
    "m_LoadType",
    "m_Channels",
    "m_Frequency",
    "m_BitsPerSample",
    "m_Length",
    "m_IsTrackerFormat",
    "m_SubsoundIndex",
    "m_PreloadAudioData",
    "m_LoadInBackground",
    "m_Legacy3D",
    "m_CompressionFormat",
)


def sha256_bytes(value: bytes | bytearray | memoryview) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def audio_clips(env) -> dict[str, tuple[object, dict]]:
    result: dict[str, tuple[object, dict]] = {}
    duplicates = []
    for obj in env.objects:
        if obj.type.name != "AudioClip":
            continue
        tree = obj.read_typetree()
        name = tree["m_Name"]
        if name in result:
            duplicates.append(name)
        result[name] = (obj, tree)
    if duplicates:
        raise RuntimeError(f"duplicate AudioClip names: {sorted(set(duplicates))}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--base-resource", required=True, type=Path)
    parser.add_argument("--donor-bundle", required=True, type=Path)
    parser.add_argument("--mapping", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--output-resource", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--alignment", default=16, type=int)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    names = list(mapping["included"])
    if len(names) != len(set(names)) or not names:
        raise RuntimeError("audio mapping has duplicate or empty included names")
    if args.alignment <= 0 or args.alignment & (args.alignment - 1):
        raise ValueError("alignment must be a positive power of two")

    donor_env = UnityPy.load(str(args.donor_bundle))
    donor_index = audio_clips(donor_env)
    missing_donor = sorted(set(names) - set(donor_index))
    extra_donor = sorted(set(donor_index) - set(names))
    if missing_donor or extra_donor:
        raise RuntimeError(
            f"donor inventory differs from mapping: missing={missing_donor}, extra={extra_donor}"
        )
    donors = {}
    for name in names:
        obj, tree = donor_index[name]
        resource = tree["m_Resource"]
        payload = bytes(
            get_resource_data(
                resource["m_Source"],
                obj.assets_file,
                resource["m_Offset"],
                resource["m_Size"],
            )
        )
        if len(payload) != resource["m_Size"] or not payload:
            raise RuntimeError(f"invalid donor payload for {name}")
        donors[name] = {
            "metadata": {field: tree[field] for field in AUDIO_METADATA_FIELDS},
            "payload": payload,
            "payload_sha256": sha256_bytes(payload),
        }
    del donor_env, donor_index
    gc.collect()

    env = UnityPy.load(str(args.base_bundle))
    target_index = audio_clips(env)
    missing_target = sorted(set(names) - set(target_index))
    if missing_target:
        raise RuntimeError(f"target is missing mapped AudioClips: {missing_target}")

    untouched_audio = {
        (obj.assets_file.name, obj.path_id): sha256_bytes(obj.get_raw_data())
        for name, (obj, _) in target_index.items()
        if name not in names
    }
    if not args.base_resource.is_file():
        raise FileNotFoundError(f"missing target resource file: {args.base_resource}")
    resource_name = args.base_resource.name
    original_resource_size = args.base_resource.stat().st_size
    original_resource_hash = sha256_file(args.base_resource)
    resource_cursor = original_resource_size
    changes = []

    for name in names:
        obj, tree = target_index[name]
        donor = donors[name]
        target_source = tree["m_Resource"]["m_Source"]
        if ntpath.basename(target_source).lower() != resource_name.lower():
            raise RuntimeError(
                f"{name} references {target_source!r}, expected external {resource_name!r}"
            )
        padding = (-resource_cursor) % args.alignment
        resource_cursor += padding
        offset = resource_cursor
        payload = donor["payload"]
        resource_cursor += len(payload)

        before = {
            "file": obj.assets_file.name,
            "path_id": obj.path_id,
            "resource": dict(tree["m_Resource"]),
            "metadata": {field: tree[field] for field in AUDIO_METADATA_FIELDS},
        }
        for field, value in donor["metadata"].items():
            tree[field] = value
        tree["m_Resource"] = {
            "m_Source": target_source,
            "m_Offset": offset,
            "m_Size": len(payload),
        }
        obj.save_typetree(tree)
        changes.append(
            {
                "name": name,
                "before": before,
                "after": {
                    "resource_file": resource_name,
                    "resource": dict(tree["m_Resource"]),
                    "metadata": donor["metadata"],
                    "payload_sha256": donor["payload_sha256"],
                },
            }
        )

    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    del output_bytes, env, target_index
    gc.collect()

    args.output_resource.parent.mkdir(parents=True, exist_ok=True)
    with args.base_resource.open("rb") as reader, args.output_resource.open("wb") as writer:
        shutil.copyfileobj(reader, writer, length=8 * 1024 * 1024)
        for name in names:
            padding = (-writer.tell()) % args.alignment
            if padding:
                writer.write(b"\x00" * padding)
            writer.write(donors[name]["payload"])
    if args.output_resource.stat().st_size != resource_cursor:
        raise RuntimeError("external resource size differs from planned AudioClip offsets")

    check_env = UnityPy.load(str(args.output))
    check_index = audio_clips(check_env)
    with args.output_resource.open("rb") as resource_reader:
        for name in names:
            _, tree = check_index[name]
            donor = donors[name]
            for field, expected in donor["metadata"].items():
                if tree[field] != expected:
                    raise RuntimeError(f"reopened {name}.{field} differs from donor")
            resource = tree["m_Resource"]
            if ntpath.basename(resource["m_Source"]).lower() != resource_name.lower():
                raise RuntimeError(f"reopened source differs for {name}")
            resource_reader.seek(resource["m_Offset"])
            payload = resource_reader.read(resource["m_Size"])
            if sha256_bytes(payload) != donor["payload_sha256"]:
                raise RuntimeError(f"reopened external payload differs for {name}")

    for key, expected_hash in untouched_audio.items():
        matches = [
            obj for obj in check_env.objects
            if (obj.assets_file.name, obj.path_id) == key
        ]
        if len(matches) != 1 or sha256_bytes(matches[0].get_raw_data()) != expected_hash:
            raise RuntimeError(f"untouched AudioClip changed: {key}")

    prefix_digest = hashlib.sha256()
    remaining = original_resource_size
    with args.output_resource.open("rb") as handle:
        while remaining:
            chunk = handle.read(min(8 * 1024 * 1024, remaining))
            if not chunk:
                raise RuntimeError("output resource ended inside the original prefix")
            prefix_digest.update(chunk)
            remaining -= len(chunk)
    if prefix_digest.hexdigest() != original_resource_hash:
        raise RuntimeError("original external resource prefix changed")
    resource_reports = {
        resource_name: {
            "original_size": original_resource_size,
            "output_size": args.output_resource.stat().st_size,
            "appended_size": args.output_resource.stat().st_size - original_resource_size,
            "original_prefix_sha256": original_resource_hash,
            "output_sha256": sha256_file(args.output_resource),
        }
    }
    del check_env, check_index
    gc.collect()

    report = {
        "format_version": 1,
        "base": {"path": str(args.base_bundle.resolve()), "sha256": sha256_file(args.base_bundle)},
        "donor": {"path": str(args.donor_bundle.resolve()), "sha256": sha256_file(args.donor_bundle)},
        "mapping": {
            "path": str(args.mapping.resolve()),
            "sha256": sha256_file(args.mapping),
            "pc_branch": mapping.get("pc_branch"),
            "pc_commit": mapping.get("pc_commit"),
            "excluded": mapping.get("excluded", {}),
        },
        "output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
            "resource_path": str(args.output_resource.resolve()),
            "resource_size": args.output_resource.stat().st_size,
            "resource_sha256": sha256_file(args.output_resource),
        },
        "transplanted_clip_count": len(names),
        "untouched_audio_clip_count": len(untouched_audio),
        "resource_files": resource_reports,
        "changes": changes,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": report["output"],
                "transplanted_clip_count": report["transplanted_clip_count"],
                "untouched_audio_clip_count": report["untouched_audio_clip_count"],
                "resource_files": report["resource_files"],
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
