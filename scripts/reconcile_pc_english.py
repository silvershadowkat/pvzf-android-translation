#!/usr/bin/env python3
"""Final, source-aligned PC wording pass after Android layout/font polishing.

Missing or unusable PC text never causes a historical English field to revert.
Run without --output to audit; --output writes and verifies a data-only bundle.
"""
from __future__ import annotations

import argparse
import collections
import gc
import hashlib
import json
import re
from pathlib import Path

import UnityPy

from build_metadata_translation import load_pc_translations, translate_complete_pc_literal
from build_unity_text_translation import (
    ALMANAC_FILES, ALMANAC_SCHEMAS, is_usable_pc_translation,
    load_pc_maps, merge_android_almanac, merge_android_detail_strings,
)
from build_unity_ui_translation import (
    hierarchy_for_component, read_tmp_text, replace_tmp_text, serialized_string,
)
from overlay_text_assets import normalize_overlay_text_asset


def wording(text):
    # These tags affect presentation, not PC terminology.
    return re.sub(r"</?(?:size|nobr)(?:=[^>]+)?>", "", text, flags=re.I).replace("\u2014", "-").replace("\r\n", "\n")


def balance_pc_color_tags(text):
    """Keep PC wording while dropping orphan closes and closing open colors.

    Some complete upstream fields have an extra </color> (e.g. plant 5000
    cost at e24586aa). Apply only to imported PC fields, not existing UI.
    """
    depth = 0
    def replace(match):
        nonlocal depth
        tag = match.group(0)
        if tag.lower().startswith('</'):
            if depth == 0:
                return ''
            depth -= 1
        else:
            depth += 1
        return tag
    normalized = re.sub(r'<color=[^>]+>|</color>', replace, text, flags=re.I)
    return normalized + '</color>' * depth


def balance_pc_rich_text(text):
    """Repair paired TMP style tags while retaining text and active styles."""
    stack = []
    def replace(match):
        closing, name = match.group(1), match.group(2).lower()
        if not closing:
            stack.append((name, match.group(0)))
            return match.group(0)
        positions = [i for i, (tag, _) in enumerate(stack) if tag == name]
        if not positions:
            return ''
        index = positions[-1]
        reopen = stack[index + 1:]
        del stack[index:]
        stack.extend(reopen)
        return (''.join(f'</{tag}>' for tag, _ in reversed(reopen))
                + match.group(0) + ''.join(tag for _, tag in reopen))
    result = re.sub(r'<(/?)(color|size|nobr|b|i|u|s|sub|sup)(?:=[^>]*)?>',
                    replace, text, flags=re.I)
    return result + ''.join(f'</{tag}>' for tag, _ in reversed(stack))


def prefer_pc_tree(source, current, exact, regexes, changes, path=(), deferred=None, repair_existing_markup=False):
    """Consult original source keys even when the candidate is already English."""
    if isinstance(source, str) and isinstance(current, str):
        target, method = translate_complete_pc_literal(source, exact, regexes)
        if method and re.search(r"<size=0(?:%?)>", current, re.I):
            if deferred is not None:
                deferred.append({"field": list(path), "source": source, "current": current, "pc": target,
                                 "reason": "Shipped text is hidden with size=0; preserve visibility pending context review."})
            return current
        if method:
            if repair_existing_markup and wording(target) == wording(current):
                # Retain Android size/wrapping choices when wording agrees.
                repaired = balance_pc_rich_text(current)
                if repaired != current:
                    changes.append({"field": list(path), "source": source, "before": current,
                                    "after": repaired, "method": "pc_markup_cleanup"})
                    return repaired
        if method and wording(target) != wording(current):
            target = balance_pc_rich_text(target)
            changes.append({"field": list(path), "source": source, "before": current, "after": target, "method": method})
            return target
    elif isinstance(source, dict) and isinstance(current, dict):
        result = dict(current)
        for key in source.keys() & current.keys():
            result[key] = prefer_pc_tree(source[key], current[key], exact, regexes, changes, path + (key,), deferred, repair_existing_markup)
        return result
    elif isinstance(source, list) and isinstance(current, list) and len(source) == len(current):
        return [prefer_pc_tree(a, b, exact, regexes, changes, path + (index,), deferred, repair_existing_markup) for index, (a, b) in enumerate(zip(source, current))]
    return current


