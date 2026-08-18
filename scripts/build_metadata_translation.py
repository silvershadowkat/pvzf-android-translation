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
CSHARP_FORMAT_FIELD_RE = re.compile(r"\{(\d+)(?:,[^}:]+)?(?::[^}]+)?\}")
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

    # Plant inspection popup. The official Android fragments all retain a
    # trailing newline; older English references dropped it and caused the
    # independently formatted stats to run together (for example,
    # "300/300Damage"). Preserve the source separators exactly.
    "生命值：{0}/{1}\n": "HP: {0}/{1}\n",
    "攻击力：{0}\n": "Damage: {0}\n",
    "生产间隔：{0}秒\n": "Production CD: {0}s\n",
    "光照等级：{0}\n": "Lumos Level: {0}\n",

    # The Gods: Evolved builds this card body by appending a short suffix to
    # the live plant name. The PC project has the completed sentence, while
    # Android stores only this fragment in its literal table.
    "保底时大招所需射击子弹数-10": ": -10 shots needed for ultimate",

    # Gods: Evolved, Gatling Cherrybomber's Ballistics upgrade. The PC
    # translator replaces the complete sentence, while Android stores only
    # this suffix and prepends the localized plant name at runtime.
    "每次攻击多发射一发子弹": ": Gains +1 projectile",

    # The same Android-only split-string pattern is used by several other
    # Gods: Evolved upgrade cards. These suffixes are exact matches inside the
    # complete sentences translated by the PC community project.
    "每一发子弹都会造成爆头伤害": ": Critical hits are now guaranteed",
    "每次攻击额外发射一枚黑冰刺": ": Fires an additional doomspike every attack",
    "每轮攻击额外发射一轮多功能杨桃子弹": (
        ": Fires additional quasar projectiles each attack"
    ),
    "升级成星辉形态": ": Upgrade to Stellar form",
    "变为五线射手，子弹可无限穿透": (
        ": Now shoots in all lanes and its projectiles pierce infinitely"
    ),
    "在前方生成一束天网攻击僵尸": (
        ": Summons a Celestial Beam at the farthest available column to attack zombies"
    ),
    "大招所需杀敌数-20": ": -20 kills required for ultimate",
    "攻击时没有吞噬僵尸也将释放爆炸，吞下则释放两次": (
        ": If its attack misses, it will still release an explosion. "
        "If it devours a zombie, it will release two explosions"
    ),
    "爆头所需次数-1": ": Attacks required for headshot -1",
    "的子弹命中僵尸时额外造成多次伤害，每次伤害对小范围内的敌方随机单体造成相当于子弹伤害100%的伤害": (
        ": When its projectiles hit zombies, they deal 100% of their damage "
        "to a random zombie in a small area"
    ),
    "连射、散射概率增加12%": (
        ": Rapid fire and spread fire chances increased by 12%"
    ),
    "陨星+1\n陨星锁定全场血量最高的僵尸，落地时造成相当于卷心菜攻击力100%的群体伤害\n然后造成30次伤害，每次伤害对范围内敌方随机单体造成100%的爆炸伤害": (
        ": +1 Helios Meteor. The meteor targets the zombie with the most health "
        "on the lawn, causing area damage equivalent to 100% of Helios Cabbage's "
        "attack power when landing, then dealing 30 hits of 100% explosive damage "
        "to random zombies in range"
    ),

    # This mode sentence is assembled as prefix + live plant name + suffix.
    "在该模式中，": "In this mode, ",
    "会持续射击鼠标所在位置": " continuously shoots at the cursor position",

    # Damage Statistics. The PC translator handles the complete rendered rows
    # with regexes, but Android builds the hypnotized-zombie row from this
    # standalone label plus a separately translated total-damage fragment.
    # Match the PC community project's established wording.
    "魅惑僵尸": "Hypnotized Zombies",

    # Additional player-facing fragments found by the post-release audit.
    # Several are stored as a short title beside an already-English
    # description, so an exact full-sentence comparison cannot discover them.
    "升级为": " upgrades to ",
    "大帅线": "Archduke Route",
    "斩将祭旗": "Trophy Hunter",
    "格挡反击：僵尸闪避时对附近植物造成100%反伤": (
        "Counterstrike: Zombies deal 100% damage back to nearby plants when they dodge"
    ),
    "游戏失败": "Game Over",
    "生生不息": "Perennial Vitality",
    "获得新植物：": "Obtain a new plant: ",
    "获得词条：": "Modifier Acquired: ",
    "解锁新卡牌：": "New card unlocked: ",
    "高能射线": "Energy Focus",
    "黑曜护体": "Soul Curtain",
    "斩杀失败时也能造成5000真实伤害": (
        "Deals 5,000 true damage even if the execute fails"
    ),
    "在场时记录全场植物的治疗量，爆炸时基于治疗量造成额外伤害并治疗全体植物": (
        "While present, records healing done by all plants. When it explodes, "
        "deals bonus damage based on the recorded healing and heals all plants"
    ),
    "格挡子弹时会使周围植物回复生命值，并使其造成的攻击力提高": (
        "Blocking projectiles restores HP to nearby plants and increases their damage"
    ),
    "持续为周围3x3低血量植物提供护盾": (
        "Continuously shields low-HP plants in the surrounding 3x3 area"
    ),
    "根据BGM节奏点击下落的音符\n连击越高，子弹越多！": (
        "Hit falling notes to the BGM rhythm\nHigher combos fire more projectiles!"
    ),
    "消耗自身生命值和周围3x3植物血量生命值攻击敌人，击中敌人会回复自身生命值": (
        "Consumes its own HP and the HP of plants in the surrounding 3x3 area to "
        "attack enemies. Hitting an enemy restores its HP"
    ),
    "毁灭魅惑菇 + 毁灭菇\n使用金盏花、毁灭菇进行亚种切换\n<color=red>亚种在非旅行模式不推荐使用</color>": (
        "Curse-shroom + Doom-shroom\nUse Marigold or Doom-shroom to switch "
        "subspecies\n<color=red>Subspecies are not recommended outside Odyssey Mode</color>"
    ),
    "铁豆x3 + 磁力菇\n使用三叶草、磁力菇进行亚种切换": (
        "Buck-shroom x3 + Magnet-shroom\nUse Blover or Magnet-shroom to switch subspecies"
    ),
    "Modifier Acquired: 力量会给予希望\n获得植物：": (
        "Modifier Acquired: Vulcannon + Epic Twin Inferno-nut Synergy ON!!\n"
        "Plant Acquired: "
    ),

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

# Android 3.9 corrections that intentionally differ from the older PC text.
# The seed-selection font maps punctuation poorly, so the start button uses
# plain capital letters to avoid displaying apostrophe or exclamation glyphs
# as unrelated symbols.
ANDROID_CONFIRMED_EXACT.update({
    "一起摇滚吧！": "<size=20>LETS ROCK",
    "超级肥料": "Super Fertilizer",
    "\n版本：": "\nVersion: ",
    "\n当前版本：": "\nCurrent version: ",

    # Android 3.9 SP Evolution cards. A broad PC regex translated only the
    # colored heading and discarded every unlock recipe that followed it.
    "<color=red>【SP进化】</color>：\n<nobr>解锁<color=red>究极寒冰小喷菇</color>\n寒冰机枪小喷菇+豌豆射手</nobr>\n<nobr>解锁<color=red>究极阳光小喷菇</color>\n阳光机枪小喷菇+豌豆射手</nobr>\n继承原转换配方": (
        "<color=red>[SP Evolution]</color>:\n"
        "<nobr>Unlock <color=red>Ultimate Gatling Icicle-shroom</color>\n"
        "Gatling Icicle-shroom + Peashooter</nobr>\n"
        "<nobr>Unlock <color=red>Ultimate Gatling Sun-shroom</color>\n"
        "Gatling Sun-shroom + Peashooter</nobr>\n"
        "Inherits the original conversion recipe"
    ),
    "<color=red>【SP进化】</color>：\n<nobr>解锁<color=red>究极毁灭菇射手</color>\n毁灭菇机枪射手+毁灭菇</nobr>\n<nobr>解锁<color=red>究极毁灭胆小菇</color>\n毁灭机枪胆小菇+毁灭菇</nobr>\n继承原转换配方": (
        "<color=red>[SP Evolution]</color>:\n"
        "<nobr>Unlock <color=red>Ultimate Doom Gatling</color>\n"
        "Doom Gatling + Doom-shroom</nobr>\n"
        "<nobr>Unlock <color=red>Ultimate Doom Scaredy-shroom</color>\n"
        "Doom Gatling Scaredy-shroom + Doom-shroom</nobr>\n"
        "Inherits the original conversion recipe"
    ),
    "<color=red>【SP进化】</color>：\n<nobr>解锁<color=red>究极浴火射手</color>\n浴火三线射手+火爆辣椒</nobr>\n<nobr>解锁<color=red>究极飞火射手</color></nobr>\n继承原转换配方": (
        "<color=red>[SP Evolution]</color>:\n"
        "<nobr>Unlock <color=red>Ultimate Phoenix Threepeater</color>\n"
        "Phoenix Threepeater + Jalapeno</nobr>\n"
        "<nobr>Unlock <color=red>Ultimate Flying Phoenix</color></nobr>\n"
        "Inherits the original conversion recipe"
    ),
    "<color=red>【SP进化】</color>：\n<nobr>解锁<color=red>究极阳光帝果</color>\n阳光帝果+坚果</nobr>\n<nobr>解锁<color=red>究极火焰帝果</color>\n火焰帝果+坚果</nobr>\n继承原转换配方": (
        "<color=red>[SP Evolution]</color>:\n"
        "<nobr>Unlock <color=red>Ultimate Twin Solar-nut</color>\n"
        "Twin Solar-nut + Wall-nut</nobr>\n"
        "<nobr>Unlock <color=red>Ultimate Fire Twin Solar-nut</color>\n"
        "Fire Twin Solar-nut + Wall-nut</nobr>\n"
        "Inherits the original conversion recipe"
    ),
})

