> Current release candidate: prerelease 3 r20, approved by the maintainer on 2026-10-21. See [the final audit](ANDROID405-PRE3-FINAL-AUDIT.md) and [release notes](../RELEASE-NOTES-4.0.5-PRE3.md). The revision-specific notes below are historical; do not install an old seed over the approved build.

> Latest main candidate: **revision 11**, installed over r10 on S26 at explicit request. Startup reached the main-menu changelog and playerData.json stayed identical across installation. Revision 10 has a confirmed Tactics crash. Revision 11 corrects managed-reference writes and Projectile Info visibility/layout. Read [the runtime fix review](ANDROID405-PRE3-RUNTIME-FIX.md); device validation is pending. Manual r9 update preservation and r10 clean startup were confirmed previously.

# Android 4.0.5 prerelease 3: local review

Prepared 2026-10-21. Local test candidate only, not published. The maintainer confirmed live music switching and persistence before the settings layout regressions. Revision 9 removes the experimental column reflow. Full gameplay, multiple-save update and additional screen-size checks remain pending.

## Scope and compatibility

The app ID changes from `com.LanPiaoPiao.PlantsVsZombiesRH` to `com.LanPiaoPiao.PlantsVsZombiesEN`. Android treats it as a separate application. It can coexist with RH, but cannot update RH in place or read RH's private saves automatically. A one-time manual save/settings transfer is necessary to continue existing progress. Keep RH installed until that transfer is verified. Do not transfer the `il2cpp` directory or translation caches.

Private Android preferences may require one-time manual re-entry if the chosen backup method cannot export them. The refresh fixture verifies updates within EN, not migration from RH.

Subsequent EN builds must retain this app ID and signing key and increase versionCode. Android then retains app data during installation. The runtime refresh changes only explicitly managed translation files. Revision 5 enumerates immediate directories under `Saves` to locate each profile's language overrides; it never reads, rewrites or deletes player-save contents or unknown files. This preserves multiple mode saves without assuming their formats.

## Exact source changes

| File | Change and reason |
| --- | --- |
| `.gitignore` | Allow the new `runtime` source tree to be tracked. |
| `runtime/CMakeLists.txt` | Build a C++17 Android library with statically linked, pinned Dobby for arm64-v8a and armeabi-v7a. Limit build jobs to two, build ABIs sequentially. |
| `runtime/english.cpp` | IL2CPP display translation hooks, integrated projectile-info button, settings music selector, and lazy local audio switching. Method/field lookup uses reflection names, not game-specific offsets. |
| `runtime/field_access.h`, `runtime/tests/FieldAccessTest.cpp` | Separate reference/value write conventions, compile-time pointer guard, and host ABI regression tests for the revision 11 crash fix. |
| `runtime/java/com/silvershadow/pvzf/EnglishActivity.java` | Small bootstrap Activity before Unity. Verify/refresh known metadata overrides and managed assets on a worker thread. Load translation rules and start runtime once. Store music preference in its own SharedPreferences. Show a startup error if preparation fails. |
| `runtime/java/com/silvershadow/pvzf/ManagedFiles.java` | SHA-256 verified, temporary-file and atomic-rename replacement constrained to app-owned paths. Reject traversal and symlink aliases. Do not remove the previous file on verification/rename failure. |
| `runtime/tests/ManagedFilesTest.java` | Fault, repeat-run, path-boundary, and save-preservation tests. |
| `runtime/tests/RestoredMetadataTest.java`, `RestoredAlmanacTest.java` | Use the actual APK pair to restore stale metadata and plant-name JSON repeatedly, including internal/external roots and named profiles. Verify current hashes, preserved save fixtures and strict language-file allowlisting. |
| `runtime/tests/RegexReview.java` | Compile every Java regex and check replacement capture references. |
| `runtime/tests/TranslationTest.java` | Exercise the actual translator: exact/capture matches, whitespace, mixed-language multiline panels, line endings, unknown text, no substring substitution, English and null inputs. |
| `scripts/runtime_apk.py` | Structured binary AndroidManifest/resources edits plus the single DEX application-ID constant update and DEX checksum repair. |
| `scripts/prepare_runtime_payload.py` | Build PC-derived display dictionaries, retain reviewed Android corrections, restore original soundtrack records/resources, change Unity PlayerSettings product name (and exact application-ID fields if present), and generate a stale-metadata fixture. |
| `scripts/audit_runtime_payload.py` | Independently compare every serialized Unity object, package references, launcher and permissions. |
| `scripts/build_runtime_apk.py` | Compile, package, sign and validate both local APK variants. Enforce input hashes, Dobby source archive, protected metadata and original-native invariants. Emit per-build inventory and hashes. |
| `THIRD_PARTY.md`, `CLAUDE.md`, this review and quick-test guide | Attribution, current handoff and review/test instructions. |

