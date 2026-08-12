#!/usr/bin/env python3
"""Verify that a translated APK changes only its declared Unity data payloads.

This is a comparative release audit, not a general malware guarantee. It
proves that the Android manifest, DEX bytecode, native libraries, resources,
and every other non-signature entry are byte-identical to the supplied base
APK, while also checking ZIP integrity and package metadata.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath


DATA_ENTRIES = {
    "assets/bin/Data/data.unity3d",
    "assets/bin/Data/Managed/Metadata/global-metadata.dat",
}
SIGNATURE_SUFFIXES = (".SF", ".RSA", ".DSA", ".EC")


def is_signature(name: str) -> bool:
    upper = name.upper()
    return upper == "META-INF/MANIFEST.MF" or (
        upper.startswith("META-INF/") and upper.endswith(SIGNATURE_SUFFIXES)
    )


def hash_entry(archive: zipfile.ZipFile, name: str) -> str:
    digest = hashlib.sha256()
    with archive.open(name) as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def unsafe_name(name: str) -> bool:
    path = PurePosixPath(name.replace("\\", "/"))
    return path.is_absolute() or ".." in path.parts


def parse_badging(aapt2: Path, apk: Path) -> dict[str, object]:
    result = subprocess.run(
        [str(aapt2), "dump", "badging", str(apk)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = result.stdout
    package = re.search(
        r"^package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'",
        output,
        re.MULTILINE,
    )
    label = re.search(r"^application-label:'([^']*)'", output, re.MULTILINE)
    permissions = sorted(set(re.findall(r"^uses-permission: name='([^']+)'", output, re.MULTILINE)))
    native = re.search(r"^native-code: (.*)$", output, re.MULTILINE)
    if package is None or label is None:
        raise RuntimeError(f"could not parse aapt2 badging for {apk}")
    return {
        "package": package.group(1),
        "version_code": package.group(2),
        "version_name": package.group(3),
        "application_label": label.group(1),
        "permissions": permissions,
        "native_code": native.group(1) if native else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-apk", required=True, type=Path)
    parser.add_argument("--release-apk", required=True, type=Path)
    parser.add_argument("--aapt2", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    with zipfile.ZipFile(args.base_apk) as base, zipfile.ZipFile(args.release_apk) as release:
        base_names = base.namelist()
        release_names = release.namelist()
        duplicate_base = sorted(name for name, count in collections.Counter(base_names).items() if count > 1)
        duplicate_release = sorted(
            name for name, count in collections.Counter(release_names).items() if count > 1
        )
        unsafe_entries = sorted({name for name in release_names if unsafe_name(name)})
        base_set = set(base_names)
        release_set = set(release_names)
        added_non_signatures = sorted(
            name for name in release_set - base_set if not is_signature(name)
        )
        removed_non_signatures = sorted(
            name for name in base_set - release_set if not is_signature(name)
        )

        unexpected_changes = []
        unchanged_entry_count = 0
        executable_checks = []
        expected_payloads = []
        for name in sorted(base_set & release_set):
            if is_signature(name):
                continue
            base_hash = hash_entry(base, name)
            release_hash = hash_entry(release, name)
            same = base_hash == release_hash
            if name in DATA_ENTRIES:
                expected_payloads.append(
                    {"entry": name, "base_sha256": base_hash, "release_sha256": release_hash}
                )
            elif not same:
                unexpected_changes.append(name)
            else:
                unchanged_entry_count += 1
            if name == "classes.dex" or (name.startswith("lib/") and name.endswith(".so")):
                executable_checks.append({"entry": name, "byte_identical": same, "sha256": release_hash})

        zip_test = release.testzip()
        manifest_identical = (
            hash_entry(base, "AndroidManifest.xml") == hash_entry(release, "AndroidManifest.xml")
        )

    base_badging = parse_badging(args.aapt2, args.base_apk)
    release_badging = parse_badging(args.aapt2, args.release_apk)
    badging_identical = base_badging == release_badging
    executable_identical = all(item["byte_identical"] for item in executable_checks)
    payloads_changed = {item["entry"] for item in expected_payloads if item["base_sha256"] != item["release_sha256"]}
    passed = all(
        (
            not duplicate_base,
            not duplicate_release,
            not unsafe_entries,
            not added_non_signatures,
            not removed_non_signatures,
            not unexpected_changes,
            zip_test is None,
            manifest_identical,
            badging_identical,
            executable_identical,
            payloads_changed == DATA_ENTRIES,
        )
    )
    report = {
        "format_version": 1,
        "scope": "comparative APK content audit; not a general malware guarantee",
        "passed": passed,
        "base_apk": str(args.base_apk.resolve()),
        "release_apk": str(args.release_apk.resolve()),
        "package": release_badging,
        "manifest_byte_identical": manifest_identical,
        "badging_identical": badging_identical,
        "zip_test_error_entry": zip_test,
        "duplicate_entries": {"base": duplicate_base, "release": duplicate_release},
        "unsafe_entry_names": unsafe_entries,
        "added_non_signature_entries": added_non_signatures,
        "removed_non_signature_entries": removed_non_signatures,
        "unexpected_changed_entries": unexpected_changes,
        "expected_changed_payloads": expected_payloads,
        "unchanged_non_signature_entry_count": unchanged_entry_count,
        "executable_entries": executable_checks,
        "executable_entries_byte_identical": executable_identical,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
