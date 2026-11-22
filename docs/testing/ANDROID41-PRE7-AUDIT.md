# Android 4.1 pre7 description audit

## Scope and evidence

All 742 plant and 238 zombie Almanac entries were matched by their scoped
`PlantType`/`ZombieType` enum IDs to the shipped Android 4.1 data assets. The
bundle contains 764 plant and 240 zombie configuration records, including
entities without Almanac entries. No Almanac entity lacked a matching record.

The direct comparison covered health, armor, base attack damage and firing
intervals. Source-versus-English numeric differences were also screened for
effect descriptions and upgrade prices. A data mismatch is a candidate, not
automatic proof: projectile damage, ability reloads, persistent hit ticks and
derived child health can differ from a base configuration field. Native code
was traced for these exceptions before changing the descriptions.

`ANDROID41-PRE7-STATS-AUDIT.json` records every entity's data-object hash,
configuration values, source/target description hashes and retained exceptions.
`assets/prerelease7-4.1-review.json` contains exact previous/source guards and
the replacement prose. This is a static description audit with targeted runtime
startup checks, not exhaustive combat testing of every effect or upgrade.

## Corrections

| Plants | Verified correction |
| --- | --- |
| 212-216 | Item health 2000 -> 1000. |
| 217 Holographic Obsidian Tall-nut | Health 20000 -> 4000; creation sets the holographic type without replacing health. |
| 235 Doubleblast Passionfruit | Firing 1.5s -> 3s; normal/Ultimate armor bonus uses 20% of current Type 1 armor. Giant seed has 40 base damage and shrinks size/HP to 70%. |
| 351 Sunrise-shroom TD | Two branch prices 150 -> 160 Sun, per current official 4.1 upgrade descriptions. |
| 353 Star-nut TD | Basic upgrade adds fixed 2000 HP, rather than 50%; branch multiplies both current and maximum HP by three. |
| 947 Lifereaver Spruce | Distinguish firing every 1.5s from saw hits every 0.02s for 5s. |
| 952 Litter-pult | Firing 2s -> 3s; inherited interval is not overridden. |
| 955 Selene Cabbage | Firing 1.5s -> 2s. |
| 957 Maelonstorm | Firing 0.35s -> 0.5s; its update uses the actual interval field. |
| 1035 Icicle-shroom | 20 damage every 2.25s, replacing stale 1.5s. |
| 1051 Kelp-spreader | 20x3 -> 30x3 damage. |
| 1121 Cob-pult | 120 -> 140 damage every 3s. |
| 1170 Nugget-shroom | Firing 1.5s -> 2s. Chinese prose also has a stale 2.25s; `Awake` does not override the 2s data value. |
| 1196 Spring Melon | Firing 4s -> 3s. |
| 1220 Spruce Supershooter | Distinguish firing every 3s from 0.02s needle hits over 1.5s. |
| 1318 Pumpkin Pod | Twice the contained plant's interval, minimum 3s; remove nonexistent fixed 6s maximum. |
| 4001 Friendly Snowbeak | Health 3000 -> 4000; initialization does not replace it. |
| 41, 1095, 1202, 1452 | Revalidate earlier source-guarded Tundraweed, Starpick, Squash Pumpkin and Hungry-shroom factual corrections against the current source. |

| Zombies | Verified correction |
| --- | --- |
| 21, 22, 23 | Box armor 4400/2200/1100 -> 3000/1350/720. |
| 34 Melon Pogo | Health/armor 270+2200 -> 720+1100. |
| 44, 46 Dr. Zomboss forms | Health 60000 -> 45000. |
| 55 Frost Legion Blockhead | Base health 500 -> 270. |
| 94 Vibroblade Automaton | 500 health, no force-shield armor or copied shield-immunity claim. Its class inherits `LostMachine`, rather than shielded `LostMachineII`. |
| 120 Doom-shroom Zombie | Health 1350 -> 1500. |
| 235 Imperor | Health 18000 -> 12000; remove an unrelated attack claim because `ImpKing.CanAttack` returns false. |
| 332 Eternal Wraith | Replace unrelated 300/1.5s claim with 1000 non-bite damage. |

## Important retained exceptions

- Soot-shroom's manual `Shoot` resets its reload to 30s; the unused base 60s
  field must not replace the ability's correct 30s description.
- Twin Saw-me-not melee ticks and beam-family ticks differ from firing cycles.
- Spicy Starfruit's 100x25 effect differs from its base explosion field.
- Land/Sea-mine initial 900 damage differs from the full 1800 blast.
- Starburst-shroom's formula describes a variable number of projectiles.
- Spuddy-shroom's 600 damage is correct even though Chinese prose says 60.
- Necroflame's dummy zombie creates plant 228; its 1 HP configuration must not
  replace the described plant's 300 HP.
- Grounded Sharkmarine uses derived parent health and projectile ticks.
- Other ranged zombie damage values are not replaced with unrelated bite damage.
- Algebraically equivalent percentage descriptions are retained. For example,
  0.2% of an average equals 0.1% of the corresponding sum.

Selected native evidence: Plant Info `GetPlantInfo` 0x23a97ec reads the plant's
current interval directly; `BuildModernStats` 0x23ac24c consumes protected
newline/full-width-colon templates. These templates remain unchanged.
`Bullet_passionFruit.HitZombie` 0x2036610 uses 0.2 armor and 0.7 shrink factors.
`DoomFume.Shoot` 0x21c2ee0 sets its 30s reload. `PeaPumpkin.AttributeEvent`
0x215e084 clamps only the minimum interval. `Tower_starNut.Upgrade` 0x22369b8
adds fixed 2000 or multiplies both health fields. `ImpKing.CanAttack`
0x22728bc returns false. `LostMachineIII` has no shield `BodyTakeDamage`
override; its constructor 0x2280cb4 delegates to `LostMachine`.

## Translation and packaging safety

Blooms 4.1 is pinned at `c4872b81c7a846c102a47b54683a3a52e20b652e`.
The import updates 32 Gods descriptions and 18 matching fusion-showcase fields,
plus related runtime wording. PC placeholder drawing instructions and the
malformed `{0s}` currency replacement are excluded. Existing Android drawing
instructions and the validated currency rule remain effective.

Each edition is derived independently from its matching immutable pre6 APK.
Only approved display fields, corresponding metadata literals, dictionary,
managed language files and version manifests change. All 219,584 Unity objects
are compared before/after for each edition. Only approved TextAssets differ;
every gameplay configuration, prefab, sprite and other object is unchanged.
Native game code, bridge code, Java DEX, audio and recognition assets remain
byte-identical to that edition's pre6 base. The pre6 vehicle repair is retained.

The resulting manifest hashes refresh stale language files after an update or
backup restoration. Save files are excluded from that inventory. Runtime
Current Stats remains dynamic and is not hardcoded to Almanac base values.
