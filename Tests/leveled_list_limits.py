"""Synthetic boundary checks for TES5Edit/TES5Edit#1382 (SF1 and SSE).

Requires a console xDump build. --baseline expects the old silent overflow.
No installed plugins are used. All inputs and logs stay in a new output folder.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sub(name, data):
    return name.encode() + struct.pack('<H', len(data)) + data


def record(game, name, form, data, flags=0):
    return struct.pack('<4sIIIIHH', name.encode(), len(data), flags, form, 0,
                       559 if game == 'SF1' else 44, 0) + data


def plugin(game, path, master, signature, payload):
    header = sub('HEDR', struct.pack('<fII', 0.96 if game == 'SF1' else 1.7, 1, 0x900))
    header += sub('CNAM', b'Synthetic leveled-list regression\0')
    if master:
        header += sub('MAST', master.encode() + b'\0')
        if game == 'SSE':
            header += sub('DATA', bytes(8))
    header += sub('INCC', bytes(4))
    body = record(game, signature, 0x01000800 if master else 0x800, payload)
    group = struct.pack('<4sI4sIII', b'GRUP', len(body) + 24, signature.encode(), 0, 0, 0)
    path.write_bytes(record(game, 'TES4', 0, header, 1) + group + body)


def leveled(game, count):
    data = sub('EDID', f'Limit{count}'.encode() + b'\0')
    data += sub('OBND', bytes(24 if game == 'SF1' else 12))
    if game == 'SF1':
        data += sub('ODTY', bytes(4))
    data += sub('LVLD', bytes(4 if game == 'SF1' else 1))
    if game == 'SF1':
        data += sub('LVLM', bytes(1))
    data += sub('LVLF', bytes(2 if game == 'SF1' else 1)) + sub('LLCT', bytes([count & 255]))
    for index in range(count):
        data += sub('LVLO', struct.pack('<HHIHBB', index + 1, 0, 0x800, 1, 0, 0))
    if game == 'SF1':
        data += sub('FLLD', bytes(4))
    return data


def generate(root):
    cases = []
    for game, master in [('SF1', 'Starfield.esm'), ('SSE', 'Skyrim.esm')]:
        data = root / game
        data.mkdir(parents=True, exist_ok=False)
        plugin(game, data / master, None, 'LVLI', leveled(game, 0))
        for count in [0, 1, 254, 255, 256, 257]:
            name = f'Limits{count}.esm'
            plugin(game, data / name, master, 'LVLI', leveled(game, count))
            cases.append({'game': game, 'plugin': name, 'entries': count, 'oversized': count > 255})
        # An unrelated variable-size array must retain its existing behavior.
        payload = sub('EDID', b'UnboundedFormList\0')
        payload += sub('LNAM', struct.pack('<I', 0x800)) * 300
        plugin(game, data / 'Unbounded.esm', master, 'FLST', payload)
        cases.append({'game': game, 'plugin': 'Unbounded.esm', 'entries': 300, 'oversized': False})
    return cases


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--exe', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--baseline', action='store_true')
    args = cli.parse_args()
    exe = args.exe.resolve(strict=True)
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    cases = generate(root / 'fixtures')
    inputs = {str(p.relative_to(root)): digest(p) for p in (root / 'fixtures').rglob('*.esm')}
    report = {'issue': 'https://github.com/TES5Edit/TES5Edit/issues/1382',
              'executable_sha256': digest(exe), 'baseline': args.baseline, 'inputs': inputs, 'results': []}
    for case in cases:
        data = root / 'fixtures' / case['game']
        run = root / 'runs' / case['game'] / case['plugin']
        run.mkdir(parents=True)
        command = [str(exe), '-dump', '-' + case['game'], '-nobsa', '-l:en', '-d:' + str(data),
                   '-check', str(data / case['plugin'])]
        (run / 'command.json').write_text(json.dumps(command, indent=2))
        timed_out = False
        with (run / 'stdout.log').open('wb') as out, (run / 'stderr.log').open('wb') as err:
            try:
                process = subprocess.run(command, cwd=run, stdin=subprocess.DEVNULL,
                                         stdout=out, stderr=err, timeout=30)
                code = process.returncode
            except subprocess.TimeoutExpired:
                timed_out, code = True, None
        stdout = (run / 'stdout.log').read_text(errors='replace')
        stderr = (run / 'stderr.log').read_text(errors='replace')
        expected = case['oversized'] and not args.baseline
        found = 'entries exceed the maximum of 255' in stdout
        complete = ('Finished loading record. Starting Dump.' in stderr and
                    'All Done.' in stderr and 'Unexpected Error' not in stderr)
        passed = (not timed_out and complete and code in (0, 1) and found == expected
                  and (bool(stdout.strip()) if expected else not stdout.strip()))
        report['results'].append(dict(case, native_exit_code=code, timed_out=timed_out,
                                     completed=complete, diagnostic_found=found, passed=passed,
                                     warnings=[line for line in stderr.splitlines() if 'Warning:' in line]))
    report['inputs_unchanged'] = all(digest(root / name) == value for name, value in inputs.items())
    report['tool_unchanged'] = digest(exe) == report['executable_sha256']
    report['passed'] = (all(r['passed'] for r in report['results']) and
                        report['inputs_unchanged'] and report['tool_unchanged'])
    (root / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
