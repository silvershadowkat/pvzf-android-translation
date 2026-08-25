# PvZ Fusion 3.9 English Android - Prerelease 6

Prerelease 6 is rebuilt from the official Chinese Android 3.9 APK and the PC
Blooms `3.9` branch at commit
`c2e8f962cb9974c3214d0db95fe98fea0634a2da`. It keeps the original Android
manifest, executable code, native libraries, permissions, and package identity;
only `data.unity3d`, `global-metadata.dat`, and the external
`resources.resource` audio payload differ from the official APK.

This is a prerelease intended for broad community stability testing. Back up
game data before uninstalling or performing a clean-install comparison.

## Download verification

- APK: `PvZ-Fusion-3.9-English-Android-prerelease6.apk`
- SHA-256: `9fb624cc74a896ad67bb139de4be326f10b26f64ef0fc943f47f590f90a572a3`

## Stability fixes

- Fixed the Release 5 TMP font transplant, whose English font assets retained
  dangling 3.8.1 fallback path IDs. Both English fonts now resolve to Android
  3.9's real `汉仪夏日体W SDF` fallback object at path ID `181360`.
- Made an explicit target-bundle fallback mandatory for future font
  transplants and added reopen validation for both fallback tables, the source
  font, material, atlas, and resolved fallback object.
- Added a 3.9 regression audit covering the font chain and the Almanac entries
  implicated in tester reports.

This addresses the reproducible crash in which opening Penny-shroom after
browsing other Almanac entries immediately exited to the Android launcher. The
same bad fallback chain could affect Cattail Girl, the last SP plant entries,
modifier cards, and other screens containing glyphs outside the transplanted
Latin atlas.

## Translation and Almanac fixes

- Updated all PC-sourced English data to Blooms commit `c2e8f96`.
- Fixed the Almanac placeholder detector so legitimate repeated structured
  fields such as plant costs are not discarded. Cattail Girl's cost now comes
  from the current PC translation.
- Fixed Mechanics Almanac exact 3.9 keys taking precedence over historical
  compatibility aliases.
- Fixed the new-content policy restoring the shared `植物机制` category after
  its entries had otherwise been translated. All 40 Mechanics entries now have
  English category, title, and description fields.
- Fixed oversized plant and zombie Almanac descriptions found during candidate
  testing. The low-memory TextAsset refresh had reintroduced the PC project's
  embedded `<size=36>` tags after Android layout polishing; the overlay now
  strips and validates those Android-incompatible overrides.
- Updated Penny-shroom, Cattail Girl, SP Phoenix Threepeater, Quetzalcoatl
  Blover, SP Phoenix Drone, and the rest of the 682-record plant database from
  the current aligned PC Almanac.
- Updated Spruce Sharpshooter to the current PC description, removing the
  obsolete freeze/glaciation immunity claim.
- Updated current PC changelog, tips, modifier strings, travel data, textures,
  and other exact/structured translations where the PC source provides them.
- Kept official Chinese where the current PC project has no aligned usable
  English translation.

## Translated music

- Replaced 17 same-name Android music clips with the current PC Blooms tracks:
  Boss2, Day, Day_drum, Fog, Fog_drum, Garden, IZ, MainMenu, Night,
  Night_drum, Pool, Pool_drum, Roof, Roof_drum, Roof_pre, SelectCard, and
  UltimateBattle.
- Encoded the tracks for Android with the game's Unity version,
  Unity 2022.3.62f1, instead of inserting desktop MP3/OGG bytes.
- Replaced the tracks directly with no music toggle. `Battle` was not included
  because Android 3.9 has no same-name clip; `loon` intentionally remains the
  original Android clip to preserve the PC translator's rhythm-game exception.

## Validation

- 682 unique plant records retained; all six reported critical plants exactly
  match the current PC data after Android punctuation normalization.
- 40 Mechanics Almanac records retained with zero CJK fields in category,
  title, or description.
- Both English TMP fonts reopen with 703 glyphs/characters and fallback path ID
  `181360` in both fallback tables.
- APK content audit passes: manifest/badging unchanged, no added non-signature
  files, no unexpected changed entries, and every DEX/native executable is
  byte-identical to official Android 3.9.
- APK is zip-aligned and verifies under v1, v2, and v3 signature schemes with
  the same project certificate used for prerelease 5.
- Exactly the 17 allowlisted AudioClip objects changed; the other 156 clips are
  byte-identical. The original external Android `resources.resource` remains
  an identical prefix, followed only by the 17 newly encoded music payloads.

## Community retesting requested

This is a local candidate, not a claim that every reported crash is fixed.
The broken font fallback was global and could make unrelated text-heavy screens
appear to crash randomly, so the community should specifically retest every
previously reported scenario below.

