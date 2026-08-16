# Discord screenshot and video audit - 2026-08-14

This audit records the reported screens, the evidence found in Android 3.8.1
and the PC translation, and the physical-device checks still required. Reports
from builds older than the current candidate were rechecked against the current
payload before being classified as new work.

## Translation corrections

- **Investment Odyssey:** PC `travel_buffs.json` already provides the English
  descriptions, but all 42 Investment `name` fields are blank. Android displays
  Chinese `InvestBuff` enum member names in that gap. The Android metadata pass
  now supplies validated English display titles while retaining the PC
  descriptions and all original enum values.
- **The Gods: Evolved:** the Android-only Buckshot Commando suffix now completes
  the PC sentence as `Buckshot Commando: -10 shots needed for ultimate`.
- **Princess Solarnova inspection:** HP, damage, production cooldown, and Lumos
  level retain their source newline separators. The run-together screenshot was
  produced by an older payload and must be retested with the current candidate.
- **Damage Statistics:** Android constructs the hypnotized-zombie total from a
  standalone `魅惑僵尸` label and a separate damage fragment, so the PC
  translator's complete-row regex translated only the latter in the packaged
  metadata. The Android exact adapter now renders the missing label as
  `Hypnotized Zombies`, matching the PC community wording.
- **Gods: Evolved, Gatling Cherrybomber Ballistics:** Android stores
  `每次攻击多发射一发子弹` separately and prepends the translated plant name at
  runtime. The PC project translates only the complete Chinese sentence. The
  Android exact adapter now supplies `: Gains +1 projectile`, preserving the
  PC wording and the missing separator.
- **Gods: Evolved split upgrade descriptions:** a family audit found the same
  runtime construction across the surrounding upgrade-card family. The
  Android suffix adapters now cover Berserker Snipea, Doominator, Magnetar,
  Stellar-form upgrades, Phoenix Threepeater, Photon Splitter, Thornminator,
  Doom Chomper, A.L.E.C., Apeacalypse Minigun, Wither-pult, and Helios Cabbage.
  The Napalm-shroom mode sentence is also assembled from a prefix, live plant
  name, and suffix, so both halves are translated while preserving that name.

## Runtime-fragment audit

`scripts/audit_runtime_fragments.py` compares every remaining CJK-bearing
metadata literal with the complete source strings translated by the PC
community project. It reports proper prefix, suffix, and inner matches for
manual review. It does not apply replacements automatically because a missing
plant name or destination can change the correct English sentence.

## 3.6.1-style UI positions

The shared values are:

| Setting | X | Y / scale |
|---|---:|---:|
| Bottom-left buttons | 110 | 80 |
| Bottom-left button scale | not recorded | 1.10 |
| Seed bank | 400 | 0 |
| Conveyor belt | 400 | 0 |
| Seed-selection screen | 300 | 0 |
| Plant-storage window | 400 | 0 |
| Toolbar | 400 | 0 |

Android stores these in each save/profile's `GameConfig.UIConfig`. They are
not a translation asset and a constructor-default change would affect only new
saves. More importantly, the values were tuned on 1920×1080 and may be wrong
on ultrawide displays. They remain a documented optional preset rather than a
silent save rewrite or universal default. Thanks to Naijen Wolfide for testing
and sharing the measurements.

## Where the old plant list is

The screenshots show the setup flow for a special custom/recommended level,
not a missing always-on main-menu plant list:

1. Tap the wooden **Recommended Levels** sign on the main menu.
2. Open **Super Custom Levels**.
3. Select a custom level.
4. Its pre-level **Choose Your Plants** screen exposes the large list and the
   **Upcoming Zombies** preview.

The old cactus/sign presentation was a 3.6.1-era shortcut/layout. Adding that
shortcut to normal Adventure would be a gameplay/UI modification and is not
part of the translation pass.

## 3.6.1 music comparison

`scripts/compare_audio_clips.py` compared Unity `AudioClip` payloads by asset
name:

- official Chinese 3.6.1: 168 clips;
- Joseph English 3.6.1: the same 168 names;
- official Chinese 3.8.1: 173 clips, adding five game-specific clips;
- Joseph's APK differs from official 3.6.1 in exactly 18 primarily music clips:
  `Boss2`, `Day`, `Day_drum`, `Fog`, `Fog_drum`, `Garden`, `IZ`, `MainMenu`,
  `Night`, `Night_drum`, `Pool`, `Pool_drum`, `Roof`, `Roof_drum`, `Roof_pre`,
  `SelectCard`, `UltimateBattle`, and `loon`.

The names and durations match, but the payloads were replaced or re-encoded.
The APK alone does not establish their external source or redistribution
permission. Android 3.8.1 already contains the expected original-named music;
there is no discovered built-in “Joseph soundtrack” toggle. No audio is copied
until its provenance, permission, and audible behavior are established.

## Updates, saves, and translated payloads

An APK update normally replaces its packaged `data.unity3d` and
`global-metadata.dat`. Android may preserve the writable external metadata
override under `files/il2cpp`, however, and Fusion can continue to load that
stale copy. Project policy remains documentation-only: do not add launcher code
that edits user storage or rewrites saves. Back up progression and remove only
a confirmed stale `files/il2cpp` override, or perform a clean installation.

## Future 3.9 migration

Do not use preview footage or dormant content as a base. When the official
Android 3.9 APK is released, archive its hashes and ABIs, generate a fresh
IL2CPP dump, refresh the PC translation commit, rerun both literal and enum-
definition CJK audits, rebuild from clean 3.9 assets, and physically retest all
Android-specific adapters. Parked Abyss content remains untouched unless the
official Android release exposes it.
