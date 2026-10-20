# Android 4.0.5 prerelease 2 coverage audit

Prepared October 20, 2026 on `agent/translation-4.0.5-prerelease2`, starting from `51e76484108912de8492dca7797ba2def3a07fa2`.
Local test 3 was approved unchanged and published as [4.0.5 prerelease 2](https://github.com/silvershadowkat/pvzf-android-translation/releases/tag/v4.0.5-release-2) on October 20, 2026. The uploaded APK checksum matches the local candidate. Tests 1 and 2 are superseded. Test 2 was installed fresh on the S26 Ultra and the user supplied three screenshots. No additional test 3 device test is claimed. See `ANDROID405-PRE2-RELEASE-BUILD.json`.

## Screenshot follow-up: test 3

- APK: `C:\Users\plim\Documents\Codex\Projects\Plants-Vs-Zombies-Fusion\releases\4.0.5-English\prerelease-2\PvZ-Fusion-4.0.5-English-Android-prerelease2-test3.apk`
- SHA-256: `3a2318c29d6da4ed8a2f7f7a1017f6c766c16f471cd6f8c2eae7aaf66863899d`.
- Apply `assets/prerelease2-screenshot-labels-4.0.5.json` after the test 2 manifest using `scripts/apply_gods_almanac_ui.py`. Its existing source guards support the explicitly reviewed empty suffix; generic display patch safeguards remain unchanged.
- Four trial `condition` fields are translated. No Pains No Gains retains the extra Reincarnation stage and wave restrictions. Purgatory and Reincarnation are established PC terms, not new names.
- Metadata literal 485 (` 级`) becomes empty after the already-translated `Level ` prefix. The 4.0.5 ARM64 reference scan found both ordinal fragments only in `EntryMeta` at RVA `0x24c75f0`. This restores the equivalent reviewed 4.0 fix that was missed during migration.
- The pinned PC translator DLL uses `TextMeshProUGUI_Patch.OnEnable` and `StringStore.TranslateText` to read and replace visible TMP text. No dedicated ShootingAlmanac group handler or matching English mapping for any of the 12 bare group names was found. This is evidence about the inspected version, not a claim of verified PC rendering. Android has no corresponding runtime hook layer. Internal group values and native code remain unchanged.
- Exact comparison with test 2 confirms only these four catalog fields and one metadata literal changed. All 208,662 Unity objects were verified, 66 tests passed, and 315 .NET format templates passed. Catalog runtime strings and references remain protected. APK signatures, existing certificate, alignment, original-APK comparison, test-2 comparison and Defender checks passed.
- Total changes from public prerelease 1: 140 JSON display fields and 16 metadata literals.
- Evidence: `work\upgrade405\pre2\followup` in the task workspace. See `ANDROID405-PRE2-TEST3-BUILD.json` and `ANDROID405-PRE2-TEST3-REVIEW.json` beside this document. Task stage runners are `work\fix405_screenshot_labels.py` and `work\package405_screenshot_labels.py`.
- Device check: confirm tactic levels read Level 1/2/3 without `级`, and all four Trial Modifiers show English eligibility text. The tactic group headings are still a documented limitation. Publication was explicitly approved and is complete; collect team device feedback.

The sections below record the test 2 baseline.

## Artifacts and source

- Repository: `C:\Users\plim\Documents\Codex\Projects\Plants-Vs-Zombies-Fusion\source\pvzf-android-translation`
- Working evidence: `C:\Users\plim\Documents\Codex\2026-09-06\https-github-com-silvershadowkat-pvzf-android\work\upgrade405\pre2`
- APK: `C:\Users\plim\Documents\Codex\Projects\Plants-Vs-Zombies-Fusion\releases\4.0.5-English\prerelease-2\PvZ-Fusion-4.0.5-English-Android-prerelease2-test2.apk`
- SHA-256: `769e2a2ff7b63df54a30da3579c217101c1f1657da70ee21f3af043a416dfdd8`
- Size: 655272864 bytes.
- Public prerelease 1 remains unchanged.

A fresh remote fetch confirms PC branch `4.0` is still at `94b9ec0aecc3cea494c5b2c2883a7cbf14642440`. No newer PC commit was available.
This pass corrects coverage omissions in the earlier Android importer.

## What the first audit missed

An empty PC `gods_evolved.json` does not imply that PC lacks Gods translations. The populated `travel_buffs.json` contains tactic, trial, curse and upgrade names/descriptions.
The earlier importer handled complete combined strings, but Android's indexed Almanac separates the tactic title and description. It also protected all plant buff fields, inadvertently retaining human-readable `descriptionOverride` prose as Chinese.
The new projection matches the entire Chinese title plus description to one PC source record. Repeated titles are disambiguated by their complete body. Trials have one explicitly recognized category prefix. No body-only, array-position or fuzzy matching is used.
The only new allowed catalog path is `plants[index].buffs[index].descriptionOverride`. Adjacent types, arguments, maximum counts, groups, IDs, resource paths and lookup strings remain protected.

## Changes

- 52 source-matched modifier records: 48 tactic levels and four trials. This changes 100 separate title/description fields because four trial titles already matched.
- All 26 nonempty embedded curse/upgrade description overrides now use complete PC English.
- 12 qualified modifier names replace old wording or Chinese titles using a unique structured PC record. Four bare-name conflicts between PC tables remain unchanged.
- Two condition cross-references now use `Luck • Loan - X`.
- Four new Omnipotence availability conditions reuse reviewed English from identical Chinese conditions in the same tactic category.
- Sea-greed Zombox and Pyroboros Pot gain their missing information/recipe fields. Their English names and flavor text were already present.

Total relative to public prerelease 1: **136 JSON display fields and 15 metadata literals**.

## Source accuracy and duplicate IDs

PC lists both Sea-greed Zombox and Pyroboros Pot under ID 5003. Android uses 5003 and 5005. A general duplicate-ID quarantine remains enabled.
These two specific records were reviewed bilingually against the official PC/Android source, independently verified English names, recipes and numeric mechanics. The explicit patch targets original Android IDs and preserves them.
The separate alignment record stores hashes of the exact Chinese and PC English records. No generic positional matching or upstream ID rewrite was introduced.

The existing Omnipotence - B 30% damage correction is retained in the newly projected Almanac text, avoiding PC's stale 10%.
The Decryption description restores the Chinese source's doubled normal-attack stacking chance and does not add a nearby-target restriction. Its metadata and Almanac override stay consistent.
Pyroboros Pot retains the source's short/carrier traits and separate per-explosion-type cooldowns.
Two PC typographical errors, `max H` and `Mecha Figher`, are corrected in both corresponding metadata and Almanac descriptions.

## Coverage and remaining text

Checked exact and complete-regex PC mappings, structured travel modifiers, source-aligned Almanac data, tips, custom-level tables, metadata, qualified name variants, eligible serialized display fields, texture catalog coverage and previous audio provenance.
There are no remaining unprotected exact PC matches in metadata or eligible JSON display fields. The three metadata matches intentionally left Chinese are protected runtime keys: `升级`, `护盾保护`, `爆炸保护`.
All 48 tactic-level titles/effects and 26 description overrides pass the no-CJK check. The final eligible JSON display scan contains 35 fields with CJK; this includes contributor names, not just untranslated prose.
Remaining catalog gaps include two shield conditions, the unverified mysterious-cannon entry and four trial conditions. Internal group headings remain original because they also identify tactics. Unsupported editor help topics and two zombie flavor paragraphs remain Chinese.
Puzzle labels also identify level resources and were not renamed.
`custom_level_data.json` has no populated corresponding PC Chinese dump and is not imported without source identity.
All 60 PC texture files were inventoried: 47 matching replacements are already carried; 13 have no exact Android texture-name match. No additional applicable PC image replacement was found. Font atlases, approved credits and all sprites/textures remain unchanged from prerelease 1.
PC music source blobs remain the same as the prerelease 1 pin; audio is byte-identical.

## Verification

- 66 tests passed, including new full-record matching, ambiguous-record rejection, incomplete-description rejection and exact display-path protection cases.
- 315 actual .NET formatting checks passed.
- All 208,662 Unity objects checked. All JSON structures, IDs and nontext values preserved.
- The complete changed-field set matches the reviewed manifest: no extra text changes.
- Protected catalog reflection references validated against the current Android types.
- Compared with prerelease 1, only `data.unity3d` and `global-metadata.dat` differ outside signatures.
- Original native code, manifest, permissions, resources/audio, fonts, textures and layout settings remain unchanged.
- v1/v2/v3 signatures, existing certificate and ZIP alignment verified. Defender scan reported no threats.
- No game or emulator launched. Longer English descriptions have valid tags/placeholders and use existing scrolling/wrapping; actual device rendering and gameplay still need smoke testing.

## Reproduction and next steps

Apply `assets/prerelease2-display-4.0.5.json` with `scripts/apply_reviewed_display_patch.py` to the exact prerelease 1 bundle and metadata, using the official 4.0.5 files as source guards and the existing type dump.
The reusable migration now projects separate indexed entries with `scripts/project_pc_modifier_records.py`, and recognizes only the precise display-override path. Preserve the reviewed factual patches after future PC imports.
Local stage runners in `C:\Users\plim\Documents\Codex\2026-09-06\https-github-com-silvershadowkat-pvzf-android\work`: `audit405_pre2.py`, `explore405_pre2.py`, `project405_pc.py`, `aliases405_pre2.py`, `review405_pre2.py`, `build405_pre2.py`, `verify405_pre2.py`, `package405_pre2.py`, and `finish405_pre2.py`. Bounded logs and reports are in the evidence directory.

Device test priority: browse tactic levels and maximum-tier purchase dialogs, inspect curse descriptions, inspect both restored plant descriptions/recipes, then start a Gods run and reach a modifier choice. Confirm saves still load and watch for clipped text.
The user approved test 3 for publication. Prerelease 2 is published separately; prerelease 1 remains available.
