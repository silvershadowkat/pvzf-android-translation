# Android 4.0.5 prerelease 3: final local build

> Historical base audit: this page records the original October 21 r20 APK. Prerelease 3 assets were updated on October 22 with a regular translation refresh and a separate experimental AI APK. The hash and no-AI statements below apply to the original base, not both current downloads. See [the current AI/text audit](../magic-plantbrush-prototype.md), [release notes](../RELEASE-NOTES-4.0.5-PRE3.md), and the release's updated checksums/build record.

The maintainer reported that everything looks good on 2026-10-21 and explicitly authorized publishing this unchanged build as prerelease 3. Published as [v4.0.5-release-3](https://github.com/silvershadowkat/pvzf-android-translation/releases/tag/v4.0.5-release-3); the uploaded APK hash matches this approved build. See ANDROID405-PRE3-RELEASE-BUILD.json. The installable file is `PvZ-Fusion-4.0.5-English-Android-prerelease3.apk`, version code 4050339, package `com.LanPiaoPiao.PlantsVsZombiesEN`. It is the same signed APK as internal build test1-r20.

SHA256: `9d10eb7b8082ac27b9530a526f9cffb7dcfc0a1e27011e2951054a6a70810b5c`

## Final translation audit

The audit scanned 308 TextAssets, serialized TMP/legacy text, and metadata from the staged 4.0.5 payload. It exercised all 1,440 CJK-bearing source occurrences through the actual Java display translator, then reviewed remaining strings against current context and the previously reviewed PC Blooms source at `c7fb5997d65e1d5248f3d7a9ca9c9e0a4b516640`.

Added 232 exact display mappings and nine narrowly anchored formatted rules. These cover editor field labels, list/value editing, projectile and entity actions, validation messages, numeric upgrade prompts, Gods save/reward messages, the two shield applicability explanations, and I, Zombie end-credit headings and roles. Creator aliases are retained. `assets/final-ui-audit-4.0.5.json` records every source, source location and English rendering. Ordinary missing wording was translated with Context Aware AI using established terminology; these additions are not claimed as new PC translations.

No additional exact-match PC translation was found among the initial residual strings in this census. That is an exact-source comparison, not proof that every possible live screen is covered. Full strings assembled at runtime, server-delivered levels and text baked into other images need separate review.

Residual CJK-bearing occurrences fell from 1,028 to 797: 717 metadata occurrences, 77 TextAsset occurrences and three serialized UI occurrences. These are not counts of untranslated visible labels. They include developer logs, internal identifiers, enum/route names, formatting templates, creator aliases and guide references whose original spelling is required. Unverified plant/modifier names and effects remain unchanged rather than being guessed. Livestream-specific help remains pending context and Android reachability review; the other two remaining serialized UI texts contain credited creator names. The AI-recognizer mode remains unavailable.

The new mappings affect rendering only. Source metadata, graph IDs, saved variables and serialized lookup keys are unchanged by this audit. Editable input controls continue to bypass the display translator. The earlier, separate initial-template-name patch remains limited to the reviewed `My Rule` literal.

## Adventure Extra and Help artwork

All four diary pages were translated from their original Chinese prose. The inspected PC image had blank pages rather than usable English narrative. Sword-shroom and Shield-shroom follow PC terminology; Yelena is a transliteration. Generic narrative descriptions were not turned into invented plant names. The user approved the artwork.

The Help parchment starts from the inspected PC English image. Its lower-left Android section now reads:

> English Android Port:
> SilverShadow, Joseph Franci, aha,
> All of the testers in the PVZ Fusion Fans Discord,
> All of the modders that provided guidance

The Blooms credits remain on the right. The final correction adds Fusion to the Discord name. The approved raster assets, exact prompts, packing details and hashes are recorded in `assets/storybook-4.0.5-review.json` and `assets/parchments-4.0.5-production.json`.

`scripts/apply_parchments_405.py` replaces only `resources.assets` Texture2D 432 (`剧情文本`) and 2307 (`thanks`). It preserves texture dimensions, ASTC format, mip counts and every Sprite rectangle/mesh. A before/after hash comparison of 208,662 serialized objects found exactly those two changed objects. The saved bundle was reopened and decoded artwork inspected. This verifies the packed assets, not their final placement on every phone screen.

## Magic Plantbrush freeze prevention

The untouched Chinese 4.0.5 app reproduced the unresponsive interface. Its Recommended Levels entry is already marked unavailable on mobile. The original `Advanture_Btn.OnMouseUp` route opens the unavailable modal through `UIMgr.EnterOtherMenu` and `OtherMenu.UpdateText`.

The runtime hook intercepts only `levelType == 1`, `buttonNumber == 197`, and `limInMobile == true`. It restores the button's anchored position and calls the existing `Core.InGameText.ShowText` notification with `Magic Plantbrush is not available on Android.` for four seconds. It does not enter the mode or open the broken modal. Every other button calls the original method. Class, field and method names are resolved through IL2CPP APIs on both ABIs; disassembly addresses are evidence only, not patch offsets.

No AI model, Windows executable, server or service dependency is included. This change is a narrow workaround for the unavailable path, not an implementation of Magic Plantbrush. Repeated taps, notification fading and returning to another level still need device validation on this final APK.

## Validation and update safety

- arm64-v8a and armeabi-v7a native builds passed.
- Signature, ZIP alignment, package/version and protected metadata checks passed.
- Original game native libraries remain byte-identical to the selected baseline.
- Managed refresh checks passed: eight checks preserving 11 save/settings/unknown-file fixtures.
- 624 Java regex/capture checks and 17 base display checks passed.
- 1,203 editor, guide, formatted-text and preservation fixtures passed through the actual Java translator.
- Payloads in the final APK match the audited staged bundle, metadata and dictionary.

r20 installed in place on S26 (R5GL14CN45N). Runtime initialized; all nine readable nontranslation files, including both survival saves and player/garden data, remained unchanged through installation and startup. Existing managed overrides match the APK. Feature/UI smoke checks and private settings verification still need user testing. Prior r19 testing preserved all nine readable nontranslation files, including both survival slots, and the user confirmed that a save loads. That earlier evidence must not be represented as an r20 device test. This update does not change the save-refresh policy: only explicitly managed translation paths refresh; other files and additional save slots remain untouched.

## Quick phone test

1. Install this APK over the current English prerelease 3 test build. Do not uninstall or install a seed. Load an existing survival save and check the remembered music choice.
2. Tap Magic Plantbrush in Recommended Levels. Expect the temporary unavailable message, then confirm other buttons and Back still work. Repeat once.
3. Open Adventure Extra's diary pages and Help. Check page order, clipping and the PVZ Fusion Fans credit.
4. Open the Creator Guide/editor and The Gods almanac. Check labels, Tactics, shield explanations and scrollable descriptions for fit.

Moving from prerelease 2 still needs the already-documented one-time manual save transfer because the package identity changed. This does not affect in-place updates from the current EN test builds.

## Maintainer approval

On 2026-10-21, after installing r20 on the S26, the maintainer reported “everything looks good” and requested publication. This is general acceptance, not a separately recorded pass for every checklist item or device. The default Player rename investigation made no APK or save changes and is not a feature of this release.
