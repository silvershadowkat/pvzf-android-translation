#!/usr/bin/env python3
"""Apply Android-specific UI polish after translation and TMP transplant.

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
import sys
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_metadata_translation import (  # noqa: E402
    ANDROID_CONFIRMED_EXACT,
    ANDROID_REQUIRED_OVERRIDE_SOURCES,
    CJK_RE,
    is_usable_pc_translation,
    load_pc_translations,
)


SIZE_TAG_RE = re.compile(r"</?size(?:=[^>]*)?>", re.IGNORECASE)
ALMANAC_ASSETS = {"LawnStrings", "ZombieStrings"}

SERIALIZED_ANDROID_CORRECTIONS = {
    "<size=20>Let's Rock!": "<size=20>LETS ROCK",
    "Let's Rock!": "LETS ROCK",
    r"\u56fe\u9274" + "\ufffd\ufffd" + r"\u50f5\u5c38": "The Suburban Almanac - Zombies",
}

# User-approved, deterministic Android UI labels introduced in 3.9. This is a
# deliberately closed allowlist; other new 3.9 content still requires current
# PC English and otherwise remains Chinese.
CONFIRMED_NEW_39_UI = {
    "禁用屏幕抖动": "Disable Screen Shake",
    "伤害跳字": "Damage Numbers",
    "互动出怪上限": "Interactive Spawn Limit",
    "植物强化": "Plant Enhancement",
    "名字：弹幕": "Name: Bullet Chat",
    "关闭弹幕": "Disable Bullet Chat",
    "子弹基础伤害": "Base Projectile Damage",
    "点赞模式": "Like Mode",
    "刷一只僵尸\n所需点赞数": "Likes Required\nto Spawn One Zombie",
    "哔哩哔哩直播互动设置": "Bilibili Live Interaction Settings",
    "弹幕模式": "Bullet Chat Mode",
    "开启弹幕": "Enable Bullet Chat",
    "断开连接": "Disconnect",
    "刷怪模式": "Spawn Mode",
    "下载游戏搜索：\n蓝飘飘fly（B站）\n": (
        "To download the game, search:\n蓝飘飘fly (Bilibili)\n"
    ),
    "礼物模式": "Gift Mode",
    "启用SC": "Enable Super Chat",
    "连接直播间": "Connect to Live Room",
    "其他设置": "Other Settings",
    "弹幕刷怪单次上限": "Zombie Spawn Limit per Message",
}

TEXT_ASSET_REPLACEMENTS = {
    # Android retains category fields alongside the translated Mechanics
    # Almanac title/body. Translate them as well so future category/filter UI
    # cannot surface Chinese even though the current list mainly shows titles.
    "DetailStrings": {
        "玩法": "Gameplay",
        "基本机制": "Basic Mechanics",
        "植物特性": "Plant Traits",
        "植物体系": "Plant Systems",
        "僵尸机制": "Zombie Mechanics",
        "环境机制": "Environmental Mechanics",
        "关卡机制": "Level Mechanics",
    },
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
<size=12>蓝飘飘fly - Direction, Code & Animation
机鱼吐司 - Art & Visual Direction
梦珞 - Video Editing
射命丸文 - Animation Support
蓝蝶 - Art Support</size></align>"""

