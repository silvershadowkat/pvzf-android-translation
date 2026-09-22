# Android 4.0 English prerelease 1

Release `v4.0-release-1`, September 22, 2026. The maintainer tested and approved local revision 2 for publication as a prerelease. Device model and Android version were not supplied. PC archives are references only.

## Published revision 2

The first candidate received a positive initial user check. The maintainer subsequently tested and approved revision 2. It keeps the first candidate available separately.

- Corrected 24 exact navigation text objects (including shadow labels) from Disabled to Back or Close, based on their button actions. The global PC mapping and genuine disabled states remain unchanged.
- Reviewed 56 additional generic UI mappings. Applied 29 metadata occurrences, 23 Gods Almanac fields, and 5 other serialized labels. Plant reference tokens and runtime formatting remain intact.
- Translated 36 changelog lines using ordinary English and PC Almanac names resolved by ID. An unverified story line and specialized names remain Chinese. The new currency name also remains Chinese until PC supplies it.
- Restored 17 PC replacement music tracks using the previously verified Android encoding. Every source audio blob at the pinned PC 4.0 commit matches the source used for those 3.9 encodes. References and offsets were remapped to fresh 4.0 AudioClips. The other 157 audio clips are byte-identical to official 4.0; the full official resource prefix is preserved and music is appended. The rhythm exception `loon` stays original, and `Battle` has no same-name 4.0 target.
- 35 tests pass. All 206,358 Unity objects and 301 JSON assets validate. All 306 changed runtime templates pass actual .NET formatting; no introduced tag, argument, or plant-token errors.
- Signed APK: `PvZ-Fusion-4.0-English-Android-prerelease1.apk` (identical to tested local `prerelease1-rev2.apk`); SHA-256 `0894dd8fc2dbbcb65166bf0243736c935c3c7738408f971d798bf626a298ad25`.
- Windows Defender custom APK scan on September 22, 2026 reported no threats. This is supporting evidence, not a safety guarantee.
- Signature v1/v2/v3, alignment, and the official-APK comparison pass. Exactly three non-signature entries differ: the Unity bundle, metadata, and `assets/bin/Data/resources.resource`. Manifest, permissions, executable code, and save logic remain official 4.0.

Rules and provenance: `assets/ui-feedback-4.0.json` and `assets/audio-translation-map-4.0.json`. Exact local drivers, field-level reports, safety checks and APK audit are under `work/upgrade40/feedback1`. Run `apply_android_ui_feedback.py` after the initial candidate, then `transplant_android_audio_clips.py` with its explicit donor resource and reviewed 17-track allowlist. Do not transplant an old complete bundle or resource file.

Quick retest: listen on the main menu, plant selection, and one daytime/nighttime level; open and scroll the update notice; use Back in each Almanac; inspect Gods Almanac paths, unlock prompts, and generic modifier effects.

## Initial candidate inputs

| Input | SHA-256 or Git commit |
|---|---|
| Official `pvzrh4.0.apk` | `37234f51c4f17d954257fa8e62d8770075224b0ce17cee98751ab30debaa354f` |
| Official `PC_PVZ-Fusion-4.0.zip` | `514dea07051a2b02454a561fffd05873147796811cd5fedd18075f0ad8addfc7` |
| Stable 3.9 prerelease 9 APK | `d45f25d748b42aac71d36b0706e386b27d1d6ea8fc56a48e350891449ac384c5` |
| Latest PC 3.9 | `d9c05a39e7c0abb09f84ddfb15582885d60a0efe` |
| Pinned PC 4.0 | `9a170fdfa999e4e8dc6fe45e31c0806a1271577d` |
| Candidate APK | `884cc1dca8938eb1d24e5a266f0508a8d70d68fcd997aafd336cd8faa2d16abf` |

PC 3.9 has no new commits since Release 9. All 26 PC 4.0 JSON files parse without the comma repairs needed by the old snapshot. Fresh Android 4.0 metadata and ARM64 IL2CPP generated the matching 66 Dummy DLLs. Unity is now `2022.3.62f1c1`.

## Initial migration results

