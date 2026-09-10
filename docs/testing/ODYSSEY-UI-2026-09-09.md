# Odyssey upgrade screen feedback — September 9

## Scope and authority

The user authorized plain, harmless UI translations after screenshot review
when PC does not have them. Plant and modifier names, recipes and gameplay
descriptions still require completed, source-aligned PC wording.

Checked remote PC 3.9 commit `67a6767ba332d0793a2752dffa59543f6e0448e1`.
The existing build source remains pinned at
`5d3ca86876cafc38b70c4a8aa87f6f5cf54266f2`; unrelated upstream updates were not
silently incorporated into this narrow correction.

## Prepared counter correction

The official Android metadata contains two complete format strings for the
four Chinese labels shown in the first screenshot:

| Literal index | Original | Prepared English | Provenance |
| --- | --- | --- | --- |
| 46 | `\n\n伤害占比：{0:F2}%\n总词条数：{1}` | `\n\nDamage Share: {0:F2}%\nTotal Modifiers: {1}` | Reviewed generic UI; no completed PC translation found |
| 17055 | `当前幸运：{0}\n场上敌人数量：{1}` | `Current Luck: {0}\nZombie(s): {1}` | Reviewed two-line Android adapter using PC counter wording |

PC's regex file translates the standalone zombie counter and a three-line
luck/zombie/difficulty counter. Neither rule fully matches Android's two-line
block. The standalone counter and the combined zombie/plant-limit counter
were already translated in the candidate and remain unchanged. No partial
regex replacement was used, and no difficulty-points line was added.

Moved the two historical candidate mappings into `ANDROID_39_REVIEWED_UI_EXACT`
so the explicit 3.9 UI allowance applies. The prior strict new-content filter
had preserved these strings in Chinese. Future complete PC English still wins.

## Shield card: awaiting PC description

The second screenshot corresponds to `advancedBuffs.13001`. Latest PC names
it **Enchanted Shield**, but leaves its description in Chinese. PC's source
and target describe the shield-based healing effect without Android's extra
immediate 6,000-shield clause. There is no completed, source-aligned PC English
description for the full Android card.

Preserved metadata literals 17184 (title), 17185 (combined title/body), and
17195 (extended body) exactly as in the prior candidate. Keep the card together
pending a complete PC translation; do not substitute an older shorter effect
description or create an independent ability name. Historical assisted
`Shield Protection` mappings already exist in the builder but were not enabled
or automatically reverted by this work.

## Upstream data issue

Latest PC `Localization/English/Strings/travel_buffs.json` is invalid JSON:
`debuffs.10000` has a missing comma after `"name": "Jinxed"` (line 1328).
The strict parser rejected it. The inspection report records the error;
the malformed file was not used to build a payload or edited upstream.
For the counters, its raw source contains none of the four target Chinese
label terms. The shield record was inspected directly in the raw source at
lines 659–662 and compared with the valid source dump. Do not treat this
investigation as validation of a full September 9 PC import.

## Verification and continuation

Rebuilt metadata from the clean official 3.9 input using the existing release-6
preservation workflow. Compared all 19,061 literal occurrences against the
prior verified candidate: exactly indices 46 and 17055 changed. Placeholder
order, format precision, percent signs and newline counts are preserved.
All metadata bytes outside the literal table, text heap and their header
bookkeeping are identical. All 15 regression tests pass; diff whitespace
validation passes. No bundle, layout, plant data, executable code, APK,
signature, release or cheats-version edit was made.

Current candidate: task `work/english-audit/global-metadata.dat` and its
`metadata-report.json`. This adds two literal corrections to the prior 14;
the September 6 reports remain historical snapshots. Incremental evidence is
in task `outputs/odyssey-labels-verification.json`. Before/after payloads and
the bounded build log are in `work/odyssey-labels/`.

Device testing remains pending, particularly label fit at different screen
sizes and long counters. Both tester findings appear once in the running
release notes, with the shield card distinguished from prepared fixes.
