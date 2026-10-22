# Prerelease 3 r16: generated editor help

Local test build, not published. Completes the additional editor labels found while checking the r13 Creator Guide on the S26. The user approved the main guide's wording. These additions use Context Aware AI and the game's existing English terminology, as disclosed in the draft release notes.

## What changed

- Added 63 reviewed source literals for Node Help headings, input/output descriptions, template controls, connection checks, and editor validation messages. Each entry records its exact Android 4.0.5 metadata index and Chinese source; the apply script rejects a changed source.
- Added 12 anchored, complete-display patterns for generated status messages, variable/template counts, connected ports, entered values, port types, and troubleshooting node IDs. Captured values and rich-text tags are retained.
- Added individual lines from reviewed help blocks because the game combines these blocks into longer TMP labels. A whole-block match alone misses these generated panels.
- Corrected the Timed Sun Tutorial to say **On Toggle On**, matching the existing port label. This is a wording correction, not a node/port rename.
- The tool popup's Close label now receives the same correction as the Creator Guide. This native check requires the live event editor's `toolWindow` subtree and a `TheButton` ancestor (the actual editor button class). It does not globally change Disabled or the shared Chinese literal used by settings toggles.

## Boundaries

The original game native libraries and metadata are unchanged from r13. The added runtime library performs the scoped Close-label check through named IL2CPP classes, fields and methods. It does not use version-specific memory offsets or change event handlers.

Translation runs only while rendering. Existing input-field exclusions remain in place. User template names, node IDs, port identifiers, object binding names, entered values, save files and the managed-file refresh policy are not rewritten. Only known translation files are refreshed during updates; unknown files are preserved.

The three intentional Chinese technical identifiers documented in [the guide review](ANDROID405-PRE3-GUIDE.md) remain literal. This review does not claim every possible editor operation or all player-facing Chinese in the game has been tested.

## Reproduction and evidence

- `assets/creator-editor-ui-4.0.5.json` contains the source-indexed additions and full-display patterns.
- `scripts/translate_creator_guide_405.py --work <pre3>` applies these alongside the guide. It reuses an earlier bundle object comparison only when the English content, frozen baseline and resulting bundle hashes all match the recorded verification.
- `scripts/check_creator_editor_405.py --work <pre3> --jdk <jdk> --sdk <sdk>` exercises the actual Java translator, including formatted multi-section help, generated statuses and unchanged technical identifiers. All 948 fixtures passed before packaging.
- `work/upgrade405/pre3/editor-r14` holds fixture results, the retained r13 report, build/device evidence and a backup of the scratch editor draft created during this audit. These are local evidence, not user data to distribute.

Build and device results are recorded in the local release handoff. Quick check: Recommended Levels > Super Custom Levels > Level Event > Add Rule Template. Inspect the template menu, then select a node and open Node Help. Scroll to the bottom. Check headings, port descriptions and Close. Reading help does not save a level.

## r16 package and device result

Both ABI builds, package signing/alignment/manifest, protected metadata and managed-refresh checks passed. r16 (4050331) was installed with `-r` over r15, without clearing data. All eleven readable nontranslation files were byte-identical during installation and after startup, including both survival saves, player/garden data and two audit-created editor drafts. Existing plant-name and metadata overrides matched the APK. Runtime initialized.

Device screenshots in `editor-r16` verify English template menus, More Tools, Node Help and its bottom section, status/type labels and working Close buttons. The final native check uses `TheButton`, confirmed from the game's editor prefab creation. The earlier Button/UIButton assumptions were corrected before final verification. r16 does not alter the r15 translation payload, only the added runtime libraries and version/manifest entries.

Three scratch drafts created by this audit were backed up and individually removed after exiting the editor. Exact remote hashes matched the backups before deletion. Both survival saves, player and garden data remained unchanged. No whole custom level was saved and no user save was deleted or restored. See `editor-r16/scratch-cleanup.json`. Private preferences are outside the shell-readable hash check. The editable default template name remains untouched, as do technical IDs.
