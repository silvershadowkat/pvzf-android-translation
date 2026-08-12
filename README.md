# PvZ Fusion Android Translation Toolkit

Research and tooling for producing a repeatable English translation patch for
the Android IL2CPP build of *Plants vs. Zombies Fusion*. The immediate target
is Android 3.8.1; the larger goal is a workflow that can be rerun when the game
updates.

> Status: working research build under iterative on-device visual testing.
> Metadata, Unity text/UI reconstruction, TMP font transplantation, targeted
> layout refinement, and APK packaging are implemented and self-validating.

This repository intentionally contains **no APKs, game binaries, extracted
assets, signing keys, or bundled translation data**. Supply legally obtained
game files locally and clone the translation project separately.

## What is known

Joseph Franci's Android 3.6.1 build and aha's unfinished Android 3.8.1 build
use the same basic architecture:

1. Replace IL2CPP string literals in `global-metadata.dat`.
2. Modify serialized content in `data.unity3d` for almanac text, UI text,
   fonts, textures, and other content that is not sourced from IL2CPP literals.
3. Repackage and sign the APK, or install the metadata as a writable hot patch.

Joseph's port was substantially broader. It modified 257 `TextAsset` objects
and 3,081 `MonoBehaviour` objects; aha's 3.8.1 port modified only the three
almanac `TextAsset` objects and 1,598 `MonoBehaviour` objects.

The current clean 3.8.1 metadata build translates 2,571 literal occurrences,
compared with 335 in aha's updated file. Remaining Chinese literal occurrences
drop from 3,762 to 1,236. This does not mean every remaining occurrence is
visible player-facing text, and asset-side text still needs separate handling.

See [Research findings](docs/RESEARCH.md) and the [repeatable workflow](docs/WORKFLOW.md).

## Metadata builder

`scripts/build_metadata_translation.py` uses only the Python standard library.
It starts from a clean official metadata file every time, applies current PC
exact and regex translations, optionally learns fallback mappings from known
Chinese/English Android pairs, appends one rebuilt literal database, corrects
the metadata header, and validates the result by reading it back.

Example layout (all ignored by Git):

```text
artifacts/
  ChineseAPK3.6.1/
  ChineseAPK3.8.1/
  JosephEnglish3.6.1/
  ahaEnglish3.8.1/
translation-data/
```

Example invocation:

```powershell
python scripts/build_metadata_translation.py `
  --base artifacts/ChineseAPK3.8.1/global-metadata.dat `
  --strings-dir translation-data/PvZ_Fusion_Translator/Localization/English/Strings `
  --reference-pair Joseph-3.6.1 artifacts/ChineseAPK3.6.1/global-metadata.dat artifacts/JosephEnglish3.6.1/global-metadata.dat `
  --reference-pair aha-3.8.1 artifacts/ChineseAPK3.8.1/global-metadata.dat artifacts/ahaEnglish3.8.1/global-metadata.dat `
  --output generated/global-metadata.dat `
  --report generated/metadata-report.json
```

The order of reference pairs sets fallback priority. Current PC translation
entries always take precedence over learned historical mappings.

## Unity analysis utilities

Install the optional Unity dependency:

```powershell
python -m pip install -r requirements.txt
```

Available scripts:

- `build_unity_text_translation.py` builds and reopens a translated TextAsset
  bundle, preserving JSON structure and using current PC data before safe
  unchanged-source historical fallbacks. Its optional `--preserve-fonts-from`
  argument restores matching Font objects from an official bundle after using
  an unfinished translated bundle as the UI/text source.
- `build_unity_ui_translation.py` rewrites only the serialized `m_text` field
  of TextMesh Pro components. It uses the official same-version bundle as the
  structural source, applies contextual UI fixes and current PC data first,
  and treats unfinished builds only as fallback translation data.
- `replace_unity_font_data.py` transplants donor font payloads into stable
  same-version Font object IDs. This permits Joseph-style typography without
  changing TextMesh Pro component layout or introducing fragile object paths.
- `transplant_tmp_font_asset.py` performs the complete TMP transplant: glyph
  and character tables, SDF atlas pixels, material settings, source Font
  references, and an optional CJK fallback, all remapped into stable target
  object IDs.
- `refine_almanac_layout.py` retargets only the three long 3.8.1 Almanac
  description components from the handwriting TMP slot to the transplanted
  Dynamic slot and normalizes the oversized plant-page title.
- `polish_android_ui.py` removes PC-only Almanac size tags to match Joseph's
  Android data, translates visible configuration-backed labels, adds the
  current Android-port credits, cleans mixed-language UI defaults, and applies
  the final narrow title/layout corrections.
- `audit_remaining_cjk.py` separately inventories CJK-bearing IL2CPP literals,
  TextAsset JSON leaves, and serialized TMP text so internal data and creator
  names are not confused with missed player-facing UI.
- `package_apk_payload.py` replaces only `data.unity3d` and
  `global-metadata.dat` in a supplied APK, removes obsolete signature entries,
  and validates the embedded payload hashes. Its output is deliberately
  unsigned; use Android SDK `zipalign` and `apksigner` afterward.
- `compare_unity_bundles.py` compares serialized object hashes by asset file and
  path ID.
- `inventory_unity_bundle.py` inventories object types, names, and text assets.
- `extract_text_assets.py` extracts selected Unity `TextAsset` objects.

## Safety and distribution

- Back up Android saves before reinstalling or changing signing identities.
- A re-signed APK cannot update an APK signed by another private key. Choose one
  project key and preserve it securely for future releases.
- Local research APKs may be signed with a debug key, but public releases should
  use a dedicated private project key that is securely backed up.
- Do not commit or publicly redistribute game APKs or proprietary game assets.
- Translation data from Teyliu's project is CC BY-NC 4.0 and must remain
  attributed and noncommercial.

This is an independent fan interoperability project and is not affiliated with
PopCap, Electronic Arts, LanPiaoPiao, or the translation maintainers.
