# Android 4.1 prerelease 1 preparation

Initial investigation notes, November 3, 2026. Work is local on `agent/translation-4.1`, starting from prerelease 4 source `9345d21`. This checklist records the preparation stage; see [the completed candidate audit](ANDROID41-PRE1-AUDIT.md) for implementation and verification. The maintainer approved the final r4 APK for publication as 4.1 pre-release 1. See [the release notes](../RELEASE-NOTES-4.1-PRE1.md). The preparation decisions below are historical.

## Maintainer decisions

- Build one public EN APK, `com.LanPiaoPiao.PlantsVsZombiesEN`. Exclude the local recognizer model, ONNX runtime, service, warmup and recognition hooks. Remove our 4.0.5 Magic Plantbrush entry blocker and allow the official 4.1 implementation to run.
- Keep the first APK local for maintainer testing. Prepare release notes, but do not upload the APK or publish the release before that test.
- Include current Blooms 4.1 English data, with the existing source-alignment and terminology rules. Never import Lite fork translations.
- Restore a separate, manually operated screen-mode button. Do not automatically apply a display change. Repair reversible switching and avoid the original fixed 1920x1080 resolution call. Keep the soundtrack control separately accessible.
- Audit and normalize music levels, including paired music/drum balance. Investigate the playback architecture rather than treating restart-only selection as a sufficient fix. Restart-required soundtrack selection is acceptable.
- Preserve all saves, additional slots and settings during an EN update; refresh only explicitly managed language files. ENAI saves remain separate unless manually migrated.

## Verified input findings

- Android `pvzrh4.1.apk`: 620,177,229 bytes. Metadata SHA-256 `05e1449481edacfd4b7283e94c5b774f9e86965e0962a76309be8037a9f7775c`, version 31, 21,142 string literals.
- PC `PC_PVZ-Fusion-4.1.zip`: 482,813,933 bytes. Metadata SHA-256 `1aafcdc791e40f9a2897777fd1e076a1948544a1cf7531a0708bd625df7f7673`, 21,160 literals.
- Android literal comparison with official 4.0.5: 19,749 shared distinct strings, 1,393 added, 120 removed. Exact-source guards are required; old indices cannot be reused.
- Blooms branch `4.1` pinned at `5a415154d81243771d75e2dd90ae14ae79d52632`. A filtered local archive snapshot was downloaded. Nothing has been imported yet.
- Official 4.1 Unity bundle contains 219,540 objects, 176 AudioClips. `MaLiangService` TextAsset supplies an HTTP recognition endpoint and a token. The token is not reproduced in audit output. Official `MaLiangLocalRequest` uses UnityWebRequest with endpoint/token configuration and new network error messages. This is a network service path, not our offline model.
- Official 4.1 `OptionBtn.OnMouseUpAsButton` still calls `Screen.SetResolution(1920,1080,...)` for the screen button. This was confirmed by ARM64 disassembly, not inferred from an old comment.

## Reported regressions and acceptance checks

| Area | Report | Verification needed |
| --- | --- | --- |
| Offline AI, parked | After a horde, Identify loads then reports recognition stopped | Historical memory/process-death hypothesis remains unconfirmed without logs. Exclude local AI from 4.1 APK. |
| Music playback | Blooms stops after lag and Original becomes audible | Existing Java player errors and 15-second prepare/seek timeout explicitly cause native fallback. No tester log identifies the actual trigger. |
| Music timing | Offset or cut sound after freeze fix | Independent Android media/drum playback clocks and timing inherited from original tracks need replacement or measured synchronization. No audible fix verified yet. |
| Music level | Blooms louder than Original | Measure both sets, normalize without changing tempo, preserve shared gain and timing for paired stems, verify peaks and levels after encoding. |
| Screen mode | Tablet user needs fill/stretch control | Separate button, no automatic application, device-aware sizing, reversible within the same session, settings/main menu/gameplay navigation and touch positions. |
| Modifier card | Chinese `质变：专武登场` and body | Screenshot 1; also appears in Almanac screenshot 5. Compare actual prerelease 4 runtime output and PC 4.1 exact Chinese source, not only a title match. |
| Gods Almanac | `强化：裂解`, mixed Apocalypse Railgun body | Screenshot 2. Recheck actual prerelease 4 before calling it a new regression; tester may have used prerelease 3. |
| Gods Almanac | `强化：穿透`, Melancholy Commando projectile hit count +5 | Screenshot 3. Resolve complete and mixed-language variants. |
| Gods Almanac | Ascend: Toxicity availability condition | Screenshot 4; official source says `蒜毒骤发`, which must use established PC terminology. |
| Gods Almanac | Squash Pumpkin availability, speed and ascend conditions | Screenshot 5; source conditions persist in 4.1. Preserve eligibility semantics. |
| Gods Almanac | `强化：冲击`, Supremacy-shroom effect | Screenshot 6. Reuse approved names and confirm numeric/selection effects. |
| Gods Almanac | `强化：飞天爆竹`, Dragonbreath Torcher effect | Screenshot 7. Handle concatenated source fragments and complete body. |

## Music implementation investigation

The released 4.0.5 bridge keeps the original Unity music sources silent and runs up to two Android MediaPlayers. They prepare and seek independently, with a 15-second timeout and per-channel Original fallback. This confirms plausible paths for the reported offset and soundtrack switch, not a reproduced device failure.

A candidate for 4.1 is Android-encoded, streaming Unity AudioClips for both profiles, selected only at startup. This would preserve the game's own playback, fades and paired-track timing, remove the external players and muted duplicate playback, and avoid loading full decoded songs. Before adopting it, verify resource registration, clip cloning, Android encoding, bounded loading, all unchanged originals and actual-device playback. The installed Unity 2022.3.62f1 editor includes Android support. Official ResourceManager maps music under `audio/music/`; Resources.Load(string,Type) is available. AssetBundle loading APIs and the managed streamAudio setter are stripped, so those routes must not be assumed available.

## Local evidence and next steps

Local evidence lives in task workspace `work/upgrade41/`: input audit, pinned PC source, official extracted Unity inputs, type dump, named disassembly and Unity inventory. These are original game intermediates, not repository deliverables.

Next: validate the streaming clip pipeline; perform measured normalization; port translations from clean 4.1 inputs; remove old recognition hooks; implement the two independent settings buttons; build and run host/package/refresh checks; smoke-test available authorized device if present; deliver one local APK and brief test instructions. Release remains unpublished and the APK remains unuploaded pending maintainer testing.

## Current local checkpoint

Local r3 (4100102) supersedes the initial investigation options above. DecompressOnLoad replaced streaming after on-device seek diagnostics; no external players or offline recognizer ship. The settings column and manual resolution reversal are verified on S26. Follow-up fixes restore almanac font normalization, scope recipe matching to known ingredients, and expand Super Stacking/Odyssey UI. See the candidate audit/build record for current checks. No upload or publication. Test only S26 until further notice; leave Nova untouched.
