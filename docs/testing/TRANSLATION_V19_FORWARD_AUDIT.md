# Translation V19 Forward Audit

## Why the Puzzle label was missed

The earlier audit concentrated on TextMesh Pro's `m_text` field. Puzzle Mode's
`切换关卡组` label is a legacy `UnityEngine.UI.Text` component stored in `m_Text`.
The production audit now recursively inspects every readable serialized string
field, plus TextAssets and IL2CPP string literals. The label is translated as
`Switch Level Group` by the Android translation pipeline.

## Additional proactive findings

- Remaining Mechanics Almanac category `type` values are mapped by the Android
  schema adapter instead of relying on a whole-file PC replacement.
- Android-only short perk labels no longer get misidentified as undiscovered
  fusion recipes by the broad PC regex fallback.
- Mixed-language undiscovered recipes now use the current community plant
  names, including Umbrella Kale, Charm Magnet, Garlic-pult, Magnet Blover,
  Frost Gloom-shroom, Cryonic-shroom, Cherry Chomper, Magnet Cactus, and
  Gatling Cherry.

## Remaining CJK classification

The reachable serialized player-facing text inventory is clean except for
original creator names that must remain Chinese. Other serialized CJK hits are
internal animation, skeleton, font, and object names. Remaining TextAsset hits
are creator/level-maker handles or internal data/documentation. A large IL2CPP
font glyph-range table is also intentionally untouched.

Static auditing cannot prove that every conditional runtime composition is
visible and correct. Physical screenshots remain necessary for inactive
scenes, save-generated strings, textures containing baked text, and strings
assembled only after unusual gameplay events.

## Abyss

Android 3.8.1 contains dormant Abyss classes, scenes, and a Challenge-menu
button object, but that button is explicitly inactive. Abyss is parked for this
Android build and is not considered playable content. Do not expose it, add a
shortcut, or use it as a translation-completeness requirement unless the
upstream Android port officially enables it later.

## V19 phone checks

1. Puzzle Mode: confirm `Switch Level Group` at the bottom.
2. Mechanics Almanac: sample entries from every category and verify the left
   category labels and body text.
3. Locked/undiscovered plants: inspect several fusion hints, especially the
   advanced plants listed above.
4. Starbound/perk screens: inspect short stat labels such as attack speed,
   cooldown reduction, critical damage, healing, and projectile count.
5. Confirm the original Chinese creator names remain unchanged.
