#!/usr/bin/env python3
"""Patch translatable TextAsset content in a PvZ Fusion Unity bundle.

The first intended 3.8.1 target is aha's unfinished bundle because it already
contains translated serialized UI strings and textures.  The script fills its
missing text from current PC translation data and from only those Joseph 3.6.1
assets whose Chinese source payload is unchanged.  It can also restore matching
Font objects from an official bundle, avoiding the unfinished port's global
replacement of the game's original typography.
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

from build_metadata_translation import ANDROID_CONFIRMED_EXACT


CJK_RE = re.compile(r"[\u3400-\u9fff]")
PLACEHOLDER_RE = re.compile(
    r"(?:description[_ -]?missing|translation[_ -]?missing|missing[_ -]?description|"
    r"\b(?:todo|tbd|wip)\b|currently bugged|^\?+$|^[xy]$)",
    re.IGNORECASE,
)
ALMANAC_FILES = {
    "LawnStrings": "LawnStringsTranslate.json",
    "ZombieStrings": "ZombieStringsTranslate.json",
}
ALMANAC_SCHEMAS = {
    "LawnStrings": ("plants", "seedType"),
    "ZombieStrings": ("zombies", "theZombieType"),
}
DETAIL_STRINGS_FILE = "DetailStringsTranslate.json"
DETAIL_TYPE_TRANSLATIONS = {
    "玩法": "Gameplay",
    "基本机制": "Basic Mechanics",
    "植物特性": "Plant Traits",
    "植物体系": "Plant Systems",
    "植物机制": "Plant Systems",
    "僵尸机制": "Zombie Mechanics",
    "环境机制": "Environmental Mechanics",
    "关卡机制": "Level Mechanics",
}
ANDROID_39_DETAIL_ALIASES = {
    "低矮、高大、巨型植物": ("植物特性-植物体型",),
    "可密植、坚实、金属植物": (
        "植物特性-可密植植物",
        "植物特性-坚实植物",
        "植物特性-金属植物",
    ),
    "植物机制-护盾": ("基本机制-护盾",),
    "植物机制-寒冷与冻结状态": ("植物体系-寒冷与冻结状态",),
    "植物机制-余烬状态": ("植物体系-余烬状态",),
    "植物机制-水草值": ("植物体系-水草值",),
    "植物机制-红温状态": ("植物体系-红温状态",),
    "植物机制-光照等级": ("植物体系-光照等级",),
    "植物机制-磁力系统": ("植物体系-磁力系统",),
    "植物机制-中毒状态": ("植物体系-中毒状态",),
    "植物机制-传送状态": ("植物体系-传送状态",),
    "僵尸机制-临界值": ("基本机制-临界值",),
    "僵尸机制-防具": ("基本机制-僵尸防具",),
    "僵尸机制-护甲": ("基本机制-护甲值",),
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


def is_usable_pc_translation(value: Any) -> bool:
    """Reject empty, CJK-bearing, and explicit placeholder PC values."""
    return (
        isinstance(value, str)
        and bool(value.strip())
        and CJK_RE.search(value) is None
        and PLACEHOLDER_RE.search(value.strip()) is None
    )


def parse_json_text(value: str) -> Any:
    # Joseph's translated TextAssets commonly retain a UTF-8 BOM as the first
    # decoded character. Unity accepts it, but Python's json.loads does not.
    return json.loads(value.lstrip("\ufeff"))


def merge_android_almanac(
    asset_name: str,
    source_script: str,
    pc_source_script: str,
    pc_script: str,
    overrides: dict[str, Any],
) -> tuple[str, dict[str, int]]:
    """Overlay PC translations onto the matching official Android records.

    Replacing an entire Almanac TextAsset with an older PC file drops records
    introduced by a newer Android release. Keep the official list, order, and
    schema, then overlay translations by the stable numeric game ID.
    """
    list_key, id_key = ALMANAC_SCHEMAS[asset_name]
    source_tree = parse_json_text(source_script)
    pc_source_tree = parse_json_text(pc_source_script)
    pc_tree = parse_json_text(pc_script)
    if not isinstance(source_tree, dict) or not isinstance(source_tree.get(list_key), list):
        raise RuntimeError(f"official {asset_name} does not contain a {list_key} list")
    if not isinstance(pc_tree, dict) or not isinstance(pc_tree.get(list_key), list):
        raise RuntimeError(f"PC {asset_name} does not contain a {list_key} list")
    if not isinstance(pc_source_tree, dict) or not isinstance(pc_source_tree.get(list_key), list):
        raise RuntimeError(f"PC source {asset_name} does not contain a {list_key} list")

    def index_records(records: list[Any], label: str) -> dict[str, dict[str, Any]]:
        indexed: dict[str, dict[str, Any]] = {}
        for position, record in enumerate(records):
            if not isinstance(record, dict) or id_key not in record:
                raise RuntimeError(f"{label} {asset_name} record {position} has no {id_key}")
            stable_id = str(record[id_key])
            if stable_id in indexed:
                raise RuntimeError(f"{label} {asset_name} has duplicate {id_key} {stable_id}")
            indexed[stable_id] = record
        return indexed

    source_records = source_tree[list_key]
    source_by_id = index_records(source_records, "official")
    pc_source_by_id = index_records(pc_source_tree[list_key], "PC source")
    pc_by_id = index_records(pc_tree[list_key], "PC")
    asset_overrides = overrides.get(asset_name, {})
    if not isinstance(asset_overrides, dict):
        raise RuntimeError(f"Android Almanac overrides for {asset_name} must be an object")
    unknown_overrides = sorted(set(asset_overrides) - set(source_by_id))
    if unknown_overrides:
        raise RuntimeError(f"Android Almanac overrides reference unknown {asset_name} IDs: {unknown_overrides}")

    # Placeholder commits sometimes seed multiple new records with the same
    # unrelated English body. Detect one translation value aligned to multiple
    # distinct Chinese sources and reject that field while retaining valid
    # independently translated fields such as a plant name.
    translated_sources: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    translated_body_signatures: collections.Counter[tuple[tuple[str, str], ...]] = (
        collections.Counter()
    )
    for stable_id, translated_record in pc_by_id.items():
        pc_source_record = pc_source_by_id.get(stable_id)
        if pc_source_record is None:
            continue
        for field, translated_value in translated_record.items():
            source_value = pc_source_record.get(field)
            if isinstance(source_value, str) and isinstance(translated_value, str):
                translated_sources[(field, translated_value)].add(source_value)
        body_signature = tuple(
            sorted(
                (field, value)
                for field, value in translated_record.items()
                if field not in {id_key, "name"} and isinstance(value, str) and value
            )
        )
        if body_signature:
            translated_body_signatures[body_signature] += 1

    merged_records: list[dict[str, Any]] = []
    pc_applied = 0
    pc_fields_applied = 0
    pc_placeholder_fields_rejected = 0
    pc_unaligned_fields_rejected = 0
    override_applied = 0
    official_only = 0
    for source_record in source_records:
        stable_id = str(source_record[id_key])
        merged = dict(source_record)
        pc_record = pc_by_id.get(stable_id)
        pc_source_record = pc_source_by_id.get(stable_id)
        applied_fields = 0
        if pc_record is not None and pc_source_record is not None:
            body_signature = tuple(
                sorted(
                    (field, value)
                    for field, value in pc_record.items()
                    if field not in {id_key, "name"} and isinstance(value, str) and value
                )
            )
            repeated_record_body = translated_body_signatures[body_signature] > 1
            for field, translated_value in pc_record.items():
                if field == id_key:
                    continue
                official_value = source_record.get(field)
                pc_source_value = pc_source_record.get(field)
                if official_value != pc_source_value:
                    pc_unaligned_fields_rejected += 1
                    continue
                duplicate_placeholder = (
                    isinstance(pc_source_value, str)
                    and isinstance(translated_value, str)
                    and len(translated_sources[(field, translated_value)]) > 1
                    and field != "name"
                )
                if (
                    not is_usable_pc_translation(translated_value)
                    or duplicate_placeholder
                    or (repeated_record_body and field != "name")
                ):
                    pc_placeholder_fields_rejected += 1
                    continue
                merged[field] = translated_value
                applied_fields += 1
            merged[id_key] = source_record[id_key]
            if applied_fields:
                pc_applied += 1
                pc_fields_applied += applied_fields
            else:
                official_only += 1
        else:
            official_only += 1
        override = asset_overrides.get(stable_id)
        if override is not None:
            if not isinstance(override, dict):
                raise RuntimeError(f"Android Almanac override {asset_name} {stable_id} must be an object")
            merged.update(override)
            merged[id_key] = source_record[id_key]
            override_applied += 1
        merged_records.append(merged)
    source_tree[list_key] = merged_records
    return json.dumps(source_tree, ensure_ascii=False, indent=4), {
        "official_records": len(source_records),
        "pc_records_applied": pc_applied,
        "pc_fields_applied": pc_fields_applied,
        "pc_placeholder_fields_rejected": pc_placeholder_fields_rejected,
        "pc_unaligned_fields_rejected": pc_unaligned_fields_rejected,
        "android_overrides_applied": override_applied,
        "official_only_records": official_only,
        "pc_records_not_in_official": len(set(pc_by_id) - set(source_by_id)),
    }


def merge_android_detail_strings(
    source_script: str,
    pc_descriptions: dict[str, str],
    exact: dict[str, str],
    allow_untranslated_new_content: bool = False,
) -> tuple[str, dict[str, list[str]]]:
    """Merge PC Mechanics Almanac copy into Android's required list schema."""
    tree = parse_json_text(source_script)
    if not isinstance(tree, dict) or not isinstance(tree.get("details"), list):
        raise RuntimeError("official Android DetailStrings no longer contains a details list")
    details = tree["details"]
    source_titles: list[str] = []
    for index, item in enumerate(details):
        if not isinstance(item, dict):
            raise RuntimeError(f"Android DetailStrings item {index} is not an object")
        title = item.get("title")
        if not isinstance(title, str) or not title:
            raise RuntimeError(f"Android DetailStrings item {index} has no title")
        source_titles.append(title)
    if len(source_titles) != len(set(source_titles)):
        raise RuntimeError("official Android DetailStrings contains duplicate titles")
    resolved_titles: set[str] = set()
    for source_title in source_titles:
        translated_title = exact.get(source_title)
        has_title = is_usable_pc_translation(translated_title)
        has_description = source_title in pc_descriptions or (
            source_title in ANDROID_39_DETAIL_ALIASES
            and all(key in pc_descriptions for key in ANDROID_39_DETAIL_ALIASES[source_title])
        )
        if has_title and has_description:
            resolved_titles.add(source_title)
    missing = sorted(set(source_titles) - resolved_titles)
    extra = sorted(set(pc_descriptions) - set(source_titles))
    if (missing or extra) and not allow_untranslated_new_content:
        raise RuntimeError(
            "PC/Android Mechanics Almanac title mismatch: "
            f"missing={missing!r}, extra={extra!r}"
        )
    for item, source_title in zip(details, source_titles):
        if source_title in missing:
            # Compatibility migrations intentionally preserve newly introduced
            # upstream entries until they have been reviewed and translated.
            # Existing entries are still merged from the community project.
            continue
        source_type = item.get("type")
        translated_type = DETAIL_TYPE_TRANSLATIONS.get(source_type)
        if translated_type is None:
            raise RuntimeError(
                f"missing English Mechanics Almanac category for {source_type!r}"
            )
        translated_title = exact.get(source_title)
        if not is_usable_pc_translation(translated_title):
            raise RuntimeError(f"missing English Mechanics Almanac title for {source_title!r}")
        if source_title in ANDROID_39_DETAIL_ALIASES:
            description = "\n\n".join(pc_descriptions[key] for key in ANDROID_39_DETAIL_ALIASES[source_title])
        else:
            description = pc_descriptions[source_title]
        if not is_usable_pc_translation(description):
            raise RuntimeError(f"invalid PC Mechanics Almanac text for {source_title!r}")
        item["type"] = translated_type
        item["title"] = translated_title
        item["text"] = description
    return json.dumps(tree, ensure_ascii=False, indent=4), {
        "untranslated_android_titles": missing,
        "unused_pc_titles": extra,
    }


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


