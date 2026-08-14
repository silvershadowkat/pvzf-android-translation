# PC Particle Texture Audit

The Android 3.8.1 data bundle was compared against all 60 PNG replacements in
the PC English translation texture catalog by exact asset name and dimensions.

## Result

- 39 textures were already localized, with remaining pixel differences
  attributable to Android/Unity texture compression.
- 10 PC textures have no exact Android 3.8.1 `Texture2D` target.
- 8 particle textures were genuine untranslated matches and are now replaced:
  `Dong`, `Doom`, `ExplosionPowie`, `ExplosionSpudow`, `guang`, `Pow`,
  `Sproing`, and `SunExplosionPowie`.
- 3 exact matches are intentionally preserved:
  - `Logo/Logo3.6.png` is obsolete version-specific 3.6 artwork.
  - `Menu/thanks.png` is the approved Android credits parchment.
  - The Abyss entrance texture belongs to parked content and is out of scope.

The replacement tool validates that each selected Android asset has one exact
`Texture2D`, one matching `Sprite`, the expected dimensions, and a valid
Sprite-to-Texture2D link. It reopens the output bundle and verifies the written
assets before accepting the result.

## Physical-device checks

Exercise plants and effects that display impact/explosion text and confirm the
Chinese particles are replaced by their PC English artwork. In particular, the
large purple cloud shown in the original report uses `Dong` (English artwork:
`FWOOM!!`). Also check that unrelated menus, credits, and logos are unchanged.
