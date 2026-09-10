# All modifier categories — September 9, 2026

Local candidate only. Based on the actual Release 6 APK and original Chinese 3.9 metadata; PC commit `e24586aaf9feb85eae6fc30af3460237778558ff`. No APK, signing, push, or release.

## Complete-pattern review

Audited 455 modifier/unlock literal occurrences across all categories, including all 384 combined modifier strings. All 441 usable full PC matches agree with the candidate. Every combined modifier has a nonempty title and body, with Android’s `：\n` separator preserved. This is a whole-dataset check, not a screenshot-only replacement.

This review changes 122 metadata occurrences: 89 completed PC modifier updates, 5 explicitly reviewed Chinese restorations, 22 other unlock descriptions with PC conversion lines, 4 runtime UI labels, and 2 PC prize/rarity terms. Including earlier fixes, metadata differs from Release 6 at 140 occurrences. Gameplay code and nonliteral metadata bytes are unchanged.

The builder now rejects subject-only modifier descriptions and blank-name records before they can bypass validation through generic structured pairing. All four SP Evolution descriptions are present. Jinxed and Expert Fast-track replace the misleading Lost Luck/Wave 8 appearances; Lackey Comeback contains the full wave-51 effect.

## Intentional or already-correct text

PC intentionally has 6 Crisis, 14 Nemesis, and 5 Majestic Presence records with different bodies. Coldsnap Insight I uses `(Level 1)` and II uses plain `Level 2`; retained. Blaze of Glory is already correctly separated. Existing Elemental Fury and Ravenous Reach wording matches the full PC body and remains; the latter includes PC’s known-bug note.

The older clipped/full-description-as-title screenshots do not match the corresponding Release 6 literal contents. That does not establish the tester’s installed version or the cause; no imported-save or installation diagnosis is claimed. The later screenshots containing Chinese for Gamble of Bounty, Rejuvenating Essence, Bullet Hell, Stickier Butter and Treasure Hoard are addressed by the same whole-record import.

## Chinese retained or restored

| Literal | Reason |
| --- | --- |
| 15961 | PC No Pains, No Gains still has Chinese gameplay text. |
| 16188 | PC Curse of Pride source/effects differ from Android (including the multiplier). |
| 16507 | No completed source-aligned PC record found. |
| 16587 | Runtime luck-result template differs from PC Whims of Fate draw description; preserve {0}. |
| 17185 | PC Enchanted Shield description is unfinished; the related upgrade card also has Android-specific shield wording. |
| 17582 | PC Zombie Parry includes a 0.2-second cooldown absent from this Android source. |
| 17651 | PC Undead March description ends after Buckshot Commando Zombie: with no effect. |
| 18709 | PC Pain Response source specifies a damage threshold and numerical cap absent from this Android source. |
| 18820 | No complete source-aligned PC Minion Reinforcement record found. |
| 18876 | No complete source-aligned PC Bully the Weak record found. |
| 18891 | No complete source-aligned PC Leader Reinforcement record found. |

Only literals 17582, 18709, 18820, 18876 and 18891 were deliberately restored from unsupported historical English to original Chinese, preserving the formatted title/body boundary. This implements the user’s scoped request; unrelated historical wording is not automatically reverted.

## Screenshot cross-check

| Screenshot | Reported wording | Literal(s) |
| --- | --- | --- |
| 1 | Headshot Every Time | 17572 |
| 2 | Open Fire | 16974 |
| 3 | Crowded Road | 16866 |
| 4 | Stored Potential | 16515 |
| 5 | Surprise in the Box | 16466 |
| 6 | Resolute Glow | 16674 |
| 7 | Surging Vitality | 17983 |
| 8 | Supernova | 18582 |
| 9 | Unlimited Firepower | 17356 |
| 10 | Blaze of Glory | 16788, 16789 |
| 11 | SP Evolution Phoenix | 1622 |
| 12 | SP Evolution ice/sunburst | 1620 |
| 13 | Ascension - Hand It Over | 18509 |
| 14 | Who Split My Melon? | 18521 |
| 15 | Polarization | 15987 |
| 16 | Envy | 16753 |
| 17 | Curse - Tempered a Thousand Times | 18415 |
| 18 | Fish Ball Protection | 18940 |
| 19 | Unlimited Firepower repeated | 17356 |
| 20 | Elemental Alchemy | 16238 |
| 21 | Brittle Branches | 18295 |
| 22 | Crisis: Celestial Gargantuar | 1772, 1773, 1774, 1775, 1776, 1777 |
| 23 | Crisis: Gatling Doom Newspaper | 1772, 1773, 1774, 1775, 1776, 1777 |
| 24 | Crisis: D.A.M.P. Disc | 1772, 1773, 1774, 1775, 1776, 1777 |
| 25 | Crisis: Alpha Assassin Hitman | 1772, 1773, 1774, 1775, 1776, 1777 |
| 26 | Crisis: Buckshot Knight Captain | 1772, 1773, 1774, 1775, 1776, 1777 |
| 27 | Nemesis: Abysssal Gargantuar | 1758, 1759, 1760, 1761, 1762, 1763, 1764, 1765, 1766, 1767, 1768, 1769, 1770, 1771 |
| 28 | Nemesis: Giga Football Striker | 1758, 1759, 1760, 1761, 1762, 1763, 1764, 1765, 1766, 1767, 1768, 1769, 1770, 1771 |
| 29 | Nemesis: Ultra Mecha-nut | 1758, 1759, 1760, 1761, 1762, 1763, 1764, 1765, 1766, 1767, 1768, 1769, 1770, 1771 |
| 30 | Majestic Presence: Jackson Worldwide | 1806, 1807, 1808, 1809, 1810 |
| 31 | Majestic Presence: Archduke Deathrider | 1806, 1807, 1808, 1809, 1810 |
| 32 | Lost Luck | 15976 |
| 33 | Wave 8 | 16024 |
| 34 | Coldsnap Insight I / II | 18938, 18937 |
| 35 | Purgatory negative selection / Wave 51 | 16023, 52, 121 |
| 36 | Trial Envy / counters / Purgatory mode | 16753, 18429, 46, 17055, 52, 121, 18469 |
| 37 | Random speed bonus / counters | 15723, 46, 17055, 52, 121 |

## Provenance and repeatability

Upstream travel_buffs.json has one missing comma after Jinxed. `scripts/prepare_reviewed_pc_strings.py` exports the pinned JSON files and fixes only that exact hash-checked syntax error; strict JSON parsing remains enabled and no translation value changes. The PC checkout is not merged or modified. Run the metadata builder with the resulting English/Strings directory, clean official metadata, Release 6 reference/preservation report and `--pc-records docs/pc-reviewed-records.json`.

Evidence: task outputs `modifier-review-verified.json`, `all-modifiers-audit.json`, and `recent-changes-safety.json`. Actual Android rendering, scrolling, selection and crash tests remain pending.
