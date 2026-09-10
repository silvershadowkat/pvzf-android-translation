# PC update check — September 10

Compared reviewed PC 3.9 commit `e24586aaf9feb85eae6fc30af3460237778558ff`
with remote branch tip `9afdca02ffba383582b44d5225be1fd9e62cc854`.
Three new commits changed three English files. The existing PC checkout
stays at its prior pin; an isolated snapshot supplies the current inputs.

## Imported

- `travel_buffs.json`, `debuffs.36`: completed Undead March description,
  `Buckshot Commando Zombie: Now ignores plants when moving`. Android source
  meaning matches; metadata literal 17651 now contains the full PC card.
- `translation_regexs.json`: fixed the extra space in the Game Speed match
  and added a 75% size prefix. Android literal 18730 now reads
  `<size=75%>Game Speed: ×{0:F2}</size>`. Added only the missing closing size
  tag; preserved the PC wording and Android numeric format.
- Upstream fixed Jinxed's missing JSON comma, so this snapshot needs no local
  syntax repair. `gods_evolved.json` changed indentation only.

No Almanac, recipe, showcase, texture, audio, or source-dump updates occurred
in this upstream range. The earlier Icicle-shroom and Ultra Mecha-nut
discrepancies remain unresolved by these commits.

## Validation and inputs

- All 25 exported JSON files parse strictly without syntax repair.
- Exactly two of 19,061 metadata literals changed. Every other literal and
  non-literal metadata structure is unchanged; placeholders and paired markup
  are checked. Purgatory and Gacha feedback corrections are preserved.
- Reconciliation against the current bundle found zero further asset changes.
- All 21 tests pass.
- Snapshot: task workspace `work/pc-refresh-sept10/pc-source`.
- Future metadata/reconciliation runs must use that snapshot's Strings and
  Localization/English paths, plus the existing reviewed-records manifest.
- Candidate metadata SHA-256:
  `ccb4c7fef2308a69297254add15b384634439d3c1948e63d8d20a306f0ba3683`.
- Detailed result: task workspace `outputs/PC-REFRESH-2026-09-10.json`.

Updates are staged locally. No APK was packaged for this refresh; the existing
Release 7 test2 APK does not contain these two new translations. Nothing was
pushed or published. Android runtime testing remains pending.
