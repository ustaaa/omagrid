#!/usr/bin/env python3
"""Exercise pilot installer ownership/path checks in temporary homes. No executable is run."""
from pathlib import Path
import io
import os
import platform
import struct
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
APP = 'io.github.ustaaa.OmaGrid'
source = (ROOT / 'packaging/linux/install-pilot.sh').read_text().split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
# Permit the filesystem-only installer test on macOS too; synthetic ELF files are never launched.
driver = "import platform; platform.system = lambda: 'Linux'; exec(compile(" + repr(source) + ", 'install-pilot.sh', 'exec'))"


def invoke(home, *args, ok=True):
    result = subprocess.run([sys.executable, '-c', driver, *map(str, args)], env={**os.environ, 'HOME': str(home)}, capture_output=True, text=True)
    assert (result.returncode == 0) == ok, result.stdout + result.stderr
    return result.stdout + result.stderr


def fixture(path, extra=None):
    with tarfile.open(path, 'w:gz') as archive:
        def add(name, data, mode=0o644):
            item = tarfile.TarInfo('omagrid-test/' + name)
            item.size = len(data)
            item.mode = mode
            archive.addfile(item, io.BytesIO(data))
        elf = bytearray(20)
        elf[:6] = b'\x7fELF\x02\x01'
        elf[18:20] = struct.pack('<H', 62 if platform.machine() == 'x86_64' else 183)
        for name in ('omagrid', 'omagrid-cli'):
            add('bin/' + name, elf, 0o755)
        add(f'share/applications/{APP}.desktop', (ROOT / f'packaging/linux/{APP}.desktop').read_bytes())
        for size in (16, 24, 32, 48, 64, 128, 256, 512):
            add(f'share/icons/hicolor/{size}x{size}/apps/{APP}.png', (ROOT / f'assets/omagrid-icon/{size}/{APP}.png').read_bytes())
        add(f'share/icons/hicolor/scalable/apps/{APP}.svg', (ROOT / f'assets/omagrid-icon/{APP}.svg').read_bytes())
        if extra:
            archive.addfile(extra)


with tempfile.TemporaryDirectory(prefix='omagrid-installer-test-') as temporary:
    root = Path(temporary)
    home = root / 'home with spaces'
    home.mkdir()
    archive = root / 'good.tar.gz'
    fixture(archive)
    invoke(home, archive, 'first', '--dry-run')
    assert not (home / '.local').exists(), 'Dry run wrote files'
    invoke(home, archive, 'first')
    base = home / '.local/share/omagrid'
    desktop = (home / f'.local/share/applications/{APP}.desktop').read_text()
    assert f'Exec="{base}/current/bin/omagrid" %F' in desktop
    assert f'TryExec={base}/current/bin/omagrid' in desktop
    invoke(home, archive, 'first', ok=False)
    invoke(home, archive, 'second')
    assert os.readlink(base / 'current') == 'versions/second'
    invoke(home, '--uninstall')
    assert not (base / 'current').is_symlink()
    assert (base / 'versions/first').is_dir() and (base / 'versions/second').is_dir()
    assert not (home / '.local/bin/omagrid').is_symlink()
    collision = home / '.local/bin/omagrid'
    collision.write_text('unrelated')
    invoke(home, archive, 'third', ok=False)
    assert collision.read_text() == 'unrelated'
    collision.unlink()
    collision.symlink_to('/unrelated/file')
    invoke(home, archive, 'third', ok=False)
    assert os.readlink(collision) == '/unrelated/file'
    collision.unlink()
    for name, entry in [('traversal', tarfile.TarInfo('omagrid-test/../../escape')), ('symlink', tarfile.TarInfo('omagrid-test/bin/link'))]:
        if name == 'symlink':
            entry.type = tarfile.SYMTYPE
            entry.linkname = '/etc/passwd'
        bad = root / f'{name}.tar.gz'
        fixture(bad, entry)
        invoke(home, bad, 'third', ok=False)
        assert not (base / 'versions/third').exists()
    assert not (root / 'escape').exists()
print('PASS: dry run, install, upgrade, duplicate ID, uninstall, collision, traversal and symlink checks')
