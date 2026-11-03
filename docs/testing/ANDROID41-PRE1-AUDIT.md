# Android 4.1 prerelease 1 candidate audit

November 3, 2026. Local branch `agent/translation-4.1`, based on published prerelease 4 source `9345d21`. Unpublished candidate; final binary identity and checks are in `ANDROID41-PRE1-BUILD.json`.

## Inputs and scope

- One EN APK, version code `4100100`, `com.LanPiaoPiao.PlantsVsZombiesEN`.
- Official Android `pvzrh4.1.apk`: 620,177,229 bytes, SHA-256 `6272551fd2573bd3e342acf1a214aa0ee6d44833260babe600e27301ef9a6390`.
- Blooms 4.1 snapshot `5a415154d81243771d75e2dd90ae14ae79d52632`, compared with actual official PC 4.1 source where needed.
- No Lite translations, offline recognizer model, ONNX library, recognition service/warmup or old mode blocker is shipped.

## Translations

The base port changes 275 TextAssets and 1,837 serialized UI strings. Metadata changes are source-aligned against current 4.1. Dynamic cards, eligibility, TMP markup and downloaded level labels use complete exact/bounded display translation. Mixed-name aliases are prepared offline, without unrestricted runtime substring replacement. Prior exact dictionary keys are retained; internal identifiers remain protected.

Blooms' Dumps omit four new records present in the actual PC 4.1 game and English data. `apply_41_review.py` requires matching Android/PC source records, IDs absent from the older Dumps and matching field hashes. This safely imports **Artsy Sunflower, Ball Cactus, SP Calamity-shroom and SP Avarice-shroom**. Existing records retain normal stale-source guards.

Context Aware AI uses verified terms for clear prose and instructions: Artsy Sunflower's painting instructions, new plant flavor text, the SP description introductions, shop/save/editor prompts and recognition messages. Actual source values win over preliminary changelogs, including Artsy's `25 x 2 / 20s`. Unverified specialized names remain Chinese, including one proper name in Artsy's flavor text.

Blooms' announcement still describes 4.0.5. The actual Android 4.1 announcement is translated separately with a complete source hash guard, verified names and retained unverified names.

Reported screenshot gaps targeted:

| Area | Change |
| --- | --- |
| Squash Pumpkin | Ascend title/body, ownership/speed conditions and one Ascend per plant |
| Apocalypse Railgun | Disintegration title and mixed laser effect, including the passive prefix |
| Melancholy Commando | Penetration title and projectile hit-count fragments |
| Toxicity | Eligibility uses the established Odyssey modifier name |
| Supremacy-shroom | Impact title and original/mixed-name effect spans |
| Dragonbreath Torcher | Firecracker title/body, Bamboombs wording; unrelated discovery banner removed from the lookup key |

The real Java translator passes 18 screenshot/regression fixtures, including tags, counters and mixed text. The census retains CJK in 1,626 of 21,142 metadata candidates, including internal keys, diagnostics and unverified content. This does not establish complete English coverage.

Approved diary/credits artwork and 48 legacy textures transfer only where original source pixels match. Current PC English textures and 15 reviewed presentation objects are applied with guards. Font transplants keep Chinese fallback. Old APK resources are not blindly reused.

## Music

The former bridge muted Unity music and used up to two independent Android MediaPlayers. Errors and a 15-second timeout could fall back to Original. Disassembly confirms that `MusicUpdater.DayMusicUpdate` changes the game's source times after initial setup; the external players did not follow those later changes. This is a concrete timing mismatch. No tester log proves the cause of their individual fallback event.

The replacement uses normalized streaming AudioClips on the game's two music sources. Unity retains playback times, drum synchronization, fades, loops and volume. There are no extra players, muted duplicate songs, per-frame music polling or startup audio extraction. SFX assignments take only pointer comparisons; a bounded cache avoids repeated resource loads. Soundtrack selection is fixed for the session, with a saved choice and restart notice.

44 banks are appended: 27 Original and 17 Blooms. Original audio objects and payload bytes remain unchanged; ResourceManager adds the new paths. Unreplaced songs use normalized Original where available. A missing profile resource retains the official clip and logs the event once per cached track. This intentional resource fallback differs from the removed player timeout fallback.

Constant gain targets -18 LUFS and a -2 dB true-peak ceiling before encoding. Paired stems share gain. No compression, tempo change, trim or padding is applied. Differing source stem lengths are preserved; sparse/silent preludes are not amplified into noise. Peak-limited tracks may remain quieter.

All 44 bank headers/sample counts pass. Six menu/day banks decode. Post-encode measurements:

| Profile / track | LUFS | True peak dB |
| --- | ---: | ---: |
| Original menu | -17.98 | -3.04 |
| Blooms menu | -17.97 | -2.91 |
| Original day pair | -17.98 | -2.29 |
| Blooms day pair | -17.98 | -2.14 |

Long-session listening, wave transitions and lower-memory performance still need play testing.

## Controls and recognition

- Screen and Music are separate controls in the original settings column. Spacing is reduced within its original height; canvas positions and collider state are refreshed.
- The official screen handler still hardcodes 1920x1080. The replacement derives bounded 16:9 rendering dimensions from the current display, captures exact default dimensions/fullscreen state, and restores them on reversal. Rejected changes time out and roll back. No automatic startup stretch.
- Projectile Info retains the existing feature, health-control visibility and customizable positioning.
- Official 4.1 enables Magic Plantbrush on mobile and uses remote recognition. Endpoint credentials are omitted from audit output. Our old blocker and offline hooks are removed. Internet and official service availability are required.

## Update safety and checks

Only the known metadata override and three named almanac JSON files are refreshed. Player data, settings, extra save slots and unknown files remain. The display dictionary loads directly from the APK; stale private copies are ignored. No broad wipe or cross-package import.

- 74 Python tests pass.
- 18 Java display fixtures and regex-prefix/cache checks pass.
- Managed files: 8 checks preserve 11 save/settings/unknown fixtures.
- Actual signed APK pair: 4 metadata and 12 almanac restore cases pass across two storage roots, multiple profiles and repeated old-backup restoration.
- ARM64/ARMv7 runtime builds pass; ARM64 screen-plan test runs on Nova.
- Signature v1/v2/v3, original certificate, 16 KB alignment, ZIP/duplicate entries, manifest/version, protected metadata, allowlisted APK changes and unchanged official native libraries pass. No offline recognizer payload.
- Nova reaches the main menu and runtime hooks register. Its 4:3 main-menu layout limits access to the separate Settings screen; no special layout workaround was added. Full phone/tablet control and music tests remain with the maintainer.

Detailed local evidence is in task `work/upgrade41/`: source inventories/disassembly, review reports, payload census, audio normalization/decode results, build logs and device captures. Extracted game binaries and credentials are not repository deliverables. The APK remains local pending maintainer testing; see the draft release notes for the short checklist and save paths.
