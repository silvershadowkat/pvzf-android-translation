# Prerelease 3 r19 follow-up review

Local work only. Nothing in this follow-up publishes a release.

## Editor default template name

Metadata literal 17475 changes from `我的规则` to `My Rule`. ARM64 `RuntimeEventNodeEditor.ShowTemplatePage` passes this literal to `MakeInput` at RVA 0x246ff34. The GOT relocation and literal initializer are recorded in `editor-r19/default-name-report.json` in the local build workspace.

This changes the initial suggested name. It does not rename existing templates or rewrite user input. The patch verifies the prior reviewed metadata hash and checks that exactly one additional literal changed. The APK builder permits only this precise additional index/source/English tuple beyond the existing reviewed PC metadata port.

## ZombiesTD opening banners

The user's Classic 1 screenshot contains `经典塔防：进化`. PC has a partial ZombiesTD prefix mapping but no complete translation for these subtitles. Three exact rendered-text mappings now cover the related Day, Pool and Evolved variants, using existing PC game terminology. Level IDs and the original title metadata are unchanged.

The narrow related audit inspected nine level-data name getters in the original ARM64 library. It found the Evolved title and prompted review of its neighboring Day and Pool literals. This is not a claim of exhaustive coverage of every game screen.

## Verification

952 actual-Java display fixtures passed, including all three intro titles and a check that the runtime does not globally rewrite user-entered `我的规则`. Build, installation and device evidence is stored under `work/upgrade405/pre3/editor-r19`; the adjacent `level-intros-r19` directory records the source references and patch hashes.

The build includes the r18 announcement wording. See ANDROID405-PRE3-ANNOUNCEMENTS.md for PC terminology evidence and the distinction between the Cherry on Top card title and the True Cherry Bomb wording in its PC description.


Device result: r19 was installed over r17 on the S26. All nine readable nontranslation files, including both survival saves and player/garden data, remained identical through startup and the visual checks. Existing managed overrides match the APK. The My Rule field and ZombiesTD Classic: Evolved opening banner were visually verified within their bounds. No template or full custom level was saved during these checks. Private preferences are outside the shell-readable comparison.

## Magic Plantbrush freeze comparison

The English app remains alive after the menu becomes unresponsive. App-specific logs did not show a new fatal exception at the observed tap. Old crash-buffer entries predate this reproduction and are not evidence of this failure.

The untouched official Chinese 4.0.5 APK was installed separately for one controlled comparison on the same S26. Its RH package was absent beforehand. After unlocking access to Recommended Levels in this temporary installation, opening Magic Plantbrush produced the same unresponsive menu, including failure to respond to Back to Menu. The original app remained alive as PID 31952. Screenshots and app-specific logs are saved under `magic-plantbrush-audit`.

This reproduces the symptom upstream; it does not establish the internal root cause. The original code references a separate local AI service at 127.0.0.1:17861, but that dependency has not been proven to cause the menu freeze. No speculative game-code fix is included. The temporary RH installation was removed after the comparison; EN data was not removed.

## Remaining limitations

Adventure Extra parchment still lacks a usable inspected PC English overlay. Broader device sizes, crowded modes and live online content remain testing areas. Magic Plantbrush remains an upstream-reproduced known issue.