No game source assembly was recompiled. No original game native library was changed. The added native library hooks eight feature functions plus two initialization entry points at runtime, which requires device validation.

## Runtime hooks

| Target | Behavior |
| --- | --- |
| `TMPro.TMP_Text.ParseInputText()` | Translate rendering input, invoke the original parser, restore source text and input mode. Keep identifiers read through the text property in their original language. Skip editable input fields. |
| `UnityEngine.UI.Text.OnPopulateMesh(VertexHelper)` | Temporarily translate the rendering text, call original, restore source. Skip editable input fields. |
| `UIButton.OnClicked()` | Handle only objects named `EnglishProjectileInfo` and `EnglishMusicSelector`; delegate other buttons unchanged. |
| `InGameUI.Start()` | Call original, clone the plant-HP button hidden into its existing grid, clear copied actions and follow the health control's visibility. Register the new collider when it becomes visible. |
| `OptionMenu.Start()` | Call original, resolve the verified `Buttons/Almanac` hierarchy, validate its UIButton, clone its style, clear copied actions and refresh collider registration. Derive a free slot between neighboring controls from their RectTransforms. Inherit parent Canvas, anchors, pivot and scale. Refuse placement if the gap cannot fit the button plus margin. |
| `GameAPP.Update()` | Call original. Mark active text dirty once after hook startup. Every 250 ms update music and projectile-button state. |
| `GameAPP.PlayMusic(MusicType)` | Temporarily silence only the two music sources before the original starts a track when Blooms is selected; immediately start replacement loading. Restore volume on success, failure, unsupported track or Original selection. |
| `UnityEngine.AudioSource.set_volume(float)` | While either tracked music source is temporarily silenced, retain the game's requested volume and keep that source at zero. All other sources pass through unchanged. Restore the latest requested volume after loading. |

Revision 2 preloads libil2cpp without initializing it and hooks the exported il2cpp_init / il2cpp_init_utf16 entry points before starting Unity. Feature hooks are installed only after successful initialization returns, on Unity's already-attached thread. The assembly-count polling worker and its premature thread attach were removed. Initialization remains once per process. Expected classes/APIs are checked, and original methods remain responsible for normal game behavior. See ANDROID405-PRE3-STARTUP-FIX.md for the confirmed revision 1 crash.

The first game update also checks existing scene menus, including inactive ones, in case their Start methods ran before hook installation. Named-child checks prevent duplicate controls. Prefab assets are not included in this scan.

### Translation coverage

The payload contains 6,032 exact display mappings and 603 full-match regex rules. These are dictionary counts, not a claim that 6,635 previously missing screens were fixed. It includes pinned PC text plus unambiguous, already-reviewed Android 4.0.5 metadata corrections. Existing prerelease 2 metadata is unchanged in the main APK.

Tactic group names receive display mappings derived from matching PC modifier records, including Android aliases `裂空` and `全能`. Tutorial/hint labels, stage names, modifier descriptions and composed text can translate when a complete rule matches. Internal group IDs, puzzle/resource keys and save keys remain unchanged. PC font-size overrides are removed to retain Android layout sizing. Unknown strings stay as supplied by the game. A bounded 2,048-entry cache avoids repeated regex work for repeated text.

If a whole panel has no match, individual lines use the same complete-match rules. This handles English headings surrounding Chinese effect lines without replacing arbitrary substrings. Original LF/CRLF line endings are retained.

`BUFF_NAME_FORMAT` is excluded because it is a PC layout template rather than a regex. `translation-coverage.json` records this and the exact tactic provenance. This does not guarantee that every Chinese string is covered: images, custom rendering and unmatched or differently composed strings require screenshot review.

### Projectile information

The new left-side control toggles `Board.showBulletDamage`, the state changed by the game's projectile-information hotkey. Turning it on also enables `GameAPP.config.showBulletDamage`. It does not modify `GameAPP.config.damagePop`, the separate damage-number popup option.

The button uses the existing HP button style and parent layout. It inherits the existing left-button group position and scale settings, rather than adding a separate position preference. Its label is two lines with automatic font sizing. Existing HP actions are removed from the clone. The integration currently targets `InGameUI`; the separate `InGameUI_IZ` UI has no matching HP template and is not independently extended.

### Music

The settings button toggles `Music: Blooms` and `Music: Original`. Blooms is the default, matching prerelease 2's soundtrack choice. Selection is stored separately from game settings. Switching is implemented live, retaining playback state and clamping the playback time to the new clip. If a replacement cannot load, the original remains available.

