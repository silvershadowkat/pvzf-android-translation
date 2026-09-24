import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from apply_reviewed_display_patch import guarded_text, metadata_target, patch_asset


class ReviewedDisplayPatchTests(unittest.TestCase):
    def test_rejects_runtime_keys_and_stale_source(self):
        rule = {'source': '升级', 'before': '升级', 'target': 'Upgrade'}
        with self.assertRaises(ValueError):
            metadata_target('升级', '升级', rule)
        rule = {'source': ' · 被动', 'before': ' · 被动', 'target': ' · Passive'}
        self.assertEqual(metadata_target(rule['source'], rule['before'], rule), ' · Passive')
        with self.assertRaises(ValueError):
            guarded_text(rule['source'], 'Previously revised', rule)

    def test_catalog_edit_cannot_change_ids_or_reflection_types(self):
        source = {'entries': [{'id': '原始标识', 'description': '效果'}],
                  'plants': [{'configType': 'Namespace.Class+Nested'}]}
        for path in (['entries', 0, 'id'], ['plants', 0, 'configType']):
            with self.assertRaises(ValueError):
                patch_asset(source, copy.deepcopy(source), 'ShootingAlmanacIndex',
                            {'path': path, 'source': 'irrelevant', 'before': 'irrelevant', 'target': 'English'})
        current = copy.deepcopy(source)
        patch_asset(source, current, 'ShootingAlmanacIndex',
                    {'path': ['entries', 0, 'description'], 'source': '效果', 'before': '效果', 'target': 'Effect'})
        self.assertEqual(current['entries'][0]['id'], source['entries'][0]['id'])
        self.assertEqual(current['plants'], source['plants'])

    def test_preserves_plant_tokens_and_format_precision(self):
        source = '[[plant:OriginalType]] 获得 {0:F0}%'
        rule = {'source': source, 'before': source, 'target': '[[plant:OriginalType]] gains {0:F0}%'}
        self.assertEqual(guarded_text(source, source, rule), rule['target'])
        for target in ('[[plant:OtherType]] gains {0:F0}%', '[[plant:OriginalType]] gains {0}%'):
            with self.assertRaises(ValueError):
                guarded_text(source, source, dict(rule, target=target))


if __name__ == '__main__':
    unittest.main()
