# English parity audit and local corrections — 2026-09-06

Status: unpublished local text corrections from release 6. No APK packaged,
signed, installed, or published. No remote commits or tags pushed. Cheats
repository unchanged. Device stability is not yet established.

## User requirements

- Use completed PC community English exactly, allowing necessary Android formatting.
- For each tester finding, locate the corresponding PC source/ID/field. If it has no completed translation, tell the user the PC project has not translated it yet. Do not invent English, even for generic UI.
- Preserve previously shipped assisted/historical wording without a usable PC replacement; identify it instead of automatically reverting it.
- The earlier release had crashes. Keep edits narrowly scoped, validate data and object identity, preserve fonts/layout/audio/gameplay data, and require device retesting before claiming stability.
- Defer porting to the cheats variant until the main corrections are complete.

## Pinned state

- Android release: `v3.9-release-6`, commit `d0b02fa751ebaf1e376a98c64bfeee91c7d49b72`.
- Main working branch: `agent/translation-3.9-tester-fixes`.
- Main repo: `C:\Users\plim\Documents\Codex\Projects\Plants-Vs-Zombies-Fusion\source\pvzf-android-translation`.
- PC branch: `3.9`, commit `5d3ca86876cafc38b70c4a8aa87f6f5cf54266f2`; remote branch tip rechecked during this pass.
- Existing fertilizer feedback in `docs/NEXT-RELEASE.md` retained.

## Audit coverage and confirmed fixes

Compared 682 plant records, 226 zombie records, 40 Mechanics entries, 282
TextAssets, serialized TMP text candidates, and all 19,061 metadata literals
against current PC data and the clean official Android source. Original source
strings and stable record IDs determine matches, not English-name guesses.

Applied to local candidate payloads:

- Speedy-shroom's current PC name and two descriptive fields; Second Copy explanation.
- Two Death Star descriptions that the repeated-prose heuristic wrongly rejected. Their official source bodies share a prefix; one adds a recipe line. Unrelated duplicated zombie prose remains rejected as placeholder text.
- 157 level tips whose exact official source matches the PC source dump and has completed PC English.
- Four talent-name corrections (`Sunny Day I`, `Sunny Day II`, `Sunny Day III`, `Solar Bonus`) and an unlock description using Glacier-shroom.
- The confirmed Doomspike-shroom → Glacier-shroom challenge label, preserving its original size markup and line break.
- 14 metadata literal corrections, including the same challenge name, current PC runtime wording, and correct price/item placeholder ordering in the out-of-stock prompt.

The verified bundle changes 168 text fields in 160 TextAssets and one TMP
caption. The metadata candidate has exactly 14 changed literal occurrences
relative to release 6 and **zero reversions** to official Chinese.

## Changes deliberately held for context

- 172 broader UI wording candidates are listed in `pc-reconciliation-verified.json`. They have possible complete PC wording, but are not applied by default. Review the screen and interaction before enabling `--include-ui-candidates`.
- 13 existing Android context/layout exceptions are retained, including Close versus Disabled, the compact skin caption, numeric difficulty context, approved LETS ROCK lettering, and a points counter that must not use the PC currency regex.
- The Quick Hands I talent label is hidden in release 6 with repeated `<size=0>` markup. Its visibility and text are retained until context is understood.
- Missing/placeholder PC fields remain unchanged. Some historical Android English has no confirmed current PC match; the previous provenance inventory remains available. An absent exact dictionary key alone is not proof of missing PC English—inspect structured records and complete applicable regexes.
- Artwork was compared read-only against all 60 PC PNGs: 47 compatible textures have nonzero decoded-pixel differences, 10 lack a unique compatible Android target, and 3 are intentional Android art exceptions. Compression, alpha pixels, and adaptation can cause differences; these counts do not establish incorrect English. No artwork was changed. Visual checks can use tester screenshots.

## Pipeline changes and verification

`build_metadata_translation.py` now checks complete current PC exact/regex
translations before historical fallbacks. Regexes must cover the whole source;
partial damage/price matches cannot replace a full description. Numeric stat
bonuses cannot acquire the broad PC fusion-recipe boilerplate. Previously
shipped fields can be preserved with `--preserve-release-report`, which checks
the same official-input hash and source/index identity and records provenance.

`reconcile_pc_english.py` is a final, source-aligned text pass after Android
polishing. It consults original Chinese keys even when a candidate is already
English, preserves existing fields when PC English is unavailable, leaves
hidden text hidden, and defaults to deferring broader UI candidates. It changes
only serialized text bytes, then reopens and verifies the saved bundle.

- All 15 focused regression tests pass.
- Metadata literal counts and round trips pass.
- All 201,406 Unity objects retain their identities. Every untouched object's bytes match release 6, and every changed object exactly matches the intended replacement bytes. Font/fallback objects, audio, textures, layout fields, and other non-text object data are unchanged.
- All three final Almanacs exactly match the current source-aligned PC merge after Android formatting and placeholder policy.
- All JSON assets preserve keys, list lengths, field types, and every non-string value.
- Hidden talent markup remains intact.

Two intermediate verification runs were rejected, and no APK was made from
them. Inspection of UnityPy identified a verifier error: `get_raw_data()` reads
the original stream even after `set_raw_data()`; saved replacements are held in
`obj.data`. The verifier now hashes the replacement buffer and validates the
reopened file. The final narrowed candidate passes; rejected intermediate
results are not release artifacts.

These structural checks do not prove freedom from runtime crashes. Before any
release, package only after the tester corrections are complete, run APK and
signature/comparative checks, and perform device tests of Almanac navigation,
the affected challenge/talent/tip screens, shop prompts, saves, and gameplay.
Specifically recheck Penny-shroom/Cattail Girl/SP Phoenix navigation and the
release 6 fallback-font regression routes. Do not claim stable based only on
offline audits.

## Local continuation files

The corrected payloads are under this task's `work/english-audit/`:

- `data-pc-reconciled.unity3d`: verified final text-only bundle candidate.
- `global-metadata.dat`: verified metadata candidate rebuilt from clean official metadata.
- `metadata-report.json`: generated metadata provenance and validation report.

Current task root:
`C:\Users\plim\Documents\Codex\2026-09-06\https-github-com-silvershadowkat-pvzf-android`.

Reports in `outputs/`: `pc-reconciliation-verified.json`,
`metadata-parity-corrections.json`, `final-text-validation.json`,
`english-parity-audit.json`, and `pc-art-parity.json`. The initial raw parity
audit is a discovery inventory and includes formatting differences and rejected
partial-regex candidates; it is not a list of approved edits. The older
`pc-reconciliation-plan.json` is superseded by the verified, narrowed report.

The signing key/properties remain in the existing Secrets directory and were
not used. No task-owned installer, build, Python worker, emulator, or server is
intended to remain running; complete the final process audit before handoff.