The Android player strips persistent-event inspection APIs. The selector uses the verified Buttons/Almanac template and Buttons/F slot. The original F control calls SetResolution with fixed 1920 by 1080 dimensions, which stretches the S26 display. Revision 9 deactivates that control and its PC fullscreen caption, placing Music in exactly its slot. It copies anchors, pivot, size, scale and local position from F. Existing lower controls and their confirmation captions retain their original transforms and event handlers. The revision 6 to 8 column reflow has been removed after missing-button and press-animation regressions. Other aspect ratios still need physical-device testing.

Revision 4 also prevents the original track from being audible while Blooms loads. This player strips AudioSource.mute, so the guard uses its available volume setter and preserves volume changes made during loading. Only music and musicDrum are held. Local audio requests have a 15-second timeout plus an elapsed-time fallback, after which the original track is restored. Startup silence, live transitions and volume controls still require listening checks on the phone.

Seventeen matched tracks are provided: Boss2, Day, Day_drum, Fog, Fog_drum, Garden, IZ, MainMenu, Night, Night_drum, Pool, Pool_drum, Roof, Roof_drum, Roof_pre, SelectCard and UltimateBattle. Gameplay sound effects and unmatched tracks retain their original audio. Original AudioClip records and their matching resource file are restored together. PC audio is loaded from app-private files through local Unity audio requests. Only currently used tracks are retained, with unused requests/clips released. Live transitions, drum synchronization and memory behavior still need phone testing.

## Storage and package changes

| Location | Action |
| --- | --- |
| `AndroidManifest.xml` | EN package, English app label, prerelease 3 version, bootstrap launcher Activity. Original Unity Activity remains the game entry and is launched explicitly. No new permissions or shared UID. |
| `resources.arsc` package header | RH to EN; retain existing resource IDs. |
| `classes.dex` BuildConfig application-ID string | RH to EN, same encoded length; repair SHA-1 and Adler-32. Existing Java class namespaces remain RH because they are class identities, not storage paths. |
| Unity `PlayerSettings` | Change productName from PlantsVsZombiesRH to PlantsVsZombiesEN. This build has no full application-ID field in PlayerSettings. |
| Own external/internal `files/il2cpp/Metadata/global-metadata.dat` | If an override exists, verify against this APK's metadata and atomically replace only that file if stale. The test seed also creates an external override when absent. |
| Own external/internal `files/{LawnStrings,ZombieStrings,DetailStrings}.json` and `files/Saves/<profile>/{same three names}.json` | Revision 5 refreshes existing almanac overrides using the exact English TextAssets extracted from the current bundle. Enumerate immediate profile directories only and reject symlink aliases. No recursive save traversal. Main leaves absent overrides absent; seed creates LawnStrings fixtures in external default/existing profiles. |
| Own internal `files/english-runtime/` | Verify and maintain the listed 17 music files, dictionary and third-party notice. |
| Own `english-runtime` SharedPreferences | Record completed revision and soundtrack preference. |

The resulting external game directory is `/Android/data/com.LanPiaoPiao.PlantsVsZombiesEN/files` (lowercase `files`). Internal storage is assigned by Android for the EN package. The refresh runs before Unity opens metadata and verifies actual hashes each launch, including a stale override restored later. A failed file replacement retains the previous file and stops startup; it does not launch with an unverified override. The update is atomic per managed file, not a single transaction across all files. Retries reverify each file.

### Revision 5: restored plant names

The Android ARM64 `AlmanacDataLoader.LoadPlantData` calls `SaveInfo.GetDataPath`, appends `LawnStrings.json`, and can read that file instead of the `LawnStrings` resource when `GameAPP.almanalTextSafe` is enabled. Zombie and detail loaders similarly use `ZombieStrings.json` and `DetailStrings.json`. `GetDataPath` uses persistentDataPath for the default Player profile and persistentDataPath/Saves/playerName for named profiles. `GetName(PlantType)` calls GetPlantData and reads PlantInfo.name. This is a distinct stale-language source that metadata refresh alone does not cover. Evidence is in `almanac-source-trace.json` and the retained disassembly; unrelated speculative literal matches in that trace are not used as writable paths.

The revision 5 seed changes only plant seedType 0's display-name field from `Peashooter` to `STALE Pea` in its embedded LawnStrings TextAsset and its exported JSON fixture. Plant IDs, enum values, descriptions and recipes are unchanged. Its existing `STALE TEST Coins: {0}` marker remains in IL2CPP global-metadata.dat. The main APK contains neither marker. Phone testing must check both labels and actual override hashes; seeing a label alone cannot prove which source supplied it.

## Build inputs and artifacts

