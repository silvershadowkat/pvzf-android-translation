# Prerelease 3 revision 2 startup repair

## Confirmed failure

On 2026-10-21, the maintainer's S26 Ultra (SM-S948W, ARM64, Android 17) crashed when launching the original refresh-seed APK. Both original prerelease 3 variants contained the same affected runtime code and are withdrawn. They are retained under the output folder's `withdrawn-r1` directory for investigation only.

The process log at 13:51:28 shows successful managed-file refresh and dictionary loading. The first fault is SIGSEGV on the runtime initialization worker, with `libpvzfenglish.so initialize()+1216` in the stack. Symbolization maps that call to the premature `il2cpp_thread_attach`. UnityMain was still inside `il2cpp_init`; its subsequent SIGABRT is a secondary failure in the same process.

The original guard waited for a non-null domain and more than 50 published assemblies. Those conditions can become true before IL2CPP's thread/runtime initialization completes. This is an implementation bug in the added runtime, not evidence of a stale cache or dependency on the old Chinese package. The host tests did not exercise the startup ordering on ARM.

## Exact repair

- `EnglishActivity.java`: load libil2cpp after managed-file preparation, before loading/starting the English bridge and before opening UnityPlayerActivity. Loading the shared library does not invoke IL2CPP initialization. The pinned game library has only system shared-library dependencies.
- `english.cpp`: replace assembly-count polling and detached worker attachment with hooks on exported `il2cpp_init` and `il2cpp_init_utf16`. Call the original initializer first, preserve its result, and install feature hooks once only after a successful return. Run this on Unity's existing initialization thread. No arbitrary sleep and no background thread attachment remain in the startup path.
- The actual ARM64 initializer was disassembled to confirm its integer success result. Feature hooks and their behavior are otherwise unchanged.
- `build_runtime_apk.py`: add numbered revisions to filenames, managed-file revisions, build records and version codes. Revision 2 seed is 4050302; revision 2 main is 4050303. They can update the installed EN app without uninstalling or clearing data.
- `audit_runtime_payload.py`: select the corresponding revision's build record for independent validation.

## Device evidence and limits

The corrected seed was installed over the existing EN app on S26 serial R5GL14CN45N. No uninstall, data clear, or cache clear was performed. Its log records `IL2CPP completion hooks installed before Unity startup`, six successful feature-hook results, and `Runtime initialization finished after IL2CPP init`. The original premature-attach fault did not recur during the observed startup. The maintainer subsequently confirmed that the main menu appears.

This validates the repaired startup path only. It does not establish that all translations, settings layouts, music switches, gameplay controls, save migration or seed-to-main refresh behavior have passed phone testing. Keep the corrected seed installed for the maintainer to create test progress, then update to the corrected main APK using the quick-test guide. The main APK is prepared locally, not published.

Evidence is retained in the task workspace `work/upgrade405/pre3`: s26-crash.log, s26-process.log, s26-exit.log, s26-install-seed-r2.log, s26-launch-seed-r2.log and s26-seed-r2-runtime.log. Build/signature and host-test logs are under package-seed-r2 and package-test1-r2.
