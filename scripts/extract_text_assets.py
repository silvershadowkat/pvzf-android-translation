#!/usr/bin/env python3
"""Extract selected TextAsset payloads from a Unity bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import UnityPy


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("names", nargs="*")
    args = parser.parse_args()

    wanted = set(args.names)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    env = UnityPy.load(str(args.bundle))
    manifest: list[dict[str, object]] = []

    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.parse_as_object()
        if wanted and data.m_Name not in wanted:
            continue
        raw = data.m_Script.encode("utf-8", "surrogateescape")
        suffix = ".json" if raw.lstrip().startswith((b"{", b"[")) else ".txt"
        out = args.output_dir / f"{data.m_Name}{suffix}"
        out.write_bytes(raw)
        manifest.append({"name": data.m_Name, "path_id": obj.path_id, "size": len(raw), "output": out.name})

    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