def read_raw_objects(bundle: Path, type_name: str) -> dict[tuple[str, int], tuple[str, bytes]]:
    env = UnityPy.load(str(bundle))
    records: dict[tuple[str, int], tuple[str, bytes]] = {}
    for obj in env.objects:
        if obj.type.name != type_name:
            continue
        data = obj.read()
        key = (obj.assets_file.name, obj.path_id)
        records[key] = (data.m_Name, bytes(obj.get_raw_data()))
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


def collect_cjk_strings(value: Any, output: set[str]) -> None:
    if isinstance(value, str):
        if CJK_RE.search(value):
            output.add(value)
        return
    if isinstance(value, dict):
        for item in value.values():
            collect_cjk_strings(item, output)
        return
    if isinstance(value, list):
        for item in value:
            collect_cjk_strings(item, output)


def collect_bundle_cjk_strings(bundle: Path) -> set[str]:
    output: set[str] = set()
    for record in read_text_records(bundle).values():
        try:
            tree = parse_json_text(record.script)
        except (json.JSONDecodeError, TypeError):
            collect_cjk_strings(record.script, output)
        else:
            collect_cjk_strings(tree, output)
    return output


def collect_approved_pairs(source: Any, translated: Any, output: dict[str, set[str]]) -> None:
    if isinstance(source, str) and isinstance(translated, str):
        if source != translated and CJK_RE.search(source) and is_usable_pc_translation(translated):
            output.setdefault(source, set()).add(translated)
        return
    if isinstance(source, dict) and isinstance(translated, dict):
        for key in source.keys() & translated.keys():
            collect_approved_pairs(source[key], translated[key], output)
        return
    if isinstance(source, list) and isinstance(translated, list):
        for left, right in zip(source, translated):
            collect_approved_pairs(left, right, output)


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


