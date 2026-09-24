# Android 4.0 prerelease 3: September 23 screenshot review

## Status and scope

Local `prerelease3-test1` is based on published prerelease 2 rev 3 plus the metadata-safety diagnostic. The user authorized screenshot triage, a fresh PC check, generic UI corrections and prerelease 3 preparation. Publishing is not authorized yet. No PC executable code was imported.

The user reported that the local diagnostic seemed better but could not be certain. That is encouraging feedback, not proof of a gameplay fix. Earlier missing-choice screenshots were from an older version; retain the distinction documented in the metadata-safety review.

## PC update

Checked branch `4.0` of [Teyliu/PVZF-Translation](https://github.com/Teyliu/PVZF-Translation) on September 23. It advanced from `9a170fdfa999e4e8dc6fe45e31c0806a1271577d` to `e6f597488b4756d1cc43ff223198feae24df64ae` through three commits. Seven files changed: PC DLL, changelog, custom-level titles, custom-level literal/regex text, general literals and travel buffs. See [the machine-readable check](ANDROID40-PRE3-UPSTREAM.json).

Export both `Localization/English` and `Dumps` at the pinned revision before loading PC translations: structured source alignment depends on the Dumps directory. The complete export produces 21 changed exact keys, seven Android display candidates, of which two already match and five need edits. The additional Bombershroom text and titles did not match display fields in this Android snapshot. The PC DLL remains reference-only.

`Strings/gods_evolved.json` is still empty. All 74 remaining Chinese catalog display fields were checked against the complete PC data; none had a complete usable mapping. Do not invent tactic, curse or modifier terminology.

PC's Almanac contains English descriptions for both Sea-greed Zombox and Pyroboros Pot, but assigns both `seedType: 5003`. Android uses 5003 and 5005. Keep both descriptions quarantined pending unambiguous source alignment. The new changelog independently identifies Pyroboros Pot and its Dragonbreath Torcher > Flower Pot recipe, so its Android 5005 display name is now safe to adopt.

## Applied edits

The tracked manifest `assets/prerelease3-display-4.0.json` contains 11 guarded display edits:

- Six metadata literals: Can You Dig It? capitalization, Snow Level 9 prerequisite, Weathering Gale grammar, Passive suffix, Intermediate card stage and Purgatory availability.
- Two JSON display fields: Pyroboros Pot's name and Apex: Inferno's effect. The latter retains `[[plant:...]]` tokens, 600% damage, and the exact existing PC modifier wording `Vulcannon + Epic Twin Inferno-nut Synergy ON!!`.
- Three serialized text fields: Snowy Night navigation, Scratch Off! rules punctuation, and the Android changelog. The changelog replaces five verified names: Pyroboros Pot, Snowbeak, Doom Lily Pad, Astral Convergence and Celestial Beacon. It preserves Android-specific content rather than copying PC installation text.

The `<size=80%>` tag in PC's Snowy Night label is closed for valid Android rich text. Weathering Gale retains the existing Android `<nobr>` wrapper. These are formatting adaptations only.

In addition, the four protected metadata restorations from the diagnostic remain present: slots 16742, 18864, 17502 and 18309. Relative to public prerelease 2 there are ten changed metadata literals and five changed Unity objects. Resource names, reflection types, IDs, group keys, save keys, game tokens, numeric effects and native code remain intact.

## Screenshot dispositions

All files have prefix `Screenshot_2026-09-23-` and suffix `_com.LanPiaoPiao.PlantsVsZombiesRH.jpg` in the user's `Desktop/pvz sep23` folder. Times below uniquely identify the supplied files.

| # | Time | Finding and disposition |
|---|---|---|
| 1 | 08-23-19-254 | Changelog: Doom Lily Pad, Astral Convergence and Celestial Beacon names added from new PC text. |
| 2 | 08-27-49-522 | Puzzle chapter and tutorial labels use resource/loading names. Preserved pending a display adapter. |
| 3 | 08-28-09-223 | Same resource-name issue for chapters 2 and 3. |
| 4 | 08-28-14-170 | Same issue for chapters 3 and 4. |
| 5 | 08-28-17-505 | Same issue for chapters 4 and 5. |
| 6 | 08-28-20-884 | Tutorial, hint and special-thanks labels are also resource names. Preserved. |
| 7 | 08-28-37-790 | Chapter body/title already English; bottom label is resource-derived and retained. |
| 8 | 18-48-59-855 | Gatling Cherrybomber: Passive and Purgatory availability translated; specialized curse body awaits PC. |
| 9 | 18-49-55-411 | Duplicate of the same curse view; same disposition. |
| 10 | 18-50-06-017 | Cherrizilla route: Intermediate replaces Chinese stage label. Existing PC Percentage Damage wording retained. |
| 11 | 18-50-47-967 | Thornminator route: Intermediate stage label translated. |
| 12 | 18-50-58-448 | Magnetar curse: Passive and Purgatory availability translated; specialized curse body awaits PC. |
| 13 | 18-50-54-068 | Magnetar route: Intermediate stage label translated. |
| 14 | 18-52-02-323 | SP Phoenix Threepeater modifier name lacks verified PC wording; retained. |
| 15 | 18-52-41-001 | Luck availability embeds an untranslated tactic name; retained. |
| 16 | 18-52-50-240 | Resourcefulness availability uses the same unverified tactic name; retained. |
| 17 | 18-52-55-875 | Shield availability uses specialized enemy/mode terminology; retained pending PC wording. |
| 18 | 18-53-00-893 | Second Shield availability variant: same disposition. |
| 19 | 18-53-17-075 | Apex: Inferno effect translated using verified PC names and existing plant tokens. |
| 20 | 18-53-21-634 | Remaining Apex name and effect lack usable PC wording; retained. |
| 21 | 18-53-26-379 | First tactic level: name and specialized effect await PC. |
| 22 | 18-53-29-409 | Second tactic level: same disposition. |
| 23 | 18-53-32-047 | Third tactic level: same disposition. |
| 24 | 18-53-35-745 | Maximum tactic purchase dialog: generic UI already English, name/effect await PC. |
| 25 | 18-53-40-452 | Maximum tactic detail: same disposition. |
| 26 | 08-18-53-865 | Snowy Night narrative contains unverified named story terms; retained. Separate prerequisite/navigation messages now use PC English. |
| 27 | 18-56-09-110 | Another maximum-tier tactic dialog: name/effect await verified PC terminology. |
| 28 | 08-21-25-461 | Sea-greed Zombox description quarantined due duplicate PC ID, not absent PC English. |
| 29 | 08-21-32-433 | Lower portion of same description; same disposition. |
| 30 | 08-21-41-598 | Pyroboros Pot name added from PC changelog; description still quarantined. |
| 31 | 08-23-04-858 | Pyroboros Pot name in changelog translated. |
| 32 | 08-23-11-865 | Snowbeak name translated; unverified named Firnace form retained. |

The entire tactic catalog was checked, not just the visible selected group. Existing generic navigation, levels, prices and availability scaffolding remain English. Chinese proper names and specialized effects remain pending.

## Why puzzle labels were not renamed

`CustomIZManager.LoadLevelData` reads TextAsset `Object.get_name` into the custom-level lookup, and `CustomLevelEnter` uses `levelName` to enter a level. Examples include `101CustomIZ1:...` and resource names ending in tutorial/hint text. These strings are both identifiers and visible labels. Their bodies already contain PC chapter text. Renaming the TextAssets could break loading or saved references. A future fix must translate a separate display value while preserving these IDs. No native hooks were added in this pass.

## Rebuild and verification

Use the official Chinese 4.0 APK as the package shell. Reproduce prerelease 2 rev 3, then restore the protected metadata slots as documented in `ANDROID40-METADATA-SAFETY.md`. Apply `scripts/apply_reviewed_display_patch.py` last, supplying:

- `--official`: official 4.0 data.unity3d; `--source`: prerelease 2 rev 3 bundle.
- `--official-metadata`: official metadata; `--metadata`: metadata-safety diagnostic metadata.
- `--rules assets/prerelease3-display-4.0.json`, same-version `--dlls` and `--dump`.
- Explicit `--output`, `--output-metadata` and `--report` paths.

The tool rejects stale source/previous text, runtime catalog fields and protected metadata targets. It preserves .NET argument formatting and plant tokens, validates catalog types, checks UI roundtrips and verifies every output object after reloading. Use the existing 17-track resources.resource payload unchanged. Package, align, sign with the existing release certificate, then run the APK comparison and protected-key checks.

Results: 57 tests passed; 206,358 Unity objects verified; 301 JSON assets retained their shapes, IDs and non-text values; no format issues. Non-text metadata stayed unchanged except the previously approved display-enum field names. All 17 present protected literals match official Chinese. APK audits pass against official 4.0 (only the three approved payload entries differ) and public prerelease 2 (only metadata and bundle differ). Certificate and v1/v2/v3 signatures verified; ZIP alignment verified.

See `ANDROID40-PRE3-BUILD.json`, `ANDROID40-PRE3-VALIDATION.json`, and `ANDROID40-PRE3-UPSTREAM.json` for recorded results. This is structural/static verification, not a substitute for Android play testing. Check the Almanac routes, Apex: Inferno, modifier choices and level entry on device before approving publication.