# Deeper Android-only metadata audit. These strings survived both the PC exact
# pass and the older Android reference passes because the mobile build stores
# shortened descriptions, recipe panels, and runtime fragments rather than the
# complete PC sentence. Entries below are limited to unambiguous player-facing
# text. Internal log messages, scene/object identifiers, creator handles, and
# uncertain flavor-title terminology remain untouched for manual review.
ANDROID_CONFIRMED_EXACT.update({
    # File access and level-selection UI.
    "\n请检查设备权限是否开启": "\nPlease check that storage permission is enabled.",
    " 关卡首胜会额外获得10张抽奖券，重复刷单个关卡也能产出抽奖券": (
        " The first clear of a level awards 10 bonus raffle tickets. "
        "Repeating a level can also earn raffle tickets."
    ),

    # Android-only mode labels and controls.
    "冒险秘境：第{0}关": "Adventure Realm: Level {0}",
    "冬夜": "Winter Night",
    "减益": "Debuff",
    "出售植物：": "Sell Plant: ",
    "加速喷雾": "Speed Spray",
    "施肥": "Fertilize",
    "无法从 {0} 融合出 {1}": "Cannot fuse {1} from {0}",
    "混池</color>": "Mixed Pool</color>",
    "混池模式（已选0个场景）": "Mixed Pool Mode (0 scenes selected)",
    "混池模式：点击场景进行选择（可多选），再次点击同一场景可取消": (
        "Mixed Pool Mode: Tap scenes to select multiple. Tap a selected scene again to remove it."
    ),
    "清空弹匣": "Empty Magazine",
    "点击礼盒抽取植物": "Tap the Gift Box to draw a plant",
    "能量·金咖啡豆": "Energy: Golden Coffee Bean",
    "自动存档": "Autosave",
    "自动存档: ": "Autosave: ",
    "自动存档: 回合{0} Lv.{1} ({2})": "Autosave: Round {0} Lv.{1} ({2})",
    "自动存档不存在": "No autosave exists",
    "自动存档损坏: ": "Autosave is corrupted: ",
    "自动存档间隔: {0}秒\n": "Autosave interval: {0}s\n",
    "未知原因购买失败": "Purchase failed for an unknown reason",
    "请选择僵尸词条（可多选）": "Select zombie modifiers (multiple selections allowed)",
    "请选择僵尸词条（可多选），已选：{0}个": (
        "Select zombie modifiers (multiple selections allowed). Selected: {0}"
    ),
    "购买了{0}个{1}": "Purchased {0} x {1}",
    "购买失败，花园已满": "Purchase failed. The Garden is full.",
    "购买植物：": "Buy Plant: ",
    "高效肥料": "Efficient Fertilizer",
    "高温灼烧": "Scorching Heat",

    # Plant subspecies recipe panels. Terminology follows the current PC
    # community Almanac wherever that plant already has an English name.
    "冰地刺王 + 火地刺王\n使用坚果墙、地刺王进行亚种切换": (
        "Icerock + Hearthrock\nUse Wall-nut or Spikerock to switch subspecies"
    ),
    "机枪射手 + 毁灭菇\n使用胆小菇、豌豆射手进行亚种切换": (
        "Gatling Pea + Doom-shroom\nUse Scaredy-shroom or Peashooter to switch subspecies"
    ),
    "机枪小喷菇 + 寒冰菇\n使用向日葵、寒冰菇进行亚种切换": (
        "Gatling Pea-shroom + Ice-shroom\nUse Sunflower or Ice-shroom to switch subspecies"
    ),
    "樱桃辣椒 + 爆竹\n该植物暂时没有亚种": (
        "Pepper Popper + Bamboom\nThis plant currently has no subspecies"
    ),
    "毁灭樱桃 + 樱桃炸弹\n使用窝瓜、樱桃炸弹进行亚种切换": (
        "Black Cherry + Cherry Bomb\nUse Squash or Cherry Bomb to switch subspecies"
    ),
    "毁灭辣椒 + 毁灭大嘴花\n使用土豆雷、大嘴花进行亚种切换\n提示：使用死神大嘴花来触发植物亡语效果": (
        "M.A.D. Pepper + Doom Chomper\nUse Potato Mine or Chomper to switch subspecies\n"
        "Tip: Use Grim Chomper to trigger plant death effects"
    ),
    "流光仙人掌 + 流光保护伞\n使用寒冰菇、路灯花进行亚种切换": (
        "Lumos Cactus + Lumos Umbrella\nUse Ice-shroom or Plantern to switch subspecies"
    ),
    "流光磁力菇 + 樱桃磁力菇\n使用向日葵、樱桃炸弹进行亚种切换\n提示：试试把僵尸掉落的机械碎片放置坚果上": (
        "Lumos Magnet + Grenadier Magnet\nUse Sunflower or Cherry Bomb to switch subspecies\n"
        "Tip: Try placing machine parts dropped by zombies onto Wall-nuts"
    ),
    "磁力南瓜 + 磁力菇\n使用杨桃、南瓜头进行亚种切换": (
        "Pumpkin Morph + Magnet-shroom\nUse Starfruit or Pumpkin to switch subspecies"
    ),
    "超级伞 + 菜伞\n使用西瓜、卷心菜进行亚种切换": (
        "Alchemist Umbrella + Umbrella Kale\nUse Melon-pult or Cabbage-pult to switch subspecies"
    ),
    "金盆 + 向日葵\n使用铲子进行亚种切换": (
        "Radiant Pot + Sunflower\nUse the Shovel to switch subspecies"
    ),
    "阳光坚果 + 坚果墙\n使用火爆辣椒、向日葵进行亚种切换": (
        "Solar-nut + Wall-nut\nUse Jalapeno or Sunflower to switch subspecies"
    ),
    "魅惑菇 + 魅惑菇\n使用樱桃炸弹、魅惑菇进行亚种切换": (
        "Hypno-shroom + Hypno-shroom\nUse Cherry Bomb or Hypno-shroom to switch subspecies"
    ),
    "黄油地刺 + 窝刺\n使用花盆、铲子进行亚种切换": (
        "Butterweed + Squashweed\nUse Flower Pot or the Shovel to switch subspecies"
    ),

    # Revised or shortened modifier descriptions. Clear matches reuse the PC
    # community meaning; Android-only descriptions receive conservative literal
    # translations without inventing mechanics that are not present in source.
    "信息封锁II：永久关闭僵尸显血": "Information Lockdown II: Permanently disable zombie HP display",
    "信息封锁I：永久关闭植物显血": "Information Lockdown I: Permanently disable plant HP display",
    "关闭僵尸显血": "Disable zombie HP display",
    "关闭植物显血": "Disable plant HP display",
    "僵尸成长速度加快": "Zombies grow stronger faster",
    "僵尸死亡后有概率复活": "Zombies have a chance to revive after death",
    "僵尸死亡时有概率复活成随机僵尸": (
        "Zombies have a chance to revive as a random zombie after death"
    ),
    "僵尸获得额外强化": "Zombies gain an additional buff",
    "全民皆兵：非究极类僵尸获得2倍血量、伤害加成和1.5倍速度加成": (
        "All non-Odyssey zombies have x2 HP and Attack, and x1.5 Speed"
    ),
    "定时炸弹：魅惑僵尸死亡时会产生爆炸，对附近僵尸造成自身1.5倍韧性的伤害": (
        "Blaze of Glory: When hypnotized zombies die, they explode and deal damage equal to "
        "150% of their max HP to nearby zombies"
    ),
    "开局积分归零": "Start with 0 Points",
    "开局阳光归零": "Start with 0 Sun",
    "弱者斩杀": "Execute the Weak",
    "强健体魄III：全体僵尸血量增加400%": "Robust Physique III: All zombies gain 400% max HP",
    "强健体魄II：全体僵尸血量增加200%": "Robust Physique II: All zombies gain 200% max HP",
    "强健体魄I：全体僵尸血量增加100%": "Robust Physique I: All zombies gain 100% max HP",
    "怒不可遏III：全体僵尸攻击增加400%": "Unbridled Rage III: All zombies gain 400% Attack",
    "怒不可遏II：全体僵尸攻击增加200%": "Unbridled Rage II: All zombies gain 200% Attack",
    "怒不可遏I：全体僵尸攻击增加100%": "Unbridled Rage I: All zombies gain 100% Attack",
    "急行军：第一波僵尸到达时间降低至5秒，僵尸刷新间隔降低至15秒": (
        "The first zombie wave arrives after 5s, and the interval between waves is reduced to 15s"
    ),
    "战争激励：每3秒令全场僵尸攻击力翻倍，有上限": (
        "Double the Attack of all zombies on the lawn every 3s, up to the limit"
    ),
    "植物受到的伤害永久保留": "Damage taken by plants persists permanently",
    "植物数量上限降低": "Reduce the maximum number of plants",
    "植物有概率突然死亡": "Plants have a chance to die immediately",
    "植物死亡时对附近植物造成爆炸伤害": (
        "When a plant dies, it explodes and damages nearby plants"
    ),
    "每波僵尸数量增加": "Increase the number of zombies in each wave",
    "空军强化：飞行僵尸获得100%血量加成": "Air Force Reinforcement: Flying zombies gain 100% max HP",
    "适应之力：僵尸每次受伤，获得相当于伤害量1%的护甲，有上限": (
        "Adaptive Strength: Each time a zombie takes damage, it gains Armor equal to "
        "1% of that damage, up to the limit"
    ),
    "随从强化：非领袖僵尸获得30%速度加成和30%血量加成": (
        "Minion Reinforcement: Non-mini-boss zombies gain 30% Speed and max HP"
    ),
    "非究极僵尸获得2倍血量、伤害和1.5倍速度": (
        "Non-Odyssey zombies gain x2 HP and Attack, and x1.5 Speed"
    ),
    "非领袖僵尸获得30%速度和血量加成": (
        "Non-mini-boss zombies gain 30% Speed and max HP"
    ),
    "领袖僵尸获得30%速度和血量加成": "Mini-boss zombies gain 30% Speed and max HP",
    "领袖强化：领袖僵尸获得30%速度加成和30%血量加成": (
        "Leader Reinforcement: Mini-boss zombies gain 30% Speed and max HP"
    ),
    "飞行僵尸血量翻倍": "Flying zombies gain x2 max HP",

    # Additional unambiguous skill and synergy descriptions.
    "使我方小队造成的伤害提高，释放大流星时造成额外伤害": (
        "Increases your team's damage and deals additional damage when the Great Meteor is cast"
    ),
    "使我方植物死亡时掉落阳光": "Your plants drop Sun when they die",
    "使队友获得龙灵，队友攻击时，获得基于光照等级的护盾": (
        "Grants Dragon Spirit to allies. When an ally attacks, it gains a shield based on Lumos level"
    ),
    "全场植物按百分比分摊伤害，我方小队幸运一击伤害提高，新增固定时间获得充能": (
        "All plants share damage by percentage, your team's critical damage is increased, "
        "and charge is gained at fixed intervals"
    ),
    "出场时获得究极路灯花，超新星爆发的能量需求和伤害降低": (
        "Start with an Ultimate Plantern. Supernova Burst requires less energy and deals less damage"
    ),
    "出场自带点数，点数上限增加": "Start with Points and increase the maximum Points limit",
    "加速提供更高伤害，同时治疗生命值较低的植物": (
        "Speed boosts provide more damage and also heal low-HP plants"
    ),
    "发射的子弹附带追踪效果": "Fired projectiles gain homing",
    "可以使用金咖啡豆释放大招，为我方植物积攒能力，并使其攻击力提高": (
        "Use a Golden Coffee Bean to cast the ultimate, build power for your plants, "
        "and increase their Attack"
    ),
    "可以按星级为前台驯海游侠提供的羁绊增益": (
        "Provides a star-level synergy bonus to the active Sea-Taming Ranger"
    ),
    "吞噬僵尸可时战神行动提前": "Devouring a zombie advances the God of War's action",
    "吸引子弹可以提高子弹伤害，并提供更多金币": (
        "Attracting projectiles increases their damage and provides more Coins"
    ),
    "命中目标后为我方小队叠加增益，大招造成额外伤害": (
        "Hitting a target stacks a buff for your team, and the ultimate deals additional damage"
    ),
    "在敌人血量低于50%时额外发射子弹，并在敌人被消灭后永久提高前后台强度": (
        "Fires additional projectiles at enemies below 50% HP. Defeating an enemy permanently "
        "increases active and reserve strength"
    ),
    "场上敌人越多，全队幸运一击的伤害越高": (
        "The more enemies on the lawn, the higher your team's critical damage"
    ),
    "大招回复的生命值提高，普通攻击获得更多能量，造成更高的伤害": (
        "The ultimate restores more HP, while normal attacks gain more energy and deal more damage"
    ),
    "子弹可弹射更多次数，并使目标陷入可叠加的感电": (
        "Projectiles bounce more times and apply a stackable Electrified effect"
    ),
    "对陷入减速状态的敌人施加标记，攻击消耗标记造成额外伤害，攻击范围提高": (
        "Marks slowed enemies. Attacks consume the mark to deal additional damage, and attack range is increased"
    ),
    "小飞龙的召唤频率增加": "Summon Mini Dragons more frequently",
    "我方小队其他目标释放大招后，使玉米的大招能发射更多子弹": (
        "After another teammate casts an ultimate, Corn's ultimate fires more projectiles"
    ),
    "我方小队受到伤害时为鱼丸提供能量，释放能量以回复生命值，并发动反击": (
        "When your team takes damage, Fishball gains energy. It spends energy to restore HP and counterattack"
    ),
    "我方小队攻击敌人后，治疗我方低生命值目标": (
        "After your team attacks an enemy, heal a low-HP ally"
    ),
    "我方植物损失生命值时，仙人掌可积攒充能层数，以释放大招攻击敌人": (
        "When your plants lose HP, Cactus gains charge stacks for its ultimate"
    ),
    "手推车可以用来暂存和移动植物，且可以刷新植物状态\n在这一关中仅需3秒冷却，通关后可在绝大部分关卡中使用": (
        "The Wheelbarrow can store and move plants and refresh their state.\n"
        "It has only a 3s cooldown in this level and can be used in most levels after completion"
    ),
    "把植物放到手推车上": "Place a plant on the Wheelbarrow",
    "攻击会使蒜毒伤害立即结算一次": "Attacks immediately trigger one tick of Garlic Poison damage",
    "攻击会同时削减僵尸的护甲": "Attacks also reduce zombie Armor",
    "攻击力随攻速增加而增加": "Attack increases with Attack Speed",
    "攻击可以使敌人易伤，并触发多次射击": (
        "Attacks make enemies Vulnerable and trigger multiple shots"
    ),
    "攻击后为目标叠加持续蒜毒，并使地方被攻击后对范围内敌人额外造成持续蒜毒": (
        "Attacks stack lasting Garlic Poison on the target and spread additional Garlic Poison to nearby enemies"
    ),
    "攻击造成范围伤害": "Attacks deal area damage",
    "攻击造成范围伤害，并削减敌人的护甲": "Attacks deal area damage and reduce enemy Armor",
    "攻击附带1级寒冷，敌人被冻结后受到的伤害提高": (
        "Attacks apply 1 Cold. Frozen enemies take increased damage"
    ),
    "攻击附带余烬效果，并在可发射毁灭菇子弹": (
        "Attacks apply Ember and can fire Doom-shroom projectiles"
    ),
    "敌人攻击力-5%/10%/15%": "Enemy Attack -5%/10%/15%",
    "本关卡无法融合究极植物，但植物的数值大幅提高\n不要害怕死亡！": (
        "Odyssey plants cannot be fused in this level, but plant stats are greatly increased.\n"
        "Do not fear death!"
    ),
    "每个一段时间获得一个究极红温帝果": "Periodically gain an Ultimate Red-Heat Emperor-nut",
    "每打完一关随机重置，每5关，僵尸词条数量+1\n僵尸词条越多、强度越高，通关后掉落的抽奖券数量就越多\n当前词条：": (
        "Randomly reset after each level. Every 5 levels, gain +1 zombie modifier.\n"
        "More and stronger zombie modifiers award more raffle tickets after completion.\n"
        "Current modifiers:"
    ),
    "每次击杀敌人有概率获得金币，我方小队击杀敌人后也会释放僚机，敌人受到的伤害提高": (
        "Defeating enemies may award Coins. Your team also launches wingmen after a kill, "
        "and enemies take increased damage"
    ),
    "每次发射的豆量提高": "Fire more peas with each attack",
    "每次攻击后，提供伤害加成，敌人受到的伤害增加": (
        "Each attack grants a damage bonus and increases damage taken by enemies"
    ),
    "每第5次攻击强制触发吞噬": "Every 5th attack is guaranteed to Devour",
    "治疗范围增加到全屏": "Increase healing range to the entire lawn",
    "点燃的豌豆升至红火状态": "Ignited peas are upgraded to Red-Heat state",
    "种植僵尸后，火红莲会持续为你生产僵尸": (
        "After planting a zombie, Fire Lotus continuously produces zombies for you"
    ),
    "究极云杉会提供更多护盾，并提高拥有大量护盾目标的攻击力": (
        "Ultimate Spruce provides more shields and increases the Attack of targets with large shields"
    ),
    "究极植物削弱，普通植物大幅强化": "Odyssey plants are weakened, while normal plants are greatly strengthened",
    "羁绊的充能速度提高，我方小队的伤害和射速提高": (
        "Synergy charges faster, and your team's damage and fire rate are increased"
    ),
    "蒜毒叠加的层数提高": "Increase the maximum Garlic Poison stacks",
    "被减速的敌人受到攻击时获得能量，满能量后释放大招攻击敌人": (
        "Gain energy when attacking slowed enemies. At full energy, cast the ultimate"
    ),
    "被敌人啃食时，令敌人进入中毒效果": "Poisons enemies that bite it",
    "超级大嘴花的攻击力提高，斩杀线也提高": (
        "Chompzilla gains increased Attack and a higher execute threshold"
    ),
    "迅捷如风III：全体僵尸速度增加400%": "Swift as the Wind III: All zombies gain 400% Speed",
    "迅捷如风II：全体僵尸速度增加200%": "Swift as the Wind II: All zombies gain 200% Speed",
    "迅捷如风I：全体僵尸速度增加100%": "Swift as the Wind I: All zombies gain 100% Speed",
    "进入战斗时获得追忆，并强化所有投手植物的角色赋能效果，获得词条绝对力量": (
        "Gain Reminiscence when battle begins, strengthen all lobber role effects, "
        "and gain the Absolute Power modifier"
    ),
    "通关后随机刷新本关场景和僵尸\n": (
        "After clearing the level, randomly reroll its scene and zombies\n"
    ),
    "造成更高的伤害，我方小队造成的伤害提高": (
        "Deals more damage and increases your team's damage"
    ),
    "释放攻击后生阳光额外攻击，会基于场上向日葵的数量增加攻击段数": (
        "After attacking, produces Sun and performs additional hits based on the number of Sunflowers on the lawn"
    ),
    "释放攻击时使生命值上限永久提高，生命上限使受伤充能额外提高": (
        "Attacking permanently increases max HP. Higher max HP also increases charge gained from taking damage"
    ),
    "阳光获取量降低": "Reduce Sun gained",
    "随时间提供更多护盾，我方小队伤害提高": (
        "Provides more shields over time and increases your team's damage"
    ),
    "随机到的僵尸词条：\n": "Random zombie modifiers:\n",
    "霸凌弱者：植物因血量归零死亡时爆炸，对附近植物自身最大生命值的伤害": (
        "Bully the Weak: When a plant dies from reaching 0 HP, it explodes and deals "
        "damage equal to its max HP to nearby plants"
    ),
    "黄油概率提高，被黄油命中的僵尸会成为追踪子弹的集火目标": (
        "Increase the Butter chance. Zombies hit by Butter become the focus target for homing projectiles"
    ),
    "黑洞爆炸会延后战斗结束倒计时": "Black-hole explosions delay the battle-end countdown",
})

