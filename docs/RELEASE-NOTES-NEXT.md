# Changes after Android 4.0 English prerelease 2

Current release: [prerelease 2](RELEASE-NOTES-4.0-PRE2.md), the approved local rev 3 APK published unchanged as `v4.0-release-2`.

Prepared locally, not published or device-tested:

- Restored four internal Gods: Evolved metadata strings to their original Chinese after a developer identified runtime-sensitive keys. God Coins and the verified display-only Almanac translations remain unchanged.
- Added translation and packaging checks for all 31 reported keys to prevent accidental replacement in future builds.

See [the metadata safety review](testing/ANDROID40-METADATA-SAFETY.md). This is a precaution, not a confirmed fix for reported instability. The reporter confirmed that the missing starting choices and empty modifier menu screenshots came from an earlier version. The catalog defect repaired in prerelease 2 can also affect those paths; a current-build device retest is still needed.

Keep [the investigation](testing/ANDROID40-PRE2.md) and [rev 3 review](testing/ANDROID40-PRE2-REV3.md) as historical evidence; do not count their fixes again in the next release.

Unconfirmed tactic names and specialized effects still await verified PC wording. God Coins is an explicit provisional naming exception. Exact valid PC English takes priority over tracked fallbacks. Vague mode glitches and lingering zombie sprites remain unverified reports, not confirmed translation defects.
