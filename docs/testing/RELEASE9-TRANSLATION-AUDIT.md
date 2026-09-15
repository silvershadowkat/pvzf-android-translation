# Release 9 translation audit, September 15

Prepared from Release 8. APK build and signature evidence is recorded in
[RELEASE9-BUILD.json](RELEASE9-BUILD.json). Android device testing remains pending.

The user approved all 117 provisional UI/status translations, including
"higher-quality zombies". Their exact source/target pairs and upstream status
are retained in [the provisional UI tracker](release9/provisional-ui-tracker.json).
The reusable `scripts/audit_release9_fallbacks.py` comparison flags future
complete PC translations for replacement. The checked PC snapshot currently
has zero complete matches for this set. All 28 tests now pass, including a
regression proving future exact PC entries take priority for all 117 strings.

## What changed

- 26 PC-based metadata wording updates, including two exact Android suffix adapters for Blazer Snipea's Firewall descriptions. Android prefixes the name at runtime; the adapters preserve every word after the verified PC name. They stop matching if the upstream key or wording changes.
- 117 source-exact contextual UI/status fields, including a Whims of Fate result message gated on its PC name. These cover editor messages, save failures, upload status, fusion-tree counters, Brick Breaker menu labels and the Endless round label. Some status strings may only appear in logs or exceptional situations.
- Two repeated Chinese placeholder labels in the Travel Store changed to “Modifiers”, including the shadow copy. No live modifier effect was replaced by a placeholder.
- Retained the existing five-round zombie-selection instructions because the new PC summary drops the interaction steps. Corrected the generic plural “20 time” to “20 times”.
- Restored `{0}.{1}` in the note editor's “previous subdivision” message, which an older partial translation had dropped.

## Latest PC review

Checked branch `3.9`, from `708ffb136e33ccc6bb6db2fa67213170708934a9` to `d9c05a39e7c0abb09f84ddfb15582885d60a0efe`.
Three English JSON files changed; the duplicated `gods_evolved.json` was removed upstream. Its existing translations remain available in the main dictionary. No English Almanac or showcase JSON changed.

The new PC regex file has a missing comma and a trailing comma. The main strings file has eight missing commas. The exporter applies exactly ten punctuation edits, only for this commit and these two complete SHA-256 hashes, then parses every exported JSON file strictly. It does not rewrite translation values or accept arbitrary malformed JSON. See [snapshot provenance](release9/pc-snapshot-provenance.json).

There are no remaining complete usable PC matches for the current Chinese metadata. The full serialized reconciliation found no new applicable PC bundle text changes. Existing Android layout adjustments were retained; 170 pre-existing alternative English UI wordings were not blindly reapplied.

## Coverage estimate

This measures Chinese-origin text-field occurrences, not words, screenshots or percentage of gameplay. Duplicated fields count separately.

| Measure | Result |
| --- | ---: |
| Metadata literals scanned | 19,061 |
| Unity objects scanned | 201,406 |
| Serialized string fields inventoried | 35,659 |
| Translated fields in the text-resource estimate | 8,208 |
| Remaining fields requiring PC text or terminology review | 113 |
| Additional metadata fields needing runtime/internal-context confirmation | 167 |
| Resource estimate excluding uncertain metadata | 98.64% |
| Conservative resource estimate counting uncertain metadata as unfinished | 96.70% |
| Serialized player-text resource estimate alone | 99.41% |

Use **roughly 97-99% of the audited text resources** as a progress estimate, not “99% of everything visible in the game”. Historical translated diagnostics can still contribute to the metadata numerator. The 167 uncertain entries include diagnostic output, generated-code comments and shared fragments; they are not 167 confirmed untranslated UI labels.

There are still **879 raw Chinese-bearing occurrences** in the prepared resources: 766 metadata literals and 113 serialized fields. Many are intentional or internal, so this raw count is not the translation backlog.

### Categories

