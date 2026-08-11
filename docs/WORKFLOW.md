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

The metadata builder consumes:

- `translation_strings.json`
- `customlevel_strings.json`
- `abyss_buffs.json`
- `translation_regexs.json`
- `customlevel_regexs.json`

Historical Android Chinese/English metadata pairs are optional fallback
sources. Current PC translations always take precedence.

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

## 4. Test the metadata hot patch

The Android build mirrors metadata to this writable location:

```text
/storage/emulated/0/Android/data/com.LanPiaoPiao.PlantsVsZombiesRH/files/il2cpp/Metadata/global-metadata.dat
```

Back up saves and the existing metadata first. Android scoped-storage rules may
require a device file manager with appropriate access or ADB. Fully close the
game before replacing the file.

Test at minimum:

- first launch and main menu
- adventure and challenge selection
- almanac plants and zombies
- Odyssey modifier selection and descriptions
- custom levels and tutorials
- font rendering, rich-text tags, and line wrapping
- save/load and relaunch

## 5. Patch `data.unity3d`

Metadata alone cannot translate serialized `TextAsset` data, baked UI strings,
textures containing Chinese text, or font references. The asset pipeline should
operate by semantic asset name/type rather than fixed path ID so it survives
reasonable changes between game versions.

Planned asset stages:

1. Replace the three almanac text databases with current PC English JSON.
2. Translate level, custom-level, tutorial, and Abyss text assets.
3. Replace localized textures by asset name.
4. inject or retarget a font with Latin coverage and preserve its Unity
   dependencies.
5. Apply field-level `MonoBehaviour` transformations derived from Joseph's
   broader 3.6.1 delta.
6. Reopen the rebuilt bundle and verify every intended object.

## 6. Package and sign

Only after metadata and bundle tests pass:

1. Replace the two payload files in a clean official APK.
2. Preserve all unrelated native libraries and launcher code.
3. Align the APK.
4. Sign it with the project's stable private release key.
5. Verify the signature and installability on a test device.

Never commit the key. Store at least two secure backups and document its alias
and certificate fingerprint without recording its password.

## 7. Release without game binaries in source control

The preferred public deliverable is a patcher that accepts a user-supplied
official APK and produces a locally signed translated build. Translation data
must retain Teyliu project attribution and comply with CC BY-NC 4.0.
