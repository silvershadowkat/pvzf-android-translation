# Sea-greed Zombox recipe wording — 2026-09-09

Status: investigated; no translation, recipe, gameplay, or candidate payload changed.

## Tester request

The screenshot shows Sea-greed Zombox (plant ID 5003), with the conversion
recipe “Plant Giftbox <-> Zombie Giftbox”. The proposed clarification adds
Kelptain Goldbear to both sides of that line.

## Source findings

Checked the latest remote PC 3.9 commit
`67a6767ba332d0793a2752dffa59543f6e0448e1`, the local September 6 pin
`5d3ca86876cafc38b70c4a8aa87f6f5cf54266f2`, and release 6's PC pin
`c2e8f962cb9974c3214d0db95fe98fea0634a2da`.

- PC plant **941** is **Kelptain Goldbeard**, including the final “d”.
- PC plant **5003** is **Sea-greed Zombox**. Its description identifies it as a subspecies of plant 941.
- PC's displayed conversion recipe is **Plant Giftbox <-> Zombie Giftbox**.
- These records are unchanged across all three checked snapshots.
- The cached TextAssets extracted from the verified release 6 APK use these same names and recipe, allowing the existing Android removal of PC-only size tags.
- The official Android Chinese description itself uses the same two-giftbox conversion shorthand. We did not omit a Kelptain ingredient from that line.
- PC describes a chance to obtain the respective plant's seed packet from the corresponding giftbox on an empty tile under its second Odyssey modifier. That conditional card-spawn description is separate from the displayed conversion recipe and must not be presented as an unconditional fusion rule.

PC record source:
[LawnStringsTranslate.json at the checked commit](https://github.com/Teyliu/PVZF-Translation/blob/67a6767ba332d0793a2752dffa59543f6e0448e1/PvZ_Fusion_Translator/Localization/English/Almanac/LawnStringsTranslate.json).

The PC recipe line was introduced in commit `0747001d` on August 18, before
release 6. This finding is not a new plant-name correction.

## Decision

The request reasonably highlights unclear instructions for new players.
However, its expanded formula is not the PC wording and does not explicitly
identify the resulting plant/form. The available text alone does not establish
the full application order or reverse conversion mechanics.

Keep the existing upstream recipe. Confirm actual conversion steps through
matching game code or a reproducible in-game demonstration before judging an
expanded formula. Under the user's PC-only policy, obtain a completed upstream
clarification before replacing this wording. This field is already translated;
do not label it “not translated yet”.

Only fetched the remote PC branch for inspection; did not advance the local
build-source checkout or incorporate unrelated September 8–9 changes.

The running next-release notes record this once in a dedicated acknowledgement
of the tester request, not as a completed fix. At the user's request, that note
explains that the goal is to match the PC project as closely as possible and
that the recipe wording is retained unless PC updates its explanation.
No APK, release, or cheats-version change was made.
