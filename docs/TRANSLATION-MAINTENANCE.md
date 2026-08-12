# Translation maintenance and future-version migration

This is the repeatable path for updating the English Android build. It applies
to both the public no-menu project and the private SilverShadow build.

## Translation authority and provenance

Use this priority order:

1. Current PC community translations from `Teyliu/PVZF-Translation`.
2. Explicit Android-required overrides where Android semantics, rich-text
   contrast, or runtime formatting differs from PC.
3. Screenshot-confirmed Codex-assisted Android fallbacks only when the current
   PC data has no exact translation.
4. Historical Joseph/aha mappings only for unchanged source strings.

The metadata builder enforces this policy. Entries in
`ANDROID_CONFIRMED_EXACT` are fallback-only unless their source is listed in
`ANDROID_REQUIRED_OVERRIDE_SOURCES`. Therefore, when the PC community later
adds a translation for a Codex-assisted field, the PC value wins
automatically. Do not promote stylistic preferences to Android-required
overrides.

Generate the provenance report after every PC-data refresh. The report records
the upstream Git commit, origin URL, and dirty state automatically:

```powershell
python scripts/audit_translation_provenance.py `
  --strings-dir translation-data/PvZ_Fusion_Translator/Localization/English/Strings `
  --output analysis/translation-provenance.json
```

Review every `pc_community_replacement_preferred` entry. This status is
expected and means the local fallback has safely yielded to newer community
wording. Every `android_required_override` must retain a code comment and a
specific Android reason.

## Refresh the current PC translation

Keep the upstream translation as an ignored working clone; do not copy game
binaries into Git.

The PC translator reads local JSON from its installed `Localization` folder.
The packaged PC setup may also include `ModUpdateUtil.exe` and `Launch Game.bat`
scripts that refresh the local mod files when the game is launched. That is an
updater around the translator, not live per-screen translation. Android does
not ship or run that Windows updater. For Android maintenance, pull the latest
reviewed repository commit directly and record its hash, even if no new release
ZIP has been published yet.

```powershell
git -C translation-data pull --ff-only
git -C translation-data rev-parse HEAD
```

Record that commit hash in the build/release notes and confirm these inputs
still exist:

- `Localization/English/Strings/translation_strings.json`
- `customlevel_strings.json`, regex files, tips, and `travel_buffs.json`
- `Localization/English/Almanac/`
- the matching `Dumps/` structured source files

Never build from a previously translated metadata file or bundle. Start from
the clean official APK payload for the target game version.

## Important Android adapters

Some PC files cannot be copied wholesale:

- `DetailStringsTranslate.json` is a flat PC dictionary. Android requires
  `{"details":[...]}`. The text builder preserves the official Android list,
  types, and links, then merges PC titles/descriptions by the original title.
- PC modifier records store separate `name` and `desc` fields. Android stores
  a combined `name：description` runtime string and splits on the full-width
  colon for card/title labels. The metadata builder reconstructs that Android
  form by stable section and numeric modifier ID, puts the required name on a
  dedicated first line, and the Unity layout clips that metadata-only line so
  the visible description does not repeat the title.
- Android-only runtime format fragments (Tool Shop `Cost`/`Owned`, save
  labels, and similar fields) may not exist as complete PC strings.
- Runtime-backed page-navigation labels require the UI component backing-field
  patch in addition to ordinary TMP text replacement.
- Proper names in original game credits remain in their original Chinese.
  Translate roles and surrounding prose, not creator/helper names.
- Remove PC-only UI directions such as the changelog's `Languages` button.

All adapters validate structure/counts and stop on mismatches. A failure after
a major update is a request for investigation, not permission to loosen the
check.

## Migrating to a new major Fusion version

1. Archive the clean official APK and record SHA-256, version, package ID,
   Unity version, ABIs, `libil2cpp.so`, and metadata version.
2. Extract the official `data.unity3d` and
   `global-metadata.dat`. Confirm `arm64-v8a` before proceeding.
3. Generate a fresh IL2CPP dump and compare relevant class/method/field
   signatures. Never carry native offsets forward without validation.
4. Refresh and record the latest PC translation commit.
5. Run the metadata and Unity builders against the new clean source. Treat
   path-ID, object-count, schema, and title-set failures as version-porting
   work.
6. Run `audit_translation_provenance.py`. Accept PC replacements for fallback
   entries; manually review only Android-required conflicts.
7. Run `audit_remaining_cjk.py` on the rebuilt metadata and bundle. Classify
   results as internal identifiers, original proper names, non-player-facing
   diagnostics, or confirmed visible text.
8. For confirmed visible gaps, first search the current PC data by underlying
   ID, source string, call relationship, and data structure. Only then create a
   concise GPT/Codex draft.
9. Add a draft only after screenshot/context review. Record the source text,
   target, game version, screen/scene, and why PC data did not cover it. Keep it
   fallback-only unless Android truly requires different semantics.
10. Rebuild from clean inputs, reopen every artifact, compare the APK against
    the official shell, and physically test before publishing.

## Required audits before a release

- metadata literal count and round-trip validation;
- Unity TextAsset root/schema validation;
- Mechanics Almanac entry/title coverage;
- modifier name/description ID coverage;
- remaining CJK inventory;
- TMP/font/material validation;
- manifest, DEX, native-library, and ABI comparison;
- package ID and save-path preservation;
- physical checks of menus, saves, levels, Fusion mechanics, and the screens
  changed in that release.

A blindly renamed side-by-side package is not a valid test environment. See
`RELEASE-3.8.1-EN.md` for the compiled/hardcoded package-value warning.
