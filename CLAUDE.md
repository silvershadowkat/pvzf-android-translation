# Publication checkpoint: Android 4.0.5 prerelease 3

Published and verified on 2026-10-21 after explicit maintainer approval. The prior local-only restriction is revoked. The existing prerelease3.apk was published unchanged, SHA256 9d10eb7b8082ac27b9530a526f9cffb7dcfc0a1e27011e2951054a6a70810b5c, as v4.0.5-release-3. Release URL: https://github.com/silvershadowkat/pvzf-android-translation/releases/tag/v4.0.5-release-3. Source tag points to 00b402717072a0fc574deabc71fa14def07cb3fa. Release notes are docs/RELEASE-NOTES-4.0.5-PRE3.md. All three uploaded asset hashes were verified. Default Player renaming was investigated only and is not included. User will initially share the public link privately with mods. No Discord posting authorized.

Earlier checkpoints below describe historical local-only states. Consult the release build record for completed publication status.

# Maintainer handoff for Claude and other coding agents

## Latest checkpoint: local prerelease 3 r20 (2026-10-21)

Local prerelease 3 r20: 232 exact display translations and nine formatted rules; all four English diary pages and corrected PVZ Fusion Fans credits; narrow Magic Plantbrush unavailable-message fallback. All earlier prerelease 3 runtime, music, projectile UI and managed-refresh work retained.

Both ABI builds, signature/alignment/package/native integrity, eight managed-refresh checks preserving 11 fixtures, 624 regex checks, 17 base display checks and 1,203 expanded translation fixtures passed. Artwork comparison: exactly two of 208,662 serialized objects changed. Final APK payload hashes match audited inputs.

r20 installed in place on S26 (R5GL14CN45N). Runtime initialized; all nine readable nontranslation files, including both survival saves and player/garden data, remained unchanged through installation and startup. Existing managed overrides match the APK. Feature/UI smoke checks and private settings verification still need user testing. Check Magic Plantbrush notification/fading/navigation, diary page placement and credits, editor text fit and an existing survival save. Residual CJK includes aliases, internal identifiers, diagnostics and unverified terms. No claim of exhaustive live-screen coverage.

User explicitly requested a local build only. Nothing published, pushed, tagged or committed. Installable filename: `PvZ-Fusion-4.0.5-English-Android-prerelease3.apk`. Version code 4050339; SHA256 `9d10eb7b8082ac27b9530a526f9cffb7dcfc0a1e27011e2951054a6a70810b5c`. Internal test1-r20 is byte-identical. Latest installed S26 build is r20; feature checks remain pending. Do not uninstall EN, clear data, reseed or touch the Retroid.

Active source workspace: `C:\Users\plim\Documents\Codex\Projects\Plants-Vs-Zombies-Fusion\source\pvzf-android-translation`; branch `agent/translation-4.0.5-prerelease3`, base `68dec6e20c84588ef12eb17d6a7e72286278085e`. Working changes are uncommitted. Detailed evidence: `C:\Users\plim\Documents\Codex\2026-09-06\https-github-com-silvershadowkat-pvzf-android\work\upgrade405\pre3\final-audit-r20` and sibling `art-r20`, `package-test1-r20`, `magic-plantbrush-audit`.

Read docs/testing/ANDROID405-PRE3-FINAL-AUDIT.md first, then earlier review/coverage/guide/editor/save-test notes as needed. PC overlay remains c7fb5997d65e1d5248f3d7a9ca9c9e0a4b516640. The runtime base has its older separately recorded pin.

Layer order: previous r19 payload, apply_parchments_405.py, translate_final_ui_405.py, build_runtime_apk.py variant test1 revision 20. Keep reviewed source assets and manifests from source-review.zip. Do not rerun old preparation steps over newer layers. Original game native libraries remain unchanged. The native unavailable-button hook is in runtime/english.cpp. AI recognition is parked and excluded.

The save-refresh policy has not changed. r19 previously retained all nine readable files, including both survival slots; user confirmed save loadability. This does not substitute for r20 testing. Preserve shared ADB and unrelated jobs. All task build/helper sessions finished; final process audit stored in the local output folder.

## Earlier checkpoint history

## Current local 4.0.5 prerelease 3 work (2026-10-21)

