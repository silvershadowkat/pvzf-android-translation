# Almanac visibility audit, October 28, 2026

## Finding

There is an upstream change between 3.9 and 4.x that explains why many more
Suburban Almanac plant cards can be visible without encountering the plants.
This is not evidence of completed levels or an accidentally bundled unlocked save.
The tester's precise fresh-profile state is still unconfirmed.

In 3.9, `AlmanacCardUI.set_PlantType` displays a plant when
`Lawnf.CheckIfPlantUnlock` returns `UnlockType.Unlocked` (0), or when the plant
is in `GameAPP.config.meetPlant_runTime`, or developer mode is enabled.
The general unrestricted case returns `UnlockType.NotLimit` (2). That case
does not pass the first display condition, so an unencountered plant stays hidden.

In the original 4.0 and 4.0.5, the first condition instead calls
`PlantDataManager.IsUnlocked`, which returns a Boolean. The general unrestricted
case in `CheckIfPlantUnlock` returns true. Those plants are therefore visible
even when the encountered list is empty. The encountered-list and developer-mode
checks remain additional ways to reveal a card.

This is a display eligibility change. It does not imply that adventure,
survival, or The Gods: Evolved progression was granted. The Gods Almanac also
has its own unlock data and must not be conflated with the Suburban Almanac.

## Verification

Compared original Chinese `pvzrh4.0.5.apk` with the published regular performance
candidate. These ARM64 method bodies are byte-for-byte identical:

| Method | RVA | Bytes compared |
| --- | --- | --- |
| AlmanacCardUI.set_PlantType | 0x24af990 | 600 |
| PlantDataManager.IsUnlocked | 0x21c66a8 | 304 |
| PlantDataManager.UpdateUnlockStatus | 0x21c67d8 | 288 |
| PlantDataManager.CheckIfPlantUnlock | 0x21c697c | 4344 |
| GameConfig constructor | 0x22f94e0 | 820 |

The GameConfig constructor creates empty encountered-plant collections. The
APK inventory contains no playerData, gameConfig, PlayerPrefs, save.dat, or
settings.json payload. This filename check alone is not proof about every data
source; the native control-flow comparison provides the specific explanation.
The translation runtime does not hook these unlock methods or populate these
collections.

The 3.9 reference is the retained 3.9 native dump/library used for prerelease 9.
The decisive 3.9 display branch is at 0x2393cbc-0x2393cc0; its unrestricted
return is at 0x2218674. In original 4.0.5, the corresponding display branch is
0x24afa80-0x24afa84 and the unrestricted true return is 0x21c7198.
These addresses are audit evidence only and are not runtime patch offsets.

## Decision

Preserve original 4.0.5 behavior and all player progress. Do not erase saves or
restore 3.9 discovery restrictions as a supposed translation repair. A matched
fresh-profile comparison on Chinese and English is still useful to confirm the
tester's exact observation; it has not yet been performed for this report.
