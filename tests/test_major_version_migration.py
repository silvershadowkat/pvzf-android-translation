import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from migrate_version_text import quarantine_duplicate_pc_ids, same_arguments, normalized, is_display_asset_field


class MajorVersionMigrationTests(unittest.TestCase):
    def test_catalog_reflection_and_lookup_strings_are_not_display_text(self):
        for path in (('plants', 23, 'buffs', 2, 'type'), ('plants', 0, 'configType'),
                     ('roots', 0), ('entries', 0, 'category'), ('entries', 0, 'quality'),
                     ('entries', 0, 'id'), ('portraits', 0, 'resourcePath')):
            self.assertFalse(is_display_asset_field('ShootingAlmanacIndex', path))
        self.assertTrue(is_display_asset_field('ShootingAlmanacIndex', ('entries', 0, 'description')))
        self.assertTrue(is_display_asset_field('ShootingAlmanacIndex', ('entries', 0, 'title')))

    def test_unknown_type_fields_and_line_break_tables_are_protected(self):
        self.assertFalse(is_display_asset_field('AnotherCatalog', ('items', 0, 'type')))
        self.assertFalse(is_display_asset_field('LineBreaking Leading Characters', ()))
        self.assertTrue(is_display_asset_field('level123', ('tips',)))

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
