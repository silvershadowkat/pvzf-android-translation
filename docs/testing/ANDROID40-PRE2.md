# Android 4.0 prerelease 2 investigation and local test

Release: `v4.0-release-2`, using the maintainer-approved rev 3 APK unchanged. Based on `v4.0-release-1`, commit `be2e48f`. Source branch: `agent/translation-4.0-prerelease2`. See [release notes](../RELEASE-NOTES-4.0-PRE2.md) and `ANDROID40-PRE2-RELEASE-BUILD.json` for the public artifact. Earlier local-test status statements below are historical.

Published revision: [prerelease 2 rev 3](ANDROID40-PRE2-REV3.md), adding the explicitly approved God Coins wording and another narrow generic UI pass. The test1 and rev 2 results below remain historical records.

## Empty Gods Almanac

The user reports the empty page consistently, including with a fresh save after Unlock Everything. The Chinese comparison shows populated cards and six category buttons; the English comparison shows 0/0 roots and no category buttons.

Confirmed porting defect: the broad PC fusion regex matched nested runtime class names containing `+`. The generic asset importer treated a JSON field named `type` as display text. It changed 96 `ShootingAlmanacIndex.plants[*].buffs[*].type` values into discovery-tip prose. These are reflection class names, not labels. That can prevent catalog initialization before cards and category buttons are populated.

- Restored all 96 original class references.
- Restricted catalog translation to entry titles, descriptions, and conditions. All resource paths, class references, categories, qualities, IDs, arguments, and other runtime values must remain original.
- Removed the generic permission to translate a field merely because it is named `type`.
- Restored one internal Unity line-breaking table that had been treated as prose during dash normalization.
- Validated all 374 catalog reflection references against 209 types in the matching official 4.0 type dump. Preserved 20 roots, 109 plant records, and 70 entries.
- Added regression tests for corrupted nested class references, missing reflection targets, protected values, nested-type namespace resolution, and stale correction guards.

The previous checks proved JSON shape and numeric-data integrity, but did not prove that internal string values still named valid types. That gap is now explicitly checked across the catalog and other non-Almanac TextAssets. On September 22, the maintainer confirmed that the test1 Gods Almanac works and Nugget-shroom is corrected. The supplied screenshots show populated tabs, cards, routes and purchase dialogs. This is specific device feedback, not exhaustive crash-free coverage.

## Official 4.0 factual corrections

These are narrow description corrections supported by official Android 4.0 Chinese text. Existing PC names are preserved. Some stale PC numbers predate 4.0, so these are not all newly introduced 4.0 balance changes. No gameplay values are changed.

| ID | PC name | Correction/evidence |
|---|---|---|
| 235 | Doubleblast Passionfruit | Official damage interval is 3 seconds. |
| 1035 | Icicle-shroom | Official damage interval is 2.25 seconds. Replaces the previously documented stale PC value. |
| 1121 | Cob-pult | Official damage is 140 per 3 seconds. |
| 1170 | Nugget-shroom | Official damage interval is 2.25 seconds, reproduction remains 20 seconds. |
| 1171 | Spuddy-shroom | Official damage is 60 per 3 seconds. |
| 1196 | Spring Melon | Official damage interval is 3 seconds. |
| 212 | Jack-in-the-Box | Official Toughness is 1000. |
| 213 | Pickaxe | Official Toughness is 1000. |
| 214 | Chrono Core | Official Toughness is 1000. |
| 215 | Mecha Fragment | Official Toughness is 1000. |
| 216 | Giga Mecha Fragment | Official Toughness is 1000. |
| 1202 | Squash Pumpkin | Official text says every 2.5 seconds, one active per shell except the named variant, target range 1.1 tiles to the right and 6 attacks. Existing PC names retained. |
| 1095 | Starpick | Official 4.0 adds damage immunity. |
| 1452 | Hungry-shroom | Official 4.0 explicitly starts the cooldown whether swallowing succeeds or fails. |

Nugget-shroom's attack interval is 2.25 seconds, not 1.5 seconds. Its reproduction delay is still 20 seconds. A larger attack interval means slower attacks, not a shorter planting cooldown.

