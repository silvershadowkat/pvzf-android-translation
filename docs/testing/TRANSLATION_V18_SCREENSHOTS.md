# Translation V18 screenshot review

This batch contained 13 screenshots. The translation changes are made in the
shared payload builder and were packaged for an Android translation test pass.

Candidate APK: `outputs/PvZ-Fusion-3.8.1-English-Translation-Test-v18.apk`

- Size: `551152210` bytes
- SHA-256: `aa00d4ad52bb04f634a621fee241d337ac23e63862fcf9b7dd4fccd76f22793e`

| # | Screen | Finding | V18 action |
| ---: | --- | --- | --- |
| 1 | Android Plant Almanac | Affinity values were Chinese enum names. | Translated all 18 `SynergyType` names, not only the three visible on Gatling Cherrybomber. |
| 2 | PC Plant Almanac reference | PC currently omits the Android affinity row. | Used the PC community's authoritative synergy terminology while preserving Android's feature. |
| 3 | Note Editor, stopped | `歌曲` remained before the song name. | Added the Android runtime fragment `Song:`. |
| 4 | Note Editor, playing | `歌曲` and `时间` remained in the live header. | Added `Song:` and both runtime `Time:` formats without changing placeholders. |
| 5 | Vasebreaker PVP | `蓝飘飘fly (Bilibili)` is an original creator credit. | Intentionally preserved as a proper name. |
| 6 | Vasebreaker PVP turn assist | The turn-start and Gift Box instructions were Chinese. | Translated both turn-start and remaining-moves runtime formats. |
| 7 | Odyssey save picker | A 3.7 save's stored default name was Chinese. | No save mutation. New slots already use `New Save File`; rename a legacy slot in-game. |
| 8 | Zen Garden purchase | The successful purchase destination was Chinese. | Translated the page/row/column format while preserving all three runtime indices. |
| 9 | Garden Defense selector | Selector cards appear over the active garden scene. | Reviewed as an in-scene selector; retained the existing ultrawide modal-background correction. |
| 10 | Garden Defense report crop | Duplicate evidence for screenshot 9. | No speculative behavior patch. |
| 11 | Modifier Almanac | Selected card says `Cannot be upgraded`. | This is the static upgrade-availability label; no translation defect found. |
| 12 | Modifier Almanac selected state | Card turns green but the availability label remains. | Green is selection highlighting, not proof that an upgrade became available; unchanged. |
| 13 | Pause menu | `View All Modifiers` availability was unclear. | Reviewed as a modifier-enabled-level feature; no translation defect found. |

## Physical test checklist

1. Open several plants with different affinity combinations and confirm every
   value after `Affinities:` is English.
2. Open the Note Editor, then start playback, and verify both stopped and live
   headers contain no Chinese `Song`/`Time` labels.
3. Enable Vasebreaker PVP turn assist and advance through both players and
   multiple remaining-move counts.
4. Buy a Zen Garden plant and verify the destination page, row, and column.
5. Create a new Odyssey Cursed Purgatory save and verify `New Save File`.
   Separately confirm an existing save is unchanged and can be renamed through
   `Rename Selected Save`.
6. Exercise a synergy/affinity mode once to confirm the enum-name presentation
   change did not affect numeric gameplay membership.

## Audit limitation discovered after V18

The first follow-up Puzzle Mode screenshot exposed `切换关卡组` in a legacy
`UnityEngine.UI.Text` component (`m_Text`, path ID 186732). The earlier audit
only inspected TextMesh Pro's lowercase `m_text` field, so its statement about
serialized UI coverage was too narrow. V19 translates this button as
`Switch Level Group` and expands the audit to recursively inspect every string
field in every readable serialized `MonoBehaviour`, including both legacy Text
and TMP components. It also reports unreadable typetrees that contain possible
UTF-8 lead bytes for manual review instead of silently skipping them.
