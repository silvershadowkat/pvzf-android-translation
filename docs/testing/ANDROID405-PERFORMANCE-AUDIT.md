# Android 4.0.5 performance audit and local candidate

Date: 2026-10-23. Status: optional performance candidates added to the existing
[prerelease 3](https://github.com/silvershadowkat/pvzf-android-translation/releases/tag/v4.0.5-release-3).
The original downloads remain available. Both candidates were subsequently
installed over the existing S26 apps; performance testing remains outstanding.

[Verified candidate hashes and checks](ANDROID405-PERFORMANCE-BUILD.json).

The user reported slow gameplay and crashes in English builds, including builds
before the runtime bridge. This investigation therefore compares the Chinese
4.0.5 APK, English prereleases 1 through 3, and the Lite project's actual APK
directory. It does not assume the bridge explains every report.

## Verified baseline

- Source baseline: `49818776a1f2c0ddfa5da59bf67711a469b34a24`.
- Published regular APK SHA-256:
  `9200f8dca136ebc754a422b8ff8f843cc1c19b1ad10a60bd12bdda150dc8b97d`.
- Published experimental AI APK SHA-256:
  `be3b8c64f2852d85b10c8cc2b4c391b274bf6c7733f81b92f4f409fad4798e42`.
- [Lite source](https://github.com/Tproplay/Pvz-Fusion-Translation-Lite), inspected
  at `39d000dcf26c9b14f6752553fdf13eff03b5a58c`.
- [Lite 4.0.5 release](https://github.com/Tproplay/Pvz-Fusion-Translation-Lite/releases/tag/v4.0.5):
  its APK changes only `data.unity3d` and `global-metadata.dat` relative to Chinese,
  excluding signing records. Manifest, DEX, native libraries and original music
  resource retain the official CRCs and sizes. It does not include our runtime,
  soundtrack selector, save refresh or touch control additions.

## Changes in this candidate

1. **Skip unnecessary rendering work.** Already-English text bypasses the input
   ancestry checks and translator. The contextual `Disabled` to `Close` exception
   remains eligible, as do Chinese editor ports and custom level labels. Original
   strings are still restored after rendering, preserving gameplay keys.
2. **Cache resolved IL2CPP metadata.** Resolve method overloads and fields once
   per thread/class/signature instead of scanning method metadata repeatedly.
   Scene objects and input ancestry are deliberately not cached this way.
3. **Cache native translation results.** A content-keyed LRU avoids repeat JNI
   translation calls and managed string creation. Strong GC handles keep results
   valid. Eviction releases handles. The cache holds at most 1,024 entries and
   1 MiB of accounted text; container/object overhead is additional. Registering
   custom level text invalidates it.
4. **Bound Java translation caching and filter regex candidates.** The Java LRU
   also has entry and text-byte limits. A conservative necessary literal prefix
   skips impossible regex matches. All rules and their order remain intact;
   alternations, flags and uncertain prefixes fall back to the original matcher.
5. **Reduce UI polling allocations.** Resolve and call two known Unity boolean
   getters directly instead of boxing their results through reflection. Keep the
   existing per-frame visibility timing. Update Projectile Info label children
   only when the button instance/generation or displayed state changes.
6. **Reduce music housekeeping.** Known clips avoid repeated name conversion.
   Scene-wide music diagnostics are excluded by default. Developers can explicitly
   enable `PVZF_MUSIC_DIAGNOSTICS` in CMake when investigating audio playback.
7. **Avoid redundant startup I/O.** Verified, app-private music can reuse a receipt
   containing its expected SHA, size and modification time. New, missing, changed
   or unverified music still undergoes the existing hash/copy verification. This
   is a file-stat optimization, not a content hash on every launch; same-size,
   same-timestamp private audio modifications would not be detected by the receipt.
   It is never used for metadata, almanac overrides, saves or other external files.
   Stop copying/hashing the unused private duplicate of `translations.json`; the
   translator continues reading the unchanged dictionary directly from the APK.
8. **Strip shipped native debug sections.** Keep unstripped bridge binaries in
   the local build workspace for symbolication. Verify every allocated ELF section
   (code, data, relocations, dynamic symbols and build ID) remains byte-identical.
   This saves package/storage space; non-allocated debug data was not running code.

## Findings before the runtime existed

English prereleases 1 and 2 changed three data payloads, while preserving the
Chinese 4.0.5 manifest, DEX and native game libraries. No inherited 3.6.1 or 3.8.1
executable code was found in those builds. Older translation data and font assets
are a separate question and were inspected as assets.

The bundle contains 208,662 objects in each inspected version. The prerelease 3
diff includes translated text, artwork, font assets, four RectTransforms and the
package identity. There are no extra MonoBehaviour instances in the bundle.
All 1,864 changed MonoBehaviour, RectTransform and PlayerSettings objects decoded
successfully. Their field differences are display text, font/layout data and the
product name. Nested `data` changes are exactly 47 modifier names/descriptions;
the one changed `group` field is its title, `New Group`. No gameplay field change
was found in that object comparison.

**Music:** prereleases 1 and 2 replaced 17 recordings while retaining their loading
settings. Several recordings are longer, and `resources.resource` grew from
42,214,624 to 92,838,656 bytes. This is a historical memory/I/O suspect, not proof of
a crash cause. Prerelease 3 restores the original AudioClip objects and loads
replacement clips on demand. Unused tracks are disposed after the existing grace
period. Neither version of the candidate preloads all 17 songs.

**Music follow-up, 2026-10-23:** the Redmi Note 9 tester reports reduced general
lag with the performance candidate, but a remaining delay/freeze when music loads.
This is qualitative feedback, not a measured FPS comparison. Inspection found
that our `set_streamAudio(true)` call cannot resolve: the setter is absent from
the official 4.0.5 IL2CPP metadata/dump, and its registration name is absent from
both ARM64 and ARMv7 `libunity.so` files. The current helper silently returns for
a missing method. Earlier descriptions of confirmed streamed playback were
therefore incorrect. An asynchronous request alone does not establish streaming
or eliminate clip creation/start/seek stalls. The code also assigns/seeks/starts
clips on Unity's main thread and evicts unused tracks after four maintenance
ticks. These are investigation targets, not yet measured freeze causes. The
tester has been asked whether Original music reproduces the issue too. No new
music fix has been built or published from this follow-up.

**Fonts:** both primary English font atlases contain the same 703-glyph tables,
at 4096 by 4096, with 16 MiB of image data each. The original Chinese atlases are
empty on disk and dynamically populate, so a 32 MiB disk difference is not a
measured 32 MiB difference in resident RAM. Both English fonts remain dynamic and
have separate materials, atlas ownership and Chinese fallbacks. Blindly sharing
their mutable atlas or removing fallbacks can break missing-character rendering.
The padded glyph area exceeds a 2048-square atlas. This candidate preserves font
pixels, typography, glyph coverage and fallback behavior. Font repacking or
unifying font ownership needs its own device rendering/memory validation.

**Artwork:** apart from those font atlases, changed textures keep the original
dimensions, texture format and readability setting. Translated textures generally
have fewer mip levels and smaller stored image payloads. The stored byte total of
all textures is not a measurement of simultaneously resident GPU memory.

**Internal metadata keys:** the released English metadata retains the protected
`木桩` and `交易` values implicated in the Lite project's reported enum issue.
Copying its metadata wholesale would lose our contextual translations and is not
a justified fix for the reports here.

## Validation and limits

- Java output parity: 9,172 test strings match the frozen released translator,
  including the exact dictionary, whitespace/markup variants and dynamic fixtures.
- Prefix sampling skips 130,491 of 161,500 potential matcher creations. This is a
  host test count, not an FPS, battery or on-device latency measurement.
- Existing translation, Plantbrush text, managed-file tests and new cache/receipt
  semantic tests pass. Native cache tests exercise eviction, ownership, negative
  results and invalidation, plus the existing reference-field write barrier test.
- All 66 Python tests pass. Actual APK metadata/almanac restoration tests pass for
  both variants, including repeated restoration of stale files, multiple profiles,
  and save/settings preservation. All 17 protected metadata slots pass comparison
  with the Chinese APK.
- Both Android ABIs are built. APK verification checks signing certificate,
  16 KiB alignment, ZIP integrity and the exact changed-entry allowlist.
- Only `classes2.dex`, both `libpvzfenglish.so` files and manifest version fields
  may differ from each published base. All translation payloads, images, music,
  original game libraries, original DEX, models and package identities are retained.

No new device benchmark or reproduction of a tester crash is claimed. The
connected Retroid had no running EN process when inspected; its recent log sample
did not contain the reported app failure. No app was launched or installed for
this audit. Main-menu/profile crashes, low-memory kills and gameplay slowdowns
still need logs and matched gameplay runs on an affected device.

## Local testing

Candidates use version code `4050341`, version name
`4.0.5-English-pre3-performance1`, and the existing release signing certificate.
Regular stays `com.LanPiaoPiao.PlantsVsZombiesEN`; AI stays
`com.LanPiaoPiao.PlantsVsZombiesENAI`. Back up saves, then install over the matching
variant. No uninstall or cross-variant save import is required.

1. Cold launch twice, then test profile selection and naming.
2. Play the same early Gods Evolved stage and settings that previously lagged.
3. Open Tactics, the editor guide and custom levels; check translated labels.
4. Toggle music and Projectile Info, then reload a survival save.
5. On AI only, identify a drawing, leave the mode and return to normal gameplay.

For a useful comparison, use the same device, temperature, refresh rate, stage,
plant/zombie load and game-speed setting. Capture `logcat` and app memory if it
crashes or degrades. A successful smoke test alone does not establish an FPS gain.

Reproduction: `scripts/build_performance_candidate.py --help` documents the local
input paths. The builder pins both base hashes and writes per-variant build
manifests next to the APKs. It never installs or publishes anything.
`scripts/test_runtime_efficiency.py --help` reproduces the Java/cache parity checks
from an APK and the pinned released source revision. Detailed local inventories,
field comparisons and logs are under the task workspace's `work/lite-audit/`.
