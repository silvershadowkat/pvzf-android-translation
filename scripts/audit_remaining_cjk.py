#!/usr/bin/env python3
"""Audit CJK-bearing IL2CPP text, TextAssets, and serialized strings."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_metadata_translation import parse_metadata  # noqa: E402


CJK_RE = re.compile(r"[\u3400-\u9fff]")
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
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--dummy-dll-dir", required=True, type=Path)
    parser.add_argument(
        "--dump-cs",
        type=Path,
        help="optional Il2CppDumper dump.cs used to inventory CJK enum definition names",
    )
    parser.add_argument("--unity-version", default="2022.3.62f1")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    _, literals = parse_metadata(args.metadata.read_bytes())
    metadata_groups = defaultdict(list)
    for index, literal in enumerate(literals):
        if CJK_RE.search(literal.text):
            metadata_groups[literal.text].append(index)
    metadata = [
        {"text": safe_text(text), "occurrences": len(indices), "indices": indices}
        for text, indices in sorted(metadata_groups.items(), key=lambda item: (-len(item[1]), item[0]))
    ]

    generator = TypeTreeGenerator(args.unity_version)
    generator.load_local_dll_folder(str(args.dummy_dll_dir))
    env = UnityPy.load(str(args.bundle))
    env.typetree_generator = generator
    text_assets = []
    serialized_objects = []
    typetree_failures = []
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
    report = {
        "format_version": 2,
        "metadata": {
            "cjk_occurrences": sum(item["occurrences"] for item in metadata),
            "unique_strings": len(metadata),
            "strings": metadata,
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
