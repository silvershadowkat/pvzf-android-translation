#!/usr/bin/env python3
"""Audit the 3.9 Almanac regressions and TMP fallback chain."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

from apply_pc_changelog import clean_changelog
from build_unity_ui_translation import read_tmp_text


CJK_RE = re.compile(r"[\u3400-\u9fff]")
SIZE_TAG_RE = re.compile(r"</?size(?:=[^>]*)?>", re.IGNORECASE)
CRITICAL_PLANTS = {
    "Spruce Sharpshooter": 36,
    "Cattail Girl": 252,
    "Quetzalcoatl Blover": 998,
    "SP Phoenix Threepeater": 999,
    "Penny-shroom": 1446,
    "SP Phoenix Drone": 5000,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def mono_name(obj) -> str:
    raw = bytes(obj.get_raw_data())
    size = int.from_bytes(raw[28:32], "little", signed=True)
    return raw[32 : 32 + size].decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--localization-dir", required=True, type=Path)
    parser.add_argument("--pc-changelog", required=True, type=Path)
    parser.add_argument("--dummy-dll-dir", required=True, type=Path)
    parser.add_argument("--unity-version", default="2022.3.62f1")
    parser.add_argument("--font-asset", action="append", required=True)
    parser.add_argument("--fallback-font-asset", required=True)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    generator = TypeTreeGenerator(args.unity_version)
    generator.load_local_dll_folder(str(args.dummy_dll_dir))
    env = UnityPy.load(str(args.bundle))
    env.typetree_generator = generator
    objects = {(obj.assets_file.name, obj.path_id): obj for obj in env.objects}

    text_assets = {}
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            data = obj.parse_as_object()
            text_assets[data.m_Name] = data.m_Script
    almanac_size_tags = {
        name: len(SIZE_TAG_RE.findall(text_assets[name]))
        for name in ("LawnStrings", "ZombieStrings")
    }
    if any(almanac_size_tags.values()):
        raise RuntimeError(f"PC-only size tags remain in Android Almanacs: {almanac_size_tags}")
    lawn = json.loads(text_assets["LawnStrings"].lstrip("\ufeff"))
    plants = lawn["plants"]
    by_id = {int(record["seedType"]): record for record in plants}
    if len(plants) != 682 or len(by_id) != 682:
        raise RuntimeError(f"unexpected 3.9 plant inventory: records={len(plants)}, unique={len(by_id)}")

    pc_lawn = json.loads(
        (args.localization_dir / "Almanac" / "LawnStringsTranslate.json").read_text(
            encoding="utf-8-sig"
        )
    )
    pc_by_id = {int(record["seedType"]): record for record in pc_lawn["plants"]}
    critical = {}
    for expected_name, seed_type in CRITICAL_PLANTS.items():
        actual = by_id.get(seed_type)
        pc = pc_by_id.get(seed_type)
        if actual is None or pc is None:
            raise RuntimeError(f"missing critical plant seedType {seed_type}")
        for field in ("name", "introduce", "cost", "info"):
            expected_value = pc.get(field)
            if isinstance(expected_value, str):
                expected_value = SIZE_TAG_RE.sub("", expected_value).replace("\u2014", "-")
            if actual.get(field) != expected_value:
                raise RuntimeError(f"critical plant {seed_type} field {field} differs from current PC data")
        if actual["name"] != expected_name:
            raise RuntimeError(
                f"critical plant {seed_type} has unexpected name {actual['name']!r}, "
                f"expected {expected_name!r}"
            )
        if CJK_RE.search(actual.get("cost", "")) or CJK_RE.search(actual.get("info", "")):
            raise RuntimeError(f"critical plant {seed_type} retains CJK in cost/info")
        critical[str(seed_type)] = {
            "name": actual["name"],
            "cost_length": len(actual["cost"]),
            "info_length": len(actual["info"]),
        }
    spruce = by_id[36]["info"].lower()
    if "immune to freeze" in spruce or "glaciation" in spruce:
        raise RuntimeError("Spruce Sharpshooter still contains its obsolete freeze-immunity claim")

    details = json.loads(text_assets["DetailStrings"].lstrip("\ufeff"))["details"]
    if len(details) != 40:
        raise RuntimeError(f"unexpected Mechanics Almanac entry count: {len(details)}")
    mechanics_cjk = []
    for index, item in enumerate(details):
        for field in ("type", "title", "text"):
            if CJK_RE.search(str(item.get(field, ""))):
                mechanics_cjk.append({"index": index, "field": field, "value": item[field]})
    if mechanics_cjk:
        raise RuntimeError(f"Mechanics Almanac retains CJK: {mechanics_cjk}")

    expected_changelog = clean_changelog(args.pc_changelog.read_text(encoding="utf-8-sig"))
    changelog_matches = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        parsed = read_tmp_text(bytes(obj.get_raw_data()))
        if parsed is not None and parsed[0] == expected_changelog:
            changelog_matches.append(obj)
    if len(changelog_matches) != 1:
        raise RuntimeError(
            f"expected one current PC changelog component, found {len(changelog_matches)}"
        )
    changelog_obj = changelog_matches[0]

    mono_objects = [obj for obj in env.objects if obj.type.name == "MonoBehaviour"]
    named_mono = {}
    for obj in mono_objects:
        try:
            named_mono.setdefault(mono_name(obj), []).append(obj)
        except Exception:
            continue
    fallback_matches = named_mono.get(args.fallback_font_asset, [])
    if len(fallback_matches) != 1:
        raise RuntimeError(
            f"expected one fallback TMP asset {args.fallback_font_asset!r}, found {len(fallback_matches)}"
        )
    fallback = fallback_matches[0]
    expected_pointer = [(0, fallback.path_id)]
    fonts = {}
    for name in args.font_asset:
        matches = named_mono.get(name, [])
        if len(matches) != 1:
            raise RuntimeError(f"expected one TMP font asset {name!r}, found {len(matches)}")
        obj = matches[0]
        tree = obj.read_typetree(check_read=False)
        for field in ("fallbackFontAssets", "m_FallbackFontAssetTable"):
            pointers = [(item["m_FileID"], item["m_PathID"]) for item in tree.get(field, [])]
            if pointers != expected_pointer:
                raise RuntimeError(f"{name}.{field} has invalid fallback pointers {pointers}")
            if (obj.assets_file.name, pointers[0][1]) not in objects:
                raise RuntimeError(f"{name}.{field} points to a missing object")
        fonts[name] = {
            "path_id": obj.path_id,
            "fallback_path_id": fallback.path_id,
            "glyph_count": len(tree["m_GlyphTable"]),
            "character_count": len(tree["m_CharacterTable"]),
        }

    report = {
        "format_version": 1,
        "bundle": {"path": str(args.bundle.resolve()), "sha256": sha256_file(args.bundle)},
        "plant_records": len(plants),
        "critical_plants": critical,
        "mechanics_entries": len(details),
        "mechanics_cjk_fields": 0,
        "remaining_almanac_size_tags": almanac_size_tags,
        "changelog": {
            "file": changelog_obj.assets_file.name,
            "path_id": changelog_obj.path_id,
            "length": len(expected_changelog),
            "pc_sha256": sha256_file(args.pc_changelog),
        },
        "fallback_font_asset": {"name": args.fallback_font_asset, "path_id": fallback.path_id},
        "font_assets": fonts,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    # Keep console output portable on Windows code pages; the report itself
    # remains human-readable UTF-8 with the original asset names.
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
