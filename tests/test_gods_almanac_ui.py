import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from apply_gods_almanac_ui import choose, patch_catalog, valid_text


class GodsAlmanacUITests(unittest.TestCase):
    def test_source_guard_and_upstream_priority(self):
        r = {'source': '条件', 'before': '条件', 'target': 'Fallback'}
        self.assertEqual(choose('条件', '条件', r, {'条件': 'PC wording'}), ('PC wording', 'pc_exact'))
        self.assertEqual(choose('条件', 'Fallback', r, {'条件': 'PC wording'})[0], 'PC wording')
        self.assertEqual(choose('条件', 'New reviewed English', r, {})[0], 'New reviewed English')
        with self.assertRaises(ValueError):
            choose('New source', '条件', r, {})

    def test_format_tokens_and_partial_tags_preserved(self):
        valid_text('<size=85%>{0:F0} [[plant:Peashooter]]', '<size=85%>Count: {0:F0} [[plant:Peashooter]]')
        for bad in ('{0}', '{0:F1}', '{1:F0}'):
            with self.assertRaises(AssertionError):
                valid_text('{0:F0}', bad)
        with self.assertRaises(AssertionError):
            valid_text('[[plant:A]]', '[[plant:B]]')
        with self.assertRaises(AssertionError):
            valid_text('<size=85%>Text', '<size=85%>Text</size>')

    def test_catalog_only_changes_reviewed_condition_not_lookup_fields(self):
        original = {'plants': [{'configType': 'GameLevel.A+B', 'type': '条件'}],
                    'entries': [{'id': 'id', 'condition': '条件', 'title': '条件', 'group': '条件'}]}
        rule = {'index': 0, 'id': 'id', 'field': 'condition', 'source': '条件', 'before': '条件', 'target': 'Requirement'}
        after, _ = patch_catalog(original, original, [rule], {})
        self.assertEqual(after['plants'], original['plants'])
        self.assertEqual(after['entries'][0]['group'], '条件')
        self.assertEqual(after['entries'][0]['title'], '条件')
        self.assertEqual(original['entries'][0]['condition'], '条件')
        self.assertEqual(after['entries'][0]['condition'], 'Requirement')
        with self.assertRaises(AssertionError):
            patch_catalog(original, original, [dict(rule, field='type')], {})
        with self.assertRaises(AssertionError):
            patch_catalog(original, original, [dict(rule, id='wrong')], {})

    def test_malformed_pc_format_cannot_replace_fallback(self):
        r = {'source': '{0:F0} 次', 'before': '{0:F0} 次', 'target': '{0:F0} selections'}
        self.assertEqual(choose(r['source'], r['before'], r, {r['source']: '{0} uses'})[0], r['target'])


if __name__ == '__main__':
    unittest.main()
