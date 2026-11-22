import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from apply_41_prerelease7 import replace_guarded
from migrate_version_text import is_display_asset_field, same_arguments
from protected_metadata import PROTECTED_METADATA_STRINGS


class AlmanacAuditRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = json.loads((ROOT / 'assets/prerelease7-4.1-review.json').read_text('utf8'))
        cls.fields = {(r['asset'], r['id']): r for r in cls.review['fields']}

    def plant(self, id): return self.fields['LawnStrings', id]['english']

    def test_census_and_unique_entities(self):
        self.assertEqual(self.review['counts']['plant_entries_audited'], 742)
        self.assertEqual(self.review['counts']['zombie_entries_audited'], 238)
        self.assertEqual(len(self.fields), len(self.review['fields']))
        inventory = json.loads((ROOT / 'docs/testing/ANDROID41-PRE7-STATS-AUDIT.json').read_text('utf8'))['entities']
        self.assertEqual(len(inventory), 980)
        self.assertEqual(len({(r['group'], r['id']) for r in inventory}), 980)
        self.assertTrue(all(r['id'] == r['data_asset']['id'] for r in inventory))

    def test_intervals_follow_android_data_including_stale_source_exceptions(self):
        for id, text in [(1035, '20/2.25s'), (1170, '20/2s'), (952, '60/3s'), (957, '300/0.5s')]:
            self.assertIn(text, self.plant(id))
        self.assertNotIn(('LawnStrings', 1171), self.fields)  # Spuddy's 600 damage is correct.

    def test_persistent_hits_are_not_confused_with_firing_frequency(self):
        self.assertIn('fires every 1.5s', self.plant(947))
        self.assertIn('0.02s for 5s', self.plant(947))
        self.assertIn('fires every 3s', self.plant(1220))
        self.assertIn('0.02s for 1.5s', self.plant(1220))
        for id in (1043, 1177, 1198, 1339, 1340, 1356, 1373, 1381, 1382, 1383):
            self.assertNotIn(('LawnStrings', id), self.fields)

    def test_projectile_damage_and_derived_health_are_preserved(self):
        for id in (31, 49, 52, 70, 73, 100, 101, 102, 104, 108, 112, 113, 114, 118, 119, 130, 131, 211, 214, 223, 225, 229, 230, 252, 329):
            self.assertNotIn(('ZombieStrings', id), self.fields)
        self.assertNotIn('80/0.1s', self.fields['ZombieStrings', 235]['english'])
        self.assertNotIn('force shield', self.fields['ZombieStrings', 94]['english'])
        self.assertEqual(self.fields['ZombieStrings', 94]['game_evidence']['second_armor_health'], 0)

    def test_every_edit_is_source_guarded_and_preserves_placeholders(self):
        for row in self.review['fields'] + self.review['text_assets'] + self.review['metadata']:
            with self.subTest(row=row.get('id', row.get('index', row.get('path')))):
                self.assertEqual(replace_guarded(row['source'], row['previous'], row), row['english'])
                with self.assertRaises(AssertionError): replace_guarded(row['source'] + 'x', row['previous'], row)
                with self.assertRaises(AssertionError): replace_guarded(row['source'], row['previous'] + 'x', row)
                self.assertFalse(re.search('[\u3400-\u9fff]', row['english']))
                self.assertTrue(same_arguments(row['source'], row['english']))
        for row in self.review['metadata']: self.assertNotIn(row['source'], PROTECTED_METADATA_STRINGS)
        for row in self.review['text_assets']: self.assertTrue(is_display_asset_field(row['asset'], row['path']))

    def test_invalid_upstream_replacements_are_excluded(self):
        self.assertFalse(self.review['runtime_regex'])
        for value in self.review['runtime_exact'].values():
            self.assertNotIn('{0s}', value)
            self.assertNotIn('Untranslated', value)
            self.assertNotEqual(value, 'N/A')
        self.assertTrue(any('{0s}' in r['reason'] for r in self.review['upstream_exclusions']))


if __name__ == '__main__': unittest.main()
