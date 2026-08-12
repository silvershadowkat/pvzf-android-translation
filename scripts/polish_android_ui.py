#!/usr/bin/env python3
"""Apply Android-specific 3.8.1 UI polish after translation and TMP transplant.

This pass removes PC-only Almanac font-size tags (matching Joseph's Android
data), cleans and romanizes the credits panel, normalizes the zombie Almanac
heading, and replaces remaining mixed Chinese/English serialized UI defaults.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import re
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator


SIZE_TAG_RE = re.compile(r"</?size(?:=[^>]*)?>", re.IGNORECASE)
ALMANAC_ASSETS = {"LawnStrings", "ZombieStrings"}

CREDITS_TEXT = """<align=center><size=16>Credits</size>
<size=12>LanPiaoPiaoFly — Direction, Code & Animation
Gfishtus — Art & Visual Direction
Mengluo — Video Editing
Aya Shameimaru — Animation Support
Landie — Art Support</size></align>"""

TEXT_OVERRIDES = {
    178983: CREDITS_TEXT,
    179732: "Your Weapon",
    179832: "41_5\nSpeed Frenzy",
    179962: "Adventure Trials",
    180066: "Not Completed",
    180103: "42_5\nSpeed Frenzy II",
    180110: "Battle Skill",
    180578: "Health Upgrade",
    181012: "Please Enter",
    181063: "Plant Draw",
    181201: "Reset Trial",
    182450: "Planting Direction",
    182805: "Copy Code",
    182982: "Level 1 Reward: Reward\nReward\nReward",
    182983: "Level 1 Reward: Reward\nReward\nReward",
    183118: "Draws:\n40/90\nFeatured:\nOdys. Gloom-shroom\nReroll in:\n100\n",
    183204: "Clear Skies!",
    184559: "Tip: Right-click a plant to view all its Fusions",
    184641: "Plant Storage Level: 1    Capacity: 44",
    184722: "Next stage: 23m 23s\nMoisture:\nGrowth stage:\nAffection:",
    184723: "Next stage: 23m 23s\nMoisture:\nGrowth stage:\nAffection:",
    185023: "Brute Force!",
    185559: "<size=15>Animation - Off</size>",
    185620: "Basic Prize · Day",
    185625: "Currency War",
    185656: "New World\nNew Time (2026/6/3 14:19)\nSurvival Mode, Cheats, Version: 1.20.1",
    185703: "Upgrade Level: 10/10\nUpgrade Bonus: 500%\nCost: 3 matching cards",
    185708: "Free Rerolls: 2",
    185839: (
        "<size=75%>Shortcuts:\n"
        "1: Shovel    Q: Plant HP\n"
        "2: Glove     W: Zombie HP\n"
        "3: Time Stop E: Coffee Bean\n"
        "4: Hammer    P: Toggle Airship SFX\n"
        "5: Cart      V: Toggle Zombie Glove\n"
        "C: Hover a plant to open Almanac\n"
        "H: Hover a plant to view info</size>"
    ),
    186016: "Current Wave: 30/200",
    186184: "When enabled, clicking a card discards it",
    186413: "P\nL\nA\nY\nE\nR\n\nC\nP\nU",
    186584: "Damage Upgrade",
    186763: "Follow Us",
    186802: "Draw Tickets: 1/0/0/0",
    187035: "Next stage: 23m 23s\nMoisture:\nGrowth stage:\nAffection:",
    187555: "Plant Name",
    187742: "Free Rerolls: 2",
    187948: (
        "Click a card to select the upgrade target.\n\n"
        "More Plant Evolutions increase its in-level Sun cost.\n"
        "<size=80%>Plant Evolution (WIP; currently has no effect)</size>"
    ),
    188111: "Upgrade Level: 10/10\nUpgrade Bonus: 500%\nCost: 3 matching cards",
    188327: "I Give Up!",
    188593: "Change Page",
    189440: "Prize Pool",
    190294: (
        "Base Stats\nElement: Physical\nHealth: 300\nDamage: 20\n"
        "Attack Interval: 1.5s\nCritical Rate: 5%\nCritical Damage: 50%\n"
        "Damage Bonus: 0%\nEmpowerment: N/A"
    ),
    190507: "Draw Tickets: 1/0/0/0",
    190600: "Synergy Type:\n(0/8)",
    190664: "New Adventure Mode",
    190696: "Basic Attack",
    190712: "Manage Lane",
    190720: "Buy\nEXP",
    190816: "Change Page",
    191342: "Upgrade Level: 10/10\nUpgrade Bonus: 500%\nCost: 3 matching cards",
    191345: "P\nL\nA\nY\nE\nR\n\nC\nP\nU",
    191440: "Modifier Effects",
    191475: "Speed Upgrade",
    191574: "Draw 10",
    191862: "Placeholder Text",
    191992: (
        "Base Stats\nElement: Physical\nHealth: 300\nDamage: 20\n"
        "Attack Interval: 1.5s\nCritical Rate: 5%\nCritical Damage: 50%\n"
        "Damage Bonus: 0%\nEmpowerment: N/A"
    ),
    192348: "46_10\nBloodburn",
    192383: "Complete Level 10 to expand Plant Storage",
    192490: "Plant Draw",
    192682: "The plant cards above are the Prize Pool contents",
    194057: "Route 1",
    194085: "Difficulty cannot be changed in-game. Set it beforehand.",
    194173: "Follow Us",
    194181: "Plant Name",
}

HANDLE_REPLACEMENTS = {
    188915: {"蓝飘飘fly": "LanPiaoPiaoFly"},
    189350: {"蓝飘飘fly": "LanPiaoPiaoFly"},
}

ZOMBIE_TITLE_COMPONENTS = {184024, 189896}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def make_generator(unity_version: str, dummy_dll_dir: Path) -> TypeTreeGenerator:
    generator = TypeTreeGenerator(unity_version)
    generator.load_local_dll_folder(str(dummy_dll_dir))
    return generator


def object_map(env):
    return {(obj.assets_file.name, obj.path_id): obj for obj in env.objects}


def strip_size_tags(value):
    if isinstance(value, str):
        return SIZE_TAG_RE.sub("", value)
    if isinstance(value, list):
        return [strip_size_tags(item) for item in value]
    if isinstance(value, dict):
        return {key: strip_size_tags(item) for key, item in value.items()}
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--dummy-dll-dir", required=True, type=Path)
    parser.add_argument("--unity-version", default="2022.3.62f1")
    parser.add_argument("--zombie-title-size", default=36.0, type=float)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    generator = make_generator(args.unity_version, args.dummy_dll_dir)
    env = UnityPy.load(str(args.base_bundle))
    env.typetree_generator = generator
    objects = object_map(env)
    changes = []

    found_assets = set()
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.parse_as_object()
        if data.m_Name not in ALMANAC_ASSETS:
            continue
        found_assets.add(data.m_Name)
        tree = json.loads(data.m_Script.lstrip("\ufeff"))
        before_open = data.m_Script.lower().count("<size=")
        before_close = data.m_Script.lower().count("</size>")
        tree = strip_size_tags(tree)
        data.m_Script = json.dumps(tree, ensure_ascii=False, indent=4)
        obj.save_typetree(data)
        changes.append(
            {
                "kind": "almanac_size_tag_normalization",
                "asset": data.m_Name,
                "path_id": obj.path_id,
                "removed_open_tags": before_open,
                "removed_close_tags": before_close,
            }
        )
    if found_assets != ALMANAC_ASSETS:
        raise RuntimeError(f"missing Almanac assets: {sorted(ALMANAC_ASSETS - found_assets)}")

    for path_id, replacement in TEXT_OVERRIDES.items():
        obj = objects[("resources.assets", path_id)]
        tree = obj.read_typetree(check_read=False)
        previous = tree["m_text"]
        tree["m_text"] = replacement
        obj.save_typetree(tree)
        changes.append(
            {"kind": "ui_text", "path_id": path_id, "before": previous, "after": replacement}
        )

    for path_id, replacements in HANDLE_REPLACEMENTS.items():
        obj = objects[("resources.assets", path_id)]
        tree = obj.read_typetree(check_read=False)
        previous = tree["m_text"]
        updated = previous
        for source, target in replacements.items():
            if source not in updated:
                raise RuntimeError(f"expected handle {source!r} missing from component {path_id}")
            updated = updated.replace(source, target)
        tree["m_text"] = updated
        obj.save_typetree(tree)
        changes.append(
            {"kind": "handle_romanization", "path_id": path_id, "before": previous, "after": updated}
        )

    for path_id in ZOMBIE_TITLE_COMPONENTS:
        obj = objects[("resources.assets", path_id)]
        tree = obj.read_typetree(check_read=False)
        previous = tree["m_fontSize"]
        tree["m_fontSize"] = args.zombie_title_size
        tree["m_fontSizeBase"] = args.zombie_title_size
        obj.save_typetree(tree)
        changes.append(
            {
                "kind": "zombie_title_size",
                "path_id": path_id,
                "before": previous,
                "after": args.zombie_title_size,
            }
        )

    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    del output_bytes, env
    gc.collect()

    check_generator = make_generator(args.unity_version, args.dummy_dll_dir)
    check_env = UnityPy.load(str(args.output))
    check_env.typetree_generator = check_generator
    check_objects = object_map(check_env)
    for path_id, replacement in TEXT_OVERRIDES.items():
        tree = check_objects[("resources.assets", path_id)].read_typetree(check_read=False)
        if tree["m_text"] != replacement:
            raise RuntimeError(f"UI text validation failed for component {path_id}")
    for path_id in HANDLE_REPLACEMENTS:
        tree = check_objects[("resources.assets", path_id)].read_typetree(check_read=False)
        if any(source in tree["m_text"] for source in HANDLE_REPLACEMENTS[path_id]):
            raise RuntimeError(f"handle validation failed for component {path_id}")
    for path_id in ZOMBIE_TITLE_COMPONENTS:
        tree = check_objects[("resources.assets", path_id)].read_typetree(check_read=False)
        if tree["m_fontSize"] != args.zombie_title_size:
            raise RuntimeError(f"zombie title validation failed for component {path_id}")
    validated_assets = set()
    for obj in check_env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.parse_as_object()
        if data.m_Name not in ALMANAC_ASSETS:
            continue
        json.loads(data.m_Script)
        if SIZE_TAG_RE.search(data.m_Script):
            raise RuntimeError(f"size tags remain in {data.m_Name}")
        validated_assets.add(data.m_Name)
    if validated_assets != ALMANAC_ASSETS:
        raise RuntimeError("Almanac validation did not visit every requested asset")
    del check_env
    gc.collect()

    report = {
        "format_version": 1,
        "base": {"path": str(args.base_bundle.resolve()), "sha256": sha256_file(args.base_bundle)},
        "output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
        },
        "change_count": len(changes),
        "changes": changes,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": report["output"],
                "change_count": report["change_count"],
                "almanac_assets": sorted(validated_assets),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
