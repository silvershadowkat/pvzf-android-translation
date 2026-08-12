# Research findings

## Artifacts examined

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| Official Chinese Android 3.6.1 APK | 607,354,220 | `57460a1305e0bebac3c15543645a3f86e94a5564c098947897e40b15012b61d7` |
| Joseph English Android 3.6.1 APK | 595,434,060 | `bcdae9fa8199be1ad85ecb5d3b27c95f19168ac29ae6885691ce71d7210fe1ef` |
| Official Chinese Android 3.8.1 APK | 597,908,259 | `1d6789a388621f544ea1c29778acfb12645933b67153ecaed4f54a48c7fa43c0` |
| aha unfinished English Android 3.8.1 APK | 546,810,706 | `355b35304100b64e38ba66667eaecd8841b0f5aa8a2eb58f9f42e1cb9ba63657` |
| aha follow-up `global-metadata.dat` | 11,315,244 | `66b38880578cc9633622794c9b9c2750a2bb1d72db7b7b86be3683034286c172` |

## Joseph 3.6.1 versus official Chinese 3.6.1

The manifest, `classes.dex`, resource table, boot configuration, scripting
assembly list, `RuntimeInitializeOnLoads.json`, and ARM64 `libil2cpp.so` are
byte-identical. The translation-specific changes are therefore confined to:

- `global-metadata.dat`
- `data.unity3d`
- the Unity application GUID
- the APK signature

Joseph changed these existing Unity objects without adding or removing objects:

| Object type | Modified |
| --- | ---: |
| `AudioClip` | 18 |
| `MonoBehaviour` | 3,081 |
| `SpriteRenderer` | 16 |
| `TextAsset` | 257 |
| `Texture2D` | 60 |

The changed text assets comprise 160 `level*` files, 66 `Custom*` files, 19
tutorial files, the three almanac databases, `AbyssBuffData`, and several other
content files. This broad asset coverage explains why the 3.6.1 port was much
more complete than the later unfinished build.

## aha 3.8.1 versus official Chinese 3.8.1

The ARM64 `libil2cpp.so`, boot configuration, scripting assembly list,
`RuntimeInitializeOnLoads.json`, and Unity application GUID are byte-identical.
The Unity bundle changes are:

| Object type | Added | Modified |
| --- | ---: | ---: |
| `TextAsset` | 0 | 3 |
| `MonoBehaviour` | 1 | 1,598 |
| `Texture2D` | 40 | 41 |
| `Font` | 1 | 4 |
| `Material` | 2 | 0 |
| `Mesh` | 13 | 0 |
| `MonoScript` | 16 | 0 |
| `Shader` | 6 | 0 |
| `ComputeShader` | 6 | 0 |

The only changed `TextAsset` objects are `LawnStrings`, `ZombieStrings`, and
`DetailStrings`. The added objects are largely dependencies of an injected
English font/UI asset set.

All 1,598 modified `MonoBehaviour` objects are TextMesh Pro text components.
Their serialized differences begin at the `m_text` string and the remainder of
each component is byte-identical after accounting for string length and
alignment. No Button, GameObject, Transform, or other interaction component was
changed by aha's bundle.

The unfinished bundle also replaced the four existing Font objects `fzcq`,
`PerfectDOSVGA437`, `LiberationSans`, and `fzjz` with roughly 82 KiB generic
font payloads. Joseph's 3.6.1 translation did not modify Font objects. A
font-preserved build now restores those four objects byte-for-byte from the
official Chinese 3.8.1 bundle while retaining the translated text data.

Screenshot testing exposed a context collision in the PC exact-string table:
`关闭` maps to `Disabled`, which is correct for a toggle but wrong for Close,
Quit, and Go-back buttons. The UI builder resolves these using the serialized
GameObject hierarchy. It also injects the repository's complete English 3.8.1
changelog in place of the unfinished bundle's partially translated copy.

Visual testing showed that restoring the official 3.8.1 fonts still does not
match Joseph's presentation. Official 3.6.1 contains PvZ-style font families
including `BrianneTod`, `ContinuumBold`, `DwarvenTodcraft`, and
`HouseofTerror`; upstream 3.8.1 removed those families. Joseph's 3.6.1 bundle
does not alter the font objects, and almost all of its translated TMP text
components continue to reference the existing `ContinuumBold SDF` asset. The
v3 experiment therefore places Joseph's byte-identical `ContinuumBold` font
payload into the stable 3.8.1 `fzcq` and `fzjz` Font object IDs used by dynamic
TMP text, while retaining the 3.8.1 component structure.

