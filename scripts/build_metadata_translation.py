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

# Confirmed against the Android 3.8.1 UI. These are runtime format strings and
# fragments which the PC translator does not see in their final rendered form.
# Keep this list exact and screenshot-backed: broad CJK replacement can mutate
# internal identifiers or developer-only diagnostics.
ANDROID_CONFIRMED_EXACT = {
    # Zen Garden shop.
    "\n已持有{0}个": "\nOwned: {0}",
    "{0}\n价格：{1}": "{0}\nCost: {1}",

    # PC-authoritative numbered and color-coded six-level difficulty scale.
    "简单模式": "<size=20><color=#00C853>0: Easy Mode",
    "普通模式": "<size=20><color=#64DD17>1: Casual Mode",
    "正常模式": "<size=20><color=#AEEA00>2: Normal Mode",
    "困难模式": "<size=20><color=#FFD600>3: Veteran Mode",
    "极难模式": "<size=20><color=#FF6D00>4: Merciless Mode",
    "你确定？": "<size=20><color=#D50000>5: Are You Sure?",

    # The Gods: Evolution.
    "\n\n定位：": "\n\nRole: ",
    "升级到": " upgrades to ",
    "{0}\n已选了{1}次": "{0}\nTimes selected: {1}",
    "{0}获得{1:F0}%独立伤害增幅\n当前增幅：{2:F0}%": (
        "{0} gains {1:F0}% independent damage\nCurrent bonus: {2:F0}%"
    ),
    "{0}获得{1:F0}%速度增幅\n当前增幅：{2:F0}%": (
        "{0} gains {1:F0}% speed\nCurrent bonus: {2:F0}%"
    ),
    "的发射数量+1": "'s projectile count +1",
    "最多{0}株植物": "At most {0} plants",
    "翻页({0}/{1})": "Page ({0}/{1})",
    "经典的诸神进化\n\n": "Classic The Gods: Evolution\n\n",
    "最终面临大帅的挑战\n\n": "Final challenge: the Archduke\n\n",
    "1次轮回，最终面临僵王的挑战\n\n": "1 reincarnation; final boss: Dr. Zomboss\n\n",
    "2次轮回，最终面临黄金僵王的挑战\n\n": (
        "2 reincarnations; final boss: Golden Dr. Zomboss\n\n"
    ),
    "解锁条件：\n累计通关达20次": "Unlock condition:\nComplete 20 total runs",
    "该难度下还没有通关过": "Not yet completed at this difficulty",
    "该难度已经通关了{0}次": "Completions at this difficulty: {0}",
    "额外5次刷新机会，正常僵尸数量\n\n": "5 extra rerolls; normal zombie count\n\n",
    "额外4次刷新机会，僵尸血量x2\n\n": "4 extra rerolls; zombie HP x2\n\n",
    "额外3次刷新机会，僵尸血量x3\n\n": "3 extra rerolls; zombie HP x3\n\n",
    "额外2次刷新机会，僵尸血量x4，速度x1.5\n\n": (
        "2 extra rerolls; zombie HP x4; speed x1.5\n\n"
    ),
    "诸神：进化，推荐难度0~3，第{0}轮": "The Gods: Evolved, Recommended Diff: 0-3, Round {0}",

    # Odyssey, saves, and Almanac.
    "当前幸运值：{0}\n幸运可以增加从箱子里获取植物的数量和从抽奖中获得的阳光数量": (
        "Current Luck: {0}\nLuck increases plants from boxes and Sun from prize draws"
    ),
    "{0}，编号：{1}\n保存时间：{2}\n版本：{3}": "{0}, Slot: {1}\nSaved at: {2}\nVersion: {3}",
    "，最近一次自动保存\n保存时间：": ", Latest Autosave\nSaved at: ",
    "禁用转场动画": "Disable Transitions",

    # Starbound Task Rewards.
    "奖励1：<color=black>": "Reward 1: <color=grey>",
    "奖励1：<color=white>": "Reward 1: <color=white>",
    "奖励2：<color=black>": "Reward 2: <color=grey>",
    "奖励2：<color=white>": "Reward 2: <color=white>",
    "星辉白天：第1关": "Starbound Adventure: Day | Level 1",
    "星辉白天：第2关": "Starbound Adventure: Day | Level 2",
    "星辉白天：第3关": "Starbound Adventure: Day | Level 3",
    "星辉白天：第4关": "Starbound Adventure: Day | Level 4",
    "星辉白天：第5关": "Starbound Adventure: Day | Level 5",
    "星辉白天：第6关": "Starbound Adventure: Day | Level 6",
    "每局开始赠送一个基础植物": "Start each level with a basic plant already planted (except Roof)\n",
    "每局开始的第一次融合，都会奖励50阳光": "The first fusion of each level returns 50 Sun\n",
    "每局开始给予75点初始阳光": "Start each level with 75 bonus Sun\n",
    "每局开始额外赠送一个向日葵": "Start each level with a Sunflower already planted (except Roof)\n",
    "阳光炸弹的阳光产量永久x3": "Triple Solar Bomb's Sun production permanently\n",
    "樱桃子弹击中僵尸时有概率释放小樱桃爆炸": "Cherry projectiles may cause small Cherry explosions on hit\n",

    # Android 3.8.1 Note Editor runtime fragments. The PC regexes only see
    # fully rendered values, while Android stores these format pieces.
    "歌曲: ": "Song: ",
    "时间: {0:F2}s": "Time: {0:F2}s",
    " | 时间: {0:F3}s ({1}.{2}拍)": " | Time: {0:F3}s (Beat {1}.{2})",

    # Vasebreaker PVP turn-assist messages. The PC regex expects concrete
    # player/move values, but Android formats these placeholders at runtime.
    "{0}的回合开始了，你有{1}次行动机会\n可在指定位置放置礼盒": (
        "{0}'s turn begins. You have {1} move(s).\n"
        "Place a Gift Box in the designated area."
    ),
    "{0}还有{1}次行动机会\n可在指定位置放置礼盒": (
        "{0} has {1} move(s) left.\n"
        "Place a Gift Box in the designated area."
    ),

    # Additional Vasebreaker PVP fragments are concatenated around the live
    # player name, while the toggle suffixes are appended to two button labels.
    # Keep the leading/trailing spaces: they preserve natural spacing after the
    # game assembles the final runtime text.
    "\uff08\u5173\uff09": " (OFF)",
    "\uff08\u5f00\uff09": " (ON)",
    "\u6709\u50f5\u5c38\u8fc7\u7ebf\u4e86\uff0c": "A zombie crossed the line. ",
    "\u83b7\u5f971\u6b21\u884c\u52a8\u6b21\u6570": " gains 1 move.",
    "\u6ca1\u6709\u884c\u52a8\u6b21\u6570\u4e86\uff0c\u8bf7\u9009\u62e9\u7ee7\u7eed\u7838\u7f50\u5b50\u6216\u8005\u6309\u4e0b\u56de\u8f66\u952e\u7ed3\u675f\u56de\u5408": (
        "No moves remain. Continue breaking vases, or press Enter to end the turn."
    ),
    "\uff0c\u4f60\u5df2\u7ecf\u6ca1\u6709\u884c\u52a8\u6b21\u6570\u4e86": ", you have no moves left.",

    # Zen Garden purchase confirmation assembled after the destination slot
    # is chosen. Keep the three indices intact and in their original order.
    "购买成功，植物已放在第{0}页的第{1}行{2}列格子中": (
        "Purchase successful. Plant placed on page {0}, row {1}, column {2}."
    ),
}

