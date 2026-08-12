# Pending Android 3.8.1 English update

This file is the staging checklist for the next public English release. The
source fixes below are intentionally grouped for one later release. **No new
public APK or GitHub release should be created until the batch has completed
physical-device testing.**

## Translation areas included

- **Zen Garden Tool Shop**
  - translated the runtime `Cost` and `Owned` format fragments;
  - retained the existing item names and layout.
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
- **Challenge and Odyssey selection screens**
  - translated `Back to Menu`, `Previous Page`, `Next Page`, and `Back to
    Index` in the runtime backing fields which overwrite ordinary TMP text when
    these menus open.
- **Almanac**
  - translated the action beside `Close` as `Disable Transitions`;
  - retained the existing Android font, sizing, and layout refinements.
- **Starbound Task Rewards**
  - confirmed the complete Task Rewards dataset is already translated by the
    current English source data;
  - promoted the screenshot-confirmed Day levels and reward descriptions to
    exact Android mappings so they take precedence over generic regexes;
  - changed unselected reward labels from black to grey so they remain readable
    on the dark star-field panel.

## Reproducibility and safety

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

## Physical-device checks before release

- Open Odyssey Gacha and verify the luck overlay fits at luck values 0 and 1+.
- Open every page of Challenge and Odyssey mode selection and verify all four
  navigation labels stay English after the screen finishes opening.
- Exercise all Gods Evolution plant-card types, especially damage, speed,
  projectile-count, upgrade-path, role, and maximum-plant cards.
- Verify all Gods Evolution mode, difficulty, completion, unlock, save-slot,
  and autosave text at narrow and 16:9 aspect ratios.
- Open the Almanac index and confirm `Disable Transitions` fits beside `Close`.
- Open Starbound Task Rewards and verify selected/unselected rewards are both
  readable and all scrolling entries remain English.
- Recheck the Zen Garden Tool Shop `Cost` and `Owned` lines.

