# PvZ Fusion 3.8.1: English Android

This is an independent, noncommercial English Android port of *Plants vs.
Zombies: Fusion* 3.8.1. It is not affiliated with or endorsed by PopCap,
Electronic Arts, LanPiaoPiao, or the upstream translation maintainers.

## Install warning

**Back up your saves first, uninstall the old build, and then install this APK
fresh.** Although releases signed with this project's certificate can normally
update in place, a clean installation is recommended for this update because
Android can preserve an older external translation override during an update.

Keep the original package ID:

```text
com.LanPiaoPiao.PlantsVsZombiesRH
```

Do not blindly rename the manifest package to install a second copy. A package
rename does not rewrite every compiled package-qualified value or value added
by a mod. The renamed copy can therefore use metadata, preferences, or a
translation override associated with the original package and show the wrong
text. Supporting a different package ID requires a controlled rebuild and
audit, not a one-field rename.

This release uses a dedicated community signing certificate. Android will not
install it over the official Chinese, Joseph, or aha APK because those use
different certificates. Back up first, remove that existing build, and install
this APK.

Save/data path:

```text
/storage/emulated/0/Android/data/com.LanPiaoPiao.PlantsVsZombiesRH/files/
```

Do not restore the old `il2cpp` directory over the new installation.

### Stale metadata policy

An APK update replaces the metadata packaged inside the APK, but Android can
preserve an older writable override in `files/il2cpp`. Fusion may continue to
load that external copy, making some newly translated screens appear stale
even though the updated APK contains the correct translation.

The English Android project intentionally does **not** add startup code that
deletes, renames, replaces, or migrates external metadata. This preserves the
official launcher/DEX behavior and avoids modifying user files automatically.
If stale text remains after an update, back up the game files, fully close the
game, and manually remove only the stale `files/il2cpp` override, or perform a
clean installation. Do not remove progression or save files.

## Troubleshooting blindly renamed packages

Do not change only the manifest package ID to install this game beside another
copy. The compiled DEX still contains package-qualified `BuildConfig`/`R`
classes and the original application-ID constant, while an added mod may have
its own hardcoded paths or preference names. A manifest-only rename does not
rewrite those values and is unsupported.

With both copies installed, such a derivative can read or overwrite unexpected
metadata, configuration, preferences, or hot-patch files, or the added mod may
have directly replaced the English assets. Either case can produce text that
does not match the original English APK. The full external-storage path was
not found as a literal in the base game's IL2CPP metadata or `libil2cpp.so`, so
a proper alternate-package build would need a wider controlled audit rather
than a speculative path patch.

For reliable testing, use the unchanged package ID. Back up saves, remove the
blindly renamed derivative, and check only the original package's
`files/il2cpp` directory for stale metadata. Do not remove progression data.

## Download verification

- File: `PvZ-Fusion-3.8.1-English-Android.apk`
- Size: `550771282` bytes
- SHA-256: `2401421503011e797dde7b4f3ec8a3f97ade7d6c39da205d661b970d7aa6bfbc`
- Signing certificate SHA-256:
  `1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6`

## What is included

- current PC English translation data ported to Android 3.8.1;
- conservative Joseph 3.6.1 and aha 3.8.1 fallback mappings where current PC
  data did not cover unchanged Android strings;
- translated Almanacs, levels, custom levels, tutorials, tips, configuration,
  and serialized Android UI;
- PvZ-style TMP typography with CJK fallback;
- Android-specific title, description, footer, skin-selector, Help/Hotkeys,
  and credits layout fixes;
- in-game Android-port credits for Joseph Franci, aha, SilverShadow, and Codex.

## Changes in v3.8.1-en.2

Many of these corrections came directly from community screenshots and rapid
device testing. The targeted changes are:

- **Zen Garden Tool Shop:** translated the Android-only `Cost` and `Owned`
  values and expanded its modal background across ultrawide displays so
  inactive garden buttons no longer appear usable behind it.
- **Garden Defense:** applied the same ultrawide modal-background correction
  after testing showed that screen had the matching exposed-button problem.
