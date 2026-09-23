# Android 4.0 English prerelease 2 rev 2 candidate

Local preparation only. Not published.

- Fixed 96 translated internal class references that could leave The Gods Almanac empty, and added explicit checks to prevent recurrence.
- Corrected 14 plant descriptions against official 4.0 text, including Nugget-shroom, Icicle-shroom, Spuddy-shroom, and Squash Pumpkin. Kept established PC names.
- Verified Coffee Bean's “exempt” wording; it correctly describes the price-increase exemption and is unchanged.
- Checked PC 4.0 updates; no new upstream commits to import.
- Added context-aware English for 51 generic Gods Almanac UI fields and availability text on 70 entries. Kept established PC terminology.
- Left unconfirmed currency/tactic names and specialized descriptions unchanged to avoid misleading players.
- Maintainer confirmed the catalog fix and Nugget-shroom. Rev 2 UI testing is pending.
- Passed 46 tests, 312 runtime-format checks, catalog-reference checks, structural audits, APK comparisons, signing and alignment checks.
- Preserved gameplay, save handling, music, and executable code. Vague mode/death-sprite reports remain unverified.

[Investigation, exact corrections, and device test steps](testing/ANDROID40-PRE2.md).
