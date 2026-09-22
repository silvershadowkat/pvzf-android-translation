import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from migrate_version_text import quarantine_duplicate_pc_ids, same_arguments, normalized


class MajorVersionMigrationTests(unittest.TestCase):
    def test_conflicting_pc_ids_are_quarantined_without_guessing(self):
        source = {'plants': [{'seedType': 5003, 'name': 'A'},
                             {'seedType': 5003, 'name': 'B'},
                             {'seedType': 7, 'name': 'C'}]}
        result, duplicate_ids = quarantine_duplicate_pc_ids(source, 'plants', 'seedType')
        self.assertEqual(duplicate_ids, [5003])
        self.assertEqual(result, {'plants': [{'seedType': 7, 'name': 'C'}]})
        self.assertEqual(len(source['plants']), 3)

    def test_runtime_format_precision_cannot_be_dropped(self):
        self.assertFalse(same_arguments('剩余{0:F1}秒', 'Remaining: {0}s'))
        self.assertTrue(same_arguments('{0:F1} / {1}', '{1}: {0:F1}'))

    def test_almanac_typography_preserves_content_and_balances_tags(self):
        self.assertEqual(normalized('<size=36><color=red>Damage: 20</size>', True),
                         '<color=red>Damage: 20</color>')


if __name__ == '__main__':
    unittest.main()
