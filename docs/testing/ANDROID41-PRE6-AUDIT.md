# Android 4.1 pre-release 6 audit

Prepared November 20, 2026 from the matching immutable clean public pre5 Standard EN and Offline AI ENAI APKs. Private builds are excluded.

## Text review

The 16 supplied screenshots cover 15 zombie records plus one Gods Almanac heading. The complete embedded and managed zombie name/info/flavor fields were already English in pre5. This does not establish the reporter's version or installation error. Pre6 adds 509 exact display mappings, including complete Ascend headings, verified aliases and complete Chinese zombie field aliases reusing those reviewed English descriptions. No new plant/zombie identities or missing gameplay mechanics are inferred. Ambiguous Ascend names remain deferred. The new Summoner heading has a committed regression fixture.

Blooms branch 4.1 was checked at f5f8a205204c71a6a17bcbe250cad8e80eda3c15, 15 English JSON files. Its new Gods Almanac catalog and formatting changes contain no new English wording. This release does not blindly replace the Android catalog with PC data.

The new Unknown Modifier ID screenshot matches UltiBuff 52 / Obsidian Formation, already fixed in pre4 and retained. Offline AI also retains the pre4 lifecycle/watchdog fix. Neither the AI model, catalog, recognition algorithm nor lifecycle is changed in pre6.

## Vehicle repair

See [the detailed vehicle audit](ANDROID41-PRE6-VEHICLE-AUDIT.md) and [trial results](ANDROID41-PRE6-VEHICLE-TESTS.json). A stock vertical ground-correction instability was reproduced with actual mixed projectiles in base Survival: Fog (Endless). A live damaged Zomboni oscillated hundreds of units off the lawn and stopped receiving damage. Controlled A/B tests reproduced the same instability on both ordinary and red vehicles.

The scoped native fix preserves the stock calculated ground correction but applies it directly to the Rigidbody2D vertical position instead of holding an unstable vertical velocity between rendered frames. The independently confirmed duplicate rear damage-sprite cache is also corrected. Six final-runtime actual-combat trials at 1x/2x/4x passed: both vehicles remained in their lanes and died normally. Two roof slope trials and the Android-native C++ regression passed. Confirmation on affected physical devices is still pending; unrelated bobsled failures may remain.

## Verification

- 79 Python checks passed.
- Actual Java translator: 89 committed regression fixtures plus 509 reviewed exact-key fixtures, 598 total, passed.
- Managed integrity/refresh tests preserved 11 save/settings fixtures and passed eight checks; metadata/almanac restoration passed four and twelve checks per variant on the staged pre6 translation payload. Subsequent rebuilds changed only the native grounding repair; dictionary and restore code are identical.
- Both ARM64 and ARMv7 native bridge builds compile and release-signature / 16 KiB ZIP alignment checks pass.
- Final APK audits permit exactly five changed entries: AndroidManifest.xml, assets/english/manifest.json, assets/english/translations.json, and the two libpvzfenglish.so libraries. Every other entry's bytes and compression match its clean pre5 base, including game native libraries, DEX, Unity assets, metadata, audio and AI data.
- Both public ABIs contain the grounding repair and exclude the diagnostic command/harness markers. No private cheat code is included.
- Clean APK startup checks run only on the task-owned emulator. No phone is installed or launched for pre6.

The supplied recording was reviewed locally. Its Odyssey run has heavily overlapping effects and is not sufficient by itself to identify the installed build or the exact failure frame. The independent instrumented reproduction provides the actionable evidence.