TEXT_OVERRIDES = {
    178983: CREDITS_TEXT,
    # The longer PC label collides with the two skin-navigation arrows on
    # Android. These are the three duplicated Almanac plant-detail variants.
    179605: "<size=80%><color=black>Skin</color></size>",
    179732: "Your Weapon",
    179832: "41_5\nBerserker I",
    179962: "Adventure Trials",
    180066: "Not Completed",
    180103: "42_5\nBerserker II",
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

# This Puzzle Mode button uses the legacy UnityEngine.UI.Text component,
# whose serialized field is m_Text (capital T). TEXT_OVERRIDES above targets
# TextMesh Pro components whose field is m_text (lowercase t).
LEGACY_TEXT_OVERRIDES = {
    185329: "Return to Index",
    185334: "Confirm Loadout",
    186732: "Switch Level Group",
    186853: "Sun Drop Multiplier",
    189691: "Go to the Shop",
    192713: "OK",
    193277: "Set Sun Amount",
}

# A few 3.8.1 Android perk strings differ slightly from the current PC source
# keys, so an exact PC lookup cannot match them. These narrowly scoped
# fallbacks preserve the Android meaning while using the PC terminology.
SERIALIZED_FIELD_FALLBACKS = {
    "豌豆射手": "Peashooter",
    "向日葵": "Sunflower",
    "返回菜单": "Back to Menu",
    "查看草坪": "View Lawn",
    "查看拼图\n": "View Puzzle\n",
    "查看用途": "View Uses",
    "查看收获": "View Harvest",
    "查看危机": "View Threats",
    "查看来源": "View Source",
    "查看已选路线": "View Selected Route",
    "查看已有词条": "View Current Modifiers",
    "禁用屏幕抖动": "Disable Screen Shake",
    "伤害跳字": "Damage Numbers",
    "断开连接": "Disconnect",
    "连接失败": "Connection Failed",
    "连接成功": "Connected",
    "关闭弹幕": "Disable Bullet Chat",
    "开启弹幕": "Enable Bullet Chat",
    "弹幕模式": "Bullet Chat Mode",
    "射击模式": "Shooting Mode",
    "刷怪模式": "Spawn Mode",
    "点赞模式": "Like Mode",
    "经典塔防模式": "Classic Tower Defense",
    "白天X黑夜": "Day x Night",
    "决战黑夜！": "Final Battle: Night!",
    "决战白天！": "Final Battle: Day!",
    "坚果台球": "Wall-nut Billiards",
    "坚果台球2": "Wall-nut Billiards 2",
    "坚果台球3": "Wall-nut Billiards 3",
    "强究植物": "Empowered Ultimate Plants",
    "互动出怪上限": "Interactive Spawn Limit",
    "名字：弹幕": "Name: Bullet Chat",
    "切换全屏1920*1080": "Toggle Fullscreen 1920x1080",
    "子弹基础伤害": "Base Projectile Damage",
    "选择地图：白天": "Select Map: Day",
    "哔哩哔哩直播互动设置": "Bilibili Live Interaction Settings",
    "究极黑曜石高坚果\n皮肤挑战": "Ultimate Obsidian Tall-nut\nSkin Challenge",
    "返回索引": "Return to Index",
    "确定退出吗？\n除了生存模式以外\n不会！保存关卡进度！": (
        "Exit the level?\nOnly Survival Mode\nsaves level progress!"
    ),
    "挑\n战\n者\n\n\n\n擂\n主": "C\nH\nA\nL\nL\nE\nN\nG\nE\nR\n\nH\nO\nS\nT",
    "白天：无尽": "Day: Endless",
    "屋顶：无尽": "Roof: Endless",
    "泳池：无尽": "Pool: Endless",
    "白天：困难": "Day: Hard",
    "黑夜：困难": "Night: Hard",
    "泳池：困难": "Pool: Hard",
    "冒险模式：第1关": "Adventure Mode: Level 1",
    "诸神进化：炼狱": "The Gods: Evolved - Purgatory",
    "疾速狂热": "Berserker I",
    "植物的攻击速度增加10%": "Increase the Attack Speed of all plants by 10%",
    "疾速狂热II": "Berserker II",
    "植物的攻击速度增加20%": "Increase the Attack Speed of all plants by another 20%",
    "每融合1次植物，下次融合的植物获得1%伤害加成": (
        "Your next Fused Plant gains 1% Attack Damage for each Fusion already performed"
    ),
    "植物射击一定次数后，接下来的1秒内获得无限射速": (
        "After firing a certain number of shots, a Plant gains unlimited Attack Speed for 1 second"
    ),
    "植物获得1%生命偷取，作用于全场血量百分比最低的植物": (
        "Plants gain 1% Life Steal, applied to the Plant with the lowest HP percentage on the field"
    ),
    "解锁超级水草、超级窝炬": "Unlock Hydra Kelp & Infernowood",
    "燃血": "Bloodburn",
    "植物造成伤害时会消耗本类型的全部植物当前血量的10%，造成100%已消耗血量的伤害，在血量低于10%时不触发": (
        "When a Plant deals damage, all Plants of that type consume 10% of their current HP "
        "to deal damage equal to 100% of the HP consumed; does not trigger below 10% HP"
    ),
    "超级樱桃射手：": "Super Cherry Peashooter:",
    "星辉：白天": "Starlight: Day",
    "查看词条": "View Modifiers",
    "花园保卫战1": "Garden Defense 1",
    "花园保卫战2": "Garden Defense 2",
    "花园保卫战3": "Garden Defense 3",
    "花园保卫战4": "Garden Defense 4",
    "花园保卫战5": "Garden Defense 5",
    "十旗挑战\n全员随机": "Ten-Flag Challenge\nRandomized Teams",
    "十旗挑战\n等价交换": "Ten-Flag Challenge\nEquivalent Exchange",
    "十旗挑战\n随机植物\n": "Ten-Flag Challenge\nRandom Plants\n",
    "十旗挑战\n黑夜舞会": "Ten-Flag Challenge\nNight Dance",
    "十旗挑战\n白天": "Ten-Flag Challenge\nDay",
    "十旗挑战\n胆小菇之梦": "Ten-Flag Challenge\nScaredy-shroom's Dream",
    "十旗挑战\n随机僵尸\n": "Ten-Flag Challenge\nRandom Zombies\n",
    "十旗挑战\n黑夜": "Ten-Flag Challenge\nNight",
    "十旗挑战\n浓雾": "Ten-Flag Challenge\nFog",
    "十旗挑战\n超级随机": "Ten-Flag Challenge\nSuper Random",
    "十旗挑战\n植物僵尸": "Ten-Flag Challenge\nZomBotany",
    "十旗挑战\n屋顶": "Ten-Flag Challenge\nRoof",
    "十旗挑战\n泳池": "Ten-Flag Challenge\nPool",
    "植物掉落阳光数​": "Sun Dropped by Plants",
    "刷一只僵尸\n所需点赞数": "Likes Needed\nto Spawn One Zombie",
    "设置阳光数​": "Set Sun Amount",
    "升级需要：\n（不限耐久）": "Upgrade Requires:\n(No Toughness Limit)",
    "手推车挑战": "Wheelbarrow Challenge",
    "礼物模式": "Gift Mode",
    "刷新\n商店": "Refresh\nShop",
    "锁定商店": "Lock Shop",
    "启用SC": "Enable Super Chats",
    "数量：\n总伤害：": "Count:\nTotal Damage:",
    "砸罐子2": "Vasebreaker 2",
    "切换手套": "Switch Glove",
    "连接直播间": "Connect to Stream",
    "弱究植物": "Weaker Ultimate Plants",
    "其他设置": "Other Settings",
    "弹幕刷怪单次上限": "Per-Message Zombie Spawn Limit",
    "黑夜：无尽": "Night: Endless",
    "浓雾：困难": "Fog: Hard",
    "浓雾：无尽": "Fog: Endless",
    "屋顶：困难": "Roof: Hard",
    "弹幕模式：\n发送弹幕【行数a数量】，可在指定行放置指定数量的僵尸\n如1a3：在1路放置3个僵尸，注意，必须是小写字母a，大写A无效\n发送弹幕【行数b类型】，可在指定行发射指定类型的子弹\n类型对应子弹：1：超级樱桃、2：黑铁豆、3：究极冰刺\n如1b3：在1路发射究极冰刺，子弹伤害和数量随波次提高\n\n礼物模式：\n人气票：2路放5个僵尸\t粉丝团灯牌：3路放5个僵尸\n小花花：4路放5个僵尸\t牛哇牛哇：5路放5个僵尸\n\nSC开启时：\n发送任意SC，获得实际消费金额（元）/3次机会，如发送30元的SC获得10次机会\n每次发送弹幕，如果符合规则，则消耗1次机会执行效果\n\n规则：\n【加xx幸运】，【扣xx幸运】，幸运单次操作上限为1000，如：加1000幸运\n【在xx路放置xx个xxx】，单次放置僵尸上限为100，如：在5路放置5个究极黑曜石巨人，僵尸名以图鉴为准\n\n备注：发送的弹幕不需要加【】，在这里只是提醒强调": (
        "Bullet Chat Mode:\nSend [lane a amount] to place zombies in a chosen lane.\n"
        "Example: 1a3 places 3 zombies in lane 1. Use a lowercase a.\n"
        "Send [lane b type] to fire a projectile in a chosen lane.\n"
        "Projectile types: 1 Super Cherry, 2 Dark Iron Pea, 3 Ultimate Ice Spike.\n"
        "Example: 1b3 fires an Ultimate Ice Spike in lane 1. Damage and quantity increase by wave.\n\n"
        "Gift Mode:\nPopularity Ticket: 5 zombies in lane 2    Fan Club Badge: 5 in lane 3\n"
        "Little Flower: 5 in lane 4    Awesome: 5 in lane 5\n\n"
        "When Super Chats are enabled:\nAny Super Chat grants amount spent in CNY / 3 uses. A CNY 30 message grants 10 uses.\n"
        "Each valid message consumes one use.\n\nRules:\nAdd xx Luck or Remove xx Luck, up to 1000 per command.\n"
        "Place xx [zombie] in lane xx, up to 100 zombies per command. Use Almanac zombie names.\n\n"
        "Note: Do not type the brackets. They are shown only to emphasize the command format."
    ),
    "【融合版3.9版本更新】\r\n\r\n更新内容：\r\n\r\n1. 诸神进化更新\r\n新增炼狱难度，在关卡开始时会获得一定的负面词条\r\n新增诅咒试炼词条，通过试炼可将其反转为祝福词条\r\n（可从推荐关卡处进入）\r\n\r\n2. 新植物\r\n普通系列：末影南瓜、金盏菇、金盏大蘑菇、银魅惑菇、金魅惑菇、樱桃小蘑菇、大嘴胆小菇、保护伞大喷菇、毁灭花盆、毁灭保护伞、海大嘴花、寒冰杨桃、大嘴喷菇、小嘴菇、海蘑菇花盆、大蒜杨桃\r\n究极系列：究极贪欲盒草、究极小松炉、超级机枪大喷菇、狙击胆小菇\r\n\r\n3. 新僵尸\r\n普通僵尸：撑杆橄榄球僵尸、猫瓜僵尸\r\nBOSS僵尸：黑橄榄将军、舞台巡演车\r\n\r\n4. 新皮肤\r\n究极黑曜石高坚果-定海堡礁\r\n（通过皮肤挑战后获得）\r\n\r\n5. 新词条\r\n新增了六个僵尸词条\r\n\r\n6. 平衡性调整\r\n·雪原重置：主线基础植物在雪原种植需要额外花费75阳光。其他内容详见[机制图鉴-雪原场景]及小松炉类植物、雪枪僵尸、雪叉僵尸的图鉴\r\n·毁灭三叶草：移除对余烬状态的伤害翻倍效果\r\n·毁灭仙人掌：新增子弹能穿透2次，并在伤害时施加余烬状态的效果\r\n·现在毁灭菇效果在水路留下坑洞时，会生成毁灭菇外表的睡莲\r\n·超时空毁灭菇、究极冰神毁灭菇：增强了对已处于传送状态的僵尸的秒杀能力\r\n·SP植物在集齐基础形态双词条后，需要在商店购买配方\r\n·【旅行：诅咒】的强究极植物配方涨价\r\n·【倒反天罡】修改为诅咒模式商店彩蛋词条\r\n\r\n7. 其他优化\r\n·设置中新增[禁用屏幕抖动]，开启后将屏蔽火爆辣椒、毁灭菇等植物的抖动特效\r\n·新增多个关卡速度档位\r\n·设置中新增[伤害跳字]，一些类型的伤害有不同颜色标识。请根据设备和实际需要选择是否开启\r\n·禅境花园的超级肥料开放正常购买途径，效果为使一个植物完全成长\r\n\r\n8. 修复了一些已知的bug，优化了游戏体验\r\n修复了末影南瓜箱子在随机模式中来者不拒的BUG\r\n\n\n": (
        "[PvZ Fusion 3.9 Update]\r\n\r\n"
        "1. The Gods: Evolved\r\nAdded Purgatory difficulty with negative starting modifiers. Added Curse Trials that can reverse curses into blessings. Enter from Recommended Levels.\r\n\r\n"
        "2. New Plants\r\nNormal: Ender Pumpkin, Marigold-shroom, Giant Marigold-shroom, Silver Hypno-shroom, Gold Hypno-shroom, Cherry Puff-shroom, Chomper Scaredy-shroom, Umbrella Fume-shroom, Doom Flower Pot, Doom Umbrella Leaf, Sea Chomper, Snow Starfruit, Chomper Fume-shroom, Little Chomper-shroom, Sea-shroom Flower Pot, and Garlic Starfruit.\r\nUltimate: Ultimate Greedy Boxgrass, Ultimate Little Pine Furnace, Super Gatling Fume-shroom, and Sniper Scaredy-shroom.\r\n\r\n"
        "3. New Zombies\r\nNormal: Pole Vaulting Football Zombie and Cat Melon Zombie. Bosses: Black Football General and Touring Stage Vehicle.\r\n\r\n"
        "4. New Skin\r\nUltimate Obsidian Tall-nut: Sea Fortress Reef, earned from its Skin Challenge.\r\n\r\n"
        "5. New Modifiers\r\nAdded six Zombie Modifiers.\r\n\r\n"
        "6. Balance Changes\r\nSnowfield main-route base plants now cost 75 extra Sun. See Mechanics Almanac: Snowfield and the related plant and zombie entries. Doom Blover no longer deals double damage to Irradiated targets. Doom Cactus projectiles now pierce twice and inflict Irradiated. Doom-shroom craters in water now create Doom-shroom Lily Pads. Chrono Doom-shroom and Ultimate Ice God Doom-shroom have stronger executions against Chronoshifted zombies. SP recipes must now be purchased after collecting both base-form modifiers. Powerful Ultimate recipes cost more in Odyssey: Cursed. Reversal is now a Cursed-mode shop easter-egg modifier.\r\n\r\n"
        "7. Other Improvements\r\nAdded Disable Screen Shake, more game-speed settings, and colored Damage Numbers. Super Fertilizer can now be purchased normally in Zen Garden and fully grows one plant.\r\n\r\n"
        "8. Bug Fixes\r\nFixed known issues, including Ender Pumpkin boxes accepting everything in Random Mode.\r\n"
    ),
}

VISIBLE_UI_TITLE_WORDS = {
    "新的开始": "A New Beginning",
    "梦的开始": "The Dream Begins",
    "射击训练": "Target Practice",
    "精准打击": "Precision Strike",
    "精准打击II": "Precision Strike II",
    "全息制冷": "Holographic Cooling I",
    "全息制冷II": "Holographic Cooling II",
    "全息制冷III": "Holographic Cooling III",
    "精打细算": "Cost Efficiency I",
    "精打细算II": "Cost Efficiency II",
    "精打细算III": "Cost Efficiency III",
    "正当防卫": "Self Defense I",
    "正当防卫III": "Self Defense III",
    "绝对力量II": "Absolute Power II",
    "绝对力量III": "Absolute Power III",
    "铜墙铁壁": "Iron Defense I",
    "铜墙铁壁II": "Iron Defense II",
    "至极手速": "Quick Hands I",
    "至极手速II": "Quick Hands II",
    "至极手速III": "Quick Hands III",
    "返璞归真I": "Back to Basics I",
    "返璞归真III": "Back to Basics III",
    "超级-白天": "Super Day",
    "超级-屋顶": "Super Roof",
    "超光速提拔": "Lightspeed Promotion",
    "勤能补拙": "Practice Makes Perfect",
    "爽快射击": "Trigger Happy",
    "生命偷取": "Life Steal",
    "生命偷取II": "Life Steal II",
    "更多阳光": "More Sun",
    "超级-浓雾": "Super Fog",
    "绝对力量": "Absolute Power I",
    "光合作用": "Photosynthesis I",
    "光合作用II": "Photosynthesis II",
    "光合作用III": "Photosynthesis III",
    "正当防卫II": "Self Defense II",
    "铜墙铁壁III": "Iron Defense III",
    "超级-黑夜": "Super Night",
    "精准打击III": "Precision Strike III",
    "坚不可摧": "Indestructible",
    "超级-泳池": "Super Pool",
    "深度探索": "Deep Exploration",
    "返璞归真II": "Back to Basics II",
    "人工栽培": "Artificial Cultivation",
}


def translate_visible_ui_pattern(value: str) -> str | None:
    patterns = (
        (r"^第(\d+)关$", "Level {}"),
        (r"^支线(\d+)$", "Side Route {}"),
        (r"^(\d+)轮$", "Round {}"),
        (r"^队伍(\d+)$", "Team {}"),
        (r"^快捷键：(\d+)$", "Hotkey: {}"),
        (r"^查看词条(\d+)$", "View Modifier {}"),
        (r"^刷新\((\d+)\)$", "Reroll ({})"),
        (r"^第(\d+)页$", "Page {}"),
        (r"^第(\d+)波$", "Wave {}"),
        (r"^雪原：第(\d+)关$", "Snowfield: Level {}"),
        (r"^雪夜：第(\d+)关$", "Snowy Night: Level {}"),
        (r"^章节难度：(\d+)$", "Chapter Difficulty: {}"),
        (r"^难度阶数：(\d+)$", "Difficulty Tier: {}"),
        (r"^难度：(\d+)$", "Difficulty: {}"),
        (r"^波次：(\d+)/(\d+)$", "Wave: {}/{}"),
        (r"^(\d+)/(\d+)页$", "Page {}/{}"),
        (r"^场上敌人数量：(\d+)\n?$", "Enemies on Lawn: {}"),
        (r"^剩余阳光：(\d+)$", "Sun Remaining: {}"),
        (r"^(\d+)分$", "{} Points"),
        (r"^铲除植物：(\d+)$", "Plants Shoveled: {}"),
        (r"^当前大小：(\d+)$", "Current Size: {}"),
        (r"^现实游戏时长：(.+)$", "Real Play Time: {}"),
    )
    for pattern, template in patterns:
        match = re.fullmatch(pattern, value)
        if match:
            return template.format(*match.groups())
    match = re.fullmatch(r"(\d+_\d+)\n(.+)", value, re.DOTALL)
    if match and match.group(2) in VISIBLE_UI_TITLE_WORDS:
        return f"{match.group(1)}\n{VISIBLE_UI_TITLE_WORDS[match.group(2)]}"
    stat_prefixes = {
        "魅惑僵尸": "Hypnotized Zombies",
        "击杀僵尸": "Zombies Defeated",
        "种植植物": "Plants Planted",
        "死亡植物": "Plants Lost",
        "总伤害": "Total Damage",
        "游戏时长": "Play Time",
        "获得金币": "Coins Earned",
        "消耗金币": "Coins Spent",
        "剩余金币": "Coins Remaining",
        "当前积分": "Current Score",
        "小推车使用": "Lawn Mowers Used",
        "消耗阳光": "Sun Spent",
        "产生阳光": "Sun Produced",
    }
    for source, target in stat_prefixes.items():
        if value.startswith(source + "："):
            return target + ":" + value.split("：", 1)[1]
    return None

SERIALIZED_PC_FIELD_SUFFIXES = {
    ("m_text",),
    ("m_Text",),
    ("data", "name"),
    ("data", "description"),
    ("group", "title"),
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
# The selected Zombie Almanac name is rendered twice (foreground + shadow).
# Keep both components capped together so long PC names fit identically.
ZOMBIE_NAME_COMPONENTS = {185821, 192116}
ALMANAC_TIP_COMPONENT = 184559
ALMANAC_TIP_RECT_TRANSFORM = 176824
PORT_CREDITS_COMPONENT = 179902
PORT_CREDITS_RECT_TRANSFORM = 176070
PORT_CREDITS_FONT_ASSET = 178477  # 汉仪夏日体W SDF (parchment handwriting)
PORT_CREDITS_MATERIAL = 2
GARDEN_STORE_BACKGROUND_RECT_TRANSFORM = 173612
GARDEN_PROTECTION_BACKGROUND_RECT_TRANSFORM = 170016
ULTRAWIDE_MODAL_BACKGROUNDS = {
    GARDEN_STORE_BACKGROUND_RECT_TRANSFORM: "garden_store_ultrawide_background",
    GARDEN_PROTECTION_BACKGROUND_RECT_TRANSFORM: "garden_defense_ultrawide_background",
}


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


def object_by_path_id(objects, path_id: int):
    matches = [obj for (_, candidate_id), obj in objects.items() if candidate_id == path_id]
    if len(matches) != 1:
        raise RuntimeError(f"expected one object with path ID {path_id}, found {len(matches)}")
    return matches[0]


def game_object_name(objects, file_name: str, path_id: int) -> str:
    obj = objects.get((file_name, path_id))
    if obj is None:
        return ""
    try:
        return obj.read().m_Name
    except Exception:
        return ""


def transform_for_game_object(objects, file_name: str, game_object_id: int):
    game_object = objects.get((file_name, game_object_id))
    if game_object is None:
        return None
    try:
        components = game_object.read().m_Component
    except Exception:
        return None
    for item in components:
        pointer = getattr(item, "component", item)
        obj = objects.get((file_name, getattr(pointer, "path_id", 0)))
        if obj is not None and obj.type.name in ("Transform", "RectTransform"):
            return obj
    return None


def hierarchy_for_component(objects, obj) -> tuple[str, ...]:
    file_name = obj.assets_file.name
    if obj.type.name in ("Transform", "RectTransform"):
        transform = obj
    else:
        raw = bytes(obj.get_raw_data())
        if len(raw) < 12:
            return ()
        game_object_id = int.from_bytes(raw[4:12], "little", signed=True)
        transform = transform_for_game_object(objects, file_name, game_object_id)
    names = []
    seen = set()
    while transform is not None and transform.path_id not in seen and len(names) < 20:
        seen.add(transform.path_id)
        data = transform.read()
        names.append(game_object_name(objects, file_name, data.m_GameObject.path_id))
        father_id = getattr(data.m_Father, "path_id", 0)
        transform = objects.get((file_name, father_id)) if father_id else None
    return tuple(names)


def mono_script_name(objects, obj) -> str:
    if obj.type.name != "MonoBehaviour":
        return ""
    try:
        tree = obj.read_typetree(check_read=False)
        pointer = tree.get("m_Script", {})
        script = objects.get((obj.assets_file.name, pointer.get("m_PathID", 0)))
        return script.read().m_Name if script is not None else ""
    except Exception:
        return ""


def build_component_index(objects):
    index = {}
    for obj in objects.values():
        if obj.type.name not in ("MonoBehaviour", "RectTransform", "Transform"):
            continue
        hierarchy = hierarchy_for_component(objects, obj)
        if not hierarchy:
            continue
        key = (obj.type.name, hierarchy, mono_script_name(objects, obj))
        index.setdefault(key, []).append(obj)
    for peers in index.values():
        peers.sort(key=lambda item: item.path_id)
    return index


def resolve_reference_path_id(
    reference_objects,
    current_objects,
    reference_index,
    current_index,
    reference_path_id: int,
    field: str | None = None,
) -> int:
    reference_obj = reference_objects[("resources.assets", reference_path_id)]
    hierarchy = hierarchy_for_component(reference_objects, reference_obj)
    script_name = mono_script_name(reference_objects, reference_obj)
    key = (reference_obj.type.name, hierarchy, script_name)
    reference_peers = list(reference_index.get(key, []))
    current_peers = list(current_index.get(key, []))
    if field is not None:
        def has_field(obj) -> bool:
            try:
                return field in obj.read_typetree(check_read=False)
            except Exception:
                return False

        reference_peers = [obj for obj in reference_peers if has_field(obj)]
        current_peers = [obj for obj in current_peers if has_field(obj)]
    if len(reference_peers) != len(current_peers) or reference_obj not in reference_peers:
        raise RuntimeError(
            f"cannot safely map reference path ID {reference_path_id}: hierarchy={hierarchy!r}, "
            f"script={script_name!r}, reference peers={len(reference_peers)}, current peers={len(current_peers)}"
        )
    current_obj = current_peers[reference_peers.index(reference_obj)]
    return current_obj.path_id


def find_named_mono(objects, name: str):
    matches = []
    for obj in objects.values():
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            if obj.read_typetree(check_read=False).get("m_Name") == name:
                matches.append(obj)
        except Exception:
            continue
    if len(matches) != 1:
        raise RuntimeError(f"expected one MonoBehaviour named {name!r}, found {len(matches)}")
    return matches[0]


def find_named_material(objects, name: str):
    matches = []
    for obj in objects.values():
        if obj.type.name != "Material":
            continue
        try:
            if obj.read_typetree().get("m_Name") == name:
                matches.append(obj)
        except Exception:
            continue
    if len(matches) != 1:
        raise RuntimeError(f"expected one Material named {name!r}, found {len(matches)}")
    return matches[0]


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


def collect_string_values(value, output: set[str]) -> None:
    if isinstance(value, str):
        output.add(value)
    elif isinstance(value, dict):
        for item in value.values():
            collect_string_values(item, output)
    elif isinstance(value, list):
        for item in value:
            collect_string_values(item, output)


def collect_serialized_strings(bundle: Path, generator: TypeTreeGenerator) -> set[str]:
    env = UnityPy.load(str(bundle))
    env.typetree_generator = generator
    result: set[str] = set()
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            tree = obj.read_typetree(check_read=False)
        except Exception:
            continue
        collect_string_values(tree, result)
    del env
    gc.collect()
    return result


def translate_serialized_fields(
    value,
    exact: dict[str, str],
    previous_version_strings: set[str],
    path=(),
):
    """Translate only known player-facing configuration fields."""
    changes = []
    if isinstance(value, dict):
        for key, item in list(value.items()):
            child_path = path + (key,)
            if (
                isinstance(item, str)
                and any(
                    len(child_path) >= len(suffix)
                    and tuple(child_path[-len(suffix):]) == suffix
                    for suffix in SERIALIZED_PC_FIELD_SUFFIXES
                )
                and (CJK_RE.search(item) or item in SERIALIZED_ANDROID_CORRECTIONS)
            ):
                translated = exact.get(item)
                if translated is None and item in previous_version_strings:
                    translated = SERIALIZED_FIELD_FALLBACKS.get(item)
                if (
                    translated is None
                    and item in previous_version_strings
                    and child_path[-1] in {"m_text", "m_Text"}
                ):
                    translated = translate_visible_ui_pattern(item)
                if translated is not None:
                    value[key] = translated
                    changes.append((child_path, item, translated))
            else:
                changes.extend(
                    translate_serialized_fields(
                        item,
                        exact,
                        previous_version_strings,
                        child_path,
                    )
                )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            changes.extend(
                translate_serialized_fields(
                    item,
                    exact,
                    previous_version_strings,
                    path + (index,),
                )
            )
    return changes


def main() -> int:
    global TEXT_OVERRIDES, LEGACY_TEXT_OVERRIDES, HANDLE_REPLACEMENTS
    global ZOMBIE_TITLE_COMPONENTS, ZOMBIE_NAME_COMPONENTS
    global ALMANAC_TIP_COMPONENT, ALMANAC_TIP_RECT_TRANSFORM
    global PORT_CREDITS_COMPONENT, PORT_CREDITS_RECT_TRANSFORM
    global PORT_CREDITS_FONT_ASSET, PORT_CREDITS_MATERIAL
    global ULTRAWIDE_MODAL_BACKGROUNDS

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument(
        "--reference-bundle",
        type=Path,
        help="3.8.1 bundle used only to resolve proven UI targets by hierarchy",
    )
    parser.add_argument(
        "--previous-version-source-bundle",
        required=True,
        type=Path,
        help=(
            "official Chinese 3.8.1 bundle used to allow only inherited "
            "Android fallback translations for unchanged source text"
        ),
    )
    parser.add_argument("--dummy-dll-dir", required=True, type=Path)
    parser.add_argument(
        "--strings-dir",
        type=Path,
        default=Path(
            "translation-data/PVZF-Translation/PvZ_Fusion_Translator/"
            "Localization/English/Strings"
        ),
        help="current PC-community English Strings directory",
    )
    parser.add_argument("--unity-version", default="2022.3.62f1")
    parser.add_argument("--zombie-title-size", default=36.0, type=float)
    parser.add_argument("--zombie-name-size", default=24.0, type=float)
    parser.add_argument(
        "--allow-untranslated-new-content",
        action="store_true",
        help="allow 3.9 to remove or rename old labels while translating confirmed overlap",
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    generator = make_generator(args.unity_version, args.dummy_dll_dir)
    env = UnityPy.load(str(args.base_bundle))
    env.typetree_generator = generator
    objects = object_map(env)

    path_id_mapping = {}
    skipped_reference_targets = []
    if args.reference_bundle is not None:
        reference_env = UnityPy.load(str(args.reference_bundle))
        reference_env.typetree_generator = generator
        reference_objects = object_map(reference_env)
        reference_index = build_component_index(reference_objects)
        current_index = build_component_index(objects)

        def remap(path_id: int, field: str | None = None) -> int:
            mapped = resolve_reference_path_id(
                reference_objects,
                objects,
                reference_index,
                current_index,
                path_id,
                field,
            )
            path_id_mapping[path_id] = mapped
            return mapped

        def remap_optional(path_id: int, field: str | None = None):
            try:
                return remap(path_id, field)
            except RuntimeError as exc:
                skipped_reference_targets.append(
                    {"path_id": path_id, "field": field, "reason": str(exc)}
                )
                return None

        def remap_overrides(overrides, field):
            remapped = {}
            for path_id, value in overrides.items():
                mapped = remap(path_id, field)
                previous = remapped.get(mapped)
                if previous is not None and previous != value:
                    raise RuntimeError(
                        f"conflicting {field} overrides remap to component {mapped}: "
                        f"{previous!r} versus {value!r}"
                    )
                remapped[mapped] = value
            return remapped

        TEXT_OVERRIDES = remap_overrides(TEXT_OVERRIDES, "m_text")
        LEGACY_TEXT_OVERRIDES = remap_overrides(LEGACY_TEXT_OVERRIDES, "m_Text")
        HANDLE_REPLACEMENTS = {
            mapped: value
            for path_id, value in HANDLE_REPLACEMENTS.items()
            if (mapped := remap_optional(path_id, "m_text")) is not None
        }
        ZOMBIE_TITLE_COMPONENTS = {remap(path_id, "m_fontSize") for path_id in ZOMBIE_TITLE_COMPONENTS}
        ZOMBIE_NAME_COMPONENTS = {remap(path_id, "m_fontSize") for path_id in ZOMBIE_NAME_COMPONENTS}
        ALMANAC_TIP_COMPONENT = remap(ALMANAC_TIP_COMPONENT, "m_text")
        ALMANAC_TIP_RECT_TRANSFORM = remap(ALMANAC_TIP_RECT_TRANSFORM)
        PORT_CREDITS_COMPONENT = remap(PORT_CREDITS_COMPONENT, "m_text")
        PORT_CREDITS_RECT_TRANSFORM = remap(PORT_CREDITS_RECT_TRANSFORM)
        ULTRAWIDE_MODAL_BACKGROUNDS = {
            remap(path_id): kind for path_id, kind in ULTRAWIDE_MODAL_BACKGROUNDS.items()
        }

        reference_font = reference_objects[("resources.assets", PORT_CREDITS_FONT_ASSET)]
        reference_font_name = reference_font.read_typetree(check_read=False)["m_Name"]
        PORT_CREDITS_FONT_ASSET = find_named_mono(objects, reference_font_name).path_id
        reference_material = reference_objects[("resources.assets", PORT_CREDITS_MATERIAL)]
        reference_material_name = reference_material.read_typetree()["m_Name"]
        PORT_CREDITS_MATERIAL = find_named_material(objects, reference_material_name).path_id
        del reference_env

    changes = []
    previous_version_strings = collect_serialized_strings(
        args.previous_version_source_bundle,
        generator,
    )
    pc_exact, _, _, _ = load_pc_translations(args.strings_dir)
    # Current PC community translations remain authoritative. Reviewed
    # Android-only mappings fill exact gaps, including new 3.9 visible labels.
    serialized_exact = {
        source: translated
        for source, translated in pc_exact.items()
        if is_usable_pc_translation(translated)
    }
    for source, translated in ANDROID_CONFIRMED_EXACT.items():
        if source in previous_version_strings:
            serialized_exact.setdefault(source, translated)
    for source in ANDROID_REQUIRED_OVERRIDE_SOURCES:
        if source in ANDROID_CONFIRMED_EXACT:
            serialized_exact[source] = ANDROID_CONFIRMED_EXACT[source]
    for source, translated in CONFIRMED_NEW_39_UI.items():
        serialized_exact.setdefault(source, translated)
    serialized_exact.update(SERIALIZED_ANDROID_CORRECTIONS)

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
    expected_config_targets: dict[str, set[str]] = {}
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.parse_as_object()
        replacements = TEXT_ASSET_REPLACEMENTS.get(data.m_Name)
        if replacements is None:
            continue
        tree = json.loads(data.m_Script.lstrip("\ufeff"))
        serialized_before = json.dumps(tree, ensure_ascii=False)
        applied_sources = {source for source in replacements if source in serialized_before}
        tree = replace_nested_strings(tree, replacements)
        serialized_after = json.dumps(tree, ensure_ascii=False)
        unresolved = [source for source in replacements if source in serialized_after]
        if unresolved:
            raise RuntimeError(f"visible translations remain in {data.m_Name}: {unresolved}")
        expected_targets = {replacements[source] for source in applied_sources}
        missing_targets = sorted(target for target in expected_targets if target not in serialized_after)
        if missing_targets:
            raise RuntimeError(f"translated labels missing from {data.m_Name}: {missing_targets}")
        data.m_Script = json.dumps(tree, ensure_ascii=False, indent=4)
        obj.save_typetree(data)
        translated_config_assets.add(data.m_Name)
        expected_config_targets[data.m_Name] = expected_targets
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

    for path_id, replacement in LEGACY_TEXT_OVERRIDES.items():
        obj = objects[("resources.assets", path_id)]
        tree = obj.read_typetree(check_read=False)
        previous = tree["m_Text"]
        tree["m_Text"] = replacement
        obj.save_typetree(tree)
        changes.append(
            {
                "kind": "legacy_ui_text",
                "path_id": path_id,
                "before": previous,
                "after": replacement,
            }
        )

    serialized_field_changes = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            tree = obj.read_typetree(check_read=False)
        except Exception:
            continue
        object_changes = translate_serialized_fields(
            tree,
            serialized_exact,
            previous_version_strings,
        )
        if not object_changes:
            continue
        obj.save_typetree(tree)
        for field_path, previous, replacement in object_changes:
            change = {
                "kind": "serialized_pc_translation",
                "file": obj.assets_file.name,
                "path_id": obj.path_id,
                "field_path": list(field_path),
                "before": previous,
                "after": replacement,
                "source": "pc_exact" if previous in pc_exact else "android_reviewed_exact",
            }
            serialized_field_changes.append(change)
            changes.append(change)

    # UnityPy does not merge separate typetree edits to the same component in
    # memory. Save and reload the translated checkpoint before applying font,
    # sizing, and layout edits so those later edits cannot restore old text.
    checkpoint_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    del env, objects
    gc.collect()
    env = UnityPy.load(checkpoint_bytes)
    del checkpoint_bytes
    env.typetree_generator = generator
    objects = object_map(env)

    # `关闭` is a generic word, and the PC dictionary's context-free
    # "Disabled" is correct in some state labels but wrong on red-X close
    # buttons. Apply this after the checkpoint reload so the generic serialized
    # translation cannot be restored from UnityPy's pre-save object cache.
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            tree = obj.read_typetree(check_read=False)
        except Exception:
            continue
        if tree.get("m_text") != "Disabled":
            continue
        hierarchy = hierarchy_for_component(objects, obj)
        if len(hierarchy) < 2 or hierarchy[0] != "text" or hierarchy[1] != "Goback":
            continue
        tree["m_text"] = "Close"
        obj.save_typetree(tree)
        change = {
            "kind": "contextual_close_button",
            "file": obj.assets_file.name,
            "path_id": obj.path_id,
            "hierarchy": list(hierarchy),
            "before": "Disabled",
            "after": "Close",
        }
        changes.append(change)

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

    for path_id in ZOMBIE_NAME_COMPONENTS:
        obj = objects[("resources.assets", path_id)]
        tree = obj.read_typetree(check_read=False)
        previous = {
            "font_size": tree["m_fontSize"],
            "font_size_base": tree["m_fontSizeBase"],
            "font_size_max": tree["m_fontSizeMax"],
        }
        tree["m_fontSize"] = args.zombie_name_size
        tree["m_fontSizeBase"] = args.zombie_name_size
        tree["m_fontSizeMax"] = args.zombie_name_size
        obj.save_typetree(tree)
        changes.append(
            {
                "kind": "zombie_selected_name_size",
                "path_id": path_id,
                "before": previous,
                "after": {
                    "font_size": args.zombie_name_size,
                    "font_size_base": args.zombie_name_size,
                    "font_size_max": args.zombie_name_size,
                },
            }
        )

    tip_obj = objects[("resources.assets", ALMANAC_TIP_COMPONENT)]
    tip_tree = tip_obj.read_typetree(check_read=False)
    tip_before = {
        "font_size": tip_tree["m_fontSize"],
        "auto_size": tip_tree["m_enableAutoSizing"],
        "word_wrap": tip_tree["m_enableWordWrapping"],
    }
    # Reassert translated text after the fresh typetree read.
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

    # These Zen Garden modal menus sit over the normal shop screen. Their
    # parchment backgrounds were fixed at 1920x1080, exposing inactive shop
    # buttons on ultrawide displays. Stretch only each visual background;
    # preserve every modal control and its reference-resolution layout.
    for path_id, kind in ULTRAWIDE_MODAL_BACKGROUNDS.items():
        background_obj = objects[("resources.assets", path_id)]
        background_tree = background_obj.read_typetree()
        background_before = {
            "anchor_min": dict(background_tree["m_AnchorMin"]),
            "anchor_max": dict(background_tree["m_AnchorMax"]),
            "anchored_position": dict(background_tree["m_AnchoredPosition"]),
            "size": dict(background_tree["m_SizeDelta"]),
        }
        background_tree["m_AnchorMin"] = {"x": 0.0, "y": 0.0}
        background_tree["m_AnchorMax"] = {"x": 1.0, "y": 1.0}
        background_tree["m_AnchoredPosition"] = {"x": 0.0, "y": 0.0}
        background_tree["m_SizeDelta"] = {"x": 0.0, "y": 0.0}
        background_obj.save_typetree(background_tree)
        changes.append(
            {
                "kind": kind,
                "rect_transform_path_id": path_id,
                "before": background_before,
                "after": {
                    "anchor_min": {"x": 0.0, "y": 0.0},
                    "anchor_max": {"x": 1.0, "y": 1.0},
                    "anchored_position": {"x": 0.0, "y": 0.0},
                    "size": {"x": 0.0, "y": 0.0},
                },
            }
        )

    # UnityPy does not merge multiple unsaved typetree edits made to the same
    # component.  Persist and reload the completed typography/layout pass before
    # applying the final reviewed text overrides so those overrides cannot
    # silently restore the component's older font and sizing fields.
    layout_checkpoint_bytes = env.file.save(
        packer=None if args.packer == "none" else args.packer
    )
    del env, objects
    gc.collect()
    env = UnityPy.load(layout_checkpoint_bytes)
    del layout_checkpoint_bytes
    if env.file is None:
        raise RuntimeError("layout checkpoint reload did not produce a Unity file")
    env.typetree_generator = generator
    objects = object_map(env)

    # Explicit, reviewed Android UI labels win over the broad serialized pass.
    for path_id, replacement in TEXT_OVERRIDES.items():
        obj = objects[("resources.assets", path_id)]
        tree = obj.read_typetree(check_read=False)
        tree["m_text"] = replacement
        obj.save_typetree(tree)
    for path_id, replacement in LEGACY_TEXT_OVERRIDES.items():
        obj = objects[("resources.assets", path_id)]
        tree = obj.read_typetree(check_read=False)
        tree["m_Text"] = replacement
        obj.save_typetree(tree)

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
            raise RuntimeError(
                f"UI text validation failed for component {path_id}: "
                f"expected={replacement!r}, actual={tree['m_text']!r}"
            )
    for path_id, replacement in LEGACY_TEXT_OVERRIDES.items():
        tree = check_objects[("resources.assets", path_id)].read_typetree(check_read=False)
        if tree["m_Text"] != replacement:
            raise RuntimeError(
                f"legacy UI text validation failed for component {path_id}: "
                f"expected={replacement!r}, actual={tree['m_Text']!r}"
            )
    contextual_close_path_ids = {
        change["path_id"]
        for change in changes
        if change.get("kind") == "contextual_close_button"
    }
    for change in serialized_field_changes:
        # Explicit reviewed Android UI overrides are intentionally reasserted
        # after the broad serialized-field translation pass. Do not validate
        # the superseded generic value for the same text field.
        is_explicit_text_override = (
            change["file"] == "resources.assets"
            and (
                (
                    change["path_id"] in TEXT_OVERRIDES
                    and change["field_path"] == ["m_text"]
                )
                or (
                    change["path_id"] in LEGACY_TEXT_OVERRIDES
                    and change["field_path"] == ["m_Text"]
                )
            )
        )
        if is_explicit_text_override:
            continue
        if (
            change["file"] == "resources.assets"
            and change["path_id"] in contextual_close_path_ids
            and change["field_path"] == ["m_text"]
        ):
            continue
        tree = check_objects[(change["file"], change["path_id"])].read_typetree(check_read=False)
        value = tree
        for part in change["field_path"]:
            value = value[part]
        if value != change["after"]:
            raise RuntimeError(
                f"serialized field validation failed for component {change['path_id']}: "
                f"file={change['file']!r}, field_path={change['field_path']!r}, "
                f"expected={change['after']!r}, actual={value!r}"
            )
    for path_id in contextual_close_path_ids:
        value = check_objects[("resources.assets", path_id)].read_typetree(
            check_read=False
        )["m_text"]
        if value != "Close":
            raise RuntimeError(
                f"contextual close-button validation failed for component {path_id}: "
                f"expected='Close', actual={value!r}"
            )
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
        raise RuntimeError(
            "port-credit layout validation failed: "
            f"font_size={port_credit_tree['m_fontSize']!r}, "
            f"auto_size={port_credit_tree['m_enableAutoSizing']!r}, "
            f"word_wrap={port_credit_tree['m_enableWordWrapping']!r}, "
            f"font={port_credit_tree['m_fontAsset']['m_PathID']!r}, "
            f"material={port_credit_tree['m_sharedMaterial']['m_PathID']!r}, "
            f"position={port_credit_rect_tree['m_AnchoredPosition']!r}, "
            f"size={port_credit_rect_tree['m_SizeDelta']!r}"
        )
    for path_id in HANDLE_REPLACEMENTS:
        tree = check_objects[("resources.assets", path_id)].read_typetree(check_read=False)
        if any(source in tree["m_text"] for source in HANDLE_REPLACEMENTS[path_id]):
            raise RuntimeError(f"handle validation failed for component {path_id}")
    for path_id in ZOMBIE_TITLE_COMPONENTS:
        tree = check_objects[("resources.assets", path_id)].read_typetree(check_read=False)
        if tree["m_fontSize"] != args.zombie_title_size:
            raise RuntimeError(f"zombie title validation failed for component {path_id}")
    for path_id in ZOMBIE_NAME_COMPONENTS:
        tree = check_objects[("resources.assets", path_id)].read_typetree(check_read=False)
        if (
            tree["m_fontSize"] != args.zombie_name_size
            or tree["m_fontSizeBase"] != args.zombie_name_size
            or tree["m_fontSizeMax"] != args.zombie_name_size
        ):
            raise RuntimeError(f"zombie selected-name validation failed for component {path_id}")
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
    for path_id, kind in ULTRAWIDE_MODAL_BACKGROUNDS.items():
        background_tree = check_objects[("resources.assets", path_id)].read_typetree()
        if (
            background_tree["m_AnchorMin"] != {"x": 0.0, "y": 0.0}
            or background_tree["m_AnchorMax"] != {"x": 1.0, "y": 1.0}
            or background_tree["m_AnchoredPosition"] != {"x": 0.0, "y": 0.0}
            or background_tree["m_SizeDelta"] != {"x": 0.0, "y": 0.0}
        ):
            raise RuntimeError(f"{kind} validation failed")
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
        if any(target not in payload for target in expected_config_targets[data.m_Name]):
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
        "reference_path_id_mapping": path_id_mapping,
        "skipped_reference_targets": skipped_reference_targets,
        "previous_version_source": {
            "path": str(args.previous_version_source_bundle.resolve()),
            "serialized_string_count": len(previous_version_strings),
        },
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
