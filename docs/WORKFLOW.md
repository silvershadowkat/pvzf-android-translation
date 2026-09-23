# Repeatable update workflow

Current release: [Android 4.0 English prerelease 2](RELEASE-NOTES-4.0-PRE2.md). Use [the prerelease 2 investigation](testing/ANDROID40-PRE2.md), [rev 3 translation review](testing/ANDROID40-PRE2-REV3.md), and [release build record](testing/ANDROID40-PRE2-RELEASE-BUILD.json) for current work. The version-specific examples below are historical. The current APK changes exactly three payloads: Unity text/assets, metadata, and the audio resource. All executable code, permissions, and save logic remain official Android 4.0.


## 1. Preserve clean inputs

Keep the official Chinese APK and its extracted `global-metadata.dat` and
`data.unity3d` unchanged. Generated files must never become the baseline for a
future patch run.

Record the size and SHA-256 of every input. This makes it possible to identify
silent upstream replacements and prevents applying a patch to the wrong game
version.

## 2. Update translation sources

Pull the latest `Teyliu/PVZF-Translation` data and the associated translator
source. Review which base game version the release supports before building.
Inspect all upstream branches, not only `main`, and pin the exact selected
commit in the build report. Android prerelease 5 and the independent PC static
reference use branch `3.9` at
`d150f6f0d5ea16622c4e0b5ee6ce798d60e9c5d1`.

The metadata builder consumes:

- `translation_strings.json`
- `customlevel_strings.json`
- `abyss_buffs.json`
- structurally aligned `travel_buffs.json`, `tips_fs.json`, and `tips_iz.json`
- `translation_regexs.json`
- `customlevel_regexs.json`

Historical Android Chinese/English metadata pairs are optional fallback
sources. Current PC translations always take precedence.

For new or changed 3.9 gameplay terminology, the current PC project is the
only English authority. If it has no translation, preserve the official
Android 3.9 Chinese text. Placeholder values (`TODO`, `???`, all-question-mark
text, repeated temporary descriptions, and literal `X`/`Y` names) are not
translations. Do not generate AI-assisted English for new gameplay content.
Reviewed 3.8.1 Update 6 Android translations may remain only for unchanged
source strings.

Generic UI is a separate, narrow review layer. Settings, buttons,
connection/status messages, and tutorial prompts may be translated only after
their screen context is confirmed and only when they contain no unverified
gameplay names or mechanics terminology. Keep them in explicit code allowlists,
report their occurrences separately, and preserve PC translation precedence so
future upstream English replaces the Android review layer automatically.

## 3. Generate metadata deterministically

Run `scripts/build_metadata_translation.py` against the clean metadata file.
Inspect the generated JSON report for:

- input and output hashes
- unchanged literal count
- valid rebuilt offsets and sizes
- translations grouped by source method
- remaining CJK-bearing literals

The builder reparses the generated file and aborts if any rebuilt literal does
not round-trip exactly.

Run `scripts/audit_remaining_cjk.py` after the metadata and Unity passes. Do
not blindly translate every CJK-bearing metadata literal: some are internal
keys, debug/test messages, or configuration values whose mutation can break
game behavior. Promote additional strings only when their player-facing use is
confirmed.

## 4. Test the metadata hot patch

The Android build mirrors metadata to this writable location:

```text
/storage/emulated/0/Android/data/com.LanPiaoPiao.PlantsVsZombiesRH/files/il2cpp/Metadata/global-metadata.dat
```

Back up saves and the existing metadata first. Android scoped-storage rules may
require a device file manager with appropriate access or ADB. Fully close the
game before replacing the file.

Project policy: do not add an automatic stale-metadata migration to the APK.
The launcher must not inspect, delete, rename, replace, or move the user's
external `files/il2cpp` data during startup. APK updates can preserve that
directory, so release notes must tell users to back up their game files and
manually remove only a confirmed stale metadata override when necessary. A
clean install is the alternative. Never direct users to delete save or
progression files.

Test at minimum:

- first launch and main menu
- adventure and challenge selection
- almanac plants and zombies
- Odyssey modifier selection and descriptions
- custom levels and tutorials
- font rendering, rich-text tags, and line wrapping
- save/load and relaunch

For the 2026-08-14 Investment/Odyssey, UI-position, audio, and custom-level
investigation, including exact reproduction routes, see
`docs/testing/DISCORD_AUDIT_2026-08-14.md`.