# A second structural review covers short status text and prompts that are
# assembled at runtime. These do not resemble the PC project's complete
# sentences closely enough for exact or regex matching, but their Android UI
# meaning is unambiguous. Developer diagnostics and uncertain names are still
# intentionally excluded.
ANDROID_CONFIRMED_EXACT.update({
    # General prompts, state labels, and online/custom-level UI.
    ">退出": ">Exit",
    "API密钥无效，无法删除关卡": "Invalid API key. The level cannot be deleted.",
    "你真的要永久删除这个关卡吗？": "Permanently delete this level?",
    "你真的要重置秘境吗": "Reset the Realm?",
    "关卡不存在": "Level does not exist",
    "在线关卡\nid：": "Online Level\nID: ",
    "用户上传": "User Upload",
    "无法连接到服务器": "Unable to connect to the server",
    "无法连接至服务器，请重试": "Unable to connect to the server. Please try again.",
    "正在下载关卡: ": "Downloading level: ",
    "关卡不存在或已被删除": "The level does not exist or has been deleted",
    "未知场景": "Unknown Scene",
    "未知词条": "Unknown Modifier",
    "未知原因": "Unknown reason",
    "超时": "Timed Out",
    "有效": "Valid",
    "无效": "Invalid",
    "是": "Yes",
    "否": "No",
    "放弃": "Give Up",
    "信息": "Info",
    "选项": "Option",
    "选项描述": "Description",

    # Save selection and autosave status assembled from several fragments.
    "存档{0}": "Save {0}",
    "已选择存档：": "Selected save: ",
    "已切换到存档：": "Switched to save: ",
    "存档已重命名为 ": "Save renamed to ",
    "重命名存档：": "Rename save: ",
    "这个存档无效": "This save is invalid",
    "上次使用的存档 '": "Last used save '",
    "槽位{0}: [空]\n": "Slot {0}: [Empty]\n",
    "槽位{0}: {1} - 回合{2} Lv.{3} ({4})\n": (
        "Slot {0}: {1} - Round {2} Lv.{3} ({4})\n"
    ),
    "最大槽位数: {0}\n": "Maximum slots: {0}\n",
    "当前版本：": "Current version: ",
    "版本：": "Version: ",

    # Gacha, modifier selection, and progression UI.
    "你已经选择了所有{0}个可用的僵尸词条": (
        "You have selected all {0} available zombie modifiers"
    ),
    "已选择：{0}，当前共{1}个词条": (
        "Selected: {0}. Current modifiers: {1}"
    ),
    "所有词条已选完": "All modifiers have been selected",
    "没有可用的选项供队伍{0}选择": "No options are available for Team {0}",
    "随机到的僵尸词条：\n": "Random zombie modifiers:\n",
    "抽奖券不足": "Not enough raffle tickets",
    "抽奖券：{0} / {1} / {2} / {3}": "Raffle Tickets: {0} / {1} / {2} / {3}",
    "抽取次数：\n{0}/{1}\n": "Draws:\n{0}/{1}\n",
    "你获得了一张抽奖券": "You received a raffle ticket",
    "十连 ({0})": "Draw 10 ({0})",
    "单抽 ({0})": "Single Draw ({0})",
    "持有量已达上限": "Maximum amount reached",
    "材料不足": "Not enough materials",
    "当前奖池：": "Current Pool: ",
    "当前up植物：\n": "Current Featured Plant:\n",
    "当前能力值：{0}/100": "Current Power: {0}/100",
    "强化加成：{0:F0}%": "Upgrade Bonus: {0:F0}%",
    "强化加成：{0:F0}%\n": "Upgrade Bonus: {0:F0}%\n",
    "强化等级：{0}/{1}\n": "Upgrade Level: {0}/{1}\n",
    "强化等级：{0}/{1}（已满级）\n": "Upgrade Level: {0}/{1} (Max)\n",
    "等级": "Level",
    "等级已满": "Max Level",
    "经验": "Experience",
    "获得植物：": "Plant obtained: ",
    "还需{0}": "Need {0} more",
    "剩余{0}": "Remaining: {0}",

    # Shop and board interaction text.
    "(-{0}金币, 第{1}次刷新)": "(-{0} Coins, reroll #{1})",
    "(免费刷新)": "(Free reroll)",
    "场上植物数量: {0}\n": "Plants on the lawn: {0}\n",
    "场上已经有一个": "There is already a ",
    "{0}行{1}列已被占用，无法放置设备，已退回仓库": (
        "Row {0}, column {1} is occupied. The item was returned to storage."
    ),
    "右侧没有空位，清空并使用最右边的位置": (
        "No space on the right. Clearing and using the rightmost position."
    ),
    "左侧没有空位，清空并使用最左边的位置": (
        "No space on the left. Clearing and using the leftmost position."
    ),
    "请先点击仓库卡牌选择需要强化的植物": (
        "First tap a plant card in storage to choose the plant to upgrade"
    ),
    "植物: {0}": "Plant: {0}",
    "种植了：": "Planted: ",
    "浇水": "Water",
    "血量": "HP",
    "融合植物": "Fusion Plants",
    "直接融合: {0} 种": "Direct fusions: {0}",
    "自定义卡组已达上限": "Custom loadout limit reached",
    "自定义路线：": "Custom Route: ",

    # Scene and gameplay notifications.
    "场景切换已取消": "Scene change canceled",
    "场景切换进行中，无法进行新的切换": (
        "A scene change is already in progress"
    ),
    "场景已切换到：{0}": "Scene changed to: {0}",
    "夜晚场景": "Night Scene",
    "早晨场景": "Morning Scene",
    "小心你没见过的僵尸！": "Watch out for zombies you have not seen before!",
    "保护你的胆小菇\n两指拖动屏幕": (
        "Protect your Scaredy-shroom\nDrag the screen with two fingers"
    ),
    "第一波僵尸提前到达，刷新间隔缩短": (
        "The first zombie wave arrives earlier and wave intervals are shorter"
    ),
    "精英僵尸出现概率提高": "Elite zombies appear more often",
    "最后一击：{0}\n": "Final Hit: {0}\n",
    "并获得超进化星星{0}个": " and receive {0} Super Evolution Stars",
})

# Android's plant Almanac renders affinity names by calling ToString()
# on this enum. Enum member names live in metadata's definition string heap,
# not in the ordinary IL2CPP literal database, so the usual translation pass
# cannot reach them. The field indices moved between 3.8.1 and 3.9, so the
# build now locates and validates the complete ordered enum sequence before
# renaming it. Changing an enum member name does not change its numeric value,
# plant membership, or gameplay logic.
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

