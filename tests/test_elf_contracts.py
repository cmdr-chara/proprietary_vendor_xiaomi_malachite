"""Read-only ELF checks, including an actual cross-linked ARM64 fixture; never execute it."""
import importlib.util
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('audit', ROOT / 'tools/audit_elf_contracts.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class ElfContracts(unittest.TestCase):
    def header(self):
        data = bytearray(64)
        data[:7] = b'\x7fELF\x02\x01\x01'
        struct.pack_into('<HHI', data, 16, 3, 183, 1)
        struct.pack_into('<H', data, 52, 64)
        return data

    def test_valid_header(self):
        audit.elf_header(self.header())

    def test_rejects_wrong_headers(self):
        for offset, value in ((0, 0), (4, 1), (5, 2), (6, 0), (16, 2), (18, 62), (20, 0), (52, 0)):
            data = self.header(); data[offset] = value
            with self.subTest(offset=offset), self.assertRaises(ValueError): audit.elf_header(data)

    def test_rejects_truncated_header(self):
        with self.assertRaises(ValueError): audit.elf_header(self.header()[:63])

    def test_reads_needed_names(self):
        text = ' 0x1 (NEEDED) Shared library: [libui_shim.so]\n 0xe (SONAME) Library soname: [self.so]\n'
        self.assertEqual(audit.needed_names(text), {'libui_shim.so'})

    def test_requires_unambiguous_needed_records(self):
        for text in ('', '(NEEDED) nope', '(NEEDED) Shared library: []'):
            with self.subTest(text=text), self.assertRaises(ValueError): audit.needed_names(text)

    def test_rejects_missing_and_unsafe_input(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ('missing.so', '../a', '/a', 'x//a', 'x\\a'):
                with self.subTest(name=name), self.assertRaises(ValueError): audit.inspect(root, name, set(), set())

    def test_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / 'a').write_bytes(self.header())
            (root / 'link').symlink_to(root / 'a')
            with self.assertRaises(ValueError): audit.inspect(root, 'link', set(), set())

    def test_real_arm64_dependency_contract(self):
        for tool in ('clang', 'ld.lld', 'readelf'):
            self.assertIsNotNone(shutil.which(tool), f'{tool} is required, not silently skipped')
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'provider.c').write_text('int provided(void) { return 7; }\n')
            (root / 'consumer.c').write_text('extern int provided(void); int consume(void) { return provided(); }\n')
            for name in ('provider', 'consumer'):
                subprocess.run(['clang', '--target=aarch64-linux-gnu', '-fPIC', '-c', str(root / (name + '.c')),
                                '-o', str(root / (name + '.o'))], check=True, timeout=30)
            subprocess.run(['ld.lld', '-shared', '-soname', 'libui_shim.so', str(root / 'provider.o'),
                            '-o', str(root / 'libui_shim.so')], check=True, timeout=30)
            subprocess.run(['ld.lld', '-shared', str(root / 'consumer.o'), '-L' + td, '-l:libui_shim.so',
                            '-o', str(root / 'consumer.so')], check=True, timeout=30)
            good = audit.inspect(root, 'consumer.so', {'libui_shim.so'}, {'libtinyxml2.so'})
            self.assertEqual(good['status'], 'PASS')
            self.assertEqual(len(good['sha256']), 64)
            self.assertEqual(audit.inspect(root, 'consumer.so', {'missing.so'}, set())['status'], 'FAIL')
            self.assertEqual(audit.inspect(root, 'consumer.so', set(), {'libui_shim.so'})['status'], 'FAIL')
            with self.assertRaises(subprocess.CalledProcessError):
                audit.inspect(root, 'consumer.so', set(), set(), 'false')


if __name__ == '__main__': unittest.main()
