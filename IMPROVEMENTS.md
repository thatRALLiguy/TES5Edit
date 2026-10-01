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

## Round 3: empty command-line arguments (native test pending)

Both overloads in `Core/wbCommandLine.pas` accessed `s[1]` without first checking
whether an argument was empty. Skip empty strings when searching for switches;
return them as positional arguments when iterating positions. This preserves
explicitly supplied empty positions and avoids out-of-bounds string reads.
No parsing or rewriting of mod records is involved.

`Tests/CommandLineRegression.dpr` exercises empty leading/trailing arguments,
a switch between positional arguments, an absent switch, output clearing and
iterator advancement. Compile the actual helper with Delphi range checks enabled
(`dcc64 -B '-$R+' Tests\CommandLineRegression.dpr` in PowerShell) and run the resulting executable
with four arguments: `"" -probe:value payload ""`. Native execution is pending;
a source inspection is not an execution of this regression test.

## Round 4: avoid duplicate validation work

The recursive GUI error checker and bundled `Check for errors.pas` script called
the same element's check method a second time whenever the first call returned
an error. Reuse the diagnostic already obtained. Traversal, output formatting,
parent summaries and descendant checks remain in place. The linear GUI checker
and xDump already use one check call per element.

Diff review confirms one redundant call removed from each implementation; no
filters, record changes or skipped subtrees were introduced. This saves one
validation call per erroneous element in these two paths. No elapsed-time
speedup is claimed. GUI/script runtime verification remains pending.

## Round 5: truncated-header guard and aggregate review (in progress)

The installed binary accepted a four-byte TES4 file as a completed load. Source
review found that `TwbFile.Scan` passed the mapped file directly to the first
record constructor with no minimum main-record-header size check. Reject files
shorter than the selected game's header before constructing the first record.
This uses existing definitions (16 bytes TES3, 20 TES4, 24 later games), not a
Starfield-only hard-coded size. `TwbFileSource` has its own Scan override; the
new guard is in the plugin scanner, not the save scanner.

The native exit-code harness now includes 1-, 3-, 4- and 23-byte malformed
Starfield headers alongside the clean fixture. This guard is only a minimum
file-header bound check; it is not a complete malicious-file parser audit and
does not establish bounds coverage for every subsequent record/subrecord.
Native test results, cross-game checks and the full aggregate review are pending.

Aggregate source review caught an edge case in round 3: the positional overload
historically skips all arguments when given an empty switch-character set.
Preserve that behavior explicitly, including empty arguments, and cover it in
the native command-line regression harness.