def ui_exception(current, hierarchy, target):
    """Narrow, existing Android semantic/layout exceptions; never plant names."""
    if (current == "The Gods: Evolved\nPurgatory"
            and hierarchy == ["Name", "Window", "Level_1", "HotLevelMenu"]
            and wording(target) in {"The Gods: Evolved\nPurgatory", "The Gods: Evolved - Purgatory"}):
        return "Android Recommended Levels card needs two lines to fit its title."
    if current == "Close" and any(part in {"Goback", "Close", "Quit"} for part in hierarchy):
        return "PC Disabled is a toggle state; this Android component closes a window."
    if "Skin" in hierarchy and "AlmanacPlantMenu" in hierarchy:
        return "Existing compact skin-selector caption avoids overlapping arrows."
    if "LETS ROCK" in current:
        return "Existing approved button artwork/font text."
    if "Difficulty" in hierarchy and re.search(r"\b\d+: ", current):
        return "Android difficulty caption includes the numeric tier."
    if "Brain" in hierarchy and "Points" in hierarchy and target.startswith("$"):
        return "PC currency regex does not describe this Android points counter."
    return None


def snapshot(bundle):
    env = UnityPy.load(str(bundle))
    objects = {(obj.assets_file.name, obj.path_id): obj for obj in env.objects}
    text_assets, ui = {}, {}
    for key, obj in objects.items():
        if obj.type.name == "TextAsset":
            data = obj.parse_as_object()
            text_assets[key] = (data.m_Name, data.m_Script)
        elif obj.type.name == "MonoBehaviour":
            parsed = read_tmp_text(bytes(obj.get_raw_data()))
            if parsed is not None and parsed[0]:
                ui[key] = (parsed[0], hierarchy_for_component(objects, key))
    del objects, env
    gc.collect()
    return text_assets, ui


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-bundle", required=True, type=Path)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--localization-dir", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--include-ui-candidates", action="store_true",
        help="also apply UI wording candidates after their screen context has been reviewed",
    )
    args = parser.parse_args()
    if args.output and args.output.resolve() in {args.source_bundle.resolve(), args.base_bundle.resolve()}:
        raise ValueError("output must not overwrite an input bundle")
    source_assets, source_ui = snapshot(args.source_bundle)
    exact, _, regexes, _ = load_pc_translations(args.localization_dir / "Strings", include_android_fallbacks=False)
    detail_exact, _, _ = load_pc_maps(args.localization_dir)
    env = UnityPy.load(str(args.base_bundle))
    expected_objects = {}
    expected_text = {}
    changes, exceptions, ui_candidates, deferred_text_fields = [], [], [], []
    counts = collections.Counter()
    for obj in env.objects:
        key = (obj.assets_file.name, obj.path_id)
        before_raw = bytes(obj.get_raw_data())
        expected_objects[key] = hashlib.sha256(before_raw).hexdigest()
        if obj.type.name == "TextAsset" and key in source_assets:
            name, source_text = source_assets[key]
            data = obj.parse_as_object()
            old_text = data.m_Script
            fields = []
            try:
                source = json.loads(source_text.lstrip("\ufeff"))
                current = json.loads(old_text.lstrip("\ufeff"))
            except ValueError:
                target, method = translate_complete_pc_literal(source_text, exact, regexes)
                new_text = target if method else old_text
            else:
                if name in ALMANAC_FILES:
                    list_key, id_key = ALMANAC_SCHEMAS[name]
                    pc_file = args.localization_dir / "Almanac" / ALMANAC_FILES[name]
                    dump = args.localization_dir.parents[1] / "Dumps" / f"{name}.json"
                    merged, merge_counts = merge_android_almanac(name, source_text, dump.read_text(encoding="utf-8-sig"), pc_file.read_text(encoding="utf-8-sig"), {})
                    approved = json.loads(merged)[list_key]
                    by_id = {item[id_key]: item for item in current[list_key]}
                    source_by_id = {item[id_key]: item for item in source[list_key]}
                    if list(by_id) != list(source_by_id):
                        raise ValueError(f"{name}: candidate record IDs/order differ from official Android")
                    for translated in approved:
                        ident = translated[id_key]
                        for field, value in translated.items():
                            if not isinstance(value, str) or value == source_by_id[ident].get(field):
                                continue
                            old = by_id[ident].get(field)
                            if wording(value) != wording(old):
                                value = balance_pc_rich_text(value)
                                fields.append({"id": ident, "field": field, "before": old, "after": value, "method": "pc_almanac"})
                                by_id[ident][field] = value
                    counts[f"{name}:records"] = len(by_id)
                    counts[f"{name}:placeholder_fields_rejected"] = merge_counts["pc_placeholder_fields_rejected"]
                    updated = current
                elif name == "DetailStrings":
                    descriptions = json.loads((args.localization_dir / "Almanac/DetailStringsTranslate.json").read_text(encoding="utf-8-sig"))
                    merged, _ = merge_android_detail_strings(source_text, descriptions, detail_exact, True)
                    approved = json.loads(merged)
                    for original, actual, translated in zip(source["details"], current["details"], approved["details"]):
                        for field, value in translated.items():
                            if isinstance(value, str) and value != original.get(field) and wording(value) != wording(actual.get(field)):
                                fields.append({"title": original["title"], "field": field, "before": actual.get(field), "after": value, "method": "pc_mechanics"})
                                actual[field] = value
                    updated = current
                else:
                    deferred = []
                    updated = prefer_pc_tree(
                        source, current, exact, regexes, fields, deferred=deferred,
                        repair_existing_markup=name in {"level1395-水草大蘑菇", "level1204-浮空保护伞"},
                    )
                    deferred_text_fields.extend({"asset": name, **item} for item in deferred)
                new_text = json.dumps(updated, ensure_ascii=False, indent=4) if fields else old_text
            new_text, _, _ = normalize_overlay_text_asset(name, new_text)
            if new_text != old_text:
                old_field = serialized_string(old_text)
                if before_raw.count(old_field) != 1:
                    raise ValueError(f"TextAsset script field is not unique: {key}")
                # Replace only the serialized script field. UnityPy's deferred
                # typetree cache otherwise makes get_raw_data stale before save.
                obj.set_raw_data(before_raw.replace(old_field, serialized_string(new_text), 1))
                expected_text[key] = new_text
                changes.append({"kind": "TextAsset", "key": list(key), "name": name, "fields": fields})
                counts["TextAsset:changed"] += 1
                counts["TextAsset:fields"] += len(fields)
        elif obj.type.name == "MonoBehaviour" and key in source_ui:
            parsed = read_tmp_text(before_raw)
            if parsed is None:
                continue
            source, hierarchy = source_ui[key]
            current = parsed[0]
            target, method = translate_complete_pc_literal(source, exact, regexes)
            if not method or wording(target) == wording(current):
                continue
            reason = ui_exception(current, hierarchy, target)
            if reason:
                exceptions.append({"key": list(key), "current": current, "pc": target, "reason": reason})
                continue
            if not args.include_ui_candidates:
                # The confirmed plant rename preserves this exact released
                # label's markup and line breaks. Other UI wording is inventoried
                # for contextual review before changing live screens.
                reviewed_name = current.replace("Doomspike-shroom", "Glacier-shroom")
                if reviewed_name != current and wording(reviewed_name) == wording(target):
                    target = reviewed_name
                else:
                    ui_candidates.append({
                        "key": list(key), "hierarchy": hierarchy, "source": source,
                        "current": current, "pc": target, "method": method,
                        "reason": "Completed PC wording exists; verify Android screen context before applying.",
                    })
                    continue
            # Keep the existing component's size override, not the PC scale.
            if args.include_ui_candidates:
                size = re.match(r"(<size=[^>]+>)", current, flags=re.I)
                target = wording(target)
                if size:
                    target = size.group(1) + target + "</size>"
            obj.set_raw_data(replace_tmp_text(before_raw, target))
            expected_text[key] = target
            changes.append({"kind": "TMP", "key": list(key), "hierarchy": hierarchy, "source": source, "before": current, "after": target, "method": method})
            counts["TMP:changed"] += 1
        if key in expected_text:
            # get_raw_data reads the ORIGINAL stream even after set_raw_data.
            # UnityPy writes the replacement from obj.data. Hash that buffer.
            expected_objects[key] = hashlib.sha256(obj.data).hexdigest()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(env.file.save(packer="lz4"))
        del env
        gc.collect()
        verified = UnityPy.load(str(args.output))
        actual_keys = set()
        for obj in verified.objects:
            key = (obj.assets_file.name, obj.path_id)
            actual_keys.add(key)
            assert hashlib.sha256(bytes(obj.get_raw_data())).hexdigest() == expected_objects[key], f"Object changed unexpectedly: {key}"
            if key in expected_text:
                text = obj.parse_as_object().m_Script if obj.type.name == "TextAsset" else read_tmp_text(bytes(obj.get_raw_data()))[0]
                assert text == expected_text[key], f"Text round-trip failed: {key}"
        assert actual_keys == set(expected_objects), "Object inventory changed"
        counts["verified_objects"] = len(actual_keys)
    report = {
        "counts": dict(counts), "changes": changes, "android_exceptions": exceptions,
        "ui_candidates_for_context_review": ui_candidates,
        "deferred_text_fields": deferred_text_fields,
        "source_bundle": {"path": str(args.source_bundle), "sha256": sha256(args.source_bundle)},
        "base_bundle": {"path": str(args.base_bundle), "sha256": sha256(args.base_bundle)},
        "output": None if args.output is None else {"path": str(args.output), "sha256": sha256(args.output)},
        "policy": "Usable source-aligned PC text takes priority. Missing PC fields retain existing wording; no AI-generated translations.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"counts": dict(counts), "exceptions": len(exceptions), "ui_candidates_for_context_review": len(ui_candidates)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
