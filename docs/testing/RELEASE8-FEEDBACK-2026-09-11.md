# Release 8 feedback preparation — September 11

The user initially supplied three screenshots, then Luck/Shield and Respawn
upgrade screenshots. Complete PC English is required for plant names and effect
descriptions. The user subsequently reaffirmed permission to translate generic
UI labels with context-aware English, then approved Blast Protection's clear
shield clause as a specific description exception. The final clarification
extends that exception to plain UI and basic effects: preserve PC plant names,
recipes, and descriptions with specialized terms, but translate straightforward
generic text. The final generic review below supersedes the initial deferrals.
No APK build or publication was requested.

The initial check found PC `3.9` at Release 7's reviewed `9afdca02` commit.
A fresh fetch during the follow-up found `708ffb136e33ccc6bb6db2fa67213170708934a9`.
The intervening changes affect three Portuguese menu images only. The 25 exported
English/Dump JSON inputs strictly parse and match the previous reviewed snapshot;
there is no new English wording to import.

## Screenshot 1: two Chinese modifiers

| Android record | PC record | Finding | Action |
| --- | --- | --- | --- |
| Literal 17185, 护盾保护 | `advancedBuffs.13001` | Name: Enchanted Shield. Description remains Chinese. | Keep complete Chinese card. |
| Literal 15961, 不破不立 | `advancedBuffs.13100` | Name: No Pains No Gains. Description remains Chinese. | Keep complete Chinese card. |

PC's No Pains No Gains description still includes the plant destruction,
damage/speed bonus reduction, and repeat-after-20-waves behavior only in
Chinese. Do not enable the older assisted English fallback. Shield's separate
title and extended body also stay unchanged; the earlier Android/PC extended
effect discrepancy has not been resolved by this PC commit.

## Screenshot 2: actual missed menu title

- Screen: Odyssey: Challenges; next to Laser Pumpkin Skin Challenge.
- Android TMP object: `resources.assets`, path ID `191808`.
- Hierarchy: `Name / Window / Level / Page2 / PageNormalTravel / Levels / TravelChallengeMenu`.
- Serialized source: `究极黑曜石高坚果\n皮肤挑战`.
- Complete PC key: `究极黑曜石高坚果皮肤挑战`.
- PC translation: `Obsidian Tall-nut Skin Challenge`.
- Prepared caption: `Obsidian Tall-nut\nSkin Challenge`.
- Cause: Android's embedded newline prevents the ordinary exact PC key match.
- The associated runtime level-title literal 18101 is already English in
  Release 7, so no metadata change is needed.

`scripts/fix_obsidian_skin_challenge_caption.py` requires that complete PC
entry, guards the exact object and hierarchy, changes only the serialized text
field, and reopens the output to compare every object with expected bytes.
It refuses changed/missing PC wording for review rather than making up text.

## Screenshot 3: unclear comment and old English wording

The comment "i dont know, something is fine here" does not identify a precise
defect. Do not interpret it as an instruction to change gameplay or naming.
The screenshot differs from the verified Release 7 APK, including the old
"Envy: Zombies deal..." wording. Release 7 already matches complete current
PC records for all eight shown cards:

| Literal | Release 7 PC title |
| --- | --- |
| 16753 | Predator Instinct |
| 18416 | Curse of 1 4 3 7 |
| 18049 | Blessing of 1 4 3 7 |
| 18414 | Curse of Aggression |
| 18047 | Blessing of Aggression |
| 18417 | Curse of Equity |
| 18050 | Blessing of Equity |
| 18415 | Curse of Endurance |

Predator Instinct says plants deal 30% more damage to zombies above 50%
health and 30% less below 50%, resolving the damage-direction problem in the
old screenshot. Checked the metadata read directly from the local published
Release 7 APK; its hash matches the release record. The screenshot alone does
not establish the reporter's installed version or whether a stale override
is present. No additional edit is justified by the ambiguous comment.

## Follow-up screenshots: Luck, Shield, Respawn

The initially supplied two pictures are duplicates; the replacement second
picture identifies the Respawn card. Shield is the same deferred extended
description listed above, including the Android-only immediate 6000 shield clause.

| Literal | Finding | Prepared action |
| --- | --- | --- |
| 16954 | PC regex matches a fixed `/250`; Android uses `{2:F0}` for the cap. | Use complete PC Luck prose and retain Android's cap argument. |
| 16697 | Android adds `标准` to the current respawn-time label. | Use complete PC respawn prose and say `Current standard respawn time`. |

Both adapters require the exact reviewed Android source, complete PC regex, and
expected PC English. They reject changed or absent PC wording and extra Android
effect clauses. The existing whole-string matcher remains strict. Placeholders
`{0:F0}`, `{1:F1}`, and Luck's `{1}/{2:F0}` are preserved exactly.

