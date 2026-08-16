#!/usr/bin/env python3
"""Refine Almanac text components after the TMP font transplant.

The Android bundle assigns its long, scrolling Almanac descriptions to
the Chinese handwriting TMP asset even when the rest of the UI uses Dynamic.
That produces oversized Latin text after translation.  This pass retargets
only those three description components to Dynamic, gives all three detail
panels a small readable left inset, and normalizes the one outlier title size,
leaving every other translated component untouched.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator


TARGET_HIERARCHIES = {
    "modifier description": ("Description", "Content", "Viewport", "InroduceScroll", "Window", "AlmanacBuffMenu"),
    "plant description": ("Description", "Content", "Viewport", "InroduceScroll", "Window", "AlmanacPlantMenu"),
    "zombie description": ("Description", "Content", "Viewport", "InroduceScroll", "Window", "AlmanacZombieMenu"),
    "modifier layout": ("Content", "Viewport", "InroduceScroll", "Window", "AlmanacBuffMenu"),
    "plant title": ("Name", "Background", "AlmanacPlantMenu"),
    "mechanics description": ("MainText", "RightShow", "AlmanacSelectMenu"),
}


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


def game_object_name(objects, file_name: str, path_id: int) -> str:
    obj = objects.get((file_name, path_id))
    if obj is None:
        return ""
    try:
        return obj.read().m_Name
    except Exception:
        return ""


def transform_for_game_object(objects, file_name: str, game_object_id: int):
    game_object = objects.get((file_name, game_object_id))
    if game_object is None:
        return None
    try:
        components = game_object.read().m_Component
    except Exception:
        return None
    for item in components:
        pointer = getattr(item, "component", item)
        obj = objects.get((file_name, getattr(pointer, "path_id", 0)))
        if obj is not None and obj.type.name in ("Transform", "RectTransform"):
            return obj
    return None


def hierarchy_for_component(objects, key: tuple[str, int]) -> tuple[str, ...]:
    raw = bytes(objects[key].get_raw_data())
    if len(raw) < 12:
        return ()
    game_object_id = int.from_bytes(raw[4:12], "little", signed=True)
    transform = transform_for_game_object(objects, key[0], game_object_id)
    names = []
    seen = set()
    while transform is not None and transform.path_id not in seen and len(names) < 16:
        seen.add(transform.path_id)
        data = transform.read()
        names.append(game_object_name(objects, key[0], data.m_GameObject.path_id))
        father_id = getattr(data.m_Father, "path_id", 0)
        transform = objects.get((key[0], father_id)) if father_id else None
    return tuple(names)


def find_component_by_hierarchy(objects, hierarchy: tuple[str, ...], required_field: str):
    matches = []
    for key, obj in objects.items():
        if obj.type.name != "MonoBehaviour" or hierarchy_for_component(objects, key) != hierarchy:
            continue
        try:
            tree = obj.read_typetree(check_read=False)
        except Exception:
            continue
        if required_field in tree:
            matches.append((obj, tree))
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one {required_field} component at hierarchy {hierarchy!r}, "
            f"found {len(matches)}"
        )
    return matches[0]


def mono_name(obj) -> str:
    raw = bytes(obj.get_raw_data())
    size = int.from_bytes(raw[28:32], "little", signed=True)
    return raw[32 : 32 + size].decode("utf-8")


def find_named_mono(objects, name: str):
    matches = [obj for obj in objects.values() if obj.type.name == "MonoBehaviour" and mono_name(obj) == name]
    if len(matches) != 1:
        raise RuntimeError(f"expected one MonoBehaviour named {name!r}, found {len(matches)}")
    return matches[0]


def find_named_material(objects, name: str):
    matches = []
    for obj in objects.values():
        if obj.type.name != "Material":
            continue
        if obj.read_typetree()["m_Name"] == name:
            matches.append(obj)
    if len(matches) != 1:
        raise RuntimeError(f"expected one Material named {name!r}, found {len(matches)}")
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
    parser.add_argument("--modifier-description-size", default=20.0, type=float)
    parser.add_argument("--modifier-hidden-title-line", default=23, type=int)
    parser.add_argument("--modifier-description-left-inset", default=8.0, type=float)
    parser.add_argument("--entity-description-left-inset", default=8.0, type=float)
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
    clean_dynamic_material = find_named_material(objects, "Dynamic_light")
    outlined_dynamic_material = find_named_material(objects, "Dynamic_underLay")

    description_components = {}
    description_trees = {}
    for label in ("modifier description", "plant description", "zombie description"):
        obj, tree = find_component_by_hierarchy(objects, TARGET_HIERARCHIES[label], "m_fontAsset")
        description_components[obj.path_id] = label
        description_trees[obj.path_id] = tree
    entity_description_components = {
        path_id for path_id, label in description_components.items()
        if label in {"plant description", "zombie description"}
    }
    modifier_description_component = next(
        path_id for path_id, label in description_components.items()
        if label == "modifier description"
    )
    layout_obj, layout_tree = find_component_by_hierarchy(
        objects, TARGET_HIERARCHIES["modifier layout"], "m_Padding"
    )
    plant_title_obj, plant_title_tree = find_component_by_hierarchy(
        objects, TARGET_HIERARCHIES["plant title"], "m_fontAsset"
    )
    mechanics_obj, mechanics_tree = find_component_by_hierarchy(
        objects, TARGET_HIERARCHIES["mechanics description"], "m_fontAsset"
    )

    changes = []
    for path_id, label in description_components.items():
        obj = objects[("resources.assets", path_id)]
        tree = description_trees[path_id]
        require_pointer(tree, "m_fontAsset", handwriting_font.path_id, label)
        before = {
            "font_asset_path_id": tree["m_fontAsset"]["m_PathID"],
            "shared_material_path_id": tree["m_sharedMaterial"]["m_PathID"],
            "font_size": tree["m_fontSize"],
            "font_size_base": tree["m_fontSizeBase"],
            "margin": dict(tree["m_margin"]),
        }
        tree["m_fontAsset"] = {"m_FileID": 0, "m_PathID": dynamic_font.path_id}
        tree["m_sharedMaterial"] = {"m_FileID": 0, "m_PathID": dynamic_material_id}
        target_size = (
            args.modifier_description_size
            if path_id == modifier_description_component
            else args.description_size
        )
        tree["m_fontSize"] = target_size
        tree["m_fontSizeBase"] = target_size
        tree["m_enableAutoSizing"] = 0
        tree["m_fontSizeMin"] = min(target_size, tree["m_fontSizeMin"])
        if path_id == modifier_description_component:
            tree["m_margin"]["x"] = args.modifier_description_left_inset
        elif path_id in entity_description_components:
            tree["m_margin"]["x"] = args.entity_description_left_inset
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
                    "font_size": target_size,
                    "font_size_base": target_size,
                    "margin": dict(tree["m_margin"]),
                },
            }
        )

    # The Android game needs `name：` at the start of each modifier string to
    # derive the short card/title label, but it also assigns that entire string
    # to this masked scrolling description. The metadata builder puts the name
    # on a dedicated first line. A matching negative top padding places exactly
    # that metadata line above the viewport while preserving the Content Size
    # Fitter's height for the visible description and normal scrolling.
    layout_before = dict(layout_tree["m_Padding"])
    layout_tree["m_Padding"]["m_Top"] = -args.modifier_hidden_title_line
    layout_obj.save_typetree(layout_tree)
    changes.append(
        {
            "component": "modifier description hidden metadata line",
            "path_id": layout_obj.path_id,
            "before": {"padding": layout_before},
            "after": {"padding_top": -args.modifier_hidden_title_line},
        }
    )

    require_pointer(plant_title_tree, "m_fontAsset", dynamic_font.path_id, "plant title")
    old_title_size = plant_title_tree["m_fontSize"]
    plant_title_tree["m_fontSize"] = args.plant_title_size
    plant_title_tree["m_fontSizeBase"] = args.plant_title_size
    plant_title_tree["m_enableAutoSizing"] = 0
    plant_title_obj.save_typetree(plant_title_tree)
    changes.append(
        {
            "component": "plant title",
            "path_id": plant_title_obj.path_id,
            "before": {"font_size": old_title_size},
            "after": {"font_size": args.plant_title_size},
        }
    )

    # Every Mechanics Almanac page reuses this one TMP component. Android's
    # Dynamic_underLay material adds a large, opaque black underlay which is
    # tolerable around white text but overwhelms the smaller blue rich-text
    # emphasis. Dynamic_light uses the same Dynamic atlas with the restrained
    # treatment used elsewhere, so wording, colors, bold tags, wrapping, and
    # font metrics remain unchanged.
    require_pointer(
        mechanics_tree,
        "m_sharedMaterial",
        outlined_dynamic_material.path_id,
        "Mechanics Almanac description",
    )
    mechanics_before = {
        "shared_material_path_id": mechanics_tree["m_sharedMaterial"]["m_PathID"],
        "font_asset_path_id": mechanics_tree["m_fontAsset"]["m_PathID"],
        "font_size": mechanics_tree["m_fontSize"],
    }
    mechanics_tree["m_sharedMaterial"] = {
        "m_FileID": 0,
        "m_PathID": clean_dynamic_material.path_id,
    }
    mechanics_obj.save_typetree(mechanics_tree)
    changes.append(
        {
            "component": "Mechanics Almanac shared description",
            "path_id": mechanics_obj.path_id,
            "before": mechanics_before,
            "after": {
                **mechanics_before,
                "shared_material_path_id": clean_dynamic_material.path_id,
            },
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
    for path_id, label in description_components.items():
        tree = check_objects[("resources.assets", path_id)].read_typetree(check_read=False)
        require_pointer(tree, "m_fontAsset", dynamic_font.path_id, label)
        require_pointer(tree, "m_sharedMaterial", dynamic_material_id, label)
        target_size = (
            args.modifier_description_size
            if path_id == modifier_description_component
            else args.description_size
        )
        if tree["m_fontSize"] != target_size:
            raise RuntimeError(f"{label} font-size validation failed")
        expected_left_margin = (
            args.modifier_description_left_inset
            if path_id == modifier_description_component
            else args.entity_description_left_inset
        )
        if tree["m_margin"]["x"] != expected_left_margin:
            raise RuntimeError(f"{label} left-margin validation failed")
    layout_tree = check_objects[
        ("resources.assets", layout_obj.path_id)
    ].read_typetree(check_read=False)
    if layout_tree["m_Padding"]["m_Top"] != -args.modifier_hidden_title_line:
        raise RuntimeError("modifier description hidden-line validation failed")
    title_tree = check_objects[("resources.assets", plant_title_obj.path_id)].read_typetree(check_read=False)
    if title_tree["m_fontSize"] != args.plant_title_size:
        raise RuntimeError("plant title font-size validation failed")
    mechanics_tree = check_objects[
        ("resources.assets", mechanics_obj.path_id)
    ].read_typetree(check_read=False)
    require_pointer(
        mechanics_tree,
        "m_sharedMaterial",
        clean_dynamic_material.path_id,
        "Mechanics Almanac description",
    )
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
