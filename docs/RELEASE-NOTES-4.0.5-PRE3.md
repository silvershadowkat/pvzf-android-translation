# PvZ Fusion 4.0.5 English Android: Prerelease 3

## Runtime changes

- **Update without wiping, requested by our testers:** Future updates within the new English app can install over the existing version. Startup replaces stale managed translation files with current English files while preserving saves, extra save slots, player data and settings. **Back up your saves first, just in case.** Moving from prerelease 2 requires the one-time transfer below.
- **More English at runtime:** Added display translation for text assembled while playing, including Gods modifiers, formatted descriptions, editor labels and supported online-level titles/tips. Original lookup keys and saved level data stay intact.
- **Music selector, requested by S.O.R.O.B:** Switch between Original and PC Blooms music in Settings without restarting. The choice is remembered. It replaces Screen Mode, which could stretch the Android display.
- **Projectile Info, requested by ClarkStacks:** Added an in-game button for the T-key function. It appears with the gameplay controls, supports UI positioning and uses text sized to fit.
- **Runtime stability:** Corrected startup ordering and managed-reference handling to address startup and Tactics crashes found during testing. Removed the small preparation text before the game logo.

## One-time save transfer

The English app now uses **`com.LanPiaoPiao.PlantsVsZombiesEN`**, allowing it to coexist with the Chinese game.

Copy your backed-up save/player-data files, keeping their folder structure:

**From:** `/Android/data/com.LanPiaoPiao.PlantsVsZombiesRH/files/`

**To:** `/Android/data/com.LanPiaoPiao.PlantsVsZombiesEN/files/`

Do not copy the `il2cpp` folder or translation caches. Keep the old app until your transferred saves load successfully. Some settings may need to be entered again. If you already use an EN prerelease 3 test build, install this update over it.

## Translated pages and text

- **The Gods:** Expanded Almanac modifier/tactics text, difficulty and reward cards, shield explanations, and save/reward messages.
- **Super Level Editor:** Translated the Creator Guide and help for 241 event-node types, plus templates, fields, validation messages and connection help. Corrected “Disabled” close buttons to “Close” and the suggested template name to “My Rule.”
- Updated plant, zombie, modifier and tutorial wording from the reviewed PC Blooms translations.
- Completed startup announcement wording, ZombiesTD Day/Pool/Evolved opening banners, supported online custom-level titles/tips, and I, Zombie credit headings.

Missing guide/UI wording was translated with **Context Aware AI**, using verified game and PC translation terminology.

## Images and other fixes

- Translated **all four Adventure Extra diary pages** into English, preserving the parchment style.
- Updated the **Help/Credits parchment**, including the PVZ Fusion Fans Discord testers and modders who provided guidance.
- Fixed the **Magic Plantbrush (paintbrush mode) freeze** when selecting its unavailable Android entry. It now shows a temporary message and leaves the menu usable. The mode itself remains unavailable; no AI service is included.