# Investment Odyssey derives each card title with InvestBuff.ToString(). The
# PC translation JSON intentionally leaves these title fields blank, so its
# runtime translator only supplies the descriptions. As with plant affinities
# above, the Android build must rename the validated, ordered enum definition
# sequence while retaining every numeric value and all gameplay code unchanged.
ANDROID_381_INVEST_ENUM_FIELDS = {
    9689: ("完美开局", "Perfect Start"),
    9690: ("气氛组", "Cheer Squad"),
    9691: ("无伤通关", "Flawless Victory"),
    9692: ("植物重组", "Plant Reshuffle"),
    9693: ("究极支援", "Ultimate Support"),
    9694: ("恢复生机", "Revitalization"),
    9695: ("简单模式", "Easy Mode"),
    9696: ("难度修改器", "Difficulty Modifier"),
    9697: ("当头一棒", "Opening Strike"),
    9698: ("榜样的力量", "Role Model"),
    9699: ("基层贡献", "Grassroots Support"),
    9700: ("绝对力量奖", "Absolute Power Award"),
    9701: ("存款回报", "Deposit Returns"),
    9702: ("免费刷新", "Free Reroll"),
    9703: ("现金为王", "Cash Is King"),
    9704: ("降本增效", "Cost Efficiency"),
    9705: ("精准暴击", "Precision Crit"),
    9706: ("百花齐放", "Full Bloom"),
    9707: ("榜样的力量II", "Role Model II"),
    9708: ("风暴骑士", "Storm Knight"),
    9709: ("绕口令", "Tongue Twister"),
    9710: ("创伤小组", "Trauma Team"),
    9711: ("打通上下游", "Vertical Integration"),
    9712: ("人海战术", "Human Wave Tactics"),
    9713: ("固定理财", "Fixed Investment"),
    9714: ("星变", "Star Shift"),
    9715: ("沙里淘金", "Panning for Gold"),
    9716: ("延迟收益", "Delayed Returns"),
    9717: ("幸运闪避", "Lucky Dodge"),
    9718: ("攻防一体", "Offense and Defense"),
    9719: ("野蛮成长", "Wild Growth"),
    9720: ("鲜血阶梯", "Blood Ladder"),
    9721: ("超光速提拔", "Lightspeed Promotion"),
    9722: ("幸运之子", "Lucky One"),
    9723: ("积分大使飘飘", "Points Ambassador Piaopiao"),
    9724: ("开源节流", "Increase Revenue, Cut Costs"),
    9725: ("概率事件", "Random Event"),
    9726: ("被动收入", "Passive Income"),
    9727: ("星辉模仿卡", "Starlight Imitater"),
    9728: ("淘宝积分", "Points Marketplace"),
    9729: ("养精蓄锐", "Gathering Strength"),
    9730: ("藏一手", "Ace Up the Sleeve"),
}

