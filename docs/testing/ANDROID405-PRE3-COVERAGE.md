# Prerelease 3 r12: PC coverage audit

Historical r12 audit. The subsequent [r13 guide review](ANDROID405-PRE3-GUIDE.md) translates the guide instructions and node help described as pending below.

Local candidate only, not published. Installed over r11 on the S26 Ultra without uninstalling or clearing data.

- APK: `PvZ-Fusion-4.0.5-English-Android-prerelease3-test1-r12.apk`
- Version code: `4050323`
- SHA-256: `42c04e97af56b122772a9cebffd5518e8bb52ca621388977b57515a91b78dcdf`
- Base PC data: `Teyliu/PVZF-Translation`, branch `4.0`, commit `94b9ec0aecc3cea494c5b2c2883a7cbf14642440`.
- Reviewed overlay: PC `main`, commit `c7fb5997d65e1d5248f3d7a9ca9c9e0a4b516640`, October 21. All 27 downloaded JSON/text files matched their pinned Git blob hashes.
- PC handler reference: `Teyliu/PVZFusionTranslation`, commit `36dfab123f6b8ce2310317b1d5e81cd0b2a898f1`.

## Reported screenshots

| Area | Finding and action |
| --- | --- |
| Super Custom Levels / Super Level Editor | Both names match separate PC dictionary entries. Retained. |
| Brown editor button | Generic Android UI translation: Creator Guide. Fits on S26. |
| Guide close control | Changed Disabled to Close only under CreatorHelpWindow, at rendering time. Ordinary settings retain Disabled. Open/close tested on S26. |
| Long editor guide | Stored in LevelCreatorHelp, including topics and node documentation. No usable English asset or matching handler found in the inspected PC snapshots. Retained Chinese. |
| Adventure Extra book | PC includes a replacement texture for 剧情文本, but it is blank parchment. No matching English story overlay was found in the inspected dictionaries or C# handlers. Not imported, so the story is not erased. This is a source audit, not a claim about every possible PC build. |
| Gods difficulty card | Android says +2 rerolls and zombie HP x4. PC's longer sentence adds speed x1.5, which Android does not state. Used the two matching facts only. |
| Gods challenge cards | Added the 50, 75 and 100 God Coin reward lines using existing PC terminology. S26 screenshots show all three lines fit. |

## Exact change scope

1. Updated 34 almanac display fields from newer PC data. Records were aligned by numeric plant/zombie IDs, and original Chinese fields had to match the PC source. Existing Android English also had to match the prior PC wording. Two of the changes are DetailStrings descriptions. No IDs, recipes used by gameplay, costs used by gameplay, or schemas were changed. Almanac recipe text is descriptive only.
2. Applied 15 PC dictionary deltas plus seven small Android display variants. Existing Explosive Breath and Iron Curtain corrections remain. Added the composed `+ Integer` editor label separately. Two upstream `shrooom` spelling errors were corrected to `shroom` to match the almanac.
3. Updated nine already translated metadata literals using exact original Chinese slot and previous English checks. The build verifies this exact slot list and protected keys before allowing the metadata change.
4. Added 886 unambiguous original plant/zombie names mapped to the reviewed Android almanac names for display. Existing dictionary choices take precedence. This is a mapping count, not 886 newly observed untranslated screens.
5. Added 80 usable PC online-level records by stable online level ID. Catalog titles render through CustomButton_enterGame. On CustomLevelData.OnBoardAwake, known titles/opening tips are registered in memory for display. Downloaded levels, saved levels and editable fields are not rewritten. Empty, unknown and conflicting tips are preserved. No translation network requests were added.
6. Added translation of complete text spans between recognized formatting tags while retaining tags. Complete-match rules still apply. Added PC `_code` handling for three node-port labels only inside RuntimeNodeUI.

The full field/slot before-and-after list is in `coverage-r12/port-report.json`, copied to the local release folder as `audit-r12-port.json`. The repeatable patch is `scripts/port_pc_refresh_405.py`. It preserves a frozen baseline and rejects rerunning over unreviewed payload changes.

## Coverage and deliberate exclusions

Inspected all 308 embedded TextAssets, serialized TMP/Text fields, remaining Chinese metadata literals, PC exact/regex dictionaries, structured almanac/tip/modifier data, online-level records, English texture inventory and 327 PC C# files. The census collected 2,425 CJK-bearing occurrences, including internal identifiers, asset names, credits, guide documentation and gameplay data. It is not a count of untranslated UI labels. The actual Java translator processed all census inputs without exceptions and passed ten screenshot/regression fixtures.

The long guide and parchment still lack usable PC English in the inspected source. Two mechanical zombie biographies have unrelated generic PC placeholder text and remain Chinese. The reviewed Android Pyroboros Pot description and two modifier corrections were retained rather than overwritten. Internal keys in ShootingAlmanacIndex and route identifiers are intentionally not rewritten. Some dynamically assembled text, user-created levels, PC contextual effects and every layout cannot be exhaustively proven by an offline census. No claim of zero remaining Chinese is made.

## Verification

- Both ARM64 and ARMv7 builds, Java translation behavior tests (17 checks), refresh tests, regex compilation, protected metadata checks, APK signature/alignment and ZIP integrity passed.
- Compared 208,662 Unity objects against r11. Only the three almanac TextAssets changed, with exactly the 34 reviewed JSON field changes. No object was added or removed.
- Original game native libraries remain byte-identical. Only our runtime libraries changed.
- On S26: startup, Creator Guide button, guide Close control, Gods difficulty cards and challenge reward cards passed visual checks. No clipping was seen in those checked areas.
- r12 installed in place. All readable external files were identical immediately after installation. After startup, all nine nontranslation files were unchanged, including `level40.json`, `Player/Saves/level40_9999.json`, `playerData.json` and `GardenUnifiedData.json`. Existing LawnStrings and metadata overrides matched r12's payload hashes.
- The user separately confirmed that a survival save loaded after the earlier r11 refresh test. Private Android preferences cannot be hashed through ordinary ADB; earlier user tests confirmed settings/music retention.
- Online catalog titles/tips have automated tests but still need a live known-ID online-level check. Other aspect ratios, crowded modes, gameplay music/drums and broader long-session stability remain device testing items.

## Save refresh policy

No wipe-all-except-saves logic is used. The explicit translation allowlist is the three almanac JSON filenames at their supported locations, the known IL2CPP metadata override, and files owned by our private english-runtime manifest. Unknown files and all save slots remain untouched. This policy was unchanged in r12 and accommodates future save files without requiring us to predict their names.

## Quick next checks

1. Revisit the Gods difficulty and challenge cards; all reward lines should now be English.
2. Open Creator Guide, then Close. Its long Chinese instructions are expected for now.
3. Open a PC-translated online custom level and check its title and opening tip. Unknown or incomplete PC entries may remain Chinese.
4. Reopen one survival save and check your music preference. No seed installation or data clearing is needed.
