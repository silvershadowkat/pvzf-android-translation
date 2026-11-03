# Android 4.1 prerelease 1 candidate audit

November 3, 2026. Local branch `agent/translation-4.1`, based on published prerelease 4 source `9345d21`. Unpublished candidate; final binary identity and checks are in `ANDROID41-PRE1-BUILD.json`.

## S26 corrective test revision

The first candidate's settings hook rejected the actual hierarchy: this column uses six manually positioned controls and a disabled GridLayoutGroup, rather than a VerticalLayoutGroup. That left the original fixed-resolution button active and omitted Music. The correction derives seven anchored positions within the authored first/last bounds, disables the original handler and refreshes button origins/colliders. S26 r2/r3 screenshots show both selectors. Repeated S26 logs confirm Stretch applies 1920x1080 and Default restores the captured 2340x1080. Paused-level Settings, the music notice and Back-to-Pause navigation also pass on S26. Tablet testing remains outstanding.

Eighteen S26 screenshots identify Odyssey: Evolved, Super Stacking and Magic Plantbrush gaps. The correction bakes 85 reviewed full templates/instructions before formatting, avoiding runtime work on frequent shop stats and counters. It adds 46 short display labels and 89 individually guarded static TMP fields. C# formatting succeeds for 72 templates; 23 real Java display fixtures and 74 Python tests pass. Current specialized terms without verified English remain Chinese.

The maintainer reports smooth Chinese 4.1 playback in the same modes and audible recurring cuts in EN on Nova. Local diagnostics measured 94, 101 and 99 music seek requests per ten seconds during a basic daytime tutorial while frame counts remained near 120 FPS without 50 ms frames. Disassembly shows that DayMusicUpdate checks synchronization throughout each second where floor(Time.time) modulo 10 is zero. Unity documents packet-based timing limitations for compressed audio. These observations identify a repeated seek problem; they do not establish every reported slowdown's cause.

At the maintainer's request, the corrected candidate uses **DecompressOnLoad**, matching the original game's playback load type. Disk encoding stays Vorbis, as in the original; playback uses decoded PCM. Background loading avoids decode work on the render loop. Both the managed per-clip unload wrapper and its native binding are stripped in 4.1. The correction releases inactive profile handles, then requests Unity's available public asynchronous unused-asset cleanup. This runs only after an actual track retirement, keeps the active pair referenced and never overlaps jobs. It does not poll during ordinary frames or touch files. Transient PCM release follows completion of engine cleanup, rather than being assumed immediate.

All 44 added loading flags change under a guarded object diff; original clips, waveforms and resource bytes are unchanged. Seek/frame diagnostics are optional local-build instrumentation and are excluded from normal APKs. The streaming implementation described below is historical and superseded by this correction; its normalization measurements remain valid for the unchanged audio banks.

## Follow-up screenshots, local r3

The upgrade omitted the existing Android almanac size-tag normalization. The focused correction reuses that helper, removes 2,874 PC size tags from LawnStrings/ZombieStrings, and exports the corrected managed JSON so restored old overrides refresh too. All other serialized objects stay unchanged outside the explicit allowlist. Future text builds normalize these fields; payload export rejects leftover overrides.

Seven further S26 screenshots exposed Super Stacking prefab text as well as metadata. Another 185 source-guarded static fields cover inventory, shop tabs, research headings/costs, recycling, checkpoints, emergency support and the full instructions page. Full formatted counters are baked before rendering. Complete known rarity/item/plant combinations reuse established terms. New specialized stage reward names without a verified Blooms counterpart remain Chinese. No invented plant or modifier names.

The PC fusion-recipe regex was applied globally and incorrectly matched research text ending in +1. It now requires both captured ingredients to be in the source-aligned plant/zombie name inventory. Research/modifier bonuses fail closed; legitimate recipes still translate, including recipes containing real new plants whose names are not yet translated. No unrestricted substring replacement.

Soundtrack changes remain restart-based: background decode and paired handoff have not been validated for live switching across devices. The notice now uses the actual game ConfirmMenu prefab/stack, with its own dismiss action, rather than Android AlertDialog or the almanac unlock action. No new audio backend changes in r3.

Checks: 74 Python tests, 36 real Java fixtures, 93 actual .NET source/candidate String.Format pairs, 4 real-APK metadata restore cases and 12 real-APK almanac restore cases. Managed-file tests retain all 11 save/settings/unknown fixtures. Both ABIs compile; normal builds exclude music diagnostics.

## Inputs and scope

- One EN APK, version code `4100102` (`4.1-English-pre1-r3`), `com.LanPiaoPiao.PlantsVsZombiesEN`.
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

The initial replacement used normalized streaming AudioClips; the corrected build uses DecompressOnLoad on the game's two music sources. Unity retains playback times, drum synchronization, fades, loops and volume. There are no extra players, muted duplicate songs, per-frame music polling or startup audio extraction. SFX assignments take only pointer comparisons; a bounded cache avoids repeated resource loads. Soundtrack selection is fixed for the session, with a saved choice and restart notice.

44 banks are appended: 27 Original and 17 Blooms. Original audio objects and payload bytes remain unchanged; ResourceManager adds the new paths. Unreplaced songs use normalized Original where available. A missing profile resource retains the official clip and logs the event once per cached track. This intentional resource fallback differs from the removed player timeout fallback.

Constant gain targets -18 LUFS and a -2 dB true-peak ceiling before encoding. Paired stems share gain. No dynamic-range compression, tempo change, trim or padding is applied. FSB disk encoding remains Vorbis, as in the official assets. Differing source stem lengths are preserved; sparse/silent preludes are not amplified into noise. Peak-limited tracks may remain quieter.

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
- 36 Java display fixtures and regex-prefix/cache checks pass.
- Managed files: 8 checks preserve 11 save/settings/unknown fixtures.
- Actual signed APK pair: 4 metadata and 12 almanac restore cases pass across two storage roots, multiple profiles and repeated old-backup restoration.
- ARM64/ARMv7 runtime builds pass; ARM64 screen-plan test runs on Nova.
- Signature v1/v2/v3, original certificate, 16 KB alignment, ZIP/duplicate entries, manifest/version, protected metadata, allowlisted APK changes and unchanged official native libraries pass. No offline recognizer payload.
- S26 receives r3 as an in-place update. The maintainer reports smoother decompressed playback; long-session and lower-memory results remain unverified. Nova testing is stopped at the maintainer's request.

Detailed local evidence is in task `work/upgrade41/`: source inventories/disassembly, review reports, payload census, audio normalization/decode results, build logs and device captures. Extracted game binaries and credentials are not repository deliverables. The APK remains local pending maintainer testing; see the draft release notes for the short checklist and save paths.

S26 visual checks confirm the restored plant description sizing, full Super Stacking instructions within bounds, corrected research-point banner and costs, and the game-style music notice with working dismiss/navigation. An existing Super Stacking checkpoint loads after the update. A few specialized stage reward names without verified Blooms equivalents remain Chinese. Official HoverGardenManager.EnterRun explicitly requests a 60-second first-entry tutorial banner; InGameText uses an unscaled timer, not message length. That stock duration is preserved.

Final S26 r3 check: Explore/Unlock Silver, Bronze item names, unexplored-stage headings, Research costs and Inspect / Upgrade fit correctly. Music notice OK and Close both work from paused-level Settings; Back returns to Pause and the ordinary quit confirmation retains its original action/Cancel label. Blooms selection restored and the game returned to its main menu. No further Nova access.
