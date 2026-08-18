# Next release gate: Android 3.9 Clean Test 3

Do not publish this build until it completes a real-device first pass. The
local candidate is `PvZ-Fusion-3.9-English-Android-clean-test3.apk`; its hash
and provenance are recorded in `RELEASE-3.9-EN.md`.

## Required device checks

- Back up saves and remove only any stale external `files/il2cpp` override.
- Install over 3.8.1 Update 6 and confirm Android accepts the shared signature.
- Verify launch, version 3.9, save/load, relaunch, and normal progression.
- Create a new save and check all version labels and `New Save File`.
- Check the English Odyssey key, Return controls, pause-menu `MENU`, and exact
  `LETS ROCK` label.
- Recheck the main-menu dialog, settings/configuration screen, general button
  labels, and in-level overlays that showed scrambled glyphs in Test 1.
- Open new 3.9 plants and items; confirm their art and context menus are intact.
- Inspect new entries that remain Chinese and confirm they are complete source
  text, not PC placeholders or duplicated fallback wording.
- Inspect modifier card titles and descriptions, including untranslated cards.
  Names must not repeat descriptions.
- Compare modifier, plant, and zombie Almanac description alignment.
- Test narrow, 16:9, and ultrawide layouts where available.
- Recheck Odyssey, Challenge, Zen Garden, Gods Evolution, pause, Almanac, and
  plant-selection flows that previously regressed during 3.9 ports.

## Report with screenshots

For each defect, record the screen/navigation path, aspect ratio, whether the
text is dynamic or static, and a screenshot. Do not patch an untranslated 3.9
field with independently generated English; first check whether the PC `3.9`
branch gained a usable translation after the pinned commit.

## Release decision

After device testing, refresh the PC `3.9` branch, review any upstream changes,
rebuild from the clean official inputs, rerun all automated audits, and prepare
release notes. Do not publish the present local APK automatically.