# Android-only 3.8.1 short labels and undiscovered-plant recipes. The PC
# regex fallback mistakes the short stat labels for recipe hints and can leave
# the second ingredient in Chinese. These exact entries remain fallbacks so a
# future community English exact match wins automatically.
ANDROID_CONFIRMED_EXACT.update({
    "低血量伤害+20%/40%/70%": "Low-HP Damage + 20%/40%/70%",
    "全体伤害+10%/20%/35%": "Global Damage + 10%/20%/35%",
    "全体护盾+50/100/200": "Global Shield + 50/100/200",
    "冷却缩减+10%/20%/30%": "Cooldown Reduction + 10%/20%/30%",
    "击杀敌人金币+1/2/3": "Coins per Kill + 1/2/3",
    "前台植物攻击力+10%/20%/35%": "Active Plant Attack + 10%/20%/35%",
    "吞噬伤害+10%/20%/35%": "Devour Damage + 10%/20%/35%",
    "大招充能速度+10%/20%/35%": "Ultimate Charge Speed + 10%/20%/35%",
    "大招持续时间+5秒": "Ultimate Duration + 5s",
    "子弹弹射数量+1\n": "Projectile Bounces + 1",
    "技能伤害+15%/30%/50%": "Skill Damage + 15%/30%/50%",
    "护甲+15/30/50": "Armor + 15/30/50",
    "攻击速度+10%/20%/35%": "Attack Speed + 10%/20%/35%",
    "攻击速度+15%/30%/50%": "Attack Speed + 15%/30%/50%",
    "暴击伤害+10%/20%/35%": "Critical Damage + 10%/20%/35%",
    "暴击率/暴击伤害+10%/20%/30%": "Critical Rate/Damage + 10%/20%/30%",
    "最大散射数+10": "Maximum Spread + 10",
    "治疗效果+10%/20%/35%": "Healing Effect + 10%/20%/35%",
    "火海时间+3秒": "Fire Field Duration + 3s",
    "移动速度+10%/20%/35%": "Movement Speed + 10%/20%/35%",
    "能量获取+10%/20%/35%": "Energy Gain + 10%/20%/35%",
    "范围伤害+10%/20%/35%": "Area Damage + 10%/20%/35%",
    "追击子弹伤害+20%/40%/70%": "Pursuit Projectile Damage + 20%/40%/70%",
    "追击子弹数量+1/2/3": "Pursuit Projectile Count + 1/2/3",
    "释放的毁灭菇伤害+100%": "Released Doom-shroom Damage + 100%",
    "攻击僵尸时有几率施加一层“解读”标记。若弹射击中已标记的僵尸，则会消耗此标记，使本次弹射次数+1。多选提高概率": (
        "Attacks may apply one Interpretation mark. A ricochet that hits a marked "
        "zombie consumes the mark and gains +1 bounce. Multiple selections increase "
        "the chance."
    ),
    "寒冰加农炮+寒冰毁灭菇": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "Cryo Cannon + Demise-shroom"
    ),
    "火爆窝瓜+超级火炬": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "Spicy Squash + Infernowood"
    ),
    "超级伞+菜伞": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "Alchemist Umbrella + Umbrella Kale"
    ),
    "超级南瓜+磁力三叶草": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "Pumpkarrier + Magnet Blover"
    ),
    "超级大喷菇+寒冰忧郁菇": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "Doomspike-shroom + Frost Gloom-shroom"
    ),
    "超级大喷菇+寒冰魅惑菇": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "Doomspike-shroom + Cryonic-shroom"
    ),
    "超级大嘴花+樱桃大嘴花": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "Chompzilla + Cherry Chomper"
    ),
    "超级投手+蒜瓜": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "Salad-pult + Garlic-pult"
    ),
    "超级杨桃+磁力仙人掌": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "Stardrop + Magnet Cactus"
    ),
    "超级樱桃射手+樱桃机枪射手": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "Explode-o-shooter + Gatling Cherry"
    ),
    "超级魅惑菇+磁力魅惑菇": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "Charm-shroom + Charm Magnet"
    ),
    "魅惑菇+魅惑菇": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "Hypno-shroom + Hypno-shroom"
    ),
})