- 3,208 metadata literal occurrences and 6,043 serialized text fields differ from official Android 4.0.
- Current source-matched PC English takes priority. Historical Android prose carries only when its Chinese source still matches. Almanacs use entity ID and field; serialized UI uses hierarchy and field.
- Of 595 new or changed Chinese metadata literals, the initial PC import translated 259. The remainder require individual source/context review. Later generic additions are tracked separately.
- No unchanged player-facing metadata translation was lost. An internal Unicode table incorrectly treated as translation in an older build is preserved as official data.
- Plant/zombie Almanacs contain 354 new or changed string fields: 155 changed plant fields, 136 fields in new plant records, 36 changed zombie fields, and 27 fields in new zombie records. Four remain Chinese.
- Two English TMP fonts include their 703 glyphs/characters, matching atlases, materials, remapped Android references, and current Chinese fallback. Font atlases are excluded from ordinary artwork copying.
- All 15 old presentation changes still match their 4.0 source layout and were carried. No old object IDs are reused across versions.
- 48 old translated images have identical official 3.9/4.0 source pixels. The renamed Recommended Levels image was separately checked against both official 4.0 builds and the new PC English PNG.
- 35 exact generic UI mappings live in `assets/provisional-ui-4.0.json`. They affect 46 serialized labels, 7 generic Almanac fields, and 7 metadata occurrences. Complete PC English takes priority. No plant, fusion, currency, or skill names were invented.

## Known gaps and exclusions

- PC `LawnStringsTranslate.json` contains two conflicting records for plant ID 5003: Sea-greed Zombox and Pyroboros Pot. Both PC records are quarantined. Old wording can carry only where ID/field/source still matches. ID 5003's changed description and ID 5005's name, lore, and description stay Chinese. Do not guess a replacement ID.
- The new shooting Almanac includes untranslated tactics and mechanics. New currency terminology, specialized instructions, and unavailable PC descriptions remain Chinese. Revision 2 translates ordinary update-note text with verified names.
- Two unchanged zombie lore fields, IDs 38 and 39, still lack usable PC English. These are not new 4.0 regressions.
- Raw remaining-Chinese counts include internal tables, identifiers, credits, and editor documentation. They are not a player-visible completion percentage.
- The initial candidate retained official audio. Revision 2 restores the requested music through an explicit clip allowlist, preserving new 4.0 content.
- Four existing unreadable/non-display MonoBehaviours remain byte-identical. No old schema was used to rewrite them.

## Initial candidate safety checks

- 31 regression tests pass, including duplicate-ID quarantine, complete runtime format specifiers, and rich-text normalization.
- All 206,358 Unity objects remain present. Changes are limited to text, reviewed presentation fields, font dependencies, and translated artwork.
- All 301 JSON assets preserve keys, record counts, IDs, types, and non-string values.
- All 19,573 metadata literals parse. Outside literal storage and 60 validated display-enum name pointers, original metadata bytes are intact. Enum numeric values and other field records are unchanged.
- All changed strings preserve runtime argument IDs and format specifiers. Actual .NET composite formatting accepted all 294 changed templates.
- PC dropped `{0}` from `{0}：剩余时间：{1:F0}秒`. The tracked Android repair preserves both arguments and the numeric format.
- Incomplete PC-added style tags were closed in 161 complete metadata strings. Deliberately open source fragments remain intact. Final audit: zero introduced tag, argument, or game-token issues.
- APK signature schemes v1/v2/v3 and ZIP alignment pass. The existing release certificate is `1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6`.
- Manifest, permissions, ABIs, DEX/native executables, audio, and all other non-signature files match official 4.0 byte for byte. Only `assets/bin/Data/data.unity3d` and `assets/bin/Data/Managed/Metadata/global-metadata.dat` differ.

These checks reduce porting risk. They do not prove device crash freedom, correct rendering, or compatibility of every old save with official 4.0.

## Quick device checks

Use Unlock All if desired.

