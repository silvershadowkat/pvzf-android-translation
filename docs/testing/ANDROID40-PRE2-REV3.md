# Android 4.0 prerelease 2 rev 3

Published unchanged as Android 4.0 English prerelease 2 (`v4.0-release-2`) after explicit maintainer approval. Based on rev 2, commit `d57d500bcee458579b159ab08554c74d2440989e`. The public filename omits the local `-rev3` suffix; bytes and SHA-256 are identical. See `ANDROID40-PRE2-RELEASE-BUILD.json`.

## Approved scope

The maintainer approved **God Coins** as provisional English for `诸神币`. Apply it consistently to visible balances, costs, purchase dialogs, rewards and notices. This is a specific naming exception, not permission to invent other names. The pinned PC source remains `9a170fdfa999e4e8dc6fe45e31c0806a1271577d`.

54 additional fields are changed: 34 metadata literals, 11 catalog availability conditions, 5 catalog descriptions, and 4 serialized UI fields. The rules are recorded in `assets/gods-almanac-rev3-4.0.json` and applied after rev 2 by `scripts/apply_gods_almanac_ui.py`.

- Replaced all active display occurrences of `诸神币` with God Coins. Card prices `50币` and `100币` also use God Coins. Other currencies are unaffected. Some otherwise untranslated mode descriptions retain Chinese names/prose, with only the approved currency term changed.
- Changed the small tactic ordinal fragments to `Level 1`, `Level 2`, etc. Read-only native inspection traced the prefix/suffix to the Almanac's `EntryMeta` display construction. The compact card prices were found in `RefreshCatalog` and `SelectRoot`. No native instructions were modified.
- Translated the plain endless-mode round/reward instruction and classic-mode reward prompt using existing mode terminology.
- Added five clear effect descriptions: three basic Solar Reactor effects, the larger hammer after a hit, and the mechanical ship targeting the leftmost zombie. Solar Reactor is existing PC terminology for `阳光反应器`, verified in the Sun God / Stellar Prophecy PC entry. The ship and hammer wording describes ordinary objects without creating proper names.

The prior rev 2 rules remain a separate historical layer. They still record the previous decision to retain the currency, which rev 3 intentionally supersedes. Keep both stages when reproducing this candidate. If PC English later supplies complete usable wording, the exact-match PC mapping takes priority. Do not rename the actual currency storage fields or save keys.

## Review of all 11 screenshots

Each screen's heading, tabs, left list, middle cards, right description/availability text, bottom balance and footer was reviewed. Generic headings and availability text already looked translated. The remaining repeated generic omissions were the currency and level labels.

| Screenshot time | Selected tactic | Result |
|---|---|---|
| 21:55:07 | 天罚 | Basic lightning effect already English. Retain named tactic titles. |
| 21:55:04 | 光棱 | Translate the plain ship/leftmost-target instruction. Retain names and unconfirmed refraction terminology. |
| 21:55:02 | 业火 | Retain the named explosion/skill description and titles pending PC wording. |
| 21:54:59 | 宝藏 | Basic effect already English. Retain names. |
| 21:54:57 | 交易 | Basic effect already English. Retain names and the complex maximum-tier description. |
| 21:54:55 | 硬化 | Basic damage reduction already English. Retain names and the specialized maximum-tier interaction. |
| 21:54:52 | 明月 | Retain unconfirmed named reactor/effect descriptions and titles. |
| 21:54:50 | 裂空 | Retain the named miniature mech descriptions and titles. |
| 21:54:48 | 战锤 | Basic effects already English. Additionally translate the generic maximum-tier large-hammer instruction. Retain titles. |
| 21:54:47 | 烈阳 | Translate three basic Solar Reactor effects using verified PC naming. Retain the named meteor effect and titles. |
| 21:54:45 | 木桩 | Retain the named zombie and specialized damage-sharing descriptions and titles. |

No tactic group, entry ID, quality enum, reflection type, plant name or resource lookup string is translated by this pass. A plain word serving as a tactic's proper name is still a name; do not translate it merely because its dictionary meaning seems simple.

## Verification and next test

See `ANDROID40-PRE2-REV3-BUILD.json` for the final build hash and check results. Verbose local reports are in the task workspace's `work/upgrade40/pre2-rev3`. `ordinal-references.json` and `entry-meta-disassembly.txt` record the read-only ordinal investigation.

- APK: `PvZ-Fusion-4.0-English-Android-prerelease2-rev3.apk`.
- SHA-256: `b21f9295292d00d0239d00f1771eacba19c997064d2d3292333116855ab5811c`.
- 48 tests and 315 actual .NET format templates passed. All 374 reflection references, 206,358 Unity objects and 301 JSON assets passed the integrity audit.
- No introduced placeholder, rich-text or plant-token errors. All 15 original serialized currency fields are covered; active metadata and audited display text contain no remaining `诸神币`. Original unused string bytes remain in preserved metadata storage and must not be mistaken for active display text.
- Official-4.0 and rev-2 APK comparisons passed. Only bundle and metadata changed relative to rev 2 outside signatures. Package details, code, music and other content are unchanged.
- ZIP alignment and v1/v2/v3 signatures passed using the existing certificate. Defender completed with exit code 0.

On Android, check the God Coins balance, locked-plant dialog, route/card costs, and tactic maximum-tier purchase prompt. Check that `Level 1/2/3` fits on the cards. Open the Solar Reactor, mechanical ship and hammer effects, then return and reopen the menu. Avoid spending currency merely to test the text. The maintainer approved this revision as-is. Earlier screenshots confirm catalog operation; exhaustive rev 3 interaction testing and the device model/Android version were not supplied.

Publication was explicitly approved for prerelease 2. Future releases require their own authorization. Gameplay, saves, executable code, music, and layout are unchanged from rev 2.
