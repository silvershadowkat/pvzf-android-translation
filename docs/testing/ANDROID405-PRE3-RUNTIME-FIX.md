# Prerelease 3 revision 11: runtime crash and gameplay button

Local candidate, not published. The maintainer confirmed on S26 that Tactic Modifiers no longer crashes and Projectile Info now looks good. No Chinese was noticed in their Gods Almanac checks. Crowded modes and other aspect ratios are not yet comprehensively verified.

## Report and evidence

The maintainer reported that opening Tactic Modifiers in The Gods Almanac crashes main-r10. Two existing S26 crash records have the same signature. No further reproduction or relaunch was attempted during diagnosis; the maintainer was testing Projectile Info.

The native stack enters our `parseText` hook, then `TMP_Text.ParseInputText`, `PopulateTextBackingArray` and `System.String.get_Chars`. The supposed string pointer is a stack address near the stack pointer. This matches an incorrect pointer level in our field setter, rather than evidence of an invalid Chinese tactic key.

The generic setter previously passed `&v` to `il2cpp_field_set_value` for both values and managed references. Disassembly of the pinned official ARM64 library confirms:

- `il2cpp_field_set_value` at RVA `0x1e65e80` branches to `0x1e7b5dc`. It forwards its third argument to the type-dependent writer with the indirect flag cleared. The reference branch at `0x1e7af24` therefore stores that argument directly.
- `il2cpp_field_set_value_object` at RVA `0x1e65e84` branches to `0x1e7b714`. It passes the managed object directly to the write-barrier path at `0x1ebe500`.
- TMP's `TextString` input-source enum is 3 in this Android version. That existing enum value was checked and is unchanged.

## Exact changes

- Added `runtime/field_access.h`. Value writes accept non-pointer values only, with a compile-time rejection of pointers and null-pointer values. Reference writes use the explicit object-reference API.
- Updated `runtime/english.cpp` to load `il2cpp_field_set_value_object` and use it for temporary TMP text, restored TMP text, temporary/restored legacy UI text and new UnityEvent references. Boolean, integer and Vector3 writes retain the value API. Source text is still restored after rendering; internal game keys are not translated permanently.
- Added `runtime/tests/FieldAccessTest.cpp`. It models the independently verified ABI and checks translated string identity/content, original-string restoration, null references, event references, bool/int/Vector3 values and compiler rejection of accidental pointer use in the value writer.
- Projectile Info now starts hidden and follows the original plant-health button's active state on each game update. It shares the original parent, so parent visibility and UI position/scale changes also apply. When shown, it joins the menu's collider registration while preserving the menu's interaction state.
- Removed manual positioning and forced activation for the gameplay clone. The existing `LeftButtons` GridLayoutGroup owns its placement and size. No original button is replaced or deactivated.
- The two-line Projectile Info label uses a 10 to 14 font-size range, disables additional word wrapping and stretches inside the button with an inset. Music-button formatting is unchanged.

## Layout evidence and limits

The pinned prefab has 15 existing child objects under `LeftButtons`, many hidden until needed. Its grid uses bottom-left alignment, 125 by 52 cells, vertical spacing -7 and one fixed column. Appending our button puts it above the existing active items. This explains the previously observed position above Switch Glove.

There is no five-button assumption. Extra active controls participate in the same grid. However, a tall stack at a large UI scale can still run out of vertical space. Revision 11 does not change the player's group position or scale, or invent a second layout system. Crowded modes and other aspect ratios still require device checks; automatic wrapping is not implemented.

## Validation and next device checks

The host field-ABI regression executable passed. Its negative compilation case failed with the intended managed-reference diagnostic. Both Android ABIs compiled with the same pointer guard. Standard build checks include signing, alignment, ZIP integrity, translation rules, managed-file tests and unchanged original game libraries.

The maintainer already confirmed main-r10's Projectile Info toggle works, and earlier manual seed-to-main-r9 updating corrected both stale labels while retaining progress/settings. Those are prior observations, not proof that revision 11's crash or layout fixes pass on device.

1. Open Tactic Modifiers, change tactic groups and select levels, including the maximum-tier dialog. Then sample Plant, Reinforcement, Other, Apex and Trial tabs.
2. Enter plant selection. Projectile Info should be hidden and Open Almanac unobstructed.
3. Start gameplay. Projectile Info should appear with the health controls, fit both On and Off labels, and toggle the same information as before.
4. Pause/resume, leave and re-enter a level, then check a mode with more left-side buttons and a changed UI position/scale. Report any off-screen controls or overlap.

After diagnosis, the maintainer explicitly requested installation. Main-r11 (4050321) was installed over r10 with no uninstall or data clear. playerData.json was byte-identical immediately before and after installation. PID 15533 reached the visible main-menu changelog; runtime initialization and one playing Blooms source were logged. The maintainer subsequently confirmed Tactics no longer crashes and Projectile Info looks good. Broader mode/aspect-ratio checks remain pending. Nothing was published.
