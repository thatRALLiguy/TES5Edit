# Leveled-list count regression (#1382)

Related upstream report: https://github.com/TES5Edit/TES5Edit/issues/1382.

Starfield and Skyrim leveled lists store LLCT in one byte. Appending entry 256
previously wrapped that count to zero. The bounded array definition rejects
oversized assignments before changing the target, reports already oversized
input, and preserves loaded entries so that the user can inspect and repair it.
Removing entries to reach 255 synchronizes the stored count again. Arrays with
no maximum retain their existing behavior.

## Console reproduction

Run from the repository root with Python 3.11+ and a console xDump executable:

```powershell
python Tests/leveled_list_limits.py --exe C:/Build/xDump.exe --output C:/Audit/limits-fixed
python Tests/leveled_list_limits.py --exe C:/Official/xDump.exe --output C:/Audit/limits-baseline --baseline
```

Each output directory must be new. The helper creates synthetic SF1 and SSE
masters, lists with 0/1/254/255/256/257 entries, and an unrelated 300-entry form
list. It checks native completion, overflow diagnostics and input/tool hashes.
No installed plugins are needed. The baseline option expects the original
absence of overflow diagnostics, not corrected behavior.

## Actual editor regression

Use a fresh **copy** of one generated game's fixtures as the editor's Data
directory. Load its synthetic master, Limits1/254/255/256/257.esm and
Unbounded.esm. Run `LeveledListLimits.pas` through the matching SF1 or SSE editor.
Set the two output paths in the script to an isolated, writable audit directory.
Never load installed plugins for this mutation test. The editor may save the
working copies on exit; `-DontSave` is not a supported editor switch.

Expect 21 `PASS:` lines and `COMPLETE`. The script checks allowed growth to 255,
rejected appends, rejected whole-array replacement, valid replacement, retained
oversized data, repair and an unbounded form-list control. Rejected assignments
also emit the expected native exception diagnostic. `limits-repaired.esm`
must contain LLCT=255 and 255 physical LVLO subrecords. Reopen it with xDump
beside the matching synthetic master and require zero record diagnostics.

## Verification recorded October 1, 2026

- Official 4.1.5q: 14/14 baseline console cases reproduced the missing diagnostic.
- Modified build: 14/14 console cases and all 21 editor assertions in each of
  SF1 and SSE passed. Frozen source fixtures remained unchanged; only the
  expected disposable working files were saved.
- Both official and modified dump tools reopened both repaired artifacts with
  zero record diagnostics. Official SF1Dump also emitted its existing missing
  Wwise soundbank warning in the synthetic environment.

Runtime verification used Win64 LiteDebug executables built with Delphi 13 CE
from the private development tree containing these same four core-file changes.
The builder reported both builds completed without warnings or hints.
This public patch applies to the public fork's Delphi-compatible base
`0037a1699a8400abbd9d23bc21c42e0698380730`; it is not a claim that pristine upstream
was compiled or that this public branch received an independent binary build.

Executable SHA-256:

- Official dump: `100dc3552da0dbd03985ed9dcc93648f001ab738f8db812b1feac36b01ad13ec`
- Modified dump: `acbe20300df521a90e1d78c0645d05ecb8f9c6f0e7b20cd6af7027b46c80b9e2`
- Modified editor: `cd36bed8cd323e1ad5f6870206e00f350bcdb0e899c166a5d76eebb8aa81689c`

Coverage is synthetic LVLI and FLST data with actual editor scripting and
serialization. Other leveled-list schemas, GUI clicks, mixed multi-element
replacement batches, Win32, Fallout modes and gameplay have not been exercised
by this regression. Existing malformed files are diagnosed, not auto-repaired.
