# 4.1 English prerelease 1

Local test draft. Do not publish or upload the APK before maintainer testing.

## Updating

- One APK: `PvZ-Fusion-4.1-English-prerelease1.apk`, package `com.LanPiaoPiao.PlantsVsZombiesEN`.
- Back up saves first, just in case. Install over the previous Standard EN build without uninstalling. Managed language files refresh while player data, settings and additional save slots stay intact.
- Chinese RH and the previous AI ENAI app have separate storage. A one-time manual save transfer is needed from their `Android/data/<package>/files/` folder to `Android/data/com.LanPiaoPiao.PlantsVsZombiesEN/files/`. There is no automatic cross-app import. Keep the source copy until the transferred saves load correctly.

## Translation

- Updated to official Android 4.1 and reviewed Blooms 4.1 English data. Existing translated pages, diary artwork and credits are retained where the original assets match.
- Fixed the reported Gods card and almanac gaps: Squash Pumpkin's Ascend and eligibility text, Apocalypse Railgun's Disintegration effect, Melancholy Commando's Penetration effect, Toxicity eligibility, Supremacy-shroom's Impact effect, and Dragonbreath Torcher's Firecracker effect.
- Added verified Blooms records for Artsy Sunflower, Ball Cactus, SP Calamity-shroom and SP Avarice-shroom.
- Context Aware AI, using established game terms, covers the actual 4.1 announcement, clear new plant prose and instructions, shop/save/editor prompts and recognition messages. Unverified specialized names remain Chinese.
- Restored Android almanac description sizing. Fixed Odyssey shop node/bench/HP/interest/refresh labels and Super Stacking research, recycling, inventory, tiered item names, checkpoints and its full help page. Prevented research bonuses from triggering an incorrect fusion-discovery banner.
- Expanded Odyssey: Evolved's difficulty, shop, leader preview, card-stat and counter text, Super Stacking's shop/tutorial text, and Magic Plantbrush's instructions. Removed its outdated "Untranslated" label.

## Runtime and controls

- Dynamic cards, eligibility text, styled UI and downloaded level labels still use exact or bounded display translation. Complete mixed-language keys are prepared at build time. Gameplay identifiers are preserved.
- Music uses Unity's original decompressed playback with background loading. Inactive decoded music is released when tracks change. Soundtrack changes require closing and reopening the game, with a notice using the game's own popup style. This replaces the separate Android players and the first 4.1 candidate's compressed streaming.
- Fixed the missing music selector by using the settings column's actual manually positioned layout. The separate Screen button derives rendering dimensions from the current display and restores the captured default when toggled back. No automatic stretching or fixed 1080p override.
- Projectile Info touch access and customizable button positioning remain available.
- Removed our Magic Plantbrush launch blocker and offline recognizer. The mode now uses 4.1's official online recognition service. It needs internet and depends on that service being available.

## Quick test

1. Update an existing EN install. Confirm progress, music choice and every extra save slot remain, then load a save.
2. Open Settings from the main menu and a paused level. Check Back, both selectors and their layout.
3. Compare menu, pool and Gods music, including wave transitions. Change soundtrack, restart and confirm the choice persists. Check for cuts, unexpected restarts or volume jumps.
4. Toggle Screen to Stretch and back on the target phone/tablet. Check touch alignment and settings layout.
5. Check the listed Gods modifiers, new plant records, 4.1 announcement and translated artwork.
6. Enter Magic Plantbrush, draw and identify with internet, then leave and reopen it. Report any server/network failure text separately from a game freeze.

This is a local candidate. Host/package checks do not establish long-session performance on lower-memory devices.
