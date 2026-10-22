# S26 real survival-save and translation-refresh test

Date: 2026-10-21. Package: `com.LanPiaoPiao.PlantsVsZombiesEN`. APK: `PvZ-Fusion-4.0.5-English-Android-prerelease3-test1-r11.apk`, versionCode 4050321. Local only, not published.

## Result

PASS for the readable files tested. Both actual survival save files, player progress and garden data stayed byte-for-byte identical while stale plant-name JSON and metadata overrides were refreshed to the current APK payloads.

| Actual device file | Bytes | SHA-256 before and after | Result |
| --- | --- | --- | --- |
| `level40.json` | 16061 | `b0e7defdd52e180bbdb12a7e3770d80023c949aeea724da630cb82aa9b25c202` | Identical |
| `Player/Saves/level40_9999.json` | 16061 | `9eee4f8ea48ec6ef56d29fd3fa67213b94f14a9fd81bc4120051c52a95a77943` | Identical |
| `playerData.json` | 27183 | `bc9ec7d241e55258e4a0f4f28d00a3c67c24b15a9b00a8cbd4e1be569ffaa492` | Identical |
| `GardenUnifiedData.json` | 111 | `c9cb2e3abaecab7a556bafcdca67d23a7ace6b3bb00557f69b577ccc957b12e5` | Identical |

Both survival files contain structured save data including plants, boardData, travelData, cardOnBank and godData. These are actual player-created files, not test save fixtures. The nested `Player/Saves/level40_9999.json` path is distinct from named profiles under `Saves/<profile>`. The updater preserves both because neither is a managed translation path. Two files do not establish coverage of every possible save mode or slot count.

## Procedure

1. Enumerated the EN external files directory, then stopped the app to stabilize the baseline.
2. Hashed and backed up all 11 readable files locally, including unknown/resource files. No save content was edited or restored.
3. Verified the current `LawnStrings.json` and `il2cpp/Metadata/global-metadata.dat` matched the r11 manifest.
4. Replaced only those two existing translation files with the known seed-r9 fixtures containing `STALE Pea` and `STALE TEST Coins`. Verified that precisely those two paths changed and all other readable hashes stayed unchanged.
5. Reinstalled the current r11 APK with `adb install -r`. Verified every readable external-file hash matched the staged snapshot immediately after installation, before launching.
6. Started the app once. Runtime log confirmed the managed-file refresh and Unity Update. Compared the post-startup snapshot: all nine non-fixture files matched their baseline hashes, and both translation files matched the exact current payload hashes from the APK. No new readable files appeared.

This test reinstalled the same version intentionally. It demonstrates stale content is corrected even without a revision change. The maintainer's earlier manual seed-r9 to main-r9 update separately covered a versionCode increase and confirmed progress/settings retention.

## Scope and limits

Three pre-existing crash tombstones were unreadable through ADB and were not modified. Private Android preferences were not accessible for hashing; their persistence was previously checked by the maintainer. The file comparison proves the tested saved data was preserved. Opening a survival save in-game is the remaining user-facing loadability check.

The local backup is in the task workspace at `work/upgrade405/pre3/s26-survival-refresh-r11/backup`. It is not included in the source review ZIP or committed. Audit snapshots and runtime logs are in the adjacent directory. The repeatable local test script is `work/upgrade405/pre3/check_survival_refresh_r11.py`; its prepare step refuses to overwrite the original baseline.

## Related maintainer confirmations

- Tactic Modifiers no longer crashes on r11.
- No remaining Chinese was noticed in the maintainer's Gods Almanac checks; this is not an exhaustive entry-by-entry coverage claim.
- Projectile Info now looks good, following the earlier successful toggle test.

## Deferred translation audit

After this quick test, inspect Recommended Levels > Super Level Editor > the top-right Chinese button. Its window contains substantial Chinese text, and the close control says `Disabled`. Compare with current PC handling and translations before editing. This batch has been recorded but is not fixed by this save-preservation test.
