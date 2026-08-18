# PvZ Fusion 3.9 English Android - Clean Test 3

This is a local first-pass test build. It has not been published as a GitHub
release. Automated build and package audits pass, but real-device testing is
still required.

## Test file

- File: `PvZ-Fusion-3.9-English-Android-clean-test3.apk`
- Size: `570,936,224` bytes
- SHA-256: `5EC4D6EF7A0E2585F427FA9145B2A1A2FBC47DF88A236EFF379709A3B920F623`
- Package: `com.LanPiaoPiao.PlantsVsZombiesRH`
- Version: `3.9`
- Signing certificate SHA-256:
  `1F2552CC7DBFBBBEE21D2EA7E77EDF371A377902CDCB78BA4F3104E387CD7BC6`

The certificate matches the 3.8.1 English Android Update 6 APK, so an in-place
update should be signature-compatible.

## Clean rebuild sources

- Known-good English baseline: `PvZ-Fusion-3.8.1-English-Android-update6.apk`
  (`A8441C6792363E0475AD0D989CE2046EC6D536F3011EF9496DC8E1EAF6A35C93`)
- Official Android 3.9 shell: `ChineseAPK3.9.apk`
  (`A3ADF7D8742D537F167217867E943E1B9FAEAA361A868E33E388A373671320B0`)
- PC translation: `Teyliu/PVZF-Translation`, branch `3.9`, commit
  `0747001d10b6f3b82f89ea1ee022f2e30f347791`

The 3.8.1 baseline was normalized to remove em dashes before any 3.9 content
was integrated. The final 3.9 payload received the same validation pass.

## Translation policy

- Use a current PC translation for new or changed 3.9 content only when the
  source field matches and the PC value is a usable translation.
- Reject placeholders such as `TODO`, `???`, repeated temporary descriptions,
  and literal `X`/`Y` names.
- Leave untranslated new 3.9 fields in official Chinese.
- Do not add context-aware or other AI translations for new 3.9 gameplay
  content.
- Preserve reviewed Update 6 Android translations only for unchanged source
  strings.
- Permit only explicitly reviewed generic settings, buttons, status messages,
  and tutorial prompts that do not invent plant, zombie, fusion, item,
  modifier, or mechanics terminology. Track these separately and let later PC
  English supersede them automatically.

Some new plant and modifier fields intentionally remain Chinese because the
pinned PC branch does not yet contain usable English for them.

## Included fixes

- Fixed the Test 1 glyph corruption. The legacy texture pass had copied the
  Update 6 `fzcq Atlas` bitmap without its matching 703-entry glyph table into
  a 3.9 font asset with a 1,740-entry table. Test 3 excludes all TMP font
  atlases from ordinary texture inheritance and transplants the complete
  matching Update 6/PC English PvZ2 font chain: source payload, 703-entry glyph
  and character tables, SDF atlas, material, and object pointers. The official
  Chinese fallback font remains available for intentionally untranslated text.
- Corrected `关闭` only in confirmed back/close button hierarchies to `Close`;
  unrelated enabled/disabled controls retain their actual state meaning.
- Translated confirmed generic 3.9 settings such as screen shake and damage
  numbers while preserving unreviewed gameplay-bearing Chinese.
- Preserved official 3.9 plants, menus, serialized data, and changed artwork.
- Restored the English Odyssey key, Return controls, and pause-menu `MENU`
  texture where official 3.9 retained the same underlying art.
- Restored the exact `LETS ROCK` wave-start label and a compatible visible font.
- Fixed the new-save version labels and default `New Save File` text.
- Rebuilt modifier-card records so descriptions no longer repeat inside names;
  untranslated records keep their official Chinese name and description.
- Shifted modifier Almanac descriptions right to the same margin as regular
  plant and zombie descriptions.
- Removed em dashes from player-facing translated metadata and bundle text.

## Automated verification

- APK signature schemes v1, v2, and v3 verify with one signer.
- ZIP alignment passes.
- Manifest, package badging, DEX, native libraries, ABIs, and 35 other
  non-signature entries match the official 3.9 APK byte-for-byte.
- Only `global-metadata.dat` and `data.unity3d` differ from the official shell.
- Metadata and Unity bundle reopen/round-trip validation passes.
- Both primary Latin TMP assets use the matching 703-glyph PvZ2 chain and the
  same validated atlas hash. The separate Chinese fallback retains 2,790
  glyphs for intentional untranslated content.
