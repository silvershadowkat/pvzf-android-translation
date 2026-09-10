# Release 7 detailed translation and feedback review

**Release 7 detail archive.** The tested APK is approved for prerelease publication. These changes still
need testing on Android devices. This list covers changes since Release 6.

## Translation updates

- Imported the September 10 PC update completing **Undead March**: **Buckshot Commando Zombie: Now ignores plants when moving**. This card no longer needs to remain Chinese.
- Imported PC's corrected **Game Speed** label and matching rule, preserving the displayed number and closing its size tag for Android.
- Updated the English translation using the completed PC 3.9 community translations, including the reviewed September 9 modifier and recipe updates.
- Renamed **Shooty-shroom** to **Speedy-shroom** and updated its Almanac text to match the PC version.
- Corrected **Doomspike-shroom** to **Glacier-shroom** in the affected challenge title and talent unlock description.
- Added the PC English descriptions for both affected **Death Star** Almanac entries, which had incorrectly remained in Chinese.
- Added **158 English level tips** that were already translated in PC but missing from Android. Checked all 174 bundled level-tip records; every gameplay instruction is now English. Chinese contributor names in the Melon Morph credits are kept as PC wrote them.
- Updated the explanation of **Second Copy** so it no longer uses the older “Carbon Copy” name.
- Updated four talent names to match PC: **Sunny Day I**, **Sunny Day II**, **Sunny Day III**, and **Solar Bonus**.
- Added the completed PC translation for the **Kelptain Goldbeard / Sea-greed Zombox** Odyssey/Purgatory unlock card, which remained Chinese in Release 6. It now uses the same names as the Almanac and PC's **Plant Giftbox / Zombie Giftbox** wording. The older “Ultimate Greedy Kelp / Ultimate Greedy Boxgrass” wording reported in screenshots is not used in the corrected card.
- Translated **Tyrannoflora Lux (951)**'s remaining Chinese gameplay description and modifier details using PC's English. Its note about a bugged modifier had mistakenly caused the whole section to be treated as unfinished; that PC note is included in the translation.
- Corrected the **Firnessence Panacea (5004)** Odyssey/Purgatory unlock card to match PC and the Almanac: **Firnurse + Aloe Nivea**. Removed the old “Ultimate Little Pine Furnace” wording and the unnecessary undiscovered-plant message from that card.

- Updated modifier text across **all categories**, including full SP Evolution, Kelptain/Firnessence, curse, ascension, synergy and zombie descriptions. The review covers 455 modifier/unlock strings, including all 384 combined modifier cards. Names such as **Jinxed**, **Expert Fast-track**, **Bullet Hell**, **Deadeye**, and **Gamble of Bounty** now use the full PC entries.
- Restored five modifiers to Chinese where the historical English had no complete matching PC source. Incomplete or mismatched PC ability descriptions remain Chinese; no gameplay details were invented.
- Added PC conversion instructions to 22 other unlock descriptions and refreshed the affected Cherrybomber Drone, Habanero Weeper and SP Phoenix Drone Almanac recipe fields.

## Other text corrections

- Fixed the **The Gods: Evolved - Purgatory** title layout: two lines on the Recommended Levels card and a smaller single line on the in-game footer. The tester recheck reported improvement; broader device testing remains welcome.
- Translated the **Gacha Modifiers** starting-choice instructions (starting Luck, Luck cap, five random modifiers, and when they reroll). This is a reviewed Android instruction translation; a complete matching PC entry was unavailable.
- Translated the remaining **Damage Share**, **Total Modifiers**, **Current Luck**, **Zombie(s)**, **Difficulty Points**, random speed-bonus, and **Trial** labels on the Odyssey upgrade screen. These are simple interface labels; PC wording was reused where available, with reviewed Android wording for labels PC has not completed.
- Corrected the out-of-stock purchase message so the **item name and price appear in the right places**.
- Removed the stray **“None”** from the Wall-nut Billiards title.
- Updated the turn-start message to match PC, including the remaining moves and where Giftboxes/plants can be placed.
- Updated damage and speed bonus messages and the explanation of **Luck** to match the PC wording.
- Matched the PC wording and formatting for selection counts, save IDs, the remaining-time display, total damage, damage and attack-interval labels, and page indicators.

