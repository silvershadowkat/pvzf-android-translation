#!/usr/bin/env python3
"""Apply Android-specific 3.8.1 UI polish after translation and TMP transplant.

This pass removes PC-only Almanac font-size tags (matching Joseph's Android
data), cleans the credits while preserving original creator names, normalizes the zombie Almanac
heading, translates visible configuration-backed labels, and replaces
remaining mixed Chinese/English serialized UI defaults.
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

TEXT_ASSET_REPLACEMENTS = {
    "PlantEvolutionData": {
        "机枪路线": "Gatling Route",
        "樱桃路线": "Cherry Route",
        "寒冰路线": "Ice Route",
        "毁灭路线": "Doom Route",
        "黑高路线": "Tall-nut Route",
        "灾果路线": "Jalapeño-nut Route",
        "大喷路线": "Fume Route",
        "忧郁路线": "Gloom Route",
        "大帝路线": "Emperor Route",
        "剑仙路线": "Swordmaster Route",
        "战神路线": "War God Route",
        "毁胆路线": "Doom Scaredy Route",
        "魅胆路线": "Hypno Scaredy Route",
        "魅后路线": "Hypno Queen Route",
        "冰炮路线": "Ice Cannon Route",
        "火炮路线": "Fire Cannon Route",
        "火神路线": "Fire God Route",
        "究投路线": "Ultimate Melon Route",
        "瓜炮路线": "Melon Cannon Route",
        "菜炮路线": "Cabbage Cannon Route",
        "大哥路线": "Big Brother Route",
        "浴火路线": "Phoenix Route",
        "绿伞路线": "Emerald Umbrella Route",
        "玄钢路线": "Darksteel Route",
        "刺果路线": "Spikefruit Route",
        "爆竹路线": "Firecracker Route",
        "黑曜路线": "Obsidian Route",
    },
    "TalentData": {"至极手速": "Quick Hands I"},
}

CREDITS_TEXT = """<align=center><size=16>Credits</size>
<size=12>蓝飘飘fly — Direction, Code & Animation
机鱼吐司 — Art & Visual Direction
梦珞 — Video Editing
射命丸文 — Animation Support
蓝蝶 — Art Support</size></align>"""

TEXT_OVERRIDES = {
    178983: CREDITS_TEXT,
    # The longer PC label collides with the two skin-navigation arrows on
    # Android. These are the three duplicated Almanac plant-detail variants.
    179605: "<size=80%><color=black>Skin</color></size>",
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
    182740: "<size=80%><color=black>Skin</color></size>",
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
    # Staging text only. The subsequent bake_help_credits.py pass renders the
    # complete credit into the parchment texture and blanks this live layer.
    179902: "aha · SilverShadow · Codex",
    # The Help parchment already contains a complete baked Hotkeys column.
    # These two live overlays otherwise duplicate and obscure that artwork.
    185005: "   ",
    185839: "   ",
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
    193174: "<size=80%><color=black>Skin</color></size>",
    194057: "Route 1",
    194085: "Difficulty cannot be changed in-game. Set it beforehand.",
    194173: "Follow Us",
    194181: "Plant Name",
}

HANDLE_REPLACEMENTS = {
    188915: {
        "The Official source of PvZ Fusion is only on the dev, LanPiaoPiaoFly's Bilibili": (
            "The official source of PvZ Fusion is 蓝飘飘fly's Bilibili"
        ),
        "The Official source of PvZ Fusion is only on the dev, 蓝飘飘fly's Bilibili": (
            "The official source of PvZ Fusion is 蓝飘飘fly's Bilibili"
        ),
        "LanPiaoPiaoFly": "蓝飘飘fly",
    },
    189350: {"LanPiaoPiaoFly": "蓝飘飘fly"},
}

ZOMBIE_TITLE_COMPONENTS = {184024, 189896}
ALMANAC_TIP_COMPONENT = 184559
ALMANAC_TIP_RECT_TRANSFORM = 176824
PORT_CREDITS_COMPONENT = 179902
PORT_CREDITS_RECT_TRANSFORM = 176070
PORT_CREDITS_FONT_ASSET = 178477  # 汉仪夏日体W SDF (parchment handwriting)
PORT_CREDITS_MATERIAL = 2


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


def replace_nested_strings(value, replacements: dict[str, str]):
    if isinstance(value, str):
        updated = value
        for source, target in replacements.items():
            updated = updated.replace(source, target)
        return updated
    if isinstance(value, list):
        return [replace_nested_strings(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: replace_nested_strings(item, replacements) for key, item in value.items()}
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

    translated_config_assets = set()
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.parse_as_object()
        replacements = TEXT_ASSET_REPLACEMENTS.get(data.m_Name)
        if replacements is None:
            continue
        tree = json.loads(data.m_Script.lstrip("\ufeff"))
        serialized_before = json.dumps(tree, ensure_ascii=False)
        tree = replace_nested_strings(tree, replacements)
        serialized_after = json.dumps(tree, ensure_ascii=False)
        unresolved = [source for source in replacements if source in serialized_after]
        if unresolved:
            raise RuntimeError(f"visible translations remain in {data.m_Name}: {unresolved}")
        if serialized_before == serialized_after and not all(
            target in serialized_after for target in replacements.values()
        ):
            raise RuntimeError(f"expected visible labels missing from {data.m_Name}")
        data.m_Script = json.dumps(tree, ensure_ascii=False, indent=4)
        obj.save_typetree(data)
        translated_config_assets.add(data.m_Name)
        changes.append(
            {
                "kind": "visible_text_asset_translation",
                "asset": data.m_Name,
                "path_id": obj.path_id,
                "replacement_count": len(replacements),
            }
        )
    if translated_config_assets != set(TEXT_ASSET_REPLACEMENTS):
        raise RuntimeError(
            "missing visible TextAssets: "
            f"{sorted(set(TEXT_ASSET_REPLACEMENTS) - translated_config_assets)}"
        )

    for path_id, replacement in TEXT_OVERRIDES.items():
        obj = objects[("resources.assets", path_id)]
        tree = obj.read_typetree(check_read=False)
        previous = tree["m_text"]
        tree["m_text"] = replacement
        obj.save_typetree(tree)
        changes.append(
            {"kind": "ui_text", "path_id": path_id, "before": previous, "after": replacement}
        )

    port_credit_obj = objects[("resources.assets", PORT_CREDITS_COMPONENT)]
    port_credit_tree = port_credit_obj.read_typetree(check_read=False)
    credit_typography_before = {
        "font_size": port_credit_tree["m_fontSize"],
        "auto_size": port_credit_tree["m_enableAutoSizing"],
        "word_wrap": port_credit_tree["m_enableWordWrapping"],
        "font_asset": dict(port_credit_tree["m_fontAsset"]),
        "shared_material": dict(port_credit_tree["m_sharedMaterial"]),
    }
    # Reassert the text because this fresh typetree read may predate the
    # generic override saved above in UnityPy's object cache.
    port_credit_tree["m_text"] = TEXT_OVERRIDES[PORT_CREDITS_COMPONENT]
    port_credit_tree["m_fontAsset"] = {"m_FileID": 0, "m_PathID": PORT_CREDITS_FONT_ASSET}
    port_credit_tree["m_sharedMaterial"] = {"m_FileID": 0, "m_PathID": PORT_CREDITS_MATERIAL}
    port_credit_tree["m_hasFontAssetChanged"] = 1
    port_credit_tree["m_fontSize"] = 20.0
    port_credit_tree["m_fontSizeBase"] = 20.0
    port_credit_tree["m_enableAutoSizing"] = 1
    port_credit_tree["m_fontSizeMin"] = 16.0
    port_credit_tree["m_fontSizeMax"] = 20.0
    port_credit_tree["m_enableWordWrapping"] = 0
    port_credit_obj.save_typetree(port_credit_tree)

    port_credit_rect_obj = objects[("resources.assets", PORT_CREDITS_RECT_TRANSFORM)]
    port_credit_rect_tree = port_credit_rect_obj.read_typetree()
    if port_credit_rect_tree["m_GameObject"]["m_PathID"] != port_credit_tree["m_GameObject"]["m_PathID"]:
        raise RuntimeError("port-credit RectTransform no longer belongs to the expected GameObject")
    credit_rect_before = {
        "anchored_position": dict(port_credit_rect_tree["m_AnchoredPosition"]),
        "size": dict(port_credit_rect_tree["m_SizeDelta"]),
    }
    port_credit_rect_tree["m_AnchoredPosition"]["x"] = -3.39
    port_credit_rect_tree["m_AnchoredPosition"]["y"] = -2.35
    port_credit_rect_tree["m_SizeDelta"]["x"] = 30.0
    port_credit_rect_tree["m_SizeDelta"]["y"] = 1.0
    port_credit_rect_obj.save_typetree(port_credit_rect_tree)
    changes.append(
        {
            "kind": "english_android_port_credits",
            "component_path_id": PORT_CREDITS_COMPONENT,
            "rect_transform_path_id": PORT_CREDITS_RECT_TRANSFORM,
            "before": {**credit_typography_before, **credit_rect_before},
            "after": {
                "text": TEXT_OVERRIDES[PORT_CREDITS_COMPONENT],
                "font_size": 20.0,
                "auto_size": 1,
                "word_wrap": 0,
                "font_asset": PORT_CREDITS_FONT_ASSET,
                "shared_material": PORT_CREDITS_MATERIAL,
                "anchored_position": {"x": -3.39, "y": -2.35},
                "size": {"x": 30.0, "y": 1.0},
            },
        }
    )

    for path_id, replacements in HANDLE_REPLACEMENTS.items():
        obj = objects[("resources.assets", path_id)]
        tree = obj.read_typetree(check_read=False)
        previous = tree["m_text"]
        updated = previous
        for source, target in replacements.items():
            updated = updated.replace(source, target)
        if "蓝飘飘fly" not in updated:
            raise RuntimeError(f"original creator name missing from component {path_id}")
        tree["m_text"] = updated
        obj.save_typetree(tree)
        changes.append(
            {"kind": "original_creator_name_restore", "path_id": path_id, "before": previous, "after": updated}
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

    tip_obj = objects[("resources.assets", ALMANAC_TIP_COMPONENT)]
    tip_tree = tip_obj.read_typetree(check_read=False)
    tip_before = {
        "font_size": tip_tree["m_fontSize"],
        "auto_size": tip_tree["m_enableAutoSizing"],
        "word_wrap": tip_tree["m_enableWordWrapping"],
    }
    # Reassert the translated text because this fresh typetree read can predate
    # the generic TEXT_OVERRIDES save in UnityPy's object cache.
    tip_tree["m_text"] = TEXT_OVERRIDES[ALMANAC_TIP_COMPONENT]
    tip_tree["m_fontSize"] = 24.0
    tip_tree["m_fontSizeBase"] = 24.0
    tip_tree["m_enableAutoSizing"] = 1
    tip_tree["m_fontSizeMin"] = 12.0
    tip_tree["m_fontSizeMax"] = 24.0
    tip_tree["m_enableWordWrapping"] = 0
    tip_obj.save_typetree(tip_tree)

    tip_rect_obj = objects[("resources.assets", ALMANAC_TIP_RECT_TRANSFORM)]
    tip_rect_tree = tip_rect_obj.read_typetree()
    if tip_rect_tree["m_GameObject"]["m_PathID"] != tip_tree["m_GameObject"]["m_PathID"]:
        raise RuntimeError("Almanac tip RectTransform no longer belongs to the expected GameObject")
    rect_before = {
        "anchored_x": tip_rect_tree["m_AnchoredPosition"]["x"],
        "width": tip_rect_tree["m_SizeDelta"]["x"],
    }
    # Keep the original left edge while ending before the centered Search box.
    tip_rect_tree["m_AnchoredPosition"]["x"] = -472.0
    tip_rect_tree["m_SizeDelta"]["x"] = 880.0
    tip_rect_obj.save_typetree(tip_rect_tree)
    changes.append(
        {
            "kind": "almanac_tip_layout",
            "path_id": ALMANAC_TIP_COMPONENT,
            "rect_transform_path_id": ALMANAC_TIP_RECT_TRANSFORM,
            "before": {**tip_before, **rect_before},
            "after": {
                "font_size": 24.0,
                "auto_size": 1,
                "word_wrap": 0,
                "anchored_x": -472.0,
                "width": 880.0,
            },
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
    port_credit_tree = check_objects[("resources.assets", PORT_CREDITS_COMPONENT)].read_typetree(
        check_read=False
    )
    port_credit_rect_tree = check_objects[
        ("resources.assets", PORT_CREDITS_RECT_TRANSFORM)
    ].read_typetree()
    if (
        port_credit_tree["m_fontSize"] != 20.0
        or port_credit_tree["m_enableAutoSizing"] != 1
        or port_credit_tree["m_enableWordWrapping"] != 0
        or port_credit_tree["m_fontAsset"]["m_PathID"] != PORT_CREDITS_FONT_ASSET
        or port_credit_tree["m_sharedMaterial"]["m_PathID"] != PORT_CREDITS_MATERIAL
        or abs(port_credit_rect_tree["m_AnchoredPosition"]["x"] - -3.39) > 0.001
        or abs(port_credit_rect_tree["m_AnchoredPosition"]["y"] - -2.35) > 0.001
        or abs(port_credit_rect_tree["m_SizeDelta"]["x"] - 30.0) > 0.001
    ):
        raise RuntimeError("port-credit layout validation failed")
    for path_id in HANDLE_REPLACEMENTS:
        tree = check_objects[("resources.assets", path_id)].read_typetree(check_read=False)
        if any(source in tree["m_text"] for source in HANDLE_REPLACEMENTS[path_id]):
            raise RuntimeError(f"handle validation failed for component {path_id}")
    for path_id in ZOMBIE_TITLE_COMPONENTS:
        tree = check_objects[("resources.assets", path_id)].read_typetree(check_read=False)
        if tree["m_fontSize"] != args.zombie_title_size:
            raise RuntimeError(f"zombie title validation failed for component {path_id}")
    tip_tree = check_objects[("resources.assets", ALMANAC_TIP_COMPONENT)].read_typetree(check_read=False)
    if (
        tip_tree["m_fontSize"] != 24.0
        or tip_tree["m_enableAutoSizing"] != 1
        or tip_tree["m_enableWordWrapping"] != 0
    ):
        raise RuntimeError("Almanac tip typography validation failed")
    tip_rect_tree = check_objects[("resources.assets", ALMANAC_TIP_RECT_TRANSFORM)].read_typetree()
    if (
        tip_rect_tree["m_AnchoredPosition"]["x"] != -472.0
        or tip_rect_tree["m_SizeDelta"]["x"] != 880.0
    ):
        raise RuntimeError("Almanac tip rectangle validation failed")
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
    validated_config_assets = set()
    for obj in check_env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.parse_as_object()
        replacements = TEXT_ASSET_REPLACEMENTS.get(data.m_Name)
        if replacements is None:
            continue
        payload = data.m_Script
        if any(source in payload for source in replacements):
            raise RuntimeError(f"visible CJK labels remain in {data.m_Name}")
        if not all(target in payload for target in replacements.values()):
            raise RuntimeError(f"translated labels missing from {data.m_Name}")
        validated_config_assets.add(data.m_Name)
    if validated_config_assets != set(TEXT_ASSET_REPLACEMENTS):
        raise RuntimeError("visible TextAsset validation did not visit every requested asset")
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