Latest test result: user confirmed r11 Tactic Modifiers no longer crashes, no Chinese noticed in Gods Almanac checks, and Projectile Info looks good. On S26, both real survival files (`level40.json`, `Player/Saves/level40_9999.json`) plus player/garden data remained byte-identical after staging two known stale language overrides, reinstalling r11 in place and starting the app. All nine non-fixture readable files were unchanged; both language overrides exactly matched current APK payloads after refresh. Local backup retained, no save writes/restores. See docs/testing/ANDROID405-PRE3-SAVE-TEST.md. Latest phone PID 19793; ask user to load a survival save for the separate loadability check. Deferred next translation audit: Recommended Levels > Super Level Editor > top-right Chinese button/window, with a close control incorrectly labeled Disabled. Do not claim that batch is fixed. No task-owned helpers/builds remain; no publication.


Branch `agent/translation-4.0.5-prerelease3`, uncommitted local work, no publication. Latest main candidate is test1-r11 (4050321), installed over main-r10 on S26 at explicit user request. playerData.json SHA remained identical across installation. PID 15533 reached the visible main-menu changelog and logged one playing Blooms source. User reported a Tactics crash; two existing identical native stacks were collected without relaunching. The shared field setter passed an address-of-pointer for managed references. Revision 11 uses il2cpp_field_set_value_object for TMP/legacy text and UnityEvent references, plus a compile-time pointer guard for value writes. Native ABI regression tests passed, including the expected negative compilation. Both Android ABI builds and signing/alignment/ZIP/translation/managed-refresh checks passed. Only the two added runtime libraries and manifest/revision entries differ from r10. See docs/testing/ANDROID405-PRE3-RUNTIME-FIX.md and audit-r11-delta.json.

User also confirmed Projectile Info toggles correctly on r10 but appears during plant selection, overlaps Open Almanac, jumps into the left stack after starting, and has an oversized label. Revision 11 follows the health button's active state, uses the native grid without manual placement, and insets a smaller two-line label. No original gameplay button is replaced. Crowded modes remain unverified; the original grid has one column, not automatic wrapping. Do not silently claim all screen sizes or modes are covered. The phone was left untouched during diagnosis. The user then said "install when ready"; r11 was installed with -r and launched once. The user subsequently confirmed Tactics no longer crashes and the Projectile Info button looks good; crowded-mode/aspect-ratio checks remain broader validation items.

User requested release-note credits: ClarkStacks for the T-key Projectile Info button, S.O.R.O.B for music choice, and testers collectively for easier save-preserving translation updates. Draft notes updated with these credits and the one-time RH-to-EN transfer caveat. Manual seed-to-main-r9 updating already corrected both stale labels and preserved progress/settings/music. r10 clean startup also passed per user. Never uninstall, clear data or reinstall the seed on this S26. Remaining validation includes r11 crash/UI fixes, gameplay music/drums, real multiple-profile/mode saves and other aspect ratios. Runtime extension, EN identity, managed refresh and integrated controls are authorized; historical data-only restrictions do not apply.

Package is `com.LanPiaoPiao.PlantsVsZombiesEN`, separate from prerelease 2 RH. No automatic cross-package save import. Future EN updates retain Android app data and refresh only known metadata overrides and explicitly managed runtime files. For fresh fixture testing only, install the lower-version refresh-seed APK first, create test progress/settings, then install test1 over it without uninstalling. This test has already passed on the current S26; do not reseed it. The Gods Almanac caption changes from STALE TEST Coins to God Coins. Never publish the seed.

Outputs: `C:/Users/plim/Documents/Codex/Projects/Plants-Vs-Zombies-Fusion/releases/4.0.5-English/prerelease-3`. Build evidence: task workspace `work/upgrade405/pre3`. PC pin remains `94b9ec0aecc3cea494c5b2c2883a7cbf14642440`. Dobby source pin `21f07a5ce184cda9346afb8009c07fe7e47390d0`. Only `Dobby-android` is used; earlier experimental Dobby folders in the task workspace are not build inputs. Both original game native libraries remain byte-identical; the added runtime hooks eight feature methods and two IL2CPP initialization exports. Device testing and publication approval remain pending. Do not claim complete Chinese coverage or validated runtime stability from host tests.


## Published 4.0.5 prerelease 2

