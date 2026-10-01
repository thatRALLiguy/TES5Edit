"""Generate synthetic, non-game mixed-master fixtures and run an xDump binary.

Never point this at a game Data directory. Output must be a new directory.
This tests reference resolution, not gameplay or preservation of arbitrary plugins.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess


def subrecord(signature, data):
    return signature.encode('ascii') + struct.pack('<H', len(data)) + data


def record(signature, form_id, data, flags=0):
    return struct.pack('<4sIIIIHH', signature.encode('ascii'), len(data), flags,
                       form_id, 0, 559, 0) + data


def plugin(path, masters, flags, forms):
    header = subrecord('HEDR', struct.pack('<fII', 0.96, len(forms) + 1, 0x900))
    header += subrecord('CNAM', b'xEdit regression fixture\0')
    for master in masters:
        header += subrecord('MAST', master.encode('ascii') + b'\0')
    header += subrecord('INCC', struct.pack('<I', 0))
    content = b''
    for form_id, editor_id, references in forms:
        data = subrecord('EDID', editor_id.encode('ascii') + b'\0')
        for reference in references:
            data += subrecord('LNAM', struct.pack('<I', reference))
        content += record('FLST', form_id, data)
    group = struct.pack('<4sI4sIII', b'GRUP', len(content) + 24, b'FLST', 0, 0, 0)
    path.write_bytes(record('TES4', 0, header, flags) + group + content)


def generate(data):
    data.mkdir()
    plugin(data / 'Starfield.esm', [], 1, [(0x800, 'BaseFixture', [])])
    plugin(data / 'Full.esm', ['Starfield.esm'], 1,
           [(0x01000800, 'FullFixture', [])])
    plugin(data / 'Small.esm', ['Starfield.esm'], 0x101,
           [(0x01000800, 'SmallFixture', [])])
    plugin(data / 'Medium.esm', ['Starfield.esm'], 0x401,
           [(0x01000800, 'MediumFixture', [])])
    # Interleave scales: the full slot is 1 although Full.esm is MAST entry 3.
    masters = ['Starfield.esm', 'Small.esm', 'Medium.esm', 'Full.esm']
    cases = {
        'FullReference.esm': (0x01000800, 'FullFixture'),
        'SmallReference.esm': (0xFE000800, 'SmallFixture'),
        'MediumReference.esm': (0xFD000800, 'MediumFixture'),
    }
    for filename, (reference, _) in cases.items():
        plugin(data / filename, masters, 1,
               [(0x02000800, 'ReferenceFixture', [reference])])
    plugin(data / 'UnresolvedReference.esm', masters, 1,
           [(0x02000800, 'BrokenReferenceFixture', [0xFE000899])])
    return cases


def hashes(data):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(data.glob('*.esm'))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    exe = args.exe.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    data = output / 'Data'
    cases = generate(data)
    before = hashes(data)
    results = []
    for name, expected in [*( (n, e[1]) for n, e in cases.items()),
                            ('UnresolvedReference.esm', None)]:
        command = [str(exe), '-dump', '-SF1', '-nobsa', '-l:en', f'-d:{data}', str(data / name)]
        run = subprocess.run(command, cwd=output, capture_output=True, timeout=120)
        (output / (name + '.stdout.txt')).write_bytes(run.stdout)
        (output / (name + '.stderr.txt')).write_bytes(run.stderr)
        text = run.stdout.decode('utf-8', errors='replace')
        errors = run.stderr.decode('utf-8', errors='replace')
        # Assert a field-level target identity, not just a successful exit.
        reference_lines = [line for line in text.splitlines() if 'LNAM' in line]
        passed = (run.returncode == 0 and 'All Done.' in errors and 'Unexpected Error:' not in errors
                  and len(reference_lines) == 1)
        if passed:
            if expected:
                passed = expected in reference_lines[0]
            else:
                passed = 'could not be resolved' in reference_lines[0].lower()
        results.append({'plugin': name, 'expected': expected, 'passed': passed,
                        'returncode': run.returncode, 'reference_lines': reference_lines})
    unchanged = hashes(data) == before
    report = {'executable': str(exe),
              'executable_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
              'fixtures_unchanged': unchanged, 'fixture_sha256': before, 'cases': results}
    (output / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if unchanged and all(r['passed'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
