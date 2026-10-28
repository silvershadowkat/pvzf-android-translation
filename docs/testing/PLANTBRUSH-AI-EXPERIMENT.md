# Experimental AI APK: current test checklist

Target: the October 28 performance follow-up for [4.0.5 prerelease 3](https://github.com/silvershadowkat/pvzf-android-translation/releases/tag/v4.0.5-release-3). The new local AI file ends in `Experimental-AI.apk`. See [the follow-up audit](ANDROID405-PERFORMANCE2-AUDIT.md) for publication and verification status. The regular APK intentionally keeps the unavailable-mode notice.

## Installation and saves

- Back up saves first. Install ENAI over an existing ENAI prototype without clearing data. The regular EN app and ENAI app are separate installations.
- AI saves: `/Android/data/com.LanPiaoPiao.PlantsVsZombiesENAI/files/`.
- Regular saves: `/Android/data/com.LanPiaoPiao.PlantsVsZombiesEN/files/`.
- There is no automatic cross-app import. Do not restore old translation files, the `il2cpp` folder, or the entire old data directory. See [the save guide](../../README.md#moving-saves-without-restoring-old-translation-files).

## Quick play checks

1. Open Recommended Levels, then tap Magic Plantbrush once. The mode should open while its recognizer loads. Identify still requires successful native warmup: an early tap should wait and run automatically when ready. Closing the drawing menu must cancel a waiting Identify.
2. Open a brush and draw a recognizable plant. Tap Identify, select a candidate when offered, and check that the received plant and its name appear correctly.
3. Test Standard and Cursed modes, different brush tiers, changing a plant's appearance, and more than one recognition in the same session.
4. Try a blank drawing and an unclear drawing. Check that rejection/result messages stay readable and English. If a drawing triggers the zombie event, its notice should also be English.
5. Toggle the grid and drawing tools. Check status text, candidate similarity/strength, undo/redo, and cancel/close behavior on your normal screen size.
6. Leave the mode, return, and identify again. Also test background/resume, including more than 30 seconds outside the game. Check for a useful loading/failure notice and no frozen game UI.
7. Close/reopen the app and verify your progress, extra mode saves and settings remain intact. Install later updates over the same package and repeat that check.
8. If recognition fails or the service stops, wait a few seconds and tap Identify again. It should reload the recognizer without restarting the game. Report repeated failures instead of repeatedly retrying.

## Shared performance checks

- With Blooms selected, move from the main menu through plant selection to a Pool level and back. Check for stalls, a song starting twice, and delayed tracks after leaving a screen.
- Switch Original/Blooms repeatedly, change music volume, and background/resume. Confirm only the selected soundtrack is audible and music stops in the background.
- Confirm the music selector and Projectile Info button still appear, with the latter hidden during plant selection and other blocking menus.
- Check Ravenous Reach, Zombie Parry and Pain Response for English descriptions. Check the Settings label `Disable Mini Sun Visual Effect`.

## What is verified, and what is not

Earlier AI gameplay was tested on a Retroid Pocket Nova and a Samsung Galaxy S26 Ultra. The original runtime failed on the S26 with a native CPU-instruction error; ONNX Runtime 1.24.3 passed warmup, six recognition fixtures, and an actual in-game recognition there. The maintainer then confirmed successful play. Those are historical engine results, not verification of every October 28 lifecycle change. The newer follow-up retains that engine/model and changes entry, recovery, file verification and music streaming; its device results are recorded separately in the follow-up audit.

The final shared translation code passed 129 display checks for each variant. The static audit covers 164 mode-related methods, 24 drawing-window labels, and 744 catalog display names. See [the evidence](../magic-plantbrush-prototype.md) and [machine-readable text audit](../plantbrush-text-audit.json). This does not mean every rare event or phone has been manually tested.

S26 fixture requests took about 0.15 to 0.16 seconds. One recognizer-process sample used about 438 MiB PSS in addition to the game. These measurements are not a minimum-device specification or a performance guarantee. Long sessions, low-memory phones, 32-bit devices and other chip families need testing. No universal compatibility claim is made.

When reporting a failure, include APK filename, phone model/chip if known, Android version, mode and brush tier, what you pressed, and whether it was the first Identify or followed background/resume. A screenshot and approximate failure time help. Do not share save files or private data unless needed for a specific investigation.

Automatic persistent failure tracking, a diagnostic-export button, and a conservative alternative inference build were discussed but are not implemented features of this release.
