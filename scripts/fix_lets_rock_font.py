#!/usr/bin/env python3
"""Assign the exact LETS ROCK label a font containing the required glyphs.

The original Android font assigned to the plant-selection start button lacks
several Latin capitals. TextMeshPro therefore substitutes lookalike glyphs,
making ``LETS ROCK`` appear as ``L3TS R0CW``. This pass changes only that
single text component's font asset and shared material. The visible text is
left byte-for-byte unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator


TARGET_TEXT = "<size=20>LETS ROCK"
TARGET_FONT_NAME = "汉仪夏日体W SDF"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_generator(unity_version: str, dummy_dll_dir: Path) -> TypeTreeGenerator:
    generator = TypeTreeGenerator(unity_version)
    generator.load_local_dll_folder(str(dummy_dll_dir))
    return generator


def read_tree(obj: object) -> dict | None:
    try:
        return obj.read_typetree()
    except Exception:
        return None


def find_target(env: UnityPy.Environment) -> tuple[object, dict]:
    matches: list[tuple[object, dict]] = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        tree = read_tree(obj)
        if tree is not None and tree.get("m_text") == TARGET_TEXT:
            matches.append((obj, tree))
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one exact {TARGET_TEXT!r} component, found {len(matches)}"
        )
    return matches[0]


def find_font(env: UnityPy.Environment) -> tuple[object, dict]:
    matches: list[tuple[object, dict]] = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        tree = read_tree(obj)
        if tree is not None and tree.get("m_Name") == TARGET_FONT_NAME:
            matches.append((obj, tree))
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one exact {TARGET_FONT_NAME!r} font asset, found {len(matches)}"
        )
    return matches[0]


def pointer_path_id(value: object) -> int:
    if not isinstance(value, dict) or "m_PathID" not in value:
        raise RuntimeError(f"expected a Unity object pointer, got {value!r}")
    return int(value["m_PathID"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--dummy-dll-dir", type=Path, required=True)
    parser.add_argument("--unity-version", default="2021.3.45f1")
    args = parser.parse_args()

    generator = make_generator(args.unity_version, args.dummy_dll_dir)
    env = UnityPy.load(str(args.base_bundle))
    env.typetree_generator = generator

    target_obj, target_tree = find_target(env)
    font_obj, font_tree = find_font(env)
    material_path_id = pointer_path_id(font_tree.get("material"))

    before_font_path_id = pointer_path_id(target_tree.get("m_fontAsset"))
    before_material_path_id = pointer_path_id(target_tree.get("m_sharedMaterial"))

    target_tree["m_fontAsset"] = {"m_FileID": 0, "m_PathID": font_obj.path_id}
    target_tree["m_sharedMaterial"] = {
        "m_FileID": 0,
        "m_PathID": material_path_id,
    }
    target_tree["m_hasFontAssetChanged"] = 1
    target_obj.save_typetree(target_tree)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(env.file.save(packer="original"))

    check_generator = make_generator(args.unity_version, args.dummy_dll_dir)
    check_env = UnityPy.load(str(args.output))
    check_env.typetree_generator = check_generator
    check_obj, check_tree = find_target(check_env)
    check_font_obj, _ = find_font(check_env)

    actual_font_path_id = pointer_path_id(check_tree.get("m_fontAsset"))
    actual_material_path_id = pointer_path_id(check_tree.get("m_sharedMaterial"))
    if check_tree.get("m_text") != TARGET_TEXT:
        raise RuntimeError("LETS ROCK text changed during font reassignment")
    if actual_font_path_id != check_font_obj.path_id:
        raise RuntimeError("LETS ROCK font asset did not persist")
    if actual_material_path_id != material_path_id:
        raise RuntimeError("LETS ROCK shared material did not persist")

    report = {
        "base_bundle": str(args.base_bundle.resolve()),
        "base_sha256": sha256(args.base_bundle),
        "output": str(args.output.resolve()),
        "output_sha256": sha256(args.output),
        "target_text": TARGET_TEXT,
        "target_component_path_id": check_obj.path_id,
        "font_name": TARGET_FONT_NAME,
        "before_font_path_id": before_font_path_id,
        "after_font_path_id": actual_font_path_id,
        "before_material_path_id": before_material_path_id,
        "after_material_path_id": actual_material_path_id,
        "visible_text_unchanged": True,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