## 5. Patch `data.unity3d`

Metadata alone cannot translate serialized `TextAsset` data, baked UI strings,
textures containing Chinese text, or font references. The asset pipeline should
operate by semantic asset name/type rather than fixed path ID so it survives
reasonable changes between game versions.

Planned asset stages:

1. Replace the three almanac text databases with current PC English JSON.
2. Translate level, custom-level, tutorial, and Abyss text assets.
3. Validate that every original JSON asset remains JSON with the same root
   structure and top-level fields.
4. Replace localized textures by asset name.
5. Inject or retarget a font with Latin coverage and preserve its Unity
   dependencies.
6. Apply field-level `MonoBehaviour` transformations derived from Joseph's
   broader 3.6.1 delta.
7. Reopen the rebuilt bundle and verify every intended object.

For Android 3.9, first run `scripts/apply_legacy_texture_translations.py`. It
compares official 3.8.1 pixels, English Update 6 pixels, and official 3.9
pixels, then carries a reviewed English texture forward only when the official
3.9 texture is unchanged. This restores assets such as the Odyssey key, Return
controls, and pause-menu `MENU` without overwriting new 3.9 artwork.

The legacy pass must never copy a TMP `* Atlas` texture independently. Font
atlas pixels are indexed by the matching glyph/character tables and coupled to
the font material. Test 1 demonstrated that mixing the Update 6 `fzcq Atlas`
with 3.9's larger table scrambles text across the game. Any future font change
must use the complete font transplant pipeline and validate the table, atlas,
material, and pointer chain together.

Run `scripts/apply_pc_texture_translations.py` after that pass so current PC
texture translations have final authority. The script requires compatible
name and dimensions, repairs particle Sprite meshes where necessary, reopens
the result, and validates the texture/Sprite relationship.

Rebuild combined modifier records structurally even when they remain Chinese:
the name belongs before the full-width colon and the description after it.
Never use a description as a fallback name. Apply
`scripts/refine_almanac_layout.py` so modifier, plant, and zombie description
bodies share the same horizontal margin.

Run `scripts/normalize_em_dashes.py` as the final bundle pass and require zero
remaining em dashes in player-facing translated text. Metadata normalization is
also mandatory and is applied before 3.9 integration as well as in the final
metadata builder.

## 6. Package and sign

Before packaging, run the final source-aligned wording pass
`scripts/reconcile_pc_english.py` **after all UI/layout/texture polishing**.
Pass the clean official same-version bundle with `--source-bundle`, the fully
polished candidate with `--base-bundle`, the pinned PC English directory with
`--localization-dir`, and new `--output`/`--report` paths. This final pass
refreshes stale English using original source keys and verifies that only
intended serialized text bytes changed. It is not a substitute for rebuilding
major stages from clean official inputs.

When continuing release 6, pass its verified metadata report to
`build_metadata_translation.py --preserve-release-report` in addition to the
ordinary clean inputs and fallback sources. The builder requires the report's
official-input SHA-256 and literal source/index pairs to match. This preserves
already shipped wording where there is no usable PC replacement, while still
allowing complete current PC translations to win. Record preserved wording
separately; it is not newly PC-authored text.

For this next-release candidate, also pass
`--pc-records docs/pc-reviewed-records.json`. This explicitly imports reviewed,
complete PC records newer than the main source pin, with their exact source,
section/ID and upstream commit recorded. The current manifest contains
`unlocks.14` for Kelptain Goldbeard / Sea-greed Zombox and `unlocks.27` for
Firnessence Panacea. Omitting the flag would drop these corrections when
rebuilding from the older PC pin. Current complete
PC exact or full-regex translations take priority over the manifest. Do not
turn malformed upstream JSON into a partially accepted production document;
keep any scoped import explicit and validate its whole candidate delta.

See `docs/ENGLISH-PARITY-2026-09-06.md` for the local continuation paths and
the tester-feedback rule. No release is authorized by these workflow notes.

Only after metadata and bundle tests pass:

For the September 10 Purgatory caption correction, run
`fix_purgatory_card_layout.py --input <candidate-bundle> --output <final-bundle> --report <report.json>`
after the final PC reconciliation and before packaging. It checks the exact
Android 3.9 object/hierarchy, changes only the title string, and reopens all
objects to verify every other byte is preserved. The metadata builder applies
the separate compact single-line footer; the menu and footer must not share
one line-break policy.

