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
        json.loads(raw.decode("utf-8-sig"))  # Strict parser; no general repair.
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        records.append({"file": name, "upstream_sha256": source_hash,
                        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
                        "missing_comma_repaired": repaired})
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
