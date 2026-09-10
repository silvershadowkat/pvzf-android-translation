# Tyrannoflora Lux and Firnessence Panacea — September 9

Checked latest PC 3.9 commit `e24586aaf9feb85eae6fc30af3460237778558ff`, original
Android text, release 6, and the current candidate. Both reports identify real
release-6 translation gaps. Both corrections are now applied locally.

## Tyrannoflora Lux (951)

The name, story and separate recipe were already English; the gameplay `info`
field remained Chinese. PC has a complete English description aligned to the
exact same source field. The placeholder filter rejected it because one
modifier includes "currently bugged and does nothing". That is a gameplay bug
note within a complete description, not a missing translation.

Allowed only this exact full PC field by SHA-256:
`d766c7fcc2896d1e36dfb40ab1c46ea3b6a7d8e877c83479e91dff2845023cfb`.
It is also present at the pinned September 6 PC source. Other placeholders and
unreviewed changes remain rejected. Name, story and separate recipe are unchanged.

Copied PC English verbatim apart from existing Android size-tag formatting.
PC's mechanics wording differs from its own Chinese source dump: it states
`5 + (Sum Toughness of Zombies)^0.33s` digestion, 10 seconds less digestion per
Lumos level (minimum 5 seconds), and doubled attack range with a bug note. The
Chinese prose instead gives `8+3×ln(...)`, a light-level speed multiplier, and
1.5 extra tiles. The PC source dump still exactly matches Android's Chinese
field. Following the user's PC-wording authority, this imports the complete
PC English without inventing a hybrid or changing mechanics. Actual Android
behavior has not been checked in-game; PC wording parity does not verify those
formulas or constitute a gameplay bug fix.

## Firnessence Panacea (5004)

The Almanac already matches PC: **Firnessence Panacea**, recipe **Firnurse +
Aloe Nivea**. Actual release-6 metadata literal 1785 uses "Ultimate Little Pine
Furnace", "Super Little Pine Furnace" and "Snowspike Aloe", with an unnecessary
undiscovered-plant prompt. This mismatch is in the released payload.

Imported latest PC `travel_buffs.json`, `unlocks.27`, verbatim:

> Unlock Firnessence Panacea: Firnurse + Aloe Nivea

Its Chinese source exactly matches the Android literal. The explicit manifest
`docs/pc-reviewed-records.json` now contains unlocks 14 and 27; the Kelptain
record was rechecked against the same latest commit and retained unchanged.
The main PC checkout stays pinned. No unrelated PC modifier or executable
updates were imported, and no historical fallbacks were automatically reverted.

## Verification and continuation

- Rebuilt metadata from clean official 3.9 with release-6 preservation and both
  explicit PC records. Only literal 1785 changed versus the previous candidate.
  Other 19,060 literals, including earlier counter and Kelptain corrections,
  and non-literal metadata bytes are unchanged apart from text bookkeeping.
- The final bundle pass changed only plant 951's `info` in `LawnStrings`.
  Reopened and verified all 201,406 objects: untouched bytes match and the
  intended serialized-text replacement matches exactly. No font, layout,
  image, audio, ID, executable or other non-text data changed.
- All 17 regression tests pass. The build additionally verifies the exact
  reviewed description is accepted but an appended TODO is rejected.
- No device/gameplay or visual-fit testing yet. No APK, signing, release or
  cheats-version changes. Build/test processes exited; no task worker remains.

Current candidate files remain in task `work/english-audit/`:
`data-pc-reconciled.unity3d`, `global-metadata.dat`, and `metadata-report.json`.
Future metadata builds must use `--pc-records docs/pc-reviewed-records.json`.
Incremental evidence: `outputs/lux-firnessence-verification.json`,
`outputs/lux-bundle-verification.json`, and `outputs/lux-firnessence-check.json`.
Logs and before/after payloads are under `work/lux-firnessence/`. Historical
reports describe their earlier checkpoints; cumulative metadata corrections
since release 6 now total 18 literal occurrences. Both findings are recorded
once as prepared corrections in the running release notes.