# Reviewed Android 3.9 additions. The PC community project did not yet ship a
# 3.9 string pack when this migration was made, so these exact mappings cover
# only new player-facing text. Internal diagnostics, creator handles, font
# character maps, regular expressions, and Unity object identifiers remain
# untouched. A future PC exact translation automatically takes priority.
ANDROID_CONFIRMED_EXACT.update({
    "<color=red>【SP进化】</color>: ": "<color=red>[SP Evolution]</color>: ",
    "\n\n伤害占比：{0:F2}%\n总词条数：{1}": "\n\nDamage Share: {0:F2}%\nTotal Modifiers: {1}",
    "\n\n难度积分：{0}": "\n\nDifficulty Score: {0}",
    "\n难度积分：{0}": "\nDifficulty Score: {0}",
    "<nobr>解锁<color=red>究极贪欲水草</color>\n超级水草+双子金盏花</nobr>\n<nobr>解锁<color=red>究极贪欲盒草</color></nobr>\n惊喜礼盒←→僵尸盲盒": (
        "<nobr>Unlock <color=red>Ultimate Greedy Kelp</color>\n"
        "Hydra Kelp + Twin Marigold</nobr>\n"
        "<nobr>Unlock <color=red>Ultimate Greedy Boxgrass</color></nobr>\n"
        "Surprise Gift Box ↔ Zombie Mystery Box"
    ),
    "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n<nobr>解锁<color=red>究极小松炉</color>\n超级小松炉 + 雪棘芦荟</nobr>": (
        "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n"
        "<nobr>Unlock <color=red>Ultimate Little Pine Furnace</color>\n"
        "Super Little Pine Furnace + Snowspike Aloe</nobr>"
    ),
    "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n子弹飞行时间 + 1秒，每飞行1秒，造成的伤害增加10%": (
        "<size=90%>Projectile flight time +1 second. Damage increases by 10% for each second in flight"
    ),
    "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n攻击僵尸时有4%概率施加一层“解读”标记。若弹射击中已标记的僵尸，则会消耗此标记，使本次弹射次数 + 1。多选每次提高4%概率": (
        "<size=90%>Attacks have a 4% chance to apply 1 Interpretation mark. A ricochet that hits a marked zombie consumes the mark and ricochets 1 additional time. Each additional selection adds 4%"
    ),
    "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n生命值上限 + 50%，其他植物受伤时，获得相当于5%伤害量的蓄能": (
        "<size=90%>Max HP +50%. When another plant takes damage, gain Charge equal to 5% of that damage"
    ),
    "<size=90%>You haven't discovered this plant yet! You can find it by fusing:\n蓄能获取效率增加 + 100%": (
        "<size=90%>Charge gain efficiency +100%"
    ),
    "Ascend: 人人有份": "Ascend: Share the Wealth",
    "Ascend: 固甲摧锋": "Ascend: Armorbreaker",
    "Ascend: 杀戮光环": "Ascend: Killing Aura",
    "Ascend: 烈焰迸发": "Ascend: Flame Burst",
    "Ascend: 谁劈了我的瓜？": "Ascend: Who Split My Melon?",
    "Ascend: 饱和弹射": "Ascend: Saturation Ricochet",
    "Fusion Challenge: 究极黑曜石高坚果皮肤": "Fusion Challenge: Ultimate Obsidian Tall-nut Skin",
    "Upgrade: 密集火焰": "Upgrade: Dense Flames",
    "Upgrade: 延时": "Upgrade: Delay",
    "Upgrade: 杀戮": "Upgrade: Slaughter",
    "Upgrade: 蓄力": "Upgrade: Charge",
    "Upgrade: 财富": "Upgrade: Wealth",
    "{0}给你加了{1}幸运": "{0} gave you {1} Luck",
    "{0}给你扣了{1}幸运": "{0} took {1} Luck from you",
    "{0}给你放了{1}个僵尸": "{0} spawned {1} zombies for you",
    "{0}获得随机独立伤害增幅\n当前增幅：{1:F0}%": "{0} gains a random independent damage bonus\nCurrent bonus: {1:F0}%",
    "{0}获得随机速度增幅\n当前增幅：{1:F0}%": "{0} gains a random speed bonus\nCurrent bonus: {1:F0}%",
    "不破不立：杀死你的全部植物，并将全场植物的独立伤害增幅和速度增幅减半\n在20波后重复这一操作，但改为增幅翻倍": (
        "Rebirth Through Ruin: Kill all your plants and halve every plant's independent damage and speed bonuses. After Wave 20, repeat this operation, but double the bonuses instead"
    ),
    "丢失幸运：幸运值降低75": "Lost Luck: Lose 75 Luck",
    "两极分化：若你的幸运低于75，则立即将幸运设置为75非保底时，你的白银、黄金词条降级为木头品质，但钻石词条升级为棱彩品质": (
        "Polarization: If your Luck is below 75, set it to 75 immediately. Outside guaranteed draws, Silver and Gold modifiers become Wooden quality, while Diamond modifiers become Prismatic quality"
    ),
    "人气票": "Popularity Ticket",
    "从多个植物中任选一个": "Choose one from several plants",
    "从多个选项中自选一株专家植物": "Choose one Expert Plant from several options",
    "以50的幸运开局，并使幸运上限增加至300，然后随机选择5个僵尸词条\n随机的5个词条只有在成功通关任意难度诸神进化后才会刷新": (
        "Start with 50 Luck and increase the Luck cap to 300, then randomly select 5 Zombie Modifiers. These 5 modifiers reroll only after clearing The Gods: Evolved on any difficulty"
    ),
    "伤情恶化：被黑橄榄高坚果僵尸攻击的植物在1秒内无法回血": "Worsening Wounds: Plants hit by Black Football Tall-nut Zombies cannot recover HP for 1 second",
    "使用了超级肥料": "Used Super Fertilizer",
    "倒反天罡：究极植物的倍率降为原来的10%，非究极植物的倍率提高到原来的400%，并获得2倍速度增幅": (
        "Role Reversal: Ultimate Plant multipliers fall to 10% of normal. Non-Ultimate Plant multipliers rise to 400%, with a 2x speed bonus"
    ),
    "傲慢：当你的植物在僵尸上方时，额外造成30%伤害，当你的植物在僵尸下方时，少造成30%伤害，方位以屏幕上下判定": (
        "Pride: Plants deal 30% more damage while above a zombie and 30% less damage while below it, based on vertical screen position"
    ),
    "僵尸方的小丑爆炸伤害降低至1000，并立即获得3000护盾": "Enemy Jack-in-the-box explosion damage is reduced to 1000, and plants immediately gain 3000 Shield",
    "元素反应：究极大喷菇会转化出黑曜石雪爪僵尸；究极火神弹弹菇主子弹额外分裂一个伤害受冰火植物数量增幅的黑曜石瓜；僵尸同时受到红温和寒冷状态时会产生黑曜爆炸": (
        "Elemental Reaction: Ultimate Fume-shroom transforms Obsidian Snowclaw Zombies. Ultimate Fire God Rebound-shroom's main projectile also splits off an Obsidian Melon whose damage scales with the number of Ice and Fire Plants. Zombies that are both Overheated and Chilled trigger an Obsidian Explosion"
    ),
    "全体植物获得抵御碾压的能力，复活后依然生效，并立即获得3000护盾": "All plants become uncrushable, including after revival, and immediately gain 3000 Shield",
    "共5轮，每轮从5个词条中自选一个僵尸词条": "5 rounds total. Choose 1 Zombie Modifier from 5 each round",
    "冷冻冬眠：植物复活后被强制冻结2秒": "Frozen Hibernation: Revived plants are frozen for 2 seconds",
    "出保底了，当前保底阈值：{0}": "Guaranteed reward triggered. Current threshold: {0}",
    "加": "Add",
    "匣中惊喜：究极贪欲水草及亚种的子弹在每轮关卡可获得的积分上限翻倍，且这两种植物的卡牌有概率在种植惊喜礼盒、僵尸盲盒、模仿者时生成": (
        "Surprise in the Box: The per-round point cap from Ultimate Greedy Kelp and its variant's projectiles is doubled. Cards for both plants can appear when planting a Surprise Gift Box, Zombie Mystery Box, or Imitater"
    ),
    "卧薪尝胆：令全场植物的独立伤害增幅和速度增幅翻倍": "Endure and Prepare: Double every plant's independent damage and speed bonuses",
    "危机四伏：每一波僵尸刷新时，额外刷新随机路线的僵尸，数量随波次增加": "Danger Everywhere: Each wave also spawns zombies in random lanes. Their number increases with the wave",
    "厚积薄发：每拥有1000积分，究极贪欲水草及亚种的速度增加1%": "Stored Potential: Ultimate Greedy Kelp and its variant gain 1% speed for every 1000 points",
    "同步治疗：植物回复生命值时，使随机一个僵尸回复25%最大生命值，可过充": "Synchronized Healing: When a plant recovers HP, a random zombie recovers 25% of its max HP and may overheal",
    "命运无常：每次抽取词条时，随机获得-27~23幸运": "Fickle Fate: Gain -27 to 23 Luck whenever modifiers are drawn",
    "命运无常：获得了{0}幸运": "Fickle Fate: Gained {0} Luck",
    "坚毅灵光：究极小松炉的精华落地时，可使植物的韧性增加基础值的0.2%（每轮刷新）": "Resolute Glow: When Ultimate Little Pine Furnace Essence lands, it can increase a plant's Toughness by 0.2% of its base value. Resets each round",
    "复活时间降低99%\n当前标准复活时长：0秒": "Revival time reduced by 99%\nCurrent standard revival time: 0 seconds",
    "复活时间降低{0:F0}%\n当前标准复活时长：{1:F1}秒": "Revival time reduced by {0:F0}%\nCurrent standard revival time: {1:F1} seconds",
    "大变活尸：黑袍小丑王的投掷物不会被保护伞弹走，且落地时召唤一个黑袍小丑王": "Zombie Transformation: Black-robed Jester King's projectile cannot be deflected by Umbrella Leaves and summons another Black-robed Jester King when it lands",
    "嫉妒：当僵尸血量高于50%时，额外造成30%伤害，当僵尸血量低于50%时，少造成30%伤害": "Envy: Zombies deal 30% more damage above 50% HP and 30% less damage below 50% HP",
    "子弹旋转半径提高12%，旋转速度提高80%": "Projectile orbit radius +12% and rotation speed +80%",
    "小丑派对：僵尸血量低于10%时有概率自爆（对领袖和boss无效）": "Jester Party: Zombies below 10% HP have a chance to self-destruct. Does not affect mini-bosses or bosses",
    "小花花": "Little Flower",
    "小鬼当家：非boss僵尸的生命值和体型降低30%，但速度提高200%": "Little Terrors: Non-boss zombies lose 30% HP and size but gain 200% speed",
    "尝试重连   最大次数:{0}，当前次数:{1}": "Reconnecting   Maximum attempts: {0}, current attempt: {1}",
    "尸稠之路：解锁亚种窝油帝盆。窝油帝刺的攻击和窝油帝盆生成的黄油窝瓜的定身时间x3": "Crowded Road: Unlock the Butter Emperor Pot variant. Butter Emperor Spike attacks and Butter Squashes created by Butter Emperor Pot immobilize for 3x as long",
    "帅令加身：机枪黑橄榄僵尸将发射诅咒铁豌豆": "Commander's Order: Gatling Black Football Zombies fire Cursed Iron Peas",
    "幸运提高{0:F0}，幸运可以提高好词条出现概率\n当前幸运值：{1}/{2:F0}": "Luck +{0:F0}. Luck increases the chance of better modifiers\nCurrent Luck: {1}/{2:F0}",
    "廉价审美：木头、白银词条加成变为原来的110%，黄金，钻石词条加成变为原来的70%": "Cheap Taste: Wooden and Silver modifier bonuses become 110% of normal; Gold and Diamond bonuses become 70%",
    "开炮：解锁亚种铁豆突击队。铁豆小队的防空炮的击退幅度翻倍，伤害x3。铁豆突击队的伤害x3": "Open Fire: Unlock the Iron Pea Assault Team variant. Iron Pea Squad anti-air knockback is doubled and damage x3. Iron Pea Assault Team damage x3",
    "当前幸运：{0}\n场上敌人数量：{1}": "Current Luck: {0}\nEnemies on the field: {1}",
    "恃强凌弱：场上植物数量为0/1/2/3/4/5/6及以上时，僵尸受到75%/80%/85%/90%/95%/100%/105%伤害": "Bully the Weak: With 0/1/2/3/4/5/6+ plants on the field, zombies take 75%/80%/85%/90%/95%/100%/105% damage",
    "恶贯满盈：黑袍小丑王施加的诅咒量翻倍，且投掷6秒后重新获得诅咒玩偶匣": "Utterly Wicked: Black-robed Jester King applies twice as much Curse and regains its Cursed Doll Box 6 seconds after throwing it",
    "成群结队：僵尸出现时，有概率额外出现一次（领袖和boss除外），概率随关卡波次提高": "Gathering Horde: Zombies have a chance to spawn an extra copy. Excludes mini-bosses and bosses. Chance rises with the wave",
    "战个痛快：刷新间隔缩短，每次刷新僵尸时，有概率立即刷新下一波": "Fight to the Finish: Spawn intervals are shorter, and each zombie spawn has a chance to trigger the next wave immediately",
    "扣": "Subtract",
    "抢你小车：禁用小推车": "Mower Thief: Disable Lawn Mowers",
    "护盾保护": "Shield Protection",
    "护盾保护：持有护盾的植物每秒回复0.1%护盾量的生命值": "Shield Protection: Shielded plants recover HP equal to 0.1% of their Shield each second",
    "持有护盾的植物每秒回复0.1%护盾量的生命值，并立即获得6000护盾": "Shielded plants recover HP equal to 0.1% of their Shield each second and immediately gain 6000 Shield",
    "文件格式异常": "Invalid file format",
    "斗转星移：每一波僵尸刷新时，使你的植物移动到随机位置": "Star Shift: Move your plants to random positions whenever a zombie wave spawns",
    "无理投资：刷新词条时降低25幸运": "Unwise Investment: Lose 25 Luck when rerolling modifiers",
    "无限火力：究极浮空樱桃射手与究极毁灭胆小菇协同攻击时，发射的子弹数会疯狂增长。停止攻击后该增幅会逐渐衰减": "Unlimited Firepower: When Ultimate Floating Cherry Shooter and Ultimate Doom Scaredy-shroom attack together, their projectile count grows rapidly. The bonus gradually fades after they stop attacking",
    "枪枪爆头：铁豆小队的狙击爆头频率的期望提升至5秒1次。铁豆突击队伤害x3": "Headshot Every Time: Iron Pea Squad's expected sniper headshot rate becomes once every 5 seconds. Iron Pea Assault Team damage x3",
    "植物熄火：每一波开始后的前2秒内植物方造成的伤害降低至1点": "Plant Misfire: Plant damage is reduced to 1 during the first 2 seconds of each wave",
    "榜样激励：伤害统计面板排名第一的植物造成85%的原伤害，其他植物造成105%原伤害": "Role Model: The top plant on the Damage Statistics panel deals 85% normal damage; all others deal 105%",
    "正当防卫：僵尸受到伤害时，原地生成一个僵尸方的豌豆子弹，伤害为自身攻击力的10%，最低20，0.02秒内最多触发10次": "Self Defense: When damaged, a zombie creates an enemy Pea projectile at its position for 10% of its Attack, minimum 20. Triggers at most 10 times per 0.02 seconds",
    "步步紧逼：僵尸进化的波数降低至每4波一次": "Relentless Advance: Zombies evolve every 4 waves",
    "死亡行军：机枪黑橄榄僵尸移动时会无视植物": "Death March: Gatling Black Football Zombies ignore plants while moving",
    "每次攻击多掉落一枚钱币": "Each attack drops 1 additional coin",
    "永眠之地：开局场上获得三列墓碑": "Land of Eternal Rest: Begin with 3 columns of graves",
    "沙漠": "Desert",
    "深度创伤：被黑橄榄高坚果僵尸攻击的植物在1秒内受到的伤害x3": "Deep Trauma: Plants hit by Black Football Tall-nut Zombies take 3x damage for 1 second",
    "游戏关闭": "Game Closed",
    "火菜炮的诅咒效果反转了": "Fire Cabbage Cannon's Curse has been reversed",
    "点钻成金：非保底时出现钻石品质时，以对应的黄金品质词条代替": "Diamond to Gold: Outside guaranteed draws, Diamond-quality modifiers are replaced by their Gold versions",
    "炼狱难度需要选择：{0}/5个负面词条": "Purgatory requires selecting {0}/5 negative modifiers",
    "牛哇牛哇": "Amazing",
    "特立独行：僵尸出现时，有概率立即消失，并使随机的一个其他僵尸获得自身80%生命值（对领袖和boss无效），概率随关卡波次提高": "Lone Wolf: A spawned zombie may disappear immediately and grant 80% of its HP to another random zombie. Excludes mini-bosses and bosses. Chance rises with the wave",
    "猫瓜纪元：僵尸出现时，有概率立即消失，并在原地生成一个继承血量的猫瓜僵尸，概率随波次增加": "Cat-Squash Era: A spawned zombie may disappear and be replaced by a Cat-Squash Zombie that inherits its HP. Chance rises with the wave",
    "生化危机：植物消失时，在原地生成一只随机僵尸，该僵尸获得额外的血量加成": "Biohazard: When a plant disappears, spawn a random zombie there with bonus HP",
    "生机翻涌：究极小松炉的精华提供的血量与护盾量翻倍，解冻数量提升至3株，且精华自动储备速度翻倍": "Surging Vitality: Ultimate Little Pine Furnace Essence grants twice the HP and Shield, thaws 3 plants, and stores Essence twice as fast",
    "白银时代：非保底时，具有不同品质的词条只会出现白银品质，若拥有点钻成金，则将金、钻降级为木头": "Silver Age: Outside guaranteed draws, modifiers with multiple qualities appear only as Silver. With Diamond to Gold, Gold and Diamond are reduced to Wooden",
    "的火墙密度+3\n需要重新手动建立火墙": " Fire Wall density +3\nThe Fire Wall must be rebuilt manually",
    "的火墙顶点数加2": " Fire Wall vertex count +2",
    "的诅咒效果已反转": " Curse has been reversed",
    "真实伤害：植物受到伤害后，额外受到30%的真实伤害": "True Damage: After taking damage, plants take an additional 30% as true damage",
    "磁力坚果的基础伤害x3": "Magnet-nut base damage x3",
    "磁力坚果的诅咒效果反转了": "Magnet-nut's Curse has been reversed",
    "祝福-争强好胜：究极樱桃射手每次攻击，额外从屏幕左方发射若干樱桃子弹，攻击力等同于其他植物已造成伤害的0.0001%": "Blessing - Competitive Spirit: Each Ultimate Cherry Shooter attack also fires Cherry projectiles from the left side of the screen. Their Attack equals 0.0001% of damage dealt by other plants",
    "祝福-千锤百炼：磁力坚果每次攻击时，额外发射一颗已吸引子弹中数量最多的类型的子弹": "Blessing - Tempered a Thousand Times: Each Magnet-nut attack also fires 1 projectile of the most frequently absorbed type",
    "祝福-壹肆叁柒：究极杨桃大帝发射的多功能子弹额外获得1437点基础伤害": "Blessing - 1437: Ultimate Starfruit Emperor's multifunction projectiles gain 1437 base damage",
    "祝福-见者有份：究极火菜炮每有一个目标，发射的子弹伤害增加1%": "Blessing - Share the Wealth: Ultimate Fire Cabbage Cannon projectile damage increases by 1% per target",
    "神魂不稳：植物复活时间延长50%": "Unstable Spirit: Plant revival time +50%",
    "积重难返：植物每次复活，下一次复活时间增加0.5秒": "Lingering Burden: Each plant revival adds 0.5 seconds to its next revival",
    "秽土转生：僵尸死亡后有概率从本行最右侧复活为其他僵尸（对领袖和boss无效），概率随波次增加": "Reanimation: A dead zombie may revive as a different zombie at the far right of its lane. Excludes mini-bosses and bosses. Chance rises with the wave",
    "第一轮回强化：第一轮回的僵尸血量提高20%，速度提高20%": "First Reincarnation: Zombie HP +20% and speed +20%",
    "第二轮回强化：第二轮回的僵尸血量提高40%，速度提高25%": "Second Reincarnation: Zombie HP +40% and speed +25%",
    "第三轮回强化：第三轮回的僵尸血量提高60%，速度提高30%": "Third Reincarnation: Zombie HP +60% and speed +30%",
    "粉丝团灯牌": "Fan Club Sign",
    "紧追不放：碾压类僵尸的碾压被抵抗时，受到的强制击退量减半": "Close Pursuit: When a crusher zombie's crush is resisted, its forced knockback is halved",
    "老当益壮：关卡波次增加时，有概率出现一些特别的读报僵尸，概率随波次提高": "Still Going Strong: Special Newspaper Zombies may appear, with chance rising by wave",
    "腐朽之息：每3秒为全场植物施加5%最大生命值的诅咒": "Breath of Decay: Apply Curse equal to 5% max HP to all plants every 3 seconds",
    "膨胀危机：非boss僵尸的生命值和体型提高60%，但速度降低50%": "Expansion Crisis: Non-boss zombies gain 60% HP and size but lose 50% speed",
    "自选词条": "Choose Modifier",
    "舞影重重：关卡波次增加时，有概率出现一些特别的舞王僵尸，概率随波次提高": "Dancing Shadows: Special Dancing Zombies may appear, with chance rising by wave",
    "英雄退场：每一波僵尸刷新时，词条数拿的最多的植物降低1%独立伤害增幅，最低为0": "Hero's Exit: Each wave, the plant with the most modifiers loses 1% independent damage bonus, to a minimum of 0",
    "荆枝易折：植物方受到的伤害x1.5": "Brittle Branches: Plants take 1.5x damage",
    "获得一个神秘大炮": "Gain a Mystery Cannon",
    "获得了{0:F0}%力量增幅": "Gained {0:F0}% power bonus",
    "获得了{0:F0}%速度增幅": "Gained {0:F0}% speed bonus",
    "诅咒-争强好胜：究极樱桃射手发射的子弹伤害降低50%，累计造成3亿伤害后反转诅咒\n反转效果：究极樱桃射手每次攻击，额外从屏幕左方发射若干樱桃子弹，攻击力等同于其他植物已造成伤害的0.0001%": (
        "Curse - Competitive Spirit: Ultimate Cherry Shooter projectile damage -50%. "
        "Deal 300M cumulative damage to reverse the Curse\n"
        "Reversed: Each Ultimate Cherry Shooter attack also fires Cherry projectiles "
        "from the left side of the screen. Their Attack equals 0.0001% of damage dealt "
        "by other plants"
    ),
    "诅咒-千锤百炼：磁力坚果不再发射子弹，累计吸引5000发子弹后反转诅咒\n反转效果：每次攻击时，额外发射一颗已吸引子弹中数量最多的类型的子弹": "Curse - Tempered a Thousand Times: Magnet-nut no longer fires. Absorb 5000 projectiles to reverse the Curse\nReversed: Each attack also fires 1 projectile of the most frequently absorbed type",
    "诅咒-壹肆叁柒：究极杨桃大帝的攻击间隔翻倍，在攻击1437次后反转诅咒，每轮攻击计入5次\n反转效果：发射的多功能子弹额外获得1437点基础伤害": "Curse - 1437: Ultimate Starfruit Emperor's attack interval is doubled. Reverse the Curse after 1437 attacks; each volley counts as 5\nReversed: Multifunction projectiles gain 1437 base damage",
    "诅咒-见者有份：究极火菜炮每有一个目标，发射的子弹伤害降低1%，最低降低为原来的30%，累计通过此方式降低50000%后反转诅咒\n反转效果：究极火菜炮每有一个目标，发射的子弹伤害增加1%": "Curse - Share the Wealth: Ultimate Fire Cabbage Cannon projectile damage drops 1% per target, to a minimum of 30%. Reverse the Curse after 50000% total reduction\nReversed: Projectile damage increases 1% per target",
    "诅咒任务：{0}\n": "Curse Trial: {0}\n",
    "诅咒：争强好胜": "Curse: Competitive Spirit",
    "诅咒：千锤百炼": "Curse: Tempered a Thousand Times",
    "诅咒：壹肆叁柒": "Curse: 1437",
    "诅咒：见者有份": "Curse: Share the Wealth",
    "试炼：": "Trial: ",
    "请在文件OpenBLive中填写数据": "Enter the required data in the OpenBLive file",
    "诸神进化：无尽，第{0}轮": "The Gods: Evolved - Endless, Round {0}",
    "诸神进化：炼狱": "The Gods: Evolved - Purgatory",
    "质变-万剑归宗：究极剑仙杨桃每有2发大剑，每次攻击额外发射1发旋转小剑": (
        "Ascend: Myriad Blades: For every 2 greatswords held by Ultimate Swordmaster "
        "Starfruit, each attack also fires 1 rotating small sword"
    ),
    "质变-人人有份：金瓜大招额外给全场僵尸发射西瓜，且大招分裂数x2": "Ascension - Share the Wealth: Golden Melon's skill also fires Melons at every zombie and doubles the skill's split count",
    "质变-固甲摧锋：究极云杉发射的子弹额外附带当前护盾量0.6%的攻击力，最高不超过基础攻击力的300%": "Ascension - Armorbreaker: Ultimate Spruce projectiles gain Attack equal to 0.6% of current Shield, capped at 300% of base Attack",
    "质变-拿来吧你：普通攻击叠加解读的概率翻倍。敌方目标进入战斗时，魔法寒冰射手对其施加3层“解读”。每一波开始时，对全场血量最高的僵尸施加100层“解读”，每层解读额外使本次伤害提高100%，僵尸死亡后，将剩余解读层数传递给其他僵尸": "Ascension - Hand It Over: Double the chance for normal attacks to apply Interpretation. Magic Snow Pea applies 3 stacks when an enemy enters battle. At each wave, apply 100 stacks to the highest-HP zombie. Each stack adds 100% damage to that hit; remaining stacks transfer when the zombie dies",
    "质变-杀戮光环：磁力坚果发射的子弹可无限穿透，但存在时间降低为10秒": "Ascension - Killing Aura: Magnet-nut projectiles pierce infinitely but last only 10 seconds",
    "质变-谁劈了我的瓜：西瓜坚果发射的西瓜飞到最高点时会瞬间炸开，并分裂成若干个小西瓜扔向全场僵尸": "Ascension - Who Split My Melon?: Melons fired by Melon-nut burst at their highest point and split into small Melons thrown at zombies across the field",
    "质变-饱和弹射：火菜炮索敌范围上下额外拓展1行，同时向所有目标发射子弹。若索敌目标数小于最大散射数，将剩余弹药平均分配给索敌目标。子弹飞行时间降低50%": "Ascension - Saturation Ricochet: Fire Cabbage Cannon targets 1 extra lane above and below and fires at every target. If there are fewer targets than the maximum spread count, remaining shots are distributed evenly. Projectile flight time -50%",
    "质变： *10k": "Ascension: *10k",
    "超新星爆发：究极流光射手可以为任意行的究极路灯花输送光能。后者光能较高时进入超频攻击状态并逐渐变亮，达到极限后在耀眼的光芒中爆发，对全场僵尸造成毁灭性打击": "Supernova: Ultimate Radiant Shooter can send Light Energy to an Ultimate Plantern in any lane. At high energy it enters an overclocked attack state and grows brighter, then erupts at the limit and devastates every zombie",
    "超质变：神秘大炮": "Super Ascension: Mystery Cannon",
    "距离其他究极小松炉太近": "Too close to another Ultimate Little Pine Furnace",
    "进化：究极": "Evolution: Ultimate",
    "连接失败": "Connection Failed",
    "连接成功": "Connected",
    "速度x{0:F2}": "Speed x{0:F2}",
    "铁蹄荡川：黑橄榄骑兵僵尸冲锋结束时，施加诅咒的范围扩大至3×3": "Iron Hooves: When Black Football Cavalry Zombie finishes charging, its Curse area expands to 3x3",
    "闪电突袭：每一波刷新僵尸后，随机3只僵尸获得100%独立速度增幅": "Lightning Assault: After each wave spawns, 3 random zombies gain 100% independent speed",
    "随从号令：每一波僵尸刷新时，令全场僵尸提高20%生命值和20%速度": "Minion's Order: Each wave grants all zombies 20% HP and 20% speed",
    "飞来横祸：关卡波次增加时，有概率出现一些特别的蹦极僵尸，概率随波次提高": "Disaster from Above: Special Bungee Zombies may appear, with chance rising by wave",
    "首领号令：boss僵尸获得30%血量加成，其召唤的僵尸获得60%血量加成": "Boss's Order: Boss zombies gain 30% HP; zombies they summon gain 60% HP",
    "高贵审美：木头、白银词条加成变为原来的70%，黄金，钻石词条加成变为原来的110%": "Refined Taste: Wooden and Silver modifier bonuses become 70% of normal; Gold and Diamond bonuses become 110%",
    "鱼丸护体：立即获得3个超级机械保龄球卡牌，该植物拥有64万初始血量": (
        "Giga Guardian: Immediately gain 3 Giga Mecha-nut seed packets. "
        "This plant starts with 640K HP"
    ),
})

