# Android 4.1 vehicle investigation

Prepared November 20, 2026. Scope: regular Zomboni (`DriverZombie`, zombie 16), red Bobsled Zomboni (`SuperDriverZombie`, zombie 18), associated prefabs/resources and base Survival: Fog (Endless). Tests use a dedicated Android 34 x86_64 emulator running the ARM64 game through native translation. No physical phone was operated. No private-mod APK was a public build input.

## Evidence and reproduction

The supplied 104-second recording is Odyssey: Abyssal Garg Route, Round 9, Difficulty 5. Overlapping enemies, cold, smoke and star effects prevent reliable tracking of an individual vehicle throughout the clip. It does not identify an installed release. The separate chat report explicitly identifies base Survival: Fog (Endless), rapid pult attacks and the first damaged body stage.

An instrumented base Fog Endless board uses actual Melon Tri-pult (1433), Brood-shroom (1300), Icicle-shroom (1035) and Cryomancer Pea (1443) projectiles. Initially ordinary damage transitions worked. A repeated 4x mixed-attack trial then reproduced a live regular Zomboni leaving the lawn: its root Y moved from -4.2625 through -5.3174 and +15.2223 to roughly +1575/-323. Its health stalled at 790, its collider remained enabled, and its sprites stayed enabled/opaque. No managed exception occurred. Thus the entity became invisible and effectively unhittable by leaving the attack area, rather than having its artwork merely hidden.

## Root cause

The stock Android 4.1 `Zombie.Update -> MoveUpdate -> PositionUpdate` path invokes `DriverZombie.SetGroundedDriverVelocity`. That helper computes `(groundY - axisY) / max(Time.fixedDeltaTime, 0.0001)` and stores it as vertical Rigidbody2D velocity. The velocity remains in effect over the intervening physics steps. When several physics steps occur before the next rendered Update, the ground-height correction overshoots; even a subpixel floating-point difference can grow into alternating extreme positions. Busy combat and time scaling expose the problem. The observed 4x trial is a stress reproduction; it does not establish that every reporter used time scaling or that cold damage itself is the cause.

A controlled A/B trial adds a 0.00001-unit vertical perturbation to make the timing defect repeatable. With the stock helper, ordinary Zomboni Y reached -1541.802 while retaining 1190 HP; the red vehicle reached +417.3083 while retaining 2620 HP. With the correction enabled, both remained at Y=-4.2625 and continued taking real projectile damage.

## Scoped repair

`runtime/vehicle_grounding.inc` hooks the helper by class/method metadata. It calls the original calculation, converts that one-step correction into a direct vertical Rigidbody2D position adjustment, and clears only its vertical velocity. It uses the Rigidbody origin, preserving the prefab's animated-axis offset. The original horizontal velocity, terrain height, roof adjustment, slowing, direction, HP, attack and ice-road behavior remain under the game's code. Required methods/fields are checked before installing the hook; invalid numeric data retains the original path. No game offsets or global physics/time settings are patched.

The separate confirmed sprite-cache defect also remains repaired: stock `GameAPP.LoadSprite` assigns `Zombie_zamboni_2_damage2` to both rear damage slots 31 and 32. The scoped GC-barrier-safe repair restores the existing damage1 asset only for that exact cache state. That sprite mixup alone does not explain invulnerability.

## Validation and limits

The C++ regression models a held ground-correction velocity over multiple physics steps, reproduces divergence from subpixel error, verifies stable direct correction and physics-origin offset preservation, and rejects non-finite data. It compiles for Android x86_64 and passes on the test emulator. Actual final-runtime mixed-projectile trial results are recorded separately in `ANDROID41-PRE6-VEHICLE-TESTS.json`.

The inspected 559 vehicle prefab hierarchy objects are unchanged from the original Chinese game. Original vehicle textures retain valid ASTC 6x6 stream sizes; no translated string was found in the audited vehicle damage/movement path. This supports an upstream movement defect. Confirmation on an affected reporter's physical hardware is still pending, and the repair is not a guarantee against every possible bobsled-related issue.
