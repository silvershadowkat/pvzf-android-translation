# Release 8 generic text review

The user clarified that plain UI and basic effect descriptions may be translated locally. Plant names, fusion recipes, and specialized/ambiguous descriptions still require matching PC terminology.

This pass reviewed 928 remaining Chinese metadata literals, including 44 historical fallback candidates. Forty-three exact sources were selected; old fallback names were not copied wholesale. The previously approved Blast Protection edit is separate.

Enchanted Shield and No Pains No Gains require their exact PC names in advancedBuffs.13001 and advancedBuffs.13100. If those names change or disappear, these local entries are withheld for review. No plant names or recipes were changed.

Remaining Unity Chinese fields are contributor names, specialized streaming instructions, plant-specific evolution route names, zombie flavor text, and a hidden talent label. They were left untouched. Metadata command tokens, regex patterns, runtime locale strings, and ambiguous/specialized mechanics were also excluded.

Verification: exactly 52 metadata literal changes from Release 7 (43 from this broader pass), with all numbers, C# arguments/precision, newline counts, and non-text metadata preserved. The Unity bundle remains the previously verified one-caption candidate. All 24 tests pass. Android display testing remains pending.

| Literal | Original | Prepared English |
| --- | --- | --- |
| 15717 | {0}给你加了{1}幸运 | {0} gave you {1} Luck |
| 15718 | {0}给你扣了{1}幸运 | {0} took {1} Luck from you |
| 15719 | {0}给你放了{1}个僵尸 | {0} spawned {1} zombies for you |
| 15722 | {0}获得随机独立伤害增幅<br>当前增幅：{1:F0}% | {0} gains a random independent damage bonus<br>Current bonus: {1:F0}% |
| 15961 | 不破不立：杀死你的全部植物，并将全场植物的独立伤害增幅和速度增幅减半<br>在20波后重复这一操作，但改为增幅翻倍 | No Pains No Gains：<br>Kill all your plants and halve all plants' independent damage and speed bonuses.<br>After 20 waves, repeat this operation, but double the bonuses instead. |
| 16254 | 全体植物获得抵御碾压的能力，复活后依然生效，并立即获得3000护盾 | All plants become immune to crushing, even after revival, and immediately gain 3000 Shield. |
| 16275 | 关卡信息错误 | Invalid level information |
| 16288 | 关卡数据为空！ | Level data is empty! |
| 16289 | 关卡数据解析失败 | Failed to parse level data |
| 16342 | 出保底了，当前保底阈值：{0} | Guaranteed reward triggered. Current threshold: {0} |
| 16392 | 创建存档出现错误：{0}<br>路径：{1} | Error creating save: {0}<br>Path: {1} |
| 16418 | 删除存档出现错误：{0}<br>路径：{1} | Error deleting save: {0}<br>Path: {1} |
| 16603 | 回血成功 | Healing successful |
| 16696 | 复活时间降低99%<br>当前标准复活时长：0秒 | Plant respawn time is reduced by 99%.<br>Current standard respawn time: 0s |
| 16757 | 子弹旋转半径提高12%，旋转速度提高80% | Projectile orbit radius increases by 12% and rotation speed by 80%. |
| 16771 | 存档数量已达上限 | Save limit reached |
| 16787 | 完成第{0}关即可扩大仓库容量 | Clear level {0} to expand storage capacity |
| 16893 | 已全部抽完，按任意键返回 | All draws completed. Press any key to return. |
| 16913 | 已移除路线： | Removed route:  |
| 16915 | 已经有一个同名文件了，这次会覆盖他 | A file with this name already exists. It will be overwritten. |
| 16917 | 已经选择路线： | Selected route:  |
| 16986 | 强化成功 | Upgrade successful |
| 17120 | 成功获取 {0} 个在线关卡 | Retrieved {0} online levels |
| 17184 | 护盾保护 | Enchanted Shield |
| 17185 | 护盾保护：持有护盾的植物每秒回复0.1%护盾量的生命值 | Enchanted Shield：<br>Shielded plants recover HP equal to 0.1% of their Shield each second. |
| 17195 | 持有护盾的植物每秒回复0.1%护盾量的生命值，并立即获得6000护盾 | Shielded plants recover HP equal to 0.1% of their Shield each second and immediately gain 6000 Shield. |
| 17278 | 文件不存在: {0} | File not found: {0} |
| 17284 | 文件无效 | Invalid file |
| 17614 | 槽位{0}为空，无法加载 | Slot {0} is empty and cannot be loaded |
| 17615 | 槽位索引无效: {0} | Invalid slot index: {0} |
| 17714 | 每次攻击多掉落一枚钱币 | Each attack drops one additional coin. |
| 18007 | 的诅咒效果已反转 | 's Curse has been reversed |
| 18326 | 获得了{0:F0}%力量增幅 | Gained a {0:F0}% power bonus |
| 18327 | 获得了{0:F0}%速度增幅 | Gained a {0:F0}% speed bonus |
| 18484 | 读取文件失败: {0}<br>错误信息: {1} | Failed to read file: {0}<br>Error: {1} |
| 18634 | 路线异常，请检查存档文件 | Invalid route. Please check the save file. |
| 18646 | 输入不合法 | Invalid input |
| 18746 | 重命名存档出现错误：{0}<br>旧路径：{1}<br>新路径：{2} | Error renaming save: {0}<br>Old path: {1}<br>New path: {2} |
| 18872 | 需要至少选中2个节点才能创建分组 | Select at least 2 nodes to create a group |
| 18884 | 音符数据已保存到:<br>{0}<br>共 {1} 个音符 | Note data saved to:<br>{0}<br>Total: {1} notes |
| 18885 | 音频文件加载错误，请检查文件是否在正确的位置<br> | Failed to load audio. Check that the file is in the correct location.<br> |
| 18990 | 📋 已复制到剪贴板 | 📋 Copied to clipboard |
| 19047 | ，下次启动将自动加载此存档 | ; this save will load automatically next time |
