import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from apply_android_ui_feedback import navigation_label, render_changelog
from migrate_version_text import same_arguments


class AndroidUiFeedbackTests(unittest.TestCase):
    def test_navigation_override_is_context_specific(self):
        rule = {'hierarchy': ['text', 'Goback', 'AlmanacMenu'], 'source': '关闭', 'current': 'Disabled', 'target': 'Back'}
        self.assertEqual(navigation_label('Disabled', rule['hierarchy'], [rule]), 'Back')
        self.assertEqual(navigation_label('Disabled', ['State', 'ModifierCard'], [rule]), 'Disabled')
        self.assertEqual(navigation_label('Cancel', rule['hierarchy'], [rule]), 'Cancel')

    def test_changelog_refuses_changed_source(self):
        config = {'source_sha256': hashlib.sha256(b'original').hexdigest(), 'lines': {}}
        with self.assertRaises(AssertionError):
            render_changelog('changed', config, {})

    def test_changelog_uses_canonical_name_and_preserves_unknown_prose(self):
        source = '新植物\r\n未翻译名称\r\n'
        config = {'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                  'lines': {'新植物': 'New plant: @plant:41@'}}
        self.assertEqual(render_changelog(source, config, {('plant', '41'): 'Tundraweed'}),
                         'New plant: Tundraweed\r\n未翻译名称\r\n')

    def test_reviewed_ui_preserves_runtime_arguments(self):
        rules = json.loads((ROOT / 'assets/ui-feedback-4.0.json').read_text(encoding='utf8'))
        for source, target in rules['generic'].items():
            self.assertTrue(same_arguments(source, target), source)


if __name__ == '__main__':
    unittest.main()
