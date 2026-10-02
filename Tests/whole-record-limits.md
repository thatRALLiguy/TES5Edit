# Whole-record preservation and reference-assignment regression

This corrects regressions in the first fix for upstream
[issue #1382](https://github.com/TES5Edit/TES5Edit/issues/1382).
Rejecting an oversized nested array inside its own `AssignInternal` was too
late: whole-record assignment had already cleared the destination, and the
parent continued after the nested `Assign` caught the exception. Copying as an
override or new record could also leave a partial destination record.

Check bounded descendants before destructive whole-record assignment and deep
copy setup. Limit this preflight to operations that copy those descendants:
assigning a main record to a compatible FormID field or reference array copies
only its FormID and must still work when the referenced list is oversized.
Destination-array growth checks remain in place; malformed source records stay
inspectable and repairable.

## Reproduce

Generate SF1/SSE fixtures with `leveled_list_limits.py` as described in
`leveled-list-limits.md`. Load disposable copies in this exact order: the game
master, Limits256.esm, Limits257.esm, Limits1.esm, Limits254.esm, Limits255.esm,
Unbounded.esm. Reference targets must load after the oversized source masters.
Replace `@AUDIT@` in `WholeRecordLimits.pas` with a writable absolute directory
ending in a slash and run it in the matching editor. The script edits records
and creates synthetic files; never use installed plugins.

Require 33 `PASS:` assertions, `COMPLETE`, and no `FAIL:` or `HARNESS_ERROR`.
Expected rejection exceptions appear in diagnostics. Compare SHA-256 for all
six before/after pairs: whole-256, whole-257, copy-override, copy-new,
reference-256 and reference-257. Every pair must be byte-identical.
Reference assignments are checked through `LinksTo`, because the formatter can
return nil even after successfully changing a reference.

Reopen these artifacts beside copies of all synthetic masters using official
and corrected xDump. Require completion with no record diagnostics, and inspect
the serialized bytes independently:

- limits-repaired.esm, copy-override-valid.esm, copy-new-valid.esm: LLCT=255 and
  255 physical LVLO entries each.
- reference-list-valid.esm: LLCT=254 and 254 LVLO entries, the first pointing to
  Limits257.esm:000800 and the remaining 253 to the game master:000800.
- reference-formlist-valid.esm: 302 LNAM references; the first points to
  Limits257.esm:000800, the last two to Limits256/257.esm:000800, and the other
  299 retain their original game-master reference.

## Verified October 1, 2026

The first correction reproduced eight reference-operation failures in the
previous editor while its whole-record rejection controls passed. With the
FormID follow-up, all 33 assertions pass in both SF1 and SSE and all 12 snapshot
pairs retain identical bytes. The earlier 21 array-level assertions per game
also pass: 108 editor assertions total. All frozen inputs and tools stayed
unchanged.

All ten valid serialized artifacts reopen in both official and corrected dump
tools: 20 completed checks with zero record diagnostics. The official SF1 dump
retains its existing missing-Wwise environment warning. The corrected console
also passes 14 count-boundary cases and 24 existing native regressions.
Both full Delphi 13 CE Win64 LiteDebug builds completed with zero errors,
warnings and hints.

SHA-256 identities:

- Previous editor with the reference regression: `cfb282cd650cd833cace294cf512284b2c7afde97b817b9a3956da10a8d5b97f`
- Corrected editor: `e5c4621d1bf403b0cd62193792ee8384dab54cf55214666cc124531307a4fcb3`
- Corrected dump: `da9ebc1a83d843466c065fae17f445f0725d511a72da4bb6d4d1c2e69752f37a`
- Official dump: `100dc3552da0dbd03985ed9dcc93648f001ab738f8db812b1feac36b01ad13ec`

Runtime checks used private builds with the same core correction. The public
source was not independently compiled. This covers synthetic editor/script,
serialization and native checks, not GUI dragging, every possible nested schema,
Win32, Fallout or gameplay. No binary release is included.
