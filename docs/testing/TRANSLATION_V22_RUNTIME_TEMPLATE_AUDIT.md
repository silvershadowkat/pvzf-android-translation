# Translation V22 Runtime-Template Audit

## Reported save message

The save-success toast is not stored in save data. Android IL2CPP metadata
contains the C# format template `保存成功，编号：{0}`. The PC community project
translates the final rendered form, such as `保存成功，编号：0`, with a regex.
It was missed because the static Android builder sees `{0}` while the PC
runtime translator sees a concrete number.

## Builder correction

`build_metadata_translation.py` now uses a conservative bridge for this data
shape. It replaces C# fields with unique test values, accepts only a PC regex
that matches the entire resulting string, applies the PC community target, and
restores the original fields including format specifiers such as `:F0` and
`:D2`. Partial matches, ambiguous results, and results retaining CJK are
rejected.

This keeps the PC project authoritative and avoids maintaining duplicate
Android wording. A future PC exact-string entry still takes priority.

## Additional exact whole-template matches found

The same audit found and translated these previously missed player-facing
templates:

- current-round progress;
- page counters and type counts;
- save-success ID notification;
- global plant damage and shield bonuses;
- Tower Defense Adventure completion time;
- modifier-luck bonus/current-luck text;
- Note Editor Hold-note start/end notifications;
- Endless Mode high-score description;
- modifier-reroll reward text;
- new-plant acquisition/use-count text.

Developer diagnostics and partial regex matches were not promoted.

## Phone checks

1. Create a new survival/Odyssey save and confirm the toast says
   `Progress saved with ID: 0` (or the actual assigned ID).
2. Reopen the save picker and confirm its row remains English.
3. Sample an Endless Mode description and a page counter if reachable.
4. Confirm plant bonus messages retain whole-number formatting rather than
   exposing raw floating-point values.
