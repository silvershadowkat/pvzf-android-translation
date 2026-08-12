#!/usr/bin/env python3
"""Report Android fallback provenance against the current PC translation data."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from build_metadata_translation import (
    ANDROID_CONFIRMED_EXACT,
    ANDROID_REQUIRED_OVERRIDE_SOURCES,
    EXACT_FILES,
    read_json,
)


def load_pc_exact(strings_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    exact: dict[str, str] = {}
    sources: dict[str, str] = {}
    for filename in EXACT_FILES:
        path = strings_dir / filename
        if not path.exists():
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a JSON object")
        for source, target in payload.items():
            if isinstance(source, str) and isinstance(target, str):
                exact[source] = target
                sources[source] = filename
    return exact, sources


def translation_source_snapshot(strings_dir: Path) -> dict[str, object]:
    """Record the exact upstream checkout used by this report."""
    repository = next(
        (
            candidate
            for candidate in (strings_dir.resolve(), *strings_dir.resolve().parents)
            if (candidate / ".git").exists()
        ),
        None,
    )
    if repository is None:
        return {"repository": None, "commit": None, "origin": None, "dirty": None}

    def git(*arguments: str) -> str:
        return subprocess.check_output(
            ["git", "-c", f"safe.directory={repository}", "-C", str(repository), *arguments],
            text=True,
            encoding="utf-8",
        ).strip()

    return {
        "repository": str(repository),
        "commit": git("rev-parse", "HEAD"),
        "origin": git("remote", "get-url", "origin"),
        "dirty": bool(git("status", "--porcelain")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strings-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    pc_exact, pc_sources = load_pc_exact(args.strings_dir)
    entries = []
    counts: dict[str, int] = {}
    for source, android_target in ANDROID_CONFIRMED_EXACT.items():
        pc_target = pc_exact.get(source)
        if source in ANDROID_REQUIRED_OVERRIDE_SOURCES:
            status = "android_required_override"
        elif pc_target is None:
            status = "codex_android_fallback_active"
        elif pc_target == android_target:
            status = "pc_community_match_preferred"
        else:
            status = "pc_community_replacement_preferred"
        counts[status] = counts.get(status, 0) + 1
        entries.append(
            {
                "source": source,
                "android_target": android_target,
                "priority": "android_required" if source in ANDROID_REQUIRED_OVERRIDE_SOURCES else "fallback",
                "status": status,
                "pc_target": pc_target,
                "pc_source_file": pc_sources.get(source),
                "provenance": (
                    "Android-specific screenshot/runtime confirmation"
                    if source in ANDROID_REQUIRED_OVERRIDE_SOURCES
                    else "Codex-assisted Android fallback; PC community wins when available"
                ),
            }
        )

    report = {
        "format_version": 1,
        "translation_source": translation_source_snapshot(args.strings_dir),
        "policy": {
            "first": "current PC community exact translations",
            "second": "Android-required semantic/layout overrides",
            "third": "Codex-assisted screenshot-confirmed Android fallbacks",
            "note": "Fallbacks are never allowed to replace a newly available PC exact translation.",
        },
        "counts": dict(sorted(counts.items())),
        "entries": entries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), "counts": report["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
