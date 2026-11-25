import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from migrate_version_text import same_arguments, is_display_asset_field


class GodsContextRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = json.loads((ROOT / 'assets/prerelease9-4.1-review.json').read_text('utf8'))

    def test_shared_source_title_keeps_distinct_tier_names(self):
        rows = [r for r in self.review['text_assets'] if r['asset'] == 'ShootingAlmanacIndex' and r['path'][-1] == 'title']
        self.assertEqual([r['english'] for r in rows], ['Vanguard', 'Vanguard - A', 'Vanguard - B', 'Vanguard - X'])
        self.assertEqual([r['entry_id'] for r in rows], ['Tactics:Shooting_铁卫1', 'Tactics:Shooting_铁卫2', 'Tactics:Shooting_铁卫3', 'Tactics:Shooting_铁卫Max'])
        self.assertEqual(len({r['source'] for r in rows[:3]}), 1)

    def test_plant_reference_and_variant_polarity_are_preserved(self):
        rows = {tuple(r['path']): r for r in self.review['text_assets'] if r['asset'] == 'ShootingAlmanacIndex'}
        self.assertIn('[[plant:BlackHoleTorch]]', rows[('entries', 21, 'description')]['english'])
        self.assertIn('neither Pea Zombies nor Zombie Gacha', rows[('entries', 3, 'condition')]['english'])
        self.assertIn('Pea Zombies or Zombie Gacha', rows[('entries', 4, 'condition')]['english'])

    def test_edits_are_guarded_display_fields_with_intact_arguments(self):
        self.assertEqual(self.review['metadata'], [])
        for row in self.review['text_assets']:
            self.assertTrue(is_display_asset_field(row['asset'], row['path']))
            self.assertEqual(hashlib.sha256(row['source'].encode()).hexdigest(), row['source_sha256'])
            self.assertTrue(same_arguments(row['source'], row['english']))
            self.assertEqual(re.findall(r'\[\[.*?\]\]', row['source']), re.findall(r'\[\[.*?\]\]', row['english']))
        for row in self.review['context']:
            self.assertTrue(same_arguments(row['source'], row['english']))

    def test_trident_article_retains_android_duration_and_damage_floor(self):
        row = next(r for r in self.review['text_assets'] if r['asset'] == 'DetailStrings' and r['path'][-1] == 'text')
        for value in ('20%', '60', '25%', '5 seconds'):
            self.assertIn(value, row['english'])


if __name__ == '__main__':
    unittest.main()
