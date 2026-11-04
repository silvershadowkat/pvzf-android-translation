# Android 4.1 optional ENAI local candidate

Publication follow-up: final ENr7 and ENAIlocal4 were published unchanged as [4.1 pre-release 2](https://github.com/silvershadowkat/pvzf-android-translation/releases/tag/v4.1-release-2) on November 4, 2026. See [the verified publication record](ANDROID41-PRE2-RELEASE-BUILD.json). The dated candidate checks below retain their original scope.

November 4, 2026. Branch `agent/translation-4.1-enai-local`, based on the committed EN feedback fixes at `f670f5a`. Local artifacts only. The public `v4.1-release-1` APK and tag are unchanged.

## Identity and scope

The final regular candidate is `PvZ-Fusion-4.1-English-feedback2.apk`, version `4100106`, `4.1-English-pre1-r6`. The optional AI candidate is `PvZ-Fusion-4.1-English-ENAI-local3.apk`, version `4100108`, `4.1-English-pre1-ENAI-local3`. The adjacent BUILD records contain complete hashes and package checks.

ENAI retains `com.LanPiaoPiao.PlantsVsZombiesENAI` and the published signing certificate, so it updates an existing ENAI installation. Its saves remain separate from regular EN. No automatic import, uninstall or data clearing is performed.

The AI builder starts with the exact audited regular candidate. Exactly two Unity objects change: PlayerSettings for ENAI identity and the MaLiangService configuration for loopback-only recognition. Upstream service credentials are removed from that configuration. All other 219,582 serialized objects, protected metadata, translation data, music payload and original game native libraries remain unchanged. A semantic audit compares 181 original DEX classes; only BuildConfig.APPLICATION_ID changes. The optional Java/native bridge, inference runtime, model and catalog are added separately. Regular builds explicitly disable the optional native integration.

The old catalog has 744 references covering 718 distinct plant IDs. Every enum name/ID pair matches actual Android 4.1. It does not cover all new plants or zombie recognition. Explicit unsupported plant/zombie requests receive readable errors; the implementation does not invent a mapping or send them to an online fallback.

## Memory and lifecycle

Keep ONNX Runtime 1.24.3 and the existing float32 CLIP ViT-B/32 model. The pinned Android AAR SHA-256 is `67397e4a970e75617f765d2015ceaf911917e1d822276cfb5792744e8085cbce`. Extracted classes/libraries are compared with that AAR. Do not return to the 1.23.2 runtime that previously failed native inference on the S26.

Reuse one direct native-order input buffer, its tensor and input map on the serial worker. Stable primitive ranking preserves the previous tie ordering without boxed indices/comparator allocation. Connected-component traversal avoids per-pixel neighbor arrays. Two intra-op threads and one inter-op thread are retained, with idle spinning disabled. Model, thresholds and recognition math are unchanged. Official references: [direct-buffer tensor API](https://onnxruntime.ai/docs/api/java/ai/onnxruntime/OnnxTensor.html), [threading configuration](https://onnxruntime.ai/docs/performance/tune-performance/threading.html).

The final lifecycle follows the maintainer's explicit preference to keep recognition loaded while the game runs. Loading starts on first drawing-menu use, outside Unity's thread. The session remains loaded between modes, during idle time and while backgrounded. There is no routine two-minute idle or thirty-second background unload. Finishing the game's activity releases it; Android can also reclaim its process. Critical memory pressure releases it between requests. Normal mode disposal only cancels a queued drawing. First-load queuing, stale callback protection, explicit retry cooldown, startup deadline and stalled-inference recovery remain.

The model/index and reused buffers have fixed sizes. Recognition still makes temporary allocations, so process memory can rise during warmup or GC cycles; fixed model size is not proof of leak-free indefinite operation. A local1 S26 sample was 439,373 KiB PSS, about 429 MiB, for the recognizer alone. This is additional to Unity and is not a low-memory-device guarantee. Retention removes unnecessary reloads but does not shrink the model.

Incoming images are capped at 512 by 512 before pixel allocation; the game's actual requests are 256 by 256. HTTP input remains bounded, loopback only, serial and non-exported. No added per-frame scan or inference runs on Unity's thread.

## Verification and limits

- Both ABIs compile; signing certificate, package/version, ZIP integrity, 16 KB alignment, original native libraries and protected metadata pass.
- 172 exact preprocessing/ranking checks and six saved-embedding golden fixtures pass. Direct tensor values match the previous implementation bit for bit. The optional Windows native ORT 1.23.2 test could not initialize; it is not counted as passed. Actual Android 1.24.3 inference is tested separately below.
- 33 asynchronous lifecycle/recovery checks pass, including retention past the former background/idle deadlines and release on actual game exit. Historical MusicBridge tests are included in that harness but do not mean the old Android music backend is packaged.
- 75 Python tests and 71 real-Java display fixtures pass. The display harness now appends built-in translation rules in actual startup order. Mixed drawing-tool/Width status is covered for all known tools with bounded full-string rules.
- Actual signed old-ENAI-to-final-ENAI fixtures pass four metadata and twelve almanac restoration cases while preserving save/settings fixtures.

USB testing uses only the authorized S26 Ultra, serial `R5GL14CN45N`. No Retroid device is touched. Eight regular EN and two ENAI saved JSON files are backed up; every hash remains unchanged through installation and the first live checks, including both final updates. No progress seeding, unlocks, settings resets or whole-directory restore is used.

On EN r5, live Plantern and Peashooter Plant Info display readable English headings, HP, lane/column and separate stat cards. Peashooter has separate Attack Power, Attack Interval, Attribute Count and Lumos Level cards. The 5008 almanac displays the reviewed English description and verified recipe, retaining its unverified Chinese name. Beamshooter and night Plantern cases are additionally reproduced with the actual .NET parser; those exact plants/conditions are not claimed as manually played. Final r6 retains those payloads byte for byte. Its native loadable sections equal r5 except the GNU build ID; only Java tool-status matching changes behavior.

On ENAI local1, actual Android native warmup and all six recognition fixtures pass: blank/rectangle reject and Peashooter, targeted Peashooter, Wall-nut and Starfruit match the saved expected IDs. Fixture round trips take about 0.05 to 0.18 seconds on this S26 sample. A drawing submitted through the actual UI produces candidates and successfully awards the selected Repeater. This validates the 4.1 root endpoint and response integration. Local1's idle unload was observed, then deliberately removed at the maintainer's request. Final local3 passes 31 expected recognitions in the same native process and remains loaded beyond 130 idle seconds. PSS samples are 417,056 KiB at readiness, 458,218 after ten requests, 458,240 after twenty, 458,448 after thirty, 423,915 after idle and 426,824 after another request. This shows warmup/transient allocation and subsequent reclamation, rather than sustained growth in this short sample. It is not a long-duration leak guarantee. The final Line/Width footer is visibly English. Mode exit to the main menu and a 35-second background/resume preserve the same ready recognizer process; all six native fixtures pass again afterward without reloading. All ten saved JSON hashes remain unchanged after these final live tests. Actual Quit ends both the game and recognizer processes, and the temporary USB forwarding rule is removed.

Original EN loads main menu, card selection, Day and Day_drum. Blooms ENAI loads main menu, card selection, Pool and Pool_drum, then returns to menu. Logs show inactive decoded references released and no missing-profile resource error. The initial Original and Blooms preferences are preserved. Music profiles/loading/cleanup source and resource bytes are unchanged. The remaining report does not describe a reproducible symptom; “original” may mean the Original soundtrack option. This review does not establish that audible cuts are absent on every device or in long sessions, and no speculative audio-backend change is made.

Local device evidence is in the continuation chat's `work/s26-20261104/`. Build and host evidence is in `work/offline41/` and `work/feedback41/`. Extracted game data, private saves, model intermediates and credentials are not source-repository deliverables.