The online [LOOT Starfield masterlist](https://github.com/loot/starfield/blob/v0.29/masterlist.yaml)
was also inspected as a compatibility-data reference. It is not a binary-format
schema and does not justify adding automatic plugin edits or converting scales.
No external database contents are bundled or automatically applied to user mods.

## Completion gates still open

- Build baseline and changed xDump and xEdit with Delphi and pinned submodules.
- Run both Python native harnesses on the changed xDump; compare against the
  preserved baseline build, in addition to the older installed-binary evidence.
- Run the Delphi command-line regression with range checking enabled.
- Exercise valid/truncated inputs for TES3 and TES4 as well as Starfield to
  verify the header-size guard, and GUI/script error reporting on audit copies.
- Check complete logs and input preservation; investigate any new failures.
- Confirm pushed commit identities and baseline preservation after final changes.

Until those gates pass, these are reviewable source fixes, not a verified release.

## Verification follow-up

`Tests/xdump_header_sizes.py` now generates valid TES3, TES4 and Starfield controls
and truncated headers at 1 byte, 4 bytes and one byte below each format's header
size. Run it with the same `--exe` and fresh `--output` arguments as the other
Python harnesses. The old 4.1.5q executable accepts the valid TES4 and Starfield
controls. It returns zero for all nine malformed inputs, failing the new
exit-code/diagnostic expectations. All fixture hashes remain unchanged.

The old executable's valid TES3 control does not reach validation: it tries to
load an unavailable `Morrowind.exe` internal master. That is an explicit failed
prerequisite, not a clean TES3 check or proof of a defect in this fixture. The
new source has embedded Morrowind hardcoded data in `wbHardcoded.dfm`; a freshly
built binary is needed to determine its behavior. The harness retains this gate.

The mixed-master harness now requires a successful process exit as well as the
expected resolved target. All Python harnesses explicitly select `-dump`, so
renaming a build does not accidentally select another tool mode.

Build discovery checked conventional compiler directories and PATH, plus the
signed-in user's and machine's Embarcadero BDS registry entries. No Delphi
compiler was found. The fork's GitHub Actions runner API returned
`total_count: 0`. Neither route currently supplies a native build environment.
No compiler installation, license acquisition or remote machine configuration
has been performed.

## Fork build label

Our xEdit and xDump builds display `4.1.5rd_a`: `d` identifies the dwnfdrknss
edition and `a` is our revision. The shared `wbBuildLabel` supplies application
banners and cleaning reports; both Delphi projects use the same label in their
textual Windows file/product version metadata. Numeric Windows version fields
remain 4.1.5.0. Optional edition titles and architecture suffixes are retained.

The checked-out upstream source identifies itself internally as `4.1.5r`.
That value remains unchanged for script compatibility and update comparisons:
its numeric conversion supports a single-letter build suffix, so the fork label
is deliberately separate. The fork label matches the upstream 4.1.5r source;
the older installed 4.1.5q executable is only a historical test reference.

Delphi 13 CE installation has since started and the pinned source submodules
have been downloaded. Native builds and verification remain pending completion
of IDE setup; no executable carrying this label has yet been verified.

## Native verification: October 1, 2026

Fetched official `TES5Edit/TES5Edit` branch `dev-4.1.6` again. Its tip remains
`9fb016884bec138ea6c7b872cec831537d464c3e`, identical to our preserved base;
there are no upstream commits to merge.

Delphi 13 CE successfully compiled xDump from `a00f514` using Win64 LiteDebug
in the IDE (zero errors, six warnings, five hints). Windows file/product strings
both read `4.1.5rd_a`. The executable SHA-256 is
`00fc509998a2ca3bd837e508d36c8d7ab1aadd57bd248accc4643fbde6d39ba4`.

All three native fixture suites passed on that binary:

- Mixed Starfield master namespaces: 4/4, including the unresolved control.
- Validation/execution exit codes: 8/8.
- TES3/TES4/SF1 valid and truncated headers: 12/12, including the valid TES3
  control that could not run on the older installed executable.

Each suite verified that fixture hashes were unchanged. Local reports and full
stdout/stderr logs are under `audits/xedit-improvements-2026-10-01` in the parent
workspace, in `changed-master-ids`, `changed-exit-codes`, and
`changed-header-sizes`. A binary snapshot is in `changed-build-a00f514`.
These results verify the changed xDump on synthetic inputs; baseline-source
comparison, command-line range checks, and GUI/script checks are still open.

The editor's initial compile stopped at missing `jcld29win64.inc`. Both JCL
configuration files were then copied from `jcl.template.inc`, as documented in
the upstream README. The pinned JEDI include intentionally treats newer
compilers as its latest known compiler. No submodule source was changed.

After that setup, xEdit Win64 LiteDebug compilation failed in the pinned
SynEdit dependency. The IDE reports four errors, 42 warnings and 32 hints;
visible diagnostics include `E2197 Constant object cannot be passed as var
parameter` in `SynHighlighterMulti.pas` (including line 828), followed by
`F2063 Could not compile used unit 'SynHighlighterMulti.pas'` from
`SynEditMiscProcs.pas:2707`. No successful xEdit executable was produced.
Work stopped at this compatibility failure, in accordance with the user's
instruction to report genuine issues before continuing. It has not yet been
established whether the recommended Delphi 12 compiler accepts this dependency.
The missing VirtualEditTree designer component also prevented opening the main
form visually; that operation was cancelled without accepting component removal.