## More careful translation updates

- Improved how newer PC translations replace older Android wording, including text that was already in English.
- Added checks to prevent a short translated phrase from replacing an entire description, or a stat bonus from being mistaken for a plant-fusion recipe.
- Improved the check for unfinished PC descriptions so legitimate shared descriptions and reviewed contributor credits are accepted, while subject-only descriptions remain rejected.
- Repaired malformed color/size tags in two showcase tips and one newly imported recipe field without changing PC wording.
- Added checks that translation edits preserve the existing game data, fonts, layouts, artwork, and audio.

## A note about the Sea-greed Zombox recipe request

We acknowledge the request to make Sea-greed Zombox's conversion recipe clearer by adding Kelptain Goldbeard to the instructions. We checked both the original Chinese game text and the PC English translation: both use the same short giftbox-to-giftbox conversion, and our plant names match PC. Our goal is to match the PC translation project as closely as possible, so we have kept its recipe wording rather than adding an explanation that PC has not adopted. We can revisit this if the PC project updates its explanation.

## Other feedback checked

- **A.L.E.C. (309):** checked and kept unchanged. This is the PC project's name for the armed Chomper, short for **Arsenalized Long-range Elite Chompzilla**; it is not an Android naming mistake.
- **Penny-shroom (1446) — “Written by Doot”:** we checked this report and confirmed that the credit is included in the current PC translation. It has been kept to match PC; the feedback has not been overlooked.

- **Repeated modifier names and level punctuation:** PC intentionally uses 6 Crisis, 14 Nemesis and 5 Majestic Presence entries, and “(Level 1)” versus “Level 2” for Coldsnap Insight. Kept unchanged.
- **Icicle-shroom (1035) and Ultra Mecha-nut (310):** Android matches PC, but PC’s timing/healing wording differs from the original Chinese. We are retaining PC English as the authority for now and documenting both discrepancies for upstream review.

## What still needs testing or review

- **No new crash fix is claimed yet.** Check Almanac browsing, especially Penny-shroom, Cattail Girl, and the SP Phoenix plants, as well as the changed challenge, talent, level-tip, and shop screens.
- Check that the updated text fits its boxes, displays correctly, and does not cause crashes during normal play.
- Broader menu wording, the hidden Quick Hands I label, and the Fertilizer/Super Fertilizer naming question remain under review. They are not included as completed fixes.
- **Shield modifier card on the Odyssey upgrade screen:** its title and description still appear in Chinese. PC names it **Enchanted Shield**, but has not translated its description yet, and Android includes an extra immediate 6,000-shield effect absent from that PC description. We have kept the whole card unchanged pending a complete, matching PC translation, to avoid inventing or leaving out ability details. This report has been checked, not skipped.
- **Modifier names appearing as descriptions:** all reported families were checked, and the completed PC records—including Heal Leeching, Curse of 1 4 3 7, Exsanguination and Ascend: Decryption—are now imported. Every combined modifier has a nonempty title/body with Android’s separator preserved. In-game rendering still needs testing.
- **Odyssey rounds stuck with zombies remaining and performance feedback:** investigated and recorded, but not reproduced. No gameplay fix or optimization is claimed. The game warns that its optional projectile-damage display has a major performance cost; native game code remains identical to the original Chinese APK.
- **Custom Level List names:** the reported Chinese names were not found in the inspected bundled title fields and appear to come from loaded level files. Those files are needed to verify their titles. English menu controls remain unchanged.
- If PC has not completed a plant or ability name, recipe, or gameplay description, we will say so instead of inventing English. Simple interface labels may be translated after review. Other historical Android wording is preserved except the five explicitly reviewed modifier restorations above.

<!-- Maintainer instructions:
This is the single running player-facing release-notes draft. Update it as
each tester correction is made. Consolidate related fixes and list each change
once; do not copy Release 6 fixes into this list as new work. Keep planned or
unverified items out of the completed sections. Use everyday game terms and
keep implementation details in ENGLISH-PARITY-2026-09-06.md or later audit
notes. Recheck status and device-test claims before publishing. Updating this
draft does not authorize packaging or publishing a release.
-->
