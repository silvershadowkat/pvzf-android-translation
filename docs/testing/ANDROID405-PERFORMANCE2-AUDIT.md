# Android 4.0.5 prerelease 3: October 28 follow-up

Status: both candidates were built, signed and installed over the Retroid's existing apps. Their verified payloads are promoted as [prerelease 4](../RELEASE-NOTES-4.0.5-PRE4.md), with only version/signature changes. See [candidate build records](ANDROID405-PERFORMANCE2-BUILD.json), [release promotion verification](ANDROID405-PRE4-BUILD.json), and [remaining play checks](PLANTBRUSH-AI-EXPERIMENT.md). The candidate filenames/version numbers below describe the tested inputs.

## Music stalls

Tester reports consistently isolate the delay to Blooms music; Original music behaves better. The previous bridge requested `DownloadHandlerAudioClip.set_streamAudio`, but that setter is stripped from the Android 4.0.5 player. A missing setter did not make the request streaming. This is evidence for an avoidable full-clip loading path, not proof that every reported crash has the same cause.

`MusicBridge.java` now owns at most two Android MediaPlayer streams on a background HandlerThread. Files are prepared asynchronously. Track changes release the previous stream; repeated status updates do not seek or restart a playing song. Stale callbacks cannot revive a discarded player. A failed or timed-out decoder falls back to Original music instead of retrying continuously. Activity pause/resume controls background playback.

The original Unity music sources remain silent timing sources while Blooms is selected. The bridge preserves the volume seen by game fade logic through paired volume getter/setter hooks. Only Blooms is audible. This avoids loading replacement Unity AudioClips, but does not claim that the game's original audio sources consume zero resources. Music state is sampled four times per second. Selecting Original releases the Android streams and bypasses recurring music bridge queries.

No music files, game speed, pitch, audio quality, or gameplay data were changed.

## Plantbrush entry and recovery

- One tap enters the AI mode while the private recognizer loads in the background. Identify waits for successful native warmup; a premature Identify is queued and runs when ready. Closing/cancelling the drawing menu or leaving the mode cancels that queued action.
- Binder health calls run off Unity's thread and Android's UI thread. A lost connection, failed startup, or stalled request releases the binding. A later explicit tap can start a fresh recognizer session, with a short cooldown and no automatic crash loop.
- Startup has a 120-second deadline. A request stalled for 45 seconds reports failure. These are recovery bounds, not recognition speed guarantees.
- The separate `:plantbrush` process is still released on mode exit or after 30 seconds in the background. Only this task-owned recognizer process is terminated. Unity is not restarted.
- Verified immutable model files use private hash/size/mtime receipts, so revisiting the mode does not repeatedly hash the large model. Missing files, changed file stats, or a changed manifest hash require full SHA-256 verification and replacement. Saves and translation overrides never use these receipts.
- The regular APK still blocks the unavailable mode with a temporary notice. It contains no model or recognizer service.

## Other redundant work removed

- Removed the startup-wide text/scene scan and forced text rebuild. Runtime hooks are now installed before `il2cpp_init` returns, so ordinary Start and text callbacks handle the initial scene. The Retroid confirms both the Projectile Info button and Settings music selector are created without the scan.
- Re-registering an unchanged custom-level title/tip no longer clears the entire translation cache. Changed or ambiguous mappings still invalidate it.
- Removed superseded trailing metadata literal blocks. The compactor accepts only the verified metadata v31/256-byte header, requires a separate trailing literal section, and verifies every other active section byte-for-byte. Literal values and lookup indices are retained; the 17 protected internal strings still pass their original checks.
- Metadata is now 15,772,926 bytes, 5,297,482 bytes smaller than the previous candidate. The compaction step removed 5,960,024 bytes from the intermediate updated payload. This saves file space and hashing/loading work, not a measured gameplay FPS gain.
- Java build intermediates are cleaned within the builder's own classes/dex directories, preventing obsolete anonymous classes from entering later APKs.
- Retained per-frame projectile-button visibility synchronization because it prevents the control appearing over plant selection or modal screens. Retained full integrity checks for externally restorable translation overrides and all save-preservation guards.

## Translation audit

Upstream: Blooms `Teyliu/PVZF-Translation`, branch `4.0`, from `c7fb5997d65e1d5248f3d7a9ca9c9e0a4b516640` to `4222fa8dc86ec0948432421bfc26d8426e9b8735`.

- Imported 185 new/changed exact mappings and one wave-number regex. Updated 27 previously translated metadata literals, 12 almanac fields, and one serialized Settings label (`Disable Mini Sun Visual Effect`). Existing Android corrections and all prior dictionary keys are preserved.
- Three almanac fields did not pass the Chinese-source/prior-English guards, so their Android wording was retained: plant IDs 901/902 `info`, zombie ID 87 `introduce`. The approved name for zombie 87 becomes Tinfoilhead Zombie.
- Matched 442 Android modifier strings against PC catalog titles. The post-runtime audit found three incomplete matches: Ravenous Reach, Zombie Parry, and Pain Response. Their PC names are reused; unambiguous effects are translated from Android's actual Chinese. PC-only cooldowns, thresholds, and bug annotations are not inserted.
- Ravenous Reach had been rejected because its PC description contained “currently bugged,” leaving an English heading with a Chinese body. It now says `Tyrannoflora Lux: Increased attack range`. Both original and partially translated variants have regression fixtures, and the baked literal is corrected too.
- The full metadata display-candidate audit also includes internal keys, logs and unformatted templates. Remaining Chinese in that inventory is not evidence that all of it appears on screen. Unapproved specialized names are not invented.

