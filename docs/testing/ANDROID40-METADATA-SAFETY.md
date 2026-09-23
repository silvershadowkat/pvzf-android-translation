# Android 4.0 protected metadata review

September 22, 2026. Based on published `v4.0-release-2`, commit `84c8666657100c67bed563eea75bb7a880bb0738`. Branch: `agent/translation-4.0-metadata-safety`. This review prepares a local diagnostic candidate only. The GitHub release remains unchanged.

## Result

A developer supplied 31 exact strings that Gods: Evolved may use as runtime keys. Direct inspection of official 4.0 and both published English APKs found 17 as standalone metadata literals. Thirteen were already unchanged; four were translated in both prerelease 1 and prerelease 2:

| Literal slot | Original | Published English |
|---|---|---|
| 16742 | 升级 | Upgrade |
| 18864 | 试炼： | Trial: followed by a space |
| 17502 | 护盾保护 | Enchanted Shield |
| 18309 | 爆炸保护 | Blast Protection |

The diagnostic APK restores exactly those four slots. God Coins, all other literal values, the Unity bundle, music and native libraries remain unchanged from prerelease 2. Some labels supplied directly by these literals can consequently appear in Chinese. Verified display-only Almanac translations can remain English. Do not add a global runtime replacement to hide these labels.

The remaining 14 reported strings are absent as exact standalone literals in this Android build. Some occur within longer strings or as type/resource identifiers. Absence from the literal table does not establish that a name is unused. The complete 31-string protection set is maintained in `scripts/protected_metadata.py`; existing catalog type, ID and resource-path protections remain necessary.

## Evidence and limits

Static inspection used the official ARM64 `libil2cpp.so`, matching type dump and active metadata slots. It is not a device reproduction.

- `UpgradeBuff.get_Title` at `0x241cb48` returns slot 16742. `RogueShooting.<ReinforcePlant>d__11.MoveNext` at `0x241a164` uses the same slot in a string equality call at `0x241a548`. This confirms a logic-sensitive title, but translating the same literal on both sides does not itself prove a failure.
- `ShootingManager.RegisterOtherBuff` at `0x23f8268` supplies the shield and blast titles to option registration. This alone does not prove either title causes empty choices.
- `ShootingManager.RefisterMissionBuff` at `0x23f9228` splits a source description on the original Chinese colon and prepends slot 18864. The delimiter remained original. The translated prefix alone is not a demonstrated crash cause.
- Choice recording uses title keys. Cross-version or saved-state mismatches are a concern, but no saved-state failure was reproduced. Do not rewrite saves based on this review.

The reporter's screenshots show an empty `Page 0/0` modifier menu and multiple plants, with no starting difficulty choice. The maintainer confirmed these screenshots came from an earlier version. The known prerelease 1 catalog corruption is a relevant lead: `RogueShooting.OnAnimUIOver` calls `CanSelectPlant`, which reaches `get_PlantUnlocks` and `ShootingAlmanacCatalog.Build`. `ShowBuff` also reaches the catalog through `RegisterCoreBuff`. The 96 corrupt class references repaired in prerelease 2 could therefore affect startup and modifier choices as well as the Almanac. We have not established the reporter's exact failure path or reproduced it in current prerelease 2.

## Guard and rebuild procedure

The metadata translator and subsequent UI passes preserve protected original keys. The APK packager checks active literal slots against the official same-version APK before creating output, so later overrides cannot silently bypass protection. Searching the raw file for retained Chinese bytes is insufficient because obsolete string bytes can remain after a rebuild.

For an existing prerelease 2 payload, restore into a new file after the final metadata UI pass:

```powershell
python scripts/protected_metadata.py --official <official-global-metadata.dat> --candidate <pre2-final-metadata.dat> --output <new-safe-metadata.dat> --report <restoration.json>
```

Use the new metadata with `scripts/package_apk_payload.py`, the official 4.0 APK shell and the unchanged prerelease 2 bundle/music. Follow the existing alignment and signing procedure. The helper refuses to overwrite the restoration output. Do not apply substring-wide restoration: ordinary UI prose containing a protected word is not automatically a runtime key. Future versions need renewed call-site and catalog review rather than assuming this list is exhaustive.

## Verification and delivery

See [the build record](ANDROID40-METADATA-SAFETY-BUILD.json) for hashes and artifact details.

- All 54 repository tests passed, including six new protection tests covering duplicate slots, stale bytes, display-only translations and the packaging gate.
- Exactly four active metadata literals differ from published prerelease 2. Metadata structural content outside the rebuilt literal table/data is preserved.
- All 17 present protected literals match official Chinese in the signed candidate.
- APK signatures v1, v2 and v3 and alignment verified using the existing certificate.
- Outside signing entries, only metadata differs from prerelease 2. Against the official APK, only the established metadata, Unity bundle and music payloads differ.
- No device gameplay test, emulator run or GitHub upload was performed.

Local filename: `PvZ-Fusion-4.0-English-Android-prerelease2-metadata-safety-test1.apk`.

SHA-256: `8d9440a4d257a9b92c11b9f2d460824b37407e6a58a8a4a0f5962b23e9c63ff4`.

First retest the reported starting-choice and modifier sequence on published prerelease 2, preserving existing saves. If it still fails, compare the local diagnostic candidate using the same steps and record the exact APK, device, selections and logs. Do not advertise this precaution as a confirmed instability fix without that evidence.