Device screenshots proved that v3 changed only the dynamic source TTF; the
already baked SDF atlas continued to render the handwritten 3.8.1 glyphs. The
v4 pipeline therefore transplants the complete `ContinuumBold SDF` dependency
set into the existing `Dynamic` and `fzjz Dynamic` object IDs: 703 glyphs and
characters, the exact 4096x4096 atlas pixels, remapped material and source-font
references, and the official Chinese SDF as a fallback for untranslated names.

On-device v4 screenshots confirmed that this corrected titles, buttons,
categories, card costs, and most menu text. Three scrolling Almanac description
components were still explicitly bound to the separate `汉仪夏日体W SDF`
handwriting asset (resource path IDs 187255, 193273, and 194141), so they did
not benefit from the Dynamic transplant. The v5 refinement retargets only
those components to Dynamic and its matching material at 18 points. It also
reduces the plant Almanac title from the anomalous 70 points to the same 50
points used by the correctly fitting zombie title. All other components are
left as produced by v4.

V5 screenshots then exposed a second layer: the current PC `LawnStrings` and
`ZombieStrings` data embeds `<size=36>` in almost every field, overriding the
correct 18-point Android component size. Joseph's English 3.6.1 copies of both
assets contain no TMP size tags at all. V6 follows that proven Android behavior
and removes 2,780 opening/closing size tags from those two assets while
preserving their JSON structure and all translated content.

The V6 serialized-UI audit also reduced CJK-bearing TMP text components from
68 to zero. This includes compact romanized credits (`LanPiaoPiaoFly`,
`Gfishtus`, `Mengluo`, `Aya Shameimaru`, and `Landie`), contributor links,
storage/upgrade labels, shortcuts, draw screens, Zen Garden status, statistics,
and several later locked-mode defaults. The zombie Almanac title and shadow
were reduced to 36 points to target Joseph's single-line presentation.

V6 device screenshots identified two final layout collisions. The rotating
plant Almanac tip used a 1200-unit-wide, fixed 36-point text rectangle that
continued beneath the centered Search control. V7 preserves its left edge but
reduces the rectangle to 880 units, ends it before Search, disables wrapping,
and enables 12–24-point automatic sizing.

The Help/Credits parchment is a baked 1400x600 texture containing the original
credits, Hotkeys, translation credits, and Joseph Franci attribution. Two live
TMP overlays were redundantly drawn over the baked Hotkeys and bottom-right
credits. V7 blanks only those overlays and leaves the original texture
unchanged, avoiding lossy regeneration of names and shortcut text.

V8 reuses the dormant creator-list TMP layer to add `aha · SilverShadow`
directly beneath the baked Joseph Franci Android-port attribution. It also
translates all 27 visible `PlantEvolutionData` route labels and the remaining
`TalentData` label (`Quick Hands I`). A post-build CJK audit reports zero
serialized UI components and only 17 TextAsset leaves; those are level-maker
or contributor names, an internal shader README, and two legacy raw data
tables. They are deliberately retained.

V9 corrects the final plant-detail collision found during device testing. The
PC-sized `Change Skin` label rendered at an effective 36 points beneath the two
skin-navigation arrows. All three duplicated Almanac variants now use the
compact 24-point `Skin` label, preserving the control while keeping it clear of
both arrows.

V10 replaces the poorly matched Android-port overlay font with the bundle's
actual parchment handwriting TMP asset (`汉仪夏日体W SDF`, path 178477,
material 2). It preserves the baked `Joseph Franci` attribution and places
`aha · SilverShadow · Codex` on a wider separate line underneath. The visible
disclaimer phrase “only on the dev” is also rewritten as a direct official
source attribution. Serialized player-facing UI remains free of unexplained
CJK; remaining matches are names or internal data.

Device testing showed that the V10 TMP asset still resolved to a visually
mismatched face and placed the added line too close to the torn parchment edge.
V11 removes the runtime dependency: it extracts the game's embedded legacy
`fzjz` font, renders `Joseph Franci · aha · SilverShadow · Codex` as a single
line directly into the original 1400×600 `thanks` texture, and blanks TMP
component 179902. The saved bundle is reopened and the texture is extracted
again for exact preview validation before APK packaging.

The almanac data came almost directly from the PC translation repository:

- `ZombieStrings`: exact match to current PC English data.
- `DetailStrings`: exact match to current PC English data.
- `LawnStrings`: only two records differ from current PC English data.

## IL2CPP metadata method

The Android 3.8.1 Zen Garden Tool Shop builds its green price/ownership text
from two runtime format fragments (`{0}\n价格：{1}` and
`\n已持有{0}个`). The upstream PC regex only matches a fully rendered shop
string containing concrete digits, so these fragments survived earlier
metadata passes. `build_metadata_translation.py` now carries narrow,
screenshot-confirmed Android mappings to `Cost` and `Owned`; it does not apply
a general Chinese-text substitution.