def pc_regex_translation(
    value: str,
    pc_exact: dict[str, str],
    regex_entries: list[tuple[str, str, re.Pattern[str], str]],
) -> str | None:
    for _pattern, template, compiled, anchor in regex_entries:
        if anchor and anchor not in value:
            continue
        match = compiled.search(value)
        if match is None:
            continue
        dynamic = [pc_exact.get(group, group) for group in match.groups()]
        result = csharp_format(template, dynamic)
        if result != value and is_usable_pc_translation(result):
            return result
    return None


def enforce_new_39_policy(
    source: Any,
    candidate: Any,
    previous_cjk: set[str],
    approved_pc_pairs: dict[str, set[str]],
    pc_exact: dict[str, str],
    regex_entries: list[tuple[str, str, re.Pattern[str], str]],
    counts: collections.Counter[str],
) -> Any:
    if isinstance(source, str) and isinstance(candidate, str):
        if not CJK_RE.search(source) or source in previous_cjk or candidate == source:
            return candidate
        if candidate in approved_pc_pairs.get(source, set()) and is_usable_pc_translation(candidate):
            counts["new_39_current_pc"] += 1
            return candidate
        regex_result = pc_regex_translation(source, pc_exact, regex_entries)
        if (
            regex_result is not None
            and candidate == regex_result
            and is_usable_pc_translation(candidate)
        ):
            counts["new_39_current_pc_regex"] += 1
            return candidate
        counts["new_39_preserved_chinese"] += 1
        return source
    if isinstance(source, dict) and isinstance(candidate, dict):
        result = dict(candidate)
        for key in source.keys() & candidate.keys():
            result[key] = enforce_new_39_policy(
                source[key], candidate[key], previous_cjk, approved_pc_pairs, pc_exact, regex_entries, counts
            )
        return result
    if isinstance(source, list) and isinstance(candidate, list):
        result = list(candidate)
        for index, source_item in enumerate(source[: len(candidate)]):
            result[index] = enforce_new_39_policy(
                source_item,
                candidate[index],
                previous_cjk,
                approved_pc_pairs,
                pc_exact,
                regex_entries,
                counts,
            )
        return result
    return candidate


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
    parser.add_argument(
        "--source-bundle",
        type=Path,
        help="official bundle matching the target version; defaults to --preserve-fonts-from",
    )
    parser.add_argument(
        "--previous-version-bundle",
        required=True,
        type=Path,
        help="official Chinese 3.8.1 bundle used to identify content newly introduced in 3.9",
    )
    parser.add_argument(
        "--preserve-fonts-from",
        type=Path,
        help="optional official bundle whose matching Font objects replace modified base fonts",
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument(
        "--android-exact-map",
        type=Path,
        help="optional reviewed Android-only exact-string fallback map",
    )
    parser.add_argument(
        "--android-almanac-overrides",
        type=Path,
        help="optional Android-version Almanac records keyed by TextAsset and stable ID",
    )
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    parser.add_argument(
        "--allow-untranslated-new-content",
        action="store_true",
        help=(
            "translate the known Mechanics Almanac intersection while preserving "
            "new or renamed upstream entries for a later reviewed pass"
        ),
    )
    args = parser.parse_args()

    legacy_patches, legacy_leaf, legacy_conflicts, legacy_stats = learn_legacy_text_patches(
        args.legacy_base_bundle, args.legacy_translated_bundle
    )
    patches_by_name: dict[str, list[LegacyPatch]] = collections.defaultdict(list)
    for patch in legacy_patches:
        patches_by_name[patch.source_name].append(patch)

    pc_exact, regex_entries, extras = load_pc_maps(args.localization_dir)
    previous_cjk = collect_bundle_cjk_strings(args.previous_version_bundle)
    approved_pc_pairs: dict[str, set[str]] = {
        source: {translated}
        for source, translated in pc_exact.items()
        if source != translated and is_usable_pc_translation(translated)
    }
    exact = dict(ANDROID_CONFIRMED_EXACT)
    exact.update(pc_exact)
    if args.android_exact_map is not None:
        android_map = read_json(args.android_exact_map)
        android_exact = android_map.get("exact", android_map)
        if not isinstance(android_exact, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in android_exact.items()
        ):
            raise RuntimeError("Android exact map must contain a string-to-string 'exact' object")
        # PC community text always wins if it later contains the same source.
        for source, translated in android_exact.items():
            exact.setdefault(source, translated)
    pc_almanac = {
        name: (args.localization_dir / "Almanac" / filename).read_text(encoding="utf-8-sig")
        for name, filename in ALMANAC_FILES.items()
    }
    pc_almanac_sources = {
        name: (args.localization_dir.parents[1] / "Dumps" / filename.replace("Translate", "")).read_text(
            encoding="utf-8-sig"
        )
        for name, filename in ALMANAC_FILES.items()
    }
    almanac_overrides: dict[str, Any] = {}
    if args.android_almanac_overrides is not None:
        almanac_overrides = read_json(args.android_almanac_overrides)
        if not isinstance(almanac_overrides, dict):
            raise RuntimeError("Android Almanac overrides must contain an object")
    pc_detail_descriptions = read_json(args.localization_dir / "Almanac" / DETAIL_STRINGS_FILE)
    if not isinstance(pc_detail_descriptions, dict):
        raise RuntimeError("PC DetailStrings translation is not an object")
    source_bundle = args.source_bundle or args.preserve_fonts_from
    if source_bundle is None:
        raise RuntimeError("--source-bundle is required when --preserve-fonts-from is omitted")
    source_text_by_key = read_text_records(source_bundle)
    source_text_records = list(source_text_by_key.values())
    source_detail_records = [record for record in source_text_records if record.name == "DetailStrings"]
    if len(source_detail_records) != 1:
        raise RuntimeError(
            f"expected one official Android DetailStrings asset, found {len(source_detail_records)}"
        )
    android_detail_script, detail_merge = merge_android_detail_strings(
        source_detail_records[0].script,
        pc_detail_descriptions,
        exact,
        args.allow_untranslated_new_content,
    )
    official_detail_tree = parse_json_text(source_detail_records[0].script)
    if isinstance(official_detail_tree, dict):
        for item in official_detail_tree.get("details", []):
            if not isinstance(item, dict):
                continue
            title = item.get("title")
            source_description = item.get("text")
            pc_description = pc_detail_descriptions.get(title)
            if (
                isinstance(source_description, str)
                and isinstance(pc_description, str)
                and source_description != pc_description
                and CJK_RE.search(source_description)
                and is_usable_pc_translation(pc_description)
            ):
                approved_pc_pairs.setdefault(source_description, set()).add(pc_description)
    merged_almanac: dict[str, str] = {}
    almanac_merge_stats: dict[str, dict[str, int]] = {}
    for asset_name, pc_script in pc_almanac.items():
        matches = [record for record in source_text_records if record.name == asset_name]
        if len(matches) != 1:
            raise RuntimeError(f"expected one official Android {asset_name} asset, found {len(matches)}")
        merged_almanac[asset_name], almanac_merge_stats[asset_name] = merge_android_almanac(
            asset_name,
            matches[0].script,
            pc_almanac_sources[asset_name],
            pc_script,
            almanac_overrides,
        )
        official_tree = parse_json_text(matches[0].script)
        current_pc_tree = parse_json_text(merged_almanac[asset_name])
        list_key, id_key = ALMANAC_SCHEMAS[asset_name]
        if isinstance(official_tree, dict) and isinstance(current_pc_tree, dict):
            official_items = official_tree.get(list_key, [])
            pc_items = current_pc_tree.get(list_key, [])
            if isinstance(official_items, list) and isinstance(pc_items, list):
                pc_by_id = {
                    item.get(id_key): item
                    for item in pc_items
                    if isinstance(item, dict) and item.get(id_key) is not None
                }
                for source_item in official_items:
                    if not isinstance(source_item, dict):
                        continue
                    pc_item = pc_by_id.get(source_item.get(id_key))
                    if isinstance(pc_item, dict):
                        collect_approved_pairs(source_item, pc_item, approved_pc_pairs)
    tips_fs: dict[str, str] = extras["tips_fs"]
    tips_iz: dict[str, str] = extras["tips_iz"]

    env = UnityPy.load(str(args.base_bundle))
    method_counts: collections.Counter[str] = collections.Counter()
    changed_assets: list[dict[str, Any]] = []
    expected: dict[tuple[str, int], tuple[str, str]] = {}
    expected_structure: dict[tuple[str, int], tuple[type[Any], set[str] | None]] = {}
    expected_fonts: dict[tuple[str, int], tuple[str, str]] = {}

    if args.preserve_fonts_from is not None:
        source_fonts = read_raw_objects(args.preserve_fonts_from, "Font")
        for obj in env.objects:
            if obj.type.name != "Font":
                continue
            key = (obj.assets_file.name, obj.path_id)
            source = source_fonts.get(key)
            if source is None:
                continue
            source_name, source_raw = source
            current_name = obj.read().m_Name
            if current_name != source_name or bytes(obj.get_raw_data()) == source_raw:
                continue
            obj.set_raw_data(source_raw)
            expected_fonts[key] = (source_name, sha256(source_raw))

    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.parse_as_object()
        original_name = data.m_Name
        original_script = data.m_Script
        new_name = original_name
        new_script = original_script
        methods: list[str] = []

        if original_name == "DetailStrings":
            new_script = android_detail_script
            methods.append("current_pc_android_detail_merge")
        elif original_name in merged_almanac:
            new_script = merged_almanac[original_name]
            methods.append("current_pc_android_almanac_merge")
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

        official_record = source_text_by_key.get((obj.assets_file.name, obj.path_id))
        if official_record is not None:
            try:
                official_tree = parse_json_text(official_record.script)
                candidate_tree = parse_json_text(new_script)
            except (json.JSONDecodeError, TypeError):
                policy_script = enforce_new_39_policy(
                    official_record.script,
                    new_script,
                    previous_cjk,
                    approved_pc_pairs,
                    pc_exact,
                    regex_entries,
                    method_counts,
                )
                if policy_script != new_script:
                    new_script = policy_script
                    methods.append("new_39_pc_or_chinese_policy")
            else:
                policy_tree = enforce_new_39_policy(
                    official_tree,
                    candidate_tree,
                    previous_cjk,
                    approved_pc_pairs,
                    pc_exact,
                    regex_entries,
                    method_counts,
                )
                if policy_tree != candidate_tree:
                    new_script = json.dumps(policy_tree, ensure_ascii=False, indent=4)
                    methods.append("new_39_pc_or_chinese_policy")

        if new_name == original_name and new_script == original_script:
            continue
        data.m_Name = new_name
        data.m_Script = new_script
        obj.save_typetree(data)
        key = (obj.assets_file.name, obj.path_id)
        expected[key] = (new_name, new_script)
        structure_source_script = (
            source_detail_records[0].script if original_name == "DetailStrings" else original_script
        )
        try:
            original_tree = parse_json_text(structure_source_script)
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
        if key in expected_fonts:
            expected_name, expected_hash = expected_fonts[key]
            if obj.type.name != "Font" or obj.read().m_Name != expected_name:
                raise RuntimeError(f"Font identity validation failed for {key}")
            if sha256(bytes(obj.get_raw_data())) != expected_hash:
                raise RuntimeError(f"Font content validation failed for {key}")
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
        "font_preservation": {
            "source": str(args.preserve_fonts_from.resolve()) if args.preserve_fonts_from is not None else None,
            "restored_font_count": len(expected_fonts),
            "restored_fonts": [
                {"file": key[0], "path_id": key[1], "name": value[0], "sha256": value[1]}
                for key, value in sorted(expected_fonts.items())
            ],
        },
        "legacy_mapping_conflicts": legacy_conflicts,
        "pc_translation_entries": extras["source_counts"],
        "new_39_translation_policy": {
            "previous_version_bundle": str(args.previous_version_bundle.resolve()),
            "previous_version_cjk_string_count": len(previous_cjk),
            "approved_current_pc_source_count": len(approved_pc_pairs),
            "rule": "New 3.9 content uses current PC English only; otherwise official Chinese is preserved.",
        },
        "almanac_merge": almanac_merge_stats,
        "mechanics_almanac_merge": detail_merge,
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