Coffee Bean (211): `exempt` is correctly spelled and means unaffected by the listed price increases. The Chinese source explicitly waives snow/daytime seed-packet price increases for base plants on its tile for the current level. The English wording matches PC and was left unchanged.

Corrections are tracked in `assets/almanac-corrections-4.0.json`. Each has an exact source hash, the stale English field, reviewed replacement, and reason. If either source or PC wording changes, the old correction must not overwrite it; review the changed field. This is a limited exception to PC wording authority for demonstrable factual discrepancies, not authorization to invent plant names or complex descriptions.

## Wider review and upstream status

- Fetched upstream PC references again. PC branch `4.0` remains at `9a170fdfa999e4e8dc6fe45e31c0806a1271577d`; there are no new 4.0 imports.
- Reused the complete 354-field new/changed Almanac inventory, and compared its 104 fields with changed numeric text.
- Compared PC 3.9 and 4.0 English. 139 changed-source fields have unchanged PC English. This is a review queue, not a confirmed error count: many changes are whitespace, clearer Chinese wording, removed unlock hints, recipe notation, or additional named modifiers.
- Audited base damage/Toughness/recharge displays across the plant Almanac. Automated comparisons flagged 175 differences, including valid extra per-shot detail, damage types, reordered formulas, omitted-but-explained limits, and translated units. Only unambiguous reviewed corrections above were applied. Do not mass-replace numbers from that report.
- Complex modifier changes, named cold-state terminology, and unclear recipe/mechanics differences still need PC review. The existing ID 5003/5005 conflict remains quarantined.
- A report says dead zombie sprites persist in Chinese as well. That is unverified user testimony, not a reproduced base-game diagnosis. No specific crash log or reproducible mode-gameplay fault was supplied. Gameplay code, saves, spawning, and death handling remain untouched.

Local detailed review files are in `work/upgrade40/pre2`: `almanac-source-delta` is in its parent; this folder contains `numeric-source-deltas.json`, `stat-mismatches.json`, `LawnStrings-stale-candidates.json`, `ZombieStrings-stale-candidates.json`, `shooting-diff.json`, and `non-cjk-changes.json`. These reports remain local because they contain extracted game prose.

## Rebuild and test

1. Use the tested prerelease 1 bundle as the input to the narrowly scoped `repair_android40_catalog.py` final correction stage; use official 4.0 as the runtime-string source. A clean rebuild through `migrate_version_text.py` now prevents the faulty internal-string translations in the first place.
2. Supply the checked-in correction rules and official 4.0 `dump.cs`. Reopen and hash every object; only three TextAssets should change relative to prerelease 1. Metadata and audio resources stay byte-identical to prerelease 1.
3. Run the full structural audit, protected-string and catalog-reference checks, actual .NET formatting, tests, APK comparison, signature and alignment checks.
4. On Android: open Almanac > The Gods Almanac after Unlock Everything. Confirm six category buttons, nonzero root count, plant cards and routes. Open several plants and categories, return, and reopen the menu. Try both a fresh save and an existing profile if available.
5. Search Almanac > Plants for 1170, 1035, 1171 and 1202. Check the complete description, scrolling, and corrected values. Confirm Coffee Bean 211 is unchanged. Start a Gods: Evolved round and check selecting a modifier and returning to the Almanac.
6. For remaining glitches, record exact actions, APK version, device/Android version, save origin, and crash log when available. Compare the same steps with official Chinese 4.0 before changing gameplay assumptions.

Do not replace the existing public prerelease asset. This local candidate requires user approval before a separate prerelease 2 publication.

## Original test1 verification

- APK: `PvZ-Fusion-4.0-English-Android-prerelease2-test1.apk`.
- SHA-256: `d6307ea7caeaa1f52b7536df964df27a27d1da949c911b1f0e33541ab7f5bc5f`.
- 42 regression tests and 306 actual .NET formatting checks passed.
- All 206,358 Unity objects and 301 JSON assets passed the full audit, including protected runtime strings. No introduced tag, argument, or plant-token errors.
- Only LawnStrings, ShootingAlmanacIndex, and the internal line-breaking TextAsset differ from prerelease 1 within the bundle. Metadata, music resource, all executable code and other APK content remain unchanged from prerelease 1, except signatures.
- Official-4.0 and prerelease-1 APK comparisons, alignment, and v1/v2/v3 signatures passed. Same signing certificate as prerelease 1. Full build record: `ANDROID40-PRE2-BUILD.json`.
- User confirmed catalog operation and Nugget-shroom on September 22. No GitHub release was created or changed.