Six generic UI literals also change under the user's explicit UI exception:
98 (Remaining), 119 (Needed), 15725 (Cost/chance), 17062 (Elapsed time),
18419 (Curse objective), and 18711 (selected note/track/type).
These do not replace plant names, effects, or dynamic argument values.

## Wider pattern review

- Compared all 19,061 metadata literals against complete PC exact/regex matches
  and whitespace-normalized exact keys; no additional complete misses were found.
- Examined 351 remaining Chinese format templates and reviewed 12 candidates
  with similar PC regex wording. Luck and Respawn are the two effect matches.
- Literal 15722 describes a **random independent damage bonus**. PC's nearby
  fixed damage-bonus rule does not cover it; leave the effect text unchanged.
- Other near matches include debug logs, different messages, and incomplete
  regex captures. Do not translate them by dropping unmatched clauses.
- Scanned 2,586 serialized UI text objects and 282 TextAssets, including 39
  remaining Chinese UI/JSON string fields. No additional complete or whitespace
  variant matches were found after the skin-challenge fix.

Detailed local reports: `work/release8-feedback/pattern-audit.json`,
`near-regex-review.json`, `similar-bundle-review.json`, and `upstream-latest.json`.

## Reported Release 6 to Release 7 regression

Verified the additional Luck/Blast Protection screenshot by extracting metadata
directly from the local published Release 6 and Release 7 APKs, rather than
inferring their contents from the current source or historical fallback entries.

| Literal / screen text | Release 6 | Release 7 | Release 8 candidate |
| --- | --- | --- | --- |
| 16954, Luck upgrade body | Chinese | Identical Chinese | PC-based English, prepared |
| 16209, Blast Protection body including immediate 3000 shield | Chinese | Identical Chinese | English after user-approved shield-clause exception |
| 17906, shorter Blast Protection overview card | English | Identical English | Unchanged English |

This does **not** establish a Release 6-to-7 regression for these two screenshot
descriptions. The short Blast Protection description was already English, but
does not include the extended upgrade's shield clause. That difference could
explain the report; the screenshot alone cannot establish the tester's earlier
screen or APK. Do not replace the longer description with the shorter English.

Release 6 extracted metadata SHA-256:
`c916d7b96bc29dd2b5f6114a6ff8e19ffe4f970897e885b012a5d2a697cc0887`.
Release 7 extracted metadata SHA-256:
`ccb4c7fef2308a69297254add15b384634439d3c1948e63d8d20a306f0ba3683`.
Detailed evidence: `work/release8-feedback/release6-vs-release7-reported-cards.json`.
No game payload changes were made for this verification.

The user subsequently clarified that the straightforward shield clause should
be translated because it introduces no new plant name or confusing terminology.
The candidate now says: `Reduce Zombie Jack-in-the-Box explosion damage to 1000.
Immediately gain 3000 Shield.` (one paragraph in the game). The first sentence
uses PC's existing wording; the second directly translates Android's added
clause. This is a documented user-approved exception, not a claim that PC has
translated the longer description. Both numbers and all gameplay code remain
unchanged. The earlier comparison report records the candidate before this edit.

## Verification / next build

The user-requested broader generic pass added 43 exact-source translations.
Enchanted Shield and No Pains No Gains now use their PC names and faithful basic
effect text; random damage bonuses are also translated. These three earlier
deferrals are resolved under the clarified policy, not by a new upstream import.
See [the complete generic-text review](RELEASE8-GENERIC-TEXT-REVIEW.md) for each
source, translation, and retained exclusions.

Prepared bundle: task workspace `work/release8-feedback/data-release8.unity3d`.
Report: `work/release8-feedback/caption-verification.json`.
All 201,406 objects are verified; only object 191808's text field changes.
The component's remaining bytes, including font/layout references, match.
Metadata candidate: `work/release8-feedback/global-metadata.dat`; report:
`metadata-verification.json`. Exactly 52 literals change from Release 7;
all other literals and non-text metadata bytes match. Every changed placeholder,
precision specifier, numeric value, and newline count is preserved. All 24 tests pass, including
guards for missing/changed PC rules and extra Android effect clauses.

Keep Release 7 audio/native code unchanged. Run the caption script after
PC reconciliation and before packaging; use this bundle and the new metadata.
Retest Odyssey: Challenges and the Luck/Respawn/Blast Protection/Enchanted Shield/
No Pains No Gains cards on Android; this device check is still pending for the authorized prerelease.
The user subsequently authorized packaging and prerelease publication on September 11. The APK is signed and audited; see RELEASE8-BUILD.json. Android device testing remains pending and is explicitly disclosed in the release notes.
