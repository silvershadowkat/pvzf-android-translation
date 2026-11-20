# Android 4.1 pre-release 5 audit

Prepared November 19, 2026 from immutable public pre-release 4 EN and ENAI APKs. The private ModDeck build is excluded from the public build inputs. Source branch: `agent/translation-4.1-prerelease5`.

## Reported almanac text

All 46 supplied screenshots were reviewed by plant ID, covering 45 distinct plants; Drone Commando appears twice. The actual public pre4 embedded LawnStrings and its managed replacement agree. All 45 reported entries are already English. Of those 45 entries, 42 still contain Chinese in the public pre3 replacement file, so pre3 is consistent with most reported gaps. This does not establish the reporter's installed version or prove user error. Old overrides loading remains a possibility, but no pre4 refresh defect was reproduced.

The full managed and embedded almanac census covers 742 plant and 238 zombie entries, plus DetailStrings. The three embedded JSON records equal their packaged managed versions. No plant/zombie name, gameplay description or flavor field in the clean pre4 plant/zombie almanacs contains CJK. Pre5 retains those files byte for byte. There are zero newly named plants and zero newly translated plant almanac descriptions in this release; pre4 work is not counted again.

## Latest Blooms

Version-aligned branch 4.1 was fetched at `fa5de17a0f6b85f187f74d6ee44c9e6635c38fc5`, fourteen English JSON files. Main remains at `f7e8b5922ac7233f16afdcc653842e3966d6a5e7`, the revision reverting accidental 4.1 changes. Almanac JSON is unchanged since the pre4 snapshot. Two English Strings files changed. Eighty usable exact-key candidates were compared; 55 updates are applied, while 25 are deferred to retain reviewed Android mechanics, complete Ascend headings, modifier-acquisition wording or missing source claims. A stray B in the Firewall wording is corrected.

## Context review

`assets/prerelease5-4.1-review.json` records 221 complete official Android source literals, SHA256 guards, English targets and provenance. They cover ordinary navigation, inventory usage and explicit basic effects. Every format argument is preserved. No plant identity, recipe or missing gameplay mechanic is inferred. Existing quality wording is reused; distinct simple/basic equipment terminology is preserved. Ambiguous specialized names remain Chinese.

Twenty-two full-match rules handle already-rendered counters, percentages and cooldowns. Original metadata strings, parser delimiters, game enum names, save keys and all 32 present protected slots remain unchanged. Prior regex priority is retained. Mixed-text announcement keys and SP Evolution variants are constructed offline as complete keys, never a live substring replacement loop. SP Evolution reuses verified SP Calamity-shroom, SP Avarice-shroom and Doom-shroom names and source recipes.

## Audit coverage and remaining limits

The scan covers all plant/zombie/detail almanac records, metadata display candidates, serialized text candidates and runtime dictionary/regex output. The actual Java translator renders 2,486 CJK-bearing candidate occurrences. Pre5 changes 229 outputs, including 227 that become entirely English. The remaining 1,283 occurrences include internal identifiers, developer diagnostics, Unicode/parser tables, editor data and unresolved specialized names/effects. They are not 1,283 missing player-facing almanac descriptions. Candidate scanning does not establish that every serialized string is visible during gameplay or that every raster graphic has been translated.

No gameplay, animation, rendering, audio, AI-model or recognition-lifecycle edits are made. No speculative change is made to the reported Zomboni Fog issue or almanac loading.

## Verification

- 79 Python checks passed.
- Real Java translator: 363 new review/format/mixed-text fixtures and 88 existing screenshot/regression fixtures passed.
- Translation parity: 17,625 inputs passed against the version-aligned source baseline.
- Metadata/almanac restoration: 4 metadata and 12 almanac checks per variant, across internal/external roots, named/default profiles and repeated old-backup restoration, preserving player/config fixtures.
- Ten process startup checks passed, including restored Unity entry and excluding the isolated AI process.
- Signed APK audits allow only AndroidManifest.xml, assets/english/manifest.json and assets/english/translations.json to differ. Every other uncompressed entry and its compression method must match the corresponding clean public pre4 base. DEX, native libraries, Unity bundle, metadata, media and AI assets are unchanged.
- Release signatures and 16 KiB ZIP alignment verify. No phone is operated or installed for this task.

The separate personal ENAI build is derived only after the clean ENAI pre5 build is complete and is kept local. It is never attached to the public release.
