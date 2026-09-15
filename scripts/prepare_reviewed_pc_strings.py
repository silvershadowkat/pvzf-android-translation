#!/usr/bin/env python3
"""Export pinned PC JSON inputs without changing the checkout; parse strictly."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

COMMIT = "e24586aaf9feb85eae6fc30af3460237778558ff"
REPAIR_PATH = "PvZ_Fusion_Translator/Localization/English/Strings/travel_buffs.json"
REPAIR_SHA256 = "539bd664f83a4b64e753eed5ba2cdaeaea98cb4af628cf35e231ed338d44b267"
SEPT15_COMMIT = "d9c05a39e7c0abb09f84ddfb15582885d60a0efe"
SEPT15_REPAIRS = {
    "translation_regexs.json": ("20b8cacf35d0a212ce9d9e9ae4600dc0a70a930a7226f7db0c1cd39bf7f2a8c0", (492,), (493,)),
    "translation_strings.json": ("3373ecdff1e344377c116ca8410f88bc723f433f9696bab213370d4b63355703", (3447, 3458, 3459, 3461, 3463, 3464, 3465, 3467), ()),
}


def repair_september15_json(raw: bytes, name: str, commit: str) -> tuple[bytes, int]:
    """Ten reviewed comma-only edits, restricted to exact upstream file hashes."""
    if commit != SEPT15_COMMIT or name not in SEPT15_REPAIRS:
        return raw, 0
    expected, additions, removals = SEPT15_REPAIRS[name]
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"Reviewed September 15 JSON input hash mismatch: {name}")
    lines = raw.splitlines(keepends=True)
    for number in additions + removals:
        body = lines[number - 1].rstrip(b'\r\n')
        ending = lines[number - 1][len(body):]
        if number in additions:
            assert body.endswith(b'"')
            body += b','
        else:
            assert body.endswith(b',')
            body = body[:-1]
        lines[number - 1] = body + ending
    fixed = b''.join(lines)
    json.loads(fixed.decode('utf-8-sig'))
    return fixed, len(additions) + len(removals)


def prepare(checkout: Path, output: Path, commit: str = COMMIT) -> dict:
    def git(*args):
        return subprocess.check_output(["git", "-C", str(checkout), *args], timeout=30)

    resolved = git("rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip()
    paths = git("ls-tree", "-r", "--name-only", resolved,
                "PvZ_Fusion_Translator/Localization/English/Strings",
                "PvZ_Fusion_Translator/Localization/English/Almanac",
                "PvZ_Fusion_Translator/Dumps").decode().splitlines()
    records = []
    for name in paths:
        if not name.endswith(".json"):
            continue
        raw = git("show", f"{resolved}:{name}")
        source_hash = hashlib.sha256(raw).hexdigest()
        repaired = False
        if name == REPAIR_PATH and resolved == COMMIT:
            if source_hash != REPAIR_SHA256:
                raise ValueError("Reviewed PC JSON repair input hash does not match")
            needle = b'"name": "Jinxed"'
            if raw.count(needle) != 1:
                raise ValueError("Expected exactly one reviewed Jinxed name")
            raw = raw.replace(needle, needle + b",")
            repaired = True
        comma_repairs = 0
        if name.startswith("PvZ_Fusion_Translator/Localization/English/Strings/"):
            raw, comma_repairs = repair_september15_json(raw, Path(name).name, resolved)
        json.loads(raw.decode("utf-8-sig"))  # Strict parser; no general repair.
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        records.append({"file": name, "upstream_sha256": source_hash,
                        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
                        "missing_comma_repaired": repaired,
                        "reviewed_comma_only_edits": comma_repairs})
    report = {"pc_commit": resolved, "files": records}
    output.mkdir(parents=True, exist_ok=True)
    (output / "snapshot-provenance.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--commit", default=COMMIT, help="Reviewed commit to export")
    args = parser.parse_args()
    report = prepare(args.checkout, args.output, args.commit)
    print(json.dumps({"pc_commit": report['pc_commit'], "json_files": len(report["files"]),
                      "syntax_only_repairs": sum(r["missing_comma_repaired"] for r in report["files"])}))
