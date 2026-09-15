"""Closed, source-reviewed Release 8 UI/basic-effect translations.

No substring replacements, plant names, recipes, command tokens, or fuzzy rules.
Named modifier cards additionally require the matching reviewed PC name.
"""

GENERIC_TEXT = {
    "{0}给你加了{1}幸运": "{0} gave you {1} Luck",
    "{0}给你扣了{1}幸运": "{0} took {1} Luck from you",
    "{0}给你放了{1}个僵尸": "{0} spawned {1} zombies for you",
    "{0}获得随机独立伤害增幅\n当前增幅：{1:F0}%": "{0} gains a random independent damage bonus\nCurrent bonus: {1:F0}%",
    "全体植物获得抵御碾压的能力，复活后依然生效，并立即获得3000护盾": "All plants become immune to crushing, even after revival, and immediately gain 3000 Shield.",
    "复活时间降低99%\n当前标准复活时长：0秒": "Plant respawn time is reduced by 99%.\nCurrent standard respawn time: 0s",
    "子弹旋转半径提高12%，旋转速度提高80%": "Projectile orbit radius increases by 12% and rotation speed by 80%.",
    "每次攻击多掉落一枚钱币": "Each attack drops one additional coin.",
    "的诅咒效果已反转": "'s Curse has been reversed",
    "获得了{0:F0}%力量增幅": "Gained a {0:F0}% power bonus",
    "获得了{0:F0}%速度增幅": "Gained a {0:F0}% speed bonus",
    "护盾保护": "Enchanted Shield",
    "护盾保护：持有护盾的植物每秒回复0.1%护盾量的生命值": "Enchanted Shield：Shielded plants recover HP equal to 0.1% of their Shield each second.",
    "持有护盾的植物每秒回复0.1%护盾量的生命值，并立即获得6000护盾": "Shielded plants recover HP equal to 0.1% of their Shield each second and immediately gain 6000 Shield.",
    "不破不立：杀死你的全部植物，并将全场植物的独立伤害增幅和速度增幅减半\n在20波后重复这一操作，但改为增幅翻倍": "No Pains No Gains：Kill all your plants and halve all plants' independent damage and speed bonuses.\nAfter 20 waves, repeat this operation, but double the bonuses instead.",
    "出保底了，当前保底阈值：{0}": "Guaranteed reward triggered. Current threshold: {0}",
    "关卡信息错误": "Invalid level information",
    "关卡数据为空！": "Level data is empty!",
    "关卡数据解析失败": "Failed to parse level data",
    "创建存档出现错误：{0}\n路径：{1}": "Error creating save: {0}\nPath: {1}",
    "删除存档出现错误：{0}\n路径：{1}": "Error deleting save: {0}\nPath: {1}",
    "存档数量已达上限": "Save limit reached",
    "完成第{0}关即可扩大仓库容量": "Clear level {0} to expand storage capacity",
    "已全部抽完，按任意键返回": "All draws completed. Press any key to return.",
    "已经有一个同名文件了，这次会覆盖他": "A file with this name already exists. It will be overwritten.",
    "已经选择路线：": "Selected route: ",
    "已移除路线：": "Removed route: ",
    "强化成功": "Upgrade successful",
    "回血成功": "Healing successful",
    "成功获取 {0} 个在线关卡": "Retrieved {0} online levels",
    "文件无效": "Invalid file",
    "文件不存在: {0}": "File not found: {0}",
    "槽位{0}为空，无法加载": "Slot {0} is empty and cannot be loaded",
    "槽位索引无效: {0}": "Invalid slot index: {0}",
    "读取文件失败: {0}\n错误信息: {1}": "Failed to read file: {0}\nError: {1}",
    "重命名存档出现错误：{0}\n旧路径：{1}\n新路径：{2}": "Error renaming save: {0}\nOld path: {1}\nNew path: {2}",
    "路线异常，请检查存档文件": "Invalid route. Please check the save file.",
    "输入不合法": "Invalid input",
    "需要至少选中2个节点才能创建分组": "Select at least 2 nodes to create a group",
    "音符数据已保存到:\n{0}\n共 {1} 个音符": "Note data saved to:\n{0}\nTotal: {1} notes",
    "音频文件加载错误，请检查文件是否在正确的位置\n": "Failed to load audio. Check that the file is in the correct location.\n",
    "📋 已复制到剪贴板": "📋 Copied to clipboard",
    "，下次启动将自动加载此存档": "; this save will load automatically next time",
}

from reviewed_release9_text import GENERIC_RELEASE9
GENERIC_TEXT.update(GENERIC_RELEASE9)
GENERIC_TEXT["命运无常：获得了{0}幸运"] = "Whims of Fate：Gained {0} Luck"

PC_NAME_REQUIREMENTS = {
    source: ('advancedBuffs', '13001', 'Enchanted Shield')
    for source in GENERIC_TEXT if source.startswith('护盾保护') or source.startswith('持有护盾的植物')
}
PC_NAME_REQUIREMENTS.update({
    source: ('advancedBuffs', '13100', 'No Pains No Gains')
    for source in GENERIC_TEXT if source.startswith('不破不立：')
})
PC_NAME_REQUIREMENTS["命运无常：获得了{0}幸运"] = ('debuffs', '10044', 'Whims of Fate')
