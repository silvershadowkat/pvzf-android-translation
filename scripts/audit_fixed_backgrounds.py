#!/usr/bin/env python3
"""Inventory fixed-size Unity UI backgrounds without modifying the bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--dummy-dll-dir", required=True, type=Path)
    parser.add_argument("--unity-version", default="2022.3.62f1")
    parser.add_argument("--width", default=1920.0, type=float)
    parser.add_argument("--height", default=1080.0, type=float)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    generator = TypeTreeGenerator(args.unity_version)
    generator.load_local_dll_folder(str(args.dummy_dll_dir))
    env = UnityPy.load(str(args.bundle))
    env.typetree_generator = generator
    objects = {(obj.assets_file.name, obj.path_id): obj for obj in env.objects}

    def name_for(file_name: str, game_object_id: int) -> str:
        return objects[(file_name, game_object_id)].read_typetree().get("m_Name", "")

    def hierarchy_for(file_name: str, transform_id: int) -> list[dict]:
        hierarchy = []
        current_id = transform_id
        while current_id and len(hierarchy) < 32:
            tree = objects[(file_name, current_id)].read_typetree()
            hierarchy.append(
                {
                    "transform_path_id": current_id,
                    "name": name_for(file_name, tree["m_GameObject"]["m_PathID"]),
                    "anchor_min": tree.get("m_AnchorMin"),
                    "anchor_max": tree.get("m_AnchorMax"),
                    "anchored_position": tree.get("m_AnchoredPosition"),
                    "size_delta": tree.get("m_SizeDelta"),
                }
            )
            current_id = tree.get("m_Father", {}).get("m_PathID")
        return hierarchy

    matches = []
    for obj in env.objects:
        if obj.type.name != "RectTransform":
            continue
        try:
            tree = obj.read_typetree()
            size = tree.get("m_SizeDelta") or {}
            if (
                abs(float(size.get("x", 0.0)) - args.width) > 0.01
                or abs(float(size.get("y", 0.0)) - args.height) > 0.01
            ):
                continue
            file_name = obj.assets_file.name
            game_object_name = name_for(file_name, tree["m_GameObject"]["m_PathID"])
            if game_object_name.lower() not in {"background", "bg"}:
                continue
            matches.append(
                {
                    "asset_file": file_name,
                    "rect_transform_path_id": obj.path_id,
                    "hierarchy": hierarchy_for(file_name, obj.path_id),
                }
            )
        except Exception:
            # A malformed/unresolved object is not evidence that it is safe to
            # rewrite. Leave it out and keep this tool read-only.
            continue

    payload = {
        "format_version": 1,
        "bundle": str(args.bundle.resolve()),
        "fixed_size": {"width": args.width, "height": args.height},
        "match_count": len(matches),
        "matches": matches,
        "policy": (
            "Inventory only. Dimensions do not establish that a background is safe to stretch; "
            "confirm the menu hierarchy and an observed ultrawide defect first."
        ),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(args.report.resolve()), "match_count": len(matches)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
