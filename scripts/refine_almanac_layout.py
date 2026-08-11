#!/usr/bin/env python3
"""Refine the 3.8.1 Almanac text components after the TMP font transplant.

The 3.8.1 Android bundle assigns its long, scrolling Almanac descriptions to
the Chinese handwriting TMP asset even when the rest of the UI uses Dynamic.
That produces oversized Latin text after translation.  This pass retargets
only those three description components to Dynamic and normalizes the one
outlier title size, leaving every other translated component untouched.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator


DESCRIPTION_COMPONENTS = {
    187255: "modifier description",
    193273: "plant description",
    194141: "zombie description",
}
PLANT_TITLE_COMPONENT = 191011


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def make_generator(unity_version: str, dummy_dll_dir: Path) -> TypeTreeGenerator:
    generator = TypeTreeGenerator(unity_version)
    generator.load_local_dll_folder(str(dummy_dll_dir))
    return generator


def object_map(env):
    return {(obj.assets_file.name, obj.path_id): obj for obj in env.objects}


def mono_name(obj) -> str:
    raw = bytes(obj.get_raw_data())
    size = int.from_bytes(raw[28:32], "little", signed=True)
    return raw[32 : 32 + size].decode("utf-8")


def find_named_mono(objects, name: str):
    matches = [obj for obj in objects.values() if obj.type.name == "MonoBehaviour" and mono_name(obj) == name]
    if len(matches) != 1:
        raise RuntimeError(f"expected one MonoBehaviour named {name!r}, found {len(matches)}")
    return matches[0]


def require_pointer(tree: dict, field: str, expected_path_id: int, component: str) -> None:
    actual = tree[field]["m_PathID"]
    if actual != expected_path_id:
        raise RuntimeError(
            f"{component} has unexpected {field} path ID {actual}; expected {expected_path_id}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--dummy-dll-dir", required=True, type=Path)
    parser.add_argument("--unity-version", default="2022.3.62f1")
    parser.add_argument("--dynamic-font-asset", default="Dynamic")
    parser.add_argument("--handwriting-font-asset", default="汉仪夏日体W SDF")
    parser.add_argument("--description-size", default=18.0, type=float)
    parser.add_argument("--plant-title-size", default=50.0, type=float)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    generator = make_generator(args.unity_version, args.dummy_dll_dir)
    env = UnityPy.load(str(args.base_bundle))
    env.typetree_generator = generator
    objects = object_map(env)

    dynamic_font = find_named_mono(objects, args.dynamic_font_asset)
    handwriting_font = find_named_mono(objects, args.handwriting_font_asset)
    dynamic_font_tree = dynamic_font.read_typetree(check_read=False)
    dynamic_material_id = dynamic_font_tree["material"]["m_PathID"]

    changes = []
    for path_id, label in DESCRIPTION_COMPONENTS.items():
        obj = objects[("resources.assets", path_id)]
        tree = obj.read_typetree(check_read=False)
        require_pointer(tree, "m_fontAsset", handwriting_font.path_id, label)
        before = {
            "font_asset_path_id": tree["m_fontAsset"]["m_PathID"],
            "shared_material_path_id": tree["m_sharedMaterial"]["m_PathID"],
            "font_size": tree["m_fontSize"],
            "font_size_base": tree["m_fontSizeBase"],
        }
        tree["m_fontAsset"] = {"m_FileID": 0, "m_PathID": dynamic_font.path_id}
        tree["m_sharedMaterial"] = {"m_FileID": 0, "m_PathID": dynamic_material_id}
        tree["m_fontSize"] = args.description_size
        tree["m_fontSizeBase"] = args.description_size
        tree["m_enableAutoSizing"] = 0
        tree["m_fontSizeMin"] = min(args.description_size, tree["m_fontSizeMin"])
        tree["m_hasFontAssetChanged"] = 1
        obj.save_typetree(tree)
        changes.append(
            {
                "component": label,
                "path_id": path_id,
                "before": before,
                "after": {
                    "font_asset_path_id": dynamic_font.path_id,
                    "shared_material_path_id": dynamic_material_id,
                    "font_size": args.description_size,
                    "font_size_base": args.description_size,
                },
            }
        )

    title_obj = objects[("resources.assets", PLANT_TITLE_COMPONENT)]
    title_tree = title_obj.read_typetree(check_read=False)
    require_pointer(title_tree, "m_fontAsset", dynamic_font.path_id, "plant title")
    old_title_size = title_tree["m_fontSize"]
    title_tree["m_fontSize"] = args.plant_title_size
    title_tree["m_fontSizeBase"] = args.plant_title_size
    title_tree["m_enableAutoSizing"] = 0
    title_obj.save_typetree(title_tree)
    changes.append(
        {
            "component": "plant title",
            "path_id": PLANT_TITLE_COMPONENT,
            "before": {"font_size": old_title_size},
            "after": {"font_size": args.plant_title_size},
        }
    )

    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    del output_bytes, env
    gc.collect()

    check_generator = make_generator(args.unity_version, args.dummy_dll_dir)
    check_env = UnityPy.load(str(args.output))
    check_env.typetree_generator = check_generator
    check_objects = object_map(check_env)
    for path_id, label in DESCRIPTION_COMPONENTS.items():
        tree = check_objects[("resources.assets", path_id)].read_typetree(check_read=False)
        require_pointer(tree, "m_fontAsset", dynamic_font.path_id, label)
        require_pointer(tree, "m_sharedMaterial", dynamic_material_id, label)
        if tree["m_fontSize"] != args.description_size:
            raise RuntimeError(f"{label} font-size validation failed")
    title_tree = check_objects[("resources.assets", PLANT_TITLE_COMPONENT)].read_typetree(check_read=False)
    if title_tree["m_fontSize"] != args.plant_title_size:
        raise RuntimeError("plant title font-size validation failed")
    del check_env
    gc.collect()

    report = {
        "format_version": 1,
        "base": {"path": str(args.base_bundle.resolve()), "sha256": sha256_file(args.base_bundle)},
        "output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
        },
        "changes": changes,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": report["output"], "changes": changes}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
