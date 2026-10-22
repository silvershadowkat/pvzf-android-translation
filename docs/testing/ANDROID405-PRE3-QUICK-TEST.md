> Current downloads: prerelease 3 regular EN and experimental AI ENAI, updated October 22. Use [the current AI checklist](PLANTBRUSH-AI-EXPERIMENT.md) for the drawing mode and [release notes](../RELEASE-NOTES-4.0.5-PRE3.md) to choose an APK. The r20 and earlier seed/revision instructions below are historical; do not install an old seed over current player data.

> Latest results: Tactics and Projectile Info passed the maintainer's checks. Real survival-save file preservation and stale-translation refresh passed on S26. See [save-test evidence](ANDROID405-PRE3-SAVE-TEST.md). Next: load an existing survival save in-game.

> Latest main APK: **PvZ-Fusion-4.0.5-English-Android-prerelease3-test1-r11.apk**. Installed on S26 over r10; startup checked. See [the runtime fix checklist](ANDROID405-PRE3-RUNTIME-FIX.md) for Tactics, plant-selection visibility and Projectile Info label checks. Do not repeat the crash on r10.

# Prerelease 3 quick phone test

The maintainer already completed the seed-to-main-r9 label/progress test and confirmed r10 clean startup on S26. Do not repeat the seed installation on that phone. Main-r11 is now installed over the existing English app at the maintainer's request. No uninstall or data clear is needed.

These are local test APKs. The new English app has its own EN package and cannot update prerelease 2's RH app directly. Keep the old app and its saves until migration is verified. No automatic cross-app import is implemented.

## Fresh fixture testing only: stale-translation refresh

1. Install `PvZ-Fusion-4.0.5-English-Android-prerelease3-refresh-seed-r9.apk` FIRST. It uses the separate EN package and leaves RH installed.
2. Open the Gods Almanac. Confirm the currency caption says **STALE TEST Coins**. In the plant/fusion almanac, find Peashooter and confirm its display name says **STALE Pea**. Report either missing marker before continuing.
3. In EN, change a setting and make recognizable progress. If practical, create two saves in a mode supporting multiple slots. Note or screenshot their names/progress.
4. Close the game. Install `PvZ-Fusion-4.0.5-English-Android-prerelease3-test1-r10.apk` over the seed. **Do not uninstall, clear storage or restore a backup between these steps.**
5. Open the Gods Almanac again. It should say **God Coins**, and the plant/fusion almanac name should return to **Peashooter**. Confirm the changed setting, progress and every test save slot remain. Close and reopen once more.

For the technical check, also record SHA-256 of the EN metadata override and LawnStrings.json before/after installation, and compare them with the matching build manifest. Then, with the app fully closed, restore the seed copies of those two language files only and relaunch the main APK. Both should be repaired again even though the installed version has not changed. Repeat for a named profile if available. Do not restore or modify player-save files during this check.

The seed has a lower versionCode, so do not install the main APK first if you want this test. The seed is intentionally stale and should not be shared as the final build. A standalone `stale-test-metadata.dat` fixture is also supplied for technical inspection, but the two-APK sequence is the simple test.

## Quick feature checks

1. **Translations:** browse Gods Almanac tactic headings, levels and maximum-tier dialogs, then plant/reinforcement/other/apex modifiers. Open a puzzle from its translated label and verify the correct level loads. Report remaining Chinese with screenshots.
2. **Music:** listen at startup for a clean Blooms start without a brief original-track snippet. Open settings and tap Music: Blooms / Music: Original. Listen for both choices on the menu and in a normal level. Switch during playback and after pausing. Verify no restart is needed, no duplicate music plays, and your choice survives closing/reopening. Some unmatched tracks intentionally remain original.
3. **Projectile Info:** in a normal plant level, use the new left-side button. Check On/Off actually changes projectile information. Separately toggle damage-number indicators in settings and verify those remain a distinct feature. Confirm neighboring HP buttons still work.
4. **Layout:** check Music occupies the former Screen Mode slot at the top right, without overlap. Screen Mode and its PC fullscreen caption should be absent. Existing controls must stay in place after tapping and closing dialogs. Check on a smaller landscape phone and a tablet when available; S26 alone cannot validate every aspect ratio. Change the existing left-button position and scale settings. Confirm the new button moves/scales with that group without covering other controls. Open/close settings and dialogs to check clicks do not pass through to buttons behind them.
5. **Stability:** enter and leave a few modes, return to menu, reopen settings, switch music several times, and relaunch from the Android icon. Watch for hangs, crashes, audio loss and clipped text. The separate I, Zombie UI is not independently extended with the projectile button.

## One-time move from RH

After the above test, use your established manual backup/restore method to move player saves and settings from RH to EN. Android storage restrictions may require a computer or a supported export/import method. Preserve all mode directories and save slots, but do not copy `il2cpp` or translation caches. Verify the imported progress in EN before removing RH. Future same-package EN updates should be installed directly over EN without uninstalling.

Settings held in RH's private Android preferences may need to be entered again once if your backup method cannot export them. The seed-to-main test checks preservation within EN, not a cross-package import.

Send back: phone model, seed-to-main result, whether all saves/settings survived, whether both new controls work, and screenshots of clipping or remaining Chinese. Include the exact APK filename if reporting a crash.
