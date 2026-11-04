# Android 4.1 first tester-feedback audit

November 4, 2026. Local branch `agent/translation-4.1-feedback1`, starting from published pre-release 1 r4 and publication checkpoint `2f46155`. The signed candidate is `4.1-English-pre1-r5`, version code `4100104`. It is not installed, device-tested, pushed or published. See [the build record](ANDROID41-FEEDBACK1-BUILD.json).

## Recognition service investigation

The released APK SHA-256 is `27ed3d62353c43c585400efee8d0808c83deb52403ca858709400cbfb44abea3`. All original native libraries are byte-identical to official Chinese Android 4.1. The `MaLiangService` TextAsset is also byte-identical, including its endpoint/authentication configuration. Configuration values and credentials are deliberately omitted here. The translation runtime does not hook `MaLiangLocalRequest` or submit recognition requests.

Official ARM64 `MaLiangLocalRequest.Read` at `0x200CC94` maps both HTTP 429 and HTTP 503 to active metadata literal 20211, `识图服务繁忙，请稍后重试。`. Our English rendering, “The recognition service is busy. Try again later.”, accurately translates that shared message. The screenshot cannot distinguish the two responses or establish the service's load at the time. Client logs or the actual response status would be needed to identify the individual incident.

The official request path sends PNG data asynchronously with a 30-second timeout. `MaLiangMenu.Parse` returns when a request is already present and disables Identify after submission. Completion calls `StopRequest`; exit/disable also dispose the request. There is no added automatic retry loop, local model, duplicated request bridge or background recognition worker in this release. Increasing retries would risk adding load to a service already returning a busy/rate-limit response. No service requests were made during this audit, and no network behavior is changed in the candidate.

## Screenshot findings

| Screenshots | Finding | Disposition |
| --- | --- | --- |
| 1 and 2 | Plants 5008 and 1498 lack completed Blooms names and descriptions. Their Chinese names are also present in the released almanac. | Genuine remaining coverage, not evidence of a wrong APK. Translate explicit prose/effects using verified terms; retain unverified plant/modifier names. |
| 3 and 5 | Plant Info headings remain Chinese, and attack interval merges into Attribute Count. | Confirmed in the released metadata and native parser. Fixed in the local candidate. |
| 4 | Recognition busy message is accurate; the drawing hint and mixed Pencil footer remain Chinese. | Preserve the real error. Translate the static hint and bounded footer display. |
| 6 and 9 | Plantern/Triplantern, HP and other controls are Chinese despite their English values existing in the published payload/runtime. | These images differ from the mixed-language captures. A Chinese/different build, inactive runtime or altered/stale files are possible; screenshots alone do not prove which, or prove user modifications. |
| 7 and 8 | Plantern's translated attack-speed text merges into Attribute Count; HP is also shown in Chinese. | Parser defect is confirmed. HP already has a runtime mapping; verify that separately on an unmodified candidate rather than changing gameplay data. |

Latest Blooms 4.1 was checked at `0ff6906929dfb119b52799267cd0393d26b9e058`. Plants 1498 and 5008 remain incomplete there, and both are absent from its older Dumps. Their complete actual PC/Android 4.1 source records match. New contextual fields have individual source/previous-value SHA-256 guards. This is a targeted feedback patch, not an import of all newer Blooms changes; the base translation pin remains `5a415154d81243771d75e2dd90ae14ae79d52632`.

Established names reused include Fume-shroom, Squash, Squash-nut and Mag-nut. The names `窝瓜大喷菇`, `磁能窝瓜坚果`, `窝爱砸` and `窝爱吸` remain Chinese. No English compound plant or modifier names were invented. The two plants receive readable effect descriptions and faithful flavor prose; numbers, targeting conditions and recipes follow the actual source. Future complete source-aligned Blooms fields take priority.

## Stat parser defect and correction

`PlantDataMenu.GetPlantInfo` (`0x23A97EC`) assembles text from 15 templates. `BuildModernStats` (`0x23AC24C`) splits on LF (`0x23AC3E0`) and finds U+FF1A (`0x23AC424`) to extract each card's label/value. Several previous translations changed that colon to ASCII and removed the trailing newline. The combined intermediate text could therefore lose cards or turn the preceding stat and Attribute Count into one label.

All 15 templates are now protected as parser inputs. Fourteen translated active slots are restored to the exact official source; the unchanged Attribute Count template is also guarded. English is applied to the final labels/values through the existing TMP display layer. A narrow PlantDataMenu-only override resolves `伤害增幅` as Damage Bonus while preserving the general Blooms modifier wording elsewhere. There is no new hook, per-frame correction or scene scan.

Actual .NET formatting and separator tests reproduce the defect and verify the corrected templates:

| Case | Released cards | Candidate cards | Expected |
| --- | ---: | ---: | ---: |
| Beamshooter, interval and counter | 1 | 2 | 2 |
| Plantern, speed bonus/counter/Lumos | 1 | 3 | 3 |

## Verification

- 75 Python tests pass, including the parser/protected-metadata regression.
- 64 actual-Java display fixtures pass, including original/mixed Gods cards, both Chinese/English busy-message prefixes, stat labels, footer, unknown-name preservation and bounded numeric seconds.
- Translation/cache checks pass against the frozen 4.1 released Java engine: 17,136 inputs. Prefix semantics avoid 134,741 of 166,750 sampled matcher creations. These are host checks, not a device FPS benchmark.
- The host harness now accepts a game-version baseline, loads recipe-name provenance for both engines and selects the current 4.1 fixtures. Historical 4.0.5 offline-recognition/modifier expectations remain available in the legacy mode. They are not substituted for the changed online-service wording.
- Exactly two of 219,584 serialized objects differ from r4: `resources.assets:3670` (LawnStrings) and `resources.assets:209450` (drawing hint). All other objects, including audio and service configuration, are unchanged.
- Exactly eight non-signature APK entries differ from r4: version manifest, metadata, Unity bundle, managed manifest/dictionary/LawnStrings, and the two translation runtime libraries. Game native libraries, Java runtime DEX, original classes, resources and music payload remain unchanged.
- Both ABI builds, signature/certificate, 16 KB alignment, manifest, changed-entry allowlist, protected active slots and managed payload hashes pass.
- Actual signed r4-to-r5 fixtures pass 4 metadata and 12 almanac restoration cases across storage roots/profiles, including repeated restoration of old backups. Save/settings/unknown fixtures remain intact.

No phone was accessed. Device layout, actual popup card arrangement, gameplay and longer-session performance remain to be tested. No claim is made that the tester modified files or that every slowdown is fixed.

Local evidence is under the continuation chat's `work/feedback41/`: recognition/native disassembly, source and released record comparisons, hashed Blooms snapshot, object diff, Java fixtures, .NET parser results, package logs and save-restoration checks. The original nine screenshot paths are in this chat. Do not publish extracted game data or credentials.
