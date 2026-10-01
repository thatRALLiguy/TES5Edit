"""Native regression checks for check errors and caught execution exceptions."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from starfield_master_ids import generate, hashes, plugin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    exe = args.exe.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    data = output / 'Data'
    generate(data)
    plugin(data / 'MissingMaster.esm', ['Absent.esm'], 1,
           [(0x01000800, 'MissingMasterFixture', [])])
    for size in (1, 3, 4, 23):
        (data / f'Truncated{size}.esm').write_bytes((b'TES4' + bytes(20))[:size])
    before = hashes(data)
    cases = [
        ('valid-check', 'Starfield.esm', '-check', 0, None),
        ('invalid-check', 'UnresolvedReference.esm', '-check', 1, 'could not be resolved'),
        ('invalid-report', 'UnresolvedReference.esm', '-dcr', 1, 'could not be resolved'),
        ('missing-master', 'MissingMaster.esm', '-check', 2, 'unexpected error:'),
    ]
    cases.extend((f'truncated-{size}', f'Truncated{size}.esm', '-check', 2,
                  'truncated plugin header') for size in (1, 3, 4, 23))
    results = []
    for name, filename, mode, expected, diagnostic in cases:
        command = [str(exe), '-dump', '-SF1', '-nobsa', '-l:en', f'-d:{data}', mode, str(data / filename)]
        run = subprocess.run(command, cwd=output, capture_output=True, timeout=120)
        (output / (name + '.stdout.txt')).write_bytes(run.stdout)
        (output / (name + '.stderr.txt')).write_bytes(run.stderr)
        text = (run.stdout + run.stderr).decode('utf-8', errors='replace').lower()
        passed = run.returncode == expected
        if diagnostic:
            passed = passed and diagnostic in text
        else:
            passed = passed and 'all done.' in text and ' -> ' not in text
        results.append({'case': name, 'expected_exit': expected,
                        'actual_exit': run.returncode, 'passed': passed})
    unchanged = hashes(data) == before
    report = {'executable': str(exe),
              'executable_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
              'fixtures_unchanged': unchanged, 'cases': results}
    (output / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if unchanged and all(r['passed'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
