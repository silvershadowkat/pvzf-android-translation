#!/usr/bin/env python3
"""Patch serialized TextMesh Pro strings without changing UI layout or fonts."""

from __future__ import annotations

import argparse
import collections
import gc
import hashlib
import json
import re
import struct
from pathlib import Path

import UnityPy


CJK_RE = re.compile(r"[\u3400-\u9fff]")
TEXT_OFFSET = 88
ANDROID_RUNTIME_BACKING_EXACT = {
    "返回菜单": "Back to Menu",
    "上一页": "Previous Page",
    "下一页": "Next Page",
    "回到索引": "Back to Index",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_tmp_text(raw: bytes) -> tuple[str, int] | None:
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
    return value, padded_end


def replace_tmp_text(raw: bytes, value: str) -> bytes:
    parsed = read_tmp_text(raw)
    if parsed is None:
        raise ValueError("object does not contain a supported TMP text field")
    _old, old_end = parsed
    encoded = value.encode("utf-8")
    field = struct.pack("<i", len(encoded)) + encoded
    field += b"\0" * ((-len(field)) & 3)
    return raw[:TEXT_OFFSET] + field + raw[old_end:]


def serialized_string(value: str) -> bytes:
    encoded = value.encode("utf-8")
    field = struct.pack("<i", len(encoded)) + encoded
    return field + b"\0" * ((-len(field)) & 3)


def replace_runtime_backing_text(raw: bytes) -> tuple[bytes, str, str] | None:
    for source, target in ANDROID_RUNTIME_BACKING_EXACT.items():
        source_field = serialized_string(source)
        if raw.endswith(source_field):
            return raw[: -len(source_field)] + serialized_string(target), source, target
    return None


def load_objects(path: Path):
    env = UnityPy.load(str(path))
    objects = {(obj.assets_file.name, obj.path_id): obj for obj in env.objects}
    return env, objects


def tmp_strings(objects) -> dict[tuple[str, int], str]:
    result = {}
    for key, obj in objects.items():
        if obj.type.name != "MonoBehaviour":
            continue
        parsed = read_tmp_text(bytes(obj.get_raw_data()))
        if parsed is not None:
            result[key] = parsed[0]
    return result


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
    names = []
    seen = set()
    while transform is not None and transform.path_id not in seen and len(names) < 16:
        seen.add(transform.path_id)
        data = transform.read()
        names.append(game_object_name(objects, key[0], data.m_GameObject.path_id))
        father_id = getattr(data.m_Father, "path_id", 0)
        transform = objects.get((key[0], father_id)) if father_id else None
    return names


def load_exact(strings_dir: Path) -> dict[str, str]:
    result = {}
    for name in ("translation_strings.json", "customlevel_strings.json", "abyss_buffs.json"):
        payload = json.loads((strings_dir / name).read_text(encoding="utf-8-sig"))
        result.update({key: value for key, value in payload.items() if isinstance(key, str) and isinstance(value, str)})
    return result


def learn_legacy_map(base_strings, translated_strings) -> dict[str, str]:
    choices: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for key in base_strings.keys() & translated_strings.keys():
        source = base_strings[key]
        target = translated_strings[key]
        if source != target and CJK_RE.search(source) and not CJK_RE.search(target):
            choices[source][target] += 1
    return {source: counts.most_common(1)[0][0] for source, counts in choices.items()}


def clean_changelog(value: str) -> str:
    languages_note = (
        "If you'd like to change the language of the translation, make sure to check out "
        'the "Languages" menu in the bottom right of this menu.'
    )
    value = value.replace("LanPiaoPiaoFly", "蓝飘飘fly")
    value = value.replace(languages_note, "")
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--source-bundle", required=True, type=Path, help="official bundle matching the target version")
    parser.add_argument("--candidate-bundle", required=True, type=Path, help="unfinished translated bundle used only as fallback data")
    parser.add_argument("--legacy-base-bundle", required=True, type=Path)
    parser.add_argument("--legacy-translated-bundle", required=True, type=Path)
    parser.add_argument("--strings-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    env, objects = load_objects(args.base_bundle)
    source_env, source_objects = load_objects(args.source_bundle)
    candidate_env, candidate_objects = load_objects(args.candidate_bundle)
    legacy_base_env, legacy_base_objects = load_objects(args.legacy_base_bundle)
    legacy_translated_env, legacy_translated_objects = load_objects(args.legacy_translated_bundle)

    source_strings = tmp_strings(source_objects)
    candidate_strings = tmp_strings(candidate_objects)
    legacy_map = learn_legacy_map(tmp_strings(legacy_base_objects), tmp_strings(legacy_translated_objects))
    exact = load_exact(args.strings_dir)
    changelog = clean_changelog((args.strings_dir / "changelog.txt").read_text(encoding="utf-8-sig"))

    methods = collections.Counter()
    changes = []
    expected = {}
    for key in sorted(objects.keys() & source_strings.keys()):
        obj = objects[key]
        if obj.type.name != "MonoBehaviour":
            continue
        parsed = read_tmp_text(bytes(obj.get_raw_data()))
        if parsed is None:
            continue
        current = parsed[0]
        source = source_strings[key]
        target = None
        method = None

        if "3.8.1" in source and "版本更新" in source and len(source) > 500:
            target, method = changelog, "current_pc_changelog"
        elif source == "关闭":
            hierarchy = hierarchy_for_component(source_objects, key)
            if any(name in {"Goback", "Close", "Quit"} for name in hierarchy):
                target, method = "Close", "contextual_close"
            else:
                target, method = exact.get(source, "Disabled"), "pc_exact"
        elif source in exact and exact[source] != source:
            target, method = exact[source], "pc_exact"
        elif source in legacy_map:
            target, method = legacy_map[source], "joseph_fallback"
        else:
            candidate = candidate_strings.get(key)
            if candidate is not None and candidate != source and not CJK_RE.search(candidate):
                source_hierarchy = hierarchy_for_component(source_objects, key)
                candidate_hierarchy = hierarchy_for_component(candidate_objects, key)
                if source_hierarchy and source_hierarchy == candidate_hierarchy:
                    target, method = candidate, "validated_candidate_fallback"

        if target is None or target == current:
            continue
        obj.set_raw_data(replace_tmp_text(bytes(obj.get_raw_data()), target))
        expected[key] = target
        methods[method] += 1
        changes.append({
            "file": key[0],
            "path_id": key[1],
            "source": source,
            "previous": current,
            "translated": target,
            "method": method,
        })

    runtime_backing_expected = {}
    runtime_backing_counts = collections.Counter()
    for key, obj in sorted(objects.items()):
        if obj.type.name != "MonoBehaviour":
            continue
        replaced = replace_runtime_backing_text(bytes(obj.get_raw_data()))
        if replaced is None:
            continue
        updated, source, target = replaced
        obj.set_raw_data(updated)
        runtime_backing_expected[key] = target
        runtime_backing_counts[source] += 1
        changes.append({
            "file": key[0],
            "path_id": key[1],
            "source": source,
            "previous": source,
            "translated": target,
            "method": "android_runtime_backing",
        })
    missing_runtime_backings = set(ANDROID_RUNTIME_BACKING_EXACT) - set(runtime_backing_counts)
    if missing_runtime_backings:
        raise RuntimeError(f"missing Android runtime backing labels: {sorted(missing_runtime_backings)}")

    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    del output_bytes, env, source_env, candidate_env, legacy_base_env, legacy_translated_env
    gc.collect()

    check_env, check_objects = load_objects(args.output)
    for key, target in expected.items():
        parsed = read_tmp_text(bytes(check_objects[key].get_raw_data()))
        if parsed is None or parsed[0] != target:
            raise RuntimeError(f"TMP validation failed for {key}")
    for key, target in runtime_backing_expected.items():
        raw = bytes(check_objects[key].get_raw_data())
        if not raw.endswith(serialized_string(target)):
            raise RuntimeError(f"runtime backing validation failed for {key}")
    del check_env
    gc.collect()

    report = {
        "format_version": 1,
        "base": {"path": str(args.base_bundle.resolve()), "sha256": sha256_file(args.base_bundle)},
        "output": {"path": str(args.output.resolve()), "size": args.output.stat().st_size, "sha256": sha256_file(args.output)},
        "validated_ui_strings": len(expected),
        "validated_runtime_backing_strings": len(runtime_backing_expected),
        "runtime_backing_counts": dict(sorted(runtime_backing_counts.items())),
        "method_counts": dict(sorted(methods.items())),
        "changes": changes,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("output", "validated_ui_strings", "method_counts")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
