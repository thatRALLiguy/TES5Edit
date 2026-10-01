# Whole-record preservation regression

This corrects a data-loss regression in the first fix for upstream
[issue #1382](https://github.com/TES5Edit/TES5Edit/issues/1382).
Rejecting an oversized nested array inside its own `AssignInternal` was too
late: whole-record assignment had already cleared the destination, and the
parent continued after the nested `Assign` caught the exception. Copying as an
override or new record could also leave a partial destination record.

The correction checks bounded source descendants before destructive assignment
and before deep-copy destination setup. Parsing still retains oversized input,
and the original target-array growth checks remain in place.

## Reproduce

Generate the synthetic SF1/SSE inputs with `leveled_list_limits.py` as described
in `leveled-list-limits.md`. Load a fresh working copy of the selected game's
master and Limits1/254/255/256/257.esm plus Unbounded.esm into the matching editor.
Replace every `@AUDIT@` in `WholeRecordLimits.pas` with an absolute, writable
audit-directory path ending in a slash, then run that script. Use disposable
files only; the script edits records and creates two synthetic destination files.

Expect 21 `PASS:` assertions, `COMPLETE`, and no `FAIL:` or `HARNESS_ERROR`.
Expected rejection exceptions are logged as diagnostics. Compare SHA-256 hashes
of each `*-before.esm` / `*-after.esm` pair for `whole-256`, `whole-257`,
`copy-override` and `copy-new`. All four pairs must be byte-identical; an unchanged
entry count alone is insufficient evidence of preservation.

The valid controls assign/copy 255 entries. Reopen `limits-repaired.esm`,
`copy-override-valid.esm` and `copy-new-valid.esm` beside copies of the synthetic
masters, including their Limits*.esm dependencies, with official and modified
xDump. Require completed checks with zero record diagnostics and independently
verify one LLCT=255 paired with 255 physical LVLO entries in each artifact.

## Verified October 1, 2026

The prior editor reproduced the failure in both SF1 and SSE: rejected whole
assignments changed destination bytes, and oversized copies created partial
records. The corrected editor passed all 21 new assertions in each game and
preserved all eight rejected-operation snapshot pairs exactly. The earlier
21 array-level assertions per game also passed: 84 editor assertions in total.
Frozen fixture inputs and executables remained unchanged.

All six valid artifacts reopened in both official and corrected dump tools:
12 completed checks, zero record diagnostics. Official SF1Dump retained its
existing missing-Wwise warning in this synthetic environment. The corrected
dump also passed 14 count-boundary cases, 24 prior native regressions and 23
private agent-runner tests. The user reported no compiler diagnostics for the
corrected editor build.

SHA-256 identities:

- Prior editor: `29b0ed3d63951442f41b658f8ddaadfb86ae45e9985d8c85e306a7c47c9932a2`
- Corrected editor: `cfb282cd650cd833cace294cf512284b2c7afde97b817b9a3956da10a8d5b97f`
- Corrected dump: `5c7eb7aff6ca33ec44e8eb6742298f2584c60a481ee719701f11f405ba17050d`
- Official dump: `100dc3552da0dbd03985ed9dcc93648f001ab738f8db812b1feac36b01ad13ec`

Runtime tests used Win64 LiteDebug Delphi 13 CE private builds containing the
same core correction. The public source was not independently compiled. These
are synthetic editor/script, serialization and native checks, not GUI dragging,
all possible nested schemas, Win32, Fallout, or gameplay validation.