# Only platform-specific semantic/layout fixes override PC data. All other
# Codex/screenshot-confirmed mappings are fallbacks and automatically yield to
# a current PC community exact translation when one appears.
ANDROID_REQUIRED_OVERRIDE_SOURCES = {
    "简单模式", "普通模式", "正常模式", "困难模式", "极难模式", "你确定？",
    "禁用转场动画",
    "生命值：{0}/{1}\n", "攻击力：{0}\n",
    "生产间隔：{0}秒\n", "光照等级：{0}\n",
    "奖励1：<color=black>", "奖励1：<color=white>",
    "奖励2：<color=black>", "奖励2：<color=white>",
    "一起摇滚吧！", "超级肥料", "\n版本：", "\n当前版本：",
}


# These 3.9-only modifier titles are not present in the older PC travel-buff
# dump. They still use Android's combined `title：description` runtime format,
# so they must pass through the same final parser as PC-sourced modifiers.
ANDROID_39_MODIFIER_TITLES = {
    "不破不立", "两极分化", "枪枪爆头", "开炮", "尸愁之路II", "无限火力",
    "超新星爆发", "元素反应", "荆狂诅咒", "鱼丸护体", "厚积薄发", "打折券",
    "伤情恶化", "深度创伤", "适应之力", "随从强化", "领袖强化", "霸凌弱者",
    "斗转星移", "倒反天罡", "傲慢", "冷冻冬眠", "匣中惊喜",
    "卧薪尝胆", "危机四伏", "同步治疗", "命运无常", "坚毅灵光", "大变活尸",
    "嫉妒", "小丑派对", "小鬼当家", "尸稠之路", "帅令加身", "廉价审美",
    "恃强凌弱", "恶贯满盈", "成群结队", "战个痛快", "抢你小车", "护盾保护",
    "无理投资", "植物熄火", "榜样激励", "正当防卫", "步步紧逼", "死亡行军",
    "永眠之地", "点钻成金", "特立独行", "猫瓜纪元", "生化危机", "生机翻涌",
    "白银时代", "真实伤害", "神魂不稳", "积重难返", "秽土转生",
    "第一轮回强化", "第二轮回强化", "第三轮回强化", "紧追不放", "老当益壮",
    "腐朽之息", "膨胀危机", "舞影重重", "英雄退场", "荆枝易折", "铁蹄荡川",
    "闪电突袭", "随从号令", "飞来横祸", "首领号令", "高贵审美",
}

# Titles for revised Android 3.9 modifier bodies. Prefer the dedicated PC
# travel-buff names when they exist, then use these reviewed mobile fallbacks.
# Keeping this separate from the descriptions lets body revisions continue to
# inherit stable PC terminology without relying on a whole-string match.
ANDROID_39_MODIFIER_TITLE_TRANSLATIONS = {
    "鱼丸护体": "Giga Guardian",
    "祝福-争强好胜": "Blessing - Competitive Spirit",
    "祝福-千锤百炼": "Blessing - Tempered a Thousand Times",
    "祝福-壹肆叁柒": "Blessing - 1437",
    "祝福-见者有份": "Blessing - Share the Wealth",
    "诅咒-争强好胜": "Curse - Competitive Spirit",
    "诅咒-千锤百炼": "Curse - Tempered a Thousand Times",
    "诅咒-壹肆叁柒": "Curse - 1437",
    "诅咒-见者有份": "Curse - Share the Wealth",
    "质变-万剑归宗": "Ascend: Myriad Blades",
    "质变-人人有份": "Ascend: Share the Wealth",
    "质变-固甲摧锋": "Ascend: Armorbreaker",
    "质变-拿来吧你": "Ascend: Decryption",
    "质变-杀戮光环": "Ascend: Killing Aura",
    "质变-谁劈了我的瓜": "Ascend: Who Split My Melon?",
    "质变-饱和弹射": "Ascend: Saturation Ricochet",
}

MODIFIER_CATEGORY_PREFIXES = ("祝福-", "诅咒-", "质变-")
SP_EVOLUTION_SOURCE_TITLE = "【SP进化】"
SP_EVOLUTION_TRANSLATED_TITLE = "[SP Evolution]"


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


def translate_validated_enum_fields(
    base: bytes,
    fields: dict[int, tuple[str, str]],
    label: str,
) -> tuple[bytes, list[dict[str, object]]]:
    """Rename validated display-facing enum fields without changing their values."""
    layout = parse_definition_layout(base)
    field_count = layout.field_size // 12
    output = bytearray(base)
    new_heap = bytearray(base[layout.string_offset : layout.string_offset + layout.string_size])
    changes: list[dict[str, object]] = []

    for field_index, (expected_source, translated) in fields.items():
        if field_index >= field_count:
            raise RuntimeError(
                f"{label} enum field {field_index} is outside the {field_count}-field table"
            )
        record_offset = layout.field_offset + field_index * 12
        original_name_offset = struct.unpack_from("<I", base, record_offset)[0]
        original_name = read_definition_string(base, layout, original_name_offset)
        if original_name != expected_source:
            raise RuntimeError(
                f"{label} enum validation failed at field {field_index}: "
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
                "numeric_value_unchanged": True,
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
                f"{label} enum round-trip validation failed at field {change['field_index']}"
            )
    return bytes(output), changes