## Prerelease 2 rev 2: generic Gods Almanac UI

Requested after the maintainer's 15 screenshots of the working catalog. This is a local APK revision, not a new published release. Test1 remains the device-confirmed baseline.

- 51 metadata display literals: six tabs, base/final/evolution-stage labels, search and empty states, entry counts, selection caps, first-three-levels-free notices, purchase/unlock status and prompts, path headings, availability label, and repeated damage/speed bonus fragments with their quality disclaimer.
- 70 catalog condition fields: Luck requirements, ownership checks, tactic-level prerequisites, maximum-tier purchase requirements, Reinforcement availability, Apex selection chance, and Trial/Purgatory availability. Some remain partly Chinese where they reference an unconfirmed name or zombie type.
- Names use existing PC or already displayed terms: Reinforcement, Apex, Purgatory, Upgrade: Anti-crush, Blast Protection and Enchanted Shield. No plant names, named tactic effects, recipes or specialized descriptions were newly translated.
- Retained the unconfirmed currency name `诸神币`, tactic/group names, named Apex content, two zombie-type condition lines, and short ordinal fragments whose other runtime contexts were not verified. Translating a generic instruction must not rename its referenced content or its internal group key.

Rules and provenance: `assets/gods-almanac-ui-4.0.json`. Every rule records the original source, expected prior English, target and reason. Metadata rules also pin the literal index. Catalog rules pin the entry ID and modify only `condition`. Complete exact PC English takes priority over a fallback; malformed PC format strings are rejected. Changed source aborts the pass. Separately changed English is preserved for review. These rules do not use fuzzy, substring or general regex translation.

Rebuild rev 2 after the catalog repair and factual correction stage, using `scripts/apply_gods_almanac_ui.py`. Supply the repaired test1 bundle/metadata, official 4.0 bundle/metadata, matching type dump, rules, and pinned PC `Strings` directory. Runtime catalog fields must validate before and after the pass. Only the ShootingAlmanacIndex TextAsset changes in this stage; all other Unity objects are hash-verified unchanged. Metadata changes are restricted to the 51 reviewed literal slots. Keep the existing music resource unchanged.

Local work and verbose audits: `work/upgrade40/pre2-ui` in the task workspace. This includes `ui-report.json`, `safety-audit.json`, `dotnet-format-audit.json`, `tests.log`, and APK audit logs. The tracked rev 2 build record is `ANDROID40-PRE2-REV2-BUILD.json`.

Rev 2 automated verification: 46 tests, 312 actual .NET format templates, 206,358 Unity objects, 301 JSON assets, and all 374 catalog reflection references passed. No introduced format, tag or plant-token issues were found. Android rendering and interaction testing of this revision is still pending.

- APK: `PvZ-Fusion-4.0-English-Android-prerelease2-rev2.apk`.
- SHA-256: `fe9e1d587108b1b705dd7969b6af5bde3276c03e9b033efb1854edfab145d069`.
- APK comparisons against official 4.0 and test1 passed. Only the bundle and metadata differ from test1 outside signatures. Music, executable code, package details and other content remain unchanged.
- v1/v2/v3 signatures and ZIP alignment passed using the existing signing certificate. Defender completed with exit code 0.

Quick device retest:

1. Open Almanac > The Gods Almanac. Check all six tabs and the Reinforcement search field, including label fit.
2. Select a base plant and a final plant. Check paths, damage/speed text and maximum selection counts. Open a locked plant's purchase dialog without purchasing and check the first-path explanation.
3. Open Tactic Modifiers, Other Modifiers and Trial Modifiers. Check availability requirements, first-three-levels-free notices and maximum-tier status. Return and reopen the catalog.

Do not infer a currency or tactic translation from a partly translated condition. These deliberately retained names should be replaced only after verified PC wording is available. No gameplay, saves, executable code, audio, or layout changes were requested for rev 2.
