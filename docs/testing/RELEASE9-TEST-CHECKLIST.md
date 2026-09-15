# Release 9 test locations

These checks are for the next local APK. Only the text payloads have been prepared so far. Unlock All helps expose cards, but random upgrade offers may still take several rolls.

## Quick checks

1. **Almanac > Modifiers > Epic Modifiers.** Find Enchanted Shield and No Pains No Gains. Check the complete descriptions, especially 0.1% healing and the 20-wave condition. Their names should stay unchanged.
2. **Odyssey: Challenges > first page > The Gods: Evolved.** Start a run and inspect upgrade offers. Check “Obtain a new plant”, the selection text, Shield, Respawn, rerolls and Reinforcement-plant wording. Repeated selections should still show changing values and percentages.
3. **Recommended Levels > The Gods: Evolved Purgatory.** Check the initial zombie-modifier choice. The custom option must still explain five rounds and choosing one of five modifiers each round. The random option must retain 50 starting Luck, the 300 cap and five modifiers. Check the selection counter.
4. **In The Gods: Evolved, use Blazer Snipea and roll Firewall/Wildfire upgrades.** The formerly Chinese fragments should follow the plant name in English. Firewall must show +3 links and the instruction to rebuild it manually; Wildfire must retain the additional 2 chain points. Also check the PC names Golden Barrage and Hardened Saw if offered.
5. **Open the multi-save screen you normally use.** With a disposable save, try Start a New Save, Save as New Save, Rename Selected Save and Resume Selected Save. Normal save behavior should match Release 8. Most new save translations are errors/status messages, so they may not appear during a successful save. There is no new backup/restore feature.

## Optional checks

- **The Gods: Evolved Endless:** inspect the bottom round label after entering that variant; the round number should remain dynamic.
- **Odyssey shop / Travel Store:** open the modifier/investment list. Any initial placeholder and its shadow should say “Modifiers”, then be replaced by normal runtime content. Real modifier descriptions must remain intact.
- **Super Level Editor / Note Editor:** check upload status, local import, fusion-tree counts, file status and rhythm playback messages. The previous-subdivision message must display both beat-position numbers. Some actions are keyboard-oriented and some messages are only diagnostics, so these are lower-priority Android checks.
- **Challenge/minigame listings:** if BrickBall/BrickEndless variants are available, their dynamic labels should read Brick Breaker, Brick Breaker 2 and Endless Brick Breaker. Menu placement can depend on the selected list and unlocked content.

Check for clipped text, literal `{0}` placeholders, unexpected Chinese, and successful return to the menu. A screenshot plus the route and selected modifier helps identify the exact field.
