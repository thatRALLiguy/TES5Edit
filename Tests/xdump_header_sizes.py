"""Exercise plugin header bounds in TES3 (16), TES4 (20), and SF1 (24).

All inputs are synthetic; the output directory must not already exist.
The old binary is expected to fail the truncated-header assertions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from starfield_master_ids import generate, hashes, subrecord


def tes3_plugin():
    def sub(sig, data):
        return sig.encode('ascii') + struct.pack('<I', len(data)) + data

    def rec(sig, data):
        return struct.pack('<4sIII', sig.encode('ascii'), len(data), 0, 0) + data

    header = sub('HEDR', struct.pack('<fI32s256sI', 1.3, 1,
                 b'xEdit regression fixture', b'Synthetic test only', 1))
    glob = sub('NAME', b'HeaderSizeFixture\0') + sub('FNAM', b'f')
    glob += sub('FLTV', struct.pack('<f', 1.0))
    return rec('TES3', header) + rec('GLOB', glob)


def tes4_plugin():
    def rec(sig, form, data, flags=0):
        return struct.pack('<4sIIII', sig.encode('ascii'), len(data), flags, form, 0) + data

    header = subrecord('HEDR', struct.pack('<fII', 0.8, 2, 0x801))
    header += subrecord('CNAM', b'xEdit regression fixture\0')
    glob = subrecord('EDID', b'HeaderSizeFixture\0') + subrecord('FNAM', b'f')
    glob += subrecord('FLTV', struct.pack('<f', 1.0))
    content = rec('GLOB', 0x800, glob)
    group = struct.pack('<4sI4sII', b'GRUP', len(content) + 20, b'GLOB', 0, 0)
    return rec('TES4', 0, header, 1) + group + content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    exe = args.exe.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    results = []
    all_unchanged = True
    for mode, header_size, name, payload in (
        ('TES3', 16, 'Morrowind.esm', tes3_plugin()),
        ('TES4', 20, 'Oblivion.esm', tes4_plugin()),
        ('SF1', 24, 'Starfield.esm', None),
    ):
        data = output / mode
        if payload is None:
            generate(data)
        else:
            data.mkdir()
            (data / name).write_bytes(payload)
        for size in (1, 4, header_size - 1):
            (data / f'Truncated{size}.esm').write_bytes((data / name).read_bytes()[:size])
        before = hashes(data)
        cases = [(name, False)] + [(f'Truncated{s}.esm', True) for s in (1, 4, header_size - 1)]
        for filename, invalid in cases:
            command = [str(exe), '-dump', '-' + mode, '-nobsa', '-l:en',
                       f'-d:{data}', '-check', str(data / filename)]
            run = subprocess.run(command, cwd=output, capture_output=True, timeout=120)
            prefix = output / (mode + '-' + filename)
            Path(str(prefix) + '.stdout.txt').write_bytes(run.stdout)
            Path(str(prefix) + '.stderr.txt').write_bytes(run.stderr)
            text = (run.stdout + run.stderr).decode('utf-8', errors='replace').lower()
            if invalid:
                passed = run.returncode == 2 and 'truncated plugin header' in text
            else:
                passed = (run.returncode == 0 and 'all done.' in text
                          and ' -> ' not in text and 'unexpected error:' not in text)
            results.append({'mode': mode, 'file': filename, 'header_size': header_size,
                            'invalid': invalid, 'returncode': run.returncode, 'passed': passed})
        unchanged = hashes(data) == before
        all_unchanged = all_unchanged and unchanged
    report = {'executable': str(exe),
              'executable_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
              'fixtures_unchanged': all_unchanged, 'cases': results}
    (output / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if all_unchanged and all(r['passed'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
