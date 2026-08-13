# PvZ Fusion 3.8.1 — English Android Update 3

This is the public **no-SS** English translation build. It does not contain the
private SilverShadow Cheats prototype.

## Installation

Back up saves, uninstall the previous build, and install this APK fresh. Keep
the original package ID:

```text
com.LanPiaoPiao.PlantsVsZombiesRH
```

Do not blindly rename the package ID. Compiled and hardcoded package-qualified
values can continue pointing at the original package's files, preferences, or
external IL2CPP metadata. Do not restore an old installation's entire `files`
directory; restore only the save files documented in the README.

## Changes since Update 2

### Plant Almanac affinities

- Translated all 18 Android `SynergyType` affinity names, not only the values
  visible in the original Gatling Cherrybomber screenshot.
- Preserved each enum's numeric value and all gameplay membership logic.
- Added version/layout validation so a future incompatible metadata build
  fails safely instead of renaming the wrong fields.

### Vasebreaker PVP

- Translated the turn-start and remaining-moves Gift Box instructions.
- Translated both dynamic toggle states used by `RMB for Vase` and
  `Random Seedslot`: `(OFF)` and `(ON)`.
- Translated the split runtime notification assembled around the live player
  name: `A zombie crossed the line. Challenger gains 1 move.`
- Translated both alternate no-moves-left prompts discovered from the same
  runtime-string family.
- Preserved the original creator credit `蓝飘飘fly (Bilibili)`.

### Note Editor and runtime labels

- Translated the stopped and playing `Song` and `Time` header fragments while
  preserving BPM, beat, and time placeholders.
- Translated the Android runtime Zen Garden purchase confirmation, including
  its destination page, row, and column.

### Puzzle and legacy Android UI

- Translated Puzzle Mode's `Switch Level Group` button.
- Covered additional legacy `UnityEngine.UI.Text` labels that the earlier
  TextMesh Pro-only pass could miss: `Return to Index`, `Confirm Loadout`,
  `Sun Drop Multiplier`, `Go to the Shop`, `OK`, and `Set Sun Amount`.
- Translated all seven Mechanics Almanac category fields so hidden or future
  category/filter UI cannot expose the underlying Chinese values.

### Mixed-language perk and fusion text

- Corrected Android short perk/stat labels that a broad PC regex could mistake
  for undiscovered-plant recipes.
- Corrected mixed-language fusion hints using current PC community plant names,
  including Umbrella Kale, Charm Magnet, Garlic-pult, Magnet Blover, Frost
  Gloom-shroom, Cryonic-shroom, Cherry Chomper, Magnet Cactus, Gatling Cherry,
  Cryo Cannon, Demise-shroom, Spicy Squash, and Infernowood.
- Kept these Android-specific entries as fallbacks so future exact PC community
  translations automatically take priority.

### Translation audit and maintenance

- Expanded the remaining-Chinese audit from TMP `m_text` fields to every
  readable serialized string field, including legacy `m_Text` components.
- Added reporting for unreadable serialized objects containing potential UTF-8
  CJK data rather than silently skipping them.
- Documented how to audit dynamically concatenated text as a complete family,
  including prefixes, player names, suffixes, and toggle state fragments.
- Documented safe save-only migration and files that must not be restored from
  an older or modified installation.
- Documented that Abyss is parked/inactive in Android 3.8.1 and is intentionally
  not exposed or treated as missing playable content.

## Preserved behavior

- Package ID and save location are unchanged.
- Both `arm64-v8a` and `armeabi-v7a` remain present.
- Android manifest, DEX bytecode, native libraries, resources, and all other
  executable/application-shell files remain byte-identical to the official
  Chinese 3.8.1 APK.
- Original creator/helper names remain in their original form.

## Community thanks

Special thanks again to **S.O.R.O.B Pengantar Minuman 🤖** (`jazzuke1`) for
the rapid Vasebreaker PVP testing, careful toggle-state screenshots, and the
remaining dynamic notification report that directly led to the final fixes.

Thanks also to every tester whose screenshots exposed Android-only context and
helped bring this translation closer to completion.

## Verification

- APK SHA-256:
  `A999CBBB1F2DF42EF9C762C4F5FB67A446BE3E5EBC855F8AF3CB42EA163597FC`
- Signing certificate SHA-256:
  `1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6`
- Package: `com.LanPiaoPiao.PlantsVsZombiesRH`
- Native ABIs: `arm64-v8a`, `armeabi-v7a`
