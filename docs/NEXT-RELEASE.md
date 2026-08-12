# Android 3.8.1 English v3.8.1-en.2 update

This file records the grouped fixes prepared for the second public English
3.8.1 release. The main build received physical-device testing before release;
the detailed checklist remains useful for regression testing and future ports.

## Translation areas included

- **Zen Garden Tool Shop**
  - translated the runtime `Cost` and `Owned` format fragments;
  - retained the existing item names and controls;
  - made the modal background follow the full Android canvas so ultrawide
    phones no longer show inactive Zen Garden buttons beside the shop.
- **Odyssey Gacha**
  - translated the current-luck value and the explanation of how luck affects
    box plants and prize-draw Sun.
- **The Gods: Evolution plant selection**
  - translated `Role`, `upgrades to`, `Times selected`, damage and speed bonus
    descriptions, projectile-count upgrades, maximum-plant choices, and page
    counters;
  - fixed the Maelstrom projectile-count card so a broad fusion-recipe regex
    can no longer turn it into the unrelated "plant not discovered" message;
  - translated the mode variants, reincarnation/boss descriptions, unlock
    condition, completion status, difficulty effects, and round footer;
  - translated dynamic save-slot and latest-autosave labels.
- **Difficulty settings**
  - restored the PC translation's complete numbered six-level scale, from
    `0: Easy Mode` through `5: Are You Sure?`;
  - restored the PC green-to-red color progression across all six settings
    instead of mixing numbered and unnumbered labels.
- **Challenge and Odyssey selection screens**
  - translated `Back to Menu`, `Previous Page`, `Next Page`, and `Back to
    Index` in the runtime backing fields which overwrite ordinary TMP text when
    these menus open.
- **Almanac**
  - translated the action beside `Close` as `Disable Transitions`;
  - repaired the blank Mechanics Almanac by retaining Android's required
    `details` list and merging all 38 current PC titles/descriptions into it;
  - restored the short PC community names for modifier cards and kept their
    descriptions in the description field, eliminating duplicated long
    descriptions from the card-title area;
  - removed the heavy opaque underlay from the shared Mechanics Almanac body
    component so blue emphasized words remain readable on every mechanics
    page while preserving white text, colors, bold tags, and wrapping;
  - retained the existing Android font, sizing, and layout refinements.
- **Credits and Changelog**
  - restored the original Chinese proper names for the game's credited
    creators and helpers while keeping role descriptions in English;
  - added the approved `English 3.8.1 Android Testing` parchment credit for
    `モア` and `S.O.R.O.B` and kept its source artwork in the repository;
  - removed the changelog instruction for the PC-only `Languages` button.
- **Starbound Task Rewards**
  - confirmed the complete Task Rewards dataset is already translated by the
    current English source data;
  - promoted the screenshot-confirmed Day levels and reward descriptions to
    exact Android mappings so they take precedence over generic regexes;
  - changed unselected reward labels from black to grey so they remain readable
    on the dark star-field panel.

## Reproducibility and safety

- Added a translation provenance audit and maintenance guide. PC community
  translations automatically supersede Codex-assisted fallbacks when upstream
  gains an exact entry, while narrowly documented Android-required overrides
  remain explicit. Reports record the exact source commit, origin, and dirty
  state.
- A fresh build now reapplies the translated Almanac tip before saving its
  typography changes. This fixes an object-cache ordering issue that appeared
  only when rebuilding the full bundle from a clean input.
- The UI builder validates all 51 runtime-backed navigation replacements after
  reopening the saved bundle.
- Comparing the previous and pending final bundles found exactly those 51
  semantic navigation changes. The two reserialized TMP font assets retain the
  same parsed fields, glyph/character data, atlas references, and materials.
- The remaining-CJK audit reports zero serialized UI components. The remaining
  TextAsset and metadata findings are retained names, internal data, or strings
  that have not been confirmed as player-facing.

## Important hot-patch warning

Fusion can load metadata from this writable external path instead of the copy
packaged in the APK:

