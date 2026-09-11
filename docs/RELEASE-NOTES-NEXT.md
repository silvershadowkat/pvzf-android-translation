# Release 8 — prepared changes

Release 7's concise notes are in [RELEASE-NOTES-3.9-PRE7.md](RELEASE-NOTES-3.9-PRE7.md).
The full review is archived in [testing/RELEASE7-TRANSLATION-DETAILS.md](testing/RELEASE7-TRANSLATION-DETAILS.md).

## Prepared

- Translated **Obsidian Tall-nut Skin Challenge** in Odyssey: Challenges using PC's existing English. Android's extra line break had prevented the title from matching. Kept a two-line layout.
- Fixed missed **Luck** and **Respawn** upgrade text using PC English. Preserved Android's variable Luck cap and standard respawn-time label.
- Translated **Blast Protection**'s extended upgrade text, retaining PC's damage wording and adding the clear immediate 3,000-shield clause with user approval.
- Translated six generic counter/status fields: remaining, needed, cost chances, elapsed time, curse objective, and selected music note.
- Translated 43 more plain UI/effect fields, including **Enchanted Shield**, **No Pains No Gains**, crush protection, random bonuses, coin drops, and save/status messages. Modifier names stay PC-authored.

## Checked / left unchanged

- **Enchanted Shield** and **No Pains No Gains:** PC still lacks English descriptions. Under the user's clarified policy, translated their straightforward effects and retained PC's exact names.
- The reported English curse/blessing screenshot uses wording older than Release 7. Release 7 already has the PC names and descriptions, including **Predator Instinct** correctly describing damage dealt by plants. No further change made.
- Latest PC check: `708ffb13` only adds Portuguese menu images since the last import; no new English translations.
- Preserved plant names, fusion recipes, specialized/ambiguous descriptions, command tokens, and developer/contributor names. No plant was renamed.
- Verified the reported Luck/Blast Protection regression against both APKs: their extended bodies were Chinese in both Releases 6 and 7. Both are now English in the candidate; Blast Protection's shorter overview card remains unchanged.

## Verification

- Verified all **201,406 Unity objects**; only the skin-challenge caption changed. Its layout/font settings and all other objects are unchanged.
- Checked all 19,061 metadata literals, 2,586 serialized UI text objects, and 282 TextAssets for the relevant missing-match patterns. Only 52 metadata literals changed; numbers, placeholders, precision, line breaks, and non-text metadata were preserved.
- All 24 automated tests passed. Android display testing is still pending.
- Release 8 APK is signed and audited. The user authorized prerelease publication on September 11; Android display testing is still pending.

Details: [September 11 feedback review](testing/RELEASE8-FEEDBACK-2026-09-11.md).