- **PC-dependent: 113 fields.** 83 metadata names/specialized messages and 30 serialized fields. The latter are 27 plant-specific evolution route names, two zombie flavor-text descriptions and one streaming instruction panel mixing specific projectile names with Chinese command syntax. Existing factual/version discrepancies are included in this review category rather than silently translated.
- **Safe contextual text addressed in this pass:** 117 metadata fields and two placeholder UI fields. No new plant, fusion or special modifier name was invented. The complete source/target list is in [generic review](release9/generic-reviewed.json); the PC-name-gated Whims of Fate result is in the metadata change report.
- **Runtime/internal context needed: 167 fields.** Kept isolated instead of treating every string literal as visible UI. This includes possible shared/default-name fragments where changing a literal could affect lookup or save naming. No automatic replacements were made in those fields.
- **Intentional/internal Chinese:** command and gift tokens, date/culture formats, asset/font identifiers, contributor names, hidden text, embedded developer documentation and diagnostics. These are not counted as PC translation requests.
- **Enum identifiers:** 628 Chinese members in 18 enum definitions were inventoried separately. Their runtime visibility is not established; renaming identifiers is outside this data-only pass.

The [complete remaining-field CSV](release9/remaining-cjk.csv) records every remaining occurrence with a location and category. [Coverage summary](release9/coverage-summary.json) records the denominator and scan limitations.

### Limits and existing discrepancies

- Four serialized type trees could not be decoded. Their IDs and errors are recorded in the summary. All four objects were preserved byte-for-byte. This prevents claiming a complete view of every serialized field.
- Texture pixels, downloaded/custom levels and text produced only at runtime are outside the percentage. This was a source audit, not an Android screen-by-screen playthrough.
- PC's **Whims of Fate** now says to lose 27 to 33 Luck. Android's source description says a random gain from -27 to 23. The candidate follows the user's PC-English-authority policy and records the mismatch; this audit has not established the actual gameplay formula. No gameplay value was changed.
- Counterstrike, Adaptive Strength and the previously deferred follower/leader/Bully the Weak records remain as previously reviewed because of missing or mismatched source wording. Plant names, recipes and ambiguous special effects are not filled with guesses.

## Verification and handoff

- All 28 automated tests pass, including exact-PC suffix guards, JSON-repair hash rejection, PC fallback replacement priority and contextual placeholder/line-break checks.
- All 143 changed metadata entries preserve original C# argument IDs and formats. Non-literal metadata is identical to Release 8. No English field reverted to Chinese.
- All 201,406 Unity objects were hash-checked after saving; only two expected placeholder text fields changed. All other bytes in those components, including layout settings, were retained.
- Source JSON parses strictly after the reviewed punctuation repair. DEX, native game logic and save logic are unchanged. Device rendering and gameplay tests remain pending.

### Final formatting review before publication

All 143 changed strings passed actual .NET composite formatting with numeric
sample arguments. Their source argument IDs/format specifiers are preserved,
rich-text tags balance, and no NUL, replacement character, or unexpected control
characters were introduced. All 19,061 metadata literals decode as strict UTF-8.
The 117 provisional strings match the reviewed list, and the Whims of Fate
result retains its required title delimiter and balanced `nobr` wrapper.

One inherited difference at metadata index 15731 omits the source's `{0}`
display-name field: `Remaining time: {1:F0}s`. It is byte-identical to Release 8,
and skipping an unused format argument is valid. No new argument mismatch was
introduced. Earlier display-enum metadata differences from the Chinese build
are also preserved; non-literal metadata is identical to Release 8.

The Unity bundle was rebuilt and reopened before packaging: all 201,406 objects
match Release 8 except the two expected placeholder text fields. These checks
found no new malformed text; they do not substitute for Android gameplay tests.
See [text verification](release9/text-safety-verification.json) and
[bundle verification](release9/bundle-verification.json).

Exact payload paths and hashes: [prepared payloads](release9/prepared-payloads.json). The original Release 8 payloads and APK remain intact.
