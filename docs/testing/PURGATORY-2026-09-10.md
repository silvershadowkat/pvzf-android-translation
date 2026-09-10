# Release 7 device feedback — September 10

The tester reported most checked entries looked good. Their Syzygy screenshot
shows the complete PC description fitting the panel. This is limited visual
evidence, not a complete runtime/crash test.

## Corrections for the second local Release 7 test build

- Recommended Levels card: `resources.assets` TMP 188456, hierarchy
  `Name / Window / Level_1 / HotLevelMenu`. The one-line title extended beyond
  the card. Use `The Gods: Evolved\nPurgatory`, matching PC line breaks.
- In-game footer: metadata literal 18469. PC's two-line title placed its second
  line below the screen. Keep PC terminology with a hyphen separator inside
  balanced `<size=80%><nobr>...</nobr></size>` tags. No RectTransform, font,
  gameplay, or native-code changes.
- Gacha starting choice: literal 16056 was still Chinese. An old Android
  fallback existed, but the new-3.9 policy correctly excluded it because it
  was not reviewed UI and no complete PC mapping was found. Now explicitly
  allow this simple mode-selection instruction under the user's instruction
  policy. Preserve starting Luck 50, cap 300, five random Zombie Modifiers,
  and reroll only after clearing The Gods: Evolved on any difficulty.

## Expected exceptions and navigation correction

- Death March / Undead March, literal 17651: current PC `debuffs.36` has the
  name `Undead March` but only `Buckshot Commando Zombie: ` as its description.
  Retain the complete Chinese card; do not invent the missing PC ability.
  **Later September 10 update:** PC commit `9afdca02` now supplies the complete
  description. Imported it into the next local candidate; the already-built
  test2 APK predates that import. See `PC-REFRESH-2026-09-10.md`.
- Coldsnap Insight I and II are present at literals 18938 and 18937, mapped
  from PC `advancedBuffs.1021` and `.1022`. The earlier claim that they were
  under the Epic Modifiers filter was not verified. Use All Modifiers to find
  them; the precise Android category has not been confirmed.

## Verification

The new metadata differs at exactly 16056 and 18469; all other 19,059 literals
and non-literal metadata structures are unchanged. The bundle patch reopens
and verifies all 201,406 objects, allowing only TMP 188456's string to differ;
its remaining component bytes are unchanged. All 21 existing tests pass.
APK signing/content verification is recorded separately with the local build.
Retest both Purgatory titles and the Gacha choice on Android. No GitHub
publication is authorized by these changes.
