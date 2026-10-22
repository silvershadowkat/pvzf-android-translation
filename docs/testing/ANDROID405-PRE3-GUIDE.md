# Prerelease 3 r13: Creator Guide review

Follow-up: [r16 generated editor help](ANDROID405-PRE3-EDITOR.md) adds the separate runtime headings and tool messages, and changes the tutorial's On Enable wording to the visible On Toggle On port label. The user confirmed the main guide looks good on r13. The current apply report includes these later additions; its original r13 version is retained under `editor-r14/baseline-r13-apply-report.json`.

Local candidate, not published. This follows the r12 PC coverage audit.

## What the guide contains

The official Android 4.0.5 `LevelCreatorHelp` TextAsset contains 11 guide topics and help for 241 event-node types. Most text explains ordinary editing, programming and game controls. It is translatable without inventing new content names. The inspected PC source has no complete English replacement for this guide, so this is a reviewed Android translation using PC terminology, not a claim that the entire guide was copied from PC.

All 986 display fields are translated: topic titles/bodies and node purpose/usage/example/warning fields. Related editor labels and full explanations use the existing display-only runtime translator. No node type, level ID, port identifier, game enum, saved-level structure or player input is rewritten.

## Terminology evidence and decisions

PC terminology source: `Teyliu/PVZF-Translation` commit `c7fb5997d65e1d5248f3d7a9ca9c9e0a4b516640`, checked against the Android English payload and visible editor controls. Source files are under `PvZ_Fusion_Translator/Localization/English`.

| Chinese/context | English used | Evidence or decision |
| --- | --- | --- |
| 保存并生成关卡 | Save Level | Existing PC dictionary and the Android bottom button. Do not invent a different button name. |
| 周期切换 / 周期事件 / 周期间隔 | Periodic Cycle / Cycle Event / Interval | Existing PC node/port dictionary. |
| 获得阳光 / 条件分支 / 整数比较 | Gain Sun / Condition Branch / Compare Integer | Existing PC node dictionary. |
| 植物、僵尸名称 | Existing English almanac names | Peashooter, Ice-shroom, Jalapeno, Doom-shroom, Lily Pad, Flower Pot, Pumpkin and Conehead Zombie. |
| 旅行词条 / 羁绊 | Odyssey Modifiers / affinities | PC modifier text and `词条羁绊` entry. |
| 星辉 in plant upgrades | Stellar | PC evolution/modifier wording. Starbound is used elsewhere for adventure names, not this upgrade. |
| 红温 as a zombie status | Enflamed | PC DetailStringsTranslate, Plant System status entry. Do not use the unrelated short-key category wording Conflagration here. |
| 余烬 as a zombie status | Irradiated | PC status explanations and plant descriptions. Do not translate literally as Ember. |
| 传送 as a timed status | Chronoshift | PC DetailStringsTranslate status explanation. Not ordinary teleportation. |
| 蒜值 / 水草值 / 冻结值 | Poison Points / Tangle Points / Cryo Points | PC mechanics tutorial and descriptions. |
| 金咖啡豆 as an item | Golden Coffee Bean | Existing PC modifier/tutorial prose. The isolated dictionary key says Golden Plants in a different UI context and is unsuitable here. |
| 势不可挡 | Breakthrough | PC full zombie-modifier description. |
| 僵尸进家失败 | Lose on House Entry | Corrects PC's misleading 'Zombies failed to enter the house'. The official guide and SetZombieHouseRuleNode explicitly describe the normal loss check, enabled by default. |

## Deliberately preserved technical text

- `二爷无视植物` is the internal name of Breakthrough in the guide's modifier-removal example. The guide instructs users to enter that literal name. Display translation does not make the game accept English lookup inputs.
- `电力相生` is retained as an explicitly identified internal entry name. No verified PC English name was found. Its stated removal behavior is translated without inventing a title.
- `外挂` is retained beside 'special-enhancement flag'. The source distinguishes this flag from Stellar. The guide does not equate them or promise an unverified effect.
- `Bullet_pea`, `walk`, `SuperSkill`, `StarUp`, map enum spellings and all 241 `type` keys remain exact.
- Mouse/keyboard controls are explicitly labeled as the documented desktop controls. No untested Android gesture or touch equivalent is invented. The guide footer uses its working Close button rather than requiring Esc.

These three Chinese technical labels are intentional. The 11 instructional pages are English throughout.

## Accuracy clarifications

The official guide repeats some generic examples under nodes of different types. The English does not silently recommend invalid wiring:

- Float examples explicitly convert Integer inputs where necessary.
- Plant/zombie enum parsing uses a matching enum-to-string round trip instead of the source's unrelated string-to-integer example. It explicitly excludes localized display names.
- Repeated Integer-list get and String-list find examples are marked as examples for those list types; each other node specifies its required matching type.
- List copies create independent containers but do not clone scene objects. This clarification follows the source's CopyListValuesNode warning.
- Keypress help explains that it is a keyboard event, not a newly added mobile button.

All source limits, costs, durations, coordinate conventions and behavior warnings are retained. Numeric token differences are enumerated in `assets/creator-guide-4.0.5-review.json`: 'positive' versus '>0', 'zero-based' versus 'from 0', example identifier digits, and the corrected enum examples. Topic-only differences are English 'Method 1/2', 'Choose 1 of 3', and spelling out third/fourth columns.

## Implementation and reproducibility

- `assets/creator-guide-4.0.5.en.json`: complete reviewed English guide.
- `assets/creator-guide-ui-4.0.5.json`: exact guide-linked UI labels/explanations.
- `assets/creator-guide-4.0.5-review.json`: Chinese source hash and explicit review exceptions.
- `scripts/translate_creator_guide_405.py --work <pre3-work-directory>`: pins the Chinese source, preserves schema/IDs, replaces only TextAsset 3378, checks every serialized object's hash, and applies unambiguous full-string display translations. Existing PC translations take precedence except the reviewed house-entry correction. Nine conflicting context-dependent explanation strings are excluded from the generic dictionary.

The script keeps a frozen r12 baseline and a before/after report under `guide-r13`. It does not touch metadata, original native libraries, saved games, editable text inputs or the managed-file refresh policy. Unknown user files remain preserved. The APK carries the new guide directly in its Unity bundle.

## Validation

- Guide schema, 11 topics, 241 identical type IDs, 986 display fields, bold markup, technical identifiers and reviewed numeric differences checked.
- Compared all 208,662 serialized objects with r12. Only `resources.assets` TextAsset 3378 changed.
- r13 built, signed and installed in place on the S26. All nine readable nontranslation files were unchanged, and existing managed overrides matched the APK. The 11 guide topics were opened; inspected long pages scrolled correctly. The user approved the guide's wording. Do not interpret this content review as exhaustive testing of all 241 gameplay operations or every screen size.

Quick device check: Recommended Levels → Super Custom Levels → Creator Guide. Open the first page, Timed Sun Tutorial, Using the Toolbar, and Combat Rule Limits. Scroll long pages and check Close. In Level Event, select an existing node and use Node Help; reading the guide does not edit or save a level.
