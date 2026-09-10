# Showcase, Almanac and gameplay reports — September 9, 2026

Local, unpublished candidate. PC authority: e24586aaf9feb85eae6fc30af3460237778558ff. User explicitly chose to retain PC English while documenting known discrepancies; do not silently substitute guessed mechanics or corrected English derived from Chinese.

## All showcase instructions

Checked all 174 bundled level-tip records, including every reported Silver Ice-shroom, Thorn-nut, Pea-shroom/welcome, Beamshooter, Star-nut, Doom Pea and Rush-shroom panel. All gameplay instructions are English in the final candidate. Most reported misses were covered by the earlier 157-tip import; the broader audit found one additional case, Melon Morph (level1314).

PC’s Melon Morph instructions are complete English but its Special Thanks section retains contributor names in Chinese. A whole-field hash exception now accepts that exact reviewed PC text without romanizing names or allowing arbitrary mixed-language ability descriptions. Total new English tip fields since Release 6: 158. This exception applies in both PC metadata matching and Unity text loading.

Open Fire/Deadeye announcement text and the Chinese cards in the new screenshots use the same complete PC modifier records as the Almanac; they are covered by the modifier import.

The separate Level List screenshot shows local/online custom-level names with English controls. The supplied titles were not found as bundled title fields or compiled display literals in the inspected payloads. They appear to come from loaded level files; the screenshot alone does not supply those files. Do not invent titles or rewrite level IDs, filenames, or saved user content. The screenshot’s source and loaded files remain unverified.

## Almanac reports

- **Death Star 1277:** confirmed Chinese in Release 6, already corrected to the full source-aligned PC description in the candidate. The related Death Star entry was covered in the same prior fix.
- **Icicle-shroom 1035:** Release 6, candidate and current PC agree on 20/1.5s. Original Android and PC Chinese both say 20/2.25s. PC also omits some Chinese trait/recipe text. This is an upstream text discrepancy, not an Android-only mistranslation. Keep PC English for now per the user’s latest direction; actual attack timing was not measured.
- **Ultra Mecha-nut 310:** the follow-up image identifies the plant but not its disputed description. Its billion-HP display is not by itself contradictory: the description allows HP to exceed toughness. Current Android English matches PC, including its healing sentence. Chinese refers to healing from non-坚实 plants multiplied by ten; PC instead mentions metal objects and a comparison with Giga Mecha-nut. Retain PC wording and flag this upstream discrepancy. Do not infer a measured cap or healing rule from the screenshot. The note’s superscript 2 is not proven to be a separate plant ID.
- A complete source-aligned latest-PC Almanac comparison found three additional recipe fields: Cherrybomber Drone 939 spacing, Habanero Weeper 990’s ×3 term, and SP Phoenix Drone 5000’s conversion wording (PC no longer includes the old promotion line there). Imported PC content; no gameplay recipes or IDs were changed.

## Formatting and safety

The newer PC SP Phoenix Drone cost field contained an extra closing color tag. Two previously imported showcase tips also had malformed styles: crossed color/size tags in Grapple Kelp (1395) and orphan size closings in Hoverleaf (1204). These are repaired while retaining visible PC wording, intended style scopes, and existing Android layout choices. Existing unclosed styles outside the reviewed fields are not broadly rewritten.

The saved bundle is reopened and all 201,406 objects are checked against expected bytes. The broader verification checks every changed field since Release 6 for paired-style errors, all 274 JSON assets for identical keys/IDs/types/non-string values, all three Almanacs against the approved PC merge, and all 140 changed metadata literals for unchanged runtime placeholders. These checks reduce formatting risk; they do not prove Android crash freedom. Device checks remain required before release.

## Stuck Odyssey round and performance feedback

The supplied Abyssal Garg Route Round 16 screenshot shows Zombie(s): 2 after the visible wave bar is complete. It cannot identify the two counted entities or prove why the round fails to end. No matching save, logs, exact APK version or device model was available. No reproducible gameplay fix is claimed and no wave-completion bypass is added.

Compared Release 6 with official Chinese 3.9: classes.dex and all eight native libraries, including both libil2cpp.so ABIs, are byte-identical. Recent edits also leave gameplay/non-string data unchanged. This rules out a direct native-game-code patch by this translation port; it does not rule out an asset/UI issue or establish an upstream root cause. Public source checks did not yield a verifiable matching issue; an indexed PC lag issue link was unavailable and is not treated as evidence for Android.

The game itself warns that the projectile-damage display has a major performance cost and requires a level restart after changing its setting. Disabling that optional display is a supported first troubleshooting step. Doom-shroom and Sun visual-effect toggles also exist; their performance effect was not measured. No FPS increase, optimization, or crash fix is claimed. Profiling a repeatable affected save on the reported device is needed before changing engine behavior.

Evidence: task outputs `showcase-almanac-audit.json`, `showcase-bundle-verification.json`, `recent-changes-safety.json`, and `custom-level-performance-text-check.json`. No APK was packaged, signed, pushed or released.
