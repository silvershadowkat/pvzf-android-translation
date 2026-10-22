# Android 4.0.5 prerelease 3 settings correction

2026-10-21. Settings fix: revision 9. Latest main candidate: revision 10, with startup status text removed. Not published.

## Result and exact changes

`runtime/english.cpp`, `attachOptions` now places Music in the existing `OptionMenu/Buttons/F` slot. It clones the known `Almanac` UIButton style, clears its original click event, copies the F RectTransform anchors, pivot, size, scale and local position, and deactivates F and its fullscreen caption. The verified F component is `OptionBtn` with `optionType == 0`. Existing lower controls, their labels, confirmation prompts and event handlers are untouched.

The original Screen Mode handler in the pinned Android ARM64 binary, `OptionBtn.OnMouseUpAsButton` at RVA `0x2282404`, passes fixed dimensions 1920 and 1080 to the resolution setter. The maintainer reported stretching that required restarting the game to recover. Revision 9 removes access to that handler through this settings button. It does not add a global resolution override or change the game's keyboard handling.

The experimental lower-column reflow from revisions 6 through 8 has been removed. It first failed because neighboring controls use UIBtn/OptionBtn rather than UIButton, then caused size and press-animation regressions. Revision 9 only positions the new control in an existing slot. No existing control is repositioned or resized.

`auditMusic` uses the available two-argument scene enumeration overload. An unavailable enumeration now reports failure explicitly instead of reporting zero audio sources. This is a one-time read-only check at startup and after switching, not continuous logging. Playback implementation and preserved timestamp behavior are unchanged.

The ManagedFiles comment and main review document now correctly identify `SaveInfo.GetDataPath`. This is a documentation correction, with no save-refresh behavior change.

## Verification

- Revision 9 seed installed over revision 8 on S26 Ultra, Android 17, serial R5GL14CN45N, EN package, without uninstalling or clearing storage.
- Existing external `playerData.json` SHA-256 was identical immediately before and after installation. This proves preservation of that actual file, not an exhaustive inventory of all possible saves.
- Runtime log confirms creation in the Screen Mode slot. Screenshot confirms Music at the top right, no Screen Mode caption, and the lower controls at their original sizes and positions.
- Switched Blooms to Original and back. Both snapshots show the same main AudioSource pointer, with one known music track playing at nonzero volume. The timestamp advances across the switches. This observation covers main-menu playback, not every gameplay/drum arrangement.
- Opened the Almanac confirmation dialog, attempted Music behind the dialog, then cancelled. Music did not switch through the modal. No unlock/reset action was confirmed.
- Pixel comparisons of the Music region and existing right-column controls before/after switching and dialog cancellation are identical. This checks resting positions after those interactions; it does not claim every game button has been exhaustively tested.
- Native builds for ARM64 and ARMv7, host refresh/translation checks, APK signing, alignment and manifest checks passed for both seed and main. Results are recorded in `build-seed-r9.json` and `build-test1-r9.json`.

Evidence in the active task's `work/upgrade405/pre3`: `s26-runtime-r9.log`, `s26-install-r9-preservation.json`, `s26-settings-r9-before.png`, `s26-settings-r9-original.png`, `s26-settings-r9-dialog.png`, `s26-settings-r9-after.png`, and `s26-settings-r9-comparison.json`.

## Manual update result and revision 10

The maintainer confirmed both seed markers, STALE TEST Coins and STALE Pea(0), then manually installed test1-r9 over the seed using Android's installer. They confirmed both labels changed to God Coins and Peashooter(0), with unlocked progress, settings and music choice retained. This validates the normal on-device update path on this S26. It does not establish preservation of every possible mode/profile save configuration.

The agent's attempted pre-install file inventory stopped on unreadable historical tombstone crash logs before reaching installation. No main APK was installed by the agent. The user explicitly requested manual installation; that instruction remains in force.

Revision 10 changes only the bootstrap presentation in EnglishActivity.onCreate: replace the TextView reading Preparing English game files... with a plain black View. Translation verification, refresh, runtime initialization ordering and failure dialogs remain unchanged. Both ABI builds, host checks, signing, alignment and manifest checks passed. Relative to main-r9, only AndroidManifest.xml (version), classes2.dex and assets/english/manifest.json (revision) differ outside signing data. The old status message is absent from classes2.dex. The game payloads and runtime native libraries are unchanged. At the user's subsequent explicit request, revision 10 was installed over main-r9 on S26 without clearing data. playerData.json was byte-identical across installation. PID 9970 reached the GameAPP update/render callbacks and played Blooms on one music source. The maintainer subsequently confirmed: startup looks clean now. The revision 10 startup visual check passed on S26.

## Remaining checks

Revision 10 is installed and its clean transition to the game's launch logo is confirmed by the maintainer. Do not reinstall the seed or clear storage. Still pending: gameplay projectile button and adjustable UI group, gameplay music/drum checks, other device aspect ratios, real multiple-profile/mode-save update coverage, and reopening after the main update. The refresh replaces only known language files and preserves unknown data. No publication is authorized.
