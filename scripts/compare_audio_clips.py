#!/usr/bin/env python3
"""Compare embedded Unity AudioClip payloads by name without exporting them."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import UnityPy
from UnityPy.helpers.ResourceReader import get_resource_data


def inventory(path: Path) -> dict[str, dict[str, object]]:
    env = UnityPy.load(str(path))
    clips: dict[str, dict[str, object]] = {}
    for obj in env.objects:
        if obj.type.name != "AudioClip":
            continue
        clip = obj.parse_as_object()
        resource = clip.m_Resource
        raw = get_resource_data(
            resource.m_Source,
            obj.assets_file,
            resource.m_Offset,
            resource.m_Size,
        )
        clips[clip.m_Name] = {
            "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "length_seconds": clip.m_Length,
            "channels": clip.m_Channels,
            "frequency": clip.m_Frequency,
        }
    return clips


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("bundles", nargs="+", type=Path)
    args = parser.parse_args()

    inventories = {path.parent.parent.parent.parent.name: inventory(path) for path in args.bundles}
    labels = list(inventories)
    reference = inventories[labels[0]]
    comparisons: dict[str, object] = {}
    for label in labels[1:]:
        current = inventories[label]
        shared = sorted(reference.keys() & current.keys())
        comparisons[f"{labels[0]}_vs_{label}"] = {
            "shared_count": len(shared),
            "identical_payload_count": sum(
                reference[name]["sha256"] == current[name]["sha256"] for name in shared
            ),
            "changed_payloads": [
                name for name in shared
                if reference[name]["sha256"] != current[name]["sha256"]
            ],
            "only_reference": sorted(reference.keys() - current.keys()),
            "only_current": sorted(current.keys() - reference.keys()),
        }

    report = {
        "bundles": {label: str(path.resolve()) for label, path in zip(labels, args.bundles)},
        "clip_counts": {label: len(items) for label, items in inventories.items()},
        "comparisons": comparisons,
        "clips": inventories,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "clip_counts": report["clip_counts"],
        "comparisons": comparisons,
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
