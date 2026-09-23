import struct
import sys
import unittest
import contextlib
import io
import tempfile
import zipfile
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from protected_metadata import (PROTECTED_METADATA_STRINGS, protected_changes,
                                verify_metadata, restore_metadata)
from build_metadata_translation import (parse_metadata, translate_literal,
                                        translate_complete_pc_literal)


def metadata(strings):
    encoded = [s.encode('utf8') for s in strings]
    data = bytearray(32 + len(strings) * 8)
    struct.pack_into('<6I', data, 0, 0xfab11baf, 31, 32, len(strings)*8,
                     len(data), sum(map(len, encoded)))
    offset = 0
    for i, value in enumerate(encoded):
        struct.pack_into('<2I', data, 32+i*8, len(value), offset)
        offset += len(value)
    return bytes(data) + b''.join(encoded)


class ProtectedMetadataTests(unittest.TestCase):
    def test_pc_mapping_cannot_override_internal_metadata_key(self):
        for source in PROTECTED_METADATA_STRINGS:
            with self.subTest(source=source):
                result, method = translate_literal(source, {source: 'English'}, {source}, {}, [])
                self.assertEqual(result, source)
                self.assertEqual(method, 'protected_runtime_metadata')

    def test_display_translation_remains_available_without_blanket_substring_ban(self):
        self.assertEqual(translate_complete_pc_literal('护盾保护', {'护盾保护': 'Enchanted Shield'}, [])[0], 'Enchanted Shield')
        self.assertEqual(protected_changes(['升级说明', '试炼词条'], ['Upgrade instructions', 'Trial Modifiers']), [])

    def test_restores_shared_runtime_keys_but_preserves_other_translations(self):
        source = ['升级', '试炼：', '护盾保护', '爆炸保护', '诸神币', '木桩']
        target = ['Upgrade', 'Trial: ', 'Enchanted Shield', 'Blast Protection', 'God Coins', '木桩']
        original, candidate = metadata(source), metadata(target)
        with self.assertRaises(ValueError):
            verify_metadata(original, candidate)
        restored, changes = restore_metadata(original, candidate)
        self.assertEqual([s.text for s in parse_metadata(restored)[1]], source[:4]+target[4:])
        self.assertEqual([c['index'] for c in changes], [0, 1, 2, 3])
        self.assertEqual(verify_metadata(original, restored)['verified_slots'], 5)
        self.assertEqual(restore_metadata(original, restored), (restored, []))

    def test_duplicate_slots_checked_and_mismatched_versions_rejected(self):
        self.assertEqual([r['index'] for r in protected_changes(['升级','升级'], ['Upgrade','升级'])], [0])
        with self.assertRaises(ValueError):
            protected_changes(['升级'], [])

    def test_unused_original_bytes_do_not_hide_a_translated_active_slot(self):
        original = metadata(['升级'])
        changed = metadata(['Upgrade']) + '升级'.encode('utf8')
        self.assertIn('升级'.encode('utf8'), changed)
        with self.assertRaises(ValueError):
            verify_metadata(original, changed)

    def test_packager_rejects_late_translation_before_creating_apk(self):
        import package_apk_payload as package
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original = metadata(['升级', '诸神币'])
            candidate = metadata(['Upgrade', 'God Coins'])
            with zipfile.ZipFile(root/'base.apk', 'w') as z:
                z.writestr(package.METADATA_ENTRY, original)
                z.writestr(package.DATA_ENTRY, b'original bundle')
            (root/'metadata.dat').write_bytes(candidate)
            (root/'bundle').write_bytes(b'translated bundle')
            args = ['package', '--base-apk', str(root/'base.apk'),
                    '--data-bundle', str(root/'bundle'), '--metadata', str(root/'metadata.dat'),
                    '--output', str(root/'out.apk'), '--report', str(root/'report.json')]
            with patch.object(sys, 'argv', args), self.assertRaises(ValueError):
                package.main()
            self.assertFalse((root/'out.apk').exists())
            (root/'metadata.dat').write_bytes(restore_metadata(original, candidate)[0])
            with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(package.main(), 0)
            with zipfile.ZipFile(root/'out.apk') as z:
                verify_metadata(original, z.read(package.METADATA_ENTRY))


if __name__ == '__main__':
    unittest.main()
