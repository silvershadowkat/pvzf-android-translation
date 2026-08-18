#!/usr/bin/env python3
"""Audit CJK-bearing IL2CPP text, TextAssets, and serialized strings."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_metadata_translation import (  # noqa: E402
    is_usable_pc_translation,
    load_pc_translations,
    parse_metadata,
    translate_literal,
)


CJK_RE = re.compile(r"[\u3400-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z]")
ENUM_BLOCK_RE = re.compile(
    r"(?ms)^(?:public|private|internal|protected)?\s*enum\s+(?P<name>[^\s/]+)"
    r"[^\n]*\n\{(?P<body>.*?)^\}"
)
ENUM_MEMBER_RE = re.compile(
    r"(?m)^\s*public\s+const\s+[^\s]+\s+(?P<name>[^\s=]+)\s*=\s*(?P<value>[^;]+);"
)


def walk_strings(value, path=()):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_strings(item, path + (index,))
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from walk_strings(item, path + (key,))


def safe_text(value: str) -> str:
    return value.encode("utf-8", "backslashreplace").decode("utf-8")


def audit_dump_enums(path: Path | None) -> list[dict[str, object]]:
    """Inventory CJK enum members that may surface through Enum.ToString().

    These names live in the metadata definition-string heap rather than the
    string-literal table. The original audit therefore missed player-facing
    enums such as InvestBuff and SynergyType even though their values appeared
    on screen. The inventory is intentionally broad and remains a review list:
    many enum names are internal and must not be translated blindly.
    """
    if path is None:
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    enums = []
    for block in ENUM_BLOCK_RE.finditer(text):
        members = [
            {"name": match.group("name"), "value": match.group("value").strip()}
            for match in ENUM_MEMBER_RE.finditer(block.group("body"))
            if CJK_RE.search(match.group("name"))
        ]
        if members:
            enums.append({"enum": block.group("name"), "member_count": len(members), "members": members})
    return enums


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument(
        "--bundle",
        type=Path,
        help="optional Unity bundle to scan for TextAssets and serialized strings",
    )
    parser.add_argument(
        "--dummy-dll-dir",
        type=Path,
        help="DummyDll directory required when --bundle is supplied",
    )
    parser.add_argument(
        "--dump-cs",
        type=Path,
        help="optional Il2CppDumper dump.cs used to inventory CJK enum definition names",
    )
    parser.add_argument(
        "--pc-strings-dir",
        type=Path,
        help=(
            "optional PC English Strings directory; reports any remaining metadata "
            "literal that the community rules can still translate"
        ),
    )
    parser.add_argument("--unity-version", default="2022.3.62f1")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    _, literals = parse_metadata(args.metadata.read_bytes())
    metadata_groups = defaultdict(list)
    mixed_language = []
    short_cjk_review = []
    for index, literal in enumerate(literals):
        if CJK_RE.search(literal.text):
            metadata_groups[literal.text].append(index)
            if LATIN_RE.search(literal.text):
                mixed_language.append({"index": index, "text": safe_text(literal.text)})
            if len(literal.text) <= 32 and "\n" not in literal.text:
                short_cjk_review.append({"index": index, "text": safe_text(literal.text)})
    metadata = [
        {"text": safe_text(text), "occurrences": len(indices), "indices": indices}
        for text, indices in sorted(metadata_groups.items(), key=lambda item: (-len(item[1]), item[0]))
    ]

    text_assets = []
    serialized_objects = []
    typetree_failures = []
    if args.bundle is not None:
        if args.dummy_dll_dir is None:
            parser.error("--dummy-dll-dir is required when --bundle is supplied")
        try:
            import UnityPy
            from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
        except ImportError as error:
            parser.error(
                "UnityPy is required only for --bundle scans; install requirements.txt "
                f"or omit --bundle ({error})"
            )
        generator = TypeTreeGenerator(args.unity_version)
        generator.load_local_dll_folder(str(args.dummy_dll_dir))
        env = UnityPy.load(str(args.bundle))
        env.typetree_generator = generator
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                data = obj.parse_as_object()
                try:
                    payload = json.loads(data.m_Script.lstrip("\ufeff"))
                except (json.JSONDecodeError, TypeError):
                    strings = [((), data.m_Script)]
                else:
                    strings = walk_strings(payload)
                matches = [
                    {"json_path": list(path), "text": safe_text(text)}
                    for path, text in strings
                    if CJK_RE.search(text)
                ]
                if matches:
                    text_assets.append(
                        {
                            "file": obj.assets_file.name,
                            "path_id": obj.path_id,
                            "name": data.m_Name,
                            "match_count": len(matches),
                            "matches": matches,
                        }
                    )
            elif obj.type.name == "MonoBehaviour":
                try:
                    tree = obj.read_typetree(check_read=False)
                except Exception as error:
                    raw = bytes(obj.get_raw_data())
                    decoded = raw.decode("utf-8", errors="ignore")
                    raw_cjk = sorted(set(CJK_RE.findall(decoded)))
                    if raw_cjk:
                        typetree_failures.append(
                            {
                                "file": obj.assets_file.name,
                                "path_id": obj.path_id,
                                "type": obj.type.name,
                                "error": str(error),
                                "raw_size": len(raw),
                                "decoded_cjk_characters": raw_cjk,
                            }
                        )
                    continue
                matches = [
                    {"field_path": list(path), "text": safe_text(text)}
                    for path, text in walk_strings(tree)
                    if CJK_RE.search(text)
                ]
                if matches:
                    serialized_objects.append(
                        {
                            "file": obj.assets_file.name,
                            "path_id": obj.path_id,
                            "type": obj.type.name,
                            "match_count": len(matches),
                            "matches": matches,
                        }
                    )

    enum_definitions = audit_dump_enums(args.dump_cs)
    pc_translatable_remnants = []
    pc_counts = None
    if args.pc_strings_dir is not None:
        exact, pc_exact_sources, regex_entries, pc_counts = load_pc_translations(
            args.pc_strings_dir
        )
        for index, literal in enumerate(literals):
            if not CJK_RE.search(literal.text):
                continue
            translated, method = translate_literal(
                literal.text,
                exact,
                pc_exact_sources,
                {},
                regex_entries,
            )
            if (
                method is not None
                and method.startswith("pc_")
                and translated != literal.text
                and is_usable_pc_translation(translated)
            ):
                pc_translatable_remnants.append(
                    {
                        "index": index,
                        "method": method,
                        "source": safe_text(literal.text),
                        "translation": safe_text(translated),
                    }
                )
    report = {
        "format_version": 3,
        "metadata": {
            "cjk_occurrences": sum(item["occurrences"] for item in metadata),
            "unique_strings": len(metadata),
            "strings": metadata,
            "mixed_language_occurrences": len(mixed_language),
            "mixed_language_review": mixed_language,
            "short_cjk_occurrences": len(short_cjk_review),
            "short_cjk_review": short_cjk_review,
            "pc_translation_entries": pc_counts,
            "pc_translatable_remnant_count": len(pc_translatable_remnants),
            "pc_translatable_remnants": pc_translatable_remnants,
        },
        "text_assets": {
            "asset_count": len(text_assets),
            "cjk_string_leaves": sum(item["match_count"] for item in text_assets),
            "assets": text_assets,
        },
        "serialized_objects": {
            "object_count": len(serialized_objects),
            "cjk_string_fields": sum(item["match_count"] for item in serialized_objects),
            "objects": serialized_objects,
        },
        "typetree_failures_with_utf8_lead_bytes": typetree_failures,
        "definition_enums": {
            "source": str(args.dump_cs.resolve()) if args.dump_cs else None,
            "review_note": (
                "Definition names can reach the UI through Enum.ToString(); "
                "do not translate this broad inventory without runtime confirmation."
            ),
            "enum_count": len(enum_definitions),
            "cjk_member_count": sum(item["member_count"] for item in enum_definitions),
            "enums": enum_definitions,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "metadata_cjk_occurrences": report["metadata"]["cjk_occurrences"],
                "metadata_unique_strings": report["metadata"]["unique_strings"],
                "metadata_mixed_language_occurrences": len(mixed_language),
                "metadata_short_cjk_occurrences": len(short_cjk_review),
                "metadata_pc_translatable_remnants": len(pc_translatable_remnants),
                "text_asset_count": report["text_assets"]["asset_count"],
                "text_asset_cjk_leaves": report["text_assets"]["cjk_string_leaves"],
                "serialized_object_count": report["serialized_objects"]["object_count"],
                "serialized_cjk_string_fields": report["serialized_objects"]["cjk_string_fields"],
                "typetree_failures_with_utf8_lead_bytes": len(typetree_failures),
                "definition_enum_count": len(enum_definitions),
                "definition_cjk_members": sum(item["member_count"] for item in enum_definitions),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