def resolve_contiguous_enum_fields(
    data: bytes,
    expected_fields: dict[int, tuple[str, str]],
    label: str,
) -> dict[int, tuple[str, str]]:
    """Resolve a display enum by its complete ordered member-name sequence.

    The numeric keys in ``expected_fields`` document the original 3.8.1
    positions, but are not trusted for a different game build. Requiring one
    unique contiguous sequence avoids accidentally renaming an unrelated field
    that happens to share a short Chinese display name.
    """
    layout = parse_definition_layout(data)
    field_count = layout.field_size // 12
    ordered = list(expected_fields.values())
    expected_names = [source for source, _translated in ordered]
    field_names = []
    for field_index in range(field_count):
        record_offset = layout.field_offset + field_index * 12
        name_offset = struct.unpack_from("<I", data, record_offset)[0]
        field_names.append(read_definition_string(data, layout, name_offset))

    starts = [
        start
        for start in range(field_count - len(expected_names) + 1)
        if field_names[start : start + len(expected_names)] == expected_names
    ]
    if len(starts) != 1:
        raise RuntimeError(
            f"{label} enum sequence resolution found {len(starts)} matches; "
            f"expected exactly one"
        )
    start = starts[0]
    return {
        start + offset: entry
        for offset, entry in enumerate(ordered)
    }


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


def clean_modifier_source_title(source: str) -> str:
    """Return the unformatted Chinese title before the runtime delimiter."""
    title = re.split(r"[:：]", source, maxsplit=1)[0]
    return re.sub(r"<[^>]+>", "", title).strip()


def load_modifier_sources(
    strings_dir: Path,
) -> tuple[set[str], dict[str, str], dict[str, str], dict[str, list[str]]]:
    """Return modifier sources plus source-title and exact-record title maps."""
    sources: set[str] = set()
    title_translations: dict[str, str] = {}
    exact_title_translations: dict[str, str] = {}
    ambiguous_title_translations: dict[str, set[str]] = {}
    source_path = strings_dir.parents[2] / "Dumps" / "travel_buffs.json"
    translated_path = strings_dir / "travel_buffs.json"
    if not source_path.exists():
        raise FileNotFoundError(f"missing travel modifier source dump: {source_path}")
    if not translated_path.exists():
        raise FileNotFoundError(f"missing travel modifier translation: {translated_path}")
    source_payload = read_json(source_path)
    translated_payload = read_json(translated_path)
    for section, records in source_payload.items():
        if section == "investmentBuffs" or not isinstance(records, dict):
            continue
        translated_records = translated_payload.get(section, {})
        for record_id, record in records.items():
            if not isinstance(record, dict):
                continue
            description = record.get("desc")
            translated_record = translated_records.get(record_id, {})
            if isinstance(description, str) and ("：" in description or ":" in description):
                sources.add(description)
                translated_name = translated_record.get("name")
                if isinstance(translated_name, str) and translated_name:
                    source_title = clean_modifier_source_title(description)
                    prior_title = title_translations.get(source_title)
                    if prior_title is not None and prior_title != translated_name:
                        ambiguous_title_translations.setdefault(
                            source_title, {prior_title}
                        ).add(translated_name)
                        title_translations.pop(source_title, None)
                    elif source_title not in ambiguous_title_translations:
                        title_translations[source_title] = translated_name
                    exact_title_translations[description] = translated_name

    # Android 3.9 revises some bodies without updating the PC source dump.
    # Accept those exact fallbacks only when their parsed title agrees with the
    # PC record, or when the title is a reviewed 3.9-only modifier title.
    for source, target in ANDROID_CONFIRMED_EXACT.items():
        if "：" not in source or ": " not in target:
            continue
        source_title = source.split("：", 1)[0]
        translated_title = target.split(": ", 1)[0]
        if (
            title_translations.get(source_title) == translated_title
            or source_title in ANDROID_39_MODIFIER_TITLES
            or source_title.startswith("祝福-")
            or source_title.startswith("诅咒-")
            or source_title.startswith("质变-")
        ):
            sources.add(source)
    for source_title, translated_title in ANDROID_39_MODIFIER_TITLE_TRANSLATIONS.items():
        if source_title not in ambiguous_title_translations:
            title_translations.setdefault(source_title, translated_title)
    title_translations[SP_EVOLUTION_SOURCE_TITLE] = SP_EVOLUTION_TRANSLATED_TITLE
    for source in sources:
        source_title = clean_modifier_source_title(source)
        if source_title in title_translations:
            exact_title_translations.setdefault(source, title_translations[source_title])
    return (
        sources,
        title_translations,
        exact_title_translations,
        {
            source_title: sorted(translated_titles)
            for source_title, translated_titles in sorted(
                ambiguous_title_translations.items()
            )
        },
    )


def modifier_source_reason(source: str, exact_sources: set[str]) -> str | None:
    """Classify combined modifier strings without matching unrelated task text."""
    if source in exact_sources:
        return "exact_pc_or_reviewed_source"
    if "：" not in source and ":" not in source:
        return None
    source_title = clean_modifier_source_title(source)
    if source_title == SP_EVOLUTION_SOURCE_TITLE:
        return "sp_evolution"
    if source_title.startswith(MODIFIER_CATEGORY_PREFIXES):
        return "category_prefix"
    if source_title in ANDROID_39_MODIFIER_TITLES:
        return "reviewed_android_title"
    return None


def normalize_modifier_translation(
    translated: str,
    preferred_title: str | None = None,
) -> tuple[str, bool]:
    """Preserve the runtime delimiter while putting the body on its own line."""
    delimiter_index = translated.find("：")
    delimiter_length = 1
    if delimiter_index < 0:
        delimiter_index = translated.find(":")
    if delimiter_index < 0:
        raise ValueError(f"modifier translation has no title delimiter: {translated!r}")
    title = translated[:delimiter_index]
    body = translated[delimiter_index + delimiter_length:]
    title = re.sub(r"</?(?:nobr|size)(?:=[^>]+)?>", "", title.strip())
    title = re.sub(r"<[^>]+>", "", title).strip()
    if preferred_title:
        title = preferred_title.strip().rstrip(":：").strip()
    body = body.lstrip("\r\n ")
    title_variants = {title}
    for separator in (": ", " - "):
        if separator in title:
            title_variants.add(title.rsplit(separator, 1)[-1].strip())
    for title_variant in sorted(title_variants, key=len, reverse=True):
        redundant_heading = re.match(
            rf"^{re.escape(title_variant)}\s*[:：]\s*",
            body,
            flags=re.IGNORECASE,
        )
        if redundant_heading is not None:
            body = body[redundant_heading.end():].lstrip("\r\n ")
            break
    if not title or not body:
        raise ValueError(f"modifier translation has an empty title or body: {translated!r}")
    shrink_title = len(title) > 24
    title_markup = f"<nobr>{title}</nobr>"
    if shrink_title:
        title_markup = f"<size=80%>{title_markup}</size>"
    return f"{title_markup}：\n{body}", shrink_title


def load_pc_translations(
    strings_dir: Path,
) -> tuple[
    dict[str, str],
    set[str],
    list[tuple[str, str, re.Pattern[str], str]],
    dict[str, int],
]:
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

    # Capture provenance before Android-specific overrides and fallbacks are
    # merged. New 3.9 content may use current PC English only; this set lets
    # the final selection policy distinguish community translations from
    # older Android or hand-written fallback text.
    pc_exact_sources = set(exact)

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

    return exact, pc_exact_sources, regex_entries, counts


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


