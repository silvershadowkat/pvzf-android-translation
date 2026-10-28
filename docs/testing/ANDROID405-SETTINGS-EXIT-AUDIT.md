# Settings exit investigation, 2026-10-28

Status: device-specific save-permission failure reproduced and repaired on the Retroid; the unchanged performance2 AI APK passes the final checks. This is not evidence of a general navigation regression or a universal fix.

## Reproduction and cause

The local performance2 AI APK (versionCode 4050342) opened Settings from the main menu but remained there after Back. The regular APK exited correctly on the same device.

A temporary diagnostic native library logged the original button's persistent event without replacing its behavior. `Goback` had one listener targeting `BaseMenu.PopMenu`. Invoking it raised:

```text
UnauthorizedAccessException: Access to the path
"/storage/emulated/0/Android/data/com.LanPiaoPiao.PlantsVsZombiesENAI/files/playerData.json" is denied.
System.IO.File.WriteAllText
SaveInfo.SavePlayerData
```

The AI save file was owned by ADB's `shell` user and had mode 0644. Its containing directory belonged to the AI app. The regular app's save was app-owned with mode 0660. This is consistent with an earlier ADB save import. No evidence implicates the recognizer or translation lookup in this failure. The APK update preserves saves, including existing ownership and permissions; it does not repair an externally imported file's permissions.

For the confirmed shell-owned file only, ADB changed its mode to 0660. The SHA-256 immediately before and after that permission-only operation was identical. After restarting the AI app, the same original Back listener completed, the game saved successfully, and the main menu appeared. No save reset, translation change, extra per-frame check, exception suppression, or replacement navigation handler was needed.

This repair was specific to the observed Retroid file. Do not recursively chmod app data or apply this diagnosis to every report. On the connected S26, the installed AI app was still performance1 (4050341), and its save had app ownership and mode 0660. A failure reported on that device would require its own logs.

## Navigation checks

With the Retroid file writable, the diagnostic AI build successfully completed:

- Settings opened from the main menu, then Back.
- Recommended Levels, then Back to Menu.
- Plant Almanac, then Back to the index.
- The Gods Almanac, then Back to the index.
- Almanac index, then Back to the main menu.
- Super Level Editor, Creator Guide, Close, then Back to Recommended Levels.

These are representative paths, not every menu in the game. Diagnostic artifacts and raw device logs stay under the local `work/oct28/ui-exit*` directories. They must not replace the normal player downloads.

## Final uninstrumented verification

The original performance2 AI APK was installed over the diagnostic build. Its installed `base.apk` SHA-256 was `34158c00ce48c9bf8a85ac94ae52d5316957755fb132d0b56df38c254b701d53`, matching the existing local deliverable exactly.

- Two separate cold launches: main menu → Settings → Back returned to the main menu.
- ZombiesTD Classic 1 gameplay: pause menu → Settings → Back returned to the pause menu.
- Pause menu → Main Menu → confirmation returned from the test level.
- Captured final-session logs contained no save-access exception, managed-call failure, or diagnostic callback logging.

Both Retroid packages are left on the normal performance2 APKs. No production native/Java source, translation payload, save contents or public release asset was changed by the repair. Normal subsequent in-game saves do update `playerData.json`. The S26 was inspected read-only and was not updated during this investigation.
