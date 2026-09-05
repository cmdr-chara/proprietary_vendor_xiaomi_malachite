#!/usr/bin/env python3
"""Read five preserved AArch64 blobs and check their selected DT_NEEDED contracts.

Uses readelf, never dlopen/ldd or execution. This checks dependency names, not
provider availability, symbol ABI, binary patch correctness, or runtime behavior.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import struct
import subprocess

BASELINE = '28a87d5dda2c787dc839e76162ded180d59d5d42'
FIXUP_REVISION = '0f54832a13d8b4a79328c96025e3aac73b124ba8'
CONTRACTS = {
    'vendor/lib64/libmicamera_hal_core.so': (
        {'libprocessgroup_shim.so', 'libui_shim.so', 'libtinyxml2-v34.so'}, {'libtinyxml2.so'}),
    'vendor/lib64/libmialgoengine.so': ({'libprocessgroup_shim.so'}, set()),
    'vendor/lib64/libcodec2_fsr.so': (
        {'android.hardware.graphics.allocator-V2-ndk.so', 'android.hardware.graphics.common-V7-ndk.so'},
        {'android.hardware.graphics.allocator-V1-ndk.so', 'android.hardware.graphics.common-V4-ndk.so'}),
    'vendor/lib64/hw/audio.primary.mt6878.so': (
        {'libalsautils-stock.so', 'libtinyxml2-v34.so'}, {'libalsautils.so', 'libtinyxml2.so'}),
    'vendor/lib64/hw/vendor.mediatek.hardware.pq_aidl-impl.so': (
        {'libui_shim.so', 'libtinyxml2-v34.so'}, {'libtinyxml2.so'}),
}
MAX_BYTES = 256 * 1024 * 1024


def elf_header(data: bytes) -> None:
    if len(data) < 64 or data[:7] != b'\x7fELF\x02\x01\x01':
        raise ValueError('Expected an ELF64 little-endian current-version header')
    if struct.unpack_from('<HHI', data, 16) != (3, 183, 1):
        raise ValueError('Expected an AArch64 ET_DYN object, not executable host code')
    if struct.unpack_from('<H', data, 52)[0] != 64:
        raise ValueError('Invalid ELF64 header size')


def needed_names(text: str) -> set[str]:
    names = set()
    for line in text.splitlines():
        if '(NEEDED)' not in line:
            continue
        match = re.search(r'\(NEEDED\)\s+Shared library: \[([^\]\r\n]+)\]\s*$', line)
        if not match:
            raise ValueError('Unrecognized readelf dependency record')
        names.add(match.group(1))
    if not names:
        raise ValueError('No DT_NEEDED entries found in a selected dynamic library')
    return names


def inspect(root: Path, relative: str, required: set[str], forbidden: set[str],
            readelf: str = 'readelf') -> dict:
    rel = PurePosixPath(relative)
    if (not rel.parts or rel.is_absolute() or '..' in rel.parts or
            str(rel) != relative or '\\' in relative or '\x00' in relative):
        raise ValueError('Unsafe relative blob path')
    root = root.resolve(strict=True)
    path = root
    for part in rel.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Symlink input is not a preserved regular blob')
    if not path.is_file() or not 64 <= path.stat().st_size <= MAX_BYTES:
        raise ValueError('Missing, truncated or oversized input')
    data = path.read_bytes()
    elf_header(data)
    run = subprocess.run([readelf, '-W', '-d', str(path)], check=True,
                         capture_output=True, text=True, timeout=30,
                         env=dict(os.environ, LC_ALL='C'))
    needed = needed_names(run.stdout)
    missing, unexpected = required - needed, forbidden & needed
    return {'path': relative, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
            'needed': sorted(needed), 'required_missing': sorted(missing),
            'forbidden_present': sorted(unexpected),
            'status': 'FAIL' if missing or unexpected else 'PASS',
            'readelf_diagnostics': run.stderr.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1] / 'proprietary')
    parser.add_argument('--readelf', default='readelf')
    args = parser.parse_args()
    results = []
    for path, (required, forbidden) in CONTRACTS.items():
        try:
            results.append(inspect(args.root, path, required, forbidden, args.readelf))
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            results.append({'path': path, 'status': 'FAIL', 'error': f'{type(error).__name__}: {error}'})
    failed = any(r['status'] != 'PASS' for r in results)
    print(json.dumps({'schema_version': 1, 'status': 'FAIL' if failed else 'PASS',
                      'scope': 'Five selected ELF dependency-name contracts only',
                      'expected_vendor_baseline': BASELINE, 'device_fixup_revision': FIXUP_REVISION,
                      'runtime_compatibility': 'GAP', 'release_status': 'BLOCKED',
                      'artifacts': results}, indent=2, sort_keys=True))
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
