# Translation v20  -  Vasebreaker PVP

This translation test build addresses the dynamic text reported in Vasebreaker PVP.

## Corrected runtime strings

- `RMB for Vase (I) (OFF)` / `(ON)`
- `Random Seedslot (O) (OFF)` / `(ON)`
- `A zombie crossed the line. {player} gains 1 move.`
- `No moves remain. Continue breaking vases, or press Enter to end the turn.`
- `{player}, you have no moves left.`

The existing translated turn-start and remaining-moves messages were retained.
Creator handles and credits remain unchanged.

## Phone checks

1. Toggle **RMB for Vase** off and on; verify both English state suffixes.
2. Toggle **Random Seedslot** off and on; verify both English state suffixes.
3. Let a zombie cross the red line and verify the entire sentence is English,
   including clean spacing around the current player name.
4. Exhaust the available moves and check both alternate no-moves prompts.
5. Confirm the plant-storage panel still opens and the mode continues normally.

## Build audit

- Package ID: `com.LanPiaoPiao.PlantsVsZombiesRH`
- ABIs preserved: `arm64-v8a`, `armeabi-v7a`
- Manifest, DEX, resources, and native libraries match the official base.
- Only `data.unity3d` and `global-metadata.dat` differ, as expected for the
  English translation payload.
