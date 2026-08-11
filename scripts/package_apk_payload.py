#!/usr/bin/env python3
"""Replace translated payloads in an APK without decoding/rebuilding resources.

The resulting APK is unsigned. Run Android SDK zipalign and apksigner after
this script. Existing JAR signature entries are removed; unrelated META-INF
metadata is preserved.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path


DATA_ENTRY = "assets/bin/Data/data.unity3d"
METADATA_ENTRY = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
SIGNATURE_SUFFIXES = (".SF", ".RSA", ".DSA", ".EC")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def is_old_signature(filename: str) -> bool:
    upper = filename.upper()
    if not upper.startswith("META-INF/"):
        return False
    return upper == "META-INF/MANIFEST.MF" or upper.endswith(SIGNATURE_SUFFIXES)


def copy_entry(source: zipfile.ZipFile, target: zipfile.ZipFile, info: zipfile.ZipInfo) -> None:
    cloned = copy.copy(info)
    with source.open(info, "r") as reader, target.open(cloned, "w", force_zip64=True) as writer:
        shutil.copyfileobj(reader, writer, length=8 * 1024 * 1024)


def write_replacement(target: zipfile.ZipFile, original: zipfile.ZipInfo, replacement: Path) -> None:
    cloned = copy.copy(original)
    cloned.file_size = 0
    cloned.compress_size = 0
    cloned.CRC = 0
    with replacement.open("rb") as reader, target.open(cloned, "w", force_zip64=True) as writer:
        shutil.copyfileobj(reader, writer, length=8 * 1024 * 1024)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-apk", required=True, type=Path)
    parser.add_argument("--data-bundle", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="unsigned output APK")
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    replacements = {DATA_ENTRY: args.data_bundle, METADATA_ENTRY: args.metadata}
    for name, path in replacements.items():
        if not path.is_file():
            raise FileNotFoundError(f"missing replacement for {name}: {path}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary_handle, temporary_name = tempfile.mkstemp(
        prefix=args.output.name + ".", suffix=".tmp", dir=args.output.parent
    )
    os.close(temporary_handle)
    temporary = Path(temporary_name)

    removed_signatures: list[str] = []
    replaced: list[dict[str, object]] = []
    seen: set[str] = set()
    try:
        with zipfile.ZipFile(args.base_apk, "r") as source, zipfile.ZipFile(
            temporary, "w", allowZip64=True
        ) as target:
            for info in source.infolist():
                if is_old_signature(info.filename):
                    removed_signatures.append(info.filename)
                    continue
                replacement = replacements.get(info.filename)
                if replacement is None:
                    copy_entry(source, target, info)
                    continue
                write_replacement(target, info, replacement)
                seen.add(info.filename)
                replaced.append(
                    {
                        "entry": info.filename,
                        "original_size": info.file_size,
                        "replacement_size": replacement.stat().st_size,
                        "compression_method": info.compress_type,
                        "replacement_sha256": sha256_file(replacement),
                    }
                )
        missing = replacements.keys() - seen
        if missing:
            raise KeyError(f"base APK is missing expected entries: {sorted(missing)}")
        os.replace(temporary, args.output)
    finally:
        if temporary.exists():
            temporary.unlink()

    with zipfile.ZipFile(args.output, "r") as result:
        result_names = set(result.namelist())
        remaining_signatures = [name for name in result_names if is_old_signature(name)]
        if remaining_signatures:
            raise RuntimeError(f"old signature files remain: {remaining_signatures}")
        for entry, replacement in replacements.items():
            info = result.getinfo(entry)
            if info.file_size != replacement.stat().st_size:
                raise RuntimeError(f"replacement size validation failed for {entry}")
            digest = hashlib.sha256()
            with result.open(entry, "r") as handle:
                while chunk := handle.read(8 * 1024 * 1024):
                    digest.update(chunk)
            if digest.hexdigest() != sha256_file(replacement):
                raise RuntimeError(f"replacement hash validation failed for {entry}")

    report = {
        "format_version": 1,
        "base_apk": {
            "path": str(args.base_apk.resolve()),
            "size": args.base_apk.stat().st_size,
            "sha256": sha256_file(args.base_apk),
        },
        "unsigned_output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
        },
        "removed_signature_entries": sorted(removed_signatures),
        "replaced_entries": replaced,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
