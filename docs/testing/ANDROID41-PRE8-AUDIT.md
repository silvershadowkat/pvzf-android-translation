# Android 4.1 prerelease 8 audit

Prepared November 24, 2026 from public prerelease 7 EN and ENAI, independently. Exact input hashes and reviewed source/previous/target text are recorded in `assets/prerelease8-4.1-review.json`. Release results and checksums are in `ANDROID41-PRE8-RELEASE-BUILD.json`.

## Vehicle correction

The public bridge now includes the rendered-root correction from commit `71aff7f`. Prerelease 7 still used its earlier Rigidbody-relative implementation. Several rendered Updates before a physics step could repeatedly apply a stale error to an already corrected body position. The corrected absolute target uses the same rendered coordinate snapshot as the original ground-error calculation, preserving prefab offsets and the game's ground/roof target.

This shared method covers Zomboni, red bobsled vehicle, Michael Zomboni and Jackson Worldwide, including custom levels. It does not replace walking Jackson or Jackson Universe movement. Damage, HP, X velocity, terrain, attack behavior and global time settings remain owned by the game.

See `ANDROID41-VEHICLE-RENDER-SYNC.md` for controlled reproduction, four-variant correction and roof-combat observations, and `ANDROID41-VEHICLE-RELATED-AUDIT-20261124.md` for the wider nine-variant lifecycle audit. Those documents also correct the earlier diagnostic's unavailable interpolation getter: a default zero was not a measurement. Spawn code requests interpolation.

The independent C++ regression was recompiled and executed successfully on Android x86_64 for this release. Both ARM64 and ARMv7 production libraries were rebuilt, stripped with loaded-section equivalence and signed into each edition. Reporter-device reproduction and exhaustive combat coverage remain outstanding; there is no guarantee against every possible disappearance bug.

## Translation review

Blooms 4.1 is pinned to `ab5d1c03ad44ba2039855381b16045fe54519767`, compared with prerelease 7's `c4872b81c7a846c102a47b54683a3a52e20b652e`.

- Reviewed one Balloon-shroom Almanac grammar correction and two fusion-showcase tips. Existing Android stat corrections are retained.
- Updated Gods Almanac/category/upgrade wording and related exact translations. Added a Switch Glove fallback and an anchored custom-level speed-label rule.
- Imported the corrected anchored TGE currency rules. Existing Android aliases remain available.
- Updated nine matching display metadata literals. All 32 present protected parser/runtime slots remain unchanged.
- Excluded the PC plugin changelog because its Languages menu, untranslated-mode notices and server-recognition instructions do not describe Android EN/ENAI.

The screenshot's English Custom Level title identifies a mode, not its build. Its glove, HP-display, menu, start-round, speed, hotkey, difficulty and enemy-count labels are covered by source/exact translations or real Java translation fixtures. The screenshot alone does not prove a missing Android translation or establish a particular vehicle failure sequence.

Both Unity bundles were reopened and all 219,584 objects compared. Only the three allowlisted JSON TextAssets changed; IDs, game data and other objects remain identical. Both APK audits permit exactly eight changed entries: version manifest, managed translation manifest, dictionary, metadata, bundle, plant Almanac and two bridge libraries. Game IL2CPP libraries, DEX, audio and ENAI model/inference payloads remain identical to their matching public prerelease 7 inputs.

## Verification and limits

85 Python checks, 263 Java display fixtures, managed-refresh checks, actual-APK metadata/Almanac restoration tests and final EN/ENAI emulator startup/render checks passed. Both editions refresh language files restored from an old backup while retaining player fixtures. ZIP integrity, preserved compression, 16 KiB alignment and project v1/v2/v3 signatures are checked by the builders. Scanner version/date and physical smoke results are recorded separately in the release build record.

The emulator uses ARM64 native translation; it is not a substitute for 32-bit hardware testing. Custom-level labels have targeted coverage rather than an exhaustive review of player-authored levels. ENAI's model and lifecycle implementation have not changed. Startup-loading experiments remain diagnostic-only and are not enabled in these APKs; no startup-time or combat-FPS improvement is claimed.