All examined builds use metadata version 31. Each literal lookup entry is an
eight-byte `(byte_length, relative_offset)` pair. The header stores lookup and
literal-database offsets at bytes 8 through 23.

| Build | Literals | Data offset | Header data size |
| --- | ---: | ---: | ---: |
| Chinese 3.6.1 | 12,914 | 103,568 | 385,280 |
| Joseph 3.6.1 | 12,914 | 10,860,853 | 385,280 (stale) |
| Chinese 3.8.1 | 14,249 | 114,248 | 432,780 |
| aha 3.8.1 embedded | 14,249 | 10,879,107 | 436,140 |
| aha 3.8.1 follow-up | 14,249 | 10,879,107 | 435,917 |

Both translators append a rebuilt literal database and redirect the lookup
table to it. Joseph's header failed to update the data-size field; the game
tolerates it, but the new builder writes the correct value. Repeatedly patching
an already patched file also causes needless growth. The new builder always
starts from a clean official file and produces a deterministic single append.

Literal changes:

| Comparison | Changed occurrences |
| --- | ---: |
| Joseph 3.6.1 versus Chinese 3.6.1 | 2,105 |
| aha embedded 3.8.1 versus Chinese 3.8.1 | 280 |
| aha follow-up 3.8.1 versus Chinese 3.8.1 | 335 |
| New generated 3.8.1 versus Chinese 3.8.1 | 2,571 |

The new build combines 1,841 current PC exact matches, 123 current PC regex
matches, 579 Joseph fallback mappings, and 28 aha fallback mappings. It reduces
CJK-bearing literal occurrences from 3,762 to 1,236. The remaining literals
are retained unless they can be proven player-facing; blindly translating
internal keys, test strings, or configuration values is unsafe.

## First 3.8.1 TextAsset rebuild

Starting from aha's font-enabled 3.8.1 bundle, the deterministic TextAsset
builder modifies and validates 278 of 291 text assets. It applies current PC
almanac/tip data, safely reuses Joseph content only where the Chinese source is
unchanged, and recursively translates remaining JSON string leaves.

The rebuilt bundle:

- preserves every JSON asset's root type and top-level key set;
- matches all 274 current PC Fusion Showcase/I-Zombie tip entries that
  correspond to bundled assets;
- reduces CJK-bearing TextAsset content from 21,852 characters in aha's bundle
  to 1,141 characters across 20 assets;
- retains remaining Chinese that is also present in the available PC
  translation source, internal data/credits, or newly untranslated content.

This output is not yet an end-user release. It must be tested on Android before
being inserted into a signed APK.

## First packaged research APK

The payload packager successfully inserted the generated bundle and metadata
into aha's 3.8.1 APK shell without rebuilding the Android manifest or native
libraries. The local research build verifies with APK Signature Schemes v1,
v2, and v3, passes `zipalign -c 4`, retains package
`com.LanPiaoPiao.PlantsVsZombiesRH` and version `3.8.1`, and contains the exact
expected payload hashes.

It is signed with a local Android debug key for testing only. That certificate
does not match the official, Joseph, or aha certificates, so it requires a
one-time save backup and reinstall unless the device already has a build signed
with that same local key.

## Signing identities

The official Chinese APK, Joseph APK, and aha APK use different signing keys.
aha used the standard Android debug certificate. Consequently, users cannot
install one build as an update over another unless it has the same signing key.
A maintained release must establish one stable project key and preserve it.

No attempt should be made to obtain or bypass somebody else's private signing
key. A one-time save migration/reinstall is the legitimate path when changing
signing identity.

## Final 3.8.1 English release audit

The final package uses the official Chinese 3.8.1 APK—not aha's repackaged
shell—as its Android base. Comparative auditing proves the manifest, resource
table, `classes.dex`, all eight ARM native libraries, and every other
non-signature entry are byte-identical to the official APK. Only the two
declared translation payloads differ:

- `data.unity3d`: `90ebea8f5e876bf5d74054e3656228de3642af97b633d4b721c8d7fc71366be2`
- `global-metadata.dat`: `51670b65758f26adc7856a3cfc1eb9412e300174fcc552726dd783a06844dbc2`

The final APK passes ZIP integrity, `zipalign`, and Android v1/v2/v3 signature
verification. Its dedicated 4096-bit release certificate has SHA-256
`1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6`.
Windows Defender reported no threats on August 11, 2026. These checks provide
strong comparative evidence about the port but are not an absolute guarantee
about the upstream game or every runtime path.