# Android 3.8.1's plant Almanac renders affinity names by calling ToString()
# on this enum. Enum member names live in metadata's definition string heap,
# not in the ordinary IL2CPP literal database, so the usual translation pass
# cannot reach them. These 18 contiguous field indices are validated against
# the clean 3.8.1 metadata before being renamed. Changing an enum member name
# does not change its numeric value, plant membership, or gameplay logic.
ANDROID_381_SYNERGY_ENUM_FIELDS = {
    7343: ("前院守卫", "Forest Protectors"),
    7344: ("蘑菇岛", "Fungal Colony"),
    7345: ("后院守卫", "River Raiders"),
    7346: ("战术小队", "Tactician Squad"),
    7347: ("屋顶守卫", "Hilltop Defenders"),
    7348: ("冰雪之地", "Cold Core"),
    7349: ("寰宇", "Galaxy Guardians"),
    7350: ("爽快射击", "Trigger Happy"),
    7351: ("爆破王", "Demolitionists"),
    7352: ("磁力科技", "Magnetrons"),
    7353: ("阳光财团", "Solar Consortium"),
    7354: ("泰坦之躯", "Bulwarks"),
    7355: ("百步穿杨", "Precision Piercers"),
    7356: ("前线壁垒", "Razorwires"),
    7357: ("极致之冰", "Cryonicists"),
    7358: ("持续伤害", "Lingering Attackers"),
    7359: ("烈焰战士", "Fireworkers"),
    7360: ("召唤师", "Necromancers"),
}

