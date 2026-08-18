#!/usr/bin/env python3
"""Create and verify a UTF-8-safe ZIP of a prepared PC comparison build."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def windows_path_key(name: str) -> str:
    parts = []
    for part in PurePosixPath(name).parts:
        normalized = unicodedata.normalize("NFC", part).rstrip(" .").casefold()
        parts.append(normalized)
    return "/".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--exclude", action="append", default=[])
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output.resolve()
    excludes = {PurePosixPath(value).as_posix() for value in args.exclude}
    if not root.is_dir():
        raise SystemExit(f"source root is not a directory: {root}")
    if output == root or root in output.parents:
        raise SystemExit("output ZIP must be outside the source root")

    files: list[tuple[Path, str]] = []
    for source in root.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(root).as_posix()
        if relative in excludes:
            continue
        files.append((source, relative))
    files.sort(key=lambda item: (windows_path_key(item[1]), item[1]))

    collisions: dict[str, list[str]] = defaultdict(list)
    for _, relative in files:
        collisions[windows_path_key(relative)].append(relative)
    collisions = {
        key: values for key, values in collisions.items() if len(values) > 1
    }
    if collisions:
        raise SystemExit(
            "source contains paths that collide on Windows:\n"
            + json.dumps(collisions, ensure_ascii=False, indent=2)
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    try:
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
            allowZip64=True,
        ) as archive:
            for source, relative in files:
                archive.write(source, relative)

        expected_names = [relative for _, relative in files]
        with zipfile.ZipFile(temporary) as archive:
            actual_names = archive.namelist()
            if actual_names != expected_names:
                raise RuntimeError("archive entry list does not match the source list")
            if len(actual_names) != len(set(actual_names)):
                raise RuntimeError("archive contains duplicate entry names")
            bad_entry = archive.testzip()
            if bad_entry is not None:
                raise RuntimeError(f"archive CRC validation failed: {bad_entry}")
            non_ascii_without_utf8 = [
                info.filename
                for info in archive.infolist()
                if not info.filename.isascii() and not (info.flag_bits & 0x800)
            ]
            if non_ascii_without_utf8:
                raise RuntimeError(
                    "non-ASCII archive names are missing the UTF-8 flag: "
                    + repr(non_ascii_without_utf8[:5])
                )
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()

    report = {
        "format_version": 1,
        "source_root": str(root),
        "output": str(output),
        "file_count": len(files),
        "non_ascii_path_count": sum(not relative.isascii() for _, relative in files),
        "excluded_paths": sorted(excludes),
        "size": output.stat().st_size,
        "sha256": sha256_file(output),
        "duplicate_entry_count": 0,
        "windows_path_collision_count": 0,
        "crc_bad_entry": None,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
