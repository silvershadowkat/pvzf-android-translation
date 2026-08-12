# PvZ Fusion 3.8.1 — English Android

This is an independent, noncommercial English Android port of *Plants vs.
Zombies: Fusion* 3.8.1. It is not affiliated with or endorsed by PopCap,
Electronic Arts, LanPiaoPiao, or the upstream translation maintainers.

## Install warning

Back up your saves first. The package ID is unchanged, but this release uses a
dedicated community signing certificate. Android will not install it over the
official Chinese, Joseph, or aha APK because those use different certificates.
After backing up, uninstall the existing build and install this APK. Future
releases signed with this same project certificate can update it in place.

Save/data path:

```text
/storage/emulated/0/Android/data/com.LanPiaoPiao.PlantsVsZombiesRH/files/
```

Do not restore the old `il2cpp` directory over the new installation.

## Troubleshooting blindly renamed packages

Do not change only the manifest package ID to install this game beside another
copy. The compiled DEX still contains package-qualified `BuildConfig`/`R`
classes and the original application-ID constant, while an added mod may have
its own hardcoded paths or preference names. A manifest-only rename does not
rewrite those values and is unsupported.

With both copies installed, such a derivative can read or overwrite unexpected
metadata, configuration, preferences, or hot-patch files—or the added mod may
have directly replaced the English assets. Either case can produce text that
does not match the original English APK. The full external-storage path was
not found as a literal in the base game's IL2CPP metadata or `libil2cpp.so`, so
a proper alternate-package build would need a wider controlled audit rather
than a speculative path patch.

For reliable testing, use the unchanged package ID. Back up saves, remove the
blindly renamed derivative, and check only the original package's
`files/il2cpp` directory for stale metadata. Do not remove progression data.

## Download verification

- File: `PvZ-Fusion-3.8.1-English-Android.apk`
- Size: `550689362` bytes
- SHA-256: `3a13cfdb083186cf8d359c641fc20b770ffa64aca8f536220cddd03feb329cc7`
- Signing certificate SHA-256:
  `1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6`

## What is included

- current PC English translation data ported to Android 3.8.1;
- conservative Joseph 3.6.1 and aha 3.8.1 fallback mappings where current PC
  data did not cover unchanged Android strings;
- translated Almanacs, levels, custom levels, tutorials, tips, configuration,
  and serialized Android UI;
- PvZ-style TMP typography with CJK fallback;
- Android-specific title, description, footer, skin-selector, Help/Hotkeys,
  and credits layout fixes;
- in-game Android-port credits for Joseph Franci, aha, SilverShadow, and Codex.

## Safety evidence

The release uses the official Chinese 3.8.1 APK shell. A comparative audit
proves the manifest, resources, DEX bytecode, and all native libraries are
byte-identical to the official APK. Only `data.unity3d` and
`global-metadata.dat` differ. The APK passes ZIP integrity, alignment, and
Android signature v1/v2/v3 verification. Windows Defender reported no threats
on August 11, 2026. See `docs/RELEASE-SAFETY.md` for scope and limitations.

## Credits and license

Game by LanPiaoPiaoFly and the PvZ Fusion team. English translation data and
terminology by Teyliu, Mamoru-kun, and the full PVZF Translation/Blooms
community credited in the repository README and upstream project. Android port
lineage and references: Joseph Franci and aha. This port/toolkit: SilverShadow
and Codex.

Translation data is used under CC BY-NC 4.0 and the release is noncommercial.
Toolkit code is MIT. Full provenance and contributor names are in `README.md`
and `THIRD_PARTY.md`.

The APK contains third-party game material. Distribution may be removed if a
rights holder objects. The source toolkit intentionally contains no game
binaries or extracted proprietary assets.
