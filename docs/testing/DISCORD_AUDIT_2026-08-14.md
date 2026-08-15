# Discord screenshot and video audit: 2026-08-14

## Confirmed translation work

- Investment Odyssey retains the PC community's English descriptions and adds
  validated Android titles for the 42 blank PC title fields.
- The Gods: Evolved completes the Buckshot Commando ultimate suffix with PC
  terminology.
- Princess Solarnova's four inspection fields preserve their runtime newlines.

## Optional 1920×1080 UI-position preset

Thanks to Naijen Wolfide for testing these values: bottom-left buttons X 110,
Y 80, scale 1.10; seed bank X 400, Y 0; conveyor X 400, Y 0; seed-selection
screen X 300, Y 0; plant storage X 400, Y 0; toolbar X 400, Y 0.

The values are stored per save/profile in `GameConfig.UIConfig`. They are not
made universal defaults because values tuned for 1920×1080 may be wrong on an
ultrawide display, and this project does not silently rewrite progression data.

## Large plant-list route

Tap **Recommended Levels** on the main menu, open **Super Custom Levels**,
select a level, and use its pre-level **Choose Your Plants** screen. The large
list and **Upcoming Zombies** preview belong to this special setup flow; adding
it to normal Adventure would be a gameplay/UI modification.

## 3.6.1 soundtrack finding

Joseph English 3.6.1 has the same 168 `AudioClip` names as official Chinese
3.6.1, but 18 primarily music payloads differ: `Boss2`, `Day`, `Day_drum`,
`Fog`, `Fog_drum`, `Garden`, `IZ`, `MainMenu`, `Night`, `Night_drum`, `Pool`,
`Pool_drum`, `Roof`, `Roof_drum`, `Roof_pre`, `SelectCard`, `UltimateBattle`,
and `loon`. Official Chinese 3.8.1 has 173 clips, adding five game-specific
ones. The 3.6.1 APK alone cannot establish the altered music's source or
redistribution permission, so it is not copied and no speculative toggle is
added.

## Update and 3.9 policy

APK updates replace packaged translation assets but can preserve an external
`files/il2cpp` metadata override. The project documents removal of only a
confirmed stale override; it does not add startup code that edits user storage
or saves. Migration begins only after an official Android 3.9 APK exists, with
new hashes, ABIs, IL2CPP dump, current PC data, audits, and physical tests.
