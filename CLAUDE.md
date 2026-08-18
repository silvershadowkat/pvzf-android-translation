# Maintainer handoff for Claude and other coding agents

This file is the fastest way to resume the PvZ Fusion Android English port.
Read it completely, then read `README.md`, `docs/RESEARCH.md`, and
`docs/WORKFLOW.md` before changing build logic.

## Objective and current result

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

## Build order

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

## Release safety and signing

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
