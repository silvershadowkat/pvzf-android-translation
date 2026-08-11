#!/usr/bin/env python3
"""Patch translatable TextAsset content in a PvZ Fusion Unity bundle.

The first intended 3.8.1 target is aha's unfinished bundle because it already
contains the required Latin font/UI dependencies.  The script fills its missing
text from current PC translation data and from only those Joseph 3.6.1 assets
whose Chinese source payload is unchanged.
"""

from __future__ import annotations

import argparse
import collections
import gc
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import UnityPy


CJK_RE = re.compile(r"[\u3400-\u9fff]")
ALMANAC_FILES = {
    "LawnStrings": "LawnStringsTranslate.json",
    "ZombieStrings": "ZombieStringsTranslate.json",
    "DetailStrings": "DetailStringsTranslate.json",
}
EXACT_FILES = ("translation_strings.json", "customlevel_strings.json", "abyss_buffs.json")
REGEX_FILES = ("translation_regexs.json", "customlevel_regexs.json")


@dataclass(frozen=True)
class TextRecord:
    file: str
    path_id: int
    name: str
    script: str


@dataclass(frozen=True)
class LegacyPatch:
    source_name: str
    source_script: str
    translated_name: str
    translated_script: str


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_json_text(value: str) -> Any:
    # Joseph's translated TextAssets commonly retain a UTF-8 BOM as the first
    # decoded character. Unity accepts it, but Python's json.loads does not.
    return json.loads(value.lstrip("\ufeff"))


def read_text_records(bundle: Path) -> dict[tuple[str, int], TextRecord]:
    env = UnityPy.load(str(bundle))
    records: dict[tuple[str, int], TextRecord] = {}
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.parse_as_object()
        key = (obj.assets_file.name, obj.path_id)
        records[key] = TextRecord(key[0], key[1], data.m_Name, data.m_Script)
    del env
    gc.collect()
    return records


def collect_leaf_pairs(source: Any, translated: Any, output: dict[str, str], conflicts: list[dict[str, str]]) -> None:
    if isinstance(source, str) and isinstance(translated, str):
        if source != translated and CJK_RE.search(source) and not CJK_RE.search(translated):
            previous = output.get(source)
            if previous is not None and previous != translated:
                conflicts.append({"source": source, "kept": previous, "discarded": translated})
            else:
                output[source] = translated
        return
    if isinstance(source, dict) and isinstance(translated, dict):
        for key in source.keys() & translated.keys():
            collect_leaf_pairs(source[key], translated[key], output, conflicts)
        return
    if isinstance(source, list) and isinstance(translated, list):
        for left, right in zip(source, translated):
            collect_leaf_pairs(left, right, output, conflicts)


def learn_legacy_text_patches(
    base_bundle: Path, translated_bundle: Path
) -> tuple[list[LegacyPatch], dict[str, str], list[dict[str, str]], dict[str, int]]:
    base = read_text_records(base_bundle)
    translated = read_text_records(translated_bundle)
    patches: list[LegacyPatch] = []
    leaf_map: dict[str, str] = {}
    conflicts: list[dict[str, str]] = []
    stats: collections.Counter[str] = collections.Counter()

    for key in sorted(base.keys() & translated.keys()):
        source = base[key]
        target = translated[key]
        if source.name == target.name and source.script == target.script:
            continue
        patches.append(LegacyPatch(source.name, source.script, target.name, target.script))
        stats["changed_assets"] += 1
        try:
            source_json = parse_json_text(source.script)
            target_json = parse_json_text(target.script)
        except (json.JSONDecodeError, TypeError):
            collect_leaf_pairs(source.script, target.script, leaf_map, conflicts)
        else:
            collect_leaf_pairs(source_json, target_json, leaf_map, conflicts)

    stats["full_asset_patches"] = len(patches)
    stats["unique_leaf_mappings"] = len(leaf_map)
    stats["leaf_mapping_conflicts"] = len(conflicts)
    return patches, leaf_map, conflicts, dict(stats)


