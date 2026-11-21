# PvZ Fusion 4.1 English Android - Pre-release 6

November 20, 2026. Clean Standard EN and Offline AI ENAI builds, based on their matching public pre5 APKs. Install over the same app without uninstalling to retain its saves.

## Zomboni movement repair

Fixed a reproduced stock-game movement failure in which ordinary and red Zombonis could oscillate far above/below the lawn, becoming invisible and effectively unhittable while retaining HP. The scoped native repair stabilizes vertical grounding while preserving the game's horizontal speed, HP, attack and terrain calculations. Also corrected the independently confirmed duplicate rear damage-sprite assignment.

Validated with actual Melon Tri-pult, Brood-shroom, Icicle-shroom and Cryomancer Pea attacks in base Survival: Fog (Endless). Both vehicle types stayed in their lanes and died normally in six final-runtime trials at 1x, 2x and 4x speed. Roof slopes and a native physics regression also passed. Affected physical-device confirmation is still needed; this is a pre-release, and unrelated bobsled problems may remain.

## Translations

- Reviewed 16 screenshots, including 15 Zombie Almanac entries and the Gods Almanac Summoner heading.
- Added 509 exact display mappings for missing complete Ascend headings, full zombie text fields and verified aliases. The existing English zombie descriptions are reused; they are not counted as newly translated entries.
- Checked latest Blooms 4.1 at f5f8a205204c71a6a17bcbe250cad8e80eda3c15. Its new Gods Almanac catalog and formatting changes include no new English wording to import.
- Retained the pre4 Obsidian Formation fix for the pictured Unknown Modifier ID entry.

## Offline AI and build checks

The AI build retains the pre4 offline-recognition lifecycle/watchdog fix. The model, catalog, recognition algorithm and lifecycle code are unchanged from pre5; no new AI optimization is claimed.

598 actual Java display fixtures, 79 Python checks, managed-file restoration tests and APK integrity checks passed. Both native ABIs build, release signatures and 16 KiB alignment verify. Original game libraries, DEX, Unity bundle, metadata, music and AI assets are unchanged. Public builds contain no private cheats or diagnostic harness.

Back up saves before updating. EN and ENAI retain separate saves. Some specialized text remains Chinese pending verified translations. For remaining Zomboni failures, include the device, game mode, speed, attacking plants and a recording.