- **Odyssey Gacha:** translated the current-luck display and the explanation of
  how luck affects plants obtained from boxes and Sun obtained from draws.
- **The Gods: Evolution:** translated plant roles, upgrade paths, selection
  counts, damage/speed/projectile upgrades, maximum-plant choices, page
  counters, mode variants, difficulty effects, round text, unlock/completion
  messages, save slots, and autosave labels. It also corrects the Maelstrom
  projectile-count card that could receive an unrelated fallback message.
- **Difficulty settings:** restored all six PC-style numbered labels, from
  `0: Easy Mode` through `5: Are You Sure?`, with the complete green-to-red
  color progression.
- **Challenge and Odyssey menus:** translated runtime-backed `Back to Menu`,
  `Previous Page`, `Next Page`, and `Back to Index` controls that could revert
  after their screens opened.
- **Mechanics Almanac:** repaired the formerly blank Android page by adapting
  the current PC data to Android's required schema. All 38 current mechanics
  entries are included, and colored emphasis is now readable without the
  heavy dark text underlay seen in tester screenshots.
- **Modifier Almanac:** restored the PC community's short modifier names on
  cards and in the selected title, removed the repeated name from the visible
  description, and enlarged the description text slightly for readability.
- **Plant and Zombie Almanacs:** refined long selected-entry names so they fit
  more consistently without changing their terminology.
- **Almanac index:** translated the missing control beside `Close` as
  `Disable Transitions`.
- **Starbound Task Rewards:** added exact Android mappings for the reported day
  and reward strings and changed unselected reward text from black to grey so
  it remains readable over the star-field background.
- **Credits:** restored original Chinese names for credited creators and
  helpers, retained English role descriptions, and added the approved Android
  testing credit on the parchment using its matching visual style.
- **Changelog:** removed the reference to the PC-only `Languages` button from
  this English-only Android build.
- **Translation maintenance:** added a repeatable PC-to-Android synchronization
  and provenance workflow. New PC community translations take priority over
  Codex-assisted fallback translations when matching upstream entries become
  available, while Android-specific schema adapters remain explicit.

## Changes prepared after v3.8.1-en.5

- Translated all 42 Investment Odyssey modifier names. The descriptions still
  use the PC community translation.
- Translated the remaining Buckshot Commando upgrade text.
- Fixed the Princess Solarnova stat panel spacing.
- Improved the audit used to find hidden Android-only Chinese text.
- Documented the custom-level plant list, optional UI-position preset, update
  behavior, and 3.6.1 music comparison.

## Safety evidence

The release uses the official Chinese 3.8.1 APK shell. A comparative audit
proves the manifest, resources, DEX bytecode, and all native libraries are
byte-identical to the official APK. Only `data.unity3d` and
`global-metadata.dat` differ. The APK passes ZIP integrity, alignment, and
Android signature v1/v2/v3 verification. Windows Defender reported no threats
on August 11, 2026. See `docs/RELEASE-SAFETY.md` for scope and limitations.

## Credits and license

Game by LanPiaoPiaoFly and the PvZ Fusion team. English translation data and
terminology by Teyliu, Mamoru-kun, and the full PVZF Translation/Blooms
community credited in the repository README and upstream project. Android port
lineage and references: Joseph Franci and aha. This port/toolkit: SilverShadow
and Codex.

Translation data is used under CC BY-NC 4.0 and the release is noncommercial.
Toolkit code is MIT. Full provenance and contributor names are in `README.md`
and `THIRD_PARTY.md`.

## Community thanks

Special thanks to **モア, the Virtue of Cuteness** (`absolute201616`) and
**S.O.R.O.B Pengantar Minuman 🤖** (`jazzuke1`) for exceptionally fast,
thorough testing and clear screenshots.

Thank you to **aha** for the **3 THUMBS UP**, and to everyone else who tested,
reported an issue, followed the project, or simply looked forward to this
Android port. That enthusiasm and encouragement motivated this release.

The APK contains third-party game material. Distribution may be removed if a
rights holder objects. The source toolkit intentionally contains no game
binaries or extracted proprietary assets.