def load_pc_maps(localization_dir: Path) -> tuple[dict[str, str], list[tuple[str, str, re.Pattern[str], str]], dict[str, Any]]:
    strings_dir = localization_dir / "Strings"
    exact: dict[str, str] = {}
    regex_entries: list[tuple[str, str, re.Pattern[str], str]] = []
    source_counts: dict[str, int] = {}

    for filename in EXACT_FILES:
        payload = read_json(strings_dir / filename)
        added = 0
        for source, target in payload.items():
            if isinstance(source, str) and isinstance(target, str) and CJK_RE.search(source):
                exact[source] = target
                added += 1
        source_counts[filename] = added

    for filename in REGEX_FILES:
        payload = read_json(strings_dir / filename)
        added = 0
        for pattern, template in payload.items():
            if isinstance(pattern, str) and isinstance(template, str):
                cjk_runs = re.findall(r"[\u3400-\u9fff]+", pattern)
                anchor = max(cjk_runs, key=len) if cjk_runs else ""
                regex_entries.append((pattern, template, re.compile(pattern, re.DOTALL), anchor))
                added += 1
        source_counts[filename] = added

    extras = {
        "tips_fs": read_json(strings_dir / "tips_fs.json"),
        "tips_iz": read_json(strings_dir / "tips_iz.json"),
        "source_counts": source_counts,
    }
    return exact, regex_entries, extras


def csharp_format(template: str, values: list[str]) -> str:
    open_token = "\0OPEN_BRACE\0"
    close_token = "\0CLOSE_BRACE\0"
    protected = template.replace("{{", open_token).replace("}}", close_token)

    def replace(match: re.Match[str]) -> str:
        index = int(match.group(1))
        return values[index] if index < len(values) else match.group(0)

    protected = re.sub(r"\{(\d+)(?:,[^}:]+)?(?::[^}]+)?\}", replace, protected)
    return protected.replace(open_token, "{").replace(close_token, "}")


def translate_text(
    value: str,
    exact: dict[str, str],
    legacy_leaf: dict[str, str],
    regex_entries: list[tuple[str, str, re.Pattern[str], str]],
) -> tuple[str, str | None]:
    if not CJK_RE.search(value):
        return value, None
    if value in exact:
        return exact[value], "pc_exact"
    if value in legacy_leaf:
        return legacy_leaf[value], "legacy_leaf"
    for _pattern, template, compiled, anchor in regex_entries:
        if anchor and anchor not in value:
            continue
        match = compiled.search(value)
        if match is None:
            continue
        dynamic = [exact.get(group, legacy_leaf.get(group, group)) for group in match.groups()]
        result = csharp_format(template, dynamic)
        if result != value:
            return result, "pc_regex"
    return value, None


