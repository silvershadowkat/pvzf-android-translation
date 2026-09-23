# Translation maintenance and future-version migration

This is the repeatable path for updating the English Android build.

## Current Android 4.0 baseline

Release `v4.0-release-2` publishes local prerelease 2 rev 3 unchanged. Read [the catalog repair](testing/ANDROID40-PRE2.md), [rev 3 review](testing/ANDROID40-PRE2-REV3.md), and [release build record](testing/ANDROID40-PRE2-RELEASE-BUILD.json). Apply the protected-catalog repair and source-checked factual corrections before the rev 2 and rev 3 UI allowlists. Never translate runtime types, IDs, group keys, resource paths or save fields.

God Coins is a specifically approved provisional name for `诸神币`, not general permission to invent terminology. Other tactic names and specialized effects stay Chinese without verified PC English. Preserve the exact source/previous-English guards and prefer complete valid PC translations when they become available. Do not carry old factual corrections forward blindly when either source changes.

The older version-specific instructions below are historical context.

## Translation authority and provenance

### Current tester-feedback rule (updated 2026-09-15)

Maintain [RELEASE-NOTES-NEXT.md](RELEASE-NOTES-NEXT.md) as the single running
release-notes draft. Every completed correction from this work and future
tester feedback must be reflected there once. Combine related changes, explain
them in familiar game terms, and distinguish prepared fixes from pending
review or device testing. Keep technical evidence in the audit documents.

For every tester finding, look up the exact source/record in the current PC
3.9 translation before proposing English. If the PC project has no completed,
usable translation for that field, tell the user **the PC project has not
translated it yet**. The user's September 11 and September 15 instructions
also authorize straightforward navigation, counters, status text and basic,
unambiguous effects after context review even when PC lacks them.
Keep these exact, fallback-only entries in the reviewed UI allowlist and
document their provenance. Plant/zombie names, ability or modifier names,
recipes and specialized or ambiguous gameplay descriptions still require completed,
source-aligned PC wording. Basic effects may use a verified PC modifier name
with a faithful contextual translation of the Android effect. Do not invent
names or infer missing mechanics. Existing assisted wording is identified for review, not automatically
reverted.

This updated session rule permits the generic-UI exception below for reviewed
feedback. Lack of an exact dictionary match alone is not proof of missing PC
English: check structured Almanac records, tips, and applicable complete regexes.
Never use a partial regex match to replace a whole description.

The current parity pass and verification are documented in
[ENGLISH-PARITY-2026-09-06.md](ENGLISH-PARITY-2026-09-06.md).

For new or changed 3.9 gameplay content, use this strict beta policy:

1. Use the current PC community translation from
   `Teyliu/PVZF-Translation` exactly when it exists.
2. Otherwise preserve the official Android 3.9 Chinese text.
3. Do not create AI-assisted English fallbacks for new or changed gameplay
   text.

Confirmed generic UI and unambiguous basic effects are exceptions to the PC-or-Chinese rule. A
setting, button, connection/status message, or tutorial prompt may be
translated after visual/context review when it contains no unverified plant,
zombie, fusion, item, modifier, recipe, or mechanics term. Store these in the
explicit 3.9 reviewed-UI allowlists and count them separately in reports.
Prefer later complete PC English, but retain clear Android-specific instructions
when a shortened PC label would omit required steps. Document any such exception.
Validate placeholders, numeric precision, parser delimiters and component bytes.
Never translate command tokens, enum/storage identifiers or default filenames
without proving they are display-only.

Reviewed Android-specific 3.8.1 Update 6 translations may remain for source
strings that are unchanged in 3.9. Historical Joseph/aha mappings remain
conservative fallbacks for unchanged source strings. Do not carry independently
generated 3.9 prose from earlier prerelease branches into the clean rebuild.

Prerelease 5 uses upstream branch `3.9` at commit
`d150f6f0d5ea16622c4e0b5ee6ce798d60e9c5d1`. That branch was newer than `main`
when selected. Always inspect upstream branches and record both branch and
commit rather than assuming `main` is authoritative.

