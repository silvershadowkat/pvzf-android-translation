# Translation v24: Investment Odyssey audit

## Why this screen remained mixed-language

The current PC community translation contains English Investment modifier
descriptions in `Localization/English/Strings/travel_buffs.json`, and those
descriptions remain the source of truth. Its 42
`investmentBuffs.*.name` values are blank, though, so there were no PC title
strings for Android to import.

Android 3.8.1 builds each title from `InvestBuff.ToString()`. Those names live
in the IL2CPP definition-string heap rather than the ordinary string-literal
table scanned by the original forward audit. That explains both the English
descriptions/Chinese titles seen in screenshots and why earlier CJK scans did
not report the titles.

## Implemented correction

`scripts/build_metadata_translation.py` validates and renames all 42
`InvestBuff` fields while preserving their numeric values. It aborts if the
official 3.8.1 field name or index is not exactly the expected one. The card
descriptions still come from the PC translation.

The same metadata pass applies the PC-consistent Buckshot Commando suffix
`: -10 shots needed for ultimate`. The Princess Solarnova inspection fields
retain their official trailing newline characters so HP, damage, production
cooldown, and Lumos level render on separate lines.

## Physical-device test

1. Start Odyssey: Investment and reach each modifier-selection tier.
2. Verify every visible title and description are English in the basic, Gold,
   and Diamond pools.
3. Select several modifiers and confirm their effects still behave normally.
4. Open The Gods: Evolved and verify the Buckshot Commando Tempest card reads
   naturally with no Chinese fragment.
5. Inspect Princess Solarnova and confirm the four stat fields use separate
   lines.

The remaining physical test is presentation and gameplay validation; the
builder already verifies that no enum numeric value or executable code changes.
