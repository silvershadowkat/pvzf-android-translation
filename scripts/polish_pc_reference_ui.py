#!/usr/bin/env python3
"""Polish the static PC 3.9 reference without using Android assets or text.

The compatible 3.8.1 PC translator created a PC English font and resized text
at runtime.  Final 3.9 cannot load that DLL, so the static reference needs a
small serialized presentation pass.  This tool deliberately limits itself to
the PC OptionMenu hierarchy and a closed list of generic, user-approved PC UI
labels.  Gameplay terminology remains governed by upstream PC translations.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import re
import struct
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator


TEXT_OFFSET = 88
SIZE_TAG_RE = re.compile(r"</?size(?:=[^>]*)?>", re.IGNORECASE)

# These are generic controls, not gameplay names.  They are intentionally
# defined in this PC-only presentation pass rather than imported from Android.
REVIEWED_PC_GENERIC_UI = {
    181975: ("返回菜单", "Back to Menu"),
    184502: ("禁用屏幕抖动", "Disable Screen Shake"),
    187638: ("切换全屏1920*1080", "Toggle Fullscreen\n1920 × 1080"),
    190912: ("伤害跳字", "Damage Numbers"),
    195752: ("切换全屏1920*1080", "Toggle Fullscreen\n1920 × 1080"),
    196753: ("当前大小：5", "Current Zoom: 5"),
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


def read_tmp_text(raw: bytes) -> str | None:
    if len(raw) < TEXT_OFFSET + 4:
        return None
    size = struct.unpack_from("<i", raw, TEXT_OFFSET)[0]
    end = TEXT_OFFSET + 4 + size
    if size < 0 or end > len(raw):
        return None
    try:
        value = raw[TEXT_OFFSET + 4 : end].decode("utf-8")
    except UnicodeDecodeError:
        return None
    padded_end = (end + 3) & ~3
    if padded_end > len(raw) or any(raw[end:padded_end]):
        return None
    return value


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


def hierarchy_for_component(objects, key: tuple[str, int]) -> list[str]:
    raw = bytes(objects[key].get_raw_data())
    game_object_id = struct.unpack_from("<q", raw, 4)[0]
    transform = transform_for_game_object(objects, key[0], game_object_id)
    names: list[str] = []
    seen: set[int] = set()
    while transform is not None and transform.path_id not in seen and len(names) < 16:
        seen.add(transform.path_id)
        data = transform.read()
        names.append(game_object_name(objects, key[0], data.m_GameObject.path_id))
        father_id = getattr(data.m_Father, "path_id", 0)
        transform = objects.get((key[0], father_id)) if father_id else None
    return names


def set_fit_fields(tree: dict, minimum: float, maximum: float) -> dict:
    before = {
        "font_size": tree.get("m_fontSize"),
        "font_size_min": tree.get("m_fontSizeMin"),
        "font_size_max": tree.get("m_fontSizeMax"),
        "auto_sizing": tree.get("m_enableAutoSizing"),
        "word_wrapping": tree.get("m_enableWordWrapping"),
    }
    tree["m_enableAutoSizing"] = 1
    tree["m_enableWordWrapping"] = 1
    tree["m_fontSizeMin"] = float(minimum)
    tree["m_fontSizeMax"] = float(maximum)
    if float(tree.get("m_fontSize", maximum)) > maximum:
        tree["m_fontSize"] = float(maximum)
    return before


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--dummy-dll-dir", required=True, type=Path)
    parser.add_argument("--unity-version", default="2022.3.62f1")
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    generator = make_generator(args.unity_version, args.dummy_dll_dir)
    env = UnityPy.load(str(args.base_bundle))
    env.typetree_generator = generator
    objects = object_map(env)

    changes: list[dict] = []
    expected: dict[tuple[str, int], dict] = {}
    seen_reviewed: set[int] = set()

    for key, obj in sorted(objects.items()):
        if obj.type.name != "MonoBehaviour":
            continue
        source_text = read_tmp_text(bytes(obj.get_raw_data()))
        if source_text is None:
            continue
        hierarchy = hierarchy_for_component(objects, key)
        if not hierarchy or hierarchy[-1] != "OptionMenu":
            continue
        try:
            tree = obj.read_typetree(check_read=False)
        except Exception:
            continue
        if "m_text" not in tree or "m_fontSize" not in tree:
            continue

        target_text = source_text
        method = None
        if obj.path_id in REVIEWED_PC_GENERIC_UI:
            wanted_source, target_text = REVIEWED_PC_GENERIC_UI[obj.path_id]
            if source_text != wanted_source:
                raise RuntimeError(
                    f"reviewed PC UI source changed at {obj.path_id}: "
                    f"{source_text!r} != {wanted_source!r}"
                )
            seen_reviewed.add(obj.path_id)
            method = "reviewed_pc_generic_ui"

        is_toggle_label = (
            hierarchy[0] == "Label"
            and "ToggleView" in hierarchy
            and "Viewport" in hierarchy
            and "Content" in hierarchy
        )
        is_option_button_text = "Buttons" in hierarchy and hierarchy[0] in {
            "text", "text2", "text_1", "text_2"
        }
        is_back_button = "Goback" in hierarchy and hierarchy[0] == "text"
        if not (is_toggle_label or is_option_button_text or is_back_button):
            continue

        if is_option_button_text:
            target_text = SIZE_TAG_RE.sub("", target_text)
            before_layout = set_fit_fields(tree, 8.0, 14.0)
            method = method or "pc_option_button_autofit"
        elif is_back_button:
            before_layout = set_fit_fields(tree, 16.0, 32.0)
            method = method or "pc_back_button_autofit"
        else:
            before_layout = set_fit_fields(tree, 18.0, 36.0)
            method = method or "pc_setting_label_autofit"

        tree["m_text"] = target_text
        obj.save_typetree(tree)
        record = {
            "file": key[0],
            "path_id": obj.path_id,
            "hierarchy": hierarchy,
            "source": source_text,
            "text": target_text,
            "method": method,
            "before_layout": before_layout,
            "after_layout": {
                "font_size": tree.get("m_fontSize"),
                "font_size_min": tree.get("m_fontSizeMin"),
                "font_size_max": tree.get("m_fontSizeMax"),
                "auto_sizing": tree.get("m_enableAutoSizing"),
                "word_wrapping": tree.get("m_enableWordWrapping"),
            },
        }
        changes.append(record)
        expected[key] = record

    missing_reviewed = set(REVIEWED_PC_GENERIC_UI) - seen_reviewed
    if missing_reviewed:
        raise RuntimeError(f"reviewed PC UI components not found: {sorted(missing_reviewed)}")

    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    del output_bytes, env, objects
    gc.collect()

    check_generator = make_generator(args.unity_version, args.dummy_dll_dir)
    check_env = UnityPy.load(str(args.output))
    check_env.typetree_generator = check_generator
    check_objects = object_map(check_env)
    validated = 0
    for key, record in expected.items():
        tree = check_objects[key].read_typetree(check_read=False)
        if tree.get("m_text") != record["text"]:
            raise RuntimeError(f"PC presentation text validation failed for {key}")
        after = record["after_layout"]
        if (
            tree.get("m_enableAutoSizing") != after["auto_sizing"]
            or tree.get("m_enableWordWrapping") != after["word_wrapping"]
            or tree.get("m_fontSizeMin") != after["font_size_min"]
            or tree.get("m_fontSizeMax") != after["font_size_max"]
        ):
            raise RuntimeError(f"PC presentation layout validation failed for {key}")
        validated += 1
    del check_env, check_objects
    gc.collect()

    report = {
        "format_version": 1,
        "translation_mode": "pc_presentation",
        "android_inputs_used": False,
        "base": {
            "path": str(args.base_bundle.resolve()),
            "sha256": sha256_file(args.base_bundle),
        },
        "output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
        },
        "reviewed_generic_ui_count": len(seen_reviewed),
        "validated_component_count": validated,
        "changes": changes,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "output", "android_inputs_used", "reviewed_generic_ui_count",
        "validated_component_count"
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
