# Repeatable update workflow

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
commit in the build report. Clean Test 3 uses branch `3.9` at
`0747001d10b6f3b82f89ea1ee022f2e30f347791`.

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

Only after metadata and bundle tests pass:

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
