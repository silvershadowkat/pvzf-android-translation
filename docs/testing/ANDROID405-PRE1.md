# Android 4.0.5 prerelease 1 local test

Prepared October 20, 2026 on `agent/translation-4.0.5-prerelease1`, based on `ac8989b5d345c65f87df005d04ef4b8d1b8003b5`.
Publication update, October 20: the maintainer completed an S26 Ultra smoke test, reported generally smooth behavior with no obvious issues, and approved this APK unchanged for prerelease publication. Gods Almanac/tactics translation gaps remain. See `ANDROID405-PRE1-RELEASE-BUILD.json`. The preparation record below describes checks performed before that device test.

## Local handoff

- Repository: `C:\Users\plim\Documents\Codex\Projects\Plants-Vs-Zombies-Fusion\source\pvzf-android-translation`
- Working evidence: `C:\Users\plim\Documents\Codex\2026-09-06\https-github-com-silvershadowkat-pvzf-android\work\upgrade405`
- APK: `C:\Users\plim\Documents\Codex\Projects\Plants-Vs-Zombies-Fusion\releases\4.0.5-English\prerelease-1\PvZ-Fusion-4.0.5-English-Android-prerelease1-test1.apk`
- APK SHA-256: `37bd30c401cf7ee89484aaa28fff405dab990a00509a10994237639e47f915c1`
- Size: 655043488 bytes.
- Build, validation and upstream records are adjacent to this document.

## Inputs and upstream

Used the supplied official Android APK and PC archive, with hashes recorded in `ANDROID405-PRE1-UPSTREAM.json`.
The PC translation branch `4.0` advanced by 18 commits from `e6f597488b4756d1cc43ff223198feae24df64ae` to `94b9ec0aecc3cea494c5b2c2883a7cbf14642440`.
The latest commit is October 1. The October 20 remote check found no newer commit on that version branch.
Both supplied 4.0.5 Almanac databases match the current PC source dumps exactly.

Current usable PC text takes precedence over previous Android fallbacks, including assisted UI text.
The metadata importer reports 81 Android fallback mappings and 12 reviewed UI mappings superseded by PC English. These are mapping counts, not necessarily distinct on-screen occurrences.
Unchanged Chinese source is required before previous Android text can carry forward.
The bundle pass uses 3,541 source-aligned Almanac fields, 279 tips, 47 mechanics fields, 1,469 exact PC strings and 333 complete PC regex matches. Another 392 fields retain English only after unchanged-source checks.

## Review of changed Chinese

Compared every plant and zombie field between official 4.0 and 4.0.5: 60 changed plant fields, 16 fields in four new plant records, and three changed zombie fields.
The new plant IDs are 1484 through 1487. One changed field remains Chinese because its PC record is ambiguous.
The explicit factual manifest corrects 21 Almanac fields and seven metadata strings, with one serialized UI counterpart. Every edit requires both the current Chinese and previous English to match.

Examples include Doomwarp-shroom's 3,240 damage, 1,000 toughness for three fusion items, the 0.1% Gatling Cherrybomber synergy, Portal-pult's slow and explosion details, an omitted Pyroboros Pot bonus, a 30% overall attack bonus and Focused Fire's halved shot requirement.
Ten older factual corrections remained valid under exact current-source checks. Changed sources were reviewed again.
The drawing option previously mapped to `N/A` now explains its function. Magic Plantbrush uses the established PC name and faithful basic instructions.
The explicit overrides preserve verified PC terminology and correct numeric/source omissions rather than inventing specialized names.

## Presentation and stability

