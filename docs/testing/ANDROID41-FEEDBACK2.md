# Local 4.1 follow-up

Standard EN report, based on public pre-release 2 (`8b871c7` source checkpoint).
This candidate is not published or device-tested.

## Music

Official Android 4.1 has three music AudioSources. `GameAPP.PlayMusic` stops
all three, but the earlier profile hook redirected only `music` and `musicDrum`.
`PreludeMusic.audioSource` therefore played the factory roof intro. Its coroutine
then started the selected roof song. This is a confirmed path that can mix
Original and Blooms, not proof that every reported Starbound repeat has this cause.

The hook now includes that exact third source. During the native `Roof_pre`
call, the game's two explicit roof `LoadAudioData` calls warm the selected stems.
They remain cached until handoff, so assigning them does not load them again.
The source selection, playback, clock, drum logic and coroutine remain native.
Only current source clips and the two explicitly warmed stems retain references.
Retired clips use the existing non-overlapping asynchronous cleanup.

No extra player, timer, per-frame scan, synchronous decoder, sound effect
translation or all-song PCM cache was added. Both Android ABIs compile.
All audio entries and original game libraries are byte-identical to pre-release 2.
The stripped 4.1 build exposes no per-clip unload API, so general cache retention
was not expanded. Cold non-roof transitions may still wait for background decode.
The reported half-second delay and Starbound repeat still need device measurement.

Native evidence: `PlayMusic` at `0x22FA668`, `PreludeMusic.OnActive` at
`0x233EB50`, its coroutine at `0x233ED28`. `Roof_pre=12`, `Roof=10`,
`Roof_drum=11`. `AudioClip.LoadAudioData` at `0x46BF9A4` does not read MethodInfo.
Runtime lookup uses named metadata fields and methods, not these offsets.

## Text

Reviewed Blooms commit: `38129198512e7d97aec2552be636578cad20dc24`.
Official PC and Android source descriptions match for plants 1469 and 1487.
Use Blooms names, prose and terms, retaining explicit source mechanics that its
current description omits. Do not introduce the extra main-body 50 damage claim
for Mandiboulder that is absent from this 4.1 description. Existing names,
flavor text and recipes stay unchanged.

The Absolute Immunity card now handles the real bullet/newline template.
Its effect follows the source: immunity to most status effects; if unselected,
Professor Cherryz gains one spare newspaper. The different Unbridled Rage I/II/III
cards retain their identities. The score card's numeric effect is translated;
its unverified specialized title `落袋为安` remains Chinese.

Only metadata display slots 18115 and 20048 change. All 32 present protected
slots remain intact. Only the LawnStrings TextAsset changes among 219,584 bundle
objects. No gameplay names, keys or save structures change.

## Plant Info and Lumos

Public pre-release 2 already contains the stat-parser repair and Lumos display
translation. The supplied merged-card images resemble the old parser defect.
Screenshots alone do not establish the installed package revision or its file
overrides, and are not evidence that the tester modified the wrong files.

Original `GetPlantInfo` reads `Plant.currentLightLevel` and includes the Lumos
line only when the value is at least 1 (`0x23A9E3C`). Preserve this behavior.
Do not add a fabricated zero-level stat or change a plant's light value.

## Verification

- 75 Python checks pass.
- Actual C++ music hooks pass intro handoff, warm reuse, both profiles, missing
  replacement fallback, sound effect isolation and 100 repeated transitions.
- Actual Java translator passes 76 fixtures and 17,154 parity inputs.
- Managed refresh checks preserve save/settings/unknown fixtures.
- Signed APK verifies both ABI libraries, certificate, package, version and
  16 KiB alignment. Its exact eight-entry delta is recorded in the build JSON.
- S26 `R5GL14CN45N` was unavailable through ADB. No other device was accessed.

Reproduce with `apply_41_feedback2.py`, then `build_41_feedback2.py` using the
immutable pre-release 2 Standard APK and `assets/feedback2-4.1-review.json`.
The latter builds a local candidate only and never installs or publishes it.
