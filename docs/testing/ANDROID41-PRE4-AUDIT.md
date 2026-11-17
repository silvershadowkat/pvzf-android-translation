# Android 4.1 pre-release 4 audit

Prepared November 17, 2026 on `agent/translation-4.1-prerelease4` from public pre-release 3. Both normal release variants are included. The local private cheat build is not an input and no cheat code is included.

## Translation sources and counts

Blooms 4.1 branch: `88f68f1538c108941a4531c138ba0a0c44eacd58`. Fourteen English JSON files were fetched at that immutable commit. Main was also inspected at `f7e8b5922ac7233f16afdcc653842e3966d6a5e7`, whose commit explicitly reverts accidental 4.1 changes; the 4.1 branch is the version-aligned reference.

The review in `assets/prerelease4-4.1-review.json` records source text, prior text, English text, field identity and provenance for all 144 changed almanac fields. Every candidate's original Android source matches the corresponding original PC 4.1 source. Matching source IDs alone are not treated as proof that an English description is current: numerical or mechanical conflicts receive context translations from the actual Android prose, using verified Blooms names and terms.

| Change | Plants | Zombies |
| --- | ---: | ---: |
| Entries with changes | 84 | 17 |
| Names | 19 | 3 |
| Gameplay descriptions | 74 | 14 |
| Flavor descriptions | 28 | 6 |

New plant names: Tycoonwood, Longfeng Torcher, Temporal Torch, Cabbage Morph, Scrap-pult, Chrono-pult, Balloon-shroom, Fume Pot, Magnet Squash, Umbrella Squash, Melon Pod, Trinity-shroom, Crush-shroom, Cabbage Pod, Springy-shroom, Stinky Squash, Silver Squash, Golden Squash and Gravi-nut.

New zombie names: Channeler Pozeidon, Giga Dolphin-nut Zombie and Cherrizilla Zombie.

There are also 28 metadata display-literal changes and five full-match equipment rules. The runtime dictionary retains every pre3 source key. Reviewed names are reused in complete display entries at build time. No runtime substring-replacement loop, scene scan, network translator, invented plant identity, recipe or gameplay effect is introduced. Font size tags are removed from imported almanac prose using the existing Android policy.

SP Gatling Doom retains the actual every-16th-shell, six-times-damage and 4.5-second rest mechanics. Speedy-shroom retains 5% attack speed per attack, a 150% cap, fear reset and one damage per 5% bonus. Focused Fire retains the Android half-shots requirement rather than the stale PC minus-three-shots claim. Gravi-nut keeps pre3's source-corrected description and receives verified Smasher and Capacity modifier names.

## Offline recognition

The resident-session policy was already present. A deterministic test reproduced an additional defect: after a 15-second scheduling gap, `Session.run()` tested time since the last reply before sending another status request. It unbound a healthy ready service, and the isolated service deliberately terminates its process on unbind. Thus the reports cannot safely be attributed only to Android reclaiming a background process.

The watchdog now times a real in-flight health transaction, grants fresh time after a scheduling gap, and never treats an idle late callback as proof of failure. Binder work remains off the UI and Unity threads. The bind uses `BIND_IMPORTANT` so the recognition process can inherit foreground importance from the game. It adds no foreground-service notification, wake lock, perpetual restart loop or extra worker. Existing startup and stuck-request timeouts, explicit retry cooldown, genuine critical-memory release and game-exit release remain.

The model, index, plant-only catalog, preprocessing, ranking and ONNX Runtime libraries are unchanged. No ordinary idle, mode-exit or background unload is added. Android may still reclaim the service, and the reporter's exact cause cannot be proved without their device or logs. Do not promise that every phone can keep this memory resident.

Android references: [BIND_IMPORTANT](https://developer.android.com/reference/android/content/Context#BIND_IMPORTANT) and [memory callbacks](https://developer.android.com/reference/android/content/ComponentCallbacks2). Running-critical callbacks are no longer delivered on stock API 34 and later, so a generic claim that this particular reporter triggered that callback would be unsupported.

## Unknown modifier

The pictured Obsidian Jugger-nut entry is `UltiBuff` 52, `堡垒1`. Native `TravelMgr.GetText(object)` returns its unknown-index fallback when its display dictionary lacks that key. Blooms `ultimateBuffs[52]` supplies Obsidian Formation and its description.

One named-method hook first calls the native method, then supplies the verified text only for a boxed `UltiBuff` value 52 whose native result is exactly the Chinese unknown-index string or the existing English Unknown Modifier ID. Valid native text, other IDs and other enum types pass through unchanged. No modifier effect, unlock, numeric value or gameplay dictionary is changed. The fallback uses no per-frame polling.

## Zomboni Fog report

The damage and movement methods are in `DriverZombie`, with body damage at `0x2260038` in the reference arm64 build. The actual damage-state strings, including `shake` and `zombie{0}`, are unchanged in pre3. Code lookup uses metadata names; these addresses are investigation evidence only.

A comparison inspected 58,959 rendering objects between original Chinese 4.1 and pre3. Rendering changes belong to font atlases/materials, menu lettering and translated comic/effect text. Sprite renderers, meshes, animation clips/controllers, shaders and vehicle artwork were not changed. Pre4 changes exactly two TextAssets among all 219,584 Unity objects per variant, leaving the rendering objects unchanged from pre3. The original game native libraries remain byte-identical.

This excludes several obvious port-corruption paths but does not establish a root cause or prove the bug occurs in the Chinese version. No speculative renderer, fog, animation, damage or gameplay patch is included. The reported transition after the first two columns or a dented front bumper remains an open reproduction case.

## Verification

- 79 Python checks pass.
- Real Java translator: 88 screenshot/regression fixtures and 17,346 parity inputs pass; cache, prefix and managed-file tests pass.
- 36 asynchronous bridge checks pass, including the previously failing scheduling-gap case, explicit retries, stale callback isolation and idle/background retention.
- Six production modifier-fallback checks pass for the missing ID, both unknown strings, other IDs/types and existing native descriptions.
- Both Android ABIs compile for EN and ENAI. Package identities, release signing certificate and 16 KiB alignment verify.
- Signed-APK delta checks retain every unlisted entry and its compression method. EN changes nine entries; ENAI changes ten. The normal EN bridge DEX and the ENAI model/catalog assets reproduce their existing bytes.
- All 32 present protected metadata slots remain unchanged, including the Plant Info LF and full-width-colon protocol.
- Actual signed-APK restoration checks cover both variants, default and named profiles, internal/external storage, and repeated restoration of old translation overrides while preserving all player/config fixtures.

Verification is on PC. No phone is installed, restarted or operated for this release. The Zomboni issue and the reporter's ENAI behavior have not been reproduced on their device.

Build with `apply_41_prerelease4.py`, then `build_41_prerelease4.py`, using the immutable matching public pre3 variant, the pinned original Chinese APK and the checked review. Exact artifact hashes and publication evidence are in `ANDROID41-PRE4-RELEASE-BUILD.json`.