def translate_tree(
    value: Any,
    exact: dict[str, str],
    legacy_leaf: dict[str, str],
    regex_entries: list[tuple[str, str, re.Pattern[str], str]],
    counts: collections.Counter[str],
) -> tuple[Any, bool]:
    if isinstance(value, str):
        translated, method = translate_text(value, exact, legacy_leaf, regex_entries)
        if method is not None and translated != value:
            counts[method] += 1
            return translated, True
        return value, False
    if isinstance(value, list):
        result = []
        changed = False
        for item in value:
            translated, item_changed = translate_tree(item, exact, legacy_leaf, regex_entries, counts)
            result.append(translated)
            changed |= item_changed
        return result, changed
    if isinstance(value, dict):
        result = {}
        changed = False
        for key, item in value.items():
            translated, item_changed = translate_tree(item, exact, legacy_leaf, regex_entries, counts)
            result[key] = translated
            changed |= item_changed
        return result, changed
    return value, False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path, help="bundle to patch; for 3.8.1 use aha's font-enabled bundle")
    parser.add_argument("--localization-dir", required=True, type=Path, help="PC Localization/English directory")
    parser.add_argument("--legacy-base-bundle", required=True, type=Path, help="official Chinese 3.6.1 bundle")
    parser.add_argument("--legacy-translated-bundle", required=True, type=Path, help="Joseph English 3.6.1 bundle")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    legacy_patches, legacy_leaf, legacy_conflicts, legacy_stats = learn_legacy_text_patches(
        args.legacy_base_bundle, args.legacy_translated_bundle
    )
    patches_by_name: dict[str, list[LegacyPatch]] = collections.defaultdict(list)
    for patch in legacy_patches:
        patches_by_name[patch.source_name].append(patch)

    exact, regex_entries, extras = load_pc_maps(args.localization_dir)
    almanac = {
        name: (args.localization_dir / "Almanac" / filename).read_text(encoding="utf-8-sig")
        for name, filename in ALMANAC_FILES.items()
    }
    tips_fs: dict[str, str] = extras["tips_fs"]
    tips_iz: dict[str, str] = extras["tips_iz"]

    env = UnityPy.load(str(args.base_bundle))
    method_counts: collections.Counter[str] = collections.Counter()
    changed_assets: list[dict[str, Any]] = []
    expected: dict[tuple[str, int], tuple[str, str]] = {}
    expected_structure: dict[tuple[str, int], tuple[type[Any], set[str] | None]] = {}

    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.parse_as_object()
        original_name = data.m_Name
        original_script = data.m_Script
        new_name = original_name
        new_script = original_script
        methods: list[str] = []

        if original_name in almanac:
            new_script = almanac[original_name]
            methods.append("current_pc_almanac")
        else:
            exact_legacy = next(
                (patch for patch in patches_by_name.get(original_name, []) if patch.source_script == original_script),
                None,
            )
            if exact_legacy is not None:
                new_name = exact_legacy.translated_name
                new_script = exact_legacy.translated_script
                methods.append("legacy_full_unchanged_source")

            try:
                tree = parse_json_text(new_script)
            except (json.JSONDecodeError, TypeError):
                translated, method = translate_text(new_script, exact, legacy_leaf, regex_entries)
                if method is not None:
                    new_script = translated
                    method_counts[method] += 1
                    methods.append(method)
            else:
                translated_tree, tree_changed = translate_tree(
                    tree, exact, legacy_leaf, regex_entries, method_counts
                )
                if isinstance(translated_tree, dict):
                    translated_tip = tips_iz.get(original_name)
                    tip_method = "current_pc_iz_tip"
                    if translated_tip is None:
                        translated_tip = tips_fs.get(original_name)
                        tip_method = "current_pc_fs_tip"
                    if translated_tip is not None and translated_tree.get("tips") != translated_tip:
                        translated_tree["tips"] = translated_tip
                        tree_changed = True
                        methods.append(tip_method)
                if tree_changed:
                    new_script = json.dumps(translated_tree, ensure_ascii=False, indent=4)
                    methods.append("structured_translation")

        if new_name == original_name and new_script == original_script:
            continue
        data.m_Name = new_name
        data.m_Script = new_script
        obj.save_typetree(data)
        key = (obj.assets_file.name, obj.path_id)
        expected[key] = (new_name, new_script)
        try:
            original_tree = parse_json_text(original_script)
        except (json.JSONDecodeError, TypeError):
            pass
        else:
            original_keys = set(original_tree) if isinstance(original_tree, dict) else None
            expected_structure[key] = (type(original_tree), original_keys)
        changed_assets.append(
            {
                "file": key[0],
                "path_id": key[1],
                "original_name": original_name,
                "translated_name": new_name,
                "methods": methods,
                "source_size": len(original_script.encode("utf-8")),
                "translated_size": len(new_script.encode("utf-8")),
            }
        )
        for method in methods:
            method_counts[method] += 1

    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    del output_bytes
    del env
    gc.collect()

    # Reopen and validate every intended TextAsset mutation.
    validated = 0
    check_env = UnityPy.load(str(args.output))
    for obj in check_env.objects:
        key = (obj.assets_file.name, obj.path_id)
        if key not in expected:
            continue
        data = obj.parse_as_object()
        if (data.m_Name, data.m_Script) != expected[key]:
            raise RuntimeError(f"TextAsset validation failed for {key}")
        if key in expected_structure:
            expected_type, expected_keys = expected_structure[key]
            try:
                validated_tree = parse_json_text(data.m_Script)
            except (json.JSONDecodeError, TypeError) as exc:
                raise RuntimeError(f"TextAsset JSON structure was destroyed for {key}") from exc
            if type(validated_tree) is not expected_type:
                raise RuntimeError(f"TextAsset JSON root type changed for {key}")
            if expected_keys is not None and set(validated_tree) != expected_keys:
                raise RuntimeError(f"TextAsset JSON top-level keys changed for {key}")
        validated += 1
    if validated != len(expected):
        raise RuntimeError(f"validated {validated} of {len(expected)} patched TextAssets")
    del check_env
    gc.collect()

    report = {
        "format_version": 1,
        "base": {
            "path": str(args.base_bundle.resolve()),
            "size": args.base_bundle.stat().st_size,
            "sha256": sha256_file(args.base_bundle),
        },
        "output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
            "validated_text_assets": validated,
        },
        "legacy_learning": legacy_stats,
        "legacy_mapping_conflicts": legacy_conflicts,
        "pc_translation_entries": extras["source_counts"],
        "method_counts": dict(sorted(method_counts.items())),
        "changed_text_asset_count": len(changed_assets),
        "changed_text_assets": changed_assets,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": report["output"],
                "method_counts": report["method_counts"],
                "changed_text_asset_count": report["changed_text_asset_count"],
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
