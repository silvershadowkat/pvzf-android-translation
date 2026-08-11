#!/usr/bin/env python3
"""Inventory a Unity bundle without exporting its large binary assets."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

import UnityPy


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    env = UnityPy.load(str(args.bundle))
    counts: collections.Counter[str] = collections.Counter()
    named: list[dict[str, object]] = []
    text_assets: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []

    for obj in env.objects:
        type_name = obj.type.name
        counts[type_name] += 1
        try:
            name = obj.peek_name()
        except Exception as exc:  # pragma: no cover - diagnostic path
            errors.append({"path_id": obj.path_id, "type": type_name, "error": repr(exc)})
            continue

        if name or type_name in {"TextAsset", "Font", "Texture2D", "Sprite", "MonoBehaviour"}:
            item: dict[str, object] = {
                "path_id": obj.path_id,
                "type": type_name,
                "name": name,
                "serialized_size": obj.byte_size,
            }
            named.append(item)

        if type_name == "TextAsset":
            try:
                data = obj.parse_as_object()
                raw = data.m_Script.encode("utf-8", "surrogateescape")
                text_assets.append(
                    {
                        "path_id": obj.path_id,
                        "name": data.m_Name,
                        "size": len(raw),
                        "sha256": sha256(raw),
                        "utf8_preview": raw[:500].decode("utf-8", "replace"),
                    }
                )
            except Exception as exc:  # pragma: no cover - diagnostic path
                errors.append({"path_id": obj.path_id, "type": type_name, "error": repr(exc)})

    report = {
        "unitypy_version": UnityPy.__version__,
        "bundle": str(args.bundle.resolve()),
        "bundle_size": args.bundle.stat().st_size,
        "object_count": sum(counts.values()),
        "object_types": dict(sorted(counts.items())),
        "files": sorted(env.files.keys()),
        "container_paths": sorted(env.container.keys()),
        "text_assets": text_assets,
        "named_objects": named,
        "errors": errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "object_count": report["object_count"],
        "object_types": report["object_types"],
        "text_asset_count": len(text_assets),
        "named_object_count": len(named),
        "error_count": len(errors),
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
