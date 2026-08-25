#!/usr/bin/env python3
"""Replace the embedded Android changelog with the current PC English text."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import re
from pathlib import Path

import UnityPy

from build_unity_ui_translation import read_tmp_text, replace_tmp_text


CJK_RE = re.compile(r"[\u3400-\u9fff]")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def clean_changelog(value: str) -> str:
    languages_note = (
        "If you'd like to change the language of the translation, make sure to check out "
        'the "Languages" menu in the bottom right of this menu.'
    )
    value = value.replace("LanPiaoPiaoFly", "蓝飘飘fly")
    value = value.replace(languages_note, "")
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def find_changelog(env) -> tuple[object, str]:
    matches = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        parsed = read_tmp_text(bytes(obj.get_raw_data()))
        if parsed is None:
            continue
        text = parsed[0]
        if len(text) > 500 and "3.9" in text and "版本更新" in text:
            matches.append((obj, text))
    if len(matches) != 1:
        raise RuntimeError(f"expected one official Android 3.9 changelog component, found {len(matches)}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--source-bundle", required=True, type=Path)
    parser.add_argument("--pc-changelog", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    source_env = UnityPy.load(str(args.source_bundle))
    source_obj, source_text = find_changelog(source_env)
    key = (source_obj.assets_file.name, source_obj.path_id)
    del source_env
    gc.collect()

    replacement = clean_changelog(args.pc_changelog.read_text(encoding="utf-8-sig"))
    if not replacement or CJK_RE.search(replacement.replace("蓝飘飘", "")):
        raise RuntimeError("current PC changelog is empty or unexpectedly retains CJK")

    env = UnityPy.load(str(args.base_bundle))
    matches = [
        obj for obj in env.objects
        if obj.type.name == "MonoBehaviour"
        and (obj.assets_file.name, obj.path_id) == key
    ]
    if len(matches) != 1:
        raise RuntimeError(f"target changelog component {key} is missing")
    target = matches[0]
    current = read_tmp_text(bytes(target.get_raw_data()))
    if current is None:
        raise RuntimeError(f"target changelog component {key} no longer has a supported TMP string")
    target.set_raw_data(replace_tmp_text(bytes(target.get_raw_data()), replacement))

    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    del output_bytes, env
    gc.collect()

    check_env = UnityPy.load(str(args.output))
    check_obj = next(
        obj for obj in check_env.objects
        if obj.type.name == "MonoBehaviour"
        and (obj.assets_file.name, obj.path_id) == key
    )
    reopened = read_tmp_text(bytes(check_obj.get_raw_data()))
    if reopened is None or reopened[0] != replacement:
        raise RuntimeError("reopened changelog validation failed")
    del check_env

    report = {
        "format_version": 1,
        "base": {"path": str(args.base_bundle.resolve()), "sha256": sha256_file(args.base_bundle)},
        "source": {"path": str(args.source_bundle.resolve()), "sha256": sha256_file(args.source_bundle)},
        "pc_changelog": {
            "path": str(args.pc_changelog.resolve()),
            "sha256": sha256_file(args.pc_changelog),
        },
        "component": {"file": key[0], "path_id": key[1]},
        "official_length": len(source_text),
        "before_length": len(current[0]),
        "after_length": len(replacement),
        "output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
