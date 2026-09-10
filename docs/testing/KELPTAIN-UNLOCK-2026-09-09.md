# Kelptain / Sea-greed unlock card and A.L.E.C. — September 9

## Findings

The tester's Odyssey/Purgatory unlock screenshot uses historical fallback
names "Ultimate Greedy Kelp" and "Ultimate Greedy Boxgrass". These differ from
PC's **Kelptain Goldbeard (941)** and **Sea-greed Zombox (5003)**. The Almanac
names in release 6 already match PC, including the final d in Goldbeard.

The actual release-6 APK and the pre-correction candidate leave metadata
literal **1800** (this entire unlock card) in original Chinese. The old English
fallback is present in source code but was not enabled for this 3.9 literal.
Thus the screenshot does not establish that this incorrect English shipped
in release 6; the real current gap was an untranslated unlock card. Do not
attribute the tester's state to imported saves without runtime evidence.

Latest PC commit `67a6767ba332d0793a2752dffa59543f6e0448e1` has a complete
translation in `travel_buffs.json`, `unlocks.14`, whose Chinese source matches
the whole Android literal exactly:

> Unlock Kelptain Goldbeard: Twin Marigold > Hydra Kelp
> and its Subspecies Sea-greed Zombox
> Conversion: Plant Giftbox <-> Zombie Giftbox

Imported that complete PC string without creating names, translating gameplay
prose independently, or expanding the conversion formula. The existing Almanac
recipe remains unchanged. Historical fallback mappings were not automatically
deleted or rewritten.

**A.L.E.C. (309)** also matches PC and release 6. PC's `info` field explicitly
expands it to **Arsenalized Long-range Elite Chompzilla** and describes the
heavy machine gun and sniper rifle shown on the plant. This is an intentional
PC name, not a misplaced Android name; no correction was made to that entry.

## Implementation and verification

The full latest PC travel-buff file is currently invalid JSON because of an
unrelated missing comma. The exact individual `unlocks.14` record was decoded
for this bounded import, with the valid source dump and matching literal ID
checked. Upstream was not edited and production JSON parsing was not relaxed.

`docs/pc-reviewed-records.json` stores the verbatim source/target pair, section,
ID, file paths and upstream commit. The metadata builder now accepts the
explicit `--pc-records` argument and records its hash/commit in the report.
Only complete English and unchanged runtime placeholders are accepted;
complete PC mappings in the normal source files retain priority.

Rebuilt from clean official 3.9 metadata while preserving release 6 and earlier
candidate corrections. Exactly **one of 19,061 literals changed: index 1800**.
Its replacement exactly equals the PC record. All other literals and all
non-literal metadata bytes (apart from text-table bookkeeping) are unchanged.
The four counter-label fixes remain present. The Unity bundle was not edited.
All **16 regression tests pass**, including rejection of incomplete imported
records and altered placeholder precision/indices. Whitespace checks pass.

Current metadata candidate/report remain at task
`work/english-audit/global-metadata.dat` and `metadata-report.json`. This is
now 17 metadata literal corrections relative to release 6 (14 initial parity,
two counter blocks, one unlock card). The earlier reports are historical
snapshots; use `outputs/kelptain-unlock-verification.json` for this delta.
Before/after data and bounded build log are in `work/kelptain-unlock/`.

Future rebuilds must pass `--pc-records docs/pc-reviewed-records.json` until
the full PC refresh supplies these exact records. Four modifier translations
identified in the separate screenshot check are still pending; this manifest
does not import them. Device testing of unlock-card fit and normal interaction
remains pending. No APK, signature, release, or cheats-version change was made.

Both findings appear once in the running notes: the shared unlock card as a
prepared correction, and A.L.E.C. as reviewed and intentionally unchanged.
Task-owned build/test processes exited; unrelated processes were not stopped.