Branch `agent/translation-4.0.5-prerelease2`. The maintainer approved local test 3 unchanged, published as `v4.0.5-release-2`; tests 1 and 2 are superseded. Read `docs/testing/ANDROID405-PRE2-RELEASE-BUILD.json` for the verified public asset and source commit. Read `docs/testing/ANDROID405-PRE2.md` and its audit/build records. It adds 140 reviewed JSON display edits and 16 metadata changes relative to prerelease 1. Test 2 was installed fresh on the S26 Ultra; its three screenshots confirmed known group/condition leftovers and a missed ordinal suffix. Test 3 translates all four trial availability conditions and removes that suffix, using `assets/prerelease2-screenshot-labels-4.0.5.json` after the test 2 manifest. PC uses visible-text runtime hooks, but no dedicated tactic-group handler or bare-group mapping was found in the pinned translator. Group identifiers remain protected. The previous claim that PC lacked most tactic text was incomplete: those records exist in `travel_buffs.json` and need full-record projection into split Android fields. Only the exact `descriptionOverride` path is newly display-editable; all runtime fields remain guarded. Two plant duplicate-ID exceptions have explicit bilingual identity reviews. Four bare PC name conflicts remain held. Prerelease 1 is preserved. Publication and uploaded digest verification are complete. Test 3 has no additional device test; do not imply otherwise. Collect team feedback.

## Published 4.0.5 prerelease 1

Branch `agent/translation-4.0.5-prerelease1`, release tag `v4.0.5-release-1`. The maintainer approved the existing local test 1 APK unchanged after an S26 Ultra smoke test: generally smooth, no obvious issues, Gods Almanac/tactics still substantially untranslated. Read `docs/testing/ANDROID405-PRE1.md` and the RELEASE-BUILD record. Preserve the exact artifact hash and signature when handling publication. The latest reviewed PC pin is `94b9ec0aecc3cea494c5b2c2883a7cbf14642440`. Current-source factual corrections, UI and music manifests use the 4.0.5 suffix. Do not reuse old metadata/object IDs wholesale or translate internal keys. Smoke testing is not exhaustive device validation.

## Historical 4.0 development


The active Android-only follow-up branch is `agent/translation-4.0-prerelease3`, based on metadata-safety commit `d997b2fc0e27d720ae75f56feb835b6f0edf45eb`. Local prerelease 3 test 1 is prepared but not published or device-tested. Read `docs/testing/ANDROID40-PRE3.md` and its build, validation and upstream records. It contains 11 display edits and the previous four internal metadata restorations. The latest reviewed PC 4.0 commit is `e6f597488b4756d1cc43ff223198feae24df64ae`. Apply `assets/prerelease3-display-4.0.json` with `scripts/apply_reviewed_display_patch.py` after the metadata-safety step. The user said the prior diagnostic seemed better but was unsure; do not claim a confirmed stability fix. Preserve internal Chinese keys even when PC English exists. The entire tactic area still lacks usable PC wording; two plant descriptions have conflicting PC IDs; puzzle labels also identify resources. See the screenshot dispositions before attempting more translations.

The preceding branch `agent/translation-4.0-prerelease2` fixes a confirmed prerelease 1 catalog-string regression; its approved rev 3 artifact is published unchanged as `v4.0-release-2`. Read `docs/testing/ANDROID40-PRE2.md` for that repair.
The maintainer verified test1 catalog operation and Nugget-shroom. The published prerelease 2 uses **local rev 3** unchanged, with the public filename omitting `-rev3`. Apply rev 2's `assets/gods-almanac-ui-4.0.json` after the protected-catalog repair, then rev 3's `assets/gods-almanac-rev3-4.0.json` with `scripts/apply_gods_almanac_ui.py`. Rev 3 uses explicitly approved provisional **God Coins**, generic level labels and five reviewed effect descriptions. Read `docs/testing/ANDROID40-PRE2-REV3.md`. Preserve all type/group/ID fields and unknown terminology. Exact PC English replaces these fallbacks when valid. The maintainer explicitly approved rev 3 as-is for publication. Do not imply exhaustive device testing. See `docs/testing/ANDROID40-PRE2-RELEASE-BUILD.json` and `docs/RELEASE-NOTES-4.0-PRE2.md`.
Read `docs/testing/ANDROID40-PRE1.md` and `ANDROID40-PRE1-BUILD.json` in that directory before using the historical 3.9 pipeline below. Release `v4.0-release-1` publishes the maintainer-approved revision 2 APK unchanged. Its three allowed payloads include resources.resource for 17 reviewed PC music replacements. PC archives are references only; do not build a PC release. Future releases still require user authorization. Provisional context-aware AI UI rules, navigation overrides, source pins, known PC conflicts, and upgrade guards are documented in the 4.0 handoff.

This file is the fastest way to resume the PvZ Fusion Android English port.
Read it completely, then read `README.md`, `docs/RESEARCH.md`, and
`docs/WORKFLOW.md` before changing build logic.

## Historical 3.9 objective and result