```text
/storage/emulated/0/Android/data/com.LanPiaoPiao.PlantsVsZombiesRH/files/il2cpp/Metadata/global-metadata.dat
```

The supplied Task Rewards screenshot does not match the metadata embedded in
the current English APK: the packaged copy already contains English versions
of the shown strings. This strongly indicates that the phone was still using
an older external metadata hot patch. Before judging the next build, back up
the game files, fully close the game, and remove only the stale external
`files/il2cpp` override. Do not delete the save/progression files.

Installing the new APK as an update does not necessarily fix this state. An
APK update replaces the embedded copy, but Android preserves the existing
package's writable `Android/data/.../files` directory. If an older external
metadata file is present there, Fusion can keep choosing it over the newer
copy in the APK. A clean install removes that override, but the safer targeted
test is to back up the game files and remove only `files/il2cpp` while leaving
all progression/save files intact.

This remains a documented manual recovery procedure. The project will not add
startup code that automatically inspects, deletes, renames, replaces, or
migrates external metadata. That decision preserves the official launcher/DEX
behavior and avoids modifying user files without an explicit action.

The same diagnosis applies when newer bundle-based fixes appear but newer
metadata-based fixes do not. For example, a device may show the repaired
Mechanics Almanac and Tool Shop while still showing unnumbered difficulty
labels or modifier descriptions duplicated into their titles. Those exact
difficulty and modifier fixes are already embedded in the pending APK; this
mixed old/new result points to a stale external metadata override, not a
different translation inside the APK.

## Community testing thanks

Special thanks for rapid, thorough device testing and clear screenshots:

- **モア, the Virtue of Cuteness** (`absolute201616`)
- **S.O.R.O.B Pengantar Minuman 🤖** (`jazzuke1`)

The full Discord display names and usernames are recorded here for precise
attribution. The proposed in-game heading is `English 3.8.1 Android Testing:`
with the shorter display forms `モア` and `S.O.R.O.B` so the parchment remains
readable.

## Troubleshooting blindly renamed packages

Do not change only the manifest package ID to install a second copy beside the
original. The APK's compiled `classes.dex` still contains package-qualified
`BuildConfig`/`R` classes and the original application-ID constant, and an
added mod can also retain its own hardcoded package paths or preference names.
A blind manifest rename does not update those compiled or hardcoded values.

This can make a renamed derivative read or overwrite unexpected metadata,
configuration, preferences, or hot-patch files when both copies are installed.
It may then display translations that do not match the embedded APK. It can
also simply contain translation assets overwritten by the additional mod, as
happened in the reported test.

The complete external-storage path was not found as a literal in Fusion's
IL2CPP metadata or `libil2cpp.so`, so this warning does not claim that the base
game itself hardcodes that one path. Supporting a second package correctly
would require auditing and rebuilding every package-qualified component and
the added mod—not a one-field rename.

For a valid test, use the unchanged package ID and expected signed APK. Back up
saves, remove the blindly renamed derivative, and ensure the original
package's external `files/il2cpp` directory has no stale metadata override.
Never delete progression files as part of this check.

## Physical-device checks before release

- Open Odyssey Gacha and verify the luck overlay fits at luck values 0 and 1+.
- Open every page of Challenge and Odyssey mode selection and verify all four
  navigation labels stay English after the screen finishes opening.
- Exercise all Gods Evolution plant-card types, especially damage, speed,
  projectile-count, upgrade-path, role, and maximum-plant cards.
- Verify all Gods Evolution mode, difficulty, completion, unlock, save-slot,
  and autosave text at narrow and 16:9 aspect ratios.
- Open the Almanac index and confirm `Disable Transitions` fits beside `Close`.
- Open several Mechanics Almanac pages and confirm blue emphasis remains crisp
  and readable without the former heavy black underlay.
- Open Starbound Task Rewards and verify selected/unselected rewards are both
  readable and all scrolling entries remain English.
- Recheck the Zen Garden Tool Shop `Cost` and `Owned` lines.
- On an ultrawide phone, open the Tool Shop and confirm its background covers
  the whole screen and no inactive Zen Garden buttons remain visible beside it.