Treat PC placeholders as untranslated. This includes `TODO`, `TBD`, `WIP`,
all-question-mark values, `currently bugged` placeholders, repeated temporary
descriptions reused across records, and literal `X`/`Y` names. Preserve the
corresponding official Chinese field. Structured records may mix a valid PC
name with an untranslated Chinese description only when each field is aligned
to the matching official PC source dump.

September 9 reviewed exception: Tyrannoflora Lux (951)'s complete PC `info`
field contains an embedded "currently bugged" gameplay note. Its exact English
SHA-256 is allowlisted in `REVIEWED_PC_COMPLETE_FIELD_HASHES` in the Unity text
builder. All other placeholder checks remain active; unreviewed edits require
another review. See [LUX-FIRNESSENCE-2026-09-09.md](testing/LUX-FIRNESSENCE-2026-09-09.md).

The metadata builder enforces this policy. Entries in
`ANDROID_CONFIRMED_EXACT` are fallback-only unless their source is listed in
`ANDROID_REQUIRED_OVERRIDE_SOURCES`. Therefore, when the PC community later
adds a translation for a previously Chinese 3.9 field, the PC value wins
automatically. Do not promote stylistic preferences to Android-required
overrides and do not translate untranslated 3.9 fields independently.

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
- Audit dynamic UI fragments as families, not only as completed screenshots.
  Vasebreaker PVP, for example, appends the standalone full-width state
  suffixes `（关）` / `（开）` to more than one toggle and constructs notices
  from a prefix, the live player name, and a suffix. Search the metadata for
  nearby turn/move/vase fragments after any one member is reported. Translate
  the exact fragments while preserving placeholders and intentional spaces;
  never globally replace the individual characters `关` or `开`.
- Plant affinity labels are the 18 member names of Android 3.8.1's
  `SynergyType` enum. The Almanac renders them with `ToString()`, so they live
  in the IL2CPP definition-string heap rather than the ordinary literal table
  or `LawnStrings`. `build_metadata_translation.py` renames only the 18
  version-validated enum fields; it preserves their numeric values and aborts
  if any expected source name or table layout differs. Revalidate these field
  indices after every game update.
- Investment Odyssey descriptions come from the PC community
  `travel_buffs.json`, but its 42 `investmentBuffs.*.name` fields are currently
  blank. Android renders the corresponding card titles with
  `InvestBuff.ToString()`. The metadata builder therefore keeps the PC
  descriptions and renames only the 42 version-validated Android enum fields.
  Record this distinction in release notes: Android completes missing display
  titles; it does not supersede the PC translation or alter enum values.
- `audit_remaining_cjk.py --dump-cs <dump.cs>` must accompany the ordinary
  literal/bundle scan. Player-facing enum member names live in the IL2CPP
  definition-string heap and were invisible to the older literal-only audit.
  Treat its enum report as a review inventory, not permission to translate
  every identifier. Patch only a class proven to be displayed through
  `ToString()` and validate every expected field name and index.
- Runtime-backed page-navigation labels require the UI component backing-field
  patch in addition to ordinary TMP text replacement.
- Serialized UI is not uniformly TextMesh Pro. Legacy `UnityEngine.UI.Text`
  components use `m_Text` (capital T), while TMP uses `m_text`. The remaining-
  CJK audit recursively scans all readable serialized string fields and reports
  unreadable candidate objects; do not reduce this check back to one field.
- Audit mixed-language output as well as fully Chinese output. A broad PC regex
  can translate the surrounding sentence while leaving an Android-only perk
  label or one fusion ingredient in Chinese. Exact Android 3.8.1 fallbacks fix
  those cases and automatically yield if the PC community later supplies an
  exact English entry.
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
7. Run `audit_remaining_cjk.py` on the rebuilt metadata and bundle and pass the
   new version's `dump.cs` with `--dump-cs`. Classify literal and definition-
   enum results as internal identifiers, original proper names, non-player-
   facing diagnostics, or confirmed visible text.
8. For confirmed visible gaps, first search the current PC data by underlying
   ID, source string, call relationship, and data structure. Gameplay-bearing
   gaps remain Chinese when PC English is unavailable.
9. Add generic UI English only after screenshot/context review. Record the
   source text, target, game version, screen/scene, and why PC data did not
   cover it. Keep it fallback-only unless Android truly requires different
   semantics.
