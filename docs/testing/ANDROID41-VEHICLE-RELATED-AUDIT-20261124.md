# Related vehicle defects audit — November 24, 2026

## Findings

No additional gameplay cause of off-lawn invisibility/invulnerability was confirmed in this pass. The confirmed movement defects remain the stock held-velocity feedback and the pre6/pre7 correction's stale-Transform/current-Rigidbody accumulation. The latter is repaired by local commit `71aff7f`, not by the public pre7 APK. The original rear damage-sprite cache mixup is another confirmed related defect, already repaired in pre6; it is cosmetic and does not establish an invulnerability cause.

This pass found a diagnostic defect: the old log's `interp=0` was a fallback from a missing `Rigidbody2D.get_interpolation` method, not an observed property value. The getter is absent from the shipped IL2CPP metadata. The prefab assets have `m_Interpolate=0`, but `CreateZombie.SetZombie` and `SetZombieWithMindControl` set spawned bodies to `Interpolate` (enum 1). Thus prefab defaults cannot be used to dismiss runtime interpolation issues. The new diagnostic hooks the actual setter, calls the original setter unchanged, records its requested value, and labels it `requested_interp`; it does not pretend to read the stripped getter. Runtime initialization confirms getter availability false, and all nine trials record requested value 1.

The walking-Jackson diagnostic also emitted three `get_name` warnings while printing an intentionally null `Zombie_Jackson_outerarm_upper` sprite after damage. Each warning is immediately paired with that renderer's `ptr=0x0` record. These are classified as diagnostic formatting warnings, not game movement exceptions. The test formatter now checks for a null sprite before requesting its name. Its source guard was added after the recorded run; the raw evidence is retained unchanged.

## New code and asset review

Reviewed 128 selected methods covering the original driver family, evolved drivers, walking/quick Jackson, Jackson Universe, turn/summon logic, and relevant base damage/movement/death methods. Followed all 14 direct native call sites to the Rigidbody2D interpolation setter, including both spawn paths. Reviewed healthy damage-stage calls for collider size/offset, layer, simulation, activation and renderer changes. No new healthy-body hitbox-disabling path was identified in the reviewed code.

Inspected all physics components in the eight driver-family prefab hierarchies: ordinary/red/Michael/Worldwide vehicles, three evolved drivers, and Jackson Universe. Their enabled trigger hitboxes and kinematic simulated Rigidbody2D components are on the prefab roots. Child visual damage-stage activation therefore does not by itself disable those root hitboxes. This is a scoped asset/code conclusion, not proof that unrelated effects can never alter collision later.

The inspected SurvivalData schema saves plants and board/run data, rather than a list of live zombie transforms. No evidence was found here for a saved off-lawn zombie transform being the normal Survival restore path.

## Live validation

Dedicated Android 14 x86_64 emulator, ARM64 game via native translation, 2 CPU cores/2048 MiB. The diagnostic APK uses public EN pre7 assets and the local `71aff7f` vehicle correction. No physical device is operated. Only test-created scene actors are tracked through `CreateZombie.AddToList`, so both normal and mind-controlled creation paths are covered by cleanup. Cleanup destroys scene objects without invoking their gameplay death/summon handlers.

Nine variants were exercised: Zomboni 16, red Zomboni 18, Michael Zomboni 201, Jackson Worldwide 222, evolved drivers 321/322/323, Jackson Universe 261, and walking Jackson 10. Tests cover a small seeded vertical error at 0.1x cadence, a 4x cadence window, body damage to one-third health, facing changes, a forced row-change request, knockback and butter requests, and resumed movement. These are controlled API scenarios; an immune zombie may ignore a requested effect. They are not nine full-wave tests or an affected-player save reproduction.

All sampled positions remained finite and bounded; no off-lawn feedback divergence occurred. The slow and fast windows' maximum sampled render/physics horizontal separation was below 0.037 world units, with no observed large freeze-and-catch-up jump. All 36 explicit collider-enabled observations were true while the observed actors remained alive. Sprite world positions were also recorded. Jackson Universe's row request subsequently returned to its usual row and converged back toward that ground height; the transient row transition is not classified as divergence. The walking Jackson's diagnostic formatting warnings above are retained separately from game exceptions.

## Known Unity issues checked

The source bundle header reports Unity `2022.3.62f1c1`. Unity documents similar earlier engine defects:

- [UUM-80058, fixed in 2022.3.48f1](https://unity.com/releases/editor/whats-new/2022.3.48f1): changing 2D Rigidbody rotation with interpolation could use an incorrect position and cause movement discontinuities.
- [UUM-82789, fixed in 2022.3.49f1](https://unity.com/releases/editor/whats-new/2022.3.49f1): Transform/Rigidbody pose priority during interpolation could cause jitter.

Those official fixes precede the bundle's reported revision. That version comparison does not independently prove which fixes a particular China-branch player binary contains. Neither issue was confirmed as an additional cause by these game tests, so no engine-level interpolation/rotation workaround is shipped on that basis. A 3D Rigidbody issue with superficially similar wording was not treated as evidence about this 2D game.

The project's first 100 current/closed GitHub issues were searched for the relevant Zomboni/bobsled/invisibility/Jackson terms; no matching issue body/title was found in that set. This does not replace the user-supplied chat reports or establish that no upstream/community report exists.

## Limits and release state

ARM64-emulated runtime evidence does not validate every physical Android device, 32-bit runtime, modifier combination, animation state, renderer or frame sequence. The new tests do not establish that the latest reported screenshot was produced by a build containing `71aff7f`. No additional production gameplay patch is justified by the unconfirmed candidates in this pass. Public releases and user devices remain unchanged. Structured results accompany this report; raw evidence and corrected diagnostic sources are retained in the task's output archive.