For the Release 8 Obsidian skin-challenge title correction, subsequently run
`fix_obsidian_skin_challenge_caption.py --input <candidate-bundle> --output <final-bundle> --strings-dir <reviewed-PC-Strings> --report <report.json>`.
This bridges only the reviewed Android line-wrapped source to the complete
PC title. It validates that PC wording, the exact menu hierarchy, and every
output object. Keep the separate runtime title unchanged; this script does not
modify metadata.

For Release 8 metadata, use the reviewed `708ffb136e33ccc6bb6db2fa67213170708934a9`
snapshot (English inputs are identical to `9afdca02`). The metadata builder
includes two exact-source PC regex adaptations for Luck/Respawn, six generic
UI fields, and the user-approved Blast Protection shield clause. Compare against
Release 7: literals 98, 119, 15725, 16209, 16697, 16954,
17062, 18419, and 18711 change, plus the 43 closed, reviewed source matches in
`scripts/reviewed_generic_text.py` (52 total). Named generic modifiers require
the reviewed PC names; a missing or changed name cannot enable an old fallback.
User-approved generic text takes priority over historical preservation only for
these exact sources. Preserve format specifiers and the dynamic
Luck cap; do not replace it with PC's fixed 250. See the Release 8 feedback review.

1. Run `package_apk_payload.py` to replace the two payload files in the chosen
   APK shell and remove its obsolete JAR signature entries.
2. Preserve all unrelated native libraries and launcher code.
3. Align the APK.
4. Sign it with the project's stable private release key.
5. Verify the signature and installability on a test device.

Never commit the key. Store at least two secure backups and document its alias
and certificate fingerprint without recording its password.

Example verification commands after signing:

```powershell
zipalign -c 4 translated.apk
apksigner verify --verbose --print-certs translated.apk
aapt dump badging translated.apk
```

## 7. Release without game binaries in source control

The preferred public deliverable is a patcher that accepts a user-supplied
official APK and produces a locally signed translated build. Translation data
must retain Teyliu project attribution and comply with CC BY-NC 4.0.

For a final-PC-3.9 visual reference, start from the untouched official PC
archive and run the metadata, Unity text, UI, and texture tools with
`--pc-reference-only`. This mode must exclude Android exact mappings, reviewed
Android UI allowlists, historical Android fallbacks, Android fonts, and Android
textures. Preserve incomplete or placeholder PC entries as official PC text.

Do not install MelonLoader or the current `PvZ_Fusion_Translator.dll` into this
reference: that DLL targets 3.8.1 APIs and fails on final 3.9. Apply only the
current upstream PC data statically, retain the official PC font assets, and
validate that the final bundle has the same object inventory as the official
base. The only original files allowed to differ are `data.unity3d` and
`global-metadata.dat`; a launcher and a provenance README may be added.

For a separate presentation test, run `scripts/polish_pc_reference_ui.py`
against the completed strict PC bundle. Its closed scope is the PC Settings
hierarchy: enable TMP auto-sizing/wrapping and apply only the generic control
labels declared in that PC-only script. Do not import Android mappings or use an
Android bundle as a font/layout donor. Keep the strict reference unchanged so
translation coverage and local presentation edits remain distinguishable.

When a ZIP is explicitly needed, use `scripts/package_pc_comparison.py`. Do not
use Windows `tar -a`: its ZIP writer can replace non-ASCII texture names with
question marks and collapse multiple source files onto one archive path. The
PC packager requires an exact source/archive path match, UTF-8 flags for
non-ASCII names, zero Windows path collisions, and a complete CRC pass.


## September 9 continuation input

Use `scripts/prepare_reviewed_pc_strings.py --checkout translation-data/PVZF-Translation --output <snapshot>` for the pinned, strictly parsed September 9 JSON input. Supply its `PvZ_Fusion_Translator/Localization/English/Strings` to the metadata builder together with the existing Release 6 reference/preservation report and reviewed-record manifest. The older checkout pin alone no longer reproduces the current modifier candidate. See [testing/ALL-MODIFIERS-2026-09-09.md](testing/ALL-MODIFIERS-2026-09-09.md) and [testing/SHOWCASE-ALMANAC-2026-09-09.md](testing/SHOWCASE-ALMANAC-2026-09-09.md) for coverage, exceptions and pending device checks. Reconcile Almanacs against the three English Almanac JSON files from that same commit. No packaging or publishing is authorized by these notes.