10. Rebuild from clean inputs, reopen every artifact, compare the APK against
    the official shell, and physically test before publishing.

Do not translate existing save-slot names automatically. A legacy save whose
stored default name is Chinese should be renamed with the game's
`Rename Selected Save` control. New saves use the translated default. This
keeps migration tooling away from progression data.

### Why an imported save can still say `新的存档`

The save picker does not generate the whole row from one translatable string.
Its row format supplies `Slot`, `Saved at`, and `Version`, but the first value
is the save's persisted `SurvivalData.name`. In the official game,
`SaveInfo.SaveSurvivalData` and `SaveMgr.SaveBoard` historically created a new
slot with the default name `新的存档`. Translating that default to `New Save
File` affects newly created saves only; it cannot safely rewrite names already
stored in progression data.

This distinction can be confirmed from the UI itself: English row labels
surrounding a Chinese first line mean the current translation is active, while
an older displayed save version (for example, `Version: 3.7` in a 3.8.1 build)
proves the slot was imported from an earlier game version. The player may use
`Rename Selected Save` to change that stored label. If a genuinely new save
created by the current clean build still receives the Chinese default, check
for a stale external `files/il2cpp` metadata override before changing code.

### Preserve runtime formatting characters

Some metadata literals deliberately end in `\n` because the game concatenates
several formatted fields into one inspection panel. Translations must preserve
those separators. For example, the SolarNova inspection fields for HP, damage,
production cooldown, and Lumos level each retain the official trailing newline.
Removing it causes adjacent labels and values to run together even though the
individual words are correctly translated.

## Release 9 provisional UI tracking

The user approved retaining all 117 contextual translations, including
"higher-quality zombies" in the red-vase Crisis Mode message. These are
provisional English, not PC-authored terminology. The two Travel Store
placeholder labels are separate from the 117 entries.

[The tracker](testing/release9/provisional-ui-tracker.json) records every exact
Chinese source, provisional English, PC-name requirement, PC commit checked,
and complete PC match, if available. Existing metadata indices and actual
rendered targets are in [the change report](testing/release9/metadata-changes.json).
Use source text as the stable key; indices may move in later game versions.

On every PC translation refresh, run this against the newly reviewed, strictly
parsed English Strings snapshot:

```text
python scripts/audit_release9_fallbacks.py --strings-dir <reviewed-English-Strings> --pc-commit <commit> --output docs/testing/release9/provisional-ui-tracker.json
```

Review `pc_candidate_available` entries for full-source coverage, preserved
format arguments, and terminology. The metadata builder already gives usable
exact PC entries priority over these fallbacks. Complete PC regex/template
candidates must also pass the normal full-record build review. Never replace
from a partial or fuzzy match. Keep the provisional mapping as historical
fallback provenance, and regenerate the tracker and payload verification when
adopting PC text. The comparison command only writes its report.

At commit `d9c05a39e7c0abb09f84ddfb15582885d60a0efe`, none of these 117 entries
has a complete usable PC match. A regression test verifies that all 117 yield
to future exact PC translations, including the PC-name-gated result message.

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

Abyss is deliberately parked in Android 3.8.1. Dormant classes and an inactive
Challenge-menu object exist in the shipped assets, but the translation project
must not expose or shortcut that mode. Reassess only if a future upstream
Android build officially enables it.


## September 9 continuation input

Use `scripts/prepare_reviewed_pc_strings.py --checkout translation-data/PVZF-Translation --output <snapshot>` for the pinned, strictly parsed September 9 JSON input. Supply its `PvZ_Fusion_Translator/Localization/English/Strings` to the metadata builder together with the existing Release 6 reference/preservation report and reviewed-record manifest. The older checkout pin alone no longer reproduces the current modifier candidate. See [testing/ALL-MODIFIERS-2026-09-09.md](testing/ALL-MODIFIERS-2026-09-09.md) and [testing/SHOWCASE-ALMANAC-2026-09-09.md](testing/SHOWCASE-ALMANAC-2026-09-09.md) for coverage, exceptions and pending device checks. Reconcile Almanacs against the three English Almanac JSON files from that same commit. No packaging or publishing is authorized by these notes.