### Highest-priority stability checks

1. **Penny-shroom Almanac crash and description corruption**
   - Open several other plant descriptions first, using both the plant tiles
     and the Previous/Next buttons, and then open Penny-shroom.
   - Confirm the game stays open, Penny-shroom always shows its own description,
     and returning to earlier plants does not replace either description.
   - Repeat in different navigation orders and after reopening the Almanac.
2. **Cattail Girl Almanac corruption**
   - Repeat the same sequence with Cattail Girl after viewing several other
     plants. Confirm its description and cost remain correct.
3. **Last SP Almanac entries**
   - Alternate among SP Phoenix Threepeater, Quetzalcoatl Blover, the preceding
     plant, and the Previous/Next buttons.
   - Confirm each description appears, changes with the selected plant, and is
     not blank or stuck on the prior entry.
4. **Odyssey / Survival modifier transitions**
   - Complete more than one round and reach every post-battle modifier choice.
   - Confirm the modifier cards populate after round 1, their descriptions are
     visible, selecting/rerolling/skipping works, and the game does not crash.
5. **Cursed Purgatory and Gods Evolution choices**
   - Open plant-modifier selections in Cursed Purgatory and card choices in
     Gods Evolution.
   - Confirm every card has a name/description when expected and that opening,
     selecting, rerolling, or skipping a card does not crash.
6. **General crash soak**
   - Test launching the game, opening seed selection, starting several
     different levels, placing plants, and playing continuously for at least
     15-30 minutes.
   - Include devices that frequently crashed on prerelease 5, especially the
     reported Galaxy Tab S9, and note whether the candidate was installed over
     an older build or as a clean install.
   - Back up game data before uninstalling or attempting a clean-install test;
     testers should not risk an existing save solely for this checklist.
   - Specifically retry placing the purple/green mushroom highlighted by the
     red arrow in the original report.

### Targeted gameplay and interface checks

7. **Solitary Spear zombie health display**
   - Repeatedly toggle or click the zombie-health display during active waves,
     including with many zombies present. Confirm it no longer force-closes.
8. **Reported Torchwood fusion setup**
   - Recreate Scorchwood in back, Doomwood in front, with a Peashooter, then
     reverse placement order if possible. Report whether either sequence still
     crashes. No direct gameplay-code fix is claimed for this report.
9. **Spike Cabbage in Sandbox**
   - Verify whether Spike Cabbage attacks and interacts correctly in Sandbox
     and compare it with a normal level. No direct fix is claimed; this may be
     an upstream Chinese 3.9 gameplay issue.
10. **Spruce Sharpshooter mechanics**
    - Confirm its English description no longer promises freeze/glaciation
      immunity and compare the described behavior with its actual current 3.9
      behavior.
11. **Mechanics Almanac**
    - Browse all categories and entries, particularly the magnetic-system page
      shown in the report. Confirm category labels, titles, and descriptions
      display in English and change correctly when navigating.
12. **Modifier Almanac and recipe cards**
    - Browse every modifier category, including the duplicated-looking entries
      and the cards previously showing Chinese names or blank descriptions.
    - Check fusion/evolution recipe cards for correct plant names, wrapping,
      and non-blank text. Chinese is expected only where the pinned PC Blooms
      source has no aligned English translation.
13. **Changelog and general translation smoke test**
    - Open the in-game changelog and confirm it displays the current English
      3.9 text. Report any newly introduced Chinese text, blank label, stuck
      description, clipped text, or suspiciously old mechanic description.
14. **Audio smoke test**
    - Confirm the translated Blooms music plays in the main menu, plant select,
      Garden, `I, Zombie`, daytime, nighttime, pool, fog, roof, boss, and Ultimate
      Battle contexts.
    - Check that drum stems remain synchronized, loops and transitions are
      clean, and volume is reasonable. Pay particular attention to `Roof_pre`.
    - Confirm the rhythm minigame still behaves correctly with the unchanged
      original `loon` clip, and confirm sound effects are otherwise unchanged.

### What to include with a failed test

Please include the device model, Android version, whether this was a clean
install or an update, the game mode/level, exact steps and placement order, and
whether the issue reproduces consistently. **A video showing exactly how to
reproduce the issue is extremely helpful**: start recording before the relevant
menu, navigation sequence, plant placement, card selection, or other trigger so
testers can see the complete lead-up rather than only the final error screen.
For a crash, also include the approximate time of the crash and an Android
logcat excerpt if available. Do not include account details or other personal
information. Reports that only say "random crash" are still welcome, but the
last plant/card/screen opened before the crash is especially important.

The corrected build passed an initial physical-device audio smoke test, but it
still needs broad community stability testing across devices and game modes.