- No PC-translatable CJK metadata remnant was found; remaining Chinese is
  intentional untranslated/internal content.

## PC visual-comparison folder

- Folder: `PvZ-Fusion-3.9-English-PC-static-d150f6f0`
- Base: the user-supplied official PC 3.9 archive
- English project: `Teyliu/PVZF-Translation` branch `3.9`, commit
  `d150f6f0d5ea16622c4e0b5ee6ce798d60e9c5d1`
- Patched `data.unity3d` SHA-256:
  `65359A4AE07A5750C4A976F9F51FEF767E675D55EE9C13063264F2C63E3479A2`
- Patched `global-metadata.dat` SHA-256:
  `FBA7B199CF7C1CA5D24F1440D705EAD776EF3F0F86E557CFE951D8A52E5D44B0`
- Loader: none

This is a local static visual reference, not a published PC English 3.9
release. Run `Launch Game.bat` directly from the supplied folder. It is built
only from official PC 3.9 and the current PC translation project. It contains
no Android strings, reviewed Android UI mappings, Android fallbacks, Android
fonts, or Android textures.

The available translator DLL targets 3.8.1 APIs and fails on final PC 3.9, so
MelonLoader and the DLL are intentionally absent. Upstream PC exact, regex,
structured, Almanac, tips, UI, and compatible texture data are applied
statically. Missing, placeholder, or incomplete PC entries retain the complete
official PC text. Fifteen modifier regex candidates provide a title but discard
their description; those incomplete candidates are deliberately not applied.

The final bundle retains the official PC object inventory of 201,407 objects.
Only 1,226 `MonoBehaviour`, 121 `TextAsset`, 47 `Texture2D`, and 8 `Sprite`
objects differ; no font, shader, script, executable, or native-library object
was replaced. All other files from the official PC archive are byte-identical.

### PC presentation test 1

- Folder: `PvZ-Fusion-3.9-English-PC-presentation-test1-d150f6f0`
- Patched `data.unity3d` SHA-256:
  `813F541C9C5F15BA6D497F9198886A55EF182357363FA68B465CC39F8E379684`
- Patched `global-metadata.dat` SHA-256:
  `FBA7B199CF7C1CA5D24F1440D705EAD776EF3F0F86E557CFE951D8A52E5D44B0`

This is a separate, visually reviewed derivative of the strict PC reference.
It uses `scripts/polish_pc_reference_ui.py` to enable auto-sizing and wrapping
for 30 existing PC Settings components and to translate six duplicated/generic
PC control components. The reviewed controls are Back to Menu, Toggle
Fullscreen, Current Zoom, Disable Screen Shake, and Damage Numbers. They do not
introduce gameplay terminology and are explicitly marked as local PC UI in the
folder README.

No Android translation, font, texture, fallback, or bundle is an input. The
official PC font remains because the 3.8.1 translator's runtime-generated PvZ2
font cannot be reproduced safely by merely swapping a TTF into a serialized TMP
asset. The resulting presentation is improved but intentionally not described
as a perfect recreation of the 3.8.1 runtime translator.

The final bundle retains all 201,407 official PC objects. Relative to the
official PC base, 1,232 `MonoBehaviour`, 121 `TextAsset`, 47 `Texture2D`, and 8
`Sprite` objects differ. No font, shader, script, executable, or native library
was replaced. The Settings screen passed a live visual check without the prior
text collisions.

## Installation warning

Back up saves before installing. Do not restore the old app's entire `files`
directory. In particular, a stale writable override at
`files/il2cpp/Metadata/global-metadata.dat` can supersede the new APK payload
and make old translation defects reappear. Remove only a confirmed stale
`files/il2cpp` override; do not remove progression files.

## First-pass device checklist

- Launch, reach the main menu, and confirm the game reports version 3.9.
- Create a new save and check `New Save File`, `Version`, and current-version
  labels. Imported saves may retain their previously stored Chinese name.
- Check the Odyssey key, Return controls, pause-menu `MENU`, and `LETS ROCK`.
- Open new 3.9 plant entries and confirm new assets display correctly.
- Open several modifier cards and verify names do not contain their full
  descriptions.
- Compare regular and modifier Almanac description alignment.
- Exercise new 3.9 context menus and item screens for clipping, missing text,
  or stale 3.8.1 content.
- Confirm intentionally untranslated new fields remain coherent Chinese rather
  than placeholder or invented English.
