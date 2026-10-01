# xEdit safety, accuracy and efficiency work

Original revision: `9fb016884bec138ea6c7b872cec831537d464c3e`.
Preserved locally and on the fork as `codex/base-2026-10-01`.
Changes live on `codex/safety-accuracy-efficiency`; `dev-4.1.6` remains untouched.
Restore the baseline by checking out the baseline branch in a clean checkout.
Do not reset a checkout containing work you need to keep.

## Five review rounds

1. Correct SF1Dump's Starfield master namespace selection; exercise full,
   small and medium references with interleaved master types and a negative case.
2. Make command-line validation failures observable to automation; retain
   diagnostic text and distinguish check failures from execution failures.
3. Inspect initialization and argument handling for demonstrable accuracy bugs.
4. Remove redundant validation work without losing diagnostic coverage.
5. Review the aggregate diff and run positive/negative regression checks,
   preservation checks and native build checks. Add functionality only where
   a specific observed gap warrants it.

Every round requires a purpose, source evidence, validation and an explicit
statement of limits. Source checks and fixture generation are not native
execution of a modified binary. Native build/runtime verification remains a
completion gate, not an optional follow-up.

## Round 1: Starfield master namespaces (implementation; native test pending)

`xEdit/xeInit.pas` enables `wbComplexFileFileID` for Starfield; `xDump.dpr`
did not. `TwbFile.FileFileIDtoLoadOrderFileID` in `Core/wbImplementation.pas`
selects full/small/medium master tables only when that flag is enabled.
Enable it in xDump's Starfield initialization before definitions and loading.
Other games and the no-save settings are unchanged.

Independent references:

- [Ortham's reverse-engineering results](https://blog.ortham.net/posts/2024-06-28-load-order-in-starfield/)
  explain separate on-disk namespaces and show mixed-master examples. These
  observations concern the versions named in that article, not every later game.
- [LOOT's plugin-type documentation](https://loot.github.io/docs/help/changing-plugin-types-in-starfield/)
  explains why changing a released plugin's scale is unsafe. This fix interprets
  files using the existing core implementation; it does not convert plugin types.

`Tests/starfield_master_ids.py` generates entirely synthetic FLST fixtures in a
new directory, checks actual LNAM target names from a supplied xDump executable,
includes a deliberately unresolved reference and hashes every fixture before
and after execution. Example:

```powershell
python Tests/starfield_master_ids.py --exe C:\build\xDump.exe --output C:\audit\new-run
```

Baseline execution on October 1, 2026 used installed SF1Dump 4.1.5q, SHA-256
`100dc3552da0dbd03985ed9dcc93648f001ab738f8db812b1feac36b01ad13ec`.
The full reference incorrectly resolved to `SmallFixture`; small and medium
references were unresolved. All fixture hashes were unchanged. This reproduces
the failure in an older installed executable, not a build of the baseline source.
The deliberately broken reference must remain unresolved after the fix.

No Delphi compiler was found on PATH, in the conventional Embarcadero program
directories, or the checked BDS registry locations. A native build of this branch
and rerun are still required. No updated executable or gameplay pass is claimed.

## Round 2: observable validation failures (native test pending)

xDump discarded the Boolean result from `CheckForErrors`; its exception handler
also only printed a diagnostic. Both could exit successfully after failure.
Return 1 for `-check`/`-dcr` element-check errors and 2 for caught execution
exceptions, retaining the original diagnostic text. Ordinary non-check dumps
retain their current behavior. This does not promise that every loader warning
or invalid command line is covered; further review is required.

`Tests/xdump_exit_codes.py` exercises a clean plugin, an unresolved reference in
both check modes, and a missing master. The installed 4.1.5q binary returned 0
for all four. The clean control passes, while all three failure-exit expectations
fail. All fixture hashes remain unchanged. Native verification of this branch
is pending. Fixture headers now include the required CNAM and INCC members so
unrelated header errors cannot contaminate the clean control.

During test development a four-byte `TES4` input was accepted by the installed
binary. That observation requires investigation during the input-safety review;
it is not yet attributed to a particular core implementation path.
