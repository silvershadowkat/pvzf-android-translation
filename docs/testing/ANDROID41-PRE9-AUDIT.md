# Android 4.1 prerelease 9 translation audit

Prepared November 24, 2026 from matching immutable public prerelease 8 EN and ENAI inputs. The source-guarded review is `assets/prerelease9-4.1-review.json`; final checksums/results are in `ANDROID41-PRE9-RELEASE-BUILD.json`.

## Gods Almanac context

The 12 known remaining catalog fields are translated by their stable entry IDs. The same Chinese title is reused in three Vanguard tiers, so a global title replacement would lose the distinctions. Travel modifier IDs 13050/13051/13052/13053 supply the existing Blooms names Vanguard/A/B/X and their descriptions. The `[[plant:BlackHoleTorch]]` reference remains unchanged and resolves to the existing PlantType 313 Temporal Torch. All argument and plant-reference tokens are preserved.

The Voodoo Dummy description's contact wording contains a Chinese typo. Native `TrainingDummy.OnTriggerStay2D` checks the target's row and `isMindControlled` before invoking virtual `Zombie.Die` in this mode; its damage path checks the existing modifier and distributes damage. The English description preserves the contact-kill behavior rather than copying an older explanation that lacks it. No mechanics are changed.

A targeted scan of 260 Gods/new-mode string-producing methods also caught the generated tier suffix outside the catalog. Narrow, anchored display rules cover plain and quality-prefixed labels while preserving already-translated Level prefixes. The live Tactical screen additionally exposed raw internal group names inside combined badges. Whole-label rules cover all 13 known tactic groups at ordinary and maximum tiers, including purchased/not-purchased states. Group IDs are not edited. Logging, command parsers and test strings are retained.

## Wider audit

306 JSON TextAssets and 2,098 remaining CJK metadata candidates were inspected through the actual Java translator. Most raw hits require classification: source identifiers, developer logs, editor/test commands and creator credits are not automatically rewritten. The focused fixes cover the trident mechanics article, the Melon Morph showcase and 126 clear shop/equipment/reward/modifier messages, plus related short labels and existing aliases. Canonical plant/zombie/modifier names are reused; straightforward new-item labels are translated consistently from their Chinese wording.

The final census checks 2,968 plant fields, 714 zombie fields, 96 mechanics fields and 519 Gods fields: 4,297 display fields in total, with no remaining CJK after the actual translator. This is a catalog census, not a guarantee that every generated label, texture, optional mode or user-authored level is fully translated. Creator names remain in credits.

Blooms 4.1 was refreshed at ab5d1c03ad44ba2039855381b16045fe54519767, unchanged since prerelease 8. Existing upstream Vanguard and showcase translations are reused. The trident article retains the Android source's 5-second Drenched duration, 25% Speed reduction and 20%-current-HP damage with a minimum of 60. No additional PC-only mechanic claim is imported.

## Integrity and verification

Both bundles are reopened and all 219,584 Unity objects compared; only the three reviewed TextAssets change. Catalog IDs, reflection names, enum values, lookup groups, functional arguments and gameplay data remain unchanged. Metadata is byte-identical to prerelease 8, including all 32 present protected slots. The mechanics Almanac update is synchronized between embedded and restored copies.

Each public APK permits exactly five changed entries: version manifest, Unity bundle, mechanics Almanac, managed integrity manifest and runtime dictionary. DEX, all native libraries (including the pre8 vehicle repair), audio, the ENAI model and its lifecycle implementation remain byte-identical. Signatures, ZIP integrity, compression and 16 KiB alignment are checked by the packager. Automated fixture, restoration, emulator and physical results are recorded in the release build record; 32-bit device runtime testing and exhaustive combat remain outside this translation revision.

