# Prerelease 3 r18: startup announcement terminology

The embedded Android 4.0.5 announcement retained four Chinese fragments in three lines. This patch completes those lines using the official Chinese announcement and terminology from the reviewed PC main revision `c7fb5997d65e1d5248f3d7a9ca9c9e0a4b516640`.

## Term review

| Chinese fragment | English used | Evidence |
| --- | --- | --- |
| 阿尔法日记 | Alpha's diary | A descriptive translation, not a newly named plant or official book title. PC strings establish Alpha; the official announcement places the diary in Snowy Night. |
| 究极火炬 | Infernal Squashwood and Infernal Sparkwood | PC almanac entries 902 and 948. The former lists the Phoenix Pea damage multiplier; the latter is its subspecies and inherits its treatment of other projectiles. The announcement uses a shortened family reference. |
| 浴火豌豆 | Phoenix Peas | Paired Chinese/English almanac entry 902, Phoenix Threepeater entries, and the level1319 tip all identify the projectile. It is not a new plant name. |
| 真正的樱桃炸弹 | Cherry on Top | PC `travel_buffs.json`, `advancedBuffs/1013`: the card title is Cherry on Top, while its description starts True Cherry Bomb. The current Android runtime uses the same card title. |

The PC changelog is already English but does not directly translate every line of the official Android notice and includes material carried over from the larger 4.0 update. It was used as reference, not copied wholesale. Existing English names in the other announcement sections were checked against it. No balance numbers were copied from potentially stale almanac prose.

## Implementation and safeguards

- `assets/announcements-4.0.5-review.json` records exact source text, its SHA256, English text, the object identity and terminology provenance.
- `scripts/translate_announcements_405.py --work <pre3>` runs after the verified Creator Guide patch. Changed sources or an unexpected intermediate bundle fail closed.
- Only `resources.assets/196738/m_text` changes. All 208,662 serialized objects were compared before and after repacking; the single intended object was the only difference. Reopening it confirmed every other component field, including font/layout settings, stayed identical.
- Numbers, line breaks and rich-text tags are preserved; the completed announcement contains no Chinese or em dash.
- No metadata, runtime translation dictionary, native code, save logic, or game data changes accompany this wording patch.

The verified r16 editor fixes remain included. Reproduction order is the r12 PC refresh, r13-r15 guide/editor data patch, r16 runtime source fix, then this announcement patch. Do not rerun an earlier layer against a later layer without restoring and verifying its recorded input; the scripts intentionally refuse that ambiguous state.

r17 passed on-device checks for the upper and lower announcement sections. r18 smooths the diary sentence to "Completed Alpha's diary" without changing its meaning. Build and device results are recorded in the local release handoff and `announcements-r17` evidence directory. This is a local candidate, not a publication.
