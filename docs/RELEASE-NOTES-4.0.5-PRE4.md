# PvZ Fusion 4.0.5 English Android: Prerelease 4

## Choose one APK

- **Standard:** `PvZ-Fusion-4.0.5-English-prerelease4-Standard.apk`. All English translations and improvements, without the AI model. Magic Plantbrush shows an unavailable message instead of freezing.
- **AI:** `PvZ-Fusion-4.0.5-English-prerelease4-AI.apk`. Also includes offline Magic Plantbrush recognition in the same app. Requires Android 8.0 or newer and additional memory. No companion app or internet connection is needed for recognition.

**AI recognition has only been tested on two Snapdragon devices: Samsung Galaxy S26 Ultra and Retroid Pocket Nova. Compatibility and performance on other phones or chipsets are not guaranteed.**

## Updating

**Back up your saves first, just in case.** Install over your matching prerelease 3 app without uninstalling. Managed translation files refresh while saves, extra save slots, player data and settings are preserved.

Standard uses `com.LanPiaoPiao.PlantsVsZombiesEN`; AI uses `com.LanPiaoPiao.PlantsVsZombiesENAI`. They remain separate apps with separate saves under `/Android/data/<package name>/files/`. Switching variants does not automatically transfer progress. Chinese/prerelease 2 users should follow the [one-time save transfer instructions](https://github.com/silvershadowkat/pvzf-android-translation#moving-saves-without-restoring-old-translation-files).

## Performance and reliability

- **Blooms music delays and restarts:** Replaced full replacement-track loading with background audio streaming. Repeated updates no longer restart or seek through a playing track. Failed music loading falls back to Original music.
- **Less repeated work:** Reduced translation and reflection lookups, unnecessary UI updates, startup text scanning and cache clearing. Removed obsolete metadata blocks while keeping translations and save-preservation checks.
- **Magic Plantbrush:** One tap opens the mode while recognition loads. An early Identify waits until ready. Failed or disconnected sessions can reload on a later attempt without restarting the game. Leaving the mode releases the recognizer, and unchanged private model files no longer need repeated full verification.

These changes target the reported music freezes, repeated loading work and recognition interruptions. Lower-memory phones and long Gods sessions still need further testing; this is not a claim that every crash is fixed.

## Translation fixes

- **Ravenous Reach:** Completed the Chinese description: “Tyrannoflora Lux: Increased attack range.”
- **Zombie Parry:** Completed the effect explaining that dodging zombies deal 100% reflected damage to nearby plants.
- **Pain Response:** Completed the effect explaining that zombies gain Armor equal to 1% of damage received, up to a limit.
- **Settings:** Corrected “Disable Sun Visual Effect” to “Disable Mini Sun Visual Effect.”
- **Reviewed Blooms updates:** Brought over 185 new or revised text mappings plus wave-number text, 27 embedded text updates and 12 almanac fields. These include Gods modifier/support wording, Cocoa Bean terminology, Graveout mode names, Tinfoilhead Zombie, Lily Pad instructions, and plant/zombie descriptions.

Established Blooms names were reused. The three modifier effects follow Android's actual wording, without adding PC-only mechanics. All earlier English pages, guides, diary artwork, credits, music selection and Projectile Info controls remain included. Official 4.0.5 almanac visibility behavior is unchanged.

[Detailed translation and performance audit](https://github.com/silvershadowkat/pvzf-android-translation/blob/agent/magic-plantbrush-single-apk/docs/testing/ANDROID405-PERFORMANCE2-AUDIT.md)
