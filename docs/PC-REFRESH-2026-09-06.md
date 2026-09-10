# PC translation refresh — 2026-09-06

The main Android project is ready for the next tester-feedback batch. No APK,
release, tag, or remote commit was created or pushed. The cheats project has
not been modified.

## Baseline and source

- Main checkout: `C:\Users\plim\Documents\Codex\Projects\Plants-Vs-Zombies-Fusion\source\pvzf-android-translation`
- Working branch: `agent/translation-3.9-tester-fixes`.
- Exact latest release: `v3.9-release-6`, commit `d0b02fa751ebaf1e376a98c64bfeee91c7d49b72`.
- The previously checked-out local commit `2d8e933` has the same tree as the release tag. The existing fertilizer feedback note was preserved when creating the new branch.
- PC checkout: `translation-data/PVZF-Translation`, branch `3.9`, clean at `5d3ca86876cafc38b70c4a8aa87f6f5cf54266f2`.
- Prior release PC source: `c2e8f962cb9974c3214d0db95fe98fea0634a2da`.
- Checked upstream branches; `3.9` remains the matching game-version source. Its tip is dated September 4; `main` is dated September 2. This refresh imports the matching 3.9 branch, not translations from other game versions.
- Machine-readable source pin: `docs/pc-translation-source.json`.

## Imported PC changes

Only two English input files changed since release 6:

1. `Almanac/LawnStringsTranslate.json`: plant ID 1425 changes Shooty-shroom to Speedy-shroom, including the corresponding name in its flavor text and description. Upstream commit `b6736ed8`.
2. `Almanac/DetailStringsTranslate.json`: the Second Copy explanation now consistently says Second Copy instead of Carbon Copy. Upstream commit `f526977a`.

These are four changed fields. The English exact/regex dictionaries, modifiers,
tips, zombie Almanac, changelog, textures, audio, and matching source dumps did
not change on this branch. No additional Chinese or English translation was
generated. Incomplete PC translations remain governed by the existing
PC-or-original-Chinese policy.

## Validation and prepared data

- Verified the official Android 3.9 APK SHA-256 `a3adf7d8742d537f167217867e943e1b9faeaa361a868e33e388a373671320b0`.
- Verified the local release 6 APK SHA-256 `9fb624cc74a896ad67bb139de4be326f10b26f64ef0fc943f47f590f90a572a3`.
- All 13 current English JSON inputs parse successfully.
- All six existing translation-safety regression tests pass.
- Rebuilt the two affected TextAssets from the official Android source using the existing Android adapters and matching PC source dump.
- Confirmed the old-PC rebuild matches the entire corresponding release 6 JSON trees, not just the four changed fields.
- Confirmed the refreshed merge changes exactly four fields and retains all 682 plant records and 40 Mechanics records. Android size-tag removal and punctuation normalization remain in effect.
- Prepared JSON is staged locally under the current task's `work/pc-refresh/`; no Unity bundle or APK was rebuilt. Future builds consume the updated ignored PC checkout and must retain the release 6 font, layout, audio, and resource-packaging fixes.

The refresh report in the current task's `outputs/pc-refresh-report.json`
contains the exact old/new fields, merge counts, and input hashes.

## Earlier assisted wording identified

The existing provenance auditor explicitly describes the Android fallback table
as Codex-assisted. Its 539 entries currently classify as 513 fallbacks without
a PC exact match, 18 Android-required overrides, four matching PC values, and
four differing values where PC English takes priority. These table counts do
not establish which strings appear on a particular game screen.

Release 6's metadata report records 339 literal occurrences using the Android
confirmed mapping method. The review inventory lists every occurrence with its
source, shipped English, and available mapping provenance. The separate 12-entry
reviewed 3.9 UI allowlist is also included. The 677 occurrences inherited from
Update 6 have mixed provenance and are not automatically labeled AI-generated.
This inventory does not establish complete authorship of Unity UI, enum labels,
baked textures, or inherited references. Nothing was reverted.

## Local release setup and next work

The existing signing key and properties file are present under
`C:\Users\plim\Documents\Codex\Secrets\Plants-Vs-Zombies-Fusion`.
Neither was opened for its secret contents, changed, copied, or used to sign.
Release 6's recorded public certificate fingerprint is
`1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6`.
Official inputs and the release 6 APK/reports are present under the project.
Old dated build paths in historical reports no longer exist; use the current
project paths above. The project's declared Python dependencies have been
restored in its local `.venv`. A restricted pip cache caused an initial stall;
installing without cache with temporary files in this workspace resolved it.

Next: collect the user's tester findings, apply corrections to this main branch,
then rebuild and run the required APK/device checks. Preserve the parked
fertilizer terminology question in `docs/NEXT-RELEASE.md`; do not rename it
without matching the specific upstream source and UI context. Port to the
cheats variant only after the main changes are finished and the user is ready.
No task-owned installer, build, Python worker, or server remains running after
the final process audit.