- Official Android 4.0.5 SHA-256: `2c200c6eef6ecfb6cfe2554125cf1f52ba74dab1f037594c8591903ee53ef9f6`.
- Published English prerelease 2 SHA-256: `3a2318c29d6da4ed8a2f7f7a1017f6c766c16f471cd6f8c2eae7aaf66863899d`.
- PC 4.0 translation commit: `94b9ec0aecc3cea494c5b2c2883a7cbf14642440`. Upstream branch was checked during this task.
- Dobby: `21f07a5ce184cda9346afb8009c07fe7e47390d0`, Apache-2.0, unmodified Android-compatible source. Source archive SHA-256: `d39de3241ffef216e5e07ae9587c1f2502a747577948070e6203c3390b8491c6`. Builder checks every archived source file before compilation.
- Toolchain: JDK 11.0.12, Android SDK/build tools 35, NDK 25.2.9519653, CMake 3.22.1, Java bytecode target 8, minSdk 22, targetSdk 35.
- Existing project signing certificate SHA-256: `1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6`.

`build-test1-r5.json` and `build-seed-r5.json` beside the APKs contain final hashes, sizes, entry inventories and managed-file hashes. The revision 5 main versionCode is 4050309. The seed is 4050308, deliberately lower to permit a normal update from seed to main.

The main APK changes five existing ZIP entries: AndroidManifest.xml, resources.arsc, classes.dex, data.unity3d and resources.resource. It adds classes2.dex, one runtime library per ABI, and the English asset directory. The seed additionally changes the Peashooter display name in its LawnStrings TextAsset and exported JSON, and the metadata label at string-literal index 19151 from `God Coins: {0}` to `STALE TEST Coins: {0}`. It is a test fixture, not a release candidate.

## Validation and release gate

Both APKs are checked for ZIP integrity, alignment, v1/v2/v3 signatures, expected certificate, exact changed-entry allowlist, unchanged original native libraries, and protected metadata. Java tests exercise stale replacement, unchanged-file skip, hash failure, atomic-rename failure, retry, save preservation, path escape rejection and temporary-file cleanup. Eleven save/settings/unknown-file fixtures remain byte-identical. All 603 regex rules compile and their capture references validate.

All 66 existing repository tests and eight display-translation behavior checks pass. The independent audit compares 208,662 serialized Unity objects: only 17 AudioClip records and the PlayerSettings product name change. Every other object is byte-identical. The audit finds no old full RH package identifier in bundle objects or native libraries, confirms unchanged permissions and a single launcher, and confirms the main metadata remains identical to prerelease 2.

Revision 5 additionally passed four actual-APK metadata restoration checks and twelve actual-APK plant-almanac restoration checks, including repeated restoration after a successful refresh, two storage roots and default/named profiles. Save fixtures remained byte-identical, absent overrides stayed absent, and non-language filenames were rejected. The seed/main bundle comparison examined 208,662 objects and found exactly one additional changed TextAsset, LawnStrings, for the name fixture. See `restore-verification-r5.json` and `seed-bundle-audit-r5.json`.

See `audit.json` and `unit-tests.log` for the earlier independent main-payload audit and repository tests. These host checks do not verify ARM execution, touchscreen placement, scene changes, save compatibility after manual transfer, or live music. Follow `ANDROID405-PRE3-QUICK-TEST.md` before approval. Do not publish this build until the maintainer approves device results.

## Rebuilding and future updates

Run `prepare_runtime_payload.py` with explicit `--base`, `--official`, `--pc`, `--work`, and `--dlls` inputs. Use `--rebuild-bundle` after changing bundle logic; normal resumption reuses the prepared bundle. Place the pinned Dobby archive at `<work>/dobby-android-source.zip` and its extracted source at `<work>/Dobby-android`. Then run `build_runtime_apk.py` with explicit base/official/work/output/SDK/JDK/signing-directory arguments and `--revision 5` with `--variant test1` or `--variant seed`. Signing passwords are read from the existing local signing properties and passed by environment, never stored in source or build logs.

Run `audit_runtime_payload.py` against the same work directory, base APK, output directory and aapt2 executable. After building both variants, run `RestoredMetadataTest` and `RestoredAlmanacTest` from `<work>/java-tests`, passing `<work> <seed.apk> <main.apk>` to each Java main class. These tests use the actual APK payloads, not substitute strings. Retain the build JSON, coverage report, audit and test logs with the candidate. `source-review.zip` contains this change's source files and documents; `source-inventory.json` supplies their hashes and the starting Git revision.

For a future game release, stop on changed input hashes and re-audit the Android shell, Unity version, reflected class/method/field names, UI templates, exact writable metadata path, audio names and PC mappings before updating the pins. Preserve the EN package and signing certificate, and increase versionCode. Do not assume these hooks or metadata files are compatible with another game version. No release/upload command is part of this build procedure.
