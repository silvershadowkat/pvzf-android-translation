# Magic Plantbrush: local Android prototype 1

## Delivery

Local test APK only. Not published or uploaded.

- AI: `PvZ-Fusion-4.0.5-English-AI-prototype1.apk`
- Package: `com.LanPiaoPiao.PlantsVsZombiesENAI`
- App label: **PvZ Fusion English AI**
- Save directory: `/Android/data/com.LanPiaoPiao.PlantsVsZombiesENAI/files/`
- Android 8.0 or newer; arm64-v8a and armeabi-v7a included.
- Separate installation and data from regular `com.LanPiaoPiao.PlantsVsZombiesEN`. No automatic save import.
- Regular text-only build: `PvZ-Fusion-4.0.5-English-Android-prerelease3-drawing-text-fix.apk`. This retains the regular package, version code, native runtime, and unavailable-mode guard.

Both are signed with the existing English release certificate. Published prerelease 3 remains unchanged. Build JSON files alongside the APKs contain exact hashes and sizes.

## What changed

The AI APK contains the game and its recognizer in one installation. It needs no companion app, desktop server, model download, account, or cloud recognition. The original Windows executable is not bundled or executed. No Spanish companion app code was reused.

1. **Entry guard:** the existing `Advanture_Btn.OnMouseUp` hook targets only challenge 197. While the recognizer loads, entry shows a temporary loading notice. Once ready, it temporarily clears this button's `limInMobile` flag, calls the original handler, and restores the flag. The game's original Android unavailable dialog is bypassed only for that mode.
2. **Drawing requests:** `MaLiangMenu.Parse` calls the original method only when the local recognizer is ready. Original canvas, touch controls, candidate selection, plant creation, statistics, and game logic are retained.
3. **Lifetime:** `GameLevel.MaLiangLevelData.Dispose` releases the recognizer. Activity lifecycle handling also releases it after 30 seconds in the background. Service failure does not automatically restart it in a loop.
4. **Private Android service:** a non-exported bound service runs in the app's `:plantbrush` process. It listens only on `127.0.0.1:17861`, matching the game's existing protocol. It exposes health and PNG recognition requests. Killing this dedicated process releases native model memory without terminating Unity.
5. **Recognition port:** OpenAI CLIP ViT-B/32 vision-only float32 ONNX model, ONNX Runtime 1.23.2 CPU, two inference threads. The supplied Windows revision-3 catalog, reference embeddings, negative examples, drawing measurements, candidate scoring, and confirmation behavior were ported to Java. All 744 catalog records use approved English game names by numeric plant ID, covering 718 distinct plants. No plant names were invented.
6. **Shared translations:** `PlantbrushTranslations.java` supplies drawing-tool status, recognition failures, result-card similarity/strength/selection wording, plant-received notices, and appearance-change notices. Complete display matches preserve numeric values and unknown text. These rules are included in both builds. The regular correction changes only `classes2.dex`, using the release tag's original activity and file-refresh implementation plus these shared rules.
7. **Separate identity:** ENAI application ID, app label, resource package, BuildConfig application ID, and Unity PlayerSettings product identity. Java class namespaces remain unchanged. The app uses Android-provided storage paths, preserving separation from EN and RH.

## Safety and data boundaries

- Base APK SHA-256 is pinned to published prerelease 3.
- Original game native libraries, metadata, translated artwork, audio, save structures, and gameplay objects are unchanged.
- Unity object audit compared 208,662 objects. Only the PlayerSettings object changed for ENAI identity.
- DEX disassembly compared 181 classes. Only BuildConfig APPLICATION_ID changed semantically; the writer also omitted explicit zero/null static initializers, which have identical default values.
- Model/index/catalog copies are hash-verified in the app's own `noBackupFilesDir`. The save-refresh allowlist is unchanged.
- Recognition runs away from the Unity/UI thread. Loading has a two-minute deadline. HTTP headers, PNG size, decoded dimensions, and socket waits are bounded. Requests are processed serially.
- Android cleartext traffic is allowed to support the game's existing HTTP loopback protocol. No external AI endpoint is added.
- AI failures retain the existing game process; the UI reports failure and asks for a restart. There is no retry loop.
- Both builds retain the current release version code 4050339. ENAI is a separate package, not an update to EN.