def observed_translations_report(
    label: str, report_path: Path
) -> tuple[dict[str, str], dict[str, object]]:
    """Load previously validated exact Android mappings from a build report.

    This is the safe migration path when the original aligned APK pair is not
    available locally.  A mapping is accepted only when the old report records
    a Chinese source, a non-empty non-Chinese translation, and one unambiguous
    translation for that exact source string.
    """
    payload = read_json(report_path)
    if not isinstance(payload, dict) or not isinstance(payload.get("changes"), list):
        raise ValueError(f"reference report {label!r} has no changes list: {report_path}")

    choices: dict[str, set[str]] = {}
    accepted_occurrences = 0
    for change in payload["changes"]:
        if not isinstance(change, dict):
            continue
        source = change.get("source")
        target = change.get("translation")
        if (
            not isinstance(source, str)
            or not isinstance(target, str)
            or not target
            or not CJK_RE.search(source)
            or CJK_RE.search(target)
            or source == target
        ):
            continue
        choices.setdefault(source, set()).add(target)
        accepted_occurrences += 1

    conflicts = {source: values for source, values in choices.items() if len(values) != 1}
    mapping = {
        source: next(iter(values))
        for source, values in choices.items()
        if len(values) == 1
    }
    stats = {
        "label": label,
        "report": str(report_path.resolve()),
        "accepted_occurrences": accepted_occurrences,
        "unique_mappings": len(mapping),
        "conflicts": len(conflicts),
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


def translate_csharp_template_with_pc_regex(
    text: str,
    regex_entries: list[tuple[str, str, re.Pattern[str], str]],
) -> str | None:
    """Bridge PC runtime regexes to Android's compiled C# format strings.

    The PC translator sees the final rendered text, such as
    ``保存成功，编号：0``, while IL2CPP metadata contains the pre-rendered
    template ``保存成功，编号：{0}``.  Substitute unique numeric sentinels,
    require a whole-string PC regex match, render the community translation,
    and then restore the original C# placeholders (including format specifiers
    such as ``:F0`` and ``:D2``).

    Only a single unambiguous, fully English result is accepted.  Partial
    matches are deliberately rejected so a small regex such as ``第(\\d+)页``
    cannot discard the rest of a longer Android diagnostic or UI message.
    """

    fields = list(CSHARP_FORMAT_FIELD_RE.finditer(text))
    if not fields:
        return None

    original_fields: dict[int, str] = {}
    sentinels: dict[int, str] = {}
    for field in fields:
        index = int(field.group(1))
        original = field.group(0)
        previous = original_fields.get(index)
        if previous is not None and previous != original:
            # One argument rendered with different format specifiers cannot be
            # restored safely after a regex has rearranged its capture groups.
            return None
        original_fields[index] = original
        sentinels[index] = f"927401{index:03d}683"

    sample = CSHARP_FORMAT_FIELD_RE.sub(
        lambda match: sentinels[int(match.group(1))], text
    )
    candidates: set[str] = set()
    for _pattern, template, compiled, anchor in regex_entries:
        if anchor and anchor not in sample:
            continue
        match = compiled.search(sample)
        if match is None or match.span() != (0, len(sample)):
            continue
        rendered = csharp_format(template, match.groups())
        for index, sentinel in sentinels.items():
            rendered = rendered.replace(sentinel, original_fields[index])
        if rendered != text and not CJK_RE.search(rendered):
            candidates.add(rendered)

    if len(candidates) == 1:
        return candidates.pop()
    return None


def translate_literal(
    text: str,
    exact: dict[str, str],
    pc_exact_sources: set[str],
    observed: dict[str, tuple[str, str]],
    regex_entries: list[tuple[str, str, re.Pattern[str], str]],
) -> tuple[str, str | None]:
    def resolve_chain(value: str) -> str:
        """Resolve exact/reference outputs that are themselves source keys.

        PC regex rules sometimes normalize an Android string into a second,
        mixed-language source key. Keep resolving while CJK remains so the
        final exact community translation is not stranded halfway through.
        """
        seen = {value}
        for _ in range(8):
            if not CJK_RE.search(value):
                break
            if value in exact:
                next_value = exact[value]
            elif value in observed:
                next_value = observed[value][0]
            else:
                break
            if next_value == value or next_value in seen:
                break
            value = next_value
            seen.add(value)
        return value

    if not CJK_RE.search(text):
        return text, None
    if text in exact:
        method = (
            "pc_exact"
            if text in pc_exact_sources and text not in ANDROID_REQUIRED_OVERRIDE_SOURCES
            else "android_confirmed_exact"
        )
        return resolve_chain(exact[text]), method
    if text in observed:
        translated, label = observed[text]
        return resolve_chain(translated), f"reference:{label}"

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
        # A broad PC regex can legitimately produce another PC source key.
        # Example: 手推车挑战 becomes the intermediate mixed-language text
        # "Fusion Challenge: 手推车", for which the community project has a
        # more specific exact translation. Resolve that second stage before
        # accepting the regex output.
        result = resolve_chain(result)
        if result != text:
            return result, "pc_regex"

    template_result = translate_csharp_template_with_pc_regex(text, regex_entries)
    if template_result is not None:
        template_result = resolve_chain(template_result)
        return template_result, "pc_regex_csharp_template"
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
    parser.add_argument(
        "--previous-version-base",
        type=Path,
        help=(
            "clean metadata from the preceding official release; when supplied, "
            "Chinese literals absent from it are treated as new content and may "
            "use current PC English only"
        ),
    )
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
    parser.add_argument(
        "--reference-report",
        action="append",
        nargs=2,
        metavar=("LABEL", "METADATA_REPORT"),
        default=[],
        help=(
            "fallback exact mappings from a previously validated metadata build report; "
            "order sets priority after current PC/community translations"
        ),
    )
    args = parser.parse_args()

    base = args.base.read_bytes()
    layout, literals = parse_metadata(base)
    exact, pc_exact_sources, regex_entries, pc_counts = load_pc_translations(args.strings_dir)
    previous_base = None
    previous_literals: list[MetadataLiteral] = []
    previous_literal_texts: set[str] = set()
    if args.previous_version_base is not None:
        previous_base = args.previous_version_base.read_bytes()
        _, previous_literals = parse_metadata(previous_base)
        previous_literal_texts = {literal.text for literal in previous_literals}
    (
        modifier_sources,
        modifier_title_translations,
        modifier_exact_title_translations,
        modifier_ambiguous_title_translations,
    ) = load_modifier_sources(args.strings_dir)

    observed: dict[str, tuple[str, str]] = {}
    reference_stats: list[dict[str, object]] = []
    reference_conflicts: list[dict[str, str]] = []
    for label, report_name in args.reference_report:
        mapping, stats = observed_translations_report(label, Path(report_name))
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
    modifier_records: list[dict[str, object]] = []
    final_methods: list[str | None] = []
    new_39_audit: dict[str, dict[str, object]] = {}
    new_39_occurrences = 0
    new_39_pc_translated_occurrences = 0
    new_39_preserved_occurrences = 0
    preserved_new_39_indexes: set[int] = set()
    cjk_before = 0
    cjk_after = 0
    for index, literal in enumerate(literals):
        if CJK_RE.search(literal.text):
            cjk_before += 1
        translated_text, method = translate_literal(
            literal.text,
            exact,
            pc_exact_sources,
            observed,
            regex_entries,
        )
        is_new_39 = (
            args.previous_version_base is not None
            and CJK_RE.search(literal.text) is not None
            and literal.text not in previous_literal_texts
        )
        preserved_new_39 = False
        if is_new_39:
            new_39_occurrences += 1
            pc_authoritative = (
                method is not None
                and method.startswith("pc_")
                and CJK_RE.search(translated_text) is None
            )
            if pc_authoritative:
                new_39_pc_translated_occurrences += 1
                outcome = "pc_english"
            else:
                translated_text = literal.text
                method = "preserved_new_39_chinese"
                preserved_new_39 = True
                preserved_new_39_indexes.add(index)
                new_39_preserved_occurrences += 1
                outcome = "preserved_official_chinese"

            audit_record = new_39_audit.setdefault(
                literal.text,
                {
                    "source": literal.text,
                    "outcome": outcome,
                    "method": method,
                    "translation": translated_text,
                    "occurrences": 0,
                },
            )
            audit_record["occurrences"] = int(audit_record["occurrences"]) + 1
        modifier_reason = modifier_source_reason(literal.text, modifier_sources)
        if modifier_reason is not None and not (
            "：" in translated_text or ":" in translated_text
        ):
            modifier_reason = None
        if modifier_reason is not None and preserved_new_39:
            modifier_records.append(
                {
                    "index": index,
                    "source": literal.text,
                    "source_title": clean_modifier_source_title(literal.text),
                    "match_reason": modifier_reason,
                    "preferred_title": None,
                    "before": literal.text,
                    "translation": literal.text,
                    "title_shrunk": False,
                    "changed_by_final_parser": False,
                    "preserved_new_39_chinese": True,
                }
            )
        elif modifier_reason is not None:
            before_normalization = translated_text
            source_title = clean_modifier_source_title(literal.text)
            preferred_title = modifier_exact_title_translations.get(
                literal.text,
                modifier_title_translations.get(source_title),
            )
            translated_text, title_shrunk = normalize_modifier_translation(
                translated_text,
                preferred_title,
            )
            modifier_records.append(
                {
                    "index": index,
                    "source": literal.text,
                    "source_title": source_title,
                    "match_reason": modifier_reason,
                    "preferred_title": preferred_title,
                    "before": before_normalization,
                    "translation": translated_text,
                    "title_shrunk": title_shrunk,
                    "changed_by_final_parser": translated_text != before_normalization,
                    "preserved_new_39_chinese": False,
                }
            )
        translated_text = translated_text.replace("\u2014", "-")
        final_methods.append(method)
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

    synergy_fields = resolve_contiguous_enum_fields(
        base,
        ANDROID_381_SYNERGY_ENUM_FIELDS,
        "Android affinity display",
    )
    invest_fields = resolve_contiguous_enum_fields(
        base,
        ANDROID_381_INVEST_ENUM_FIELDS,
        "Android Investment display",
    )
    definition_patched_base, display_enum_changes = translate_validated_enum_fields(
        base,
        {**synergy_fields, **invest_fields},
        "Android display",
    )
    synergy_enum_changes = [
        change for change in display_enum_changes
        if int(change["field_index"]) in synergy_fields
    ]
    invest_enum_changes = [
        change for change in display_enum_changes
        if int(change["field_index"]) in invest_fields
    ]
    output = build_metadata(definition_patched_base, layout, translated_bytes)
    output_layout, output_literals = parse_metadata(output)
    if [item.raw for item in output_literals] != translated_bytes:
        raise RuntimeError("self-validation failed: output literals do not match generated data")
    pc_exact_remnants = [
        {"index": index, "source": item.text, "expected": exact[item.text]}
        for index, item in enumerate(output_literals)
        if CJK_RE.search(item.text)
        and item.text in pc_exact_sources
        and exact[item.text] != item.text
        and index not in preserved_new_39_indexes
    ]
    if pc_exact_remnants:
        preview = json.dumps(pc_exact_remnants[:10], ensure_ascii=False)
        raise RuntimeError(
            "self-validation failed: translated output still contains PC exact source keys: "
            f"{preview}"
        )

    escaped_category_modifiers = [
        {"index": index, "source": literal.text}
        for index, literal in enumerate(literals)
        if clean_modifier_source_title(literal.text).startswith(MODIFIER_CATEGORY_PREFIXES)
        and not any(record["index"] == index for record in modifier_records)
    ]
    if escaped_category_modifiers:
        preview = json.dumps(escaped_category_modifiers[:10], ensure_ascii=False)
        raise RuntimeError(
            "self-validation failed: categorized modifiers escaped final parsing: "
            f"{preview}"
        )

    malformed_modifier_outputs: list[dict[str, object]] = []
    placeholder_re = re.compile(
        r"(?:description[_ -]?missing|translation[_ -]?missing|missing[_ -]?description|"
        r"\b(?:todo|tbd)\b|^\?+$)",
        re.IGNORECASE,
    )
    for record in modifier_records:
        if bool(record.get("preserved_new_39_chinese")):
            if record["translation"] != record["source"]:
                malformed_modifier_outputs.append(record)
            continue
        translated = str(record["translation"])
        parts = translated.split("：\n", 1)
        if len(parts) != 2:
            malformed_modifier_outputs.append(record)
            continue
        plain_title = re.sub(r"<[^>]+>", "", parts[0]).strip()
        body = parts[1].lstrip()
        title_variants = {plain_title}
        for separator in (": ", " - "):
            if separator in plain_title:
                title_variants.add(plain_title.rsplit(separator, 1)[-1].strip())
        preferred_title = record.get("preferred_title")
        if (
            not plain_title
            or not body
            or (
                isinstance(preferred_title, str)
                and preferred_title.strip().rstrip(":：").strip() != plain_title
            )
            or placeholder_re.search(plain_title) is not None
            or placeholder_re.search(body) is not None
            or any(
                re.match(
                    rf"^{re.escape(title_variant)}\s*[:：]",
                    body,
                    flags=re.IGNORECASE,
                )
                for title_variant in title_variants
            )
            or re.match(r"^.{1,24}\?*\s*:\s*(?:\n|$)", body)
        ):
            malformed_modifier_outputs.append(record)
    if malformed_modifier_outputs:
        preview = json.dumps(malformed_modifier_outputs[:10], ensure_ascii=False)
        raise RuntimeError(
            "self-validation failed: modifier title text leaked into a description: "
            f"{preview}"
        )

    recognized_modifier_indexes = {int(record["index"]) for record in modifier_records}
    missing_structured_modifier_records = [
        {"index": index, "source": literal.text}
        for index, literal in enumerate(literals)
        if literal.text in modifier_sources and index not in recognized_modifier_indexes
    ]
    if missing_structured_modifier_records:
        preview = json.dumps(missing_structured_modifier_records[:10], ensure_ascii=False)
        raise RuntimeError(
            "self-validation failed: structured PC modifier records escaped normalization: "
            f"{preview}"
        )

    sp_evolution_records = [
        {
            "index": index,
            "source": literals[index].text,
            "translation": output_literals[index].text,
            "method": final_methods[index],
            "new_39": literals[index].text not in previous_literal_texts
            if args.previous_version_base is not None
            else None,
        }
        for index in range(len(literals))
        if "【SP进化】" in literals[index].text
    ]
    if len(sp_evolution_records) != 4 or any(
        (
            record["new_39"] is True
            and record["translation"] != record["source"]
            and not (
                isinstance(record["method"], str)
                and str(record["method"]).startswith("pc_")
                and CJK_RE.search(str(record["translation"])) is None
            )
        )
        for record in sp_evolution_records
    ):
        raise RuntimeError(
            "self-validation failed: a new SP Evolution recipe did not follow PC-or-Chinese policy"
        )

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
        "pc_exact_source_remnants": 0,
        "new_39_translation_policy": {
            "enabled": args.previous_version_base is not None,
            "rule": (
                "Use current PC English for content introduced in 3.9; otherwise preserve "
                "the official Chinese literal"
            ),
            "previous_version_base": None
            if args.previous_version_base is None
            else {
                "path": str(args.previous_version_base.resolve()),
                "size": len(previous_base or b""),
                "sha256": sha256(previous_base or b""),
                "literal_count": len(previous_literals),
                "unique_literal_count": len(previous_literal_texts),
            },
            "new_cjk_literal_occurrences": new_39_occurrences,
            "pc_english_occurrences": new_39_pc_translated_occurrences,
            "preserved_official_chinese_occurrences": new_39_preserved_occurrences,
            "unique_records": sorted(
                new_39_audit.values(),
                key=lambda record: str(record["source"]),
            ),
        },
        "android_affinity_enum": {
            "strategy": "validated field-name rename; enum values and all IL2CPP code unchanged",
            "changed_field_count": len(synergy_enum_changes),
            "changes": synergy_enum_changes,
        },
        "android_investment_enum": {
            "strategy": "validated field-name rename; enum values and all IL2CPP code unchanged",
            "changed_field_count": len(invest_enum_changes),
            "changes": invest_enum_changes,
        },
        "reference_pairs": reference_stats,
        "reference_conflicts": reference_conflicts,
        "modifier_almanac_parser": {
            "known_source_count": len(modifier_sources),
            "known_title_translation_count": len(modifier_title_translations),
            "known_exact_title_translation_count": len(modifier_exact_title_translations),
            "ambiguous_source_titles": modifier_ambiguous_title_translations,
            "parsed_literal_occurrences": len(modifier_records),
            "title_based_literal_occurrences": sum(
                record["match_reason"] != "exact_pc_or_reviewed_source"
                for record in modifier_records
            ),
            "preferred_title_occurrences": sum(
                record["preferred_title"] is not None
                for record in modifier_records
            ),
            "shrunk_title_occurrences": sum(
                bool(record["title_shrunk"])
                for record in modifier_records
            ),
            "escaped_category_modifier_occurrences": 0,
            "changed_after_provenance_resolution": sum(
                bool(record["changed_by_final_parser"])
                for record in modifier_records
            ),
            "records": modifier_records,
        },
        "sp_evolution_recipe_occurrences": len(sp_evolution_records),
        "sp_evolution_recipe_records": sp_evolution_records,
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
