# PvZ Fusion Android Translation Toolkit

Research and tooling for producing a repeatable English translation patch for
the Android IL2CPP build of *Plants vs. Zombies Fusion*. The immediate target
is Android 3.8.1; the larger goal is a workflow that can be rerun when the game
updates.

> Status: Android 3.8.1 release pipeline implemented and self-validating.
> Metadata, Unity text/UI reconstruction, TMP font transplantation, targeted
> layout refinement, APK packaging, and comparative release auditing are
> complete. Final releases still require a real-device smoke test.

This repository intentionally contains **no APKs, game binaries, extracted
assets, signing keys, or bundled translation data**. Supply legally obtained
game files locally and clone the translation project separately.

The community APK is distributed separately on the
[v3.8.1-en.1 release page](https://github.com/silvershadowkat/pvzf-android-translation/releases/tag/v3.8.1-en.1).
Back up saves and read the installation warning there before installing.

## What is known

Joseph Franci's Android 3.6.1 build and aha's unfinished Android 3.8.1 build
use the same basic architecture:

1. Replace IL2CPP string literals in `global-metadata.dat`.
2. Modify serialized content in `data.unity3d` for almanac text, UI text,
   fonts, textures, and other content that is not sourced from IL2CPP literals.
3. Repackage and sign the APK, or install the metadata as a writable hot patch.

Joseph's port was substantially broader. It modified 257 `TextAsset` objects
and 3,081 `MonoBehaviour` objects; aha's 3.8.1 port modified only the three
almanac `TextAsset` objects and 1,598 `MonoBehaviour` objects.

The current clean 3.8.1 metadata build translates 2,594 literal occurrences,
compared with 335 in aha's updated file. Remaining Chinese literal occurrences
drop from 3,762 to 1,211. This does not mean every remaining occurrence is
visible player-facing text, and asset-side text still needs separate handling.

For future maintainers and coding agents, start with
[CLAUDE.md](CLAUDE.md). Also see the [research findings](docs/RESEARCH.md),
[repeatable workflow](docs/WORKFLOW.md), and [release safety notes](docs/RELEASE-SAFETY.md).

## What this Android port changed

This project did not merely copy one old translated APK. For Android 3.8.1 it:

- rebuilt the IL2CPP string-literal database deterministically from a clean
  metadata base, updating offsets and header sizes correctly;
- applied 2,594 translated literal occurrences, including current PC exact and
  regex translations plus conservative historical Android fallbacks;
- rebuilt and validated 278 Unity `TextAsset` objects, covering Almanacs,
  levels, custom levels, tutorials, tips, Abyss/configuration data, and other
  serialized player-facing text;
- translated serialized TextMesh Pro UI while resolving Android-specific
  context collisions such as `Close` versus `Disabled`;
- transplanted the complete PvZ-style TMP dependency set—not just a font file—
  including glyphs, character tables, SDF atlas, material, source-font links,
  and a CJK fallback;
- corrected Android-only font sizes, wrapping, Almanac titles/descriptions,
  footer collisions, the skin selector, Help/Hotkeys overlays, and credits;
- preserved creator/contributor names and internal CJK data that should not be
  translated blindly;
- added deterministic reopen validation, remaining-CJK auditing, payload-only
  APK packaging, and a comparative release safety audit;
- left the Android manifest, DEX bytecode, native libraries, resources, and all
  other executable/application-shell content unchanged from the official
  Chinese 3.8.1 APK shell.

The in-game Android-port credit is baked into the Help parchment as one clean
line in the game's original embedded `fzjz` handwriting font:
`Joseph Franci · aha · SilverShadow · Codex`. The former live overlay is
disabled, so runtime TMP substitution cannot change its font or placement.

## What was reused and from whom

- **LanPiaoPiaoFly and the PvZ Fusion team:** the original game and official
  Chinese Android builds. No game binaries are stored in this source repo.
- **Joseph Franci:** the pioneering English Android 3.6.1 port. Its clean
  Chinese/English pair supplied conservative fallback mappings; its broad
  Unity changes and original PvZ typography provided the reference for what a
  complete Android port needed to cover. No Joseph APK content is distributed
  from the source repository.
- **aha:** the unfinished English Android 3.8.1 port and follow-up metadata,
  which proved the same-version font/UI injection path and supplied a small set
  of same-version fallback translations. It remains a translation/font
  reference; the public release uses the official Chinese APK shell instead.
- **Teyliu and the PC translation community:** the current English strings,
  regular-expression translations, Almanac databases, level/custom-level
  text, tips, textures/references, and translation terminology. Current PC
  translations take priority over historical Android fallbacks.
- **SilverShadow:** project direction, artifact gathering, Discord research,
  extensive real-device screenshot testing, visual review, and community
  release stewardship.
- **Codex:** comparative analysis, deterministic builders/auditors, Android
  asset/font/layout integration, packaging, documentation, and release checks.

## Thanks and upstream credits

Deep thanks to the original development team: **LanPiaoPiaoFly** (program,
direction, animation and visual direction), **机鱼** (animation and animation
help), **梦珞** (video editing), and **蓝蝶** (animation/art help), plus upstream
special thanks to **北窗遥望, 略nd, MC-大麦, 潜艇伟伟迷, 熔莹, 射命丸文, 使徒,
Tip杨山木雁, 小黄鸡, 云耀yoke, and 庄不纯**.

The English translation exists thanks to **Mamoru-kun** (main translator),
**NaKune** (original translation-mod creator), **Climeron** (coding help and
font implementation), **Teyliu, Cassidy, JustNull, and Dakosha** (coding),
**TrevTV** (audio replacement), **Rollerlhite** (menu music), **Cassidy**
(English logo), **Roaoming and Shel** (custom textures), **flexyj and
CarrotD1scord** (translation textures), **Xabdi** (textures and music), and the
**Blooms Community** (translation ideas and assistance).

English translation and correction contributors credited upstream include
**Mamoru-kun, Cassidy, Ungoodapple, JustTer, Invis19, Dyna, Professor Cherry
Zaitsev, Dimardan, IzzytehWolf, |>.<|, Diiax, Hetsuko, Metroidsans, Flow,
TheXL, QwwYQ, Bertie690, and revo**. The authoritative and evolving credit list
is maintained in [Teyliu/PVZF-Translation](https://github.com/Teyliu/PVZF-Translation);
if this summary ever conflicts with upstream, upstream takes precedence.

Finally, thank you to **Joseph Franci** and **aha** for making Android English
ports possible before this toolkit existed, and to every tester and player who
reported untranslated or poorly formatted screens.

## Related and parent projects

- [Teyliu/PVZF-Translation](https://github.com/Teyliu/PVZF-Translation) —
  translation data, releases, credits, and community documentation.
- [Teyliu/PVZFusionTranslation](https://github.com/Teyliu/PVZFusionTranslation) —
  PC runtime translator implementation used as an architectural/data reference.
- [ArifRios1st/PVZ-Hyper-Fusion-Mod](https://github.com/ArifRios1st/PVZ-Hyper-Fusion-Mod) —
  credited by the PC translator as the original translation-mod predecessor.
- [jozsefsallai/il2cpp-stringliteral-patcher](https://github.com/jozsefsallai/il2cpp-stringliteral-patcher) —
  documented IL2CPP append-and-redirect method that informed the independent
  deterministic metadata builder.
- [K0lb3/UnityPy](https://github.com/K0lb3/UnityPy) — Unity asset parsing and
  serialization used by this toolkit.
- [UnityPy-Org/TypeTreeGeneratorAPI](https://github.com/UnityPy-Org/TypeTreeGeneratorAPI) —
  managed Unity type-tree generation used for IL2CPP MonoBehaviour editing.
- [TrevTV/MelonLoader-AudioTools](https://github.com/TrevTV/MelonLoader-AudioTools) —
  upstream PC translation audio replacement credit; not bundled by this port.
- [iBotPeaches/Apktool](https://github.com/iBotPeaches/Apktool) — local APK
  inspection during research; the release packager itself performs surgical
  ZIP entry replacement and does not rebuild Android resources.

See [THIRD_PARTY.md](THIRD_PARTY.md) for license-oriented attribution. These
links acknowledge lineage and tooling; they do not imply endorsement of this
independent Android release.

## Metadata builder

`scripts/build_metadata_translation.py` uses only the Python standard library.
It starts from a clean official metadata file every time, applies current PC
exact and regex translations, optionally learns fallback mappings from known
Chinese/English Android pairs, appends one rebuilt literal database, corrects
the metadata header, and validates the result by reading it back.

Example layout (all ignored by Git):

```text
artifacts/
  ChineseAPK3.6.1/
  ChineseAPK3.8.1/
  JosephEnglish3.6.1/
  ahaEnglish3.8.1/
translation-data/
```

Example invocation:

```powershell
python scripts/build_metadata_translation.py `
  --base artifacts/ChineseAPK3.8.1/global-metadata.dat `
  --strings-dir translation-data/PvZ_Fusion_Translator/Localization/English/Strings `
  --reference-pair Joseph-3.6.1 artifacts/ChineseAPK3.6.1/global-metadata.dat artifacts/JosephEnglish3.6.1/global-metadata.dat `
  --reference-pair aha-3.8.1 artifacts/ChineseAPK3.8.1/global-metadata.dat artifacts/ahaEnglish3.8.1/global-metadata.dat `
  --output generated/global-metadata.dat `
  --report generated/metadata-report.json
```

The order of reference pairs sets fallback priority. Current PC translation
entries always take precedence over learned historical mappings.

## Unity analysis utilities

Install the optional Unity dependency:

```powershell
python -m pip install -r requirements.txt
```

Available scripts:

- `audit_translation_provenance.py` reports which Android mappings are
  platform-required and which Codex-assisted fallbacks have been superseded by
  newer PC community translations. See
  [`docs/TRANSLATION-MAINTENANCE.md`](docs/TRANSLATION-MAINTENANCE.md) for the
  complete refresh and major-version migration workflow.
- `build_unity_text_translation.py` builds and reopens a translated TextAsset
  bundle, preserving JSON structure and using current PC data before safe
  unchanged-source historical fallbacks. Its optional `--preserve-fonts-from`
  argument restores matching Font objects from an official bundle after using
  an unfinished translated bundle as the UI/text source.
- `build_unity_ui_translation.py` rewrites only the serialized `m_text` field
  of TextMesh Pro components. It uses the official same-version bundle as the
  structural source, applies contextual UI fixes and current PC data first,
  and treats unfinished builds only as fallback translation data.
- `replace_unity_font_data.py` transplants donor font payloads into stable
  same-version Font object IDs. This permits Joseph-style typography without
  changing TextMesh Pro component layout or introducing fragile object paths.
- `transplant_tmp_font_asset.py` performs the complete TMP transplant: glyph
  and character tables, SDF atlas pixels, material settings, source Font
  references, and an optional CJK fallback, all remapped into stable target
  object IDs.
- `refine_almanac_layout.py` retargets only the three long 3.8.1 Almanac
  description components from the handwriting TMP slot to the transplanted
  Dynamic slot and normalizes the oversized plant-page title.
- `polish_android_ui.py` removes PC-only Almanac size tags to match Joseph's
  Android data, translates visible configuration-backed labels, adds the
  credits staging text, cleans mixed-language UI defaults, and applies
  the final narrow title/layout corrections.
- `bake_help_credits.py` replaces the 1400×600 Help parchment texture with a
  deterministic pre-rendered version and blanks the former live credit layer.
- `audit_remaining_cjk.py` separately inventories CJK-bearing IL2CPP literals,
  TextAsset JSON leaves, and serialized TMP text so internal data and creator
  names are not confused with missed player-facing UI.
- `audit_fixed_backgrounds.py` inventories fixed 1920x1080 `Background`/`BG`
  RectTransforms and records their complete menu hierarchy. Its results are
  evidence for targeted ultrawide fixes, not permission to stretch every
  reference-resolution screen.
- `audit_apk_release.py` proves that the manifest, DEX, native libraries,
  resources, and all other undeclared entries are byte-identical to the chosen
  APK shell; only the two expected data payloads may differ.
- `package_apk_payload.py` replaces only `data.unity3d` and
  `global-metadata.dat` in a supplied APK, removes obsolete signature entries,
  and validates the embedded payload hashes. Its output is deliberately
  unsigned; use Android SDK `zipalign` and `apksigner` afterward.
- `compare_unity_bundles.py` compares serialized object hashes by asset file and
  path ID.
- `inventory_unity_bundle.py` inventories object types, names, and text assets.
- `extract_text_assets.py` extracts selected Unity `TextAsset` objects.

## Safety and distribution

- Back up Android saves before reinstalling or changing signing identities.
- A re-signed APK cannot update an APK signed by another private key. Choose one
  project key and preserve it securely for future releases.
- Local research APKs may be signed with a debug key, but public releases should
  use a dedicated private project key that is securely backed up.
- Do not commit or publicly redistribute game APKs or proprietary game assets.
- Translation data from Teyliu's project is CC BY-NC 4.0 and must remain
  attributed and noncommercial.

This is an independent fan interoperability project and is not affiliated with
PopCap, Electronic Arts, LanPiaoPiao, or the translation maintainers.