# Only platform-specific semantic/layout fixes override PC data. All other
# Codex/screenshot-confirmed mappings are fallbacks and automatically yield to
# a current PC community exact translation when one appears.
ANDROID_REQUIRED_OVERRIDE_SOURCES = {
    "简单模式", "普通模式", "正常模式", "困难模式", "极难模式", "你确定？",
    "禁用转场动画",
    "奖励1：<color=black>", "奖励1：<color=white>",
    "奖励2：<color=black>", "奖励2：<color=white>",
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


@dataclass(frozen=True)
class DefinitionLayout:
    string_offset: int
    string_size: int
    field_offset: int
    field_size: int


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


def parse_definition_layout(data: bytes) -> DefinitionLayout:
    magic, version = struct.unpack_from("<2I", data, 0)
    if magic != 0xFAB11BAF or version != 31:
        raise ValueError(
            f"unsupported IL2CPP metadata header for definition patch: "
            f"magic=0x{magic:08x}, version={version}"
        )
    # Metadata v31 header pairs used here:
    #   [6,7]   definition string heap offset/size
    #   [24,25] field definition table offset/size
    string_offset, string_size = struct.unpack_from("<2I", data, 24)
    field_offset, field_size = struct.unpack_from("<2I", data, 96)
    if string_offset + string_size > len(data):
        raise ValueError("definition string heap points outside the metadata file")
    if field_offset + field_size > len(data) or field_size % 12:
        raise ValueError("field definition table is invalid")
    return DefinitionLayout(string_offset, string_size, field_offset, field_size)


def read_definition_string(data: bytes, layout: DefinitionLayout, relative_offset: int) -> str:
    if not 0 <= relative_offset < layout.string_size:
        raise ValueError(f"definition string offset is out of range: {relative_offset}")
    start = layout.string_offset + relative_offset
    end = data.find(b"\0", start, layout.string_offset + layout.string_size)
    if end < 0:
        raise ValueError(f"unterminated definition string at offset {relative_offset}")
    return data[start:end].decode("utf-8")


def translate_synergy_enum_fields(base: bytes) -> tuple[bytes, list[dict[str, object]]]:
    """Rename only the validated 3.8.1 affinity enum fields used by Almanac ToString()."""
    layout = parse_definition_layout(base)
    field_count = layout.field_size // 12
    output = bytearray(base)
    new_heap = bytearray(base[layout.string_offset : layout.string_offset + layout.string_size])
    changes: list[dict[str, object]] = []

    for field_index, (expected_source, translated) in ANDROID_381_SYNERGY_ENUM_FIELDS.items():
        if field_index >= field_count:
            raise RuntimeError(
                f"affinity enum field {field_index} is outside the {field_count}-field table"
            )
        record_offset = layout.field_offset + field_index * 12
        original_name_offset = struct.unpack_from("<I", base, record_offset)[0]
        original_name = read_definition_string(base, layout, original_name_offset)
        if original_name != expected_source:
            raise RuntimeError(
                f"affinity enum validation failed at field {field_index}: "
                f"expected {expected_source!r}, found {original_name!r}"
            )
        translated_offset = len(new_heap)
        new_heap.extend(translated.encode("utf-8") + b"\0")
        struct.pack_into("<I", output, record_offset, translated_offset)
        changes.append(
            {
                "field_index": field_index,
                "source": original_name,
                "translation": translated,
                "expected_numeric_value": field_index - min(ANDROID_381_SYNERGY_ENUM_FIELDS) + 1,
            }
        )

    new_heap_offset = len(output)
    output.extend(new_heap)
    struct.pack_into("<2I", output, 24, new_heap_offset, len(new_heap))

    translated_layout = parse_definition_layout(output)
    for change in changes:
        record_offset = translated_layout.field_offset + int(change["field_index"]) * 12
        translated_offset = struct.unpack_from("<I", output, record_offset)[0]
        actual = read_definition_string(output, translated_layout, translated_offset)
        if actual != change["translation"]:
            raise RuntimeError(
                f"affinity enum round-trip validation failed at field {change['field_index']}"
            )
    return bytes(output), changes


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
        if filename == "travel_buffs.json":
            # Android stores each modifier as one combined string and derives
            # its short card/title label from the text before the full-width
            # colon. Keep that first line solely as title metadata; the Unity
            # layout pass clips it above the description viewport so players
            # see only the larger description body below the separate title.
            for section, source_records in source_payload.items():
                translated_records = translated_payload.get(section)
                if not isinstance(source_records, dict) or not isinstance(translated_records, dict):
                    continue
                for record_id, source_record in source_records.items():
                    translated_record = translated_records.get(record_id)
                    if not isinstance(source_record, dict) or not isinstance(translated_record, dict):
                        continue
                    source_desc = source_record.get("desc")
                    translated_name = translated_record.get("name")
                    translated_desc = translated_record.get("desc")
                    if not all(isinstance(value, str) and value for value in (
                        source_desc, translated_name, translated_desc
                    )):
                        continue
                    if CJK_RE.search(source_desc):
                        exact[source_desc] = f"{translated_name}：\n{translated_desc}"
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

    fallback_added = 0
    community_preferred = 0
    for source, target in ANDROID_CONFIRMED_EXACT.items():
        if source in ANDROID_REQUIRED_OVERRIDE_SOURCES:
            exact[source] = target
        elif source in exact:
            community_preferred += 1
        else:
            exact[source] = target
            fallback_added += 1
    counts["android_confirmed_exact"] = len(ANDROID_CONFIRMED_EXACT)
    counts["android_required_overrides"] = len(ANDROID_REQUIRED_OVERRIDE_SOURCES)
    counts["android_fallbacks_added"] = fallback_added
    counts["android_fallbacks_superseded_by_pc"] = community_preferred
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

    definition_patched_base, synergy_enum_changes = translate_synergy_enum_fields(base)
    output = build_metadata(definition_patched_base, layout, translated_bytes)
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
        "android_affinity_enum": {
            "strategy": "validated field-name rename; enum values and all IL2CPP code unchanged",
            "changed_field_count": len(synergy_enum_changes),
            "changes": synergy_enum_changes,
        },
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
