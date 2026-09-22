# Android 3.9 prerelease 6 candidate test gate

Current release: [Android 4.0 English prerelease 1](RELEASE-NOTES-4.0-PRE1.md). Use [the 4.0 upgrade handoff](testing/ANDROID40-PRE1.md) and [build verification record](testing/ANDROID40-PRE1-BUILD.json) for current work. The version-specific examples below are historical. The current APK changes exactly three payloads: Unity text/assets, metadata, and the audio resource. All executable code, permissions, and save logic remain official Android 4.0.


**Historical Release 6 checklist.** Current release:
[Release 7](RELEASE-NOTES-3.9-PRE7.md), approved after the local test3 recheck.
The older "not packaged" status notes below describe their original audit date.

The single running, player-facing draft for changes **after Release 6** is
[RELEASE-NOTES-NEXT.md](RELEASE-NOTES-NEXT.md). Add each completed tester
correction there once, using plain language. The Release 6 test gate below is
retained as background and must not be presented as newly completed work.

Prerelease 6 uses the PC `3.9` branch at
`c2e8f962cb9974c3214d0db95fe98fea0634a2da`. It fixes the dangling Release 5
TMP fallback-font pointers, refreshes current PC Almanac/gameplay text, and
adds targeted regression checks for the reported Almanac failures.

## Required installation order

1. Back up the app's `files` directory.
2. Uninstall the currently installed game.
3. Install prerelease 6 and launch it once.
4. Fully close the game, then restore save/progression files only.
5. Do not restore or modify `il2cpp/`, `global-metadata.dat`, translated
   bundles, mods, caches, or unknown files from the old installation.

Clearing cache is not a substitute: the writable IL2CPP override is under the
persistent external `files/` directory. Never use **Clear storage/data** unless
you intentionally want to erase app data.

## What testers should check

- Compare Android wording against the supplied PC 3.9 English reference.
- Report English present on PC but missing or wrong on Android.
- Report broken fonts, clipping, overlap, bad wrapping, wrong button meaning,
  missing art, context-menu regressions, duplicated modifier text, or crashes.
- Check new saves, settings, Odyssey, Challenge, Zen Garden, Gods Evolution,
  pause, plant selection, regular Almanac, and modifier Almanac screens.
- Confirm the Odyssey key, Return, pause-menu `MENU`, and `LETS ROCK` art.
- Confirm the tool-shop item no longer says `??? (Currently Bugged)`.
- Reproduce the supplied Penny-shroom Almanac sequence and confirm it no longer
  exits to the launcher.
- Browse Cattail Girl, SP Phoenix Threepeater, Quetzalcoatl Blover, and SP
  Phoenix Drone in different orders and confirm every description refreshes.
- Exercise Odyssey modifier selection, Gods Evolution card selection, Solitary
  Spear's zombie-HP toggle, and the reported Torchwood/peashooter combination.

Do not report Chinese text by itself as a defect. Some current PC 3.9 fields
are incomplete and intentionally remain in the official language. For a
translation report, identify the matching PC English text or explain why the
screen is generic UI that can be translated safely without inventing gameplay
terminology.

## Parked feedback for the next fix batch

- Verify the current PC Blooms 3.9 terminology for the Zen Garden fertilizer
  item. Community feedback asks whether **Fertilizer** should be renamed to
  **Super Fertilizer** on Android. Confirm the source wording and every affected
  UI location before changing it.

## Local PC refresh before the next tester fix batch

The completed 2026-09-06 source refresh is documented in
[PC-REFRESH-2026-09-06.md](PC-REFRESH-2026-09-06.md). The current local PC
3.9 input is pinned in `pc-translation-source.json`. This is unpublished work
from release 6; no new APK has been packaged.

## English parity audit and crash-sensitive handling

See [ENGLISH-PARITY-2026-09-06.md](ENGLISH-PARITY-2026-09-06.md) for the
verified local text candidates, deferred UI/context items, provenance rules,
and required device retests. No APK or release has been produced. If a tester
field lacks completed PC English, tell the user it is not translated upstream
yet; do not invent a replacement.