The Lite fork was inspected through its October 27 changes (`52324aeb` lineage). New packaging scripts, translation-data refactoring, and PC Harmony compatibility changes did not reveal an additional applicable Android runtime performance fix. No translations or code were imported from that fork.

## Verification

Host checks completed before packaging:

- 69 Python tests, including metadata-compaction guards.
- 31 deterministic asynchronous music/recognizer/model-receipt checks. These test ordering and ownership with Android fakes, not real codec speed.
- Translator parity against the released algorithm with the updated dictionary; rich text, unknown text and dynamic message fixtures retained.
- Three modifier-card regressions from original and mixed-language inputs.
- Managed refresh fixtures preserve saves, settings and unknown files.

Final APK signature/alignment, package separation, actual-APK refresh checks and device findings are recorded in the build/device reports. Do not infer Redmi Note 9 performance, a universal crash fix, or minimum device specifications from host tests. No Redmi is available for direct reproduction.

### Final artifact and device checks

- Both APKs retain the release signing certificate and their EN/ENAI package IDs, with versionCode 4050342. The AI PlayerSettings object is byte-identical to the previous ENAI build. No original game native library changed.
- Compared 208,662 Unity objects: only the three almanac TextAssets and the reviewed Settings text component differ from the prior regular bundle. The AI bundle changes only PlayerSettings relative to that regular bundle.
- Actual signed APK tests pass for both variants: four repeated metadata-restore checks, twelve almanac/profile-restore checks, all managed asset hashes, seventeen protected internal literal slots and the three baked modifier fixes. Save/unknown-file fixtures remain intact. Translator parity covers 9,307 strings. Native cache and field-ABI tests also pass.
- Both updated apps reach the Retroid main menu. `playerData.json` was unchanged immediately after each in-place installation, before launching. This is an existing-profile check, not a claim that every possible save format was manually played.
- AI entry required one tap and entered while service state was still loading. Native warmup then passed. An actual drawing request returned the expected English low-confidence notice in 194 ms.
- After more than 30 seconds in the background, the recognizer process exited. On returning, one Identify reloaded the service and automatically completed the queued request in 193 ms after warmup. Unity's PID stayed unchanged. This verifies reload after lifecycle cleanup; deliberate native-crash and 45-second stalled-inference recovery remain host-tested only.
- Android media diagnostics show the new main-menu stream, then exactly the Pool and Pool-drum streams. Both paused on backgrounding and resumed with the same player connection IDs. No bridge decoder error appeared in the captured session. These observations do not measure audible synchronization, Redmi stalls or long-session stability.
- Projectile Info remains present during gameplay. Settings shows the music selector and updated `Disable Mini Sun Visual Effect` wording. Switching to Original releases both Android player clients. Audible switching/volume fades, early-request cancellation, the three modifier cards' final layout and long Gods sessions remain in the play-test checklist. No screen-size workaround was added for the Retroid.

### Reproduction order

1. Run `port_pc_refresh_405.py` with the pinned PC snapshots into a fresh payload workspace.
2. Apply the static component plan with `apply_static_display_delta.py` before finalization. The plan is retained in [translation evidence](ANDROID405-PERFORMANCE2-TRANSLATIONS.json).
3. Run `finalize_oct28_payload.py` against the verified official APK to add modifier fixtures, compact metadata and refresh manifest hashes.
4. Build the regular variant using `build_performance_candidate.py --variant regular --payload-report ... --release-names --version-code 4050342 --version-name 4.0.5-English-pre3-performance2` with the recorded base APKs and local toolchain/signing inputs.
5. Generate the ENAI identity bundle from that regular APK with `plantbrush_identity_assets.py` in a fresh directory. Add its path, SHA-256 and `only_player_settings_changed: true` audit result as `ai_identity_bundle` in the payload report, then build `--variant ai` with the same options. Never give the AI APK the regular Unity bundle.

The builder verifies pinned base hashes, the exact payload allowlist, both native ABIs, the certificate, alignment and unchanged non-allowlisted entries. Audit/build JSON stays with repository documentation; it is not intended as an extra player download.

The official 4.x almanac visibility behavior is unchanged. See [the separate comparison](ANDROID405-ALMANAC-VISIBILITY-AUDIT.md).

The subsequent Retroid Settings/Back failure was traced to an ADB-owned save with insufficient write permissions, not a changed button binding. See the [Settings exit investigation](ANDROID405-SETTINGS-EXIT-AUDIT.md) for the exception, repair and navigation checks. No production code change was made for that device-specific failure.
