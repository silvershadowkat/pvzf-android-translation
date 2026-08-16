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
  - `Menu/深渊入口.png` belongs to parked Abyss content and is out of scope.

The replacement tool validates that each selected Android asset has one exact
`Texture2D`, one matching `Sprite`, the expected dimensions, and a valid
Sprite-to-Texture2D link. It reopens the output bundle and verifies the written
assets before accepting the result.

The Android sprites originally retained tight polygon meshes generated around
the shapes of the Chinese particle glyphs. Those meshes clipped different parts
of all eight English replacements, including the `M` in `DOOM!!`, the corners
of the `POW!!!` burst, punctuation, and most of the left side of `Light!`.
The bake now replaces each particle's tight mesh with a four-vertex full-canvas
quad. It does not shrink or redraw the PC artwork: texture dimensions, pixels,
pivot, pixels-per-unit, and texture linkage remain unchanged. Reopen validation
requires the complete original-size canvas, four vertices, and FullRect mesh
mode for every translated particle.

## Physical-device checks

Exercise plants and effects that display impact/explosion text and confirm the
Chinese particles are replaced by complete, unclipped PC English artwork. Test
all eight effects where practical, especially `DOOM!!`, the orange `POW!!!`
burst corners, `SPROING!!`, `FLASH!!`, `Light!`, and `FWOOM!!`. Also check that
unrelated menus, credits, and logos are unchanged.
