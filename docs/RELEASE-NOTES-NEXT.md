# Release 9

- Updated PC English for The Gods: Evolved, including shield/respawn cards and several upgrade names.
- Fixed Blazer Snipea's two missed Firewall descriptions while keeping its runtime plant name.
- Translated 117 additional plain menu, save/status, editor and counter fields; cleaned up two Travel Store placeholder labels.
- Preserved five-round selection instructions and restored missing beat-position placeholders in an old partial translation.
- Verified 28 tests, all 19,061 metadata literals and all 201,406 Unity objects. Only 143 metadata text entries and two serialized text fields differ from Release 8.
- Tracked all 117 provisional translations for replacement when complete PC English becomes available.
- Save handling, gameplay and executable code are unchanged. Specialized missing PC text and protected identifiers remain unchanged.
- Signed APK verification passed. Android display and gameplay testing remain pending. See [release notes](RELEASE-NOTES-3.9-PRE9.md).

PC source: `d9c05a39e7c0abb09f84ddfb15582885d60a0efe`. Ten exact, hash-checked comma-only syntax repairs were required before importing its JSON; no PC translation values were changed by those repairs.

Details and coverage limits: [Release 9 audit](testing/RELEASE9-TRANSLATION-AUDIT.md).
Test locations: [Release 9 checklist](testing/RELEASE9-TEST-CHECKLIST.md).
Previous published notes: [Release 8](RELEASE-NOTES-3.9-PRE8.md).
