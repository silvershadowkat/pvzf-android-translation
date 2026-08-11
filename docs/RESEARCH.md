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

The almanac data came almost directly from the PC translation repository:

- `ZombieStrings`: exact match to current PC English data.
- `DetailStrings`: exact match to current PC English data.
- `LawnStrings`: only two records differ from current PC English data.

## IL2CPP metadata method

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
| New generated 3.8.1 versus Chinese 3.8.1 | 2,515 |

The new build combines 1,485 current PC exact matches, 130 current PC regex
matches, 821 Joseph fallback mappings, and 79 aha fallback mappings. It reduces
CJK-bearing literal occurrences from 3,762 to 1,298.

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
