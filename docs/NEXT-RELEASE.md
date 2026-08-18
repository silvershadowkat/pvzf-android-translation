# Android 3.9 prerelease 5 test gate

Prerelease 5 uses the latest PC `3.9` branch at
`d150f6f0d5ea16622c4e0b5ee6ce798d60e9c5d1`. It preserves the tested Android
3.9 fixes while refreshing current PC Almanac and gameplay text.

## Required installation order

1. Back up the app's `files` directory.
2. Uninstall the currently installed game.
3. Install prerelease 5 and launch it once.
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

Do not report Chinese text by itself as a defect. Some current PC 3.9 fields
are incomplete and intentionally remain in the official language. For a
translation report, identify the matching PC English text or explain why the
screen is generic UI that can be translated safely without inventing gameplay
terminology.
