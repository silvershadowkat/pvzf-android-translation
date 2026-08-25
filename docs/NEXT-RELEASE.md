# Android 3.9 prerelease 6 candidate test gate

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