The repository contains reproducible tooling for porting the PC English
translation of *Plants vs. Zombies: Fusion* to the Android IL2CPP build. The
current supported target is Android 3.9.

The release is not a decompiled/recompiled Android application. It preserves
the Android shell and replaces exactly two Unity/IL2CPP data files:

- `assets/bin/Data/data.unity3d`
- `assets/bin/Data/Managed/Metadata/global-metadata.dat`

Do not commit APKs, extracted game data, translated bundles, metadata, DLLs,
font assets, or signing keys. `.gitignore` intentionally excludes them.

## What was learned

Joseph Franci's 3.6.1 English APK and aha's unfinished 3.8.1 APK use the same
fundamental method: translate IL2CPP literals in `global-metadata.dat`, modify
serialized Unity text/UI and fonts in `data.unity3d`, then repackage/sign.

Metadata replacement alone is insufficient. Almanac databases, TMP labels,
font references, baked textures, and layout live in the Unity bundle.

The clean 3.9 pipeline combines:

1. Teyliu PC branch `3.9` pinned to a recorded commit;
2. conservative mappings from English Android 3.8.1 Update 6, restricted to
   official source strings that are unchanged in 3.9;
3. same-version serialized UI translation;
4. TextMesh Pro font and SDF atlas transplantation;
5. narrow Android-specific layout fixes;
6. version-gated legacy textures followed by current PC textures;
7. post-build validation and comparative APK safety auditing.

See `docs/RESEARCH.md` for the full evidence and object-level discoveries.

## Known local inputs for the clean 3.9 rebuild

These files are deliberately absent from Git. A maintainer must supply legally
obtained copies under the ignored local directories.

| Purpose | Expected local path | SHA-256 |
|---|---|---|
| Official Chinese 3.9 APK shell/reference | `artifacts/ChineseAPK3.9.apk` | `a3adf7d8742d537f167217867e943e1b9faeaa361a868e33e388a373671320b0` |
| Known-good English 3.8.1 baseline | `artifacts/PvZ-Fusion-3.8.1-English-Android-update6.apk` | `a8441c6792363e0475ad0d989ce2046ec6d536f3011ef9496dc8e1eaf6a35c93` |
| Official Chinese 3.8.1 comparison | `artifacts/ChineseAPK3.8.1.apk` | `1d6789a388621f544ea1c29778acfb12645933b67153ecaed4f54a48c7fa43c0` |
| PC English data | `translation-data/PVZF-Translation` branch `3.9` | `d150f6f0d5ea16622c4e0b5ee6ce798d60e9c5d1` |

Never silently accept a hash mismatch. Upstream downloads are sometimes
replaced without changing their filename.

## Environment

- Python 3 with `requirements.txt`
- Unity version: `2022.3.62f1`
- Android SDK Build Tools 35.0.0 (`aapt2`, `zipalign`, `apksigner`)
- Dummy DLLs generated for the matching IL2CPP build, locally under
  `il2cpp/eng381_embedded/DummyDll`
- current PC translation checkout/data under ignored local directories

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Historical 3.9 build order

The important rule is to begin each major stage from its documented clean
input. Do not repeatedly mutate an already-generated asset unless the stage is
explicitly designed as a final polish pass.

1. Build translated metadata with `scripts/build_metadata_translation.py`.
2. Build translated TextAssets with `scripts/build_unity_text_translation.py`.
3. Apply serialized UI translations with `scripts/build_unity_ui_translation.py`.
4. Transplant fonts using `scripts/replace_unity_font_data.py` and
   `scripts/transplant_tmp_font_asset.py`.
5. Refine Almanac typography with `scripts/refine_almanac_layout.py`.
6. Apply Android-specific finishing work with `scripts/polish_android_ui.py`,
   passing the official 3.8.1 source bundle so old Android fallbacks cannot
   translate genuinely new 3.9 source text.
7. Apply version-gated Update 6 textures with
   `scripts/apply_legacy_texture_translations.py`.
8. Apply validated current PC texture translations with
   `scripts/apply_pc_texture_translations.py`.
9. Apply the exact `LETS ROCK` UI fix and final em-dash normalization.
10. Run `scripts/audit_remaining_cjk.py` and review every *visible* result.
11. Package only the two payloads with `scripts/package_apk_payload.py`.
12. Align, release-sign, and verify the APK.
13. Run `scripts/audit_apk_release.py` against official Android 3.9.

Every builder writes a JSON report and reopens/revalidates its generated file.
Treat a failed validation as a real failure; do not delete checks to get a
build through.

## Historical 3.8.1 final-polish specifics