1. Main menu: inspect Recommended Levels artwork, open Settings and Help, then return. Check English lettering and Chinese fallback characters.
2. Almanac > Plants: search IDs 41-44 and 1462-1483 for new records. Open and fully scroll several descriptions. Also check Icicle-shroom (1035), Death Star (1277), and long fusion recipes.
3. Almanac > Zombies: inspect IDs 92-99 and 262, especially long descriptions and scrolling.
4. The new The Gods: Evolved Almanac: inspect plant paths, search fields, lists, and generic Luck/Damage/Reroll/Shield/Respawn descriptions. Untranslated tactical descriptions are expected.
5. Recommended Levels > The Gods: Evolved: start a round and inspect live upgrade cards, Luck, shields, respawn timers, Damage Share, and Total Modifiers.
6. Recommended Levels: enter the new snow-night content when accessible. Inspect level cards and complete an early round.
7. Fusion showcase/recipe levels: check one old and one new level, including instructions and ordinary wave completion.
8. With a backup available, test an existing 3.9 save and a fresh profile separately. Save, exit, relaunch, and reload. Official 4.0 handles save migration; the port adds no save code.

## Rebuild and handoff

Active branch: `agent/translation-4.0-prerelease1`, based on Release 9 commit `00bdf581462c92b2956a4760430fb85116517a67`.

Local checkpoint: `work/upgrade40` in the task workspace. It contains pinned inputs, generated types, intermediate payloads, field-level source deltas, logs, and `build_*.py` drivers recording exact local paths. Game payloads remain outside Git.

Stages:

1. `build_metadata_translation.py`: official 4.0 metadata, pinned PC 4.0 Strings, official 3.9 previous-version source guard, and the 3.9 prerelease 9 Chinese/English reference pair.
2. `migrate_version_text.py`: fresh 4.0 DLLs and inventories, source-matched Almanacs, and complete PC translations.
3. `replace_unity_font_data.py` then `transplant_tmp_font_asset.py`: two reviewed English fonts and remapped 4.0 dependencies.
4. `migrate_version_layout.py`: source-matching presentation changes.
5. `apply_legacy_texture_translations.py`, then `apply_version_ui.py`.
6. `replace_verified_texture.py`: new PC Recommended Levels PNG, gated by official Android pixel hash `846084469e609a06c2136f672775538fdf4ed48411268e11c485c4ff22a87691`.
7. Structural/text audit, .NET format checks, and tests. Package from official 4.0, align, sign, and run `audit_apk_release.py`.

Key reports: `inputs.json`, `metadata-report.json`, `metadata-carryover-audit.json`, `text-bundle-report.json`, `almanac-source-delta.json`, `font-report.json`, `layout-report.json`, `textures-report.json`, `generic-ui-report.json`, `new-art-report.json`, `safety-audit.json`, `dotnet-format-audit.json`, and `apk/audit-original.json`.

UnityPy pitfall: after saving a tree, `get_raw_data()` and `read_typetree()` still use the original reader. Before saving the bundle, validate `obj.data` or the returned serialized bytes. Reopen the saved bundle for final validation.

## Future fixes and upgrades

- Release tag: `v4.0-release-1`. The APK contains exactly the tested revision 2 bytes; the public filename omits the local revision suffix. See `ANDROID40-PRE1-BUILD.json` for hashes and provenance.
- Keep official Chinese inputs, previous-version Chinese/English references, PC pin, generated types, and intermediate reports separate. Never use a translated bundle as a new-version structural base.
- Review new PC translations against their Chinese sources, IDs and field paths. Recheck duplicate IDs before importing. Do not guess the conflicting plant ID 5003/5005 mapping.
- Track provisional context-aware AI wording in `assets/provisional-ui-4.0.json` and `assets/ui-feedback-4.0.json`. Complete applicable PC English has priority. Navigation overrides are scoped to exact button hierarchies because the global PC value for the Chinese close/off label is ambiguous.
- Preserve complete format specifiers, argument counts, rich-text fragments, `[[plant:...]]` tokens, JSON shapes, IDs and non-text values. Reopen generated bundles; do not validate edits through UnityPy's original reader.
- For music, check current PC source blob hashes before reusing old Android encodes. Remap reviewed clips onto fresh Android objects and append to the official resource file. Preserve all unmapped clips. New or renamed tracks need individual review.
- Rerun tests, structural/string audits, actual .NET formatting, APK comparison, signing and alignment checks. Publish only the exact device-tested APK unless a new build is explicitly tested.
- Keep changes after this release in `docs/RELEASE-NOTES-NEXT.md`. No outstanding gameplay bug fix is claimed by this release.
