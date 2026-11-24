# PvZ Fusion 4.1 English Android - Pre-release 8

November 24, 2026. Standard English (EN) and Offline AI (ENAI).

- Fixed another reproduced movement-timing failure that could move Zombonis, bobsled vehicles, Michael Zomboni and Jackson Worldwide off the lawn while they remained alive. The correction now handles repeated rendered frames between physics updates as well as multiple physics updates between frames.
- Updated English wording from Blooms 4.1, including Gods Almanac categories, upgrades, currency labels, Balloon-shroom and two fusion-showcase tips.
- Added coverage for custom-level glove and speed labels. Checked the screenshot's hotkeys, difficulty and enemy-count text against the translation rules.
- Retained the Almanac stat corrections from prerelease 7, including Icicle-shroom's 20 damage every 2.25 seconds. ENAI retains its existing recognition model and lifecycle handling.

Install over the same edition without uninstalling to retain progress. EN and ENAI keep separate saves. Back up saves before updating.

The vehicle correction addresses reproduced timing failures; it does not establish that every possible disappearance scenario is resolved. Please include your edition, version, device, mode and a recording when reporting a remaining problem.

Both editions passed startup and backup-restoration checks in the Android emulator. An ARM64 startup/render check also passed on a Galaxy Tab S9 Ultra. Verified APK integrity, release signatures, 16 KiB alignment and protected game data.
