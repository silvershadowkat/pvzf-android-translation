#!/usr/bin/env python3
"""Build a deterministic translated IL2CPP global-metadata.dat.

The tool always starts from a clean metadata file, rebuilds the string-literal
database once at EOF, and rewrites the literal lookup table.  It deliberately
does not patch an already-patched output, preventing the repeated file growth
seen in older Android translation builds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


MAGIC = b"\xaf\x1b\xb1\xfa"
CJK_RE = re.compile(r"[\u3400-\u9fff]")
EXACT_FILES = ("translation_strings.json", "customlevel_strings.json", "abyss_buffs.json")
REGEX_FILES = ("translation_regexs.json", "customlevel_regexs.json")
STRUCTURED_PAIR_FILES = ("travel_buffs.json", "tips_fs.json", "tips_iz.json")

# Confirmed against the Android 3.8.1 UI.  These are runtime format fragments
# used by ZenGarden.GardenShopSlot, so the PC translator's regex for completed
# shop strings never sees them with concrete numbers substituted.
ANDROID_CONFIRMED_EXACT = {
    "\n已持有{0}个": "\nOwned: {0}",
    "{0}\n价格：{1}": "{0}\nCost: {1}",
}


@dataclass(frozen=True)
class MetadataLayout:
    lookup_offset: int
    lookup_size: int
    data_offset: int
    data_size: int


@dataclass(frozen=True)
class Literal:
    length: int
    offset: int
    raw: bytes
    text: str


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_metadata(data: bytes) -> tuple[MetadataLayout, list[Literal]]:
    if data[:4] != MAGIC:
        raise ValueError("not a supported IL2CPP global-metadata.dat")
    lookup_offset, lookup_size, data_offset, data_size = struct.unpack_from("<4I", data, 8)
    if lookup_size % 8:
        raise ValueError(f"literal lookup size is not divisible by 8: {lookup_size}")
    if lookup_offset + lookup_size > len(data) or data_offset > len(data):
        raise ValueError("literal table points outside the metadata file")

    literals: list[Literal] = []
    for index in range(lookup_size // 8):
        length, relative_offset = struct.unpack_from("<2I", data, lookup_offset + index * 8)
        start = data_offset + relative_offset
        end = start + length
        # Some existing fan patches append a larger translated database but
        # forget to update the header's data-size field.  Accept those files as
        # references as long as every entry remains inside the physical file.
        # Newly generated outputs always receive the correct size below.
        if end > len(data):
            raise ValueError(f"literal {index} points outside the metadata file")
        raw = data[start:end]
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"literal {index} is not valid UTF-8") from exc
        literals.append(Literal(length, relative_offset, raw, text))
    return MetadataLayout(lookup_offset, lookup_size, data_offset, data_size), literals


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def aligned_string_pairs(source: object, translated: object) -> Iterable[tuple[str, str]]:
    if isinstance(source, str) and isinstance(translated, str):
        yield source, translated
    elif isinstance(source, dict) and isinstance(translated, dict):
        for key, value in source.items():
            if key in translated:
                yield from aligned_string_pairs(value, translated[key])
    elif isinstance(source, list) and isinstance(translated, list):
        for source_item, translated_item in zip(source, translated):
            yield from aligned_string_pairs(source_item, translated_item)


def load_pc_translations(
    strings_dir: Path,
) -> tuple[dict[str, str], list[tuple[str, str, re.Pattern[str], str]], dict[str, int]]:
    exact: dict[str, str] = {}
    regex_entries: list[tuple[str, str, re.Pattern[str], str]] = []
    counts: dict[str, int] = {}

    for filename in EXACT_FILES:
        path = strings_dir / filename
        if not path.exists():
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a JSON object")
        added = 0
        for source, translated in payload.items():
            if (
                isinstance(source, str)
                and isinstance(translated, str)
                and CJK_RE.search(source)
                and not source.startswith("-------")
            ):
                exact[source] = translated
                added += 1
        counts[filename] = added

    dumps_dir = strings_dir.parents[2] / "Dumps"
    for filename in STRUCTURED_PAIR_FILES:
        source_path = dumps_dir / filename
        translated_path = strings_dir / filename
        if not source_path.exists() or not translated_path.exists():
            continue
        source_payload = read_json(source_path)
        translated_payload = read_json(translated_path)
        added = 0
        for source, translated in aligned_string_pairs(source_payload, translated_payload):
            if CJK_RE.search(source) and translated and source != translated and source not in exact:
                exact[source] = translated
                added += 1
        counts[f"structured:{filename}"] = added

    for filename in REGEX_FILES:
        path = strings_dir / filename
        if not path.exists():
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a JSON object")
        added = 0
        for pattern, translated in payload.items():
            if not isinstance(pattern, str) or not isinstance(translated, str):
                continue
            compiled = re.compile(pattern, re.DOTALL)
            cjk_runs = re.findall(r"[\u3400-\u9fff]+", pattern)
            anchor = max(cjk_runs, key=len) if cjk_runs else ""
            regex_entries.append((pattern, translated, compiled, anchor))
            added += 1
        counts[filename] = added

    exact.update(ANDROID_CONFIRMED_EXACT)
    counts["android_confirmed_exact"] = len(ANDROID_CONFIRMED_EXACT)

    return exact, regex_entries, counts


def observed_translations(
    label: str, base_path: Path, translated_path: Path
) -> tuple[dict[str, str], dict[str, object]]:
    base_data = base_path.read_bytes()
    translated_data = translated_path.read_bytes()
    _, base_literals = parse_metadata(base_data)
    _, translated_literals = parse_metadata(translated_data)
    if len(base_literals) != len(translated_literals):
        raise ValueError(
            f"reference pair {label!r} has different literal counts: "
            f"{len(base_literals)} vs {len(translated_literals)}"
        )

    mapping: dict[str, str] = {}
    conflicts = 0
    changed = 0
    accepted = 0
    for source, target in zip(base_literals, translated_literals):
        if source.raw == target.raw:
            continue
        changed += 1
        if not CJK_RE.search(source.text) or CJK_RE.search(target.text) or not target.text:
            continue
        previous = mapping.get(source.text)
        if previous is not None and previous != target.text:
            conflicts += 1
            continue
        mapping[source.text] = target.text
        accepted += 1

    stats = {
        "label": label,
        "base": str(base_path.resolve()),
        "translated": str(translated_path.resolve()),
        "changed_literal_occurrences": changed,
        "accepted_occurrences": accepted,
        "unique_mappings": len(mapping),
        "conflicts": conflicts,
    }
    return mapping, stats


def csharp_format(template: str, values: Iterable[str]) -> str:
    values_list = list(values)
    open_token = "\0OPEN_BRACE\0"
    close_token = "\0CLOSE_BRACE\0"
    protected = template.replace("{{", open_token).replace("}}", close_token)

    def replace(match: re.Match[str]) -> str:
        index = int(match.group(1))
        return values_list[index] if index < len(values_list) else match.group(0)

    protected = re.sub(r"\{(\d+)(?:,[^}:]+)?(?::[^}]+)?\}", replace, protected)
    return protected.replace(open_token, "{").replace(close_token, "}")


def translate_literal(
    text: str,
    exact: dict[str, str],
    observed: dict[str, tuple[str, str]],
    regex_entries: list[tuple[str, str, re.Pattern[str], str]],
) -> tuple[str, str | None]:
    if not CJK_RE.search(text):
        return text, None
    if text in exact:
        return exact[text], "pc_exact"
    if text in observed:
        translated, label = observed[text]
        return translated, f"reference:{label}"

    for _pattern, template, compiled, anchor in regex_entries:
        if anchor and anchor not in text:
            continue
        match = compiled.search(text)
        if match is None:
            continue
        dynamic: list[str] = []
        for group in match.groups():
            if group in exact:
                dynamic.append(exact[group])
            elif group in observed:
                dynamic.append(observed[group][0])
            else:
                dynamic.append(group)
        result = csharp_format(template, dynamic)
        if result != text:
            return result, "pc_regex"
    return text, None


def build_metadata(base: bytes, layout: MetadataLayout, translated: list[bytes]) -> bytes:
    output = bytearray(base)
    new_data_offset = len(output)
    cursor = 0
    for index, raw in enumerate(translated):
        struct.pack_into("<2I", output, layout.lookup_offset + index * 8, len(raw), cursor)
        cursor += len(raw)
    output.extend(b"".join(translated))
    struct.pack_into("<I", output, 16, new_data_offset)
    struct.pack_into("<I", output, 20, cursor)
    return bytes(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path, help="clean official global-metadata.dat")
    parser.add_argument("--strings-dir", required=True, type=Path, help="PC English Strings directory")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument(
        "--reference-pair",
        action="append",
        nargs=3,
        metavar=("LABEL", "CHINESE_METADATA", "TRANSLATED_METADATA"),
        default=[],
        help="fallback mappings learned from a known Android Chinese/English pair; order sets priority",
    )
    args = parser.parse_args()

    base = args.base.read_bytes()
    layout, literals = parse_metadata(base)
    exact, regex_entries, pc_counts = load_pc_translations(args.strings_dir)

    observed: dict[str, tuple[str, str]] = {}
    reference_stats: list[dict[str, object]] = []
    reference_conflicts: list[dict[str, str]] = []
    for label, base_name, translated_name in args.reference_pair:
        mapping, stats = observed_translations(label, Path(base_name), Path(translated_name))
        reference_stats.append(stats)
        for source, target in mapping.items():
            if source in exact:
                continue
            if source in observed and observed[source][0] != target:
                reference_conflicts.append(
                    {
                        "source": source,
                        "kept_label": observed[source][1],
                        "kept_translation": observed[source][0],
                        "discarded_label": label,
                        "discarded_translation": target,
                    }
                )
                continue
            observed.setdefault(source, (target, label))

    translated_bytes: list[bytes] = []
    method_counts: dict[str, int] = {}
    changes: list[dict[str, object]] = []
    cjk_before = 0
    cjk_after = 0
    for index, literal in enumerate(literals):
        if CJK_RE.search(literal.text):
            cjk_before += 1
        translated_text, method = translate_literal(literal.text, exact, observed, regex_entries)
        if CJK_RE.search(translated_text):
            cjk_after += 1
        raw = translated_text.encode("utf-8")
        translated_bytes.append(raw)
        if method is not None and raw != literal.raw:
            method_counts[method] = method_counts.get(method, 0) + 1
            changes.append(
                {
                    "index": index,
                    "method": method,
                    "source": literal.text,
                    "translation": translated_text,
                }
            )

    output = build_metadata(base, layout, translated_bytes)
    output_layout, output_literals = parse_metadata(output)
    if [item.raw for item in output_literals] != translated_bytes:
        raise RuntimeError("self-validation failed: output literals do not match generated data")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    report = {
        "format_version": 1,
        "base": {
            "path": str(args.base.resolve()),
            "size": len(base),
            "sha256": sha256(base),
            "literal_count": len(literals),
            "literal_data_offset": layout.data_offset,
            "literal_data_size": layout.data_size,
            "cjk_literal_occurrences": cjk_before,
        },
        "output": {
            "path": str(args.output.resolve()),
            "size": len(output),
            "sha256": sha256(output),
            "literal_count": len(output_literals),
            "literal_data_offset": output_layout.data_offset,
            "literal_data_size": output_layout.data_size,
            "cjk_literal_occurrences": cjk_after,
        },
        "pc_translation_entries": pc_counts,
        "reference_pairs": reference_stats,
        "reference_conflicts": reference_conflicts,
        "method_counts": dict(sorted(method_counts.items())),
        "changed_literal_occurrences": len(changes),
        "changes": changes,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("base", "output", "method_counts", "changed_literal_occurrences")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
