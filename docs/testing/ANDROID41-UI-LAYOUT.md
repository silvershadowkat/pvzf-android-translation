# Android 4.1 camera and UI-position typography review

Publication follow-up: final ENr7 and ENAIlocal4 were published unchanged as [4.1 pre-release 2](https://github.com/silvershadowkat/pvzf-android-translation/releases/tag/v4.1-release-2) on November 4, 2026. See [the verified publication record](ANDROID41-PRE2-RELEASE-BUILD.json). The dated candidate checks below retain their original scope.

November 4, 2026. Local branch `agent/translation-4.1-ui-layout`, based on `3e51b38`. No publication or global camera override.

## Black space around the field

The official 4.0.5 and 4.1 ARM64 `GameConfig` constructors initialize `cameraSize=5`, `canvasMatch=1`, `gameSpeed=1`, and `snapassqutch=3.3`. These values are decoded from the actual packed constructor constants, rather than inferred from a screenshot. The corresponding OptionBtn.AdjustCameraSize handlers use the same 5/6/7 cycle and save the selected camera size. A larger number shows more world, making the field smaller on screen. The empty space beyond the background is black.

The retained S26 backup from the earlier tests had size6. At this review's live comparison, Settings showed size7. With Screen: Default and the physical 2340x1080 surface, changing 7 to5 visibly fills the daytime field's height;6 and7 progressively expose larger margins. This is camera framing, not evidence of a changed stock default or a translation-created border. Scene composition and screen aspect ratio can still affect visible margins in other modes. Screen: Stretch is a separate resolution option and was not used for this comparison.

The exact initial live value7 was restored using the game's own controls. All eight saved JSON hashes match the backup taken immediately before that comparison. No global default, saved UI positions, canvas scale or automatic zoom behavior was changed. Local evidence includes both versions' native disassembly, constructor constants, three live framing screenshots and the save comparison.

## Customize UI Positions

All thirteen field captions used independent TextMesh Pro auto-sizing, with minimum18, maximum72 and base36. The serialized current sizes also differed, from25 to35.7. Short English captions therefore grew much larger than the longer ones. The numeric inputs and page title are separate UI roles.

The fix sets every one of those thirteen captions to a fixed size24 and disables auto-sizing for them. Font identity, complete label wording, wrapping, alignment, materials, inputs, numeric values, event handlers, RectTransforms and serialized player settings remain unchanged. No runtime polling or hook is added. `assets/ui-positions-4.1-review.json` binds exact base-bundle SHA-256, object IDs, original typography and full hierarchy. `scripts/fix_41_ui_positions.py` rejects a changed base/schema and validates complete round-tripped component trees.

Every one of219,584 serialized objects is compared. Exactly13 caption components change; all other219,571 objects remain identical. The only modified component fields are m_fontSize, m_fontSizeBase and m_enableAutoSizing. Relative to regular ENr6, the new APK differs only in its Unity bundle, revision manifest and Android version manifest; native/Java code, translations, metadata, music and model behavior stay the same.

The new regular artifact is `PvZ-Fusion-4.1-English-feedback3.apk`, code4100109, name4.1-English-pre1-r7. Its companion uses the existing ENAI identity, code4100110, name4.1-English-pre1-ENAI-local4, file `PvZ-Fusion-4.1-English-ENAI-local4.apk`. Detailed package hashes/checks are recorded in the adjacent BUILD file. The maintainer explicitly approved updating both on the S26 despite the paused round, which restarts the application. Existing saves and current player settings are preserved.

Both updates install successfully on the S26 using the existing package identities and certificates. All eight EN and two ENAI saved JSON hashes match their respective pre-update backups. The regular EN screen is visually verified: all thirteen captions have the same size and remain readable without clipping or overlap. Numeric values and their positions are unchanged. ENAI is installed but not separately opened in this follow-up; its shared caption payload is audited, and its Java/native/model bytes match the previously tested local3. The phone is left on the corrected regular EN screen for maintainer review. No runtime/font scan is added. Seventy-five Python checks pass; no broader replay of unchanged recognition/music tests is claimed.

The public pre-release1 release is unchanged.