Built from fresh 4.0.5 files. No old Unity bundle or metadata is substituted wholesale.
Only `data.unity3d`, `global-metadata.dat` and `resources.resource` differ from the official APK, excluding signing entries. Native libraries, manifest, permissions and all other payloads are byte-identical.
The migration no longer substitutes text using two hard-coded object IDs from an older release.
Runtime types, internal catalog/group strings and 31 protected metadata keys remain guarded. Seventeen protected literals are present in this version and all are original.
All 208,662 Unity objects were checked. All 302 JSON assets retain structure, IDs and nontext values. The 176 components whose original trees cannot be decoded were left byte-identical; any edited undecodable component would fail the audit.
Two fonts and their dependencies were remapped, retaining Chinese fallback support. The 17 reviewed audio replacements preserve the original resource prefix and leave 157 other clips untouched.
All 20 relevant upstream music blobs match the previous PC pin, so there are no new music replacements to import.
Textures use source/pixel guards. Missing old `TowerEnter` and abyss entrance textures were skipped; font atlas dependencies are handled by the font pass.
There are 64 reviewed serialized UI edits and 15 carried layout adjustments. The new drawing/editor labels were checked against font glyph advances and existing rectangle sizes. Two narrow captions were shortened to `Picker` and `Rect`. This is a static fit check, not a device rendering test.
Ninety-nine translated complete metadata strings had unclosed rich-text styles balanced. Original open runtime fragments remain open.

## Screenshot review

Reviewed all 30 files under `C:/Users/plim/Desktop/pvz sep23/oct20`.
Eighteen are byte-identical to the earlier September 23 set. The 12 additional files show SP Phoenix Threepeater reinforcement text and the Solar Reactor/Hammer tactic levels and unlock dialogs.
Generic UI and unambiguous effects carry forward where source-compatible. Current `gods_evolved.json` remains empty, so specialized tactic names and effects without usable PC text remain Chinese.
Sea-greed Zombox and Pyroboros Pot descriptions remain quarantined because the PC records conflict. Verified names can still be used independently.
Puzzle labels also function as level-loading resource names. This build does not rename those resources or introduce a runtime hook.
The supplied screenshots predate this build and do not count as device validation.

## Checks

- 62 automated tests passed.
- 315 actual .NET formatting checks passed.
- No bundle/metadata format issues; protected catalog references validated against fresh 4.0.5 type dumps.
- APK content comparison, ZIP alignment, v1/v2/v3 signatures and existing signing certificate passed.
- Defender custom scan reported no threats.
- No game or emulator launched. Device behavior, visual fit and performance remain unverified.

## Build sequence and evidence

All intermediate files and bounded command logs are under the working-evidence path above.
Task scripts in `C:\Users\plim\Documents\Codex\2026-09-06\https-github-com-silvershadowkat-pvzf-android\work` record the exact local command lines:

1. `prepare405.py` and `sources405.py`: hash/extract inputs, export the pinned PC tree and generate current Android types.
2. `upgrade405/scan_bundle.py`: inventory new Chinese and actual previous English.
3. `build405_base.py`: metadata and bundle text migration, font dependency remapping, semantic layout migration and guarded texture reuse.
4. `prepare405_review.py` and `build405_finish.py`: reviewed display rules and audio remapping.
5. `audit405_finish.py`: complete-string rich-text balancing and compact caption fixes.
6. `review405_facts.py` and `final405_review.py`: exact-source factual corrections and final validation.
7. `package405.py`: official-shell packaging, alignment, signing, payload comparison and hashes.
8. `verify405_reference.py`: supplied PC source comparison and Defender scan.

The work scripts are historical stage runners, not idempotent all-in-one rebuild commands. Reapply reviewed manifests only to the documented input stage. The caption-fit pass is already reflected in `assets/display-4.0.5.json`.
Persistent repository changes include the metadata normalizer, protected-remnant validation, version-safe inventory migration, regression tests, and three 4.0.5 review manifests.

## Suggested device smoke test

1. Install over the current English app and confirm the existing profile/progress loads. Play a normal level, return to the menu, close and reopen the app.
2. Open The Gods Almanac and browse plants, reinforcement, other, apex and tactic tabs. Start a Gods run and reach a modifier choice.
3. Inspect new 4.0.5 plants and changed descriptions, especially Portal-pult, Doomwarp-shroom, Shield Tundraweed and Pyroboros Pot.
4. Open the drawing/editor screens if accessible. Check compact controls, scrolling, navigation and text clipping. No additional Android gameplay support was added.
5. Listen for music and watch for new lag during a representative busy wave.

The user subsequently approved this exact local build after testing. Publish unchanged as `v4.0.5-release-1`; any later fixes require a new artifact and checks.