The following section records the Update 6 baseline mechanics. It is historical
context, not the complete 3.9 stage order above. Important details:

- Almanac PC `<size>` tags are removed because Android applies a different
  effective scale.
- the three plant-detail skin selectors use the compact label `Skin`;
- the rotating Almanac footer is width-limited so it does not cross Search;
- duplicate live Help/Hotkeys overlays are blanked because the parchment
  already contains that content;
- the Help parchment is Texture2D path ID `2199`, named `thanks`, and must
  remain exactly 1400×600;
- the complete credit line `Joseph Franci · aha · SilverShadow · Codex` is
  baked into that texture using embedded Font path ID `6493` (`fzjz`);
- live TMP component path ID `179902` is deliberately blanked after baking;
- the disclaimer is rewritten to avoid the awkward phrase “only on the dev.”

Path IDs are valid for this exact 3.8.1 bundle only. For a future version,
locate objects semantically and confirm ownership/hierarchy before porting the
numbers. Do not assume an unchanged path ID points to the same object.

## Typography traps

The game contains multiple superficially similar TMP assets. Do not use any of
them for the parchment credit - the final renderer uses the embedded legacy
`fzjz` Font data directly and bakes pixels into the texture:

- `Dynamic` (path `178475`, material `1`) – transplanted readable UI face;
- `fzjz Dynamic` (path `178476`, material `112`) – compact/bold face that made
  the added credits look wrong;
- `汉仪夏日体W SDF` (path `178477`, material `2`) – parchment handwriting.

Changing only the Font object is not enough for TMP. The character/glyph
tables, atlas texture, material, source Font pointer, and fallbacks must agree.
Always reopen the bundle and validate the pointers after saving.

## Translation policy

Translate only confirmed player-facing text. Remaining CJK counts include
creator names, level-maker identifiers, internal keys, shader documentation,
and raw legacy data. Blind replacement can break lookups or game logic.

For each newly seen Chinese string:

1. capture the screen and navigation path;
2. identify whether it comes from IL2CPP metadata, a TextAsset, TMP `m_text`,
   or a baked texture;
3. prefer the current PC translation when an exact semantic match exists;
4. add the narrowest deterministic transformation;
5. validate the rebuilt file and retest that screen.

## Historical release safety and signing

`scripts/audit_apk_release.py` proves that the manifest, DEX, native `.so`
libraries, resources, and all other non-signature entries are byte-identical
to the official Chinese APK shell. Only the two declared data payloads may
differ. This is strong comparative evidence, not an absolute malware guarantee.

The public Android/AOSP test key must not be used for a community release:
anyone has its private key and could publish a malicious accepted update.
Joseph used a private personal key; aha used the public Android test key. This
project uses a dedicated private release key stored only in ignored local
files. Preserve secure backups and publish only its certificate fingerprint.

The package remains `com.LanPiaoPiao.PlantsVsZombiesRH`. Consequently, a build
signed by a different certificate cannot install over Chinese, Joseph, or aha
builds. Users must back up saves, uninstall the old app, then install this one.
All future releases signed with the same project key can update in place.

## Minimum device test matrix

- fresh install and first launch;
- relaunch and save persistence;
- main menu and changelog/disclaimer;
- Adventure, Challenge, Puzzle, Survival, and Odyssey entry;
- plant, zombie, mechanic, and modifier Almanacs;
- long plant/zombie descriptions and scrolling;
- skin selector arrows and label;
- Help/Credits parchment at 16:9 and a narrower/wider Android display;
- plant selection, storage, Zen Garden, Settings, and language menu;
- both `arm64-v8a` and `armeabi-v7a` if devices are available.

## Future-version strategy

For a new Android release, first inventory and diff the clean new Chinese APK
against 3.8.1. Rebuild metadata from current PC dictionaries, then port Unity
changes by semantic object name/type. Use historical Android builds only as
translation/layout references, never as structural bases for another version.

If the game changes Unity or IL2CPP versions, regenerate matching dummy DLLs
and confirm TypeTree support before editing anything. Keep each version's
inputs, generated reports, and object mapping separate.

## Definition of done

A release is done only when:

- all builders and reopen validations pass;
- serialized visible UI has no unexplained CJK;
- the APK comparative audit passes;
- ZIP integrity, zip alignment, and v1/v2/v3 signatures verify;
- malware scanning reports no detection (record scanner/date, without claiming
  that one scanner is conclusive);
- the final APK hash and signing certificate fingerprint are published;
- at least one real-device smoke test passes;
- the source commit/tag exactly corresponding to the APK is pushed.