## Verification

- Model export checked against upstream Torch output: cosine similarity above 0.9999998 on both export fixtures.
- Six host fixtures and the same six Android requests matched upstream acceptance/rejection and selected plant: blank, rectangle, pea, targeted pea, wall-nut drawing, and starfruit drawing.
- Retroid Pocket Nova, Android 13, arm64: accepted drawing requests took approximately 0.19 to 0.29 seconds in the final ENAI integration test. This is a small fixture benchmark, not a general performance guarantee.
- Actual game flow: enter mode, select Standard Mode, open Bronze Brush, draw through touch controls, Identify, choose candidate, receive plant card.
- Blank drawing returns the English error. Tool status and candidate cards were visually checked in English without text overflow in the tested viewport.
- Private service used 439,401 KiB PSS after recognition (about 429 MiB), in addition to the game.
- Exiting to the main menu removed the AI process while the game remained running. The regular EN save file stayed byte-for-byte unchanged during the ENAI test.
- ENAI initially created fresh independent player data. Test-created unlocked data was then manually seeded for integration testing; this is not an automatic import feature.
- Signature, ZIP integrity, 16-KiB alignment, manifest identity, and APK entry-change gates passed.
- Five shared translation fixtures exercised the actual Java display translator, including unknown-name preservation.

## Remaining play tests

First tap of Magic Plantbrush may show a loading notice; tap again after a few seconds. Select a mode and use a brush card to draw. Test Standard and Cursed modes, several recognizable plants, repeated drawings, selecting/canceling candidates, leaving/re-entering, and background/resume on the S26. Compare recognition quality with the PC service using the same drawing if a result looks wrong.

Only the Nova's arm64 path was device-tested. Thirty-two-bit devices, low-memory phones, long sessions, every plant/skin, custom-target gameplay, and every layout have not been exhaustively tested. Android's existing drawing UI has truncated button labels such as Medium in the tested layout; no Nova-specific layout code was added. Recognition uncertainty is retained rather than forcing a confident plant match.

## Sources and maintenance

Source branch: `agent/magic-plantbrush-single-apk`.

- `scripts/plantbrush_export.py`: pinned upstream vision-weight conversion and index conversion.
- `scripts/plantbrush_identity_assets.py`: guarded Unity identity change and object audit.
- `runtime/plantbrush/tests/PlantbrushIdentity.java`: structured DEX identity rewrite.
- `scripts/build_plantbrush_prototype.py`: exact-base optional AI packaging and signed APK validation.
- `scripts/build_regular_drawing_text_fix.py`: release-tag-based regular translation-only APK.
- `runtime/plantbrush/java/`: Android service, inference/scoring, and image/math implementation.
- `runtime/java/com/silvershadow/pvzf/PlantbrushBridge.java`: lightweight optional lifecycle bridge.
- `runtime/java/com/silvershadow/pvzf/PlantbrushTranslations.java`: common display wording.

Workspace evidence, conversion assets, fixture scripts, logs, screenshots, and build intermediates are under the task's `work/plantbrush-prototype`. They are intentionally not committed as large binaries. CLIP and ONNX Runtime MIT licenses and attribution are packaged. The supplied MaLiang reference index and game assets retain their original provenance; this local prototype does not assert new distribution rights for them.

## Final handoff

Both final signed artifacts were installed on the Nova and passed startup checks with the shared rules loaded. Both player-data files were unchanged by installation. The regular build replaced the earlier task-only EN AI test build, restoring the published native runtime. Test apps were stopped, the ADB forwarding port was removed, and the original 960 x 1280 display setting was restored. No Nova-specific layout code was added.
