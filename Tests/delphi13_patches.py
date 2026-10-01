"""Verify dependency patches against their pinned originals without changing the checkout."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def git(directory, *args):
    return subprocess.check_output(["git", "-C", str(directory), *args])


def main():
    entries = re.findall(
        r"Name = '([^']+)'; Revision = '([^']+)'; Patch = '([^']+)'",
        (ROOT / "Tools/Prepare-Delphi13.ps1").read_text(encoding="utf-8"),
    )
    assert entries, "No dependency patches found"
    for name, revision, patch_name in entries:
        dependency = ROOT / "External" / name
        assert git(dependency, "rev-parse", "HEAD").decode().strip() == revision, name
        patch = ROOT / "Tools/compatibility" / patch_name
        files = re.findall(r"^\+\+\+ b/(.+)$", patch.read_text(encoding="latin1"), re.M)
        files = [name.rstrip("\r") for name in files]
        assert files, patch_name
        with tempfile.TemporaryDirectory(prefix="xedit-delphi13-") as directory:
            scratch = Path(directory)
            for relative in files:
                target = scratch / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(git(dependency, "show", f"{revision}:{relative}"))
            git(scratch, "apply", "--check", str(patch))
            git(scratch, "apply", str(patch))
            for relative in files:
                # Git's Windows checkout may expand LF to CRLF; compare source content.
                expected = (dependency / relative).read_bytes().replace(b"\r\n", b"\n")
                actual = (scratch / relative).read_bytes().replace(b"\r\n", b"\n")
                assert actual == expected, relative
            git(scratch, "apply", "--reverse", "--check", str(patch))
        print(f"PASS: {name}: pinned source -> patch -> matching working source ({len(files)} files)")


if __name__ == "__main__":
    main()
