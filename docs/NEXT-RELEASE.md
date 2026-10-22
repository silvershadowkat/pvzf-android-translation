# Current release and historical test gates

October 22 update: prerelease 3 now has two downloads, regular EN and experimental AI ENAI. Read [the AI experiment](magic-plantbrush-prototype.md) and [current test checklist](testing/PLANTBRUSH-AI-EXPERIMENT.md). Only the experimental APK enables Magic Plantbrush. AI device testing is limited to the S26 Ultra and Retroid Pocket Nova, with no guarantee for other chips. Both APKs include the latest shared display audit. ENAI saves are separate and are not imported automatically. The older audit/hash records below describe previous build milestones; current hashes are in the release assets.

Current release: [Android 4.0.5 English prerelease 3](RELEASE-NOTES-4.0.5-PRE3.md). See [the final audit](testing/ANDROID405-PRE3-FINAL-AUDIT.md). This version adds an Android runtime, changes the package to EN, and retains the original game native libraries unchanged. It is no longer a data-only translation patch. Use the exact prerelease 3 changed-entry inventory and signature record when auditing it.

Back up saves first. RH to EN requires a one-time manual save transfer; subsequent EN updates install in place. Do not uninstall or clear EN data for normal updates. See the release notes for both paths.

The remaining sections describe historical releases and their original audit gates, not the current package identity or update procedure.

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
